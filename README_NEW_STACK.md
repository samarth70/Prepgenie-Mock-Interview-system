# PrepGenie - AI Mock Interview Platform

A modern, full-stack interview preparation application built with React (Vite) + FastAPI.

![PrepGenie](./prep_genie_logo.png)

## 🚀 Tech Stack

### Frontend
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **State Management:** Zustand
- **Routing:** React Router v6
- **HTTP Client:** Axios
- **UI Components:** Lucide React Icons
- **Notifications:** Sonner
- **Markdown:** React Markdown

### Backend
- **Framework:** FastAPI
- **Server:** Uvicorn
- **AI:** Google Gemini (LLM-based generation)
- **PDF Processing:** PyPDF2
- **Validation:** Pydantic

### Architecture
- API-driven, state-aware adaptive logic
- RESTful API design
- Session-based interview tracking
- Real-time feedback generation

## ✨ Features

### 1. Mock Interview
- Upload your resume (PDF)
- Select from multiple job roles
- Get exactly 5 personalized interview questions
- Answer via text or audio recording
- Receive real-time feedback and metrics
- Final comprehensive evaluation

### 2. Chat with Resume
- Interactive chat about your resume
- Get improvement suggestions
- Ask specific questions about content
- AI-powered recommendations

### 3. Interview History
- Track all past interviews
- View detailed analytics
- Compare performance over time
- Access previous evaluations

## 📋 Interview Flow

1. **Upload Resume** → PDF processing and text extraction
2. **Select Roles** → Choose target job position(s)
3. **Start Interview** → AI generates 5 personalized questions
4. **Answer Questions** → One at a time with feedback
5. **Submit Interview** → Get comprehensive evaluation

### Question Categories
Each interview includes exactly 5 questions covering:
- Introduction/Background (based on resume)
- Technical Skills (role-specific)
- Behavioral (teamwork/collaboration)
- Problem-Solving (situational)
- Career Goals (personal/professional)

## 🛠️ Installation

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Unix

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # Windows
# cp .env.example .env  # Unix

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_key_here

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
copy .env.example .env  # Windows
# cp .env.example .env  # Unix

# Run development server
npm run dev

# Build for production
npm run build
```

## 🌐 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API health check |
| GET | `/health` | Detailed health status |
| POST | `/api/process-resume` | Upload and process PDF resume |
| POST | `/api/start-interview` | Start new interview session |
| POST | `/api/submit-answer` | Submit answer for current question |
| POST | `/api/submit-interview` | Submit completed interview for evaluation |
| GET | `/api/interview-history` | Get all interview history |
| DELETE | `/api/clear-history` | Clear interview history |
| POST | `/api/chat-with-resume` | Chat about resume content |

### Example Request/Response

#### Start Interview
```bash
POST /api/start-interview
Content-Type: application/json

{
  "roles": ["Software Engineer", "Full Stack Developer"],
  "resume_text": "Experienced developer with..."
}
```

```json
{
  "success": true,
  "session_id": "uuid-here",
  "question": "Tell me about your experience...",
  "total_questions": 5,
  "question_number": 1
}
```

## 📊 State Management

The application uses Zustand for lightweight, centralized state management:

```typescript
interface InterviewState {
  session: InterviewSession | null;
  currentQuestion: string | null;
  questionNumber: number;
  totalQuestions: number;
  isInterviewActive: boolean;
  isInterviewComplete: boolean;
  resumeText: string;
  selectedRoles: string[];
  feedback: string | null;
  currentMetrics: Record<string, number> | null;
}
```

## 🎨 UI Components

### Key Pages
- **Home** (`/`) - Landing page with feature overview
- **Mock Interview** (`/interview`) - Main interview interface
- **Chat with Resume** (`/chat`) - Interactive chat interface
- **Interview History** (`/history`) - Analytics and history

### Design System
- **Colors:** Primary blue gradient palette
- **Typography:** Inter font family
- **Icons:** Lucide React
- **Animations:** Smooth transitions, hover effects
- **Responsive:** Mobile-first design

## 🔒 Security Considerations

For production deployment:

1. **API Authentication:** Implement JWT or session-based auth
2. **CORS:** Configure allowed origins properly
3. **Rate Limiting:** Add request throttling
4. **File Upload:** Validate file types and sizes
5. **Environment Variables:** Never commit `.env` files
6. **Database:** Replace in-memory storage with PostgreSQL/MongoDB

## 🚀 Deployment

### Backend (Render/Railway)

```yaml
# render.yaml
services:
  - type: web
    name: prepgenie-api
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel/Netlify)

```json
// vercel.json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "devCommand": "cd frontend && npm run dev"
}
```

## 📈 Performance Optimization

- **Lazy Loading:** Code-splitting for routes
- **Caching:** API response caching
- **Compression:** Gzip/Brotli for API responses
- **CDN:** Static assets via CDN
- **Database Indexing:** For production DB

## 🧪 Testing

```bash
# Backend tests (pytest)
cd backend
pytest

# Frontend tests (Vitest)
cd frontend
npm test
```

## 📝 License

Apache 2.0 License

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- FastAPI for the amazing backend framework
- React and Vite communities
- All contributors

---

**Built with ❤️ using React + FastAPI**
