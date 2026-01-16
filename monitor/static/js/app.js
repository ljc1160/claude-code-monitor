/**
 * Claude Code 监控平台 - 前端应用
 */

class ClaudeMonitor {
    constructor() {
        this.ws = null;
        this.events = [];
        this.todos = [];
        this.sessions = {};  // 存储会话信息
        this.stats = {
            total_events: 0,
            events_by_type: {},
            tools_used: {}
        };
        this.soundEnabled = true;
        this.isPaused = false;
        this.startTime = Date.now();
        this.activityData = [];

        this.init();
    }

    init() {
        this.initParticles();
        this.initWebSocket();
        this.initEventListeners();
        this.startClock();
        this.startUptime();
        this.initActivityChart();
    }

    // 粒子背景
    initParticles() {
        const container = document.getElementById('particles');
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 15 + 's';
            particle.style.animationDuration = (10 + Math.random() * 10) + 's';
            container.appendChild(particle);
        }
    }

    // WebSocket 连接
    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.updateConnectionStatus(true);
            this.showSubtitle('已连接到监控服务', 'success');
        };

        this.ws.onclose = () => {
            this.updateConnectionStatus(false);
            this.showSubtitle('连接已断开，正在重连...', 'error');
            setTimeout(() => this.initWebSocket(), 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        setInterval(() => {
            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    }

    updateConnectionStatus(connected) {
        const dot = document.getElementById('ws-dot');
        const status = document.getElementById('ws-status');
        const statusIndicator = document.querySelector('.status-indicator');

        if (connected) {
            dot.classList.add('connected');
            status.textContent = '已连接';
            statusIndicator.querySelector('.status-text').textContent = '运行中';
        } else {
            dot.classList.remove('connected');
            status.textContent = '断开';
            statusIndicator.querySelector('.status-text').textContent = '离线';
        }
    }

    handleMessage(message) {
        switch (message.type) {
            case 'init':
                this.handleInit(message.data);
                break;
            case 'event':
                this.handleEvent(message.data);
                break;
            case 'todos':
                this.handleTodos(message.data);
                break;
            case 'sessions':
                this.handleSessions(message.data);
                break;
        }
    }

    handleInit(data) {
        if (data.stats) {
            // 直接使用后端的统计数据，不需要前端重新统计
            this.stats = data.stats;
            this.updateStats();
        }
        if (data.history) {
            // 只显示历史事件，不重新统计（统计由后端完成）
            data.history.forEach(event => {
                this.addEventToList(event, false);
            });
        }
        if (data.todos) {
            this.handleTodos(data.todos);
        }
        if (data.sessions) {
            this.handleSessions(data.sessions);
        }
    }

    handleSessions(sessions) {
        this.sessions = sessions;
        this.updateSessionsDisplay();
    }

    updateSessionsDisplay() {
        // 更新活跃会话数量显示
        const sessionCount = Object.keys(this.sessions).length;
        const sessionCountEl = document.getElementById('session-count');
        if (sessionCountEl) {
            sessionCountEl.textContent = sessionCount;
        }
        // 渲染会话列表
        this.renderSessions();
    }

    getSessionLabel(event) {
        // 获取会话标签用于显示
        const session = event.session || {};
        const projectName = session.project_name || '';
        const pid = session.pid || '';
        if (projectName) {
            return `[${projectName}]`;
        } else if (pid) {
            return `[PID:${pid}]`;
        }
        return '';
    }

    handleEvent(event) {
        if (this.isPaused) return;
        this.events.unshift(event);
        this.addEventToList(event, true);
        this.addActivityPoint();

        // 获取会话标签
        const sessionLabel = this.getSessionLabel(event);
        const eventName = this.getEventDisplayName(event.event_type);
        const summary = this.getEventSummary(event);

        // 字幕显示包含会话信息
        const subtitleText = sessionLabel
            ? `${sessionLabel} ${eventName}: ${summary}`
            : `${eventName}: ${summary}`;
        this.showSubtitle(subtitleText, 'info');

        // 音频播放由后端 claude_hooks.py 处理，前端不再播放
        // if (this.soundEnabled) {
        //     this.playEventSound(event.event_type);
        // }

        this.stats.total_events++;
        const type = event.event_type;
        this.stats.events_by_type[type] = (this.stats.events_by_type[type] || 0) + 1;

        if (type === 'PreToolUse' || type === 'PostToolUse') {
            // tool_name 在 event.data 中
            const toolName = (event.data && event.data.tool_name) || 'unknown';
            this.stats.tools_used[toolName] = (this.stats.tools_used[toolName] || 0) + 1;
        }
        this.updateStats();
    }

    handleTodos(todos) {
        this.todos = todos;
        this.renderTodos();
    }

    // 事件列表渲染
    addEventToList(event, isNew) {
        const list = document.getElementById('event-list');
        const item = document.createElement('div');
        item.className = `event-item ${isNew ? 'new' : ''}`;
        item.dataset.type = event.event_type;

        const icon = this.getEventIcon(event.event_type);
        const time = this.formatTime(event.timestamp);
        const details = this.getEventDetails(event);
        const sessionLabel = this.getSessionLabel(event);

        item.innerHTML = `
            <div class="event-header">
                <span class="event-type">
                    <span class="event-type-icon">${icon}</span>
                    ${this.getEventDisplayName(event.event_type)}
                    ${sessionLabel ? `<span class="event-session">${sessionLabel}</span>` : ''}
                </span>
                <span class="event-time">${time}</span>
            </div>
            <div class="event-details">${details}</div>
        `;

        list.insertBefore(item, list.firstChild);
        if (isNew) setTimeout(() => item.classList.remove('new'), 2000);
        while (list.children.length > 100) list.removeChild(list.lastChild);
    }

    getEventIcon(type) {
        const icons = {
            'PreToolUse': '🔧', 'PostToolUse': '✅', 'UserPromptSubmit': '💬',
            'Stop': '🏁', 'SubagentStop': '🤖', 'SessionStart': '🚀',
            'SessionEnd': '👋', 'Notification': '🔔', 'PermissionRequest': '🔐', 'PreCompact': '📦'
        };
        return icons[type] || '📌';
    }

    getEventDisplayName(type) {
        const names = {
            'PreToolUse': '工具调用', 'PostToolUse': '工具完成', 'UserPromptSubmit': '用户输入',
            'Stop': '响应完成', 'SubagentStop': '子代理完成', 'SessionStart': '会话开始',
            'SessionEnd': '会话结束', 'Notification': '通知', 'PermissionRequest': '权限请求', 'PreCompact': '上下文压缩'
        };
        return names[type] || type;
    }

    getEventDetails(event) {
        const data = event.data || {};
        if (event.event_type === 'PreToolUse' || event.event_type === 'PostToolUse') {
            const toolName = data.tool_name || '未知';
            return `工具: ${toolName}`;
        }
        if (event.event_type === 'UserPromptSubmit') {
            const prompt = data.prompt || '';
            return prompt.length > 50 ? prompt.substring(0, 50) + '...' : prompt || '用户提交了输入';
        }
        return event.event_name || '';
    }

    getEventSummary(event) {
        const data = event.data || {};
        if (data.tool_name) return data.tool_name;
        if (data.prompt) return data.prompt.substring(0, 30) + '...';
        return '';
    }

    formatTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    // 统计更新
    updateStats() {
        document.getElementById('total-events').textContent = this.stats.total_events;
        ['PreToolUse', 'UserPromptSubmit', 'Stop', 'SubagentStop'].forEach(type => {
            const el = document.getElementById(`stat-${type}`);
            if (el) el.textContent = this.stats.events_by_type[type] || 0;
        });
        this.updateToolsRanking();
    }

    updateToolsRanking() {
        const container = document.getElementById('tools-ranking');
        const tools = Object.entries(this.stats.tools_used).sort((a, b) => b[1] - a[1]).slice(0, 5);
        if (tools.length === 0) {
            container.innerHTML = '<div class="ranking-empty">暂无数据</div>';
            return;
        }
        container.innerHTML = tools.map(([name, count]) => `
            <div class="ranking-item">
                <span class="ranking-name">${name}</span>
                <span class="ranking-count">${count}</span>
            </div>
        `).join('');
    }

    // 会话列表渲染
    renderSessions() {
        const container = document.getElementById('session-list');

        const sessionList = Object.values(this.sessions);
        if (sessionList.length === 0) {
            container.innerHTML = '<div class="session-empty"><div class="empty-icon">💻</div><p>暂无活跃会话</p></div>';
            return;
        }

        // 按最后事件时间排序
        sessionList.sort((a, b) => new Date(b.last_event) - new Date(a.last_event));

        container.innerHTML = sessionList.map(session => {
            const lastEventTime = this.formatTime(session.last_event);
            const projectName = session.project_name || '未知项目';
            const projectPath = session.project_path || '';
            const hostname = session.hostname || '';
            const pid = session.pid || '';
            const sessionId = session.session_id || '';
            const eventCount = session.event_count || 0;

            // 截断路径显示
            const displayPath = projectPath.length > 40
                ? '...' + projectPath.slice(-37)
                : projectPath;

            // 截断会话ID显示（显示前8位）
            const displaySessionId = sessionId.length > 8
                ? sessionId.substring(0, 8) + '...'
                : sessionId;

            return `
                <div class="session-item">
                    <div class="session-header">
                        <span class="session-icon">💻</span>
                        <span class="session-name">${projectName}</span>
                        <span class="session-badge">${eventCount}</span>
                    </div>
                    <div class="session-details">
                        <div class="session-detail-item">
                            <span class="detail-label">🆔</span>
                            <span class="detail-value" title="${sessionId}">${displaySessionId}</span>
                        </div>
                        <div class="session-detail-item">
                            <span class="detail-label">📁</span>
                            <span class="detail-value" title="${projectPath}">${displayPath}</span>
                        </div>
                        <div class="session-detail-item">
                            <span class="detail-label">🖥️</span>
                            <span class="detail-value">${hostname}</span>
                        </div>
                        <div class="session-detail-item">
                            <span class="detail-label">🔢</span>
                            <span class="detail-value">PID: ${pid}</span>
                        </div>
                        <div class="session-detail-item">
                            <span class="detail-label">🕐</span>
                            <span class="detail-value">${lastEventTime}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // 任务列表渲染 (保留以防后续需要)
    renderTodos() {
        const container = document.getElementById('todo-list');
        const progressText = document.getElementById('todo-progress-text');
        const progressBar = document.getElementById('todo-progress-bar');

        // 如果元素不存在，直接返回
        if (!container) return;

        if (!this.todos || this.todos.length === 0) {
            container.innerHTML = '<div class="todo-empty"><div class="empty-icon">📋</div><p>暂无任务</p></div>';
            if (progressText) progressText.textContent = '0/0';
            if (progressBar) progressBar.style.width = '0%';
            return;
        }

        const completed = this.todos.filter(t => t.status === 'completed').length;
        const total = this.todos.length;
        if (progressText) progressText.textContent = `${completed}/${total}`;
        if (progressBar) progressBar.style.width = `${total > 0 ? (completed / total * 100) : 0}%`;

        container.innerHTML = this.todos.map(todo => `
            <div class="todo-item" data-status="${todo.status}">
                <span class="todo-icon">${this.getTodoIcon(todo.status)}</span>
                <span class="todo-text">${todo.status === 'in_progress' ? todo.activeForm : todo.content}</span>
                <span class="todo-status">${this.getTodoStatusText(todo.status)}</span>
            </div>
        `).join('');
    }

    getTodoIcon(status) {
        return { 'pending': '⏳', 'in_progress': '🔄', 'completed': '✅' }[status] || '📌';
    }

    getTodoStatusText(status) {
        return { 'pending': '待处理', 'in_progress': '进行中', 'completed': '已完成' }[status] || status;
    }

    // 字幕显示
    showSubtitle(text, type = 'info') {
        const container = document.getElementById('subtitle-content');
        const colors = { 'info': 'var(--primary)', 'success': 'var(--success)', 'warning': 'var(--warning)', 'error': 'var(--error)' };
        container.innerHTML = `<span class="subtitle-icon" style="color: ${colors[type]}">●</span><span class="subtitle-text">${text}</span>`;
        container.style.animation = 'none';
        container.offsetHeight;
        container.style.animation = 'subtitleSlide 0.5s ease';
    }

    // 音频播放
    playEventSound(eventType) {
        // 音频文件映射 - 使用 wav 格式
        const audioFiles = {
            'PreToolUse': 'pre_tool_use.wav',
            'PostToolUse': 'post_tool_use.wav',
            'UserPromptSubmit': 'user_prompt_submit.wav',
            'Stop': 'stop.wav',
            'SubagentStop': 'subagent_stop.wav',
            'SessionStart': 'session_start.wav',
            'SessionEnd': 'session_end.wav',
            'Notification': 'notification.wav',
            'PermissionRequest': 'permission_request.wav',
            'PreCompact': 'pre_compact.wav'
        };

        const audioFile = audioFiles[eventType];
        if (audioFile) {
            // 尝试播放音频文件
            const audio = new Audio(`/static/audio/${audioFile}`);
            audio.volume = 0.5;
            audio.play().catch(() => {
                // 如果音频文件不存在，使用 Web Audio API 生成提示音
                this.playTone(eventType);
            });
        } else {
            this.playTone(eventType);
        }
    }

    // 使用 Web Audio API 生成提示音（备用方案）
    playTone(eventType) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            const frequencies = {
                'PreToolUse': 440, 'PostToolUse': 523, 'UserPromptSubmit': 392,
                'Stop': 659, 'SubagentStop': 587, 'SessionStart': 784,
                'SessionEnd': 330, 'Notification': 698, 'PermissionRequest': 880
            };

            oscillator.frequency.value = frequencies[eventType] || 440;
            oscillator.type = 'sine';
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            console.log('Audio not supported');
        }
    }

    // 活动图表
    initActivityChart() {
        this.canvas = document.getElementById('activity-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.activityData = new Array(60).fill(0);
        this.drawActivityChart();
        setInterval(() => this.drawActivityChart(), 1000);
    }

    addActivityPoint() {
        this.activityData[this.activityData.length - 1]++;
    }

    drawActivityChart() {
        const canvas = this.canvas;
        const ctx = this.ctx;
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
        const width = canvas.width, height = canvas.height, padding = 10;
        ctx.clearRect(0, 0, width, height);
        this.activityData.shift();
        this.activityData.push(0);
        const maxVal = Math.max(...this.activityData, 1);

        // 绘制网格
        ctx.strokeStyle = 'rgba(0, 212, 255, 0.1)';
        ctx.lineWidth = 1;
        for (let i = 0; i < 5; i++) {
            const y = padding + (height - 2 * padding) * i / 4;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
        }

        // 绘制折线
        ctx.strokeStyle = 'rgba(0, 212, 255, 0.8)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        const stepX = (width - 2 * padding) / (this.activityData.length - 1);
        this.activityData.forEach((val, i) => {
            const x = padding + i * stepX;
            const y = height - padding - (val / maxVal) * (height - 2 * padding);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        ctx.stroke();

        // 渐变填充
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, 'rgba(0, 212, 255, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 212, 255, 0)');
        ctx.lineTo(width - padding, height - padding);
        ctx.lineTo(padding, height - padding);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();
    }

    // 时钟
    startClock() {
        const updateClock = () => {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleString('zh-CN');
        };
        updateClock();
        setInterval(updateClock, 1000);
    }

    // 运行时间
    startUptime() {
        const updateUptime = () => {
            const elapsed = Date.now() - this.startTime;
            const h = Math.floor(elapsed / 3600000);
            const m = Math.floor((elapsed % 3600000) / 60000);
            const s = Math.floor((elapsed % 60000) / 1000);
            document.getElementById('uptime').textContent =
                `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        };
        updateUptime();
        setInterval(updateUptime, 1000);
    }

    // 事件监听
    initEventListeners() {
        document.getElementById('fullscreen-toggle').addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        });

        document.getElementById('clear-events').addEventListener('click', () => {
            document.getElementById('event-list').innerHTML = '';
            this.events = [];
            this.showSubtitle('事件列表已清空', 'info');
        });

        document.getElementById('pause-events').addEventListener('click', () => {
            this.isPaused = !this.isPaused;
            document.getElementById('pause-events').textContent = this.isPaused ? '继续' : '暂停';
            this.showSubtitle(this.isPaused ? '事件流已暂停' : '事件流已恢复', 'info');
        });

        // 设置按钮事件
        document.getElementById('settings-toggle').addEventListener('click', () => {
            this.openSettings();
        });

        document.getElementById('modal-close').addEventListener('click', () => {
            this.closeSettings();
        });

        document.getElementById('settings-cancel').addEventListener('click', () => {
            this.closeSettings();
        });

        document.getElementById('settings-save').addEventListener('click', () => {
            this.saveSettings();
        });

        // 测试钉钉推送
        document.getElementById('test-dingtalk').addEventListener('click', async () => {
            await this.testDingtalk();
        });

        // 点击弹窗外部关闭
        document.getElementById('settings-modal').addEventListener('click', (e) => {
            if (e.target.id === 'settings-modal') {
                this.closeSettings();
            }
        });
    }

    async openSettings() {
        // 加载当前配置
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            this.currentConfig = config;

            // 填充音频开关
            const soundEnabled = config.sound_enabled || {};
            Object.keys(soundEnabled).forEach(eventType => {
                const checkbox = document.getElementById(`sound-${eventType}`);
                if (checkbox) {
                    checkbox.checked = soundEnabled[eventType];
                }
            });

            // 填充钉钉配置
            const dingtalk = config.dingtalk || {};
            document.getElementById('dingtalk-enabled').checked = dingtalk.enabled || false;
            document.getElementById('dingtalk-webhook').value = dingtalk.webhook_url || '';
            document.getElementById('dingtalk-secret').value = dingtalk.secret || '';

            // 填充钉钉事件选择
            const dingtalkEvents = dingtalk.events || [];
            document.querySelectorAll('.dingtalk-event').forEach(checkbox => {
                checkbox.checked = dingtalkEvents.includes(checkbox.value);
            });

            // 显示弹窗
            document.getElementById('settings-modal').classList.add('active');
        } catch (error) {
            console.error('加载配置失败:', error);
            this.showSubtitle('加载配置失败', 'error');
        }
    }

    closeSettings() {
        document.getElementById('settings-modal').classList.remove('active');
    }

    async saveSettings() {
        // 收集音频开关配置
        const soundEnabled = {};
        ['PreToolUse', 'PostToolUse', 'PermissionRequest', 'UserPromptSubmit',
         'Notification', 'Stop', 'SubagentStop', 'PreCompact', 'SessionStart', 'SessionEnd'].forEach(eventType => {
            const checkbox = document.getElementById(`sound-${eventType}`);
            if (checkbox) {
                soundEnabled[eventType] = checkbox.checked;
            }
        });

        // 收集钉钉配置
        const dingtalkEvents = [];
        document.querySelectorAll('.dingtalk-event:checked').forEach(checkbox => {
            dingtalkEvents.push(checkbox.value);
        });

        const config = {
            sound_enabled: soundEnabled,
            dingtalk: {
                enabled: document.getElementById('dingtalk-enabled').checked,
                webhook_url: document.getElementById('dingtalk-webhook').value,
                secret: document.getElementById('dingtalk-secret').value,
                events: dingtalkEvents
            }
        };

        // 保存配置
        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();
            if (result.status === 'ok') {
                this.showSubtitle('配置已保存', 'success');
                this.closeSettings();
                this.currentConfig = config;
            } else {
                this.showSubtitle('配置保存失败: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('保存配置失败:', error);
            this.showSubtitle('配置保存失败', 'error');
        }
    }

    async testDingtalk() {
        const button = document.getElementById('test-dingtalk');
        const originalText = button.textContent;

        try {
            button.disabled = true;
            button.textContent = '发送中...';

            const response = await fetch('/api/test-dingtalk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.status === 'ok') {
                this.showSubtitle('✅ ' + result.message, 'success');
            } else {
                this.showSubtitle('❌ ' + result.message, 'error');
            }
        } catch (error) {
            console.error('测试钉钉推送失败:', error);
            this.showSubtitle('❌ 测试失败: ' + error.message, 'error');
        } finally {
            button.disabled = false;
            button.textContent = originalText;
        }
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.monitor = new ClaudeMonitor();
});
