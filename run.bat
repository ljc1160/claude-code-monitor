@echo off
chcp 936 >nul
title Claude Code Monitor
color 0A

echo ============================================
echo   Claude Code Monitor
echo ============================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查是否需要安装
set NEED_INSTALL=0

REM 检查依赖是否已安装
pip show fastapi >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

REM 检查 hooks 是否已配置
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
cd /d "%~dp0monitor"
start "Monitor Server" python server.py

REM 等待服务器启动
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

REM 关闭服务器
taskkill /FI "WINDOWTITLE eq Monitor Server*" /F >nul 2>&1
echo.
echo Monitor stopped.
pause
