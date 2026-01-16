# Claude Code Monitor

[English](README.md)

Claude Code 监控平台 - 实时监控 Claude Code 运行状态的科技感看板。

## 功能特性

- 实时事件监控（WebSocket）
- 音频提醒
- 钉钉推送通知
- 任务管理展示
- 活动统计图表
- Web 管理界面配置音频开关和推送设置

## 快速开始

### Windows 用户

双击运行 `run.bat` 即可完成安装和启动。

### macOS/Linux 用户

```bash
# 1. Clone 项目
git clone https://github.com/ljc1160/claude-code-monitor.git
cd claude-code-monitor

# 2. 运行启动脚本
chmod +x run.sh
./run.sh
```

### 手动安装（可选）

```bash
# 1. Clone 项目
git clone https://github.com/ljc1160/claude-code-monitor.git
cd claude-code-monitor

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 Claude Code hooks
python install.py

# 4. （可选）生成音频文件
python cosy_voice_tts_save.py

# 5. 启动监控服务
cd monitor
python server.py

# 6. 访问监控面板
# 浏览器打开 http://localhost:18765
```

## 文件结构

```
claude-code-monitor/
├── run.bat                 # Windows 一键启动脚本
├── run.sh                  # macOS/Linux 一键启动脚本
├── install.py              # 安装脚本（自动配置 hooks）
├── claude_hooks.py         # Claude Code hooks 实现
├── settings.json.template  # Hooks 配置模板
├── cosy_voice_tts_save.py  # 音频生成脚本
├── monitor/                # 监控平台
│   ├── server.py          # 后端服务
│   ├── config.json        # 配置文件
│   ├── static/            # 前端资源
│   └── audio/             # 音频文件目录
└── requirements.txt        # Python 依赖
```

## 配置说明

### 1. Hooks 配置

运行 `install.py` 后，会自动将 hooks 配置合并到 `~/.claude/settings.json`（Windows 为 `%USERPROFILE%\.claude\settings.json`），无需手动修改。

### 2. 音频配置

#### 生成音频文件

项目提供了 `cosy_voice_tts_save.py` 脚本，可自动生成所有事件的音频文件：

```bash
python cosy_voice_tts_save.py
```

音频文件会自动保存到 `monitor/static/audio/` 目录。支持的事件类型：
- PreToolUse - 工具使用前
- PostToolUse - 工具使用后
- PermissionRequest - 权限请求
- UserPromptSubmit - 用户提交提示
- Notification - 通知
- Stop - 停止
- SubagentStop - 子代理停止
- PreCompact - 压缩前
- SessionStart - 会话开始
- SessionEnd - 会话结束

#### 音频开关控制

访问 **http://localhost:18765/config** 可在 Web 界面动态开关各事件的音频播放。

### 3. 钉钉推送配置

访问 **http://localhost:18765/config** 设置：
- 钉钉机器人 Webhook URL
- AccessToken（可选）

配置后，监控事件会自动推送到钉钉群。

## 系统支持

- Windows
- macOS
- Linux
