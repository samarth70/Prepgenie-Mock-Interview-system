@echo off
title PrepGenie Frontend
color 09

echo.
echo ============================================
echo    PrepGenie Frontend Server
echo ============================================
echo.

REM Check if we're in the frontend directory
if not exist "package.json" (
    echo ERROR: Please run this script from the frontend directory!
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Starting Vite development server...
echo.
echo Frontend will be available at:
echo   - App: http://localhost:3000
echo.
echo Press CTRL+C to stop the server
echo.
echo ============================================
echo.

npm run dev
