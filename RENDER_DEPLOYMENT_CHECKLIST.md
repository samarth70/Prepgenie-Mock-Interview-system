# ✅ Render Deployment Checklist

**Project:** PrepGenie  
**Version:** 3.2.0  
**Platform:** Render.com  
**Created by:** Samarth Agarwal

---

## 📋 Pre-Deployment Checklist

### Files Ready
- [x] `render.yaml` - Render configuration
- [x] `backend/main.py` - FastAPI application
- [x] `backend/requirements.txt` - Python dependencies
- [x] `backend/database_render.py` - Database layer
- [x] `backend/ai_service.py` - AI service
- [x] `.renderignore` - Files to ignore
- [x] `RENDER_DEPLOYMENT_GUIDE.md` - Deployment guide
- [x] `deploy-to-render.bat` / `.sh` - Deployment scripts

### Code Updates
- [x] Removed Cloudflare-specific code
- [x] Updated CORS configuration
- [x] Added health check endpoint
- [x] In-memory database for free tier
- [x] Proper error handling
- [x] Logging configured

---

## 🚀 Deployment Steps

### Step 1: Push to GitHub ⏳

```bash
# Run the deployment script
deploy-to-render.bat    # Windows
# or
./deploy-to-render.sh   # Mac/Linux
```

**OR manually:**

```bash
git init
git add .
git commit -m "Deploy to Render"
git remote add origin https://github.com/YOUR_USERNAME/prepgenie.git
git branch -M main
git push -u origin main
```

- [ ] Code pushed to GitHub
- [ ] Repository is public (or Render connected)

---

### Step 2: Deploy on Render ⏳

1. [ ] Go to https://render.com
2. [ ] Sign up / Log in
3. [ ] Click **"New +"** → **"Blueprint"**
4. [ ] Connect GitHub account (if first time)
5. [ ] Select `prepgenie` repository
6. [ ] Click **"Connect"**
7. [ ] Review configuration
8. [ ] Click **"Apply"**

---

### Step 3: Configure Environment Variables ⏳

Go to **prepgenie-api** → **Environment** tab:

- [ ] Add `GOOGLE_API_KEY` = `your_key_here`
- [ ] Add `GROQ_API_KEY` = `your_key_here` (optional)
- [ ] Add `OPENROUTER_API_KEY` = `your_key_here` (optional)
- [ ] Add `CORS_ORIGINS` = `https://prepgenie.onrender.com` (optional)
- [ ] Click **"Save Changes"**

**Get API Keys:**
- Google: https://makersuite.google.com/app/apikey
- Groq: https://console.groq.com/keys
- OpenRouter: https://openrouter.ai/keys

---

### Step 4: Monitor Deployment ⏳

1. [ ] Go to **Logs** tab
2. [ ] Watch for successful startup:
   ```
   INFO:     Started server process
   INFO:     PrepGenie API starting up...
   INFO:     PrepGenie API ready!
   ```
3. [ ] Check for errors
4. [ ] Wait for "Deployed" status

**Deployment URL:** `https://prepgenie-api-<random>.onrender.com`

---

## ✅ Post-Deployment Testing

### Test 1: Health Check
```bash
curl https://prepgenie-api-<random>.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "creator": "Samarth Agarwal",
  "ai_providers": {
    "groq": "configured",
    "gemini": "configured"
  },
  "platform": "Render.com",
  "version": "3.2.0"
}
```

- [ ] Health endpoint returns 200
- [ ] Status is "healthy"
- [ ] At least one AI provider configured

---

### Test 2: Root Endpoint
```bash
curl https://prepgenie-api-<random>.onrender.com/
```

Expected:
```json
{
  "message": "Welcome to PrepGenie API",
  "creator": "Samarth Agarwal",
  "status": "online",
  "platform": "Render.com"
}
```

- [ ] Root endpoint works
- [ ] Creator name shows

---

### Test 3: Process Resume
```bash
curl -X POST https://prepgenie-api-<random>.onrender.com/api/process-resume \
  -F "file=@test_resume.pdf"
```

- [ ] File upload works
- [ ] Returns success: true
- [ ] Extracts text from PDF

---

### Test 4: Start Interview
```bash
curl -X POST https://prepgenie-api-<random>.onrender.com/api/start-interview \
  -H "Content-Type: application/json" \
  -d '{"roles": ["Developer"], "resume_text": "Test resume"}'
```

Expected:
```json
{
  "success": true,
  "session_id": "...",
  "question": "...",
  "total_questions": 5
}
```

- [ ] Interview starts
- [ ] Session ID returned
- [ ] First question generated

---

### Test 5: Submit Answer
```bash
curl -X POST https://prepgenie-api-<random>.onrender.com/api/submit-answer \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "answer_text": "My answer here"}'
```

- [ ] Answer submitted
- [ ] Feedback returned
- [ ] Metrics calculated

---

### Test 6: Get History
```bash
curl https://prepgenie-api-<random>.onrender.com/api/history
```

- [ ] History endpoint works
- [ ] Returns interview list
- [ ] Count is correct

---

## 🔧 Troubleshooting

### Issue: Deployment Fails

**Check:**
- [ ] `render.yaml` is in root directory
- [ ] `requirements.txt` is in `backend/` folder
- [ ] No syntax errors in Python files
- [ ] All dependencies are valid

**View build logs in Render dashboard**

---

### Issue: 500 Errors

**Check:**
- [ ] API keys are set correctly
- [ ] No typos in environment variable names
- [ ] Logs show no import errors
- [ ] Health endpoint works first

---

### Issue: Slow Response

**Normal for free tier:**
- First request after 15 min idle = cold start (30-60 sec)
- Subsequent requests = fast (1-3 sec)

**Solution:** Upgrade to Starter plan ($7/month)

---

### Issue: CORS Errors

**Fix:**
1. Add `CORS_ORIGINS` environment variable
2. Include your frontend URL
3. Redeploy

Example:
```
CORS_ORIGINS=https://prepgenie.onrender.com,https://myapp.vercel.app
```

---

## 📊 Monitoring

### Daily Checks
- [ ] Health endpoint responds
- [ ] No errors in logs
- [ ] API keys still valid
- [ ] Disk usage < 1GB

### Weekly Checks
- [ ] Review usage stats
- [ ] Check for dependency updates
- [ ] Review error logs
- [ ] Test all endpoints

---

## 🎯 Success Criteria

All checked = Deployment successful! ✅

- [ ] Code deployed to GitHub
- [ ] Render Blueprint applied
- [ ] Environment variables set
- [ ] Health check passes
- [ ] All API endpoints work
- [ ] No errors in logs
- [ ] Frontend can connect (if applicable)
- [ ] Interview flow complete (start → answer → evaluate)

---

## 📞 Support Resources

- **Render Dashboard:** https://dashboard.render.com
- **Render Docs:** https://render.com/docs
- **Status Page:** https://status.render.com
- **Community:** https://community.render.com
- **Deployment Guide:** `RENDER_DEPLOYMENT_GUIDE.md`

---

## 🎉 Deployment Complete!

Once all tests pass:

1. **Save your API URL:** `https://prepgenie-api-<random>.onrender.com`
2. **Update frontend** `.env` with the API URL
3. **Share your app!**
4. **Monitor usage** in Render dashboard
5. **Consider upgrading** if going to production

---

**Created by Samarth Agarwal**  
**PrepGenie v3.2.0**  
**Deployed to Render.com** 🚀
