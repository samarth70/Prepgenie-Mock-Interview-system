# Deploying PrepGenie to Render

## Overview
This guide explains how to deploy PrepGenie backend to Render.com

## Prerequisites
- GitHub account with your code pushed
- Render account (free tier available)
- Google API Key (and optionally Groq/OpenRouter)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your code is pushed to GitHub with the proper structure:
```
PrepGenie/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── ai_service.py        # AI service
│   ├── database.py          # Database ops
│   ├── requirements.txt     # Python dependencies
│   └── schema.sql           # Database schema
├── frontend/
│   └── dist/                # Built frontend (optional)
└── README.md
```

### 2. Create a Render Blueprint File

Create `render.yaml` in your project root:

```yaml
services:
  - type: web
    name: prepgenie-api
    env: python
    region: oregon
    plan: free
    branch: main
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: DATABASE_URL
        generateValue: postgresql://...
        sync: false
    disk:
      name: data
      mountPath: /opt/render/project/src/data
      sizeGB: 1
```

### 3. Update requirements.txt

Ensure `backend/requirements.txt` has:
```
fastapi
uvicorn
pypdf
pydantic
python-dotenv
httpx
google-generativeai
```

### 4. Deploy on Render

1. Go to https://render.com and sign in
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Select the `render.yaml` file
5. Click "Apply"

### 5. Set Environment Variables

After deployment starts:
1. Go to your service dashboard
2. Click "Environment" tab
3. Add your API keys:
   - `GOOGLE_API_KEY`
   - `GROQ_API_KEY` (optional)
   - `OPENROUTER_API_KEY` (optional)

### 6. Access Your API

Once deployed, your API will be available at:
```
https://prepgenie-api.onrender.com
```

Test endpoints:
- Health: `https://prepgenie-api.onrender.com/health`
- API Docs: `https://prepgenie-api.onrender.com/docs`

## Alternative: Manual Setup

If you prefer not to use Blueprints:

1. **Create New Web Service**
   - Dashboard → New + → Web Service
   - Connect your GitHub repo

2. **Configure Build**
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   - Add all required API keys

4. **Deploy**
   - Click "Create Web Service"

## Database Setup

### Option A: Render PostgreSQL (Recommended)

1. Dashboard → New + → PostgreSQL
2. Choose free tier
3. Copy the internal database URL
4. Add as `DATABASE_URL` environment variable

### Option B: SQLite (Simple, Free)

Modify `database.py` to use SQLite:
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/prepgenie.db"
```

## Frontend Deployment

### Deploy Frontend Separately

1. **Build locally:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Deploy to Vercel:**
   ```bash
   vercel deploy --prod
   ```

3. **Update API URL:**
   - Set `VITE_API_URL` in frontend `.env`
   - Point to your Render backend URL

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Ensure `requirements.txt` is in the correct location
- Verify Python version (3.8+)

### Runtime Errors
- Check runtime logs
- Verify all environment variables are set
- Test API endpoints individually

### Database Connection Issues
- Verify DATABASE_URL format
- Check database is accessible from Render
- Run migrations if needed

## Cost Estimate

**Free Tier:**
- Web Service: 750 hours/month (enough for 1 service)
- PostgreSQL: 1GB storage, limited hours
- Total: Free (with limitations)

**Paid Tier (if needed):**
- Starter Plan: $7/month per service
- Better performance, no sleep mode

## Support

- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- Community: https://community.render.com

---

**Created by Samarth Agarwal**
**PrepGenie v3.2.0**
