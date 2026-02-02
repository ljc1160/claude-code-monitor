import os
import json
import sys
import shutil
from pathlib import Path

def detect_python_command():
    """检测系统中可用的 Python 命令"""
    # Windows 优先使用 py launcher
    if sys.platform == 'win32':
        if shutil.which('py'):
            return 'py'
        elif shutil.which('python'):
            return 'python'
    else:
        # Linux/macOS 优先使用 python3
        if shutil.which('python3'):
            return 'python3'
        elif shutil.which('python'):
            return 'python'

    # 如果都找不到，返回默认值
    return 'python3' if sys.platform != 'win32' else 'python'

def install():
    # 检测 Python 命令
    python_cmd = detect_python_command()
    print(f"[INFO] 检测到 Python 命令: {python_cmd}")

    # 获取路径
    project_dir = Path(__file__).parent.absolute()
    claude_dir = Path.home() / ".claude"
    hook_script = project_dir / "claude_hooks.py"

    # 读取模板
    with open(project_dir / "settings.json.template", 'r', encoding='utf-8') as f:
        template_content = f.read()

    # 根据操作系统处理路径
    if sys.platform == 'win32':
        # Windows: 使用反斜杠并转义
        project_path = str(project_dir).replace("\\", "\\\\")
        path_sep = "\\\\"
    else:
        # Linux/macOS: 使用正斜杠，不需要转义
        project_path = str(project_dir)
        path_sep = "/"
        # 将模板中的 Windows 路径分隔符替换为 Unix 路径分隔符
        template_content = template_content.replace("\\\\", "/")

    # 替换占位符
    template_content = template_content.replace("{{PROJECT_DIR}}", project_path)
    template_content = template_content.replace("python ", f"{python_cmd} ")
    config = json.loads(template_content)

    # 合并到用户配置
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.json"

    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        user_config["hooks"] = config["hooks"]
    else:
        user_config = config

    # 保存配置
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(user_config, f, indent=2, ensure_ascii=False)

    print(f"[OK] 配置已更新到: {settings_path}")
    print(f"[OK] Hook 脚本路径: {hook_script}")
    print(f"[OK] 使用 Python 命令: {python_cmd}")

if __name__ == "__main__":
    install()
