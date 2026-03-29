#!/bin/bash
# PrepGenie - Deploy to Render
# This script helps you deploy to Render.com

echo "============================================"
echo "  PrepGenie - Render Deployment Helper"
echo "  Created by Samarth Agarwal"
echo "============================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git is not installed!"
    echo "Please install Git from https://git-scm.com/"
    exit 1
fi

echo "[1/4] Checking Git status..."
git status
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "[ERROR] Not a Git repository!"
    echo ""
    echo "Initializing Git repository..."
    git init
    echo ""
fi

echo "[2/4] Adding files to Git..."
git add .
git commit -m "Deploy to Render - $(date)"
echo ""

echo "[3/4] Current Git remote:"
git remote -v
echo ""

read -p "Do you have a GitHub remote configured? (y/n): " HAS_REMOTE
if [ "$HAS_REMOTE" = "y" ] || [ "$HAS_REMOTE" = "Y" ]; then
    echo ""
    echo "[4/4] Pushing to GitHub..."
    git push -u origin main
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] Push failed!"
        echo "Make sure your remote is configured correctly."
        echo ""
        exit 1
    fi
else
    echo ""
    echo "Please create a GitHub repository and add it as remote:"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/prepgenie.git"
    echo "  git push -u origin main"
    echo ""
fi

echo ""
echo "============================================"
echo "  Next Steps:"
echo "============================================"
echo ""
echo "1. Go to https://render.com and sign in"
echo "2. Click 'New +' then 'Blueprint'"
echo "3. Connect your GitHub repository"
echo "4. Apply the configuration"
echo "5. Add your API keys in Environment tab"
echo ""
echo "For detailed instructions, see:"
echo "  RENDER_DEPLOYMENT_GUIDE.md"
echo ""
echo "============================================"
echo ""
