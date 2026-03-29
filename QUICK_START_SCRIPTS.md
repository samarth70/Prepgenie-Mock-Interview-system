# Quick Start Scripts

## 🚀 **Easy Server Startup**

### **Option 1: Start Everything (Recommended)**

Double-click: **`start_servers.bat`** (in root directory)

This will:
- ✅ Start **Backend** server (Port 8000) in one window
- ✅ Start **Frontend** server (Port 3000) in another window
- ✅ Open both in separate command prompt windows
- ✅ Wait 5 seconds between starts

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### **Option 2: Start Individually**

#### **Backend Only:**
1. Navigate to `backend/` folder
2. Double-click: **`start_backend.bat`**

**Or run manually:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### **Frontend Only:**
1. Navigate to `frontend/` folder
2. Double-click: **`start_frontend.bat`**

**Or run manually:**
```bash
cd frontend
npm run dev
```

---

## 📋 **What Each Script Does**

### **`start_servers.bat`** (Root Directory)
```
✅ Checks if running from correct directory
✅ Activates virtual environment (if exists)
✅ Starts backend in new window titled "PrepGenie Backend"
✅ Waits 5 seconds
✅ Starts frontend in new window titled "PrepGenie Frontend"
✅ Shows all URLs
```

### **`start_backend.bat`** (Backend Directory)
```
✅ Checks if running from backend directory
✅ Activates virtual environment (if exists)
✅ Starts uvicorn server on port 8000
✅ Shows API URLs
```

### **`start_frontend.bat`** (Frontend Directory)
```
✅ Checks if running from frontend directory
✅ Starts npm dev server on port 3000
✅ Shows frontend URL
```

---

## 🎨 **Window Colors**

- **Green** (`start_servers.bat`) - Main launcher
- **Cyan** (`start_backend.bat`) - Backend server
- **Blue** (`start_frontend.bat`) - Frontend server

---

## 🛑 **How to Stop**

### **If using `start_servers.bat`:**
- Close both "PrepGenie Backend" and "PrepGenie Frontend" windows
- Or press `CTRL+C` in each window

### **If running individually:**
- Press `CTRL+C` in the command window
- Or just close the window

---

## ⚡ **Quick Commands**

### **Check if servers are running:**
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

### **View API Documentation:**
Open browser: http://localhost:8000/docs

---

## 🐛 **Troubleshooting**

### **Error: "Python not found"**
**Solution:** Install Python 3.8+ or activate your conda environment

### **Error: "npm not found"**
**Solution:** Install Node.js from https://nodejs.org

### **Error: "Port 8000 already in use"**
**Solution:**
```bash
# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

### **Error: "Port 3000 already in use"**
**Solution:**
```bash
# Windows - Find and kill process
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

### **Error: "Module not found"**
**Solution:**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

---

## 📝 **Environment Setup**

### **Backend (.env file):**
Create `backend/.env` with:
```bash
# Google Gemini (Primary)
GOOGLE_API_KEY=your_key_here

# Anthropic Claude (Fallback 1 - Optional)
ANTHROPIC_API_KEY=your_key_here

# Alibaba Qwen (Fallback 2 - Optional)
DASHSCOPE_API_KEY=your_key_here

# Ollama (Fallback 3 - FREE, no key needed!)
# Just install from https://ollama.ai
```

### **Frontend (.env file):**
Create `frontend/.env` with:
```bash
VITE_API_URL=http://localhost:8000
```

---

## 🎯 **Recommended Workflow**

1. **Double-click** `start_servers.bat`
2. Wait for both servers to start
3. Open http://localhost:3000 in browser
4. Test the application
5. When done, close both server windows

---

## 💡 **Pro Tips**

### **1. Create Desktop Shortcut**
Right-click `start_servers.bat` → Send to → Desktop (create shortcut)

### **2. Run as Administrator** (if needed)
Right-click → Run as administrator

### **3. Auto-restart on Changes**
Both servers have `--reload` flag, so they auto-restart when you save code changes!

### **4. View Logs**
- Backend logs show in "PrepGenie Backend" window
- Frontend logs show in "PrepGenie Frontend" window
- Check console for detailed error messages

---

## 📊 **Expected Output**

### **Backend Window:**
```
============================================
    PrepGenie Backend Server
============================================

Starting FastAPI backend...

Server will be available at:
  - API: http://localhost:8000
  - Docs: http://localhost:8000/docs
  - Health: http://localhost:8000/health

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### **Frontend Window:**
```
============================================
    PrepGenie Frontend Server
============================================

Starting Vite development server...

Frontend will be available at:
  - App: http://localhost:3000

  VITE v5.4.21  ready in 600 ms

  ➜  Local:   http://localhost:3000/
```

---

**Now you can start PrepGenie with just a double-click!** 🚀✨
