@echo off
REM Run InsightShop in Docker with env file (AWS keys, JWT, etc.).
REM 1. Copy env.docker.example to .env and set your values.
REM 2. Run this script (or: docker-compose up --build)

cd /d "%~dp0"

if not exist ".env" (
    echo .env not found. Copy env.docker.example to .env and set:
    echo   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, JWT_SECRET, SECRET_KEY
    echo.
    echo   copy env.docker.example .env
    pause
    exit /b 1
)

echo Building image...
docker build -t insightshop:latest .
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo Starting container with --env-file .env ...
docker run --rm -p 5000:5000 --env-file .env insightshop:latest
