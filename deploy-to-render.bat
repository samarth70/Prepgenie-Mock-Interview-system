@echo off
REM PrepGenie - Deploy to Render
REM This script helps you deploy to Render.com

echo ============================================
echo   PrepGenie - Render Deployment Helper
echo   Created by Samarth Agarwal
echo ============================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed!
    echo Please install Git from https://git-scm.com/
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking Git status...
git status
echo.

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Not a Git repository!
    echo.
    echo Initializing Git repository...
    git init
    echo.
)

echo [2/4] Adding files to Git...
git add .
git commit -m "Deploy to Render - %DATE%"
echo.

echo [3/4] Current Git remote:
git remote -v
echo.

set /p HAS_REMOTE="Do you have a GitHub remote configured? (y/n): "
if /i "%HAS_REMOTE%"=="y" (
    echo.
    echo [4/4] Pushing to GitHub...
    git push -u origin main
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Push failed!
        echo Make sure your remote is configured correctly.
        echo.
        pause
        exit /b 1
    )
) else (
    echo.
    echo Please create a GitHub repository and add it as remote:
    echo   git remote add origin https://github.com/YOUR_USERNAME/prepgenie.git
    echo   git push -u origin main
    echo.
)

echo.
echo ============================================
echo   Next Steps:
echo ============================================
echo.
echo 1. Go to https://render.com and sign in
echo 2. Click "New +" then "Blueprint"
echo 3. Connect your GitHub repository
echo 4. Apply the configuration
echo 5. Add your API keys in Environment tab
echo.
echo For detailed instructions, see:
echo   RENDER_DEPLOYMENT_GUIDE.md
echo.
echo ============================================
echo.
pause
