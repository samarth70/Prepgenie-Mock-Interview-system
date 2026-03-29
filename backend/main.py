"""
PrepGenie Backend - FastAPI Application for Render.com

Created by Samarth Agarwal
AI Mock Interview Platform
"""

import os
import io
import uuid
import logging
import json
import pypdf
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

import ai_service
import database_render as db

# ──────────────────────────────────────────────────────────────
#  App Configuration
# ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="PrepGenie API",
    description="Created by Samarth Agarwal - AI Mock Interview Platform",
    version="3.2.0 (Render)",
)

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins and cors_origins != "*":
    origins = [origin.strip() for origin in cors_origins.split(",")]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("prepgenie.api")

# ──────────────────────────────────────────────────────────────
#  Startup Event
# ──────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("PrepGenie API starting up...")
    logger.info(f"CORS Origins: {os.getenv('CORS_ORIGINS', '*')}")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    logger.info("PrepGenie API ready!")

# ──────────────────────────────────────────────────────────────
#  Request/Response Models
# ──────────────────────────────────────────────────────────────

class StartInterviewRequest(BaseModel):
    roles: List[str]
    resume_text: str

    @field_validator("roles")
    @classmethod
    def roles_not_empty(cls, v):
        if not v or not any(v):
            raise ValueError("At least one role is required")
        return v

class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer_text: str

class ChatRequest(BaseModel):
    resume_text: str
    query: str

# ──────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")

# ──────────────────────────────────────────────────────────────
#  API Endpoints
# ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Welcome to PrepGenie API",
        "creator": "Samarth Agarwal",
        "status": "online",
        "platform": "Render.com",
        "version": "3.2.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render."""
    return {
        "status": "healthy",
        "creator": ai_service.get_attribution(),
        "ai_providers": ai_service.get_provider_status(),
        "platform": "Render.com",
        "version": "3.2.0"
    }

@app.post("/api/process-resume")
async def process_resume(file: UploadFile = File(...)):
    """Process uploaded resume PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()
    raw_text = extract_text_from_pdf(contents)
    if not raw_text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    formatted_text = await ai_service.format_resume(raw_text)

    return {
        "success": True,
        "raw_text": raw_text,
        "formatted_text": formatted_text,
    }

@app.post("/api/start-interview")
async def start_interview(request_body: StartInterviewRequest):
    """Start a new mock interview session."""
    session_id = str(uuid.uuid4())
    questions = await ai_service.generate_questions(
        request_body.roles, 
        request_body.resume_text
    )

    await db.create_session(
        session_id=session_id,
        roles=request_body.roles,
        resume_text=request_body.resume_text,
        questions=questions,
    )

    return {
        "success": True,
        "session_id": session_id,
        "question": questions[0] if questions else None,
        "total_questions": len(questions),
        "question_number": 1,
    }

@app.post("/api/submit-answer")
async def submit_answer(request_body: SubmitAnswerRequest):
    """Submit an answer to the current interview question."""
    session = await db.get_interview_session(request_body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    feedback_data = await ai_service.generate_answer_feedback(
        session.questions[session.current_question_index],
        request_body.answer_text,
        session.resume_text
    )

    # Update session state
    new_index = session.current_question_index + 1
    new_answers = session.answers + [request_body.answer_text]
    new_feedback = session.feedback + [feedback_data["feedback"]]
    new_metrics = session.metrics_list + [feedback_data["metrics"]]

    interactions = session.interactions
    interactions[session.questions[session.current_question_index]] = request_body.answer_text

    await db.update_session(
        session_id=request_body.session_id,
        current_question_index=new_index,
        answers=new_answers,
        feedback=new_feedback,
        metrics_list=new_metrics,
        interactions=interactions
    )

    if new_index < len(session.questions):
        return {
            "success": True,
            "next_question": session.questions[new_index],
            "question_number": new_index + 1,
            "is_complete": False,
            "feedback": feedback_data["feedback"],
            "metrics": feedback_data["metrics"],
        }
    else:
        # Generate final evaluation
        final_eval = await ai_service.generate_evaluation(
            session.resume_text, session.roles, interactions
        )

        # Save to history
        await db.save_history({
            "session_id": request_body.session_id,
            "roles": session.roles,
            "interactions": interactions,
            **final_eval
        })

        # Cleanup session
        await db.delete_session(request_body.session_id)

        return {
            "success": True,
            "is_complete": True,
            "evaluation": final_eval,
        }

@app.get("/api/history")
async def get_history():
    """Get all interview history."""
    history = await db.get_all_history()
    return {
        "success": True,
        "history": history,
        "count": len(history),
    }

@app.post("/api/clear-history")
async def clear_history():
    """Clear all interview history."""
    await db.clear_all_history()
    return {"success": True, "message": "History cleared"}

@app.post("/api/chat-with-resume")
async def chat_with_resume(request_body: ChatRequest):
    """Chat with resume content."""
    prompt = f"Resume:\n{request_body.resume_text}\n\nQuestion: {request_body.query}"
    ok, result = await ai_service.generate(
        prompt,
        system_prompt="You are a professional resume assistant for PrepGenie (by Samarth Agarwal).",
        max_tokens=1024,
    )
    
    return {
        "success": ok,
        "response": result,
        "creator": ai_service.get_attribution()
    }
