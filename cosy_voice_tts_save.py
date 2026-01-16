# coding=utf-8
import os
import sys
import subprocess
import time
import wave

# 自动安装依赖
def auto_install_requirements():
    """检查并安装缺失的依赖包"""
    required_packages = ['dashscope']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"检测到缺失的依赖包: {', '.join(missing_packages)}")
        print("正在自动安装...")

        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} 安装成功")
            except subprocess.CalledProcessError as e:
                print(f"✗ {package} 安装失败: {e}")
                print(f"\n请手动执行: pip install {package}")
                sys.exit(1)

        print("所有依赖包安装完成！\n")

# 执行自动安装
auto_install_requirements()

import dashscope
from dashscope.audio.tts_v2 import *

# 设置 API Key（如果环境变量中没有配置的话）
# dashscope.api_key = "your-api-key"

# 或者从环境变量读取
if not dashscope.api_key:
    dashscope.api_key = "YOUR-API-KEY"

# 模型
model = "cosyvoice-v2"
# 音色
voice = "longanyun"

# 输出目录
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor", "static", "audio")
os.makedirs(output_dir, exist_ok=True)

# 要合成的文本列表
tts_texts = {
    "pre_tool_use": "晓川主人，我先动手了哦",
    "post_tool_use": "报告晓川，这步完成了",
    "permission_request": "晓川主人，这个得您批准一下",
    "user_prompt_submit": "收到晓川指示，立刻执行",
    "notification": "晓川主人，有一条消息等待您的批准",
    "stop": "报告完毕，等晓川下一步指示",
    "subagent_stop": "晓川主人，派出去的小弟回来了",
    "pre_compact": "晓川稍等，我整理下笔记",
    "session_start": "晓川您好，随时待命",
    "session_end": "晓川再见，随叫随到",
}


class SaveToFileCallback(ResultCallback):
    def __init__(self, output_file):
        self._output_file = output_file
        self._audio_data = b""

    def on_open(self):
        print(f"开始合成: {self._output_file}")

    def on_complete(self):
        print(f"合成完成: {self._output_file}")

    def on_error(self, message: str):
        print(f"合成出错: {message}")

    def on_close(self):
        # 保存为 WAV 文件
        with wave.open(self._output_file, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16bit = 2 bytes
            wf.setframerate(22050)
            wf.writeframes(self._audio_data)
        print(f"已保存: {self._output_file}")

    def on_event(self, message):
        pass

    def on_data(self, data: bytes) -> None:
        self._audio_data += data


def synthesize_and_save(name, text):
    output_file = os.path.join(output_dir, f"{name}.wav")
    callback = SaveToFileCallback(output_file)

    synthesizer = SpeechSynthesizer(
        model=model,
        voice=voice,
        format=AudioFormat.PCM_22050HZ_MONO_16BIT,
        callback=callback,
    )

    synthesizer.streaming_call(text)
    time.sleep(0.1)
    synthesizer.streaming_complete()

    print(f"[{name}] 首包延迟: {synthesizer.get_first_package_delay()}ms")
    print("-" * 40)


if __name__ == "__main__":
    print("开始批量合成音频...")
    print("=" * 40)

    for name, text in tts_texts.items():
        synthesize_and_save(name, text)
        time.sleep(0.5)  # 间隔一下避免请求过快

    print("=" * 40)
    print("全部合成完成！")
