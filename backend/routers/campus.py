from fastapi import APIRouter, Query
from typing import Optional
from backend.services import knowledge_service

router = APIRouter(prefix="/api/campus", tags=["Campus Knowledge Base"])

@router.get("/overview")
async def get_campus_overview():
    exams = knowledge_service.query_exam()
    notices = knowledge_service.query_notices()
    events = knowledge_service.query_events()
    faculty = knowledge_service.query_faculty()
    timetable = knowledge_service.query_timetable()
    
    return {
        "campus_name": "Nexus Institute of Technology",
        "academic_year": "2026-2027",
        "current_semester": "Fall 2026",
        "quick_stats": {
            "upcoming_exams": len(exams),
            "active_notices": len(notices),
            "events": len(events),
            "faculty_members": len(faculty),
            "timetable_slots": len(timetable)
        }
    }

@router.get("/exams")
async def get_exams(subject: Optional[str] = Query(None)):
    return knowledge_service.query_exam(subject)

@router.get("/timetable")
async def get_timetable(day: Optional[str] = Query(None), subject: Optional[str] = Query(None)):
    return knowledge_service.query_timetable(day, subject)

@router.get("/faculty")
async def get_faculty(query: Optional[str] = Query(None)):
    return knowledge_service.query_faculty(query)

@router.get("/classrooms")
async def get_classrooms(name: Optional[str] = Query(None)):
    return knowledge_service.query_classroom(name)

@router.get("/notices")
async def get_notices(category: Optional[str] = Query(None)):
    return knowledge_service.query_notices(category)

@router.get("/assignments")
async def get_assignments(subject: Optional[str] = Query(None)):
    return knowledge_service.query_assignments(subject)

@router.get("/events")
async def get_events():
    return knowledge_service.query_events()

@router.get("/library")
async def get_library():
    return knowledge_service.query_library()

@router.get("/facilities")
async def get_facilities(name: Optional[str] = Query(None)):
    return knowledge_service.query_facilities(name)
