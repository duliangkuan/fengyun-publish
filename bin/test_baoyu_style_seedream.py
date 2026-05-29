"""
实测脚本:用豆包 Seedream 5.0 + 宝玉式 prompt 测试能否复现宝玉风格。
基于 baoyu-cover-image 官方 sketch-notes 预设(warm palette + hand-drawn rendering + scene type + title-subtitle)。
"""
from __future__ import annotations
import json, os, ssl, sys, time, urllib.request
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
load_dotenv(ROOT / ".env")
ARK_KEY = os.environ["VOLCENGINE_IMAGE_KEY"]
ARK_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL = "doubao-seedream-5-0-260128"

# 实测主题:风云 v4 主题「Anthropic 一周 7 件事」
# 对应宝玉风:type=scene + palette=warm + rendering=hand-drawn + text=title-subtitle
PROMPT_BAOYU_STYLE = """A WeChat article cover illustration in hand-drawn sketchnote style, 2.35:1 cinematic aspect ratio.

# Style (CRITICAL)
Hand-drawn illustration with visible wobble strokes, natural hand tremor in lines. Paper grain texture on warm cream background (#FFFAF0 / #F8F0E0). Variable line weight. Casual fills with visible brush direction. Slight imperfections that feel personal, like a skilled illustrator's iPad Procreate sketch.

# Color Palette (warm)
Warm Orange #ED8936 as primary, Terracotta #C05621 as accent, Golden Yellow #F6AD55 for highlights, soft cream #FFFAF0 background. Sparingly use Deep Brown #744210 for line work and Soft Red #E53E3E for warning/important marks. Olive green #788C5D as supporting accent for nature/plant elements.

# Composition (scene type, split layout)
LEFT HALF (60%): Narrative illustration scene depicting "Anthropic's seven announcements in one week" — a young cartoon engineer character (simplified face, hand-drawn style) standing in a workshop scene with 7 floating cards/icons around him: a sword icon, a tea cloud, a bank warning sign, a broken cage, a 7-day calendar, a code window, and a glowing terminal. The engineer looks thoughtful, holding one card. Decorative dotted arrows connecting elements. Small plants and stars as decorative elements.

RIGHT HALF (40%): Title text area, embedded in the illustration with hand-lettered Chinese typography.
- Main title (large, hand-drawn brush stroke style): 「Anthropic 一周 7 件事」
- Highlight one keyword with a yellow marker swipe behind it: 「7 件事」 has a flat yellow #F6AD55 highlighter swipe behind it
- Subtitle (smaller, below title in a hand-drawn dashed-line frame with two small stars at corners): 「神话、银行、破笼、剑 — 一周的 Anthropic 信号」

# Text Rendering
Chinese characters MUST be rendered clearly and legibly, in hand-drawn brush calligraphy style. Title characters thick, bouncy baseline, slight wobble. Highlight keyword wrapped in yellow marker swipe shape. Subtitle in thinner stroke inside a hand-drawn dashed rectangle decoration.

# Mood
Balanced contrast, warm and approachable, narrative storytelling feel. NOT minimalist, NOT abstract — densely populated with concrete props that tell the article's story.

# What to AVOID
- NO flat-vector geometric style
- NO single abstract symbol on white background
- NO photorealistic elements
- NO 3D rendering or gradients
- NO English UI text overlay
- NO generic AI symbols (brain, neural network nodes, robot heads)

# Final Check
The result should look like a hand-drawn warm-cream illustrated WeChat cover, with embedded Chinese title and a young engineer cartoon character in a narrative scene. Reference visual family: warm cream paper sketchnote illustrations from popular AI Chinese tech blogs (similar to dotey/baoyu style)."""

def gen(prompt_text: str, out_path: Path, size: str = "2K"):
    payload = {
        "model": MODEL,
        "prompt": prompt_text,
        "size": size,
        "response_format": "url",
        "watermark": False,
    }
    headers = {"Authorization": f"Bearer {ARK_KEY}", "Content-Type": "application/json"}
    req = urllib.request.Request(ARK_URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    print(f"[seedream] generating (size={size})…", flush=True)
    t0 = time.time()
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=240) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    img_url = data["data"][0]["url"]
    seed = data["data"][0].get("seed")
    print(f"[seedream] done in {time.time()-t0:.1f}s, seed={seed}", flush=True)
    urllib.request.urlretrieve(img_url, str(out_path))
    print(f"[seedream] saved → {out_path}", flush=True)
    return seed

if __name__ == "__main__":
    out = ROOT / "output" / "images" / "baoyu_style_test" / "seedream_v1_anthropic_7days.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        seed = gen(PROMPT_BAOYU_STYLE, out)
        print(f"\n=== OK seed={seed} ===\n{out}")
    except Exception as e:
        print(f"=== FAIL: {e}", file=sys.stderr)
        sys.exit(1)
