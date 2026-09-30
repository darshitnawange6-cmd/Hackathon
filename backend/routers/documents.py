import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pypdf

from backend.config import DATA_DIR
from backend.services.supabase_service import supabase_service
from backend.services.rag_service import rag_service

router = APIRouter(prefix="/api/documents", tags=["Document Management"])

@router.get("/")
async def list_documents():
    """
    Returns list of all indexed college documents.
    Uses Supabase if connected, otherwise reads local document directory.
    """
    if supabase_service.is_connected:
        docs = supabase_service.list_documents()
        return {
            "source": "supabase",
            "connected": True,
            "count": len(docs),
            "documents": docs
        }

    # Fallback to local files
    doc_dir = DATA_DIR / "documents"
    local_docs = []
    if doc_dir.exists():
        for f in doc_dir.glob("*.*"):
            local_docs.append({
                "id": f.name,
                "title": f.stem.replace("_", " ").title(),
                "filename": f.name,
                "category": "general",
                "file_type": f.suffix.replace(".", "").lower(),
                "chunks_count": len([c for c in rag_service.chunks if c.source_file == f.name]),
                "created_at": "Local storage"
            })

    return {
        "source": "local",
        "connected": False,
        "count": len(local_docs),
        "documents": local_docs
    }

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form("general")
):
    """
    Uploads a PDF, TXT, or MD document, extracts text, chunks it,
    and stores in Supabase and local storage.
    """
    filename = file.filename or "uploaded_document.txt"
    file_ext = Path(filename).suffix.lower()

    if file_ext not in [".pdf", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail="Only .pdf, .txt, and .md files are supported.")

    doc_dir = DATA_DIR / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    local_path = doc_dir / filename

    # Read content
    content_bytes = await file.read()
    with open(local_path, "wb") as f:
        f.write(content_bytes)

    # Extract text
    text = ""
    if file_ext == ".pdf":
        try:
            reader = pypdf.PdfReader(str(local_path))
            for p in reader.pages:
                text += (p.extract_text() or "") + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF text: {str(e)}")
    else:
        text = content_bytes.decode("utf-8", errors="ignore")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Extracted text from document is empty.")

    # Ingest into Supabase if connected
    supabase_res = None
    if supabase_service.is_connected:
        try:
            supabase_res = supabase_service.upload_document(
                title=title,
                category=category,
                filename=filename,
                file_type=file_ext.replace(".", ""),
                content_text=text,
                metadata={"file_size": len(content_bytes)}
            )
        except Exception as e:
            print(f"[DocumentUpload] Supabase upload failed: {e}")

    # Reindex local RAG
    rag_service.reindex()

    return {
        "success": True,
        "filename": filename,
        "title": title,
        "category": category,
        "supabase_synced": bool(supabase_res and supabase_res.get("success")),
        "chunks_count": supabase_res.get("chunks_count") if supabase_res else len(rag_service.chunks)
    }

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    Deletes a document by ID or filename.
    """
    deleted_supabase = False
    if supabase_service.is_connected:
        deleted_supabase = supabase_service.delete_document(doc_id)

    # Also check local file by doc_id (which might be filename)
    doc_dir = DATA_DIR / "documents"
    local_file = doc_dir / doc_id
    deleted_local = False
    if local_file.exists():
        os.remove(local_file)
        deleted_local = True

    rag_service.reindex()

    return {
        "success": deleted_supabase or deleted_local,
        "doc_id": doc_id,
        "deleted_from_supabase": deleted_supabase,
        "deleted_from_local": deleted_local
    }

@router.post("/sync")
async def sync_documents():
    """Syncs all files in data/documents to Supabase."""
    res = supabase_service.sync_local_documents()
    rag_service.reindex()
    return res
