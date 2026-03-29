@echo off
title PrepGenie Backend Server
color 0B

echo.
echo ============================================
echo    PrepGenie Backend Server
echo ============================================
echo.

REM Check if we're in the backend directory
if not exist "main.py" (
    echo ERROR: Please run this script from the backend directory!
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Activate Conda environment
echo Activating Conda environment: agenticAi
call conda activate agenticAi

echo.
echo Starting FastAPI backend...
echo.
echo Server will be available at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo   - Health: http://localhost:8000/health
echo.
echo Press CTRL+C to stop the server
echo.
echo ============================================
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
