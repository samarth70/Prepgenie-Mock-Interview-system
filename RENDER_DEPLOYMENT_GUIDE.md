# 🚀 Deploy PrepGenie to Render - Complete Guide

**Created by:** Samarth Agarwal  
**Version:** 3.2.0  
**Platform:** Render.com

---

## ✅ Quick Start (5 Minutes)

### Step 1: Push to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - PrepGenie ready for Render"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/prepgenie.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. **Go to https://render.com** and sign up/login

2. **Click "New +" → "Blueprint"**

3. **Connect your GitHub repository**
   - Click "Connect account" if first time
   - Find and select your `prepgenie` repository
   - Click "Connect"

4. **Apply the Blueprint**
   - Render will auto-detect `render.yaml`
   - Review the configuration
   - Click "Apply"

### Step 3: Set API Keys

1. Go to your service dashboard: **prepgenie-api**

2. Click **"Environment"** tab

3. Add these environment variables:
   ```
   Key: GOOGLE_API_KEY
   Value: your_google_api_key_here
   
   Key: GROQ_API_KEY  
   Value: your_groq_api_key_here (optional)
   
   Key: OPENROUTER_API_KEY
   Value: your_openrouter_api_key_here (optional)
   ```

4. Click **"Save Changes"**

### Step 4: Wait for Deployment

- Render will automatically start deploying
- Watch the logs in the **"Logs"** tab
- Deployment takes ~3-5 minutes

### Step 5: Test Your API

Once deployed, you'll get a URL like:
```
https://prepgenie-api-xyz.onrender.com
```

Test it:
```bash
curl https://prepgenie-api-xyz.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "creator": "Samarth Agarwal",
  "ai_providers": {
    "groq": "configured",
    "gemini": "configured",
    "openrouter": "configured"
  },
  "platform": "Render.com",
  "version": "3.2.0"
}
```

---

## 📁 Project Structure

```
PrepGenie/
├── backend/
│   ├── main.py                 # FastAPI application ✅
│   ├── ai_service.py           # AI service layer ✅
│   ├── database_render.py      # In-memory database ✅
│   ├── requirements.txt        # Python dependencies ✅
│   └── schema.sql              # Database schema (future)
├── frontend/                   # React app (deploy separately)
├── render.yaml                 # Render configuration ✅
├── .renderignore               # Files to ignore ✅
└── README.md
```

---

## 🔧 Configuration Files

### render.yaml

```yaml
services:
  - type: web
    name: prepgenie-api
    env: python
    region: oregon
    plan: free
    branch: main
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: GOOGLE_API_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: CORS_ORIGINS
        value: https://prepgenie.onrender.com,http://localhost:3000
    disk:
      name: interview-data
      mountPath: /opt/render/project/src/data
      sizeGB: 1
```

### .renderignore

```
__pycache__/
*.pyc
venv/
env/
.env
.env.local
.dev.vars
.vscode/
.idea/
*.log
.git/
```

### requirements.txt

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
httpx>=0.26.0
pypdf>=3.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
google-generativeai>=0.3.0
matplotlib>=3.8.0
numpy>=1.24.0
```

---

## 🔑 Getting API Keys

### Google Gemini API

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key
5. Add to Render environment variables

### Groq API (Optional but Recommended)

1. Go to https://console.groq.com/keys
2. Sign up/login
3. Click "Create API Key"
4. Copy the key
5. Add to Render

### OpenRouter API (Optional)

1. Go to https://openrouter.ai/keys
2. Sign up/login
3. Create API key
4. Copy and add to Render

---

## 🧪 Testing the Deployment

### Test Health Endpoint

```bash
curl https://prepgenie-api-xyz.onrender.com/health
```

### Test Root Endpoint

```bash
curl https://prepgenie-api-xyz.onrender.com/
```

### Test Resume Processing

```bash
curl -X POST https://prepgenie-api-xyz.onrender.com/api/process-resume \
  -F "file=@/path/to/your/resume.pdf"
```

### Test Start Interview

```bash
curl -X POST https://prepgenie-api-xyz.onrender.com/api/start-interview \
  -H "Content-Type: application/json" \
  -d '{
    "roles": ["Software Engineer"],
    "resume_text": "John Doe\nDeveloper\n5 years experience"
  }'
```

### Test Chat with Resume

```bash
curl -X POST https://prepgenie-api-xyz.onrender.com/api/chat-with-resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe\nDeveloper",
    "query": "What are the key skills?"
  }'
```

---

## 📊 Monitoring & Logs

### View Logs

1. Go to Render Dashboard
2. Select **prepgenie-api**
3. Click **"Logs"** tab
4. View real-time logs

### Common Log Messages

✅ **Healthy:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     PrepGenie API starting up...
INFO:     PrepGenie API ready!
```

⚠️ **Missing API Key:**
```
AI providers: groq: not configured, gemini: not configured
```

❌ **Build Error:**
```
ERROR: Could not find a version that satisfies the requirement
```
→ Check `requirements.txt` for typos

---

## 🆘 Troubleshooting

### Deployment Fails

**Problem:** Build fails with "No such file or directory"

**Solution:**
- Ensure `rootDir: backend` in `render.yaml`
- Check `requirements.txt` is in `backend/` folder

### API Returns 500 Error

**Problem:** All endpoints return 500

**Solution:**
1. Check logs in Render dashboard
2. Verify API keys are set correctly
3. Test health endpoint first

### API is Slow to Respond

**Problem:** First request takes 30+ seconds

**Solution:** This is normal for free tier (cold start)
- Upgrade to Starter plan ($7/month) for faster response
- Or use a service like UptimeRobot to keep it warm

### CORS Errors

**Problem:** Frontend can't connect to backend

**Solution:**
1. Set `CORS_ORIGINS` environment variable
2. Include your frontend URL:
   ```
   CORS_ORIGINS=https://prepgenie.onrender.com,https://your-frontend.vercel.app
   ```

---

## 💰 Cost Estimate

### Free Tier
- **750 hours/month** of uptime (enough for 1 service)
- **1 GB** persistent disk
- **Limited** bandwidth
- **Sleeps** after 15 minutes of inactivity

### Starter Plan - $7/month
- No sleep mode
- Faster response times
- More resources
- Recommended for production

---

## 🔄 Updating Your Deployment

### Automatic Deploys

Render automatically deploys when you push to GitHub:

```bash
git add .
git commit -m "Fix bug in interview logic"
git push origin main
```

Render will:
1. Detect the push
2. Start building
3. Deploy when ready
4. Zero downtime!

### Manual Redeploy

1. Go to Render Dashboard
2. Select your service
3. Click **"Manual Deploy"**
4. Select branch
5. Click **"Deploy"**

---

## 🌐 Frontend Deployment (Optional)

### Deploy Frontend to Vercel

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

### Connect Frontend to Backend

1. Create `frontend/.env`:
   ```
   VITE_API_URL=https://prepgenie-api-xyz.onrender.com
   ```

2. Rebuild and redeploy frontend

---

## 📈 Scaling Up

### When to Upgrade

- Need faster response times
- Want to avoid sleep mode
- Exceeding free tier limits
- Production use

### Upgrade Steps

1. Go to Render Dashboard
2. Select service
3. Click **"Upgrade"**
4. Choose **Starter** ($7/month)
5. Confirm

### Add PostgreSQL (Future)

1. New + → PostgreSQL
2. Choose free tier
3. Copy connection string
4. Add as `DATABASE_URL` env var
5. Update `database_render.py` to use SQLAlchemy

---

## 🎯 Next Steps

1. ✅ Deploy to Render
2. ✅ Set API keys
3. ✅ Test all endpoints
4. 📱 Deploy frontend (Vercel/Netlify)
5. 🔒 Add authentication (optional)
6. 📊 Add monitoring (optional)
7. 🎨 Customize branding

---

## 📞 Support

- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Community:** https://community.render.com
- **Status Page:** https://status.render.com

---

## 🎉 Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render Blueprint applied
- [ ] API keys configured
- [ ] Health endpoint returns 200
- [ ] Can start interview
- [ ] Can submit answers
- [ ] Logs show no errors
- [ ] Frontend connected (if deployed)

---

**Congratulations! Your PrepGenie API is now live on Render! 🚀**

**Created by Samarth Agarwal**
