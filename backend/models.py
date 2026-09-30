from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message via speech transcription or text")
    session_id: str = Field(default="default-student-session", description="Session identifier for multi-turn conversational context")
    is_voice: bool = Field(default=False, description="Whether the input originated from voice speech-to-text")

class IntentResult(BaseModel):
    intent: str
    confidence: float
    entities: Dict[str, Any] = {}
    description: str

class ChatResponse(BaseModel):
    response_text: str
    spoken_text: str
    detected_intent: str
    standard_intent: Optional[str] = "UNKNOWN"
    confidence: float
    entities: Dict[str, Any] = {}
    follow_up_suggestions: List[str] = []
    sources: List[str] = []
    source_details: Optional[List[Dict[str, Any]]] = []
    primary_source: Optional[str] = None
    action_executed: Optional[str] = None
    action_result: Optional[Dict[str, Any]] = None
    mode: str = "demo"
    clarification_needed: bool = False
    clarification_field: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = {}
    metadata: Dict[str, Any] = {}


class ClearSessionRequest(BaseModel):
    session_id: str = "default-student-session"

class CampusOverviewResponse(BaseModel):
    campus_name: str
    academic_year: str
    current_semester: str
    quick_stats: Dict[str, int]
