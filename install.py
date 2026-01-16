import os
import json
from pathlib import Path

def install():
    # 获取路径
    project_dir = Path(__file__).parent.absolute()
    claude_dir = Path.home() / ".claude"
    hook_script = project_dir / "claude_hooks.py"

    # 读取模板
    with open(project_dir / "settings.json.template", 'r', encoding='utf-8') as f:
        template_content = f.read()

    # 替换占位符
    template_content = template_content.replace("{{PROJECT_DIR}}", str(project_dir).replace("\\", "\\\\"))
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

if __name__ == "__main__":
    install()
