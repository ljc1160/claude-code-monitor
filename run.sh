#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "============================================"
echo "   Claude Code Monitor"
echo "============================================"
echo ""

# 检查 Python 是否安装
echo "Checking Python installation..."
PYTHON_CMD=""

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}[OK] Found python3${NC}"
    python3 --version
elif command -v python &> /dev/null; then
    # 检查 python 版本是否为 Python 3
    PYTHON_VERSION=$(python --version 2>&1 | grep -oP 'Python \K[0-9]+')
    if [ "$PYTHON_VERSION" -ge 3 ]; then
        PYTHON_CMD="python"
        echo -e "${GREEN}[OK] Found python (Python 3)${NC}"
        python --version
    else
        echo -e "${RED}[ERROR] Python 3 not found! Found Python 2 instead.${NC}"
        echo -e "${RED}Please install Python 3 first.${NC}"
        exit 1
    fi
else
    echo -e "${RED}[ERROR] Python not found! Please install Python 3 first.${NC}"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查是否需要安装
NEED_INSTALL=0

# 检查依赖是否已安装
if ! $PYTHON_CMD -m pip show fastapi &> /dev/null; then
    NEED_INSTALL=1
fi

# 检查 hooks 是否已配置
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
if [ ! -f "$CLAUDE_SETTINGS" ]; then
    NEED_INSTALL=1
fi

if [ $NEED_INSTALL -eq 1 ]; then
    echo -e "${BLUE}[Step 1/3] First time setup detected, installing...${NC}"
    echo ""

    echo "Installing Python dependencies..."
    $PYTHON_CMD -m pip install -r monitor/requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install dependencies!${NC}"
        exit 1
    fi
    echo ""

    echo "Configuring Claude Code hooks..."
    $PYTHON_CMD install.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to configure hooks!${NC}"
        exit 1
    fi
    echo ""

    echo -e "${GREEN}[OK] Installation completed!${NC}"
    echo ""
    echo "============================================"
    echo "   Optional: Generate Audio Files"
    echo "============================================"
    echo "You can generate audio files by running:"
    echo "  $PYTHON_CMD cosy_voice_tts_save.py"
    echo ""
    read -p "Press Enter to start the monitor server..."
    echo ""
fi

echo -e "${BLUE}[Step 2/3] Starting monitor server...${NC}"
echo ""

# 启动服务器
cd "$SCRIPT_DIR/monitor"
$PYTHON_CMD server.py &
SERVER_PID=$!

# 等待服务器启动
sleep 3

echo -e "${BLUE}[Step 3/3] Opening browser...${NC}"

# 根据系统打开浏览器
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:18765
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:18765
    fi
fi

echo ""
echo "============================================"
echo "   Monitor is running!"
echo "============================================"
echo "   URL: http://localhost:18765"
echo "   Config: http://localhost:18765/config"
echo ""
echo "   Server PID: $SERVER_PID"
echo ""
echo "Press Ctrl+C to stop the monitor..."
echo "============================================"

# 等待 Ctrl+C
trap "echo ''; echo 'Stopping monitor...'; kill $SERVER_PID 2>/dev/null; echo 'Monitor stopped.'; exit 0" INT

# 保持脚本运行
wait $SERVER_PID
