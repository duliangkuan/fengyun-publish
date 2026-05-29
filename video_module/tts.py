import asyncio
from pathlib import Path

import edge_tts

DEFAULT_VOICE = "zh-CN-YunjianNeural"

PRESET_VOICES = {
    "male_calm": "zh-CN-YunjianNeural",
    "male_news": "zh-CN-YunyangNeural",
    "male_warm": "zh-CN-YunxiNeural",
    "female_warm": "zh-CN-XiaoxiaoNeural",
    "female_smart": "zh-CN-XiaoyiNeural",
}


def synthesize(text: str, output_path: Path, voice: str = DEFAULT_VOICE, rate: str = "+0%") -> Path:
    voice = PRESET_VOICES.get(voice, voice)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_run(text, voice, rate, output_path))
    return output_path


async def _run(text: str, voice: str, rate: str, output_path: Path):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(output_path))
