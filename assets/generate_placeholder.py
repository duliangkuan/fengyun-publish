"""Round 25 placeholder image generator (v2, Jobs P0 revised).

Jobs 反对意见落实:
- 删「图片生成中」文案(不向读者承认空洞)
- 删「云」签名(品牌不该背书故障)
- 删「Round 25 placeholder」内部 metadata(不把 build number 印给读者)
- 改成「有意留白的抽象 sketch」,看起来像设计选择,不像生成失败

视觉:沙黄底 #F8F0E0 + 陶土橙极简 sketch(三个抽象圆 + 一条曲线),无任何文字。
跑一次即可,生成 placeholder-sketch.png 静态文件。
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "placeholder-sketch.png"

W, H = 1920, 1080
BG = (248, 240, 224)   # #F8F0E0 沙黄底
ORANGE = (193, 95, 60)  # #C15F3C 陶土橙
ORANGE_LIGHT = (216, 138, 96)  # 浅陶土

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ============================================================
# 抽象 sketch — 三个手绘风圆 + 一条贯穿曲线,无文字
# Jobs 原则:placeholder 看起来像「设计选择」,不像「失败兜底」
# ============================================================

# 中心区域参考点
cx, cy = W // 2, H // 2

# 1) 主圆(空心,粗描边,中心偏左)
r1 = 220
x1, y1 = cx - 280, cy
draw.ellipse(
    [x1 - r1, y1 - r1, x1 + r1, y1 + r1],
    outline=ORANGE, width=6,
)

# 2) 中圆(填充浅陶土,偏右上,部分跟主圆重叠)
r2 = 140
x2, y2 = cx + 180, cy - 120
draw.ellipse(
    [x2 - r2, y2 - r2, x2 + r2, y2 + r2],
    fill=ORANGE_LIGHT, outline=ORANGE, width=4,
)

# 3) 小圆(空心,右下角)
r3 = 80
x3, y3 = cx + 260, cy + 220
draw.ellipse(
    [x3 - r3, y3 - r3, x3 + r3, y3 + r3],
    outline=ORANGE, width=5,
)

# 4) 贯穿曲线 — 用多个短线段模拟手绘 wobble
def sketch_curve(draw, points: list, color, width=4):
    """两点之间用多段短线连接,微抖动模拟手绘"""
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        draw.line([x0, y0, x1, y1], fill=color, width=width)


curve_points = []
for t in range(0, 100, 2):
    progress = t / 100.0
    # 贝塞尔风格曲线穿过三个圆
    x = int(W * 0.15 + (W * 0.7) * progress)
    y = int(cy + 240 * math.sin(progress * math.pi * 1.8))
    # 微抖动
    if t % 6 == 0:
        x += (-3 if t % 12 == 0 else 3)
    curve_points.append((x, y))

sketch_curve(draw, curve_points, ORANGE, width=5)

# 5) 外框(极细,跟封面体系呼应,但不喧宾夺主)
border = 48
draw.rectangle([border, border, W - border, H - border], outline=ORANGE, width=3)

img.save(OUT, "PNG", optimize=True)
print(f"OK -> {OUT}  size={OUT.stat().st_size // 1024} KB")
