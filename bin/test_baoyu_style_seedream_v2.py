"""
第二张实测 — 验证可复现性,不同主题。强化中文文字渲染指令。
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

# 主题:Agent Harness 的诞生(风云核心定位主题)
PROMPT = """A WeChat article cover illustration in hand-drawn sketchnote style, 2.35:1 cinematic aspect ratio.

# Style (CRITICAL — must be hand-drawn warm sketchnote, NOT flat-vector)
Hand-drawn illustration with visible wobble strokes, natural hand tremor in lines. Paper grain texture on warm cream background (#F8F0E0). Variable line weight (thicker at pressure points). Casual fills with visible brush direction. Slight imperfections that feel personal — like a skilled illustrator's iPad Procreate sketch or a senior dev's whiteboard sketchnote.

# Color Palette
Background: warm cream #F8F0E0.
Primary: terracotta orange #D97757 (Anthropic same-family).
Secondary: warm orange #ED8936, golden yellow #F6AD55 for highlights only.
Line work: deep brown #744210.
Supporting: olive green #788C5D for plants.
Use red sparingly only for warning/alert marks.

# Composition (scene type, left-image right-text split)
LEFT 60% — Narrative scene:
A young cartoon engineer character (simplified hand-drawn face, big eyes, casual hoodie or shirt). He stands beside or inside a "harness frame" — picture a stylized hand-drawn diagram-like structure around him, with concentric labeled regions: "工具" (tools), "记忆" (memory), "上下文" (context), "运行时" (runtime), "验证" (validation). At the center floats a glowing orange brain shape labeled "大模型" (LLM). Around him: a laptop screen with code, a wrench, a small floating cloud labeled "云", arrows connecting elements with hand-drawn dashed lines. Small decorative stars and dots scattered.

RIGHT 40% — Title text area:
- MAIN TITLE (very large, hand-drawn brush stroke Chinese typography, thick wobbly strokes):
  「Harness 才是 Agent」
- KEYWORD HIGHLIGHT: behind the word "Harness" paint a flat yellow #F6AD55 highlighter marker swipe shape
- SUBTITLE (smaller text inside a hand-drawn dashed-line rectangle frame with a tiny star at each corner):
  「如果你不是模型,你就是 Harness」

# Text Rendering Requirements (CRITICAL)
- All Chinese characters must be rendered LEGIBLY and CORRECTLY
- Title characters: hand-lettered brush calligraphy, thick, slight wobble, bouncy baseline
- The English word "Harness" inside the title uses the same hand-drawn stroke style
- Highlight keyword has a flat yellow marker swipe behind it (like a real highlighter pen)
- Subtitle inside a dashed rectangle frame, smaller, thinner stroke
- Decorations: tiny five-pointed stars, dotted arrows, small flower or plant icons at corners

# Mood
Balanced contrast, warm and approachable, narrative storytelling feel. Densely populated with concrete props that tell the article's story. Like a senior engineer's whiteboard explanation of an idea.

# What to AVOID (CRITICAL)
- NO flat-vector geometric minimalism
- NO single abstract cloud or shape on empty white background
- NO photorealistic elements, NO 3D, NO gradients
- NO generic AI clichés (robot heads, blue neural network grids, glowing data streams)
- NO over-bright neon or cool blue palette
- Whitespace should be 25-35% MAX (not 70%) — composition should feel populated"""

def gen(prompt_text, out_path, size="2K"):
    payload = {"model": MODEL, "prompt": prompt_text, "size": size, "response_format": "url", "watermark": False}
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
    out = ROOT / "output" / "images" / "baoyu_style_test" / "seedream_v2_harness.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        seed = gen(PROMPT, out)
        print(f"\n=== OK seed={seed} ===\n{out}")
    except Exception as e:
        print(f"=== FAIL: {e}", file=sys.stderr)
        sys.exit(1)
