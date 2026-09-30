import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.models import ChatRequest, ChatResponse, ClearSessionRequest
from backend.services.llm_service import llm_service
from backend.services import conversation_service
from backend.database import get_db_connection

router = APIRouter(prefix="/api", tags=["Conversational AI"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    cleaned_msg = payload.message.strip()
    if not cleaned_msg:
        raise HTTPException(status_code=400, detail="User message cannot be empty.")
    
    try:
        response = await llm_service.generate_response(
            query=cleaned_msg,
            session_id=payload.session_id,
            is_voice=payload.is_voice
        )
        return response
    except Exception as e:
        print(f"[Chat Endpoint Error]: {e}")
        # Safe Tier 3 Fallback without exposing raw error traces
        return ChatResponse(
            response_text="### ℹ️ Campus Assistant (Local Mode)\n\nI encountered a momentary service interruption. I am active on local campus knowledge mode. How can I help you with your exams, timetable, or campus rules?",
            spoken_text="I am active on local campus mode. How can I help you with your exams or classes?",
            detected_intent="general_campus",
            standard_intent="UNKNOWN",
            confidence=1.0,
            entities={},
            follow_up_suggestions=["When is my Physics exam?", "Today's timetable", "College notices"],
            sources=["Campus Core Fallback"],
            source_details=[{
                "document_name": "Campus Core Fallback",
                "category": "Resilient Fallback",
                "date": "Active Session",
                "section": "Local Resilient Mode"
            }],
            primary_source="Campus Core Fallback",
            action_executed=None,
            action_result=None,
            mode="demo",
            clarification_needed=False,
            clarification_field=None,
            metrics={"retrieval_time_ms": 0.0, "ai_response_time_ms": 0.0, "total_response_time_ms": 1.0},
            metadata={"fallback": True}
        )

@router.post("/chat/stream")
async def chat_stream_endpoint(payload: ChatRequest):
    cleaned_msg = payload.message.strip()
    if not cleaned_msg:
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    async def event_generator():
        try:
            response = await llm_service.generate_response(
                query=cleaned_msg,
                session_id=payload.session_id,
                is_voice=payload.is_voice
            )

            # Metadata header
            meta_payload = {
                "type": "metadata",
                "detected_intent": response.get("detected_intent"),
                "standard_intent": response.get("standard_intent"),
                "sources": response.get("sources", []),
                "source_details": response.get("source_details", []),
                "primary_source": response.get("primary_source"),
                "action_executed": response.get("action_executed"),
                "mode": response.get("mode")
            }
            yield f"data: {json.dumps(meta_payload)}\n\n"

            # Progressive token/word stream
            full_text = response.get("response_text", "")
            words = full_text.split(" ")
            chunk_size = 4
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                if i + chunk_size < len(words):
                    chunk += " "
                yield f"data: {json.dumps({'type': 'delta', 'delta': chunk})}\n\n"
                await asyncio.sleep(0.015)

            # Done event
            done_payload = {
                "type": "done",
                "full_text": full_text,
                "spoken_text": response.get("spoken_text", ""),
                "follow_up_suggestions": response.get("follow_up_suggestions", []),
                "metrics": response.get("metrics", {}),
                "action_result": response.get("action_result"),
                "clarification_needed": response.get("clarification_needed", False),
                "clarification_field": response.get("clarification_field")
            }
            yield f"data: {json.dumps(done_payload)}\n\n"
        except Exception as e:
            print(f"[Chat Stream Error]: {e}")
            fallback_text = "I encountered a momentary service interruption. I am active on local campus knowledge mode. How can I help you with your exams, timetable, or campus rules?"
            yield f"data: {json.dumps({'type': 'delta', 'delta': fallback_text})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'full_text': fallback_text, 'spoken_text': fallback_text, 'follow_up_suggestions': ['When is my Physics exam?', 'Today timetable', 'College notices'], 'metrics': {'total_response_time_ms': 1.0}})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/session/{session_id}")
async def get_session_details(session_id: str):
    history = conversation_service.get_conversation_history(session_id)
    context = conversation_service.get_session_context(session_id)
    return {
        "session_id": session_id,
        "context": context,
        "history": history
    }

@router.post("/session/clear")
async def clear_session_endpoint(payload: ClearSessionRequest):
    conversation_service.clear_session(payload.session_id)
    return {
        "status": "success",
        "message": f"Session {payload.session_id} conversation context cleared."
    }

@router.get("/health")
async def health_check():
    status = llm_service.get_status()
    db_connected = False
    exam_count = 0
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM exams")
        exam_count = c.fetchone()[0]
        conn.close()
        db_connected = True
    except Exception:
        db_connected = False

    return {
        "status": "healthy",
        "service": "VocaGuide Campus Assistant Backend",
        "database_connected": db_connected,
        "sample_records_loaded": exam_count,
        "ai_engine": status
    }
