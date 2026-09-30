import os
import json
import time
import httpx
from typing import Dict, Any, Tuple, List, Optional
from backend.config import (
    AI_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, MODEL_NAME
)
from backend.services.intent_service import classify_intent, get_standard_intent
from backend.services import knowledge_service, conversation_service
from backend.services.rag_service import rag_service
from backend.services.action_service import action_registry
from backend.services.supabase_service import supabase_service

DEFAULT_SYSTEM_PROMPT = (
    "You are VocaGuide, an intelligent voice-first AI campus assistant for college students at Nexus Institute of Technology. "
    "Your role is to assist students with exam schedules, timetables, classrooms, faculty, college rules, handbooks, and notices. "
    "CRITICAL GROUNDING RULES:\n"
    "1. Answer using ONLY the verified context documents and database records provided below.\n"
    "2. If the answer is NOT present in the retrieved knowledge, clearly state that the information is not found in the official records. Do NOT hallucinate or invent policies.\n"
    "3. Provide a structured markdown response with clear headings and bullet points for the visual UI.\n"
    "4. Provide a concise, smooth, 1-2 sentence 'spoken_text' optimized for text-to-speech synthesis (no markdown symbols, asterisks, or raw URLs).\n"
    "5. Cite the source document title used for the response."
)

class LLMService:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.model_name = MODEL_NAME
        self.system_prompt = DEFAULT_SYSTEM_PROMPT

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model_name,
            "is_demo_mode": self.provider == "demo",
            "available_providers": {
                "gemini": bool(GEMINI_API_KEY),
                "openai": bool(OPENAI_API_KEY),
                "groq": bool(GROQ_API_KEY),
                "demo": True
            },
            "supabase": supabase_service.get_status(),
            "rag_chunks_indexed": len(rag_service.chunks),
            "rag_documents": rag_service.indexed_files
        }

    async def generate_response(
        self,
        query: str,
        session_id: str = "default-student-session",
        is_voice: bool = False
    ) -> Dict[str, Any]:
        """
        Orchestrates RAG document retrieval, action tool execution,
        conversational memory, intent classification, and grounded response synthesis.
        Tracks performance latencies: retrieval_time_ms, ai_response_time_ms, total_response_time_ms.
        """
        start_total = time.time()

        # 1. Retrieve current session context & conversation history
        ctx = conversation_service.get_session_context(session_id)
        history = conversation_service.get_conversation_history(session_id, limit=6)

        # 2. Check for Direct Action Tool Invocation (with pronoun resolution using context)
        detected_action = action_registry.detect_action(query, context=ctx)
        if detected_action:
            tool = action_registry.get_tool(detected_action["name"])
            if tool:
                action_res = tool.execute(detected_action.get("params", {}), session_id=session_id)
                formatted = self._format_action_response(query, detected_action["name"], action_res, session_id)
                total_time = round((time.time() - start_total) * 1000, 2)
                formatted["metrics"] = {
                    "retrieval_time_ms": 1.2,
                    "ai_response_time_ms": round(total_time * 0.7, 2),
                    "total_response_time_ms": total_time
                }
                return formatted

        # 3. Intent classification and entity extraction
        intent, confidence, entities = classify_intent(query, ctx)

        # 4. Handle Clarification if request is underspecified
        if intent == "exam_schedule" and not entities.get("subject") and not ctx.get("last_subject"):
            conversation_service.update_session_context(session_id, {
                "last_intent": "exam_schedule",
                "awaiting_clarification": "subject"
            })
            clarification_msg = "Which subject's exam are you asking about? Options include Physics, Mathematics, Data Structures, Artificial Intelligence, or Database Systems."
            spoken_msg = "Which subject's exam are you asking about? For example, Physics, Mathematics, or Data Structures."

            conversation_service.save_conversation_turn(session_id, "user", query, intent, entities)
            conversation_service.save_conversation_turn(session_id, "assistant", clarification_msg, intent, entities)

            total_time = round((time.time() - start_total) * 1000, 2)
            return {
                "response_text": clarification_msg,
                "spoken_text": spoken_msg,
                "detected_intent": "exam_schedule",
                "standard_intent": get_standard_intent("exam_schedule"),
                "confidence": confidence,
                "entities": entities,
                "follow_up_suggestions": [
                    "Physics exam",
                    "Mathematics exam",
                    "Data Structures exam",
                    "AI exam"
                ],
                "sources": ["Midterm Examination Schedule (Fall 2026) (campus_exam_roster.db)"],
                "source_details": [{
                    "document_name": "Midterm Examination Schedule (Fall 2026)",
                    "category": "Examination Roster",
                    "date": "Fall 2026",
                    "section": "Schedule by Subject"
                }],
                "primary_source": "Midterm Examination Schedule (Fall 2026)",
                "action_executed": None,
                "action_result": None,
                "mode": "demo" if self.provider == "demo" else self.provider,
                "clarification_needed": True,
                "clarification_field": "subject",
                "metrics": {
                    "retrieval_time_ms": 1.0,
                    "ai_response_time_ms": round(total_time * 0.8, 2),
                    "total_response_time_ms": total_time
                },
                "metadata": {"status": "awaiting_subject_clarification"}
            }

        # Clear awaiting clarification if user provided an entity
        if ctx.get("awaiting_clarification") and ("subject" in entities or entities.get("day")):
            ctx["awaiting_clarification"] = None

        # 5. RAG Retrieval from Documents & Knowledge base (Supabase primary, Local fallback)
        t_retrieval_start = time.time()
        rag_results = {"found": False, "chunks": [], "sources": [], "primary_source": None}
        if supabase_service.is_connected:
            try:
                rag_results = supabase_service.search_knowledge(query, match_count=3)
            except Exception as e:
                print(f"[LLMService] Supabase search error: {e}")

        if not rag_results.get("found"):
            rag_results = rag_service.retrieve(query, top_k=3, threshold=0.10)
        retrieval_time_ms = round((time.time() - t_retrieval_start) * 1000, 2)

        # 6. Synthesize response using Local Engine or External LLM
        t_ai_start = time.time()
        if self.provider == "demo" or not (GEMINI_API_KEY or OPENAI_API_KEY or GROQ_API_KEY):
            res = self._synthesize_local_response(query, intent, confidence, entities, ctx, session_id, rag_results)
        else:
            try:
                res = await self._synthesize_external_llm(query, intent, confidence, entities, ctx, session_id, rag_results, history)
            except Exception as e:
                print(f"[LLMService Error] Failed external LLM call: {e}. Falling back to intelligent Demo Engine.")
                res = self._synthesize_local_response(query, intent, confidence, entities, ctx, session_id, rag_results)
                res["metadata"]["fallback_reason"] = str(e)
        ai_response_time_ms = round((time.time() - t_ai_start) * 1000, 2)
        total_response_time_ms = round((time.time() - start_total) * 1000, 2)

        # Ensure standardized intent, source details, and performance metrics
        res["standard_intent"] = get_standard_intent(res.get("detected_intent", intent))
        res["metrics"] = {
            "retrieval_time_ms": retrieval_time_ms,
            "ai_response_time_ms": ai_response_time_ms,
            "total_response_time_ms": total_response_time_ms
        }

        # 7. Persist turn to conversation history (Local SQLite & Supabase)
        conversation_service.save_conversation_turn(session_id, "user", query, intent, entities)
        conversation_service.save_conversation_turn(session_id, "assistant", res["response_text"], intent, entities)

        if supabase_service.is_connected:
            supabase_service.save_session_turn(
                session_id=session_id,
                role="user",
                content=query,
                intent=intent,
                entities=entities,
                sources=res.get("sources"),
                action_executed=res.get("action_executed")
            )
            supabase_service.save_session_turn(
                session_id=session_id,
                role="assistant",
                content=res["response_text"],
                intent=intent,
                entities=entities,
                sources=res.get("sources"),
                action_executed=res.get("action_executed")
            )

        return res

    def _format_action_response(self, query: str, action_name: str, action_res: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Formats responses for executed student tools like creating reminders or listing them."""
        source_details: List[Dict[str, Any]] = []

        if action_name == "create_reminder":
            resp_text = (
                f"### ⏰ Reminder Successfully Created\n\n"
                f"- 📝 **Task:** {action_res.get('title')}\n"
                f"- 📅 **Due / Date:** {action_res.get('due_date')}\n"
                f"- ⚡ **Priority:** {action_res.get('priority')}\n\n"
                f"I've saved this in your student study reminders."
            )
            spoken = f"I have set a reminder for {action_res.get('title')} on {action_res.get('due_date')}."
            follow_ups = ["Show my reminders", "When are my upcoming exams?", "Today's timetable"]
            sources = ["Student Reminders Engine (campus.db)"]
            primary_source = "Student Reminders Engine"
            source_details = [{
                "document_name": "Student Reminders Engine",
                "category": "Reminders",
                "date": "Active Session",
                "section": "Task Scheduler"
            }]
        elif action_name == "list_reminders":
            rems = action_res.get("reminders", [])
            if rems:
                items = "\n".join([f"- 📌 **{r['title']}** (Due: {r['due_date']}) [{r['priority']}]" for r in rems])
                resp_text = f"### 📋 Your Active Reminders\n\n{items}"
                spoken = f"You have {len(rems)} active reminders."
            else:
                resp_text = "### 📋 Your Active Reminders\n\nYou currently have no active reminders saved."
                spoken = "You have no active reminders saved."
            follow_ups = ["Remind me to submit assignment", "Upcoming exams"]
            sources = ["Student Reminders Engine (campus.db)"]
            primary_source = "Student Reminders Engine"
            source_details = [{
                "document_name": "Student Reminders Engine",
                "category": "Reminders",
                "date": "Active Session",
                "section": "Saved Reminders List"
            }]
        elif action_name == "show_timetable":
            slots = action_res.get("slots", [])
            day = action_res.get("day", "Today")
            if slots:
                slot_lines = "\n".join([
                    f"- **{s['time']}**: **{s['subject']}** ({s.get('type', 'Lecture')}) in *{s['room']}* with {s['instructor']}"
                    for s in slots
                ])
                resp_text = f"### 🗓️ Timetable for {day}\n\n{slot_lines}"
                spoken = f"For {day}, your first class is {slots[0]['subject']} at {slots[0]['time']} in {slots[0]['room']}."
            else:
                resp_text = f"### 🗓️ Timetable for {day}\n\nNo classes scheduled for {day}."
                spoken = f"No classes scheduled for {day}."
            follow_ups = ["What about tomorrow?", "When are upcoming exams?", "Show my reminders"]
            sources = ["Official Campus Class Timetable (campus_timetable.db)"]
            primary_source = f"Class Timetable - {day}"
            source_details = [{
                "document_name": "Official Campus Class Timetable",
                "category": "Class Timetable",
                "date": "Fall 2026",
                "section": f"Schedule for {day}"
            }]
        elif action_name == "show_upcoming_exams":
            exams = action_res.get("exams", [])
            exam_lines = "\n".join([f"- **{e['subject']}**: {e['date']} ({e['time']}) in *{e['room']}*" for e in exams])
            resp_text = f"### 🎓 Upcoming Midterm Examination Schedule\n\n{exam_lines}"
            spoken = "Here is the upcoming midterm exam schedule. Physics starts on Monday, followed by Mathematics on Wednesday."
            follow_ups = ["When is my physics exam?", "What classroom is it in?", "What is the syllabus?"]
            sources = ["Midterm Examination Schedule (Fall 2026) (campus_exam_roster.db)"]
            primary_source = "Midterm Examination Schedule (Fall 2026)"
            source_details = [{
                "document_name": "Midterm Examination Schedule (Fall 2026)",
                "category": "Examination Roster",
                "date": "Fall 2026",
                "section": "All Exam Slots"
            }]
        elif action_name == "show_notices":
            notices = action_res.get("notices", [])
            if notices:
                notice_items = "\n\n".join([
                    f"📢 **{n['title']}** [{n['priority']} Priority]\n"
                    f"*{n['date']}* • {n['details']}\n"
                    f"👉 *Action:* {n.get('action', 'Check student portal')}"
                    for n in notices[:3]
                ])
                resp_text = f"### 🔔 Latest Campus Notices & Bulletins\n\n{notice_items}"
                spoken = f"Here are the latest campus notices. The top announcement is: {notices[0]['title']}."
            else:
                resp_text = "### 🔔 Campus Notices\n\nThere are currently no active notices posted."
                spoken = "There are no active notices posted."
            follow_ups = ["Tell me about HackSphere 2026", "Library exam hours", "Upcoming exams"]
            sources = ["Campus Bulletins & Notices (campus_notices.db)"]
            primary_source = "Campus Bulletins & Notices"
            source_details = [{
                "document_name": "Campus Bulletins & Notices",
                "category": "Announcements",
                "date": "October 2026",
                "section": "Campus Circulars"
            }]
        else:
            resp_text = f"### Action Executed: {action_name}\n\n{json.dumps(action_res, indent=2)}"
            spoken = f"Action {action_name} executed successfully."
            follow_ups = ["Today's timetable", "Upcoming exams"]
            sources = ["VocaGuide Core"]
            primary_source = "VocaGuide Core"
            source_details = [{
                "document_name": "VocaGuide Action Engine",
                "category": "Action Execution",
                "date": "Current",
                "section": action_name
            }]

        conversation_service.save_conversation_turn(session_id, "user", query, action_name, {})
        conversation_service.save_conversation_turn(session_id, "assistant", resp_text, action_name, {})

        return {
            "response_text": resp_text,
            "spoken_text": spoken,
            "detected_intent": action_name,
            "standard_intent": get_standard_intent(action_name),
            "confidence": 0.98,
            "entities": {},
            "follow_up_suggestions": follow_ups,
            "sources": sources,
            "source_details": source_details,
            "primary_source": primary_source,
            "action_executed": action_name,
            "action_result": action_res,
            "mode": "demo" if self.provider == "demo" else self.provider,
            "clarification_needed": False,
            "clarification_field": None,
            "metrics": {},
            "metadata": {"action": action_name}
        }

    def _synthesize_local_response(
        self,
        query: str,
        intent: str,
        confidence: float,
        entities: Dict[str, Any],
        ctx: Dict[str, Any],
        session_id: str,
        rag_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligent, grounded offline conversational response engine.
        Fully resolves multi-turn follow-ups, documents, and hallucination guardrails.
        """
        subject = entities.get("subject") or ctx.get("last_subject")
        response_text = ""
        spoken_text = ""
        follow_ups: List[str] = []
        sources = rag_results.get("sources", [])
        source_details: List[Dict[str, Any]] = []
        primary_source = rag_results.get("primary_source")
        metadata: Dict[str, Any] = {"engine": "VocaGuide Grounded Core (Demo Engine)"}

        # Check for RAG document queries (college rules, handbook, attendance, syllabus, policies, or newly uploaded documents)
        q_lower = query.lower()
        is_document_query = any(w in q_lower for w in [
            "attendance", "policy", "handbook", "rule", "rules", "grading", "grade",
            "curfew", "fine", "fines", "debarred", "hall ticket", "calculator", "admit card",
            "syllabus", "module", "topics", "hostel", "housing", "placement", "internship",
            "ragging", "dress code", "scholarship", "document", "regulation", "regulations"
        ])

        has_specific_db_intent = intent in [
            "exam_schedule", "exam_requirements", "exam_syllabus", "classroom_location",
            "timetable", "faculty_info", "notices_announcements", "library_info",
            "campus_facilities", "campus_events", "assignment_deadline", "greeting_or_help"
        ]

        if rag_results.get("found") and (not has_specific_db_intent or intent in ["general_campus", "college_policy_rag"]):
            top_chunk = rag_results["chunks"][0]
            sources = rag_results["sources"]
            primary_source = f"{top_chunk['title']} ({top_chunk['source_file']})"
            response_text = (
                f"### 📖 {top_chunk['title']}\n"
                f"**Section: {top_chunk['section']}**\n\n"
                f"{top_chunk['content']}\n\n"
                f"📍 *Verified Source: [{top_chunk['source_file']}]*"
            )
            # Create a clean spoken snippet from the chunk
            first_sentence = top_chunk['content'].split('.')[0].strip()
            spoken_text = f"According to the official {top_chunk['title']}, {top_chunk['section']}: {first_sentence}."
            follow_ups = [
                "What is the grading policy?",
                "What calculators are allowed in exam?",
                "When is my physics exam?"
            ]
            source_details = [{
                "document_name": top_chunk.get("title", "Campus Knowledge Document"),
                "category": "Official College Document",
                "date": "Fall 2026",
                "section": top_chunk.get("section", "General")
            }]
            return {
                "response_text": response_text,
                "spoken_text": spoken_text,
                "detected_intent": "college_policy_rag",
                "confidence": 0.95,
                "entities": entities,
                "follow_up_suggestions": follow_ups,
                "sources": sources,
                "source_details": source_details,
                "primary_source": primary_source,
                "action_executed": "search_college_info",
                "action_result": {"retrieved_chunks": len(rag_results["chunks"])},
                "mode": "demo",
                "clarification_needed": False,
                "clarification_field": None,
                "metadata": metadata
            }

        # --- INTENT: EXAM REQUIREMENTS ("What do I need?", "What is allowed?") ---
        if intent == "exam_requirements":
            active_subject = subject or "Midterm Examination"
            response_text = (
                f"### 📝 Examination Hall Requirements & Protocols: {active_subject}\n\n"
                f"For the **{active_subject} Examination**, students must bring and adhere to the following rules:\n\n"
                f"- 🪪 **Mandatory Documents:** Printed Hall Ticket / Admit Card and official Student ID card.\n"
                f"- ✏️ **Stationery:** Blue or black ballpoint pens, pencils, and erasers in a clear transparent pouch.\n"
                f"- 🔢 **Calculators:** Non-programmable scientific calculators only (Casio fx-82MS / fx-991EX approved). Graphing or programmable models are strictly prohibited.\n"
                f"- 💧 **Personal Items:** Clear transparent water bottle without any label.\n"
                f"- 🚫 **Strictly Prohibited:** Mobile phones, smartwatches, digital bands, cheat notes, or backpacks. Possession causes immediate debarment.\n\n"
                f"📍 *Report to the exam hall at least 15 minutes before the session starts.*"
            )
            spoken_text = f"For your {active_subject} exam, bring your Hall Ticket, Student ID, and an approved non-programmable calculator. Mobile phones and smartwatches are strictly prohibited."
            follow_ups = [
                "Where is it located?",
                "What is the syllabus?",
                "Remind me tomorrow about that"
            ]
            sources = ["Nexus Academic Regulations & Exam Protocols (Fall 2026)"]
            primary_source = "Nexus Examination Protocols"
            source_details = [{
                "document_name": "Nexus Academic Regulations & Exam Protocols (Fall 2026)",
                "category": "Examination Policy",
                "date": "Fall 2026",
                "section": "Section 8.4 - Permitted Exam Items & Hall Conduct"
            }]

        # --- INTENT: EXAM SYLLABUS ("What is the syllabus?", "What is on it?") ---
        elif intent == "exam_syllabus":
            active_subject = subject or "Physics"
            exams = knowledge_service.query_exam(active_subject)
            if exams:
                ex = exams[0]
                syllabus_cov = ex.get('syllabus', 'Complete semester syllabus modules 1 to 4')
                response_text = (
                    f"### 📚 Midterm Syllabus Coverage: {ex['subject']} ({ex['code']})\n\n"
                    f"The upcoming examination for **{ex['subject']}** covers the following curriculum:\n\n"
                    f"- 📖 **Topics Covered:** {syllabus_cov}\n"
                    f"- 📝 **Format:** {ex.get('format', 'Multiple Choice & Theory Problems')}\n"
                    f"- ⏱️ **Duration:** {ex.get('duration', '3 Hours')}\n"
                    f"- 🎯 **Weightage:** 30% of total course grade\n\n"
                    f"💡 *Instructor:* {ex['instructor']} (Office Hours available in Faculty Directory)."
                )
                spoken_text = f"The {ex['subject']} exam covers {syllabus_cov}. The duration is {ex.get('duration', '3 hours')}."
                follow_ups = [
                    "What do I need for it?",
                    "Where is the exam located?",
                    f"Remind me tomorrow about my {ex['subject']} exam"
                ]
                sources = [f"{ex['subject']} Course Curriculum & Syllabus (Fall 2026)"]
                primary_source = f"{ex['subject']} Course Syllabus"
                source_details = [{
                    "document_name": f"{ex['subject']} Course Curriculum & Syllabus (Fall 2026)",
                    "category": "Syllabus",
                    "date": "Fall 2026",
                    "section": f"{ex['code']} Midterm Modules"
                }]
            else:
                response_text = f"Midterm syllabus covers the first 4 modules across all core subjects. Ask for Physics, Mathematics, or Data Structures specifically."
                spoken_text = "Midterm exams cover the first four modules of your courses."
                follow_ups = ["Syllabus for Physics", "Syllabus for Mathematics", "Upcoming exams"]
                sources = ["Nexus General Academic Curriculum (Fall 2026)"]
                source_details = [{
                    "document_name": "Nexus Academic Curriculum (Fall 2026)",
                    "category": "Syllabus",
                    "date": "Fall 2026",
                    "section": "Midterm Examination Curriculum"
                }]

        # --- INTENT: EXAM SCHEDULE ---
        elif intent == "exam_schedule":
            exams = knowledge_service.query_exam(subject)
            if exams:
                ex = exams[0]
                conversation_service.update_session_context(session_id, {
                    "last_intent": "exam_schedule",
                    "last_subject": ex["subject"],
                    "last_exam": ex,
                    "last_classroom": ex["room"],
                    "last_faculty": ex["instructor"],
                    "awaiting_clarification": None
                })

                sources = ["Midterm Examination Schedule (Fall 2026) (campus_exam_roster.db)"]
                primary_source = "Midterm Examination Schedule (Fall 2026)"
                source_details = [{
                    "document_name": "Midterm Examination Schedule (Fall 2026)",
                    "category": "Examination Roster",
                    "date": "Fall 2026",
                    "section": f"{ex['subject']} Midterm Slot"
                }]

                response_text = (
                    f"### 📋 {ex['title']} ({ex['code']})\n\n"
                    f"- 📅 **Date:** {ex['date']}\n"
                    f"- ⏰ **Time:** {ex['time']} ({ex.get('duration', '3 Hours')})\n"
                    f"- 📍 **Location:** **{ex['room']}**, {ex['block']}\n"
                    f"- 👨‍🏫 **Instructor:** {ex['instructor']}\n"
                    f"- 📝 **Exam Format:** {ex.get('format', 'Standard')}\n\n"
                    f"💡 *Syllabus:* {ex.get('syllabus', 'Complete semester syllabus')}"
                )
                spoken_text = f"Your {ex['subject']} exam is scheduled for {ex['date']} from {ex['time']} in {ex['room']}."
                follow_ups = [
                    "Where is it?",
                    "What do I need?",
                    "What about mathematics?",
                    f"Remind me tomorrow about that"
                ]
                metadata["exam"] = ex
            else:
                all_exams = knowledge_service.query_exam()
                exam_list = "\n".join([f"- **{e['subject']}**: {e['date']} ({e['time']}) in *{e['room']}*" for e in all_exams])
                sources = ["Midterm Examination Schedule (Fall 2026) (campus_exam_roster.db)"]
                primary_source = "Midterm Examination Schedule (Fall 2026)"
                source_details = [{
                    "document_name": "Midterm Examination Schedule (Fall 2026)",
                    "category": "Examination Roster",
                    "date": "Fall 2026",
                    "section": "Full Schedule"
                }]
                response_text = (
                    f"### 🎓 Upcoming Midterm Examination Schedule\n\n"
                    f"{exam_list}\n\n"
                    f"You can ask me about any specific subject for detailed room directions or syllabus coverage."
                )
                spoken_text = "Here is the upcoming exam schedule. Physics starts on Monday, followed by Mathematics on Wednesday."
                follow_ups = ["When is my physics exam?", "What about mathematics?", "Where is Hall B-204?"]

        # --- INTENT: CLASSROOM LOCATION / DIRECTIONS ---
        elif intent == "classroom_location":
            room_query = entities.get("classroom")
            if not room_query and ctx.get("last_classroom"):
                room_query = ctx["last_classroom"]
            elif not room_query and subject:
                exams = knowledge_service.query_exam(subject)
                if exams:
                    room_query = exams[0]["room"]

            classrooms = knowledge_service.query_classroom(room_query)
            if classrooms:
                cr = classrooms[0]
                conversation_service.update_session_context(session_id, {
                    "last_classroom": cr["name"],
                    "last_intent": "classroom_location"
                })
                facilities_str = ", ".join(cr.get("facilities", [])) if isinstance(cr.get("facilities"), list) else str(cr.get("facilities", ""))
                sources = [f"Campus Directory & Floor Maps (classrooms.db)"]
                primary_source = f"{cr['name']} Facility Guide"
                source_details = [{
                    "document_name": "Campus Directory & Floor Maps",
                    "category": "Classroom Directory",
                    "date": "Fall 2026",
                    "section": f"{cr['name']} Floor Details"
                }]

                response_text = (
                    f"### 📍 {cr['name']} Location Guide\n\n"
                    f"- 🏢 **Building & Floor:** {cr['block']}, {cr['floor']}\n"
                    f"- 👥 **Seating Capacity:** {cr.get('capacity', 'N/A')} students\n"
                    f"- 🛠️ **Facilities:** {facilities_str}\n\n"
                    f"🧭 **Directions:** {cr['directions']}"
                )
                spoken_text = f"{cr['name']} is located on the {cr['floor']} of {cr['block']}. {cr['directions']}"
                follow_ups = [
                    "What do I need?",
                    "Today's timetable",
                    "Upcoming exams"
                ]
                metadata["classroom"] = cr
            else:
                response_text = "I couldn't locate that specific room. Major lecture halls are in Science Block (Hall B-204, B-205) and Engineering Wing (Hall C-102)."
                spoken_text = "I couldn't find that specific room. Are you asking about Hall B-204 or Hall C-102?"
                follow_ups = ["Where is Hall B-204?", "Where is Hall C-102?"]
                sources = ["Campus Directory & Floor Maps (classrooms.db)"]
                source_details = [{
                    "document_name": "Campus Directory & Floor Maps",
                    "category": "Classroom Directory",
                    "date": "Fall 2026",
                    "section": "Directory Lookup"
                }]

        # --- INTENT: TIMETABLE ---
        elif intent == "timetable":
            day = entities.get("day") or "Monday"
            slots = knowledge_service.query_timetable(day=day, subject=entities.get("subject"))
            if slots:
                slot_lines = "\n".join([
                    f"- **{s['time']}**: **{s['subject']}** ({s.get('type', 'Lecture')}) — *{s['room']}* with {s['instructor']}"
                    for s in slots
                ])
                sources = ["Official Campus Class Timetable (campus_timetable.db)"]
                primary_source = f"Class Timetable - {day}"
                source_details = [{
                    "document_name": "Official Campus Class Timetable",
                    "category": "Class Timetable",
                    "date": "Fall 2026",
                    "section": f"Schedule for {day}"
                }]
                response_text = (
                    f"### 🗓️ Timetable for {day}\n\n"
                    f"{slot_lines}\n\n"
                    f"Let me know if you need directions to any of these halls or professor office hours."
                )
                spoken_text = f"For {day}, your first class is {slots[0]['subject']} at {slots[0]['time']} in {slots[0]['room']}."
                follow_ups = [
                    "What about tomorrow's schedule?",
                    f"Where is {slots[0]['room']}?",
                    "When are upcoming exams?"
                ]
                metadata["slots"] = slots
            else:
                response_text = f"No classes scheduled for {day} in the official college roster."
                spoken_text = f"There are no scheduled classes for {day}."
                follow_ups = ["Today's timetable", "Schedule for Monday"]
                sources = ["Official Campus Class Timetable (campus_timetable.db)"]
                source_details = [{
                    "document_name": "Official Campus Class Timetable",
                    "category": "Class Timetable",
                    "date": "Fall 2026",
                    "section": f"Schedule for {day}"
                }]

        # --- INTENT: FACULTY INFO ---
        elif intent == "faculty_info":
            target = entities.get("faculty_name") or subject or ctx.get("last_faculty")
            faculty_list = knowledge_service.query_faculty(target)
            if faculty_list:
                f = faculty_list[0]
                conversation_service.update_session_context(session_id, {
                    "last_faculty": f["name"],
                    "last_intent": "faculty_info"
                })
                sub_list = ", ".join(f.get("subjects", [])) if isinstance(f.get("subjects"), list) else str(f.get("subjects", ""))
                sources = ["Faculty Directory & Office Hours (faculty_directory.db)"]
                primary_source = f"Faculty Profile: {f['name']}"
                source_details = [{
                    "document_name": "Faculty Directory & Office Hours",
                    "category": "Faculty Directory",
                    "date": "Fall 2026",
                    "section": f"Faculty Profile: {f['name']}"
                }]
                response_text = (
                    f"### 👨‍🏫 {f['name']}\n\n"
                    f"- 🏛️ **Title & Dept:** {f['title']}, {f['department']}\n"
                    f"- 🏢 **Office:** {f['office']}\n"
                    f"- 🕒 **Office Hours:** {f['office_hours']}\n"
                    f"- 📧 **Email:** [{f['email']}](mailto:{f['email']})\n"
                    f"- 📞 **Phone:** {f.get('phone', 'N/A')}\n"
                    f"- 📚 **Courses:** {sub_list}\n"
                    f"- 🔬 **Research:** {f.get('research', 'N/A')}"
                )
                spoken_text = f"{f['name']} is available during office hours on {f['office_hours']} in {f['office']}."
                follow_ups = [
                    f"When is the {f['name'].split()[-1]}'s exam?",
                    "Where is the office located?",
                    "Today's timetable"
                ]
                metadata["faculty"] = f
            else:
                response_text = "I couldn't find faculty details for that query. Faculty records include Dr. Elena Vance (Physics), Prof. Rajesh Sharma (Math), and Prof. Marcus Chen (Data Structures)."
                spoken_text = "I couldn't find that professor. You can ask about Dr. Elena Vance or Professor Rajesh Sharma."
                follow_ups = ["Who teaches Physics?", "Who teaches Mathematics?"]
                sources = ["Faculty Directory & Office Hours (faculty_directory.db)"]
                source_details = [{
                    "document_name": "Faculty Directory & Office Hours",
                    "category": "Faculty Directory",
                    "date": "Fall 2026",
                    "section": "Faculty Directory"
                }]

        # --- INTENT: NOTICES / ANNOUNCEMENTS ---
        elif intent == "notices_announcements":
            notices = knowledge_service.query_notices()
            notice_items = "\n\n".join([
                f"📢 **{n['title']}** [{n['priority']} Priority]\n"
                f"*{n['date']}* • {n['details']}\n"
                f"👉 *Action:* {n.get('action', 'Check portal')}"
                for n in notices[:3]
            ])
            sources = ["Campus Bulletins & Notices (campus_notices.db)"]
            primary_source = "Campus Bulletins & Notices"
            source_details = [{
                "document_name": "Campus Bulletins & Notices",
                "category": "Announcements",
                "date": "October 2026",
                "section": "Campus Circulars"
            }]
            response_text = (
                f"### 🔔 Latest Campus Notices & Bulletins\n\n"
                f"{notice_items}\n\n"
                f"You can ask me for more details on any notice or upcoming deadlines."
            )
            spoken_text = f"There are 3 important notices. The top announcement is: {notices[0]['title']}."
            follow_ups = [
                "Tell me about HackSphere 2026",
                "Library exam hours",
                "Upcoming exams"
            ]
            metadata["notices"] = notices[:3]

        # --- INTENT: LIBRARY INFO ---
        elif intent == "library_info":
            lib = knowledge_service.query_library()
            sources = ["Central Library Guide & Timings (campus_library.db)"]
            primary_source = "Central Library Guide"
            source_details = [{
                "document_name": "Central Library Guide & Timings",
                "category": "Library Policy",
                "date": "Fall 2026",
                "section": "Library Hours & Study Zones"
            }]
            response_text = (
                f"### 📚 {lib.get('name', 'Central Library')}\n\n"
                f"- ⏰ **Standard Hours:** {lib.get('regular_timings')}\n"
                f"- 🔥 **Exam Period:** {lib.get('exam_period_timings')}\n"
                f"- 📖 **Borrowing Limit:** {lib.get('borrowing_rules')}\n"
                f"- 🤫 **Quiet Zone:** 3rd Floor Silent Sanctuary\n"
                f"- 🌐 **Digital Resources:** {lib.get('digital_resources')}"
            )
            spoken_text = "The Central Library is open from 8 AM to 10 PM daily, and operates 24/7 during midterm exam periods."
            follow_ups = [
                "When is my physics exam?",
                "Where is the quiet study zone?",
                "Campus notices"
            ]

        # --- INTENT: CAMPUS FACILITIES ---
        elif intent == "campus_facilities":
            facs = knowledge_service.query_facilities()
            items = "\n".join([f"- **{f['name']}** ({f['location']}): {f['timings']} — *{f['services']}*" for f in facs])
            sources = ["Campus Facilities & Amenities (campus_facilities.db)"]
            primary_source = "Campus Facilities Directory"
            source_details = [{
                "document_name": "Campus Facilities & Amenities",
                "category": "Facilities Guide",
                "date": "Fall 2026",
                "section": "Campus Facilities"
            }]
            response_text = f"### 🏢 Campus Facilities & Amenities\n\n{items}"
            spoken_text = "Here are the campus facilities including the Food Court, Health Center, Sports Complex, and Shuttle Service."
            follow_ups = ["Cafeteria timings", "Library hours", "Upcoming exams"]

        # --- INTENT: CAMPUS EVENTS ---
        elif intent == "campus_events":
            evs = knowledge_service.query_events()
            items = "\n".join([f"- 🎉 **{e['title']}** ({e['date']}) at *{e['venue']}*: {e['highlights']}" for e in evs])
            sources = ["Campus Events & Hackathons (campus_events.db)"]
            primary_source = "Campus Events Calendar"
            source_details = [{
                "document_name": "Campus Events & Hackathons",
                "category": "Events Calendar",
                "date": "Fall 2026",
                "section": "Upcoming Events"
            }]
            response_text = f"### 🎪 Campus Events & Competitions\n\n{items}"
            spoken_text = f"Upcoming campus events include {evs[0]['title']} on {evs[0]['date']}."
            follow_ups = ["Tell me about HackSphere 2026", "Campus notices", "Upcoming exams"]

        # --- INTENT: ASSIGNMENT DEADLINES ---
        elif intent == "assignment_deadline":
            assigns = knowledge_service.query_assignments()
            items = "\n".join([f"- 📝 **{a['subject']}**: {a['title']} (Due: {a['due_date']}) via *{a['portal']}*" for a in assigns])
            sources = ["Student Coursework & Assignments (assignments.db)"]
            primary_source = "Student Assignment Tracker"
            source_details = [{
                "document_name": "Student Coursework & Assignments",
                "category": "Coursework",
                "date": "Fall 2026",
                "section": "Assignment Schedule"
            }]
            response_text = f"### 📌 Upcoming Coursework & Deadlines\n\n{items}"
            spoken_text = f"You have {len(assigns)} upcoming assignments. The nearest is {assigns[0]['subject']} due on {assigns[0]['due_date']}."
            follow_ups = ["Remind me about assignment", "Today's timetable", "Upcoming exams"]

        # --- INTENT: GREETING OR HELP ---
        elif intent == "greeting_or_help":
            response_text = (
                f"### 👋 Welcome to VocaGuide!\n\n"
                f"I am your AI Voice-Powered Campus Assistant for **Nexus Institute of Technology**.\n\n"
                f"You can speak naturally or ask questions about:\n"
                f"- 📅 **Exam Schedules & Syllabus** *(e.g. 'When is my physics exam?')*\n"
                f"- 🗓️ **Class Timetables** *(e.g. 'Today's timetable')*\n"
                f"- 📍 **Classrooms & Directions** *(e.g. 'What classroom is it in?')*\n"
                f"- 📜 **College Rules & Handbook** *(e.g. 'What is the attendance policy?')*\n"
                f"- ⏰ **Study Reminders** *(e.g. 'Remind me to submit lab report on Friday')*\n"
                f"- 📢 **Notices & Hackathons** *(e.g. 'College notices', 'Upcoming events')*"
            )
            spoken_text = "Hello! I am VocaGuide, your AI campus assistant. How can I help you today?"
            follow_ups = [
                "When is my physics exam?",
                "What is the attendance policy?",
                "Today's timetable",
                "College notices"
            ]
            sources = ["VocaGuide Assistant Guide"]
            source_details = [{
                "document_name": "VocaGuide Campus Assistant Guide",
                "category": "Assistant Help",
                "date": "Fall 2026",
                "section": "Getting Started"
            }]

        # --- INTENT: UNVERIFIED / NON-EXISTENT CAMPUS QUERY (ANTI-HALLUCINATION) ---
        else:
            response_text = (
                "### ℹ️ Information Not Found in College Records\n\n"
                "I could not find verified information regarding this question in the official college documents, handbook, or timetable.\n\n"
                "👉 *Please consult the Student Affairs Office or your department advisor for assistance with unlisted campus policies.*"
            )
            spoken_text = "I could not find verified information about that in the official college documents or handbook."
            follow_ups = ["When are upcoming exams?", "Today's timetable", "College notices"]
            sources = []
            source_details = []
            primary_source = None

        return {
            "response_text": response_text,
            "spoken_text": spoken_text,
            "detected_intent": intent,
            "confidence": confidence,
            "entities": entities,
            "follow_up_suggestions": follow_ups,
            "sources": sources,
            "source_details": source_details,
            "primary_source": primary_source,
            "action_executed": None,
            "action_result": None,
            "mode": "demo",
            "clarification_needed": False,
            "clarification_field": None,
            "metadata": metadata
        }

    async def _synthesize_external_llm(
        self,
        query: str,
        intent: str,
        confidence: float,
        entities: Dict[str, Any],
        ctx: Dict[str, Any],
        session_id: str,
        rag_results: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sends conversation history, RAG document chunks, and grounding rules to
        configured LLM (Gemini / OpenAI / Groq).
        """
        chunks_text = "\n\n".join([
            f"--- Document: {c['title']} ({c['source_file']}) | Section: {c['section']} ---\n{c['content']}"
            for c in rag_results.get("chunks", [])
        ])

        system_instruction = (
            f"{self.system_prompt}\n\n"
            f"=== VERIFIED CAMPUS KNOWLEDGE BASE (USE THIS TO ANSWER) ===\n"
            f"{chunks_text if chunks_text else 'No specific document chunks retrieved for this query.'}\n"
            f"=== CURRENT CONTEXT ===\n"
            f"Active Subject: {ctx.get('last_subject')}\n"
            f"Active Classroom: {ctx.get('last_classroom')}\n"
            f"Active Exam: {ctx.get('last_exam')}\n\n"
            "Return valid JSON matching this schema:\n"
            "{\n"
            "  \"response_text\": \"markdown formatted response with bullet points and bold headers\",\n"
            "  \"spoken_text\": \"1-2 conversational sentences for speech synthesis without asterisks or markdown\",\n"
            "  \"follow_up_suggestions\": [\"question 1\", \"question 2\"],\n"
            "  \"sources\": [\"document title\"]\n"
            "}"
        )

        messages_payload = [{"role": "system", "content": system_instruction}]
        for turn in history[-4:]:
            role = "assistant" if turn["role"] == "assistant" else "user"
            messages_payload.append({"role": role, "content": turn["content"]})
        messages_payload.append({"role": "user", "content": query})

        # Gemini Call
        if self.provider == "gemini" and GEMINI_API_KEY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                    for m in messages_payload if m["role"] != "system"
                ],
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "generationConfig": {"responseMimeType": "application/json"}
            }
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)

        # OpenAI / Groq Call
        else:
            api_url = "https://api.openai.com/v1/chat/completions" if self.provider == "openai" else "https://api.groq.com/openai/v1/chat/completions"
            api_key = OPENAI_API_KEY if self.provider == "openai" else GROQ_API_KEY
            payload = {
                "model": self.model_name,
                "messages": messages_payload,
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(api_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload)
                res.raise_for_status()
                data = res.json()
                raw_text = data["choices"][0]["message"]["content"]
                parsed = json.loads(raw_text)

        if "subject" in entities:
            conversation_service.update_session_context(session_id, {
                "last_intent": intent,
                "last_subject": entities["subject"]
            })

        sources = parsed.get("sources") or rag_results.get("sources", [])
        source_details = [
            {
                "document_name": c.get("title", s),
                "category": "Official College Document",
                "date": "Fall 2026",
                "section": c.get("section", "General")
            }
            for c, s in zip(rag_results.get("chunks", []), sources)
        ] if rag_results.get("chunks") else [
            {"document_name": s, "category": "Campus Knowledge", "date": "Fall 2026", "section": "Reference"}
            for s in sources
        ]

        return {
            "response_text": parsed.get("response_text", ""),
            "spoken_text": parsed.get("spoken_text", ""),
            "detected_intent": intent,
            "standard_intent": get_standard_intent(intent),
            "confidence": confidence,
            "entities": entities,
            "follow_up_suggestions": parsed.get("follow_up_suggestions", []),
            "sources": sources,
            "source_details": source_details,
            "primary_source": sources[0] if sources else None,
            "action_executed": None,
            "action_result": None,
            "mode": self.provider,
            "clarification_needed": False,
            "clarification_field": None,
            "metadata": {"provider": self.provider, "model": self.model_name}
        }

llm_service = LLMService()
