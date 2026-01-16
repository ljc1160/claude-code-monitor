#!/usr/bin/env python3
"""
Claude Code 监控平台 - 后端服务
基于 FastAPI + WebSocket 实现实时监控
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Set
from pathlib import Path
import time
import hmac
import hashlib
import base64
import urllib.parse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

# 配置
BASE_DIR = Path(__file__).parent
HOOKS_LOG_FILE = BASE_DIR.parent / "hooks_log.txt"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
CONFIG_FILE = BASE_DIR / "config.json"

app = FastAPI(title="Claude Code Monitor", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.event_history: List[Dict] = []
        self.max_history = 1000
        self.todos: List[Dict] = []
        self.sessions: Dict[str, Dict] = {}  # 会话信息存储
        self.stats = {
            "total_events": 0,
            "session_start_time": None,
            "events_by_type": {},
            "tools_used": {},
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # 发送历史数据和当前状态
        await websocket.send_json({
            "type": "init",
            "data": {
                "history": self.event_history[-100:],
                "stats": self.stats,
                "todos": self.todos,
                "sessions": self.sessions  # 发送会话信息
            }
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict):
        """广播消息到所有连接"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)

        for conn in disconnected:
            self.active_connections.discard(conn)

    def add_event(self, event: Dict):
        """添加事件到历史"""
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]

        # 更新统计
        self.stats["total_events"] += 1
        event_type = event.get("event_type", "unknown")
        self.stats["events_by_type"][event_type] = self.stats["events_by_type"].get(event_type, 0) + 1

        # 统计工具使用
        if event_type in ["PreToolUse", "PostToolUse"]:
            # 调试：打印事件结构
            print(f"[DEBUG] Event structure: {json.dumps(event, ensure_ascii=False, indent=2)}")

            # tool_name 应该在 data 字段中
            tool_name = event.get("data", {}).get("tool_name") or "unknown"
            print(f"[DEBUG] Extracted tool_name: {tool_name}")

            self.stats["tools_used"][tool_name] = self.stats["tools_used"].get(tool_name, 0) + 1

        # 更新会话信息
        session_info = event.get("session", {})
        session_id = session_info.get("session_id")
        if session_id:
            self.sessions[session_id] = {
                "session_id": session_id,
                "project_name": session_info.get("project_name", "未知项目"),
                "project_path": session_info.get("project_path", ""),
                "hostname": session_info.get("hostname", ""),
                "pid": session_info.get("pid", ""),
                "last_event": datetime.now().isoformat(),
                "event_count": self.sessions.get(session_id, {}).get("event_count", 0) + 1
            }

    def update_todos(self, todos: List[Dict]):
        """更新任务列表"""
        self.todos = todos


manager = ConnectionManager()


# 默认配置
DEFAULT_CONFIG = {
    "sound_enabled": {
        "PreToolUse": False,
        "PostToolUse": False,
        "PermissionRequest": True,
        "UserPromptSubmit": True,
        "Notification": True,
        "Stop": True,
        "SubagentStop": True,
        "PreCompact": True,
        "SessionStart": True,
        "SessionEnd": True,
    },
    "dingtalk": {
        "enabled": False,
        "webhook_url": "",
        "secret": "",
        "events": []
    }
}


def load_config() -> Dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 合并默认配置，确保新增字段存在
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                return config
        except Exception as e:
            print(f"加载配置失败: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict) -> bool:
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


async def send_dingtalk_notification(event: Dict, config: Dict):
    """发送钉钉通知"""
    dingtalk_config = config.get("dingtalk", {})

    # 检查是否启用
    if not dingtalk_config.get("enabled", False):
        return

    # 检查是否需要推送此事件
    event_type = event.get("event_type", "")
    allowed_events = dingtalk_config.get("events", [])
    if event_type not in allowed_events:
        return

    webhook_url = dingtalk_config.get("webhook_url", "")
    secret = dingtalk_config.get("secret", "")

    if not webhook_url:
        return

    try:
        # 如果配置了 secret，生成签名
        if secret:
            timestamp = str(round(time.time() * 1000))
            sign_string = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(
                secret.encode("utf-8"),
                sign_string.encode("utf-8"),
                digestmod=hashlib.sha256
            ).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

        # 构建消息内容
        session_info = event.get("session", {})
        event_name = event.get("event_name", event_type)
        project_name = session_info.get("project_name", "未知项目")

        # 格式化消息
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"Claude Code 事件通知",
                "text": f"### 🤖 Claude Code 事件通知\n\n"
                        f"**事件类型**: {event_name}\n\n"
                        f"**项目**: {project_name}\n\n"
                        f"**时间**: {event.get('timestamp', '')}\n\n"
            }
        }

        # 发送请求
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(webhook_url, json=message)
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") != 0:
                    print(f"钉钉推送失败: {result.get('errmsg')}")
            else:
                print(f"钉钉推送失败: HTTP {response.status_code}")

    except Exception as e:
        print(f"钉钉推送异常: {e}")


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """返回监控看板页面"""
    html_file = TEMPLATES_DIR / "dashboard.html"
    return FileResponse(str(html_file))


@app.get("/test_audio", response_class=HTMLResponse)
async def get_audio_test():
    """返回音频测试页面"""
    html_file = TEMPLATES_DIR / "audio_test.html"
    return FileResponse(str(html_file))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息（如果需要）
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/event")
async def receive_event(event: Dict):
    """接收来自 hooks 的事件"""
    event["timestamp"] = datetime.now().isoformat()
    event["id"] = f"{event['timestamp']}_{manager.stats['total_events']}"

    manager.add_event(event)

    # 广播到所有客户端
    await manager.broadcast({
        "type": "event",
        "data": event
    })

    # 如果有会话信息更新，也广播会话更新
    session_info = event.get("session", {})
    if session_info.get("session_id"):
        await manager.broadcast({
            "type": "sessions",
            "data": manager.sessions
        })

    # 发送钉钉通知
    config = load_config()
    await send_dingtalk_notification(event, config)

    return {"status": "ok"}


@app.post("/api/todos")
async def update_todos(todos: List[Dict]):
    """更新任务列表"""
    manager.update_todos(todos)

    await manager.broadcast({
        "type": "todos",
        "data": todos
    })

    return {"status": "ok"}


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    return manager.stats


@app.get("/api/history")
async def get_history(limit: int = 100):
    """获取历史事件"""
    return manager.event_history[-limit:]


@app.get("/api/config")
async def get_config():
    """获取配置"""
    return load_config()


@app.post("/api/config")
async def update_config(config: Dict):
    """更新配置"""
    if save_config(config):
        # 广播配置更新
        await manager.broadcast({
            "type": "config_updated",
            "data": config
        })
        return {"status": "ok", "message": "配置已保存"}
    else:
        return {"status": "error", "message": "配置保存失败"}


@app.post("/api/test-dingtalk")
async def test_dingtalk():
    """测试钉钉推送"""
    config = load_config()

    # 构造测试事件
    test_event = {
        "event_type": "Stop",
        "event_name": "Stop - 测试通知",
        "timestamp": datetime.now().isoformat(),
        "session": {
            "project_name": "Claude Code Monitor",
            "hostname": "测试主机",
            "username": "测试用户"
        },
        "data": {
            "message": "这是一条测试消息，用于验证钉钉推送功能"
        }
    }

    try:
        await send_dingtalk_notification(test_event, config)
        return {"status": "ok", "message": "测试消息已发送，请检查钉钉群"}
    except Exception as e:
        return {"status": "error", "message": f"发送失败: {str(e)}"}


async def watch_log_file():
    """监控日志文件变化"""
    last_size = 0
    last_content = ""

    while True:
        try:
            if HOOKS_LOG_FILE.exists():
                current_size = HOOKS_LOG_FILE.stat().st_size
                if current_size != last_size:
                    with open(HOOKS_LOG_FILE, "r", encoding="utf-8") as f:
                        content = f.read()

                    # 解析新增内容
                    if content != last_content:
                        new_content = content[len(last_content):]
                        if new_content.strip():
                            # 解析日志条目
                            entries = parse_log_entries(new_content)
                            for entry in entries:
                                manager.add_event(entry)
                                await manager.broadcast({
                                    "type": "event",
                                    "data": entry
                                })

                        last_content = content
                    last_size = current_size
        except Exception as e:
            print(f"Error watching log file: {e}")

        await asyncio.sleep(0.5)


def parse_log_entries(content: str) -> List[Dict]:
    """解析日志条目"""
    entries = []
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # 检测新条目开始
        if line.startswith("[") and "]" in line:
            try:
                timestamp_end = line.index("]")
                timestamp = line[1:timestamp_end]
                event_type = line[timestamp_end + 2:].strip()

                entry = {
                    "timestamp": timestamp,
                    "event_type": event_type.split(" - ")[0] if " - " in event_type else event_type,
                    "event_name": event_type,
                    "data": {},
                    "id": f"{timestamp}_{len(entries)}"
                }

                print(f"[PARSE] Found entry: {event_type}")

                # 查找数据部分
                i += 1
                json_lines = []
                while i < len(lines) and not lines[i].startswith("-" * 10):
                    if "数据:" in lines[i]:
                        print(f"[PARSE] Found data section at line {i}")
                        # 从 "数据: {" 这一行开始提取 JSON
                        # 找到 { 的位置
                        brace_pos = lines[i].find("{")
                        if brace_pos >= 0:
                            json_lines.append(lines[i][brace_pos:].strip())

                        i += 1
                        # 继续收集后续行
                        while i < len(lines) and not lines[i].startswith("-" * 10):
                            stripped = lines[i].strip()
                            if stripped:
                                json_lines.append(stripped)
                                # 检查是否收集完整
                                temp_json = "".join(json_lines)
                                open_braces = temp_json.count("{")
                                close_braces = temp_json.count("}")
                                if open_braces > 0 and open_braces == close_braces:
                                    break
                            i += 1
                        break
                    i += 1

                json_text = "".join(json_lines) if json_lines else ""
                if json_text:
                    print(f"[PARSE] Collected JSON: {json_text[:100]}...")

                # 解析 JSON
                if json_text:
                    try:
                        entry["data"] = json.loads(json_text)
                        print(f"[PARSE] Successfully parsed JSON, tool_name: {entry['data'].get('tool_name', 'N/A')}")
                    except Exception as e:
                        print(f"[PARSE] JSON parse error: {e}")
                        pass

                entries.append(entry)
            except Exception as e:
                print(f"[PARSE] Entry parse error: {e}")
                pass

        i += 1

    return entries


@app.on_event("startup")
async def startup_event():
    """启动时开始监控日志文件"""
    asyncio.create_task(watch_log_file())


if __name__ == "__main__":
    print("=" * 60)
    print("  Claude Code 监控平台")
    print("  访问地址: http://localhost:8765")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8765)
