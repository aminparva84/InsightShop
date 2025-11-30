# Launch InsightShop Backend and Frontend

Write-Host "Starting InsightShop..." -ForegroundColor Green

# Get the script directory (project root)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found! Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Found Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js not found! Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check if frontend dependencies are installed
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install frontend dependencies!" -ForegroundColor Red
        exit 1
    }
    Set-Location ..
}

# Check if Python dependencies are installed
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
python -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Python dependencies!" -ForegroundColor Red
        exit 1
    }
}

# Start Backend in a new window
Write-Host "`nStarting Flask backend on http://localhost:5000..." -ForegroundColor Cyan
$backendCommand = "cd '$scriptPath'; python app.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand -WindowStyle Normal

# Wait a bit for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if backend is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "Backend is running!" -ForegroundColor Green
    }
} catch {
    Write-Host "Backend may still be starting... (this is normal)" -ForegroundColor Yellow
}

# Start Frontend in a new window
Write-Host "`nStarting React frontend on http://localhost:3000..." -ForegroundColor Cyan
$frontendCommand = "cd '$scriptPath\frontend'; npm start"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand -WindowStyle Normal

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "InsightShop is starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend:  http://localhost:5000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "`nTwo PowerShell windows have been opened:" -ForegroundColor Cyan
Write-Host "  - One for the Flask backend" -ForegroundColor Gray
Write-Host "  - One for the React frontend" -ForegroundColor Gray
Write-Host "`nClose those windows to stop the servers." -ForegroundColor Gray
Write-Host "`nPress any key to exit this script (servers will continue running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

