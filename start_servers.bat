@echo off
title PrepGenie - AI Mock Interview Platform
color 0A

echo.
echo ============================================
echo    PrepGenie - AI Mock Interview Platform
echo ============================================
echo.
echo Starting servers...
echo.

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo ERROR: Please run this script from the PrepGenie root directory!
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Activate Conda environment
echo Activating Conda environment: agenticAi
call conda activate agenticAi

echo.
echo ============================================
echo Starting Backend Server (Port 8000)
echo ============================================
echo.

REM Start backend in a new window
start "PrepGenie Backend" cmd /k "cd backend && conda activate agenticAi && echo Backend starting on http://localhost:8000 && echo API Docs: http://localhost:8000/docs && echo. && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
echo Waiting for backend to initialize (5 seconds)...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo Starting Frontend Server (Port 3000)
echo ============================================
echo.

REM Start frontend in a new window
start "PrepGenie Frontend" cmd /k "cd frontend && echo Frontend starting on http://localhost:3000 && echo. && npm run dev"

echo.
echo ============================================
echo Servers Starting...
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
echo Press any key to exit this window...
pause >nul
