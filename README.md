# Claude Code Monitor

[中文文档](README_CN.md)

A real-time monitoring dashboard for Claude Code with a tech-inspired interface.

## Features

- Real-time event monitoring (WebSocket)
- Audio notifications
- DingTalk push notifications
- Task management display
- Activity statistics charts
- Web-based configuration for audio and notifications

## Quick Start

### Windows Users

Simply double-click `run.bat` to install and start.

### macOS/Linux Users

```bash
# 1. Clone the repository
git clone https://github.com/ljc1160/claude-code-monitor.git
cd claude-code-monitor

# 2. Run the startup script
chmod +x run.sh
./run.sh
```

### Manual Installation (Optional)

```bash
# 1. Clone the repository
git clone https://github.com/ljc1160/claude-code-monitor.git
cd claude-code-monitor

# 2. Install dependencies
pip install -r monitor/requirements.txt

# 3. Configure Claude Code hooks
python install.py

# 4. (Optional) Generate audio files
python cosy_voice_tts_save.py

# 5. Start the monitor server
cd monitor
python server.py

# 6. Open the dashboard
# Visit http://localhost:18765 in your browser
```

## Project Structure

```
claude-code-monitor/
├── run.bat                 # Windows one-click launcher
├── run.sh                  # macOS/Linux one-click launcher
├── install.py              # Installation script (auto-configure hooks)
├── claude_hooks.py         # Claude Code hooks implementation
├── settings.json.template  # Hooks configuration template
├── cosy_voice_tts_save.py  # Audio generation script
└── monitor/                # Monitor platform
    ├── server.py          # Backend server
    ├── requirements.txt   # Python dependencies
    ├── config.json        # Configuration file
    ├── static/            # Frontend resources
    └── audio/             # Audio files directory
```

## Configuration

### 1. Hooks Configuration

After running `install.py`, hooks configuration will be automatically merged into `~/.claude/settings.json` (Windows: `%USERPROFILE%\.claude\settings.json`). No manual modification needed.

### 2. Audio Configuration

#### Generate Audio Files

The project provides a `cosy_voice_tts_save.py` script to automatically generate audio files for all events:

```bash
python cosy_voice_tts_save.py
```

Audio files will be saved to `monitor/static/audio/` directory. Supported event types:
- PreToolUse - Before tool use
- PostToolUse - After tool use
- PermissionRequest - Permission request
- UserPromptSubmit - User prompt submit
- Notification - Notification
- Stop - Stop
- SubagentStop - Subagent stop
- PreCompact - Before compact
- SessionStart - Session start
- SessionEnd - Session end

#### Audio Control

Visit **http://localhost:18765/config** to toggle audio playback for each event in the web interface.

### 3. DingTalk Push Configuration

Visit **http://localhost:18765/config** to configure:
- DingTalk robot Webhook URL
- AccessToken (optional)

After configuration, monitoring events will be automatically pushed to DingTalk groups.

## System Requirements

- Windows
- macOS
- Linux

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ljc1160/claude-code-monitor&type=Date)](https://star-history.com/#ljc1160/claude-code-monitor&Date)