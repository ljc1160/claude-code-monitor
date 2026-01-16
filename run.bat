@echo off
chcp 65001 >nul
title Claude Code Monitor
color 0A

echo ============================================
echo   Claude Code Monitor
echo ============================================
echo.

REM Switch to script directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found! Please install Python first.
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Check if installation is needed
set NEED_INSTALL=0

REM Check if dependencies are installed
pip show fastapi >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

REM Check if hooks are configured
set CLAUDE_SETTINGS=%USERPROFILE%\.claude\settings.json
if not exist "%CLAUDE_SETTINGS%" set NEED_INSTALL=1

if %NEED_INSTALL%==1 (
    echo [Step 1/3] First time setup detected, installing...
    echo.

    echo Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.

    echo Configuring Claude Code hooks...
    python install.py
    if errorlevel 1 (
        echo [ERROR] Failed to configure hooks!
        pause
        exit /b 1
    )
    echo.

    echo [OK] Installation completed!
    echo.
    echo ============================================
    echo   Optional: Generate Audio Files
    echo ============================================
    echo You can generate audio files by running:
    echo   python cosy_voice_tts_save.py
    echo.
    echo Press any key to start the monitor server...
    pause >nul
    echo.
)

echo [Step 2/3] Starting monitor server...
echo.

REM Check if monitor directory exists
if not exist "%~dp0monitor" (
    echo [ERROR] monitor directory not found!
    echo Expected path: %~dp0monitor
    pause
    exit /b 1
)

REM Check if server.py exists
if not exist "%~dp0monitor\server.py" (
    echo [ERROR] server.py not found!
    echo Expected path: %~dp0monitor\server.py
    pause
    exit /b 1
)

cd /d "%~dp0monitor"
echo Starting server from: %CD%
start "Monitor Server" python server.py

REM Wait for server to start
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

echo [Step 3/3] Opening browser...
start http://localhost:8765

echo.
echo ============================================
echo   Monitor is running!
echo ============================================
echo   URL: http://localhost:8765
echo   Config: http://localhost:8765/config
echo.
echo Press any key to stop the monitor...
echo ============================================
pause >nul

REM Stop server
echo Stopping server...
taskkill /FI "WINDOWTITLE eq Monitor Server*" /F >nul 2>&1
echo.
echo Monitor stopped.
pause
