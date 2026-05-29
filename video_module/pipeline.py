import argparse
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from providers import get_provider
from tts import synthesize

ROOT = Path(__file__).parent


def run(input_path: Path):
    load_dotenv(ROOT / ".env")
    cfg = yaml.safe_load(input_path.read_text(encoding="utf-8"))

    text = cfg["text"]
    voice = cfg.get("voice", "male_calm")
    image = _resolve(cfg["avatar_image"], input_path.parent)
    provider_name = cfg.get("provider", "falai")
    out_name = cfg.get("output", input_path.stem + ".mp4")
    out_dir = ROOT / "output"
    tmp_dir = ROOT / "tmp"

    if not image.exists():
        sys.exit(f"avatar_image not found: {image}")

    print(f"[1/2] Synthesizing voice ({voice})...")
    audio_path = tmp_dir / f"{input_path.stem}.mp3"
    synthesize(text, audio_path, voice=voice)
    print(f"     -> {audio_path}")

    print(f"[2/2] Generating talking head via {provider_name}...")
    provider = get_provider(provider_name)
    output_path = out_dir / out_name
    provider.generate(
        image_path=image,
        audio_path=audio_path,
        output_path=output_path,
        text_prompt=cfg.get("text_prompt", ""),
        turbo_mode=cfg.get("turbo_mode", True),
        num_inference_steps=cfg.get("num_inference_steps", 30),
        seed=cfg.get("seed"),
    )
    print(f"Done: {output_path}")


def _resolve(p: str, base: Path) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (base / path).resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Text + portrait -> talking-head ad video")
    parser.add_argument("input", help="YAML config path (see scripts/example_input.yaml)")
    args = parser.parse_args()
    run(Path(args.input))
