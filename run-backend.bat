@echo off
REM Start Flask on port 5001 (avoids Windows port 5000 reservation).
REM Open http://localhost:5000 and run "npm run dev" for proxy+API+frontend,
REM or run frontend with: cd frontend && npm start (then set proxy to 5001 or use API at 5001).
set PORT=5001
python app.py
