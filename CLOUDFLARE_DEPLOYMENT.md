# Cloudflare Deployment Guide for PrepGenie

This guide explains how to deploy PrepGenie API to Cloudflare Workers with D1 database.

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+ (for local development)
- Cloudflare account (free tier works)
- Wrangler CLI installed globally

## Quick Start

### 1. Install Wrangler CLI

```bash
npm install -g wrangler
```

### 2. Authenticate with Cloudflare

```bash
wrangler login
```

This will open a browser window. Log in with your Cloudflare account.

### 3. Set Up Environment Variables

Create a `.dev.vars` file in the backend directory for local development:

```bash
cd backend
cp .dev.vars.example .dev.vars
```

Edit `.dev.vars` and add your API keys:

```
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 4. Create D1 Database

```bash
# Create the database
wrangler d1 create prepgenie-db

# Note the database_id from the output and update wrangler.toml
```

Update `wrangler.toml` with the `database_id` from the output.

### 5. Initialize Database Schema

```bash
# Run the schema SQL to create tables
wrangler d1 execute prepgenie-db --file=backend/schema.sql
```

### 6. Local Development

```bash
# Start the Cloudflare Worker locally
wrangler dev

# The API will be available at http://localhost:8787
```

Test endpoints:
- Health check: `http://localhost:8787/health`
- API docs: Test with curl or Postman

### 7. Deploy to Cloudflare

```bash
# Deploy the Worker
wrangler deploy

# The API will be available at https://prepgenie-api.<your-subdomain>.workers.dev
```

## Setting Secrets in Production

For production, set secrets via Wrangler:

```bash
# Set API keys as secrets (encrypted)
wrangler secret put GOOGLE_API_KEY
wrangler secret put GROQ_API_KEY
wrangler secret put OPENROUTER_API_KEY

# You'll be prompted to enter the values
```

## Frontend Deployment (Cloudflare Pages)

### Build the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# The built files will be in frontend/dist/
```

### Deploy to Cloudflare Pages

```bash
# Deploy the frontend
wrangler pages deploy frontend/dist --project-name=prepgenie

# Or use Cloudflare Dashboard:
# 1. Go to Workers & Pages > Create Application > Pages
# 2. Connect to Git or upload manually
# 3. Set build command: npm run build
# 4. Set build output directory: dist
```

### Update CORS Origins

After deploying the frontend, update the CORS origins in `wrangler.toml`:

```toml
[vars]
CORS_ORIGINS = "https://prepgenie.pages.dev,https://prepgenie-api.workers.dev"
```

Then redeploy:

```bash
wrangler deploy
```

## Project Structure

```
PrepGenie/
├── backend/
│   ├── index.py          # Cloudflare Workers entry point
│   ├── main.py           # FastAPI app (reference)
│   ├── ai_service.py     # AI service layer
│   ├── database.py       # D1 database operations
│   ├── schema.sql        # Database schema
│   ├── .dev.vars         # Local environment variables (gitignored)
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/              # React source code
│   ├── dist/             # Built files (after npm run build)
│   └── package.json
├── wrangler.toml         # Cloudflare Workers configuration
└── .dev.vars             # Root level env vars (optional)
```

## Testing Locally

### Test Health Endpoint

```bash
curl http://localhost:8787/health
```

### Test Resume Processing

```bash
curl -X POST http://localhost:8787/api/start-interview \
  -H "Content-Type: application/json" \
  -d '{
    "roles": ["Software Engineer"],
    "resume_text": "John Doe\nSoftware Developer\n5 years experience..."
  }'
```

### Test Chat with Resume

```bash
curl -X POST http://localhost:8787/api/chat-with-resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe\nSoftware Developer...",
    "query": "What are the key skills?"
  }'
```

## Troubleshooting

### Worker Fails to Deploy

**Error: No API key found**
```bash
# Ensure you're logged in
wrangler login

# Or set CLOUDFLARE_API_TOKEN
export CLOUDFLARE_API_TOKEN=your_token
```

### Database Errors

**Error: Database not found**
```bash
# Verify database exists
wrangler d1 list

# Check wrangler.toml has correct database_id
```

**Error: Table does not exist**
```bash
# Re-run schema initialization
wrangler d1 execute prepgenie-db --file=backend/schema.sql
```

### CORS Errors

If frontend can't connect to backend:

1. Check CORS_ORIGINS in `wrangler.toml` includes your frontend URL
2. Redeploy the worker after changes
3. Clear browser cache

### AI Provider Errors

**Error: All AI providers exhausted**
- Check that at least one API key is set correctly
- Verify API keys are valid and have quota remaining
- Check provider status in health endpoint response

## Monitoring

### View Logs

```bash
# Stream logs in real-time
wrangler tail

# Or view recent logs
wrangler tail --status error
```

### Check Worker Status

```bash
# View worker info
wrangler whoami

# List all workers
wrangler worker list
```

### D1 Database Queries

```bash
# Query the database
wrangler d1 execute prepgenie-db --command="SELECT * FROM interview_sessions LIMIT 10"

# View database stats
wrangler d1 info prepgenie-db
```

## Cost Estimation

### Free Tier Limits

- **Workers**: 100,000 requests/day
- **D1**: 5GB storage, 100,000 read rows/day, 10,000 write rows/day
- **Pages**: 100GB bandwidth/month

### Paid Tier (Workers Paid)

- $5/month base + usage
- Much higher limits
- Better for production

## CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloudflare

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install Wrangler
        run: npm install -g wrangler
      
      - name: Build Frontend
        run: |
          cd frontend
          npm install
          npm run build
      
      - name: Deploy Worker
        run: wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
      
      - name: Deploy Pages
        run: wrangler pages deploy frontend/dist --project-name=prepgenie
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

## Migration from Other Platforms

### From Render/Railway

1. Update API endpoints in frontend to point to Cloudflare Worker URL
2. Set up D1 database and migrate data if needed
3. Update environment variables in Cloudflare dashboard
4. Test thoroughly before switching DNS

### From Hugging Face Spaces (Gradio)

The existing `app.py` Gradio app can continue running on Hugging Face Spaces while the new React+FastAPI stack runs on Cloudflare.

## Next Steps

1. **Set up custom domain** (optional)
   - Go to Workers & Pages > Your Worker > Triggers
   - Add custom domain

2. **Enable Analytics**
   - Go to Workers & Pages > Your Worker > Analytics
   - Enable Workers Analytics

3. **Set up Alerts**
   - Configure error rate alerts in Cloudflare dashboard

4. **Optimize Performance**
   - Enable Cloudflare caching for static assets
   - Consider using Workers KV for session caching

## Support

For issues:
- Check [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- Check [D1 Documentation](https://developers.cloudflare.com/d1/)
- Review worker logs: `wrangler tail --status error`

---

**Created by Samarth Agarwal**
**Version**: 3.2.0 (Cloudflare)
