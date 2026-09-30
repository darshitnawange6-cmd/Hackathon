import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pypdf

from backend.config import DATA_DIR
from backend.services import knowledge_service

class RAGChunk:
    def __init__(self, chunk_id: str, title: str, source_file: str, section: str, content: str, tags: Optional[List[str]] = None):
        self.chunk_id = chunk_id
        self.title = title
        self.source_file = source_file
        self.section = section
        self.content = content.strip()
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "title": self.title,
            "source_file": self.source_file,
            "section": self.section,
            "content": self.content,
            "tags": self.tags
        }

class RAGKnowledgeService:
    def __init__(self):
        self.documents_dir = DATA_DIR / "documents"
        self.chunks: List[RAGChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.indexed_files: List[str] = []
        self._retrieval_cache: Dict[str, Any] = {}
        self.reindex()

    def reindex(self):
        """Scans data/documents and database records to rebuild the unified RAG index."""
        self.chunks = []
        self.indexed_files = []
        self._retrieval_cache.clear()

        # 1. Ingest files from data/documents
        if self.documents_dir.exists():
            for file_path in self.documents_dir.glob("*.*"):
                if file_path.suffix.lower() in [".txt", ".md"]:
                    self._ingest_text_file(file_path)
                elif file_path.suffix.lower() == ".pdf":
                    self._ingest_pdf_file(file_path)

        # 2. Ingest structured knowledge from SQLite
        self._ingest_database_records()

        # 3. Fit TF-IDF Vectorizer
        if self.chunks:
            corpus = [f"{c.title} {c.section} {c.content} {' '.join(c.tags)}" for c in self.chunks]
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            print(f"[RAGService] Successfully indexed {len(self.chunks)} knowledge chunks from {len(self.indexed_files)} sources.")
        else:
            self.vectorizer = None
            self.tfidf_matrix = None

    def _ingest_text_file(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
            self._split_and_add_chunks(file_path.name, raw_text)
            self.indexed_files.append(file_path.name)
        except Exception as e:
            print(f"[RAGService] Error reading text file {file_path}: {e}")

    def _ingest_pdf_file(self, file_path: Path):
        try:
            reader = pypdf.PdfReader(str(file_path))
            full_text = ""
            for idx, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                full_text += f"\n--- Page {idx + 1} ---\n" + extracted
            self._split_and_add_chunks(file_path.name, full_text)
            self.indexed_files.append(file_path.name)
        except Exception as e:
            print(f"[RAGService] Error reading PDF file {file_path}: {e}")

    def _split_and_add_chunks(self, filename: str, text: str):
        # Extract title from first markdown header if available
        first_header_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        doc_title = first_header_match.group(1).strip() if first_header_match else filename.replace("_", " ").replace(".txt", "").replace(".pdf", "").title()

        # Split by ## Section headers or large paragraphs
        sections = re.split(r"(?m)^##\s+", text)
        for idx, sec in enumerate(sections):
            sec_clean = sec.strip()
            if not sec_clean:
                continue
            lines = sec_clean.split("\n", 1)
            section_title = lines[0].strip() if len(lines) > 1 and len(lines[0]) < 120 else f"Section {idx}"
            content = lines[1].strip() if len(lines) > 1 and len(lines[0]) < 120 else sec_clean

            # Clean and add chunk
            chunk_id = f"{filename}_{idx}"
            self.chunks.append(RAGChunk(
                chunk_id=chunk_id,
                title=doc_title,
                source_file=filename,
                section=section_title,
                content=content[:1800]
            ))

    def _ingest_database_records(self):
        # Ingest Exams
        exams = knowledge_service.query_exam()
        for ex in exams:
            content = (
                f"Course: {ex['title']} ({ex['code']})\n"
                f"Exam Date: {ex['date']}\n"
                f"Time: {ex['time']} ({ex.get('duration', '3 Hours')})\n"
                f"Location / Hall: {ex['room']} located in {ex['block']}\n"
                f"Course Instructor: {ex['instructor']}\n"
                f"Format & Rules: {ex.get('format', 'Standard')}\n"
                f"Syllabus: {ex.get('syllabus', '')}"
            )
            self.chunks.append(RAGChunk(
                chunk_id=f"db_exam_{ex['id']}",
                title="Midterm Examination Schedule (Fall 2026)",
                source_file="campus_exam_roster.db",
                section=f"Exam: {ex['subject']} ({ex['code']})",
                content=content,
                tags=[ex['subject'], ex['code'], ex['room'], "exam", "midterm"]
            ))

        # Ingest Timetable
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            slots = knowledge_service.query_timetable(day=day)
            if slots:
                slot_text = "\n".join([f"- {s['time']}: {s['subject']} ({s.get('type')}) in {s['room']} with {s['instructor']}" for s in slots])
                self.chunks.append(RAGChunk(
                    chunk_id=f"db_timetable_{day.lower()}",
                    title="Official Campus Class Timetable",
                    source_file="campus_timetable.db",
                    section=f"{day} Class Schedule",
                    content=slot_text,
                    tags=[day, "timetable", "classes", "schedule"]
                ))

        # Ingest Faculty
        faculty = knowledge_service.query_faculty()
        for f in faculty:
            sub_str = ", ".join(f.get("subjects", [])) if isinstance(f.get("subjects"), list) else str(f.get("subjects", ""))
            content = (
                f"Professor: {f['name']} ({f['title']})\n"
                f"Department: {f['department']}\n"
                f"Office Location: {f['office']}\n"
                f"Office Hours: {f['office_hours']}\n"
                f"Email: {f['email']} | Phone: {f.get('phone', 'N/A')}\n"
                f"Courses Taught: {sub_str}\n"
                f"Research: {f.get('research', '')}"
            )
            self.chunks.append(RAGChunk(
                chunk_id=f"db_fac_{f['id']}",
                title="Faculty Directory & Office Hours",
                source_file="faculty_directory.db",
                section=f.get("name"),
                content=content,
                tags=[f['name'], f['department'], "faculty", "office hours"]
            ))

        # Ingest Notices
        notices = knowledge_service.query_notices()
        for n in notices:
            content = (
                f"Announcement: {n['title']}\n"
                f"Priority: {n['priority']} | Category: {n['category']} | Date: {n['date']}\n"
                f"Details: {n['details']}\n"
                f"Required Action: {n.get('action', 'None')}"
            )
            self.chunks.append(RAGChunk(
                chunk_id=f"db_notice_{n['id']}",
                title="Official Campus Bulletins & Notices",
                source_file="campus_notices.db",
                section=n['title'],
                content=content,
                tags=[n['category'], n['priority'], "notice", "announcement"]
            ))

        # Ingest Events
        events = knowledge_service.query_events()
        for ev in events:
            content = (
                f"Event: {ev['title']} ({ev['category']})\n"
                f"Date & Time: {ev['date']} at {ev['time']}\n"
                f"Venue: {ev['venue']}\n"
                f"Organizer: {ev['organizer']}\n"
                f"Highlights: {ev.get('highlights', '')}"
            )
            self.chunks.append(RAGChunk(
                chunk_id=f"db_event_{ev['id']}",
                title="Campus Events, Hackathons & Fests",
                source_file="campus_events.db",
                section=ev['title'],
                content=content,
                tags=[ev['category'], ev['organizer'], "event", "hackathon"]
            ))

        # Ingest Library & Facilities
        lib = knowledge_service.query_library()
        if lib:
            content = (
                f"Library: {lib.get('name')}\n"
                f"Regular Timings: {lib.get('regular_timings')}\n"
                f"Exam Period Timings: {lib.get('exam_period_timings')}\n"
                f"Borrowing Rules: {lib.get('borrowing_rules')}\n"
                f"Floors: {str(lib.get('floors_guide', ''))}\n"
                f"Digital Resources: {lib.get('digital_resources')}"
            )
            self.chunks.append(RAGChunk(
                chunk_id="db_library",
                title="Central Library Guide & Timings",
                source_file="campus_library.db",
                section="Central Library Regulations",
                content=content,
                tags=["library", "books", "hours", "study zone"]
            ))

    def retrieve(self, query: str, top_k: int = 3, threshold: float = 0.12) -> Dict[str, Any]:
        """
        Retrieves top relevant grounded chunks for a query.
        Returns:
            {
                "found": bool,
                "chunks": List[Dict],
                "sources": List[str],
                "primary_source": str
            }
        """
        if not self.chunks or not self.vectorizer or not self.tfidf_matrix is not None:
            return {"found": False, "chunks": [], "sources": [], "primary_source": None}

        cache_key = f"{query.strip().lower()}_{top_k}_{threshold}"
        if cache_key in self._retrieval_cache:
            return self._retrieval_cache[cache_key]

        # Vectorize query
        q_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(q_vec, self.tfidf_matrix)[0]

        # Rank indices
        ranked_indices = np.argsort(similarities)[::-1]
        results = []
        sources = set()

        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            if score >= threshold:
                chunk = self.chunks[idx]
                chunk_dict = chunk.to_dict()
                chunk_dict["score"] = round(score, 3)
                results.append(chunk_dict)
                sources.add(f"{chunk.title} ({chunk.source_file})")

        found = len(results) > 0
        res = {
            "found": found,
            "chunks": results,
            "sources": list(sources),
            "primary_source": list(sources)[0] if sources else None,
            "top_score": results[0]["score"] if results else 0.0
        }
        if len(self._retrieval_cache) > 200:
            self._retrieval_cache.clear()
        self._retrieval_cache[cache_key] = res
        return res

rag_service = RAGKnowledgeService()
