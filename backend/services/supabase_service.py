import os
import re
import time
from typing import List, Dict, Any, Optional
from backend.config import SUPABASE_URL, SUPABASE_KEY, IS_SUPABASE_ENABLED, DATA_DIR

try:
    from supabase import create_client, Client
    _supabase_installed = True
except ImportError:
    _supabase_installed = False

class SupabaseService:
    def __init__(self):
        self.client: Optional[Any] = None
        self.is_connected = False
        self._search_cache: Dict[str, Any] = {}
        self._init_client()

    def _init_client(self):
        if not _supabase_installed or not IS_SUPABASE_ENABLED:
            self.is_connected = False
            return

        try:
            self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test ping
            test_res = self.client.table("college_documents").select("id").limit(1).execute()
            if not isinstance(test_res.data, list):
                raise ValueError(f"Supabase endpoint did not return JSON records. Response type: {type(test_res.data)}")
            self.is_connected = True
            print(f"[SupabaseService] Successfully connected to live Supabase project ({SUPABASE_URL}).")
        except Exception as e:
            print(f"[SupabaseService] Connection error: {e}. Falling back to local knowledge engine.")
            self.client = None
            self.is_connected = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": IS_SUPABASE_ENABLED,
            "connected": self.is_connected,
            "url": SUPABASE_URL if self.is_connected else None
        }

    # ==========================================
    # DOCUMENT MANAGEMENT
    # ==========================================
    def upload_document(
        self,
        title: str,
        category: str,
        filename: str,
        file_type: str,
        content_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Stores document in Supabase college_documents and chunks into knowledge_chunks.
        """
        if not self.is_connected or not self.client:
            raise RuntimeError("Supabase is not connected.")

        # 1. Insert Document
        doc_payload = {
            "title": title.strip(),
            "category": category.strip().lower(),
            "filename": filename.strip(),
            "file_type": file_type.strip().lower(),
            "content_text": content_text,
            "metadata": metadata or {}
        }

        res = self.client.table("college_documents").insert(doc_payload).execute()
        if not res.data:
            raise RuntimeError("Failed to insert document into Supabase.")

        doc_record = res.data[0]
        doc_id = doc_record["id"]

        # 2. Chunk text and insert into knowledge_chunks
        chunks = self._chunk_text(content_text, title, filename)
        chunk_records = []
        for idx, ch in enumerate(chunks):
            chunk_records.append({
                "document_id": doc_id,
                "document_title": title,
                "section_title": ch["section"],
                "chunk_content": ch["content"],
                "chunk_index": idx,
                "tags": [category.lower(), filename.lower()],
                "metadata": {"source_file": filename}
            })

        if chunk_records:
            self.client.table("knowledge_chunks").insert(chunk_records).execute()

        self._search_cache.clear()
        return {
            "success": True,
            "document": doc_record,
            "chunks_count": len(chunk_records)
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []

        res = self.client.table("college_documents").select("*").order("created_at", desc=True).execute()
        docs = res.data or []

        # Fetch chunk counts per document
        for doc in docs:
            cnt_res = self.client.table("knowledge_chunks").select("id", count="exact").eq("document_id", doc["id"]).execute()
            doc["chunks_count"] = cnt_res.count if hasattr(cnt_res, "count") and cnt_res.count is not None else 0

        return docs

    def delete_document(self, doc_id: str) -> bool:
        if not self.is_connected or not self.client:
            return False

        self._search_cache.clear()
        # Attempt delete by UUID primary key
        try:
            res = self.client.table("college_documents").delete().eq("id", doc_id).execute()
            if res.data:
                return True
        except Exception:
            pass

        # Attempt delete by filename
        try:
            res = self.client.table("college_documents").delete().eq("filename", doc_id).execute()
            return bool(res.data)
        except Exception as e:
            print(f"[SupabaseService] Delete error: {e}")
            return False

    def _chunk_text(self, text: str, title: str, filename: str) -> List[Dict[str, str]]:
        sections = re.split(r"(?m)^##\s+", text)
        chunks = []
        for idx, sec in enumerate(sections):
            sec_clean = sec.strip()
            if not sec_clean:
                continue
            lines = sec_clean.split("\n", 1)
            section_title = lines[0].strip() if len(lines) > 1 and len(lines[0]) < 120 else f"Section {idx}"
            content = lines[1].strip() if len(lines) > 1 and len(lines[0]) < 120 else sec_clean
            chunks.append({
                "section": section_title,
                "content": content[:1800]
            })
        if not chunks:
            chunks.append({"section": "General", "content": text[:1800]})
        return chunks

    # ==========================================
    # KNOWLEDGE RETRIEVAL
    # ==========================================
    def search_knowledge(self, query: str, match_count: int = 4) -> Dict[str, Any]:
        """
        Retrieves grounded chunks from Supabase using Postgres full-text search function.
        Cached in-memory for 120 seconds to maximize live presentation responsiveness.
        """
        if not self.is_connected or not self.client:
            return {"found": False, "chunks": [], "sources": [], "primary_source": None}

        cache_key = f"{query.strip().lower()}_{match_count}"
        if cache_key in self._search_cache:
            entry = self._search_cache[cache_key]
            if time.time() - entry["ts"] < 120:
                return entry["result"]

        try:
            clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
            # Use stored search function
            rpc_res = self.client.rpc("search_college_knowledge", {
                "search_query": clean_q or query,
                "match_count": match_count
            }).execute()

            raw_chunks = rpc_res.data or []
            if not raw_chunks:
                res = {"found": False, "chunks": [], "sources": [], "primary_source": None}
                self._search_cache[cache_key] = {"ts": time.time(), "result": res}
                return res

            results = []
            sources = set()
            for r in raw_chunks:
                meta = r.get("metadata") or {}
                source_file = meta.get("source_file", "Supabase Document")
                doc_title = r.get("document_title") or meta.get("document_title") or "College Document"
                section_title = r.get("section_title") or "Section"
                chunk_text = r.get("chunk_content") or ""
                sources.add(f"{doc_title} ({source_file})")
                results.append({
                    "chunk_id": str(r.get("chunk_id") or r.get("id")),
                    "title": doc_title,
                    "source_file": source_file,
                    "section": section_title,
                    "content": chunk_text,
                    "score": float(r.get("similarity_score", 0.8))
                })

            res = {
                "found": len(results) > 0,
                "chunks": results,
                "sources": list(sources),
                "primary_source": list(sources)[0] if sources else None
            }
            if len(self._search_cache) > 200:
                self._search_cache.clear()
            self._search_cache[cache_key] = {"ts": time.time(), "result": res}
            return res
        except Exception as e:
            print(f"[SupabaseService] Search exception: {e}")
            return {"found": False, "chunks": [], "sources": [], "primary_source": None}

    # ==========================================
    # CONVERSATION SESSIONS
    # ==========================================
    def save_session_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        sources: Optional[List[str]] = None,
        action_executed: Optional[str] = None
    ):
        if not self.is_connected or not self.client:
            return
        try:
            self.client.table("conversation_sessions").insert({
                "session_id": session_id,
                "role": role,
                "content": content,
                "detected_intent": intent,
                "entities": entities or {},
                "sources": sources or [],
                "action_executed": action_executed
            }).execute()
        except Exception as e:
            print(f"[SupabaseService] Error logging session turn: {e}")

    # ==========================================
    # STUDENT REMINDERS
    # ==========================================
    def create_reminder(self, session_id: str, title: str, due_date: Optional[str], priority: str = "Normal") -> Dict[str, Any]:
        if not self.is_connected or not self.client:
            return {"success": False, "error": "Supabase not connected"}
        try:
            res = self.client.table("reminders").insert({
                "session_id": session_id,
                "title": title,
                "due_date": due_date,
                "priority": priority,
                "is_completed": False
            }).execute()
            return {"success": True, "reminder": res.data[0]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_reminders(self, session_id: str) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            res = self.client.table("reminders").select("*").eq("session_id", session_id).order("created_at", desc=True).execute()
            return res.data or []
        except Exception:
            return []

    # ==========================================
    # CAMPUS STRUCTURED KNOWLEDGE (SUPABASE)
    # ==========================================
    def query_exams(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            query = self.client.table("exams").select("*")
            if subject:
                s = subject.strip()
                query = query.or_(f"subject.ilike.%{s}%,code.ilike.%{s}%,title.ilike.%{s}%")
            else:
                query = query.order("iso_date", desc=False)
            res = query.execute()
            return res.data or []
        except Exception as e:
            print(f"[SupabaseService] Query exams error: {e}")
            return []

    def query_timetable(self, day: Optional[str] = None, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            query = self.client.table("timetable").select("*")
            if day and subject:
                query = query.ilike("day", f"%{day.strip()}%").ilike("subject", f"%{subject.strip()}%")
            elif day:
                query = query.ilike("day", f"%{day.strip()}%")
            elif subject:
                query = query.ilike("subject", f"%{subject.strip()}%")
            res = query.order("id", desc=False).execute()
            return res.data or []
        except Exception as e:
            print(f"[SupabaseService] Query timetable error: {e}")
            return []

    def query_faculty(self, name_or_subject: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            query = self.client.table("faculty").select("*")
            if name_or_subject:
                q = name_or_subject.strip()
                query = query.or_(f"name.ilike.%{q}%,department.ilike.%{q}%")
            res = query.order("id", desc=False).execute()
            return res.data or []
        except Exception as e:
            print(f"[SupabaseService] Query faculty error: {e}")
            return []

    def query_classrooms(self, room_name: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            query = self.client.table("classrooms").select("*")
            if room_name:
                q = room_name.strip()
                query = query.or_(f"name.ilike.%{q}%,block.ilike.%{q}%")
            res = query.order("id", desc=False).execute()
            return res.data or []
        except Exception as e:
            print(f"[SupabaseService] Query classrooms error: {e}")
            return []

    def query_notices(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            query = self.client.table("notices").select("*")
            if category:
                query = query.ilike("category", f"%{category.strip()}%")
            res = query.order("date", desc=True).execute()
            return res.data or []
        except Exception as e:
            print(f"[SupabaseService] Query notices error: {e}")
            return []

    def query_assignments(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            query = self.client.table("assignments").select("*")
            if subject:
                query = query.ilike("subject", f"%{subject.strip()}%")
            res = query.order("id", desc=False).execute()
            return res.data or []
        except Exception as e:
            print(f"[SupabaseService] Query assignments error: {e}")
            return []

    def query_events(self) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            res = self.client.table("events").select("*").order("date", desc=False).execute()
            return res.data or []
        except Exception as e:
            print(f"[SupabaseService] Query events error: {e}")
            return []

    def query_facilities(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected or not self.client:
            return []
        try:
            query = self.client.table("facilities").select("*")
            if name:
                query = query.ilike("name", f"%{name.strip()}%")
            res = query.order("id", desc=False).execute()
            return res.data or []
        except Exception as e:
            print(f"[SupabaseService] Query facilities error: {e}")
            return []

    def sync_campus_knowledge(self) -> Dict[str, Any]:
        """
        Seeds campus structured entities (exams, timetable, faculty, etc.)
        from data/campus_knowledge.json into Supabase if empty.
        """
        if not self.is_connected or not self.client:
            return {"success": False, "message": "Supabase not connected"}

        json_path = DATA_DIR / "campus_knowledge.json"
        if not json_path.exists():
            return {"success": False, "message": "campus_knowledge.json not found"}

        try:
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 1. Exams
            ex_res = self.client.table("exams").select("id", count="exact").limit(1).execute()
            if getattr(ex_res, "count", 0) == 0:
                exams_payload = []
                for ex in data.get("exams", []):
                    exams_payload.append({
                        "id": ex["id"],
                        "subject": ex["subject"],
                        "code": ex["code"],
                        "title": ex["title"],
                        "date": ex["date"],
                        "iso_date": ex.get("iso_date"),
                        "time": ex["time"],
                        "duration": ex.get("duration"),
                        "room": ex["room"],
                        "block": ex["block"],
                        "instructor": ex["instructor"],
                        "format": ex.get("format"),
                        "syllabus": ex.get("syllabus")
                    })
                if exams_payload:
                    self.client.table("exams").upsert(exams_payload).execute()

            # 2. Timetable
            tt_res = self.client.table("timetable").select("id", count="exact").limit(1).execute()
            if getattr(tt_res, "count", 0) == 0:
                tt_payload = []
                for day_item in data.get("timetable", []):
                    d = day_item["day"]
                    for slot in day_item.get("slots", []):
                        tt_payload.append({
                            "day": d,
                            "time": slot["time"],
                            "subject": slot["subject"],
                            "code": slot.get("code"),
                            "room": slot["room"],
                            "instructor": slot["instructor"],
                            "type": slot.get("type", "Lecture")
                        })
                if tt_payload:
                    self.client.table("timetable").insert(tt_payload).execute()

            # 3. Faculty
            fac_res = self.client.table("faculty").select("id", count="exact").limit(1).execute()
            if getattr(fac_res, "count", 0) == 0:
                fac_payload = []
                for fac in data.get("faculty", []):
                    fac_payload.append({
                        "name": fac["name"],
                        "title": fac["title"],
                        "department": fac["department"],
                        "email": fac["email"],
                        "phone": fac.get("phone"),
                        "office": fac["office"],
                        "office_hours": fac["office_hours"],
                        "subjects": fac.get("subjects", []),
                        "research": fac.get("research")
                    })
                if fac_payload:
                    self.client.table("faculty").insert(fac_payload).execute()

            # 4. Classrooms
            cr_res = self.client.table("classrooms").select("id", count="exact").limit(1).execute()
            if getattr(cr_res, "count", 0) == 0:
                cr_payload = []
                for cr in data.get("classrooms", []):
                    cr_payload.append({
                        "name": cr["name"],
                        "block": cr["block"],
                        "floor": cr["floor"],
                        "capacity": cr.get("capacity"),
                        "facilities": cr.get("facilities", []),
                        "directions": cr["directions"]
                    })
                if cr_payload:
                    self.client.table("classrooms").upsert(cr_payload).execute()

            # 5. Notices
            nt_res = self.client.table("notices").select("id", count="exact").limit(1).execute()
            if getattr(nt_res, "count", 0) == 0:
                nt_payload = []
                for noti in data.get("notices", []):
                    nt_payload.append({
                        "id": noti["id"],
                        "title": noti["title"],
                        "category": noti["category"],
                        "priority": noti["priority"],
                        "date": noti["date"],
                        "details": noti["details"],
                        "action": noti.get("action")
                    })
                if nt_payload:
                    self.client.table("notices").upsert(nt_payload).execute()

            # 6. Assignments
            as_res = self.client.table("assignments").select("id", count="exact").limit(1).execute()
            if getattr(as_res, "count", 0) == 0:
                as_payload = []
                for asn in data.get("assignments", []):
                    as_payload.append({
                        "subject": asn["subject"],
                        "title": asn["title"],
                        "due_date": asn["due_date"],
                        "portal": asn["portal"],
                        "weightage": asn.get("weightage"),
                        "notes": asn.get("notes")
                    })
                if as_payload:
                    self.client.table("assignments").insert(as_payload).execute()

            # 7. Events
            ev_res = self.client.table("events").select("id", count="exact").limit(1).execute()
            if getattr(ev_res, "count", 0) == 0:
                ev_payload = []
                for ev in data.get("events", []):
                    ev_payload.append({
                        "title": ev["title"],
                        "category": ev["category"],
                        "date": ev["date"],
                        "time": ev["time"],
                        "venue": ev["venue"],
                        "organizer": ev["organizer"],
                        "highlights": ev.get("highlights")
                    })
                if ev_payload:
                    self.client.table("events").insert(ev_payload).execute()

            # 8. Facilities
            fc_res = self.client.table("facilities").select("id", count="exact").limit(1).execute()
            if getattr(fc_res, "count", 0) == 0:
                fc_payload = []
                for fac in data.get("facilities", []):
                    fc_payload.append({
                        "name": fac["name"],
                        "location": fac["location"],
                        "timings": fac["timings"],
                        "services": fac["services"]
                    })
                if fc_payload:
                    self.client.table("facilities").insert(fc_payload).execute()

            return {"success": True, "message": "Supabase campus knowledge synced successfully"}
        except Exception as e:
            print(f"[SupabaseService] Sync error: {e}")
            return {"success": False, "error": str(e)}

    # ==========================================
    # SYNC LOCAL DOCUMENTS TO SUPABASE
    # ==========================================
    def sync_local_documents(self) -> Dict[str, Any]:
        """
        Seeds local files from data/documents into Supabase if not already present.
        """
        if not self.is_connected or not self.client:
            return {"success": False, "message": "Supabase not connected"}

        doc_dir = DATA_DIR / "documents"
        if not doc_dir.exists():
            return {"success": False, "message": "No local documents directory"}

        existing_docs = self.list_documents()
        existing_filenames = {d["filename"] for d in existing_docs}

        synced_count = 0
        for f in doc_dir.glob("*.*"):
            if f.name in existing_filenames:
                continue

            file_type = f.suffix.replace(".", "").lower()
            text = ""
            if file_type in ["txt", "md"]:
                with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                    text = fp.read()
            elif file_type == "pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(f))
                    for p in reader.pages:
                        text += (p.extract_text() or "") + "\n"
                except Exception:
                    pass

            if text:
                title = f.name.replace("_", " ").replace(".txt", "").replace(".pdf", "").title()
                category = "handbook" if "rules" in f.name else ("syllabus" if "syllabi" in f.name else "protocols")
                self.upload_document(title, category, f.name, file_type, text)
                synced_count += 1

        return {"success": True, "synced_count": synced_count}

supabase_service = SupabaseService()
