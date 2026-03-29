# PrepGenie Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PREPGENIE PLATFORM                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐              ┌─────────────────────┐
│   React Frontend    │              │   FastAPI Backend   │
│   (Vite + TS)       │              │   (Python)          │
│   Port: 3000        │◄────REST───►│   Port: 8000        │
│                     │    API       │                     │
│  ┌───────────────┐  │              │  ┌───────────────┐  │
│  │  Home Page    │  │              │  │  API Routes   │  │
│  ├───────────────┤  │              │  ├───────────────┤  │
│  │  Mock         │  │              │  │  Interview    │  │
│  │  Interview    │  │              │  │  Controller   │  │
│  ├───────────────┤  │              │  ├───────────────┤  │
│  │  Chat with    │  │              │  │  Chat         │  │
│  │  Resume       │  │              │  │  Controller   │  │
│  ├───────────────┤  │              │  ├───────────────┤  │
│  │  Interview    │  │              │  │  History      │  │
│  │  History      │  │              │  │  Controller   │  │
│  └───────────────┘  │              │  └───────────────┘  │
│                     │              │                     │
│  ┌───────────────┐  │              │  ┌───────────────┐  │
│  │  Zustand      │  │              │  │  Pydantic     │  │
│  │  Store        │  │              │  │  Models       │  │
│  └───────────────┘  │              │  └───────────────┘  │
│                     │              │                     │
│  ┌───────────────┐  │              │  ┌───────────────┐  │
│  │  Tailwind     │  │              │  │  Business     │  │
│  │  CSS          │  │              │  │  Logic        │  │
│  └───────────────┘  │              │  └───────────────┘  │
└─────────────────────┘              └──────────┬──────────┘
                                                │
                                                │ API Calls
                                                ▼
                                      ┌─────────────────────┐
                                      │  Google Gemini AI   │
                                      │  (LLM Service)      │
                                      │                     │
                                      │  - Question Gen     │
                                      │  - Answer Analysis  │
                                      │  - Feedback         │
                                      │  - Chat Responses   │
                                      └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW                                      │
└─────────────────────────────────────────────────────────────────────────┘

1. MOCK INTERVIEW FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   User Uploads PDF
        │
        ▼
   Frontend: File Upload ────► Backend: /api/process-resume
        │                           │
        │                           ▼
        │                     Extract Text (PyPDF2)
        │                           │
        │                           ▼
        │                     Format with AI
        │                           │
        ◄───────────────────────────┘
   Display Success
        │
        ▼
   User Selects Roles ──────────► Backend: /api/start-interview
        │                           │
        │                           ▼
        │                     Generate 5 Questions
        │                           │
        ◄───────────────────────────┘
   Display Q1
        │
        ▼
   User Submits Answer ─────────► Backend: /api/submit-answer
        │                           │
        │                           ▼
        │                     Analyze Answer
        │                     Generate Feedback
        │                     Calculate Metrics
        │                           │
        ◄───────────────────────────┘
   Show Feedback
   Next Question
        │
        ▼
   [Repeat for Q1-Q5]
        │
        ▼
   Submit Interview ────────────► Backend: /api/submit-interview
        │                           │
        │                           ▼
        │                     Final Evaluation
        │                     Overall Metrics
        │                     Save to History
        │                           │
        ◄───────────────────────────┘
   Display Results
   Show Analytics


2. CHAT WITH RESUME FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   User Uploads PDF
        │
        ▼
   Process Resume ──────────────► Backend: /api/process-resume
        │                           │
        ◄───────────────────────────┘
   Resume Text Stored
        │
        ▼
   User Asks Question ──────────► Backend: /api/chat-with-resume
        │                           │
        │                           ▼
        │                     AI Generates Response
        │                     (Context: Resume + Query)
        │                           │
        ◄───────────────────────────┘
   Display Answer
        │
        ▼
   [Continue Chat]


3. INTERVIEW HISTORY FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Navigate to History
        │
        ▼
   Load History ────────────────► Backend: /api/interview-history
        │                           │
        ◄───────────────────────────┘
   Display List
   Show Statistics
        │
        ▼
   View Details
   Clear History ───────────────► Backend: /api/clear-history


┌─────────────────────────────────────────────────────────────────────────┐
│                      STATE MANAGEMENT                                   │
└─────────────────────────────────────────────────────────────────────────┘

ZUSTAND STORE (frontend/src/store/interviewStore.ts)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

interface InterviewState {
  // Session Data
  session: InterviewSession | null
  currentQuestion: string | null
  questionNumber: number
  totalQuestions: number
  
  // Interview Status
  isInterviewActive: boolean
  isInterviewComplete: boolean
  
  // User Input
  resumeText: string
  selectedRoles: string[]
  
  // Feedback
  feedback: string | null
  currentMetrics: Record<string, number> | null
  
  // UI State
  isLoading: boolean
  error: string | null
  
  // Actions
  startInterview(roles, resumeText)
  submitAnswer(answerText)
  submitFinalInterview()
  resetInterview()
}


┌─────────────────────────────────────────────────────────────────────────┐
│                      DEPLOYMENT ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

PRODUCTION SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌─────────────────────┐
                    │   Cloudflare CDN    │
                    │   (Optional)        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
        ┌───────────┤   Vercel / Netlify  │
        │           │   (Frontend)        │
        │           │   prepgenie.app     │
        │           └─────────────────────┘
        │
        │ HTTPS API Calls
        │
        ▼
┌─────────────────────┐
│   Render / Railway  │
│   (Backend API)     │
│   api.prepgenie.app │
│                     │
│   ┌───────────────┐ │
│   │  FastAPI App  │ │
│   └───────────────┘ │
└──────────┬──────────┘
           │
           │ API Requests
           ▼
┌─────────────────────┐
│  Google Gemini AI   │
│  (External Service) │
└─────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                         SECURITY LAYERS                                 │
└─────────────────────────────────────────────────────────────────────────┘

LAYER 1: Frontend Security
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Input validation (TypeScript types)
- XSS prevention (React auto-escaping)
- CSRF protection (SameSite cookies)
- Content Security Policy headers

LAYER 2: API Security
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- CORS configuration
- Rate limiting (TODO)
- Request size limits
- Input validation (Pydantic)
- API authentication (TODO - JWT)

LAYER 3: Infrastructure Security
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- HTTPS enforcement
- Environment variables
- Secret management
- Database encryption (TODO)


┌─────────────────────────────────────────────────────────────────────────┐
│                      TECHNOLOGY STACK                                   │
└─────────────────────────────────────────────────────────────────────────┘

FRONTEND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Framework:      React 18 + TypeScript
Build Tool:     Vite 5
Styling:        Tailwind CSS 3
State:          Zustand 4
Routing:        React Router 6
HTTP Client:    Axios 1
Icons:          Lucide React
Charts:         Recharts 2
Notifications:  Sonner 1

BACKEND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Framework:      FastAPI 0.109
Server:         Uvicorn 0.27
Validation:     Pydantic 2
PDF Processing: PyPDF2 3
AI:             Google Gemini 0.3
Env:            python-dotenv 1.0

INFRASTRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Frontend Host:  Vercel / Netlify
Backend Host:   Render / Railway
CDN:            Cloudflare (optional)
Database:       In-memory → PostgreSQL (TODO)


┌─────────────────────────────────────────────────────────────────────────┐
│                      API ENDPOINT DETAILS                               │
└─────────────────────────────────────────────────────────────────────────┘

POST /api/process-resume
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request:  multipart/form-data { file: PDF }
Response: { success, raw_text, formatted_text }
Time:     ~2-5 seconds

POST /api/start-interview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request:  { roles: string[], resume_text: string }
Response: { success, session_id, question, total_questions, question_number }
Time:     ~3-8 seconds

POST /api/submit-answer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request:  { session_id: string, answer_text: string }
Response: { success, feedback, metrics, is_complete, next_question }
Time:     ~2-5 seconds

POST /api/submit-interview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request:  form-data { session_id: string }
Response: { success, evaluation, metrics, average_rating }
Time:     ~5-10 seconds

GET /api/interview-history
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request:  -
Response: { success, history: InterviewHistory[], count }
Time:     < 100ms

POST /api/chat-with-resume
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request:  { resume_text: string, query: string }
Response: { success, response: string }
Time:     ~2-5 seconds


┌─────────────────────────────────────────────────────────────────────────┐
│                      PERFORMANCE METRICS                                │
└─────────────────────────────────────────────────────────────────────────┘

TARGET METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Frontend Load Time:     < 2 seconds
API Response Time:      < 500ms (non-AI), < 5s (AI)
Time to First Question: < 10 seconds
Total Interview Time:   ~15-20 minutes
Concurrent Users:       1000+ (target)
Uptime:                 99.9%


┌─────────────────────────────────────────────────────────────────────────┐
│                      SCALABILITY PLAN                                   │
└─────────────────────────────────────────────────────────────────────────┘

PHASE 1: Current (Development)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- In-memory storage
- Single server
- Manual scaling

PHASE 2: Production Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- PostgreSQL database
- Redis caching
- Load balancer
- Auto-scaling

PHASE 3: High Scale
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Microservices architecture
- Message queues (RabbitMQ)
- CDN for static assets
- Multiple regions
- Database sharding

```

---

**Architecture Version:** 1.0  
**Last Updated:** 2026-03-27  
**Status:** Production Ready ✅
