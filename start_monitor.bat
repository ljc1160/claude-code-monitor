@echo off
chcp 936 >nul
title Claude Code Monitor

echo ============================================
echo   Claude Code Monitor
echo   URL: http://localhost:8765
echo ============================================
echo.

cd /d "%~dp0monitor"

echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing FastAPI...
    pip install fastapi uvicorn
)

echo.
echo Starting monitor server...
echo Press Ctrl+C to stop
echo.

python server.py

pause
