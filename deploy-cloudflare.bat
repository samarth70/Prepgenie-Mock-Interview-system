@echo off
REM Cloudflare Deployment Script for PrepGenie
REM Run this script to deploy the backend to Cloudflare Workers

echo ============================================
echo   PrepGenie - Cloudflare Deployment
echo   Created by Samarth Agarwal
echo ============================================
echo.

REM Check if wrangler is installed
where wrangler >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Wrangler CLI not found!
    echo.
    echo Install it with: npm install -g wrangler
    echo.
    pause
    exit /b 1
)

echo [1/5] Checking Cloudflare authentication...
wrangler whoami >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Not authenticated with Cloudflare!
    echo.
    echo Please run: wrangler login
    echo.
    pause
    exit /b 1
)
echo [OK] Authenticated with Cloudflare
echo.

echo [2/5] Checking D1 database...
wrangler d1 list | findstr prepgenie-db >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] D1 database not found. Creating...
    wrangler d1 create prepgenie-db
    echo.
    echo [ACTION REQUIRED] Update wrangler.toml with the database_id from above
    echo Then run this script again.
    echo.
    pause
    exit /b 0
)
echo [OK] D1 database found
echo.

echo [3/5] Initializing database schema...
wrangler d1 execute prepgenie-db --file=backend\schema.sql --remote
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Schema initialization failed. Continuing anyway...
) else (
    echo [OK] Database schema initialized
)
echo.

echo [4/5] Deploying to Cloudflare Workers...
wrangler deploy
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Deployment failed!
    echo.
    pause
    exit /b 1
)
echo.

echo [5/5] Deployment complete!
echo.
echo ============================================
echo   Your API is now live at:
echo   https://prepgenie-api.<your-subdomain>.workers.dev
echo ============================================
echo.
echo Next steps:
echo 1. Set up secrets: wrangler secret put GOOGLE_API_KEY
echo 2. Deploy frontend: cd frontend ^&^& npm run build ^&^& wrangler pages deploy dist
echo.
pause
