"""
PrepGenie Backend - Cloudflare Worker Implementation
Created by Samarth Agarwal
AI Mock Interview Platform
"""

import json
import uuid
import io
# pypdf is imported lazily. It is the heaviest module-level import here, and
# Cloudflare caps Python Worker *startup* CPU at 1000ms - eager import pushed
# the snapshot baseline over the limit and blocked every deploy. Only
# /api/process-resume needs it; chat and interview paths never touch it.
pypdf = None
HAS_PYPDF = True  # resolved on first use


def _load_pypdf():
    global pypdf, HAS_PYPDF
    if pypdf is None:
        try:
            import pypdf as _p
            pypdf = _p
        except ImportError:
            HAS_PYPDF = False
    return pypdf

import ai_service
import database as db

try:
    from js import Response as JSResponse, Headers
except ImportError:
    # Fallback for local testing if needed
    class JSResponse:
        @staticmethod
        def new(body, status=200, headers=None):
            return None
    class Headers:
        @staticmethod
        def new():
            return None

async def on_fetch(request, env):
    """Main entry point for Cloudflare Worker."""
    
    # Handle CORS Preflight
    if request.method == "OPTIONS":
        return _cors_response(request, env, JSResponse.new(None, status=204))

    # Routing
    url = request.url
    path = "/" + "/".join(url.split("/")[3:])
    query = ""
    if "?" in path:
        path, query = path.split("?", 1)

    try:
        # Root / Health
        if path == "/" or path == "/health":
            env_keys = []
            env_details = {}
            if env:
                try:
                    import js
                    env_keys = list(js.Object.keys(env))
                    for k in env_keys:
                        # Exclude DB which is an object binding
                        if k == "DB":
                            continue
                        val = ai_service._get_secret(env, k)
                        # Length only, never any part of the value: this endpoint is
                        # public and unauthenticated, so echoing a key prefix leaks
                        # credential material to anyone who calls it.
                        env_details[k] = {
                            "present": val is not None,
                            "length": len(val) if val is not None else 0,
                        }
                except Exception as e:
                    env_details["error"] = str(e)
            return await _json_response(request, env, {
                "status": "healthy",
                "message": "Welcome to PrepGenie API",
                "creator": ai_service.get_attribution(),
                "platform": "Cloudflare Workers",
                "version": "3.3.0",
                "has_pypdf": HAS_PYPDF,
                "env_keys": env_keys,
                "env_details": env_details,
                # _provider_status holds datetime objects in cooldown_until, which
                # json.dumps cannot serialize - that made /health return HTTP 500, so
                # the one endpoint reporting why generation fails was itself unreadable.
                # ?debug=providers actually calls each provider. Without it a healthy
                # primary hides a dead secondary, which is how a broken Groq key sat
                # unnoticed behind a working Gemini.
                "provider_probe": (await ai_service.probe_providers(env)
                                   if "debug=providers" in query else None),
                "provider_status": {
                    name: {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                           for k, v in state.items()}
                    for name, state in ai_service._provider_status.items()
                },
            })

        # Process Resume
        elif path == "/api/process-resume" and request.method == "POST":
            return await handle_process_resume(request, env)

        # Start Interview
        elif path == "/api/start-interview" and request.method == "POST":
            return await handle_start_interview(request, env)

        # Submit Answer
        elif path == "/api/submit-answer" and request.method == "POST":
            return await handle_submit_answer(request, env)

        # Submit Interview
        elif path == "/api/submit-interview" and request.method == "POST":
            return await handle_submit_interview(request, env)

        # History
        elif path in ("/api/history", "/api/interview-history") and request.method == "GET":
            return await handle_get_history(request, env)

        # Clear History
        elif path == "/api/clear-history" and request.method == "POST":
            return await handle_clear_history(request, env)

        # Chat with Resume
        elif path == "/api/chat-with-resume" and request.method == "POST":
            return await handle_chat_with_resume(request, env)

        # Not Found
        else:
            return await _json_response(request, env, {"error": f"Path {path} not found"}, status=404)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error handling {path}: {error_trace}")
        return await _json_response(request, env, {
            "error": "Internal Server Error",
            "message": str(e)
        }, status=500)

async def handle_process_resume(request, env):
    _load_pypdf()
    print(f"DEBUG: Starting handle_process_resume. HAS_PYPDF={HAS_PYPDF}")
    if not HAS_PYPDF or pypdf is None:
        return await _json_response(request, env, {"error": "PDF library missing"}, status=500)

    try:
        # Use .to_py() to resolve TypeError when accessing FormData
        form_data = (await request.formData()).to_py()
        file = form_data.get("file")
        
        if not file or not hasattr(file, "name"):
            return await _json_response(request, env, {"error": "No file uploaded"}, status=400)

        # Optimize: Directly process buffer
        contents = await file.arrayBuffer()
        pdf_bytes = bytes(contents.to_py())
        
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        # Efficient extraction loop
        raw_text = "".join(p.extract_text() or "" for p in reader.pages).strip()
        
        if not raw_text:
            return await _json_response(request, env, {"error": "Empty PDF"}, status=400)

        # AI Service
        formatted_text = await ai_service.format_resume(raw_text, env=env)

        return await _json_response(request, env, {
            "success": True,
            "raw_text": raw_text,
            "formatted_text": formatted_text,
        })
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        return await _json_response(request, env, {"error": f"Process Error: {str(e)}"}, status=500)

async def handle_start_interview(request, env):
    body = (await request.json()).to_py()
    roles = body.get("roles", [])
    resume_text = body.get("resume_text", "")

    if not roles:
        return await _json_response(request, env, {"error": "At least one role is required"}, status=400)

    session_id = str(uuid.uuid4())
    questions = await ai_service.generate_questions(roles, resume_text, env=env)

    await db.create_session(
        db=env.DB,
        session_id=session_id,
        roles=roles,
        resume_text=resume_text,
        questions=questions,
    )

    return await _json_response(request, env, {
        "success": True,
        "session_id": session_id,
        "question": questions[0] if questions else None,
        "total_questions": len(questions),
        "question_number": 1,
    })

async def handle_submit_answer(request, env):
    body = (await request.json()).to_py()
    session_id = body.get("session_id")
    answer_text = body.get("answer_text", "")

    if not session_id:
        return await _json_response(request, env, {"error": "session_id is required"}, status=400)

    session = await db.get_interview_session(env.DB, session_id)
    if not session:
        return await _json_response(request, env, {"error": "Session not found"}, status=404)

    feedback_data = await ai_service.generate_answer_feedback(
        session.questions[session.current_question_index],
        answer_text,
        session.resume_text,
        env=env
    )

    # Update session state
    new_index = session.current_question_index + 1
    new_answers = session.answers + [answer_text]
    new_feedback = session.feedback + [feedback_data["feedback"]]
    new_metrics = session.metrics_list + [feedback_data["metrics"]]

    interactions = session.interactions
    interactions[session.questions[session.current_question_index]] = answer_text

    await db.update_session(
        db=env.DB,
        session_id=session_id,
        current_question_index=new_index,
        answers_json=json.dumps(new_answers),
        feedback_json=json.dumps(new_feedback),
        metrics_list_json=json.dumps(new_metrics),
        interactions_json=json.dumps(interactions)
    )

    if new_index < len(session.questions):
        return await _json_response(request, env, {
            "success": True,
            "next_question": session.questions[new_index],
            "question_number": new_index + 1,
            "is_complete": False,
            "feedback": feedback_data["feedback"],
            "metrics": feedback_data["metrics"],
        })
    else:
        # Reached the end of questions
        return await _json_response(request, env, {
            "success": True,
            "is_complete": True,
            "feedback": feedback_data["feedback"],
            "metrics": feedback_data["metrics"],
        })

async def handle_submit_interview(request, env):
    try:
        content_type = request.headers.get("content-type", "") or ""
        if "multipart/form-data" in content_type.lower():
            form_data = (await request.formData()).to_py()
            body = {"session_id": form_data.get("session_id")}
        else:
            text = await request.text()
            body = json.loads(text) if text and text.strip() else {}
    except Exception as e:
        print(f"JSON ERROR in submit-interview: '{text if 'text' in locals() else 'multipart error'}' -> {e}")
        body = {}
        
    session_id = body.get("session_id")

    if not session_id:
        return await _json_response(request, env, {"error": "session_id is required"}, status=400)

    session = await db.get_interview_session(env.DB, session_id)
    if not session:
        return await _json_response(request, env, {"error": "Session not found"}, status=404)

    # Generate final evaluation
    # We pass session.questions to ensure standard feedback formats match if needed
    final_eval = await ai_service.generate_evaluation(
        session.resume_text, session.roles, session.interactions, env=env
    )

    # Cleanup session (No longer saving to shared database to preserve user privacy)
    await db.delete_session(env.DB, session_id)

    # Return full evaluation structure expected by frontend
    return await _json_response(request, env, {
        "success": True,
        "is_complete": True,
        "evaluation": final_eval.get("evaluation", ""),
        "metrics": final_eval.get("metrics", {}),
        "average_rating": final_eval.get("average_rating", 0.0),
        "is_fallback": final_eval.get("is_fallback", False),
        "question_feedback": final_eval.get("question_feedback", []),
        "strengths": final_eval.get("strengths", []),
        "improvements": final_eval.get("improvements", []),
        "roles": session.roles,
        "interactions": session.interactions,
    })

async def handle_get_history(request, env):
    # Stubbed to return empty lists safely to prevent 404 errors for cached clients
    # History is now fully private and stored in client-side LocalStorage
    return await _json_response(request, env, {
        "success": True,
        "history": [],
        "count": 0,
    })

async def handle_clear_history(request, env):
    # Stubbed since history is fully private and cleared entirely on the client-side
    return await _json_response(request, env, {"success": True, "message": "History cleared locally"})

# Generous enough for a long CV and a detailed question, small enough that this
# cannot be used as a free general-purpose LLM endpoint for arbitrary payloads.
MAX_RESUME_CHARS = 40000
MAX_QUERY_CHARS = 2000


async def handle_chat_with_resume(request, env):
    body = (await request.json()).to_py()
    resume_text = body.get("resume_text", "")
    query = body.get("query", "")

    if not isinstance(resume_text, str) or not isinstance(query, str):
        return await _json_response(request, env, {
            "error": "resume_text and query must be strings"}, status=400)

    query = query.strip()
    if not query:
        return await _json_response(request, env, {
            "error": "A question is required."}, status=400)

    if len(query) > MAX_QUERY_CHARS:
        return await _json_response(request, env, {
            "error": f"Question too long ({len(query)} chars). Limit is {MAX_QUERY_CHARS}."},
            status=413)

    if len(resume_text) > MAX_RESUME_CHARS:
        return await _json_response(request, env, {
            "error": f"Resume too long ({len(resume_text)} chars). Limit is {MAX_RESUME_CHARS}."},
            status=413)

    result = await ai_service.chat_with_resume(resume_text, query, env=env)
    status = 200 if result.get("success") else 502
    return await _json_response(request, env, result, status=status)

# ─── Helpers ───

async def _json_response(request, env, data, status=200):
    h = Headers.new()
    h.set("Content-Type", "application/json")
    resp = JSResponse.new(json.dumps(data), status=status, headers=h)
    return _cors_response(request, env, resp)

def _cors_response(request, env, response):
    """Echo the Origin only when it is on the allowlist.

    This previously returned Access-Control-Allow-Origin: * with a note saying it
    was temporary and for debugging. On a public unauthenticated LLM proxy that
    lets any website on the internet embed these endpoints and spend the account's
    Gemini/OpenRouter quota. CORS_ORIGINS is already configured as a Worker var.
    """
    response.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.set("Access-Control-Allow-Credentials", "false")
    response.headers.set("Vary", "Origin")

    origin = None
    try:
        origin = request.headers.get("Origin")
    except Exception:
        origin = None

    if not origin:
        # No Origin at all (curl, server-to-server). CORS is not the control here.
        response.headers.set("Access-Control-Allow-Origin", "*")
        return response

    allowed = []
    try:
        configured = ai_service._get_secret(env, "CORS_ORIGINS") or ""
        allowed = [o.strip() for o in configured.split(",") if o.strip()]
    except Exception:
        allowed = []

    # Local dev ports are convenient but must never be implied in production.
    if origin in allowed:
        response.headers.set("Access-Control-Allow-Origin", origin)
    # Otherwise the header is deliberately omitted, so the browser blocks the read.
    return response
