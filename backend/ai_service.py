"""
PrepGenie AI Service - Unified LLM Abstraction Layer.

Provides a single interface for all AI operations, with automatic
retry, rate-limit handling, and graceful fallbacks.
Supports Groq (primary) and Google Gemini (secondary).

Uses urllib.request for HTTP calls (works in Cloudflare Workers Pyodide).
"""

import os
import re
import asyncio
import logging
import json as jsonlib
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger("prepgenie.ai")

# ──────────────────────────────────────────────────────────────
#  LLM Client Initialisation
# ──────────────────────────────────────────────────────────────

# Track provider status for cooldown
_provider_status = {
    "groq": {"status": "unknown", "last_err": None, "cooldown_until": None},
    "gemini": {"status": "unknown", "last_err": None, "cooldown_until": None},
    "openrouter": {"status": "unknown", "last_err": None, "cooldown_until": None},
}

async def generate(
    prompt: str,
    *,
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.6,
    max_tokens: int = 2048,
    max_retries: int = 3,
) -> Tuple[bool, str]:
    """
    Generate text via the best available LLM with robust failover.
    (Optimized for Cloudflare Workers using direct REST calls)
    """
    now = datetime.now()

    # Prioritize providers
    active_providers = []

    # We check environment variables here directly or pass them in from main.py's env
    # For Cloudflare Workers, these will be in the 'env' object.
    # We'll assume they are available in os.getenv for local/generic use
    google_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if google_key and (not _provider_status["gemini"]["cooldown_until"] or now > _provider_status["gemini"]["cooldown_until"]):
        active_providers.append(("gemini", _generate_gemini, google_key))
    if groq_key and (not _provider_status["groq"]["cooldown_until"] or now > _provider_status["groq"]["cooldown_until"]):
        active_providers.append(("groq", _generate_groq, groq_key))
    if openrouter_key and (not _provider_status["openrouter"]["cooldown_until"] or now > _provider_status["openrouter"]["cooldown_until"]):
        active_providers.append(("openrouter", _generate_openrouter, openrouter_key))

    if not active_providers:
        return False, "⚠️ All AI providers are currently exhausted or blocked. Please try again later."

    errors = []
    
    for provider_name, fn, key in active_providers:
        backoff_schedule = [2, 5, 10]

        for attempt in range(max_retries):
            try:
                text = await fn(key, prompt, system_prompt, temperature, max_tokens)
                logger.info("✅ %s generation succeeded (attempt %d)", provider_name, attempt + 1)
                _provider_status[provider_name]["status"] = "active"
                _provider_status[provider_name]["cooldown_until"] = None
                return True, text
            except Exception as exc:
                err_msg = str(exc)
                err_lower = err_msg.lower()
                _provider_status[provider_name]["last_err"] = err_msg

                # 429 Rate Limited → Backoff
                if any(k in err_lower for k in ("429", "rate", "quota")) and "404" not in err_lower:
                    _provider_status[provider_name]["status"] = "rate_limited"
                    delay = backoff_schedule[attempt] if attempt < len(backoff_schedule) else 15
                    logger.warning("⏳ %s rate-limited (%d/%d), retrying in %ds", provider_name, attempt+1, max_retries, delay)
                    await asyncio.sleep(delay)
                    continue

                # 401/403 Auth Error → 5 min cooldown
                if any(k in err_lower for k in ("401", "403", "unauthorized", "invalid")):
                    _provider_status[provider_name]["status"] = "blocked"
                    _provider_status[provider_name]["cooldown_until"] = datetime.now() + timedelta(minutes=5)
                    logger.error("🔑 %s auth error - cooling down for 5m", provider_name)
                    errors.append(f"{provider_name.capitalize()} Auth Error")
                    break

                # Other Error → Cool down for 1 min
                logger.error("❌ %s error: %s", provider_name, err_msg)
                _provider_status[provider_name]["status"] = "error"
                _provider_status[provider_name]["cooldown_until"] = datetime.now() + timedelta(minutes=1)
                errors.append(f"{provider_name.capitalize()} error: {err_msg[:50]}...")
                break

        logger.warning("🔄 Falling back from %s", provider_name)

    error_summary = " | ".join(errors) if errors else "Internal Error"
    return False, f"⚠️ AI Offline: {error_summary}"

async def _generate_gemini(api_key: str, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    data = jsonlib.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=30) as response:
            result = jsonlib.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except HTTPError as e:
        raise Exception(f"HTTP {e.code}: {e.read().decode('utf-8')}")
    except URLError as e:
        raise Exception(f"URL Error: {e.reason}")

async def _generate_groq(api_key: str, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    data = jsonlib.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'})
    try:
        with urlopen(req, timeout=30) as response:
            result = jsonlib.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except HTTPError as e:
        raise Exception(f"HTTP {e.code}: {e.read().decode('utf-8')}")
    except URLError as e:
        raise Exception(f"URL Error: {e.reason}")

async def _generate_openrouter(api_key: str, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    data = jsonlib.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
        'HTTP-Referer': 'https://prepgenie.ai',
        'X-Title': 'PrepGenie'
    })
    try:
        with urlopen(req, timeout=30) as response:
            result = jsonlib.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except HTTPError as e:
        raise Exception(f"HTTP {e.code}: {e.read().decode('utf-8')}")
    except URLError as e:
        raise Exception(f"URL Error: {e.reason}")


# ──────────────────────────────────────────────────────────────
#  Branding Helper
# ──────────────────────────────────────────────────────────────

def get_attribution() -> str:
    return "Samarth Agarwal"


# ──────────────────────────────────────────────────────────────
#  Domain-specific helpers
# ──────────────────────────────────────────────────────────────

DEFAULT_QUESTIONS: List[str] = [
    "Could you please introduce yourself based on your resume?",
    "What are your key technical skills relevant to this role?",
    "Describe a challenging project you've worked on and how you resolved it.",
    "How do you prioritize tasks when working under tight deadlines?",
    "Where do you see yourself professionally in the next 3 to 5 years?",
]

DEFAULT_METRICS: Dict[str, float] = {
    "Communication skills": 5.0,
    "Teamwork and collaboration": 5.0,
    "Problem-solving and critical thinking": 5.0,
    "Time management and organization": 5.0,
    "Adaptability and resilience": 5.0,
}

METRIC_KEYS = list(DEFAULT_METRICS.keys())


async def format_resume(raw_text: str) -> str:
    """Format raw resume text into a structured overview."""
    if not raw_text or not raw_text.strip():
        return "No resume data provided."

    prompt = (
        f"{raw_text}\n\n"
        "Extract the candidate's name, experience, education, and skills from the above. "
        "Format everything into a single professional paragraph."
    )
    ok, result = await generate(prompt)
    return result if ok else raw_text


async def generate_questions(roles: List[str], resume_text: str) -> List[str]:
    """Generate exactly 5 tailored interview questions."""
    if not roles or not resume_text or not resume_text.strip():
        return DEFAULT_QUESTIONS.copy()

    roles_str = ", ".join(roles)

    prompt = f"""You are an expert technical interviewer.

CANDIDATE PROFILE:
{resume_text}

TARGET ROLE(S): {roles_str}

Generate EXACTLY 5 personalized interview questions. Distribution:
1. Introduction/Background (based on resume)
2. Technical Skills (specific to {roles_str})
3. Behavioral (teamwork/collaboration)
4. Problem-Solving (situational)
5. Career Goals

RULES:
- Output ONLY 5 numbered questions (1-5), one per line
- Each must end with a question mark
- NO introductions, labels, or extra text
"""

    ok, result = await generate(prompt)
    if not ok:
        logger.warning("Question generation failed, using defaults")
        return DEFAULT_QUESTIONS.copy()

    return _parse_questions(result)


async def generate_answer_feedback(
    question: str, answer: str, resume: str
) -> Dict[str, Any]:
    """Generate feedback + metrics for a single answer."""
    default = {"feedback": "Answer received.", "metrics": DEFAULT_METRICS.copy()}

    if not answer or len(answer.strip()) < 10:
        return {
            "feedback": "Please provide a more detailed answer (at least a couple of sentences).",
            "metrics": DEFAULT_METRICS.copy(),
        }

    prompt = f"""Evaluate this interview answer:

RESUME: {resume}
QUESTION: {question}
ANSWER: {answer}

Respond in EXACTLY this format:
FEEDBACK: [2-3 sentences of constructive feedback]
Communication skills: [0-10]
Teamwork and collaboration: [0-10]
Problem-solving and critical thinking: [0-10]
Time management and organization: [0-10]
Adaptability and resilience: [0-10]

Scoring: 0-3 poor, 4-5 below average, 6-7 good, 8-9 excellent, 10 outstanding.
Be critical and fair. Scores must be plain numbers only."""

    ok, result = await generate(prompt)
    if not ok:
        return default

    return _parse_feedback(result, default)


async def generate_evaluation(
    resume_text: str,
    roles: List[str],
    interactions: Dict[str, str],
) -> Dict[str, Any]:
    """
    Generate a comprehensive final evaluation.
    Returns dict with: evaluation, metrics, average_rating,
    question_feedback, strengths, improvements.
    """
    interactions_text = "\n\n".join(
        f"Question: {q}\nCandidate Answer: {a}" for q, a in interactions.items()
    )

    prompt = f"""You are an expert interviewer providing a final evaluation.

RESUME: {resume_text}
ROLE(S): {", ".join(roles)}

INTERVIEW TRANSCRIPT:
{interactions_text}

Provide your evaluation in this EXACT format:

OVERALL: [2-3 paragraph overall assessment]

Q1: [question text]
ANSWER_SUMMARY: [1-2 sentence summary]
SAMPLE_ANSWER: [ideal answer using resume specifics, 3-4 sentences]
FEEDBACK: [2-3 sentences]
SCORE: [0-10]

Q2: [question text]
ANSWER_SUMMARY: [summary]
SAMPLE_ANSWER: [ideal answer]
FEEDBACK: [feedback]
SCORE: [0-10]

Q3: [question text]
ANSWER_SUMMARY: [summary]
SAMPLE_ANSWER: [ideal answer]
FEEDBACK: [feedback]
SCORE: [0-10]

Q4: [question text]
ANSWER_SUMMARY: [summary]
SAMPLE_ANSWER: [ideal answer]
FEEDBACK: [feedback]
SCORE: [0-10]

Q5: [question text]
ANSWER_SUMMARY: [summary]
SAMPLE_ANSWER: [ideal answer]
FEEDBACK: [feedback]
SCORE: [0-10]

STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]

IMPROVEMENTS:
- [improvement 1]
- [improvement 2]
- [improvement 3]

Communication skills: [0-10]
Teamwork and collaboration: [0-10]
Problem-solving and critical thinking: [0-10]
Time management and organization: [0-10]
Adaptability and resilience: [0-10]

IMPORTANT: Vary scores based on actual answer quality. Short answers get 2-4. Detailed answers with examples get 7-9."""

    ok, result = await generate(prompt, max_tokens=4096)
    if ok and result and len(result) > 100:
        return _parse_evaluation(result)
    else:
        logger.warning("Evaluation AI failed, using fallback")
        return _fallback_evaluation(interactions, roles)


# ──────────────────────────────────────────────────────────────
#  Parsing Helpers
# ──────────────────────────────────────────────────────────────

def _parse_questions(raw: str) -> List[str]:
    """Extract exactly 5 questions from AI output."""
    questions: List[str] = []

    # Strategy 1: numbered lines
    numbered = re.findall(r"^\d+[.)]\s*(.+)", raw, re.MULTILINE)
    questions = [q.strip() for q in numbered if q.strip() and "?" in q]

    # Strategy 2: all lines containing '?'
    if len(questions) < 5:
        for line in raw.split("\n"):
            line = re.sub(r"^[\d.\-*•]+\s*", "", line).strip()
            if line and "?" in line and line not in questions:
                questions.append(line)

    # Pad with defaults
    for dq in DEFAULT_QUESTIONS:
        if len(questions) >= 5:
            break
        if dq not in questions:
            questions.append(dq)

    return questions[:5]


def _parse_feedback(raw: str, default: Dict[str, Any]) -> Dict[str, Any]:
    """Parse feedback + metrics from AI output."""
    feedback_text = ""
    metrics: Dict[str, float] = {}

    for line in raw.split("\n"):
        line = line.strip()
        if line.upper().startswith("FEEDBACK:"):
            feedback_text = line.split(":", 1)[1].strip()
        elif ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            if key in METRIC_KEYS:
                nums = re.findall(r"\d+\.?\d*", val)
                metrics[key] = min(10.0, float(nums[0])) if nums else 5.0

    # Fill missing
    for k in METRIC_KEYS:
        metrics.setdefault(k, 5.0)

    return {
        "feedback": feedback_text or default["feedback"],
        "metrics": metrics,
    }


def _parse_evaluation(raw: str) -> Dict[str, Any]:
    """Parse comprehensive evaluation from AI output."""
    evaluation_text = ""
    question_feedback: List[Dict] = []
    strengths: List[str] = []
    improvements: List[str] = []
    final_metrics: Dict[str, float] = {}

    lines = raw.split("\n")
    current_q: Dict[str, Any] = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("OVERALL:"):
            evaluation_text = line.split(":", 1)[1].strip()
            # Collect continuation paragraphs
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if nxt.startswith("Q") and ":" in nxt and len(nxt.split(":")[0]) <= 3:
                    break
                if nxt:
                    evaluation_text += " " + nxt
                j += 1

        elif re.match(r"^Q\d+:", line):
            if current_q and current_q.get("question"):
                question_feedback.append(current_q)
            current_q = {"question": line.split(":", 1)[1].strip()}

        elif line.startswith("ANSWER_SUMMARY:"):
            current_q["answer_summary"] = line.split(":", 1)[1].strip()

        elif line.startswith("SAMPLE_ANSWER:"):
            sample = line.split(":", 1)[1].strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(("FEEDBACK:", "SCORE:", "Q")):
                sample += " " + lines[j].strip()
                j += 1
            current_q["sample_answer"] = sample

        elif line.startswith("FEEDBACK:"):
            current_q["feedback"] = line.split(":", 1)[1].strip()

        elif line.startswith("SCORE:"):
            nums = re.findall(r"\d+\.?\d*", line)
            current_q["score"] = float(nums[0]) if nums else 5.0

        elif line.startswith("STRENGTHS:"):
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("-"):
                strengths.append(lines[j].strip().lstrip("- "))
                j += 1

        elif line.startswith("IMPROVEMENTS:"):
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("-"):
                improvements.append(lines[j].strip().lstrip("- "))
                j += 1

        elif ":" in line and any(sk in line for sk in METRIC_KEYS):
            key, val = line.split(":", 1)
            key = key.strip()
            if key in METRIC_KEYS:
                nums = re.findall(r"\d+\.?\d*", val)
                final_metrics[key] = min(10.0, float(nums[0])) if nums else 5.0

        i += 1

    # Save last question
    if current_q and current_q.get("question"):
        question_feedback.append(current_q)

    # Fill missing metrics
    for k in METRIC_KEYS:
        final_metrics.setdefault(k, 5.0)

    # Build rich evaluation
    if strengths:
        evaluation_text += "\n\n### Key Strengths:\n" + "".join(f"✓ {s}\n" for s in strengths)
    if improvements:
        evaluation_text += "\n\n### Areas for Improvement:\n" + "".join(f"• {i}\n" for i in improvements)

    avg = sum(final_metrics.values()) / len(final_metrics) if final_metrics else 5.0

    return {
        "evaluation": evaluation_text,
        "metrics": final_metrics,
        "average_rating": avg,
        "question_feedback": question_feedback,
        "strengths": strengths,
        "improvements": improvements,
    }


def _fallback_evaluation(interactions: Dict[str, str], roles: List[str]) -> Dict[str, Any]:
    """Generate a meaningful evaluation when AI fails."""
    answer_lengths = [len(a) for a in interactions.values()]
    avg_len = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0

    # Heuristic scoring
    base = 5.0
    if avg_len > 300:
        base += 2.0
    elif avg_len > 150:
        base += 1.5
    elif avg_len > 80:
        base += 1.0
    elif avg_len < 30:
        base -= 2.0

    metrics = {
        "Communication skills": min(10, max(0, base + 0.5)),
        "Teamwork and collaboration": min(10, max(0, base)),
        "Problem-solving and critical thinking": min(10, max(0, base + 0.3)),
        "Time management and organization": min(10, max(0, base - 0.2)),
        "Adaptability and resilience": min(10, max(0, base + 0.2)),
    }

    evaluation = (
        f"## ⚠️ System Evaluation (AI Offline)\n"
        f"**Note:** AI analysis is currently unavailable. This is a simplified evaluation based on response metrics.\n\n"
        f"Thank you for completing the mock interview for **{', '.join(roles)}**.\n\n"
        f"You answered {len(interactions)} questions with an average response length of "
        f"{avg_len:.0f} characters.\n\n"
        "### General Recommendations:\n"
        "1. Use the STAR method for behavioral questions\n"
        "2. Quantify achievements with numbers and metrics\n"
        "3. Relate your answers to the job requirements\n"
        "4. Practice speaking about your projects and their impact\n"
    )

    question_feedback = []
    for q, a in interactions.items():
        alen = len(a)
        if alen > 200:
            score = 7.0 + min(alen, 500) / 500
            fb = "Good detailed answer. Consider adding more specific metrics."
        elif alen > 80:
            score = 5.5 + alen / 240
            fb = "Adequate but could be more detailed with specific examples."
        else:
            score = 3.0 + alen / 80
            fb = "Too brief. Expand with examples and explain your thought process."
        question_feedback.append({
            "question": q,
            "answer_summary": a[:100] + ("..." if len(a) > 100 else ""),
            "sample_answer": "Based on your background, provide specific projects, technologies used, and measurable outcomes.",
            "feedback": fb,
            "score": min(10.0, max(0.0, score)),
        })

    avg_rating = sum(metrics.values()) / len(metrics)

    return {
        "evaluation": evaluation,
        "metrics": metrics,
        "average_rating": avg_rating,
        "question_feedback": question_feedback,
        "strengths": [
            "Completed all interview questions",
            "Showed willingness to engage",
            "Demonstrated interest in the role",
        ],
        "improvements": [
            "Provide more detailed, specific examples",
            "Use the STAR method for behavioral responses",
            "Quantify achievements with concrete numbers",
        ],
        "is_fallback": True,
    }


def is_available() -> bool:
    """Check if at least one AI provider is configured."""
    return bool(os.getenv("GROQ_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENROUTER_API_KEY"))

def get_provider_status() -> Dict[str, str]:
    """Return the configuration status of each provider."""
    return {
        "groq": "configured" if os.getenv("GROQ_API_KEY") else "not configured",
        "gemini": "configured" if os.getenv("GOOGLE_API_KEY") else "not configured",
        "openrouter": "configured" if os.getenv("OPENROUTER_API_KEY") else "not configured",
    }
