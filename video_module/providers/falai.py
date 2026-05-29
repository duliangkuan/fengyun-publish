import os
from pathlib import Path

import fal_client
import requests

from .base import AvatarProvider


class FalAIProvider(AvatarProvider):
    name = "falai"
    endpoint = "fal-ai/hunyuan-avatar"

    def __init__(self):
        key = os.getenv("FAL_KEY")
        if not key:
            raise RuntimeError("FAL_KEY not set. Put it in .env or export it.")

    def generate(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
        text_prompt: str = "",
        turbo_mode: bool = True,
        num_inference_steps: int = 30,
        seed: int | None = None,
    ) -> Path:
        image_url = fal_client.upload_file(str(image_path))
        audio_url = fal_client.upload_file(str(audio_path))

        arguments = {
            "image_url": image_url,
            "audio_url": audio_url,
            "turbo_mode": turbo_mode,
            "num_inference_steps": num_inference_steps,
        }
        if text_prompt:
            arguments["text"] = text_prompt
        if seed is not None:
            arguments["seed"] = seed

        result = fal_client.subscribe(
            self.endpoint,
            arguments=arguments,
            with_logs=True,
            on_queue_update=_log_queue,
        )

        video_url = result["video"]["url"] if "video" in result else result.get("url")
        if not video_url:
            raise RuntimeError(f"No video URL in response: {result}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(video_url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
        return output_path


def _log_queue(update):
    if hasattr(update, "logs"):
        for log in update.logs:
            print(f"[fal] {log.get('message', '')}")
