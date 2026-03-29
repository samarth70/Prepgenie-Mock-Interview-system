#!/bin/bash
# Cloudflare Deployment Script for PrepGenie
# Run this script to deploy the backend to Cloudflare Workers

echo "============================================"
echo "  PrepGenie - Cloudflare Deployment"
echo "  Created by Samarth Agarwal"
echo "============================================"
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "[ERROR] Wrangler CLI not found!"
    echo ""
    echo "Install it with: npm install -g wrangler"
    echo ""
    exit 1
fi

echo "[1/5] Checking Cloudflare authentication..."
if ! wrangler whoami &> /dev/null; then
    echo "[ERROR] Not authenticated with Cloudflare!"
    echo ""
    echo "Please run: wrangler login"
    echo ""
    exit 1
fi
echo "[OK] Authenticated with Cloudflare"
echo ""

echo "[2/5] Checking D1 database..."
if ! wrangler d1 list | grep -q prepgenie-db; then
    echo "[INFO] D1 database not found. Creating..."
    wrangler d1 create prepgenie-db
    echo ""
    echo "[ACTION REQUIRED] Update wrangler.toml with the database_id from above"
    echo "Then run this script again."
    echo ""
    exit 0
fi
echo "[OK] D1 database found"
echo ""

echo "[3/5] Initializing database schema..."
if ! wrangler d1 execute prepgenie-db --file=backend/schema.sql --remote; then
    echo "[WARNING] Schema initialization failed. Continuing anyway..."
else
    echo "[OK] Database schema initialized"
fi
echo ""

echo "[4/5] Deploying to Cloudflare Workers..."
if ! wrangler deploy; then
    echo ""
    echo "[ERROR] Deployment failed!"
    echo ""
    exit 1
fi
echo ""

echo "[5/5] Deployment complete!"
echo ""
echo "============================================"
echo "  Your API is now live at:"
echo "  https://prepgenie-api.<your-subdomain>.workers.dev"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Set up secrets: wrangler secret put GOOGLE_API_KEY"
echo "2. Deploy frontend: cd frontend && npm run build && wrangler pages deploy dist"
echo ""
