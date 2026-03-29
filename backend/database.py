"""
PrepGenie Database - Cloudflare D1 Integration.

Provides persistent storage for interview sessions and history via Cloudflare D1.
Optimised for the Cloudflare Workers (Python) environment.
"""

import json
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

# Handle Cloudflare Workers environment
IS_CLOUDFLARE = "wrangler" in sys.modules or "js" in sys.modules

# Note: In Cloudflare Workers, the 'db' binding is provided via the 'env' object.
# We skip the SQLModel/Engine logic and use direct SQL execution.

class InterviewSession:
    def __init__(self, data: Dict[str, Any]):
        self.session_id = data.get("session_id")
        self.roles_json = data.get("roles_json", "[]")
        self.resume_text = data.get("resume_text", "")
        self.questions_json = data.get("questions_json", "[]")
        self.current_question_index = data.get("current_question_index", 0)
        self.answers_json = data.get("answers_json", "[]")
        self.interactions_json = data.get("interactions_json", "{}")
        self.feedback_json = data.get("feedback_json", "[]")
        self.metrics_list_json = data.get("metrics_list_json", "[]")
        self.status = data.get("status", "active")
        self.created_at = data.get("created_at")

    @property
    def roles(self) -> List[str]:
        return json.loads(self.roles_json)

    @property
    def questions(self) -> List[str]:
        return json.loads(self.questions_json)

    @property
    def answers(self) -> List[str]:
        return json.loads(self.answers_json)

    @property
    def interactions(self) -> Dict[str, str]:
        return json.loads(self.interactions_json)

    @property
    def feedback(self) -> List[str]:
        return json.loads(self.feedback_json)

    @property
    def metrics_list(self) -> list:
        return json.loads(self.metrics_list_json)


class InterviewHistory:
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def to_dict(self) -> dict:
        return {
            "session_id": self.data.get("session_id"),
            "timestamp": self.data.get("timestamp"),
            "roles": json.loads(self.data.get("roles_json", "[]")),
            "interactions": json.loads(self.data.get("interactions_json", "{}")),
            "feedback": json.loads(self.data.get("feedback_json", "[]")),
            "metrics": json.loads(self.data.get("metrics_json", "{}")),
            "average_rating": self.data.get("average_rating", 0.0),
            "evaluation": self.data.get("evaluation", ""),
            "question_feedback": json.loads(self.data.get("question_feedback_json", "[]")),
            "strengths": json.loads(self.data.get("strengths_json", "[]")),
            "improvements": json.loads(self.data.get("improvements_json", "[]")),
            "is_fallback": bool(self.data.get("is_fallback")),
        }


# ──────────────────────────────────────────────────────────────
#  Async CRUD Operations (D1 Compatible)
# ──────────────────────────────────────────────────────────────

async def create_session(
    db: Any,
    session_id: str,
    roles: List[str],
    resume_text: str,
    questions: List[str],
) -> None:
    sql = """
    INSERT INTO interview_sessions (
        session_id, roles_json, resume_text, questions_json, created_at
    ) VALUES (?, ?, ?, ?, ?)
    """
    await db.prepare(sql).bind(
        session_id,
        json.dumps(roles),
        resume_text,
        json.dumps(questions),
        datetime.now().isoformat()
    ).run()


async def get_interview_session(db: Any, session_id: str) -> Optional[InterviewSession]:
    sql = "SELECT * FROM interview_sessions WHERE session_id = ?"
    row = await db.prepare(sql).bind(session_id).first()
    return InterviewSession(row) if row else None


async def update_session(db: Any, session_id: str, **kwargs) -> None:
    if not kwargs:
        return
    
    # Map high-level properties to database columns if needed (e.g. roles -> roles_json)
    # For now, we assume the caller passes the exact column names
    fields = []
    values = []
    for key, val in kwargs.items():
        if isinstance(val, (list, dict)):
            val = json.dumps(val)
        fields.append(f"{key} = ?")
        values.append(val)
    
    sql = f"UPDATE interview_sessions SET {', '.join(fields)} WHERE session_id = ?"
    values.append(session_id)
    await db.prepare(sql).bind(*values).run()


async def delete_session(db: Any, session_id: str) -> None:
    sql = "DELETE FROM interview_sessions WHERE session_id = ?"
    await db.prepare(sql).bind(session_id).run()


async def save_history(db: Any, record: dict) -> None:
    sql = """
    INSERT INTO interview_history (
        session_id, timestamp, roles_json, interactions_json, feedback_json,
        metrics_json, average_rating, evaluation, question_feedback_json,
        strengths_json, improvements_json, is_fallback
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    await db.prepare(sql).bind(
        record["session_id"],
        record.get("timestamp", datetime.now().isoformat()),
        json.dumps(record.get("roles", [])),
        json.dumps(record.get("interactions", {})),
        json.dumps(record.get("feedback", [])),
        json.dumps(record.get("metrics", {})),
        record.get("average_rating", 0.0),
        record.get("evaluation", ""),
        json.dumps(record.get("question_feedback", [])),
        json.dumps(record.get("strengths", [])),
        json.dumps(record.get("improvements", [])),
        1 if record.get("is_fallback", False) else 0
    ).run()


async def get_all_history(db: Any) -> List[dict]:
    sql = "SELECT * FROM interview_history ORDER BY id DESC"
    res = await db.prepare(sql).all()
    # D1 'all' returns an object with a 'results' list
    rows = res.get("results", []) if isinstance(res, dict) else res
    return [InterviewHistory(r).to_dict() for r in rows]


async def clear_all_history(db: Any) -> None:
    sql = "DELETE FROM interview_history"
    await db.prepare(sql).run()
