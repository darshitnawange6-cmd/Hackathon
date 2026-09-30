import json
from typing import Dict, Any, List, Optional
from backend.database import get_db_connection

# In-memory store for fast session context tracking
# Keyed by session_id
_SESSION_STORE: Dict[str, Dict[str, Any]] = {}

def get_session_context(session_id: str) -> Dict[str, Any]:
    if session_id not in _SESSION_STORE:
        _SESSION_STORE[session_id] = {
            "last_intent": None,
            "last_subject": None,
            "last_exam": None,
            "last_classroom": None,
            "last_faculty": None,
            "awaiting_clarification": None,
            "turn_count": 0
        }
    return _SESSION_STORE[session_id]

def update_session_context(session_id: str, updates: Dict[str, Any]):
    ctx = get_session_context(session_id)
    ctx.update(updates)
    ctx["turn_count"] = ctx.get("turn_count", 0) + 1
    _SESSION_STORE[session_id] = ctx

def clear_session(session_id: str):
    if session_id in _SESSION_STORE:
        del _SESSION_STORE[session_id]
    
    # Also clear from SQLite for this session
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def save_conversation_turn(session_id: str, role: str, content: str, intent: Optional[str] = None, entities: Optional[Dict[str, Any]] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO conversations (session_id, role, content, intent, entities_json)
    VALUES (?, ?, ?, ?, ?)
    """, (session_id, role, content, intent, json.dumps(entities or {})))
    conn.commit()
    conn.close()

def get_conversation_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT role, content, intent, entities_json, timestamp 
    FROM conversations 
    WHERE session_id = ? 
    ORDER BY id ASC
    LIMIT ?
    """, (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        item = dict(r)
        try:
            item["entities"] = json.loads(item.get("entities_json") or "{}")
        except Exception:
            item["entities"] = {}
        history.append(item)
    return history
