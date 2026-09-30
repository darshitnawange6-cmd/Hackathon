import json
from typing import List, Dict, Any, Optional
from backend.database import get_db_connection

def query_exam(subject: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if subject:
        cursor.execute("SELECT * FROM exams WHERE LOWER(subject) LIKE LOWER(?) OR LOWER(code) LIKE LOWER(?)", (f"%{subject}%", f"%{subject}%"))
    else:
        cursor.execute("SELECT * FROM exams ORDER BY iso_date ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def query_timetable(day: Optional[str] = None, subject: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if day and subject:
        cursor.execute("SELECT * FROM timetable WHERE LOWER(day) = LOWER(?) AND LOWER(subject) LIKE LOWER(?)", (day, f"%{subject}%"))
    elif day:
        cursor.execute("SELECT * FROM timetable WHERE LOWER(day) = LOWER(?) ORDER BY id ASC", (day,))
    elif subject:
        cursor.execute("SELECT * FROM timetable WHERE LOWER(subject) LIKE LOWER(?) ORDER BY id ASC", (f"%{subject}%",))
    else:
        cursor.execute("SELECT * FROM timetable ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def query_faculty(name_or_subject: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if name_or_subject:
        cursor.execute("""
        SELECT * FROM faculty 
        WHERE LOWER(name) LIKE LOWER(?) 
           OR LOWER(subjects) LIKE LOWER(?)
           OR LOWER(department) LIKE LOWER(?)
        """, (f"%{name_or_subject}%", f"%{name_or_subject}%", f"%{name_or_subject}%"))
    else:
        cursor.execute("SELECT * FROM faculty")
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        try:
            d["subjects"] = json.loads(d["subjects"])
        except Exception:
            pass
        results.append(d)
    return results

def query_classroom(room_name: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if room_name:
        cursor.execute("SELECT * FROM classrooms WHERE LOWER(name) LIKE LOWER(?) OR LOWER(block) LIKE LOWER(?)", (f"%{room_name}%", f"%{room_name}%"))
    else:
        cursor.execute("SELECT * FROM classrooms")
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        try:
            d["facilities"] = json.loads(d["facilities"])
        except Exception:
            pass
        results.append(d)
    return results

def query_notices(category: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT * FROM notices WHERE LOWER(category) LIKE LOWER(?) ORDER BY date DESC", (f"%{category}%",))
    else:
        cursor.execute("SELECT * FROM notices ORDER BY priority = 'High' DESC, date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def query_assignments(subject: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if subject:
        cursor.execute("SELECT * FROM assignments WHERE LOWER(subject) LIKE LOWER(?)", (f"%{subject}%",))
    else:
        cursor.execute("SELECT * FROM assignments ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def query_events() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def query_library() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM library WHERE key = 'general'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["content"])
    return {}

def query_facilities(name: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if name:
        cursor.execute("SELECT * FROM facilities WHERE LOWER(name) LIKE LOWER(?) OR LOWER(services) LIKE LOWER(?)", (f"%{name}%", f"%{name}%"))
    else:
        cursor.execute("SELECT * FROM facilities")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
