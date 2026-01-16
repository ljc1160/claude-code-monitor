#!/usr/bin/env python3
"""
Claude Code Hooks 处理脚本
用于演示和记录所有 hook 事件的触发情况
支持发送事件到监控平台
"""

import sys
import json
import os
from datetime import datetime
import threading

# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 日志文件路径
LOG_FILE = os.path.join(SCRIPT_DIR, "hooks_log.txt")

# 监控平台配置
MONITOR_URL = "http://localhost:18765/api/event"
CONFIG_URL = "http://localhost:18765/api/config"
MONITOR_ENABLED = True

# ============ 音频播放开关配置 ============
# 默认值 - 如果无法从监控平台读取，则使用这些默认值
DEFAULT_SOUND_ENABLED = {
    "PreToolUse": False,        # 工具调用前
    "PostToolUse": False,       # 工具调用后
    "PermissionRequest": False,  # 权限请求
    "UserPromptSubmit": False,  # 用户提交提示
    "Notification": False,       # 通知（建议保持开启）
    "Stop": False,               # 响应完成
    "SubagentStop": False,       # 子代理完成
    "PreCompact": False,        # 压缩前
    "SessionStart": False,       # 会话开始
    "SessionEnd": False,        # 会话结束
}

# 动态加载的配置（从监控平台读取）
SOUND_ENABLED = None
# =========================================

def send_to_monitor(event_type: str, data: dict = None):
    """异步发送事件到监控平台"""
    if not MONITOR_ENABLED:
        return

    def _send():
        try:
            import urllib.request
            import urllib.error
            import socket
            import getpass

            # 获取会话信息 - 优先使用 data 中的 session_id
            session_id = (data or {}).get('session_id') or os.environ.get('CLAUDE_SESSION_ID', '')
            if not session_id:
                session_id = f"pid_{os.getpid()}_{int(datetime.now().timestamp())}"

            # 获取项目名称（优先使用 data 中的 cwd，否则使用当前目录）
            cwd = (data or {}).get('cwd') or os.getcwd()
            project_name = os.path.basename(cwd)

            session_info = {
                "session_id": session_id,
                "project_path": cwd,
                "project_name": project_name,
                "hostname": socket.gethostname(),
                "username": getpass.getuser(),
                "pid": os.getpid()
            }

            event = {
                "event_type": event_type,
                "event_name": event_type,
                "data": data or {},
                "session": session_info,
                "timestamp": datetime.now().isoformat()
            }

            req = urllib.request.Request(
                MONITOR_URL,
                data=json.dumps(event).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=2) as response:
                response.read()
        except Exception as e:
            # 静默失败，不影响 hooks 正常运行
            pass

    # 在后台线程发送，避免阻塞
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


def load_config_from_monitor():
    """从监控平台加载配置"""
    global SOUND_ENABLED

    if SOUND_ENABLED is not None:
        # 已经加载过配置
        return SOUND_ENABLED

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            CONFIG_URL,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=1) as response:
            config = json.loads(response.read().decode('utf-8'))
            SOUND_ENABLED = config.get('sound_enabled', DEFAULT_SOUND_ENABLED)
            return SOUND_ENABLED
    except Exception as e:
        # 无法连接到监控平台，使用默认配置
        SOUND_ENABLED = DEFAULT_SOUND_ENABLED
        return DEFAULT_SOUND_ENABLED

def log_event(event_type: str, data: dict = None):
    """记录事件到日志文件并发送到监控平台"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {event_type}"
    if data:
        log_entry += f"\n  数据: {json.dumps(data, ensure_ascii=False, indent=4)}"
    log_entry += "\n" + "-" * 60 + "\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    # 同时输出到 stderr 以便调试
    print(f"[HOOK] {event_type}", file=sys.stderr)

    # 提取纯事件类型（去掉描述部分）
    # 例如: "SessionStart - 会话开始" -> "SessionStart"
    pure_event_type = event_type.split(" - ")[0] if " - " in event_type else event_type

    # 发送到监控平台
    send_to_monitor(pure_event_type, data)

def handle_pre_tool_use():
    """
    PreToolUse: 在工具调用之前运行
    - 可以阻止工具调用
    - 输入: stdin 接收 JSON，包含 tool_name, tool_input 等
    - 输出: 可返回 {"decision": "block", "reason": "..."} 来阻止
    """
    stdin_data = sys.stdin.read()

    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except Exception as e:
        data = {"raw": stdin_data}

    log_event("PreToolUse - 工具调用前", data)
    play_sound("PreToolUse")

    # 示例：不阻止任何工具
    # 如果要阻止，输出: {"decision": "block", "reason": "原因"}
    # print(json.dumps({"decision": "block", "reason": "测试阻止"}))

def handle_post_tool_use():
    """
    PostToolUse: 在工具调用完成后运行
    - 用于记录或处理工具调用结果
    - 输入: stdin 接收 JSON，包含 tool_name, tool_input, tool_output 等
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("PostToolUse - 工具调用后", data)
    play_sound("PostToolUse")

def handle_permission_request():
    """
    PermissionRequest: 在显示权限对话框时运行
    - 可以自动允许或拒绝权限请求
    - 输入: stdin 接收 JSON，包含权限请求详情
    - 输出: 可返回 {"decision": "allow"} 或 {"decision": "deny", "reason": "..."}
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("PermissionRequest - 权限请求", data)
    play_sound("PermissionRequest")

    # 示例：不自动处理，让用户决定
    # 如果要自动允许: print(json.dumps({"decision": "allow"}))
    # 如果要自动拒绝: print(json.dumps({"decision": "deny", "reason": "原因"}))

def handle_user_prompt_submit():
    """
    UserPromptSubmit: 当用户提交提示时运行，在 Claude 处理之前
    - 可以修改或阻止用户输入
    - 输入: stdin 接收 JSON，包含用户提示内容
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("UserPromptSubmit - 用户提交提示", data)
    play_sound("UserPromptSubmit")

def play_sound(event_type: str):
    """播放对应事件的音频"""
    # 从监控平台加载配置
    sound_config = load_config_from_monitor()

    if not sound_config.get(event_type, False):
        return

    # 事件类型到音频文件名的映射
    sound_files = {
        "PreToolUse": "pre_tool_use.wav",
        "PostToolUse": "post_tool_use.wav",
        "PermissionRequest": "permission_request.wav",
        "UserPromptSubmit": "user_prompt_submit.wav",
        "Notification": "notification.wav",
        "Stop": "stop.wav",
        "SubagentStop": "subagent_stop.wav",
        "PreCompact": "pre_compact.wav",
        "SessionStart": "session_start.wav",
        "SessionEnd": "session_end.wav",
    }

    # 优先使用监控平台的音频文件
    monitor_audio_dir = os.path.join(SCRIPT_DIR, "monitor", "static", "audio")
    audio_filename = sound_files.get(event_type, "notification.wav")
    audio_file = os.path.join(monitor_audio_dir, audio_filename)

    # 如果监控平台音频文件不存在，使用当前目录
    if not os.path.exists(audio_file):
        audio_file = os.path.join(SCRIPT_DIR, audio_filename)

    if sys.platform == "win32":
        import winsound
        if os.path.exists(audio_file):
            try:
                winsound.PlaySound(audio_file, winsound.SND_FILENAME)
            except Exception:
                pass
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    elif sys.platform == "darwin":
        if os.path.exists(audio_file):
            os.system(f'afplay "{audio_file}" &')
        else:
            os.system('afplay /System/Library/Sounds/Glass.aiff &')

def handle_notification():
    """
    Notification: 当 Claude Code 发送通知时运行
    - 用于自定义通知行为（如播放声音、发送到其他服务等）
    - 输入: stdin 接收 JSON，包含通知内容
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("Notification - 通知", data)
    play_sound("Notification")

def handle_stop():
    """
    Stop: 当 Claude Code 完成响应时运行
    - 用于在响应完成后执行清理或后续操作
    - 输入: stdin 接收 JSON，包含响应相关信息
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("Stop - 响应完成", data)
    play_sound("Stop")

def handle_subagent_stop():
    """
    SubagentStop: 当子代理任务完成时运行
    - 用于在子代理（Task tool）完成后执行操作
    - 输入: stdin 接收 JSON，包含子代理任务信息
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("SubagentStop - 子代理完成", data)
    play_sound("SubagentStop")

def handle_pre_compact():
    """
    PreCompact: 在 Claude Code 即将运行压缩操作之前运行
    - 压缩操作用于减少上下文长度
    - 输入: stdin 接收 JSON，包含压缩相关信息
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("PreCompact - 压缩前", data)
    play_sound("PreCompact")

def handle_session_start():
    """
    SessionStart: 当 Claude Code 启动新会话或恢复现有会话时运行
    - 用于初始化操作
    - 输入: stdin 接收 JSON，包含会话信息
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("SessionStart - 会话开始", data)
    play_sound("SessionStart")

def handle_session_end():
    """
    SessionEnd: 当 Claude Code 会话结束时运行
    - 用于清理操作
    - 输入: stdin 接收 JSON，包含会话信息
    """
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data) if stdin_data else {}
    except:
        data = {"raw": stdin_data}

    log_event("SessionEnd - 会话结束", data)
    play_sound("SessionEnd")

def main():
    if len(sys.argv) < 2:
        print("用法: python claude_hooks.py <event_type>", file=sys.stderr)
        print("支持的事件类型:", file=sys.stderr)
        print("  PreToolUse, PostToolUse, PermissionRequest,", file=sys.stderr)
        print("  UserPromptSubmit, Notification, Stop,", file=sys.stderr)
        print("  SubagentStop, PreCompact, SessionStart, SessionEnd", file=sys.stderr)
        sys.exit(1)

    event_type = sys.argv[1]

    handlers = {
        "PreToolUse": handle_pre_tool_use,
        "PostToolUse": handle_post_tool_use,
        "PermissionRequest": handle_permission_request,
        "UserPromptSubmit": handle_user_prompt_submit,
        "Notification": handle_notification,
        "Stop": handle_stop,
        "SubagentStop": handle_subagent_stop,
        "PreCompact": handle_pre_compact,
        "SessionStart": handle_session_start,
        "SessionEnd": handle_session_end,
    }

    handler = handlers.get(event_type)
    if handler:
        handler()
    else:
        log_event(f"未知事件类型: {event_type}")

if __name__ == "__main__":
    main()
