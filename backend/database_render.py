"""
PrepGenie Database - In-Memory Storage for Render Deployment.

For production use with PostgreSQL, see database_postgres.py
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# In-memory storage (for Render free tier)
interview_sessions: Dict[str, Dict] = {}
interview_history: List[Dict] = []


class InterviewSession:
    def __init__(self, data: Dict[str, Any]):
        self.session_id = data.get("session_id")
        self.roles = data.get("roles", [])
        self.resume_text = data.get("resume_text", "")
        self.questions = data.get("questions", [])
        self.current_question_index = data.get("current_question_index", 0)
        self.answers = data.get("answers", [])
        self.interactions = data.get("interactions", {})
        self.feedback = data.get("feedback", [])
        self.metrics_list = data.get("metrics_list", [])
        self.status = data.get("status", "active")
        self.created_at = data.get("created_at")

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "roles": self.roles,
            "resume_text": self.resume_text,
            "questions": self.questions,
            "current_question_index": self.current_question_index,
            "answers": self.answers,
            "interactions": self.interactions,
            "feedback": self.feedback,
            "metrics_list": self.metrics_list,
            "status": self.status,
            "created_at": self.created_at,
        }


async def create_session(
    session_id: str,
    roles: List[str],
    resume_text: str,
    questions: List[str],
) -> None:
    """Create a new interview session."""
    interview_sessions[session_id] = {
        "session_id": session_id,
        "roles": roles,
        "resume_text": resume_text,
        "questions": questions,
        "current_question_index": 0,
        "answers": [],
        "interactions": {},
        "feedback": [],
        "metrics_list": [],
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }


async def get_interview_session(session_id: str) -> Optional[InterviewSession]:
    """Get an interview session by ID."""
    data = interview_sessions.get(session_id)
    return InterviewSession(data) if data else None


async def update_session(session_id: str, **kwargs) -> None:
    """Update an existing session."""
    if session_id not in interview_sessions:
        return
    
    for key, value in kwargs.items():
        interview_sessions[session_id][key] = value


async def delete_session(session_id: str) -> None:
    """Delete a session."""
    if session_id in interview_sessions:
        del interview_sessions[session_id]


async def save_history(record: dict) -> None:
    """Save interview to history."""
    history_record = {
        "session_id": record.get("session_id"),
        "timestamp": record.get("timestamp", datetime.now().isoformat()),
        "roles": record.get("roles", []),
        "interactions": record.get("interactions", {}),
        "feedback": record.get("feedback", []),
        "metrics": record.get("metrics", {}),
        "average_rating": record.get("average_rating", 0.0),
        "evaluation": record.get("evaluation", ""),
        "question_feedback": record.get("question_feedback", []),
        "strengths": record.get("strengths", []),
        "improvements": record.get("improvements", []),
        "is_fallback": record.get("is_fallback", False),
    }
    interview_history.append(history_record)


async def get_all_history() -> List[dict]:
    """Get all interview history."""
    return list(reversed(interview_history))


async def clear_all_history() -> None:
    """Clear all interview history."""
    interview_history.clear()


async def get_history_statistics(history: List[dict]) -> dict:
    """Calculate statistics from interview history."""
    if not history:
        return {
            "total_interviews": 0,
            "average_rating": 0.0,
            "most_common_roles": [],
        }
    
    total = len(history)
    avg_rating = sum(h.get("average_rating", 0.0) for h in history) / total if total > 0 else 0.0
    
    # Count roles
    role_counts = {}
    for h in history:
        for role in h.get("roles", []):
            role_counts[role] = role_counts.get(role, 0) + 1
    
    most_common = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        "total_interviews": total,
        "average_rating": round(avg_rating, 2),
        "most_common_roles": [role for role, _ in most_common],
    }
