# 🚀 Deploy PrepGenie to Render - START HERE!

**Quick deployment guide for PrepGenie on Render.com**

---

## ⚡ 3-Minute Deployment

### Step 1: Push to GitHub

**Option A - Use the Script (Recommended):**

Windows:
```bash
deploy-to-render.bat
```

Mac/Linux:
```bash
chmod +x deploy-to-render.sh
./deploy-to-render.sh
```

**Option B - Manual:**

```bash
# Initialize and push to GitHub
git init
git add .
git commit -m "Deploy to Render"

# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/prepgenie.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy on Render (2 minutes)

1. **Go to https://render.com** and sign up/login

2. **Click "New +" → "Blueprint"**

3. **Connect your GitHub account** (if first time)

4. **Find and select your `prepgenie` repository**

5. **Click "Connect"**

6. **Review and click "Apply"**

Render will now deploy your application automatically!

---

### Step 3: Add API Keys (1 minute)

1. In Render Dashboard, click on **prepgenie-api**

2. Go to **"Environment"** tab

3. Click **"Add Environment Variable"**

4. Add at least ONE API key:

   | Name | Value | Get From |
   |------|-------|----------|
   | `GOOGLE_API_KEY` | Your key | https://makersuite.google.com/app/apikey |
   | `GROQ_API_KEY` | Your key | https://console.groq.com/keys |

5. Click **"Save Changes"**

---

## ✅ Test Your Deployment

Wait 3-5 minutes for deployment to complete, then test:

```bash
# Replace with your actual Render URL
curl https://prepgenie-api-xyz.onrender.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "creator": "Samarth Agarwal",
  "platform": "Render.com"
}
```

**🎉 Success! Your API is live!**

---

## 📚 Need More Help?

### Detailed Guides
- **Complete Guide:** `RENDER_DEPLOYMENT_GUIDE.md`
- **Checklist:** `RENDER_DEPLOYMENT_CHECKLIST.md`
- **Summary:** `RENDER_DEPLOYMENT_SUMMARY.md`

### Troubleshooting

**Deployment fails?**
- Check build logs in Render dashboard
- Ensure `render.yaml` is in root folder
- Verify `requirements.txt` is in `backend/` folder

**API returns 500?**
- Check API keys are set correctly
- View logs in Render dashboard
- Test health endpoint first

**CORS errors?**
- Add `CORS_ORIGINS` environment variable
- Include your frontend URL

---

## 📊 What You Get

✅ **REST API** for mock interviews  
✅ **AI-powered** question generation  
✅ **Resume processing** (PDF upload)  
✅ **Answer evaluation** with feedback  
✅ **Interview history** tracking  
✅ **Chat with resume** feature  

**Free Tier:** 750 hours/month (enough for 1 service)  
**Upgrade:** $7/month for no sleep mode

---

## 🔗 Your API Endpoints

Once deployed, you'll have these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Welcome message |
| `/health` | GET | Health check ✅ |
| `/api/process-resume` | POST | Upload PDF resume |
| `/api/start-interview` | POST | Start interview |
| `/api/submit-answer` | POST | Submit answer |
| `/api/history` | GET | Get history |
| `/api/clear-history` | POST | Clear history |
| `/api/chat-with-resume` | POST | Chat about resume |

Full API docs: `https://prepgenie-api-xyz.onrender.com/docs`

---

## 🎯 Next Steps After Deployment

1. ✅ **Test all endpoints** (see above)
2. 📱 **Deploy frontend** (Vercel/Netlify)
3. 🔗 **Connect frontend to backend** (update API URL)
4. 📊 **Monitor usage** (Render dashboard)
5. ⬆️ **Upgrade if needed** ($7/month for production)

---

## 📞 Support

- **Render Dashboard:** https://dashboard.render.com
- **Render Docs:** https://render.com/docs
- **Status:** https://status.render.com

---

**Ready? Let's deploy! 🚀**

Start with **Step 1** above or run `deploy-to-render.bat` / `./deploy-to-render.sh`

---

**Created by Samarth Agarwal**  
**PrepGenie v3.2.0**
