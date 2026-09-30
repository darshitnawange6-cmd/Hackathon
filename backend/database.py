import sqlite3
import json
import os
from pathlib import Path
from backend.config import DATABASE_PATH, DATA_DIR

def get_db_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id TEXT PRIMARY KEY,
        subject TEXT NOT NULL,
        code TEXT NOT NULL,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        iso_date TEXT,
        time TEXT NOT NULL,
        duration TEXT,
        room TEXT NOT NULL,
        block TEXT NOT NULL,
        instructor TEXT NOT NULL,
        format TEXT,
        syllabus TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT NOT NULL,
        time TEXT NOT NULL,
        subject TEXT NOT NULL,
        code TEXT,
        room TEXT NOT NULL,
        instructor TEXT NOT NULL,
        type TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faculty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        office TEXT NOT NULL,
        office_hours TEXT NOT NULL,
        subjects TEXT NOT NULL,
        research TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classrooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        block TEXT NOT NULL,
        floor TEXT NOT NULL,
        capacity INTEGER,
        facilities TEXT,
        directions TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notices (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        priority TEXT NOT NULL,
        date TEXT NOT NULL,
        details TEXT NOT NULL,
        action TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        title TEXT NOT NULL,
        due_date TEXT NOT NULL,
        portal TEXT NOT NULL,
        weightage TEXT,
        notes TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        venue TEXT NOT NULL,
        organizer TEXT NOT NULL,
        highlights TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS library (
        key TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        timings TEXT NOT NULL,
        services TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        intent TEXT,
        entities_json TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        title TEXT NOT NULL,
        due_date TEXT,
        priority TEXT DEFAULT 'Normal',
        is_completed INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()


    # Check if seed data needs to be populated
    cursor.execute("SELECT COUNT(*) FROM exams;")
    exam_count = cursor.fetchone()[0]

    if exam_count == 0:
        seed_db(conn)

    conn.close()

def seed_db(conn):
    cursor = conn.cursor()
    json_path = DATA_DIR / "campus_knowledge.json"
    if not json_path.exists():
        print(f"Warning: Seed file not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Seed exams
    for ex in data.get("exams", []):
        cursor.execute("""
        INSERT INTO exams (id, subject, code, title, date, iso_date, time, duration, room, block, instructor, format, syllabus)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ex["id"], ex["subject"], ex["code"], ex["title"], ex["date"],
            ex.get("iso_date"), ex["time"], ex.get("duration"), ex["room"],
            ex["block"], ex["instructor"], ex.get("format"), ex.get("syllabus")
        ))

    # Seed timetable
    for day_item in data.get("timetable", []):
        day = day_item["day"]
        for slot in day_item.get("slots", []):
            cursor.execute("""
            INSERT INTO timetable (day, time, subject, code, room, instructor, type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                day, slot["time"], slot["subject"], slot.get("code"),
                slot["room"], slot["instructor"], slot.get("type", "Lecture")
            ))

    # Seed faculty
    for fac in data.get("faculty", []):
        cursor.execute("""
        INSERT INTO faculty (name, title, department, email, phone, office, office_hours, subjects, research)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fac["name"], fac["title"], fac["department"], fac["email"],
            fac.get("phone"), fac["office"], fac["office_hours"],
            json.dumps(fac.get("subjects", [])), fac.get("research")
        ))

    # Seed classrooms
    for cr in data.get("classrooms", []):
        cursor.execute("""
        INSERT INTO classrooms (name, block, floor, capacity, facilities, directions)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cr["name"], cr["block"], cr["floor"], cr.get("capacity"),
            json.dumps(cr.get("facilities", [])), cr["directions"]
        ))

    # Seed notices
    for noti in data.get("notices", []):
        cursor.execute("""
        INSERT INTO notices (id, title, category, priority, date, details, action)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            noti["id"], noti["title"], noti["category"], noti["priority"],
            noti["date"], noti["details"], noti.get("action")
        ))

    # Seed assignments
    for asn in data.get("assignments", []):
        cursor.execute("""
        INSERT INTO assignments (subject, title, due_date, portal, weightage, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            asn["subject"], asn["title"], asn["due_date"], asn["portal"],
            asn.get("weightage"), asn.get("notes")
        ))

    # Seed events
    for ev in data.get("events", []):
        cursor.execute("""
        INSERT INTO events (title, category, date, time, venue, organizer, highlights)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ev["title"], ev["category"], ev["date"], ev["time"],
            ev["venue"], ev["organizer"], ev.get("highlights")
        ))

    # Seed library
    lib = data.get("library", {})
    if lib:
        cursor.execute("""
        INSERT INTO library (key, title, content)
        VALUES (?, ?, ?)
        """, ("general", lib.get("name", "Central Library"), json.dumps(lib)))

    # Seed facilities
    for fac in data.get("facilities", []):
        cursor.execute("""
        INSERT INTO facilities (name, location, timings, services)
        VALUES (?, ?, ?, ?)
        """, (
            fac["name"], fac["location"], fac["timings"], fac["services"]
        ))

    conn.commit()
    print("Database successfully initialized and seeded with campus data.")
