@echo off
echo ========================================
echo InsightShop Local Development Setup
echo ========================================
echo.

REM Get the script directory
cd /d "%~dp0"

REM Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.11+
    pause
    exit /b 1
)
python --version
echo.

REM Check Node.js
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)
node --version
echo.

REM Check if .env exists
echo [3/5] Checking environment configuration...
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Creating .env file from template...
    REM The .env file should have been created, but if not, we'll note it
    echo Please ensure .env file exists with proper configuration.
) else (
    echo .env file found.
)
echo.

REM Install Python dependencies
echo [4/5] Installing Python dependencies...
echo This may take a few minutes...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo WARNING: Some dependencies may have failed to install.
    echo You may need to install them manually or check your internet connection.
) else (
    echo Python dependencies installed successfully!
)
echo.

REM Install Frontend dependencies
echo [5/5] Installing Frontend dependencies...
if not exist "frontend\node_modules" (
    cd frontend
    call npm install
    cd ..
    echo Frontend dependencies installed!
) else (
    echo Frontend dependencies already installed.
)
echo.

REM Initialize database
echo.
echo ========================================
echo Initializing Database...
echo ========================================
python -c "from app import app; from models.database import init_db; init_db(app)"
if errorlevel 1 (
    echo.
    echo WARNING: Database initialization may have failed.
    echo You can try running: python -c "from app import app; from models.database import init_db; init_db(app)"
) else (
    echo Database initialized successfully!
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Review the .env file and update any required values
echo 2. If you have AWS credentials, add them to .env for AI features
echo 3. Run 'launch.bat' to start the application
echo.
echo The application will run on:
echo   - Backend: http://localhost:5000
echo   - Frontend: http://localhost:3000
echo.
pause

