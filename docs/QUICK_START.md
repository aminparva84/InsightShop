# Quick Start Guide - InsightShop

## Launch Both Backend and Frontend

### Option 1: Use Launch Script (Recommended)

**Windows PowerShell:**
```powershell
.\launch.ps1
```

**Windows Command Prompt:**
```cmd
launch.bat
```

**Linux/Mac:**
```bash
./start.sh
```

### Option 2: Manual Launch

#### Terminal 1 - Backend (Flask)
```bash
# From project root
python app.py
```
Backend will run on: http://localhost:5000

#### Terminal 2 - Frontend (React)
```bash
# From project root
cd frontend
npm start
```
Frontend will run on: http://localhost:3000

## Verify Services Are Running

1. **Backend Health Check:**
   - Open: http://localhost:5000/api/health
   - Should return: `{"status": "healthy", "service": "InsightShop API"}`

2. **Frontend:**
   - Open: http://localhost:3000
   - Should see the InsightShop homepage

## Troubleshooting

### Backend not starting?
- Check if port 5000 is already in use
- Verify Python dependencies: `pip install -r requirements.txt`
- Check for errors in the backend console

### Frontend not starting?
- Check if port 3000 is already in use
- Verify Node dependencies: `cd frontend && npm install`
- Check for errors in the frontend console

### Port already in use?
- Backend: Change port in `app.py` (line 67)
- Frontend: Set `PORT=3001` environment variable before `npm start`

## Development URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **API Health:** http://localhost:5000/api/health

## Notes

- The frontend is configured to proxy API requests to the backend (see `frontend/package.json` proxy setting)
- Both services must be running for the application to work properly
- The launch scripts open separate windows for each service

