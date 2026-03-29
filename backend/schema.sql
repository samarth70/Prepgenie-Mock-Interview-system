-- PrepGenie D1 Schema
-- Use 'npx wrangler d1 execute prepgenie-db --file=backend/schema.sql' to apply

-- Session storage for active interviews
CREATE TABLE IF NOT EXISTS interview_sessions (
    session_id TEXT PRIMARY KEY,
    roles_json TEXT DEFAULT '[]',
    resume_text TEXT DEFAULT '',
    questions_json TEXT DEFAULT '[]',
    current_question_index INTEGER DEFAULT 0,
    answers_json TEXT DEFAULT '[]',
    interactions_json TEXT DEFAULT '{}',
    feedback_json TEXT DEFAULT '[]',
    metrics_list_json TEXT DEFAULT '[]',
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- History storage for completed interviews
CREATE TABLE IF NOT EXISTS interview_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    roles_json TEXT DEFAULT '[]',
    interactions_json TEXT DEFAULT '{}',
    feedback_json TEXT DEFAULT '[]',
    metrics_json TEXT DEFAULT '{}',
    average_rating REAL DEFAULT 0.0,
    evaluation TEXT DEFAULT '',
    question_feedback_json TEXT DEFAULT '[]',
    strengths_json TEXT DEFAULT '[]',
    improvements_json TEXT DEFAULT '[]',
    is_fallback INTEGER DEFAULT 0
);
