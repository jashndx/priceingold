@echo off
title SwarnaStock - Indian Stocks in Terms of Gold
echo ========================================================
echo Starting SwarnaStock Server...
echo Pricing Indian Stocks in 24K Gold
echo ========================================================

start "" http://localhost:8000
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
pause
