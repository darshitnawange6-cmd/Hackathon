import json
import sqlite3
from typing import List, Dict, Any, Optional
from backend.database import get_db_connection, ensure_db_initialized
from backend.services.supabase_service import supabase_service

def _safe_sqlite_query(query_fn, default=None):
    """
    Executes a SQLite query with automatic schema initialization recovery.
    Prevents crashes if database tables were missing on a fresh container.
    """
    try:
        return query_fn()
    except sqlite3.OperationalError as e:
        print(f"[KnowledgeService] Database auto-recovery triggered: {e}")
        ensure_db_initialized()
        try:
            return query_fn()
        except Exception as e2:
            print(f"[KnowledgeService] Secondary query error: {e2}")
            return default if default is not None else []
    except Exception as e:
        print(f"[KnowledgeService] Query error: {e}")
        return default if default is not None else []

def query_exam(subject: Optional[str] = None) -> List[Dict[str, Any]]:
    # 1. Prioritize live Supabase knowledge base if connected
    if supabase_service.is_connected:
        supa_results = supabase_service.query_exams(subject)
        if supa_results:
            return supa_results

    # 2. Resilient fallback to SQLite database
    def _run():
        conn = get_db_connection()
        cursor = conn.cursor()
        if subject:
            cursor.execute("SELECT * FROM exams WHERE LOWER(subject) LIKE LOWER(?) OR LOWER(code) LIKE LOWER(?)", (f"%{subject}%", f"%{subject}%"))
        else:
            cursor.execute("SELECT * FROM exams ORDER BY iso_date ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    return _safe_sqlite_query(_run, default=[])

def query_timetable(day: Optional[str] = None, subject: Optional[str] = None) -> List[Dict[str, Any]]:
    # 1. Prioritize live Supabase knowledge base if connected
    if supabase_service.is_connected:
        supa_results = supabase_service.query_timetable(day=day, subject=subject)
        if supa_results:
            return supa_results

    # 2. Resilient fallback to SQLite database
    def _run():
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

    return _safe_sqlite_query(_run, default=[])

def query_faculty(name_or_subject: Optional[str] = None) -> List[Dict[str, Any]]:
    # 1. Prioritize live Supabase knowledge base if connected
    if supabase_service.is_connected:
        supa_results = supabase_service.query_faculty(name_or_subject)
        if supa_results:
            return supa_results

    # 2. Resilient fallback to SQLite database
    def _run():
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
                if isinstance(d.get("subjects"), str):
                    d["subjects"] = json.loads(d["subjects"])
            except Exception:
                pass
            results.append(d)
        return results

    return _safe_sqlite_query(_run, default=[])

def query_classroom(room_name: Optional[str] = None) -> List[Dict[str, Any]]:
    # 1. Prioritize live Supabase knowledge base if connected
    if supabase_service.is_connected:
        supa_results = supabase_service.query_classrooms(room_name)
        if supa_results:
            return supa_results

    # 2. Resilient fallback to SQLite database
    def _run():
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
                if isinstance(d.get("facilities"), str):
                    d["facilities"] = json.loads(d["facilities"])
            except Exception:
                pass
            results.append(d)
        return results

    return _safe_sqlite_query(_run, default=[])

def query_notices(category: Optional[str] = None) -> List[Dict[str, Any]]:
    # 1. Prioritize live Supabase knowledge base if connected
    if supabase_service.is_connected:
        supa_results = supabase_service.query_notices(category)
        if supa_results:
            return supa_results

    # 2. Resilient fallback to SQLite database
    def _run():
        conn = get_db_connection()
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM notices WHERE LOWER(category) LIKE LOWER(?) ORDER BY date DESC", (f"%{category}%",))
        else:
            cursor.execute("SELECT * FROM notices ORDER BY priority = 'High' DESC, date DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    return _safe_sqlite_query(_run, default=[])

def query_assignments(subject: Optional[str] = None) -> List[Dict[str, Any]]:
    # 1. Prioritize live Supabase knowledge base if connected
    if supabase_service.is_connected:
        supa_results = supabase_service.query_assignments(subject)
        if supa_results:
            return supa_results

    # 2. Resilient fallback to SQLite database
    def _run():
        conn = get_db_connection()
        cursor = conn.cursor()
        if subject:
            cursor.execute("SELECT * FROM assignments WHERE LOWER(subject) LIKE LOWER(?)", (f"%{subject}%",))
        else:
            cursor.execute("SELECT * FROM assignments ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    return _safe_sqlite_query(_run, default=[])

def query_events() -> List[Dict[str, Any]]:
    # 1. Prioritize live Supabase knowledge base if connected
    if supabase_service.is_connected:
        supa_results = supabase_service.query_events()
        if supa_results:
            return supa_results

    # 2. Resilient fallback to SQLite database
    def _run():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    return _safe_sqlite_query(_run, default=[])

def query_library() -> Dict[str, Any]:
    def _run():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM library WHERE key = 'general'")
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row["content"])
        return {}

    return _safe_sqlite_query(_run, default={})

def query_facilities(name: Optional[str] = None) -> List[Dict[str, Any]]:
    # 1. Prioritize live Supabase knowledge base if connected
    if supabase_service.is_connected:
        supa_results = supabase_service.query_facilities(name)
        if supa_results:
            return supa_results

    # 2. Resilient fallback to SQLite database
    def _run():
        conn = get_db_connection()
        cursor = conn.cursor()
        if name:
            cursor.execute("SELECT * FROM facilities WHERE LOWER(name) LIKE LOWER(?) OR LOWER(services) LIKE LOWER(?)", (f"%{name}%", f"%{name}%"))
        else:
            cursor.execute("SELECT * FROM facilities")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    return _safe_sqlite_query(_run, default=[])
