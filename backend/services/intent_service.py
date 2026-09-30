import re
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

# Canonical subject aliases
SUBJECT_ALIASES = {
    "physics": "Physics",
    "phy": "Physics",
    "physics exam": "Physics",
    "electromagnetism": "Physics",
    "math": "Mathematics",
    "maths": "Mathematics",
    "mathematics": "Mathematics",
    "linear algebra": "Mathematics",
    "discrete math": "Mathematics",
    "data structures": "Data Structures",
    "dsa": "Data Structures",
    "algorithms": "Data Structures",
    "algo": "Data Structures",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "machine learning": "Artificial Intelligence",
    "aiml": "Artificial Intelligence",
    "deep learning": "Artificial Intelligence",
    "dbms": "Database Systems",
    "database": "Database Systems",
    "database systems": "Database Systems",
    "sql": "Database Systems",
    "networks": "Computer Networks",
    "computer networks": "Computer Networks"
}

DAYS_MAP = {
    "monday": "Monday",
    "mon": "Monday",
    "tuesday": "Tuesday",
    "tue": "Tuesday",
    "wednesday": "Wednesday",
    "wed": "Wednesday",
    "thursday": "Thursday",
    "thu": "Thursday",
    "friday": "Friday",
    "fri": "Friday",
    "today": "Today",
    "tomorrow": "Tomorrow"
}

FACULTY_KEYWORDS = {
    "elena": "Dr. Elena Vance",
    "vance": "Dr. Elena Vance",
    "rajesh": "Prof. Rajesh Sharma",
    "sharma": "Prof. Rajesh Sharma",
    "marcus": "Prof. Marcus Chen",
    "chen": "Prof. Marcus Chen",
    "jenkins": "Dr. Sarah Jenkins",
    "sarah": "Dr. Sarah Jenkins",
    "priyanshi": "Dr. Priyanshi Patel",
    "patel": "Dr. Priyanshi Patel",
    "turing": "Dr. Alan Turing"
}

ROOM_KEYWORDS = {
    "b-204": "Hall B-204",
    "b204": "Hall B-204",
    "c-102": "Hall C-102",
    "c102": "Hall C-102",
    "lab 301": "Lab 301",
    "b-205": "Hall B-205",
    "b205": "Hall B-205",
    "auditorium 1": "Auditorium 1",
    "audi 1": "Auditorium 1",
    "audi": "Auditorium 1"
}

def extract_entities(query: str) -> Dict[str, Any]:
    q = query.lower()
    entities: Dict[str, Any] = {}

    # Extract Subject
    for alias, canonical in SUBJECT_ALIASES.items():
        # Match whole words or phrase
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, q):
            entities["subject"] = canonical
            break

    # Extract Day
    for alias, canonical in DAYS_MAP.items():
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, q):
            if canonical == "Today":
                # Compute current weekday (e.g. Monday - Friday)
                weekday_name = datetime.now().strftime("%A")
                if weekday_name in ["Saturday", "Sunday"]:
                    weekday_name = "Monday"  # Fallback to Monday for demo if weekend
                entities["day"] = weekday_name
                entities["is_today"] = True
            elif canonical == "Tomorrow":
                entities["day"] = "Tuesday"
            else:
                entities["day"] = canonical
            break

    # Extract Faculty
    for key, name in FACULTY_KEYWORDS.items():
        if key in q:
            entities["faculty_name"] = name
            break

    # Extract Classroom / Room
    for key, room in ROOM_KEYWORDS.items():
        if key in q:
            entities["classroom"] = room
            break

    return entities

STANDARDIZED_INTENTS = {
    "exam_schedule": "EXAM_QUERY",
    "exam_requirements": "EXAM_QUERY",
    "exam_syllabus": "EXAM_QUERY",
    "show_upcoming_exams": "EXAM_QUERY",
    "timetable": "TIMETABLE_QUERY",
    "show_timetable": "TIMETABLE_QUERY",
    "notices_announcements": "NOTICE_QUERY",
    "show_notices": "NOTICE_QUERY",
    "faculty_info": "FACULTY_QUERY",
    "classroom_location": "LOCATION_QUERY",
    "assignment_deadline": "ASSIGNMENT_QUERY",
    "campus_events": "EVENT_QUERY",
    "library_info": "LIBRARY_QUERY",
    "campus_facilities": "LOCATION_QUERY",
    "create_reminder": "REMINDER_CREATE",
    "list_reminders": "REMINDER_CREATE",
    "college_policy_rag": "GENERAL_CONVERSATION",
    "greeting_or_help": "GENERAL_CONVERSATION",
    "general_campus": "GENERAL_CONVERSATION",
    "unknown": "UNKNOWN"
}

def get_standard_intent(raw_intent: str) -> str:
    return STANDARDIZED_INTENTS.get(raw_intent, "UNKNOWN")

def classify_intent(query: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, float, Dict[str, Any]]:
    """
    Classifies the user intent and extracts entities, taking into account
    conversational history context when available (resolves follow-ups, pronouns 'it'/'that'/'there').
    """
    q = query.strip().lower()
    entities = extract_entities(query)
    ctx = context or {}
    last_intent = ctx.get("last_intent")
    last_subject = ctx.get("last_subject")
    last_exam = ctx.get("last_exam")
    last_classroom = ctx.get("last_classroom")
    last_faculty = ctx.get("last_faculty")

    # 1. Follow-up short queries like "what about mathematics?" or "what about physics?"
    if re.search(r"^(what|how)\s+about\s+", q) or re.search(r"^and\s+", q):
        if "subject" in entities:
            target_intent = last_intent if last_intent in ["exam_schedule", "timetable", "assignment_deadline", "faculty_info"] else "exam_schedule"
            return target_intent, 0.96, entities

    # 2. Contextual follow-up: "where is it?", "where is that?", "how do i get there?", "which room?", "directions to it"
    if any(phrase in q for phrase in [
        "what classroom is it in", "which classroom", "where is it", "where is that",
        "where is it located", "which room", "where is the exam", "what room is it",
        "directions to it", "directions to that", "how do i get there", "how to reach there",
        "where is there"
    ]):
        if last_exam or last_subject or last_classroom:
            entities["subject"] = entities.get("subject") or last_subject
            entities["classroom"] = entities.get("classroom") or last_classroom
            entities["inherited_context"] = True
            return "classroom_location", 0.96, entities

    # 3. Contextual follow-up: "what do i need?", "what should i bring?", "what is allowed?", "what do i need for it?"
    if any(phrase in q for phrase in [
        "what do i need", "what should i bring", "what do i bring", "what is allowed",
        "what can i take", "what items are allowed", "what do i need to bring",
        "is calculator allowed", "are calculators allowed", "what to bring"
    ]):
        if last_exam or last_subject or last_intent in ["exam_schedule", "classroom_location"]:
            entities["subject"] = entities.get("subject") or last_subject
            entities["inherited_context"] = True
            return "exam_requirements", 0.96, entities

    # 4. Contextual follow-up: "what is the syllabus?", "what is covered?", "what's on it?", "what is on it?"
    if any(phrase in q for phrase in [
        "what is the syllabus", "what is covered", "what's on it", "what is on it",
        "syllabus for that", "topics covered", "what will be on it", "modules covered"
    ]):
        if last_exam or last_subject:
            entities["subject"] = entities.get("subject") or last_subject
            entities["inherited_context"] = True
            return "exam_syllabus", 0.96, entities

    # 5. Contextual follow-up: "who teaches it?", "who is that?", "who teaches this?", "who is the professor?"
    if any(phrase in q for phrase in ["who teaches it", "who teaches that", "who is the teacher", "who is the professor", "who teaches this", "who is that"]):
        if last_subject or last_faculty:
            entities["subject"] = entities.get("subject") or last_subject
            entities["faculty_name"] = entities.get("faculty_name") or last_faculty
            entities["inherited_context"] = True
            return "faculty_info", 0.95, entities

    # 6. Contextual follow-up: "what about tomorrow?", "classes tomorrow?", "schedule tomorrow?"
    if any(phrase in q for phrase in ["what about tomorrow", "schedule for tomorrow", "classes tomorrow", "what do i have tomorrow"]):
        entities["day"] = "Tomorrow"
        return "timetable", 0.95, entities

    # 7. Clarification answer (e.g. user previously asked "When is my exam?" and now responds just with "Physics" or "Math")
    if ctx.get("awaiting_clarification") == "subject" and "subject" in entities:
        return "exam_schedule", 0.98, entities

    # 8. College Policy / Rules / Handbook / Permission Intent
    if any(w in q for w in [
        "policy", "handbook", "rule", "rules", "curfew", "fine", "fines", "attendance",
        "debar", "condonation", "grading system", "grading scale", "dress code", "inspection"
    ]) or (any(w in q for w in ["can i", "are we allowed", "is it allowed", "is it permitted"]) and any(w in q for w in ["college", "campus", "hostel", "class", "exam", "lab", "attend", "dress", "leave", "phone", "calculator"])):
        return "college_policy_rag", 0.95, entities

    # 6. Exam Schedule Intent
    if any(re.search(r"\b" + re.escape(w) + r"\b", q) for w in ["exam", "exams", "midterm", "mid-term", "finals", "test", "tests", "examinations", "exam schedule"]):
        # Check if user asked generally "when is my exam" without subject
        return "exam_schedule", 0.95, entities

    # 6. Timetable / Daily Schedule
    if any(w in q for w in ["timetable", "schedule", "classes today", "class today", "lecture", "lectures", "routine", "what do i have today"]):
        return "timetable", 0.94, entities

    # 7. Classroom & Directions
    if "classroom" in entities or any(w in q for w in ["classroom", "where is hall", "where is lab", "where is audi", "how to reach", "directions to", "room location", "floor"]):
        return "classroom_location", 0.92, entities

    # 8. Faculty & Office Hours
    if "faculty_name" in entities or any(w in q for w in ["professor", "prof", "faculty", "teacher", "instructor", "office hours", "contact dr", "email dr", "teaches", "dr."]):
        return "faculty_info", 0.92, entities

    # 9. Assignment Deadlines
    if any(w in q for w in ["assignment", "homework", "deadline", "submission", "due date", "project report", "lab report"]):
        return "assignment_deadline", 0.93, entities

    # 10. Notices & Announcements
    if any(w in q for w in ["notice", "notices", "announcement", "circular", "bulletin", "updates", "urgent news"]):
        return "notices_announcements", 0.95, entities

    # 11. Campus Events & Hackathons
    if any(w in q for w in ["event", "events", "hackathon", "hacksphere", "fest", "workshop", "competition", "seminar"]):
        return "campus_events", 0.94, entities

    # 12. Library Info
    if any(w in q for w in ["library", "books", "borrow", "quiet zone", "library hours", "study lounge"]):
        return "library_info", 0.95, entities

    # 13. Campus Facilities (Food, Gym, Medical, Shuttle, ATM)
    if any(w in q for w in ["food", "cafeteria", "canteen", "eat", "gym", "sports", "medical", "doctor", "health", "hospital", "shuttle", "bus", "atm", "facilities"]):
        return "campus_facilities", 0.93, entities

    # 14. Greetings & Capabilities
    if any(re.search(r"\b" + re.escape(w) + r"\b", q) for w in ["hello", "hi", "hey", "help", "who are you", "what can you do", "vocaguide"]):
        return "greeting_or_help", 0.90, entities

    # Fallback to subject inquiry if a subject was mentioned
    if "subject" in entities:
        return "exam_schedule", 0.80, entities

    # General campus question
    campus_keywords = ["campus", "college", "university", "student", "faculty", "dean", "department", "admission", "fees", "scholarship", "housing", "hostel"]
    if any(w in q for w in campus_keywords):
        return "general_campus", 0.70, entities

    return "unknown", 0.30, entities
