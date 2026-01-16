# Claude Code 监控平台

一个具有科技感的实时监控看板，用于监控 Claude Code 的运行状态。

## 功能特性

- 实时事件监控（WebSocket）
- 音频提醒
- 字幕通知
- 任务管理展示
- 活动统计图表

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python server.py

# 3. 访问监控面板
# 浏览器打开 http://localhost:18765
```

## 文件结构

```
monitor/
├── server.py          # 后端服务
├── requirements.txt   # Python 依赖
├── static/
│   ├── index.html     # 前端页面
│   ├── style.css      # 样式文件
│   └── app.js         # 前端逻辑
└── audio/             # 音频资源目录
```

## 配置音频

将音频文件放入 `audio/` 目录，支持的事件类型：
- PreToolUse
- PostToolUse
- Notification
- Stop
- 等等...
