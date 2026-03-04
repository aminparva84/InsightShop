@echo off
title InsightShop Dev
cd /d "%~dp0"
echo Starting proxy (5000) and React (3000). API should already be on 5001.
echo.
call npm run dev:web
pause
