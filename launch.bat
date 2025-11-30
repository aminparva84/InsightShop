@echo off
echo Starting InsightShop...
echo.

REM Get the script directory
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.11+
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

REM Check frontend dependencies
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies!
        pause
        exit /b 1
    )
    cd ..
)

REM Start Backend
echo.
echo Starting Flask backend on http://localhost:5000...
start "InsightShop Backend" cmd /k "python app.py"

REM Wait for backend
timeout /t 5 /nobreak >nul

REM Start Frontend
echo Starting React frontend on http://localhost:3000...
cd frontend
start "InsightShop Frontend" cmd /k "npm start"
cd ..

echo.
echo ========================================
echo InsightShop is starting!
echo ========================================
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Two command windows have been opened:
echo   - One for the Flask backend
echo   - One for the React frontend
echo.
echo Close those windows to stop the servers.
echo.
pause

