import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.database import get_db_connection
from backend.services import knowledge_service
from backend.services.rag_service import rag_service

class ActionTool:
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters

    def execute(self, params: Dict[str, Any], session_id: str = "default-student-session") -> Dict[str, Any]:
        raise NotImplementedError

class SearchCollegeInfoAction(ActionTool):
    def __init__(self):
        super().__init__(
            name="search_college_info",
            description="Searches campus knowledge base, official handbooks, syllabi, rules, and notices.",
            parameters={"query": "string (the search topic or question)"}
        )

    def execute(self, params: Dict[str, Any], session_id: str = "default-student-session") -> Dict[str, Any]:
        query = params.get("query", "")
        rag_res = rag_service.retrieve(query, top_k=3)
        return {
            "success": True,
            "action": "search_college_info",
            "found": rag_res["found"],
            "sources": rag_res["sources"],
            "primary_source": rag_res["primary_source"],
            "chunks": rag_res["chunks"]
        }

class ShowTimetableAction(ActionTool):
    def __init__(self):
        super().__init__(
            name="show_timetable",
            description="Retrieves class lecture and lab slots for a specific day or subject.",
            parameters={"day": "string (e.g. Monday, Tuesday, Today)", "subject": "optional string"}
        )

    def execute(self, params: Dict[str, Any], session_id: str = "default-student-session") -> Dict[str, Any]:
        day = params.get("day") or "Monday"
        if day.lower() == "today":
            day = datetime.now().strftime("%A")
            if day in ["Saturday", "Sunday"]:
                day = "Monday"
        slots = knowledge_service.query_timetable(day=day, subject=params.get("subject"))
        return {
            "success": True,
            "action": "show_timetable",
            "day": day,
            "slots": slots,
            "count": len(slots)
        }

class ShowUpcomingExamsAction(ActionTool):
    def __init__(self):
        super().__init__(
            name="show_upcoming_exams",
            description="Retrieves the official midterm or endterm examination schedule.",
            parameters={"subject": "optional string"}
        )

    def execute(self, params: Dict[str, Any], session_id: str = "default-student-session") -> Dict[str, Any]:
        subject = params.get("subject")
        exams = knowledge_service.query_exam(subject=subject)
        return {
            "success": True,
            "action": "show_upcoming_exams",
            "subject": subject,
            "exams": exams,
            "count": len(exams)
        }

from backend.services.supabase_service import supabase_service

class CreateReminderAction(ActionTool):
    def __init__(self):
        super().__init__(
            name="create_reminder",
            description="Saves a personal task, study deadline, or alert for the student.",
            parameters={
                "title": "string (the task to remember)",
                "due_date": "optional string",
                "priority": "optional string (High, Normal, Low)"
            }
        )

    def execute(self, params: Dict[str, Any], session_id: str = "default-student-session") -> Dict[str, Any]:
        title = params.get("title", "").strip()
        due_date = params.get("due_date", "Pending date").strip()
        priority = params.get("priority", "Normal").capitalize()

        if not title:
            return {"success": False, "error": "Reminder title cannot be empty."}

        # Save to local SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO reminders (session_id, title, due_date, priority)
        VALUES (?, ?, ?, ?)
        """, (session_id, title, due_date, priority))
        conn.commit()
        reminder_id = cursor.lastrowid
        conn.close()

        # Dual save to Supabase
        if supabase_service.is_connected:
            try:
                supabase_service.create_reminder(session_id, title, due_date, priority)
            except Exception as e:
                print(f"[ActionService] Supabase reminder error: {e}")

        return {
            "success": True,
            "action": "create_reminder",
            "reminder_id": reminder_id,
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "message": f"Reminder set: '{title}' for {due_date}."
        }

class ListRemindersAction(ActionTool):
    def __init__(self):
        super().__init__(
            name="list_reminders",
            description="Lists all saved reminders for the current student session.",
            parameters={}
        )

    def execute(self, params: Dict[str, Any], session_id: str = "default-student-session") -> Dict[str, Any]:
        if supabase_service.is_connected:
            try:
                sb_rems = supabase_service.list_reminders(session_id)
                if sb_rems:
                    return {
                        "success": True,
                        "action": "list_reminders",
                        "reminders": sb_rems,
                        "count": len(sb_rems)
                    }
            except Exception:
                pass

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, title, due_date, priority, is_completed, created_at
        FROM reminders
        WHERE session_id = ?
        ORDER BY id DESC
        """, (session_id,))
        rows = cursor.fetchall()
        conn.close()
        return {
            "success": True,
            "action": "list_reminders",
            "reminders": [dict(r) for r in rows],
            "count": len(rows)
        }

class ShowNoticesAction(ActionTool):
    def __init__(self):
        super().__init__(
            name="show_notices",
            description="Retrieves official campus announcements, urgent circulars, and bulletins.",
            parameters={"category": "optional string"}
        )

    def execute(self, params: Dict[str, Any], session_id: str = "default-student-session") -> Dict[str, Any]:
        notices = knowledge_service.query_notices(category=params.get("category"))
        return {
            "success": True,
            "action": "show_notices",
            "notices": notices,
            "count": len(notices)
        }

class ActionRegistry:
    def __init__(self):
        self.tools: Dict[str, ActionTool] = {}
        self.register(SearchCollegeInfoAction())
        self.register(ShowTimetableAction())
        self.register(ShowUpcomingExamsAction())
        self.register(CreateReminderAction())
        self.register(ListRemindersAction())
        self.register(ShowNoticesAction())

    def register(self, tool: ActionTool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ActionTool]:
        return self.tools.get(name)

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters
            }
            for t in self.tools.values()
        ]

    def detect_action(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        q = query.strip().lower()
        ctx = context or {}
        last_subject = ctx.get("last_subject")
        last_exam = ctx.get("last_exam")

        # 1. Bare Reminder: "remind me tomorrow", "remind me tomorrow.", "remind me next week"
        bare_remind_match = re.search(r"^remind\s+me(?:\s+(tomorrow|next week|later|today|on \w+|at \d+\w*))?[\.\?!]?$", q)
        if bare_remind_match:
            due = bare_remind_match.group(1) or "Tomorrow"
            subj = last_subject or (last_exam["subject"] if last_exam else "Coursework")
            task = f"{subj} Exam" if (last_exam or "exam" in str(last_subject).lower()) else f"{subj} Task"
            return {
                "name": "create_reminder",
                "params": {"title": task.capitalize(), "due_date": due.capitalize(), "priority": "High" if last_exam else "Normal"}
            }

        # 2. Reminder: "remind me tomorrow about my physics exam" or "remind me about that tomorrow"
        remind_about_match = re.search(r"remind\s+me\s+(?:(tomorrow|next week|on \w+|at \d+\w*)\s+)?about\s+(.+?)(?:\s+(tomorrow|next week|on \w+))?$", q)
        if remind_about_match:
            due = remind_about_match.group(1) or remind_about_match.group(3) or "Tomorrow"
            task = remind_about_match.group(2).strip()
            # Pronoun resolution: "that" / "it" / "this"
            if task in ["that", "it", "the exam", "this", "my exam"]:
                subj = last_subject or (last_exam["subject"] if last_exam else "Upcoming")
                task = f"{subj} Exam"
            return {
                "name": "create_reminder",
                "params": {"title": task.capitalize(), "due_date": due.capitalize(), "priority": "High" if "exam" in q or "urgent" in q else "Normal"}
            }

        # 2. Reminder: "remind me to submit physics lab report on friday"
        reminder_match = re.search(r"remind\s+me\s+to\s+(.+?)(?:\s+(?:by|on|at|before)\s+(.+))?$", q)
        if reminder_match:
            task = reminder_match.group(1).strip()
            due = reminder_match.group(2).strip() if reminder_match.group(2) else "Upcoming"
            if task in ["do that", "review that", "submit that", "study that"]:
                subj = last_subject or "Coursework"
                task = f"{subj} Review"
            return {
                "name": "create_reminder",
                "params": {"title": task.capitalize(), "due_date": due.capitalize(), "priority": "High" if "exam" in q or "urgent" in q else "Normal"}
            }

        # 3. List reminders
        if any(w in q for w in ["my reminders", "show reminders", "list reminders", "what are my reminders", "view reminders"]):
            return {"name": "list_reminders", "params": {}}

        # 4. Show timetable action
        if any(w in q for w in ["show timetable", "today's timetable", "timetable for today", "classes today"]):
            return {"name": "show_timetable", "params": {"day": "Today"}}

        if "timetable for tomorrow" in q or "tomorrow's timetable" in q:
            return {"name": "show_timetable", "params": {"day": "Tomorrow"}}

        # 5. Show exams action
        if any(w in q for w in ["show upcoming exams", "upcoming exams", "all exams", "show exam schedule"]):
            return {"name": "show_upcoming_exams", "params": {}}

        # 6. Show notices action
        if any(w in q for w in ["show notices", "latest notices", "show announcements", "campus circulars", "campus notices", "college notices"]):
            return {"name": "show_notices", "params": {}}

        return None

action_registry = ActionRegistry()
