# Claude 风格公众号封面调研

*调研日期：2026-05-21*
*目标：为「研究Agent的云」公众号产出封面主力风格*
*调研方法：WebFetch + WebSearch 多轮，一手源：Refero Design System、awesome-claude-design、baoyu-skills GitHub、baoyu X posts*

---

## 1. Anthropic 官方视觉系统

### 主品牌色（完整色板，来源：Refero Design System）

来源 URL：https://styles.refero.design/style/d469cba4-c448-4a43-a033-883f8bfcdc42

| 色彩角色 | 名称 | Hex | 用途 |
|---------|------|-----|------|
| **主强调色** | Clay（陶土橙） | `#d97757` | Primary CTA、高亮状态 |
| **悬停强调色** | Accent Ember | `#c6613f` | 悬停/按下状态 |
| **背景基底** | Ivory Light | `#faf9f5` | 页面底色（暖羊皮纸色） |
| **次级背景** | Ivory Medium | `#f0eee6` | 导航、次级卡片 |
| **三级背景** | Ivory Dark | `#e8e6dc` | 深色背景上的文字 |
| **燕麦色卡片** | Oat | `#e3dacc` | 三级卡片背景 |
| **主文字** | Slate Dark | `#141413` | 主体文字、边框 |
| **次级文字** | Slate Medium | `#3d3d3a` | 中等深度边框 |
| **辅助文字** | Slate Light | `#5e5d59` | 三级文字、说明文字 |
| **禁用/弱化** | Cloud Medium | `#b0aea5` | 禁用态边框 |
| **分割线** | Cloud Light | `#d1cfc5` | 细分割线 |
| **橄榄绿** | Olive | `#788c5d` | 分类标签变体 |
| **天空蓝** | Sky | `#6a9bcc` | 分类标签变体 |
| **无花果粉** | Fig | `#c46686` | 分类标签变体 |
| **仙人掌绿** | Cactus | `#bcd1ca` | 分类标签变体 |

> 补充源确认（来源：awesome-claude-design warm editorial 家族）：
> Claude/Anthropic 的品牌色三元组为 `#f4f3ee / #c96442 / #191817`
> 使用字体：**Styrene**（UI）+ **Tiempos**（衬线正文）
>
> 补充源（来源：brandcolorcode.com）：
> 品牌代表色 Peach：`#DE7356`（这是最广为流传的"Claude 橙"）

### 字体系统

| 字体家族 | 角色 | 降级方案 |
|---------|------|---------|
| **Anthropic Sans** | UI、导航、按钮 | Inter → DM Sans |
| **Anthropic Serif** | 封面标题、feature card | Playfair Display → Lora |
| **Anthropic Mono** | 元数据、技术数据 | JetBrains Mono → IBM Plex Mono |

### 图形语言

- **几何风格**：方形按钮（border-radius: 0px），卡片 8px 圆角，克制不花哨
- **表面分层**：4 个层次从暖米到近黑（#faf9f5 → #f0eee6 → #e3dacc → #141413）
- **留白充足**：base unit 4px，section gap 61px，无装饰性元素
- **色彩使用极克制**：整个色彩预算集中在单一陶土橙 Clay，其余全为暖中性色

### 与竞品对比

| 品牌 | 主色调 | 风格关键词 |
|------|--------|----------|
| **Anthropic/Claude** | 暖米 + 陶土橙 | 暖编辑体、人文感、羊皮纸 |
| **OpenAI** | 黑 + 白 | Terminal-Core、冷酷工业 |
| **Google** | 多彩（红蓝黄绿）| Playful Color、消费级 |
| **Apple** | 磨砂玻璃白 | Glass/Soft-Futurism |
| **RunwayML** | 深黑 + 饱和渐变 | Cinematic Dark |

**结论**：Anthropic 处于"Warm Editorial"美学家族的顶端定义者，暖、慢、文字重，反对 AI slop 黑色科技感。

---

## 2. 宝玉 AI 封面样本分析

### 工具确认

来源：宝玉 X 账号 @dotey
- **使用工具**：自研开源 `baoyu-cover-image` skill（GitHub: JimLiu/baoyu-skills）
- **图像生成后端**：Claude Code (Opus 4.6) 调度 + Gemini API / Nano Banana Pro 出图
- **已确认使用参数**：
  - `--style warm-flat --font handwritten --aspect 2.35:1`（来源：https://x.com/dotey/status/2019877291044553120）
  - `--type conceptual --palette warm --rendering flat-vector`（工具文档示例）

### 宝玉公开分享的 Prompt 样例（手绘科普图）

来源：https://x.com/dotey/status/2047493663580659734

```
one-page hand-drawn educational infographic
Style: Warm cream paper background (#F5F0E8), clean sketchnote style with slight hand-drawn wobble. 
No realistic elements. Looks like a notebook sketch.
```

**颜色确认**：`#F5F0E8`（暖奶油纸色，与 Anthropic 的 `#faf9f5` 非常接近）

### 风格特征提炼

| 特征维度 | 宝玉 AI 封面 |
|---------|------------|
| **色系** | 暖米色 / 暖奶油 / 淡陶土 (`#F5F0E8` ± 10%) |
| **渲染风格** | flat-vector 为主 / 偶用 hand-drawn |
| **构图** | conceptual（概念插图）/ minimal |
| **字体方向** | handwritten（手写体）/ 衬线 |
| **比例** | 2.35:1 电影宽屏 为主，部分 16:9 |
| **装饰元素** | 极简线条 / 抽象几何 / 概念化图标 |
| **文字处理** | title-only 或无文字，交给文章页处理 |

---

## 3. 赛博禅心封面样本分析

### 账号确认

- 主理人：大聪明（宋先生），产品经理背景
- 定位："拜AI古佛，修赛博禅心" / AI一手信息+技术实测+产品思考
- 阅读量：67篇作品，总阅读量215247（来源：搜索结果）
- 虎嗅号：https://m.huxiu.com/member/9910664.html

### 风格推断（注：无法直接 WebFetch 微信文章图片，以下为综合推断）

基于：
1. 用户观察（"跟宝玉风格雷同，跟 Claude 网页色调一致"）
2. 赛博禅心账号定位（Claude/Anthropic 专注内容）
3. "赛博禅心"这一名称本身带有极简东方感

推断风格特征：

| 特征维度 | 赛博禅心封面（推断） |
|---------|------------|
| **色系** | 暖米/暖灰 + 黑/深色文字 |
| **渲染风格** | minimal / flat / editorial |
| **氛围** | 禅意 + 科技感并存，非商业感 |
| **文字处理** | 大标题 + 极简留白 |

**调研空白**：赛博禅心封面无法直接 WebFetch（微信文章图需登录），以上为合理推断。

---

## 4. 两人风格共性 + 差异

### 共性（这是"Claude 风格"的真实定义）

1. **暖米色底**：背景色 `#F5F0E8` ~ `#faf9f5`（温暖、纸感、非纯白）
2. **陶土橙点缀**：强调色一律用暖橙/陶土（`#d97757` ~ `#DE7356` ~ `#c96442`）
3. **极简留白**：60%+ 留白，反对装饰堆砌
4. **平面插图风**：flat-vector 或 hand-drawn，不用写实摄影
5. **人文气质**：衬线/手写字体，对抗 AI slop 科技感

### 差异

| 维度 | 宝玉 AI | 赛博禅心（推断）|
|------|--------|--------------|
| 工具 | 自研 baoyu-cover-image skill | 未知（可能手工或其他工具）|
| 比例 | 2.35:1 电影宽屏 | 可能 16:9 或 3:4 |
| 风格偏向 | 更活泼（conceptual+hand-drawn混用）| 更禅意（minimal为主）|

---

## 5. 公开的 Prompt 资源

| 资源 | URL | 简介 |
|-----|-----|-----|
| baoyu-skills（含 cover-image skill）| https://github.com/JimLiu/baoyu-skills | 宝玉开源工具集，5维度封面生成 |
| awesome-claude-design | https://github.com/rohitg00/awesome-claude-design | 9个设计美学家族 + DESIGN.md prompt |
| Anthropic 设计系统（Refero）| https://styles.refero.design/style/d469cba4-c448-4a43-a033-883f8bfcdc42 | 完整设计 token 含 hex |
| Seedream 5.0 prompting guide（fal.ai）| https://blog.fal.ai/seedream-5-0-lite-prompting-guide/ | Seedream 官方提示词指南 |
| Seedream 5.0 prompting（Replicate）| https://replicate.com/blog/how-to-prompt-seedream-5 | 实战 prompt 示例 |
| Claude frontend aesthetics cookbook | https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics | 官方避免 AI slop 指南 |
| Claude Design 系统分析 | https://getdesign.md/claude/design-md | 独立分析 Claude 设计系统 |

**意外发现**：
- baoyu-cover-image skill 完全开源，可直接 `npx skills add jimliu/baoyu-skills` 安装使用，已内置 warm-flat 预设，不需要自己写 prompt
- awesome-claude-design 明确将 Claude/Anthropic 归为"Warm Editorial"家族，并给出参考色三元组

---

## 6. 「研究Agent的云」封面主力风格规范

### 主色板（基于 Anthropic 官方 + 宝玉实践综合）

| 色彩角色 | 名称 | Hex | 备注 |
|---------|------|-----|------|
| **主背景** | 暖羊皮纸 | `#F5F0E8` | 宝玉实证用色，接近 Anthropic `#faf9f5` |
| **次背景/卡片** | 燕麦白 | `#EDE8DF` | Anthropic Ivory Medium 变体 |
| **主强调色** | 陶土橙 | `#D97757` | Anthropic Clay 官方色 |
| **深强调色** | 琥珀橙 | `#C6613F` | Anthropic Accent Ember，按压态 |
| **主文字** | 近黑暖灰 | `#191817` | 接近 Anthropic Slate Dark `#141413` |
| **次级文字** | 温暖深灰 | `#5E5D59` | Anthropic Slate Light |
| **装饰点缀** | 橄榄绿 | `#788C5D` | Anthropic Olive，用于分类标签 |

### 视觉元素清单

| 维度 | 规范 |
|------|------|
| **主元素类型** | 平面插图（flat-vector）/ 手绘风（hand-drawn），禁用写实摄影 |
| **构图类型** | conceptual（概念型）为主，minimal（极简）次之 |
| **留白比例** | 背景占比 60-70%，主元素居中或偏上 |
| **字体方向** | 衬线（Playfair Display / Lora）或手写体；避免 Inter、Roboto |
| **文字处理** | title-only 或无文字（WeChat 封面标题在文章列表中显示） |
| **比例** | 主推 2.35:1（宽屏电影比）；也可用 16:9（标准）或 1:1（方形） |
| **装饰元素** | 极简几何线条、抽象圆形/球体、思维气泡、连接节点等 AI/Agent 相关隐喻 |
| **禁用元素** | 渐变紫色背景、蓝色科技感、深色科幻感、真实人像摄影 |
| **品牌一致性** | 所有封面保持色板一致，不同文章用不同构图变体 |

---

## 7. 5 个 Seedream Prompt 模板

> 注：以下所有 prompt 基于 Seedream 5.0 最佳实践（自然语言为主，30-80 词，引号包裹文字渲染）。推荐 Seedream 5.0 Lite via fal.ai 或火山 Seedream API。

---

### 模板 1：【Agent 网络 / 多智能体协作】暖色概念插图

```
A flat-vector editorial illustration on a warm cream paper background (#F5F0E8). Abstract minimalist scene: several glowing soft-orange circular nodes connected by clean geometric lines, suggesting a multi-agent network or neural mesh. The nodes pulse with warm terracotta light (#D97757) against an ivory field. A single larger node floats at center, surrounded by smaller satellite circles. Style: clean flat design, subtle hand-drawn texture on node edges, generous white space, no text, no humans, no photorealism. Mood: intellectual warmth, calm emergence. Aspect ratio 2.35:1.
```

**触发场景**：Agent 协作、多智能体系统、LLM 组合、AI 架构类文章
**预期效果**：暖米底 + 橙色节点网络，轻松体现 Agent 主题而不科幻
**关键词分类**：
- 色系：cream `#F5F0E8` / terracotta `#D97757`
- 元素：circular nodes / geometric lines / network
- 风格：flat-vector / hand-drawn texture
- 氛围：intellectual warmth / calm

---

### 模板 2：【深度研究 / 思考分析】暖色极简书页风

```
A minimal editorial cover illustration in warm editorial style. Background: aged parchment texture (#F5F0E8). Central motif: a single open book or folded document, rendered in clean flat linework with terracotta orange (#D97757) spine and page edges. A soft glowing magnifying glass or eye symbol overlaps the top corner. Generous negative space surrounds the central element. Typography mood: serif, contemplative. Style: hand-drawn sketchnote with slight paper grain, no gradient fills, flat color only. Mood: deep thinking, research, slow reading. 16:9 aspect ratio.
```

**触发场景**：调研报告、深度评测、行业分析、论文解读类文章
**预期效果**：书页 + 放大镜元素，学术感，适合「研究」定位
**关键词分类**：
- 色系：parchment `#F5F0E8` / terracotta accent
- 元素：open book / magnifying glass / paper grain
- 风格：hand-drawn sketchnote / flat color
- 氛围：contemplative / research

---

### 模板 3：【工具测评 / 产品对比】现代极简编辑体

```
A clean flat editorial cover in warm Anthropic aesthetic. Scene: two or three simplified geometric UI windows or cards arranged asymmetrically on a warm ivory background (#F0EEE6). One card is highlighted with a soft terracotta border (#C6613F). Thin olive-green (#788C5D) horizontal rule divides the composition. No text. No photorealistic elements. Style: flat-vector design, zero gradients, clean outline stroke weight 1.5px, very generous padding. Mood: balanced comparison, objective analysis, calm precision. 16:9 widescreen.
```

**触发场景**：Claude vs GPT / 工具横评 / 产品测评 / API 比较类文章
**预期效果**：极简卡片对比构图，传递客观评测气质
**关键词分类**：
- 色系：ivory `#F0EEE6` / terracotta `#C6613F` / olive `#788C5D`
- 元素：UI windows / cards / horizontal rule
- 风格：flat-vector / zero gradients
- 氛围：objective / precise

---

### 模板 4：【AI 前沿动态 / 新模型发布】暖色动态概念图

```
An editorial conceptual illustration with a warm cream base (#F5F0E8). A large abstract geometric form—like an unfolding origami shape or expanding hexagon—sits centered, rendered in warm terracotta gradient from #D97757 to #E8A882. Fine dotted lines radiate outward from the form's edges suggesting emergence or release. Background has a subtle paper grain texture. Style: editorial flat illustration with minimal hand-drawn details, no text, no photorealism, cinematic proportions. Mood: anticipation, emergence, intelligent expansion. Aspect ratio 2.35:1.
```

**触发场景**：模型发布、技术突破、新功能上线、行业前沿类文章
**预期效果**：展开几何形体隐喻"新事物涌现"，热度感但不失暖雅
**关键词分类**：
- 色系：cream / terracotta gradient `#D97757` to `#E8A882`
- 元素：origami / hexagon / radiating dots
- 风格：editorial flat / paper grain
- 氛围：anticipation / emergence

---

### 模板 5：【方法论 / 系统思维】禅意极简水墨改良版（推荐作为主力）

```
A minimalist editorial illustration blending warm Anthropic aesthetic with subtle East Asian ink wash sensibility. Background: warm ivory (#FAF9F5) with very light paper texture. Central composition: a single brushstroke-style circle (enso-like) rendered in warm charcoal (#3D3D3A) with one small terracotta orange accent dot (#D97757) at the top. Below, three thin horizontal geometric lines in cloud gray (#B0AEA5) suggest structure and flow. Extremely generous white space (70%). No text, no gradients, no photorealism. Style: minimal flat with ink wash texture on the brushstroke. Mood: clarity, systems thinking, calm intelligence. 16:9 widescreen.
```

**触发场景**：方法论文章、系统设计、思维框架、哲学思考类文章
**预期效果**：禅圆 + 暖色调 + 极简横线，直接命中「研究Agent的云」的禅意+AI定位
**关键词分类**：
- 色系：ivory `#FAF9F5` / charcoal `#3D3D3A` / terracotta dot `#D97757`
- 元素：enso circle / horizontal lines / paper texture
- 风格：minimal flat / ink wash texture
- 氛围：clarity / calm intelligence

---

## 7. 调研空白（找不到的）

- 赛博禅心具体封面图：微信文章图片需登录，WebFetch 无法抓取。分析为综合推断。
- baoyu-cover-image skill 内部 EXTEND.md 的 `warm-flat` 完整 prompt 内容：该文件在 runtime 生成，未公开
- Anthropic Sans / Anthropic Serif 字体文件：私有字体，未对外发布，只有降级方案
- 赛博禅心使用的具体图像工具：未公开声明

---

## 8. 一键测试：用 5 个模板生成 5 张样本封面

以下 Python 脚本调用火山引擎 Seedream API 批量生成 5 张封面对比样本。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claude_style_cover_test.py
批量生成「研究Agent的云」封面样本，测试5个模板
使用火山引擎 Seedream API（Seedream 5.0 / Seedream 4.5）
"""

import os
import base64
import json
import time
from pathlib import Path
import httpx

# ==================== 配置 ====================
API_KEY = os.environ.get("VOLC_SEEDREAM_API_KEY", "your-api-key-here")
OUTPUT_DIR = Path("D:/Dev/ai-wechat-pipeline/output/cover_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 火山引擎 Seedream API endpoint（以实际为准，以下为 fal.ai 兼容示例）
# 如用火山官方 API，请改为 https://ark.cn-beijing.volces.com/api/v3/images/generations
API_URL = "https://api.us.fal.ai/fal-ai/seedream-5-lite/text-to-image"
HEADERS = {
    "Authorization": f"Key {API_KEY}",
    "Content-Type": "application/json"
}

# ==================== 5 个模板 ====================
TEMPLATES = [
    {
        "id": "T1_agent_network",
        "theme": "Agent网络/多智能体协作",
        "aspect": "2.35:1",
        "prompt": (
            "A flat-vector editorial illustration on a warm cream paper background (#F5F0E8). "
            "Abstract minimalist scene: several glowing soft-orange circular nodes connected by clean geometric lines, "
            "suggesting a multi-agent network or neural mesh. The nodes pulse with warm terracotta light (#D97757) "
            "against an ivory field. A single larger node floats at center, surrounded by smaller satellite circles. "
            "Style: clean flat design, subtle hand-drawn texture on node edges, generous white space, no text, "
            "no humans, no photorealism. Mood: intellectual warmth, calm emergence."
        )
    },
    {
        "id": "T2_deep_research",
        "theme": "深度研究/思考分析",
        "aspect": "16:9",
        "prompt": (
            "A minimal editorial cover illustration in warm editorial style. Background: aged parchment texture (#F5F0E8). "
            "Central motif: a single open book or folded document, rendered in clean flat linework with terracotta orange "
            "(#D97757) spine and page edges. A soft glowing magnifying glass or eye symbol overlaps the top corner. "
            "Generous negative space surrounds the central element. Style: hand-drawn sketchnote with slight paper grain, "
            "no gradient fills, flat color only. Mood: deep thinking, research, slow reading."
        )
    },
    {
        "id": "T3_product_review",
        "theme": "工具测评/产品对比",
        "aspect": "16:9",
        "prompt": (
            "A clean flat editorial cover in warm Anthropic aesthetic. Scene: two or three simplified geometric UI windows "
            "or cards arranged asymmetrically on a warm ivory background (#F0EEE6). One card is highlighted with a soft "
            "terracotta border (#C6613F). Thin olive-green (#788C5D) horizontal rule divides the composition. No text. "
            "No photorealistic elements. Style: flat-vector design, zero gradients, clean outline stroke weight 1.5px, "
            "very generous padding. Mood: balanced comparison, objective analysis, calm precision."
        )
    },
    {
        "id": "T4_ai_news",
        "theme": "AI前沿动态/新模型发布",
        "aspect": "2.35:1",
        "prompt": (
            "An editorial conceptual illustration with a warm cream base (#F5F0E8). A large abstract geometric form "
            "like an unfolding origami shape or expanding hexagon sits centered, rendered in warm terracotta gradient "
            "from #D97757 to #E8A882. Fine dotted lines radiate outward from the form's edges suggesting emergence or release. "
            "Background has a subtle paper grain texture. Style: editorial flat illustration with minimal hand-drawn details, "
            "no text, no photorealism, cinematic proportions. Mood: anticipation, emergence, intelligent expansion."
        )
    },
    {
        "id": "T5_zen_method",
        "theme": "方法论/系统思维（推荐主力）",
        "aspect": "16:9",
        "prompt": (
            "A minimalist editorial illustration blending warm Anthropic aesthetic with subtle East Asian ink wash sensibility. "
            "Background: warm ivory (#FAF9F5) with very light paper texture. Central composition: a single brushstroke-style "
            "circle (enso-like) rendered in warm charcoal (#3D3D3A) with one small terracotta orange accent dot (#D97757) "
            "at the top. Below, three thin horizontal geometric lines in cloud gray (#B0AEA5) suggest structure and flow. "
            "Extremely generous white space (70%). No text, no gradients, no photorealism. "
            "Style: minimal flat with ink wash texture on the brushstroke. Mood: clarity, systems thinking, calm intelligence."
        )
    }
]

# aspect ratio → width x height（基于 WeChat 公众号最优尺寸）
ASPECT_TO_SIZE = {
    "2.35:1": (1080, 460),   # 电影宽屏，公众号适配
    "16:9": (900, 500),       # 标准宽屏
    "1:1": (900, 900),        # 方形
}

def generate_cover(template: dict) -> Path:
    w, h = ASPECT_TO_SIZE.get(template["aspect"], (900, 500))
    payload = {
        "prompt": template["prompt"],
        "image_size": {"width": w, "height": h},
        "num_inference_steps": 28,
        "guidance_scale": 6.5,
        "num_images": 1,
        "output_format": "jpeg"
    }
    
    print(f"[{template['id']}] 生成中: {template['theme']}")
    
    resp = httpx.post(API_URL, headers=HEADERS, json=payload, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    
    # fal.ai 返回格式：{"images": [{"url": "..."}]}
    img_url = result["images"][0]["url"]
    img_bytes = httpx.get(img_url).content
    
    out_path = OUTPUT_DIR / f"{template['id']}.jpg"
    out_path.write_bytes(img_bytes)
    print(f"  -> 保存到: {out_path}")
    return out_path

def main():
    print("=== 「研究Agent的云」封面样本批量生成 ===")
    print(f"输出目录: {OUTPUT_DIR}")
    print()
    
    results = []
    for tmpl in TEMPLATES:
        try:
            path = generate_cover(tmpl)
            results.append({"id": tmpl["id"], "status": "OK", "path": str(path)})
        except Exception as e:
            print(f"  [ERROR] {tmpl['id']}: {e}")
            results.append({"id": tmpl["id"], "status": "ERROR", "error": str(e)})
        time.sleep(2)  # 避免限速
    
    print("\n=== 生成结果汇总 ===")
    for r in results:
        status = "OK" if r["status"] == "OK" else f"ERROR: {r.get('error','')}"
        print(f"  {r['id']}: {status}")
    
    # 保存 manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest 保存到: {manifest_path}")

if __name__ == "__main__":
    main()
```

**运行方式**：

```bash
# 设置 API Key（fal.ai 账号）
set VOLC_SEEDREAM_API_KEY=your-fal-api-key

# 运行
python D:\Dev\ai-wechat-pipeline\reports\claude_style_cover_test.py
```

> 如果使用火山引擎原生 API（而非 fal.ai），需修改 `API_URL` 为：
> `https://ark.cn-beijing.volces.com/api/v3/images/generations`
> 并调整 `HEADERS["Authorization"]` 为 `Bearer {VOLC_API_KEY}` 格式。

---

## 附录：调研信息源清单

| 类型 | URL | 用途 |
|------|-----|------|
| 官方设计系统 | https://styles.refero.design/style/d469cba4-c448-4a43-a033-883f8bfcdc42 | Anthropic 完整 token |
| 设计家族分类 | https://github.com/rohitg00/awesome-claude-design | warm editorial 定义 |
| baoyu 工具源码 | https://github.com/JimLiu/baoyu-skills | cover-image skill |
| baoyu X（已知颜色）| https://x.com/dotey/status/2047493663580659734 | `#F5F0E8` 实证 |
| baoyu X（已知参数）| https://x.com/dotey/status/2019877291044553120 | warm-flat 参数实证 |
| Seedream 指南 | https://blog.fal.ai/seedream-5-0-lite-prompting-guide/ | prompt 结构 |
| Seedream 指南 | https://replicate.com/blog/how-to-prompt-seedream-5 | 技术细节 |
| Claude 品牌色 | https://www.brandcolorcode.com/claude | Peach `#DE7356` |
| Claude 主题色 | https://www.shadcn.io/theme/claude | oklch 值确认 |
| 前端美学指南 | https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics | 反 AI slop 规范 |
