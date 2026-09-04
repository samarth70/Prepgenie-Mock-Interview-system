"""Compact a resume into the facts downstream prompts actually need.

WHY
---
The full resume was sent verbatim on all seven LLM calls of an interview journey.
Measured against Gemini, that was 3,290 tokens - 57% of all input for a single
interview - to re-state the same document each time.

Question generation genuinely benefits from the whole document. Scoring an answer
and writing the final evaluation do not: they need who the candidate is, their
stack, their roles and roughly how senior they are. This module derives exactly
that, deterministically.

Standard library only. Cloudflare Python Workers run Pyodide and cap startup CPU,
so no third-party dependency is acceptable here - adding fastapi/pydantic once took
the startup baseline to 1338ms against a 1000ms limit and blocked every deploy.

NOT HARDCODED
-------------
Nothing about any particular candidate is baked in. SECTION_WORDS is generic resume
vocabulary and ROLE_WORDS generic job-title vocabulary; every value in the output is
read out of the document being processed. A resume that uses different headings
degrades to fewer fields rather than to wrong ones.
"""

import re
from typing import Dict, List, Optional

__all__ = ["build_digest", "digest_or_full"]

# Headings real resumes use. Matching is prefix-based so "TECHNICAL SKILLS" and
# "Skills:" both land in the same bucket.
SECTION_WORDS = (
    "experience", "employment", "work history", "professional experience",
    "projects", "education", "skills", "technical skills", "certifications",
    "achievements", "summary", "profile", "publications",
)

ROLE_WORDS = (
    "engineer", "developer", "analyst", "associate", "intern", "manager",
    "consultant", "scientist", "architect", "lead", "director", "designer",
    "administrator", "specialist", "researcher",
)

# Only ranges, so a stray "2019" in a project description does not widen the span.
DATE_RANGE = re.compile(r"\b(19|20)(\d{2})\s*[-–—]{1,2}\s*((?:19|20)\d{2}|present|current|now)\b", re.I)
CURRENT_YEAR = 2026

MAX_SKILL_CHARS = 320
MAX_ROLES = 5
MAX_PROJECTS = 5


def _normalise(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _section_key(line: str) -> Optional[str]:
    """Return a canonical section name if this line looks like a heading."""
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > 45:
        return None
    # A heading is short and is not a sentence or a bullet.
    if stripped.startswith(("-", "*", "•")) or stripped.endswith("."):
        return None
    low = stripped.lower()
    for word in SECTION_WORDS:
        if low == word or low.startswith(word):
            return word
    return None


def split_sections(text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current = "_header"
    for raw_line in text.splitlines():
        key = _section_key(raw_line)
        if key:
            current = key
            sections.setdefault(current, [])
            continue
        line = _normalise(raw_line)
        if line:
            sections.setdefault(current, []).append(line)
    return sections


def _find(sections: Dict[str, List[str]], *needles: str) -> List[str]:
    for key, lines in sections.items():
        if any(n in key for n in needles):
            return lines
    return []


def career_span_years(sections: Dict[str, List[str]]) -> Optional[int]:
    """Years spanned by EMPLOYMENT dates only.

    Deliberately ignores the education section: including it turned a 4-year career
    into "8 years" by counting an undergraduate start date.
    """
    lines = _find(sections, "experience", "employment", "work")
    if not lines:
        return None
    years: List[int] = []
    for line in lines:
        for match in DATE_RANGE.finditer(line):
            years.append(int(match.group(1) + match.group(2)))
            end = match.group(3).lower()
            years.append(CURRENT_YEAR if end in ("present", "current", "now") else int(end))
    if not years:
        return None
    span = max(years) - min(years)
    return span if 0 < span <= 50 else None


def extract_name(text: str) -> Optional[str]:
    """First short, non-numeric line - the near-universal resume convention."""
    for raw_line in text.splitlines()[:6]:
        line = _normalise(raw_line)
        if not line or len(line) > 60 or any(c.isdigit() for c in line):
            continue
        if "@" in line or "http" in line.lower():
            continue
        candidate = re.split(r"[|,–-]", line)[0].strip()
        if 2 <= len(candidate) <= 60:
            return candidate
    return None


def extract_roles(sections: Dict[str, List[str]]) -> List[str]:
    roles: List[str] = []
    for line in _find(sections, "experience", "employment", "work"):
        # Bullets describe achievements; the title line carries a date or a job word.
        if line.startswith(("-", "*", "•")):
            continue
        if DATE_RANGE.search(line) or any(w in line.lower() for w in ROLE_WORDS):
            roles.append(re.split(r"[•|]", line)[0].strip()[:90])
        if len(roles) >= MAX_ROLES:
            break
    return list(dict.fromkeys(roles))


def extract_projects(sections: Dict[str, List[str]]) -> List[str]:
    """Project names only.

    Continuation lines are skipped: an earlier version emitted
    "deployed on Cloudflare Pages and Workers." as a project because it began a
    wrapped line. A project title starts a line and is not a lowercase fragment.
    """
    names: List[str] = []
    for line in _find(sections, "projects"):
        if line.startswith(("-", "*", "•")):
            continue
        head = re.split(r"[-–—:(]", line)[0].strip()
        if not head or len(head) > 50 or len(head) < 3:
            continue
        if head[0].islower() or head.endswith(","):
            continue
        names.append(head)
        if len(names) >= MAX_PROJECTS:
            break
    return list(dict.fromkeys(names))


def extract_skills(sections: Dict[str, List[str]]) -> str:
    lines = _find(sections, "skill")
    return " ".join(lines)[:MAX_SKILL_CHARS].strip()


def build_digest(text: str) -> str:
    """A compact factual summary, or '' when the text is too unstructured to trust."""
    if not text or not text.strip():
        return ""

    sections = split_sections(text)
    parts: List[str] = []

    name = extract_name(text)
    if name:
        parts.append(f"Candidate: {name}")

    span = career_span_years(sections)
    if span:
        parts.append(f"Professional experience: about {span} years")

    roles = extract_roles(sections)
    if roles:
        parts.append("Roles held: " + "; ".join(roles))

    projects = extract_projects(sections)
    if projects:
        parts.append("Projects: " + ", ".join(projects))

    skills = extract_skills(sections)
    if skills:
        parts.append("Skills: " + skills)

    return "\n".join(parts)


def digest_or_full(text: str, min_fields: int = 3) -> str:
    """Digest when it captured enough to be useful, otherwise the original text.

    Falling back to the full resume keeps behaviour correct for unusual layouts:
    the cost saving is worth having, but never at the price of scoring a candidate
    against a digest that lost their experience.
    """
    digest = build_digest(text)
    if not digest:
        return text
    if len(digest.splitlines()) < min_fields:
        return text
    # A digest that is not meaningfully smaller is not worth the loss of detail.
    if len(digest) > len(text) * 0.6:
        return text
    return digest
