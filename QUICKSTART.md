# Quick Start Guide for PrepGenie

## Overview
This document provides quick start instructions for both the existing Gradio app and the new React+FastAPI stack.

---

## Option 1: Existing Gradio App (Quick Test)

### Prerequisites
- Python 3.8+
- Google API Key (Gemini)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "GOOGLE_API_KEY=your_key_here" > .env

# Run the app
python app.py
```

Access at: `http://localhost:7860`

---

## Option 2: New React + FastAPI Stack (Production Ready)

### Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Unix/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
# cp .env.example .env  # Unix/Mac

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_key_here

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend API running at: `http://localhost:8000`
API Docs at: `http://localhost:8000/docs`

### Frontend Setup (New Terminal)
```bash
cd frontend

# Install dependencies
npm install

# Create .env file
copy .env.example .env  # Windows
# cp .env.example .env  # Unix/Mac

# Start development server
npm run dev
```

Frontend running at: `http://localhost:3000`

---

## Key Differences

### Gradio App (Current)
✅ Quick to test
✅ Single file deployment
✅ Built-in UI components
❌ Limited customization
❌ Not production-ready UI
❌ Monolithic architecture

### React + FastAPI (New Stack)
✅ Production-ready
✅ Modern, responsive UI
✅ Separated concerns (frontend/backend)
✅ Better scalability
✅ Easier to maintain
✅ API-driven architecture
❌ Requires more setup
❌ Two services to run

---

## Troubleshooting

### Backend Issues

**Error: Module not found**
```bash
pip install -r requirements.txt --upgrade
```

**Error: Google API Key invalid**
- Check your API key in `.env`
- Ensure no extra spaces or quotes
- Verify API key is active in Google Cloud Console

**Error: Port already in use**
```bash
# Change port in uvicorn command
uvicorn main:app --reload --port 8001
```

### Frontend Issues

**Error: npm install fails**
```bash
# Clear cache and retry
npm cache clean --force
npm install
```

**Error: Cannot connect to backend**
- Ensure backend is running on port 8000
- Check `.env` has correct `VITE_API_URL`
- Check CORS settings in `backend/main.py`

**Error: Build fails**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## Testing the Application

### 1. Test Mock Interview
1. Navigate to Mock Interview tab
2. Upload a PDF resume
3. Click "Process Resume"
4. Select 1+ job roles
5. Click "Start Interview"
6. Answer all 5 questions
7. Submit for evaluation

### 2. Test Chat with Resume
1. Navigate to Chat with Resume tab
2. Upload a PDF resume
3. Click "Process Resume"
4. Ask questions about the resume
5. Get AI-powered suggestions

### 3. Test Interview History
1. Navigate to Interview History tab
2. Click "Load My Past Interviews"
3. View statistics and past interviews
4. Clear history if needed

---

## Production Deployment

### Backend (Render)
1. Create new Web Service on Render
2. Connect your GitHub repo
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `GOOGLE_API_KEY`

### Frontend (Vercel)
1. Import project to Vercel
2. Set root directory: `frontend`
3. Set build command: `npm run build`
4. Set output directory: `dist`
5. Add environment variable: `VITE_API_URL` (your Render backend URL)

---

## Architecture Diagram

```
┌─────────────────┐         ┌─────────────────┐
│   React (Vite)  │◄───────►│   FastAPI       │
│   Frontend      │  REST   │   Backend       │
│   :3000         │   API   │   :8000         │
└─────────────────┘         └────────┬────────
                                     │
                                     ▼
                              ┌─────────────────┐
                              │  Google Gemini  │
                              │  AI API         │
                              └─────────────────┘
```

---

## Next Steps

1. **Customize Roles:** Edit role options in `frontend/src/pages/MockInterview.tsx`
2. **Add Authentication:** Implement user login/signup
3. **Database:** Replace in-memory storage with PostgreSQL
4. **Audio Processing:** Add speech-to-text for audio answers
5. **Analytics:** Add more detailed performance metrics

---

## Support

For issues or questions:
- Check API logs: `backend/` terminal
- Check browser console: `frontend/` terminal
- Review API docs: `http://localhost:8000/docs`

---

**Happy Interviewing! 🚀**
