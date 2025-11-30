# Launch InsightShop Backend and Frontend

Write-Host "Starting InsightShop..." -ForegroundColor Green

# Start Backend in background
Write-Host "Starting Flask backend on http://localhost:5000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\code\InsightShop; python app.py" -WindowStyle Normal

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting React frontend on http://localhost:3000..." -ForegroundColor Cyan
cd frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\code\InsightShop\frontend; npm start" -WindowStyle Normal

Write-Host "`nBackend: http://localhost:5000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "`nPress Ctrl+C to stop servers" -ForegroundColor Gray

