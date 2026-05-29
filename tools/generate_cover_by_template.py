"""
generate_cover_by_template.py — fengyun-publish Step 7 封面生成器
(v3 — 2026-05-22 Phase 7 升级:5 → 7 模板 + 英文加固 + retry)

输入:
  --draft <draft.md>                            必需
  --research <research.md>                      可选,默认按 draft 推断
  --out <cover.png>                             可选,默认按 draft 推断
  --template T1|T2|T3|T4|T5|T6|T7               可选,默认自动分类路由
  --title <str>                                 可选,默认从 draft frontmatter 提取
  --subtitle <str>                              可选,默认从 draft digest 提取
  --seed <int>                                  可选,默认随机
  --candidates N                                可选,生成 N 张(默认 1)
  --aspect 2.35:1|16:9                          可选,默认按模板

风格(Phase 6 锁定 + Phase 7 增量):
  baoyu-style sketch-notes — 手绘叙事插画 + 卡通人物 + 中文标题嵌入图中 + 场景饱满
  暖米底 #F8F0E0 + 陶土橙 #D97757 + 黄高亮 + 橄榄绿点缀
  风云签名:左上角 small floating cloud labeled「云」

模板覆盖(Phase 7):
  T1_agent           agent / 智能体网络
  T2_research        深度研究(可选 conversation 变体:对话访谈场景)
  T3_compare         产品对比
  T4_news            发布动态
  T5_method          方法论 / 框架(default fallback)
  T6_portrait_concept  人物深度访谈/专访(半身肖像 + 概念背景)— Phase 7 新增
  T7_flow_narrative    事件叙事 / 流程梳理(信息流程图)— Phase 7 新增

英文加固(Phase 7 followup):
  - prompt 标题重复 5 次(原 3 次)
  - 英文专名逐字符 spelling 列举
  - sans-serif brand 字体暗示(让模型把英文走标题字层不走 sketch 层)
  - retry × 2(单张失败换 seed 重跑)
  - 兜底:风云草稿箱审稿,不做 OCR(避免 pip 大包)

降级链:
  1. 豆包 Seedream(火山引擎方舟)— 主力 + retry × 2
  2. terminal warn 让风云手工指定 --template 或 --seed 重跑
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
load_dotenv(ROOT / ".env")

ARK_KEY = os.environ.get("VOLCENGINE_IMAGE_KEY")
ARK_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL = "doubao-seedream-5-0-260128"

# ===== 7 模板分类规则(Phase 7 扩展) =====

CATEGORY_RULES = {
    "T1_agent":           ["agent", "智能体", "多智能体", "协作", "workflow", "mcp", "orchestrat", "harness"],
    "T2_research":        ["调研", "评测", "深度", "解析", "拆解", "报告", "论文", "分析", "实测"],
    "T3_compare":         ["vs", "对比", "横评", "测评", "哪个好", "选择", "选型"],
    "T4_news":            ["发布", "上线", "宣布", "更新", "新版", "新功能", "重磅", "开源",
                            # Bug 5 修复 2026-05-24:补财经/行业大事件 keyword
                            "融资", "估值", "反超", "收购", "IPO", "上市", "烧钱",
                            "万亿", "千亿", "百亿", "投资", "领投",
                            # Round 19 P0-4 (2026-05-25):补安全/危机事件 keyword
                            # 实测 TrapDoor 文当前路由 T7,改后应路由 T4(announcement metaphor)
                            "攻击", "漏洞", "突发", "曝光", "泄露", "入侵",
                            "供应链攻击", "0day", "CVE", "RCE", "事故",
                            "宕机", "断供", "禁令", "处罚"],
    "T5_method":          ["方法", "框架", "系统", "思考", "哲学", "反思", "本质", "理解", "是什么", "为什么"],
    "T6_portrait_concept":["专访", "对话", "访谈", "首次", "独家", "speaker", "cpo", "ceo", "cto",
                           "创始人", "讲完整", "讲清楚", "讲透", "amodei", "altman", "hassabis", "brockman",
                           "fridman", "lex", "huang", "黄仁勋", "马斯克", "musk"],
    # Bug 3 修复(2026-05-25 Round 17 · WRITE_AGENT.md v1.0):
    #   原版含「事件」纯字面词 → 任何带「事件」的新闻(融资事件 / 发布事件)
    #   会以 1:0 分压过 T4_news,误路由到 T7。
    #   T7 语义核心是「流程梳理 / 时间线 / 完整事件复盘」,
    #   单字「事件」无法区分,改为更精确的词组(「事件始末」「宫斗事件」)。
    "T7_flow_narrative":  ["流程", "时间线", "宫斗", "事件始末", "宫斗事件", "全过程",
                           "复盘", "始末", "来龙去脉",
                           "演化", "进化", "演进", "成长史",
                           "从0到", "从 0 到", "故事", "如何走到", "怎样炼成"],
}
DEFAULT_TEMPLATE = "T5_method"

# ===== 7 模板 prompt(Phase 7 升级:5→7,英文加固) =====
# 占位符:{TITLE} = 文章标题(≤ 14 字),{SUBTITLE} = 副标题(≤ 22 字)
#
# 英文加固机制(Phase 7):
#   1. 标题在 prompt 里出现 5 次(场景描述 / RIGHT 区 / MUST read / repeat-1 / repeat-2)
#   2. 英文专名暗示走 sans-serif 标题字层,不走 sketch wobble 层
#   3. 显式 "DO NOT misspell" + 字符级精确指令
#   4. AVOID 列表里加 "letter dropout, letter substitution, typo"

TEMPLATES = {
    "T1_agent": {
        "aspect": "2.35:1",
        "size": "2K",
        "prompt": (
            "Aspect 2.35:1, hand-drawn sketchnote WeChat cover. "
            "Style: warm cream #F8F0E0 paper grain background, terracotta #D97757 primary line color, "
            "hand-drawn wobble strokes, slight paper texture, rich detailed sketchnote illustration. "
            "NO HUMAN FIGURE. NO cartoon person. The metaphor is the AGENT NETWORK ITSELF as the visual subject. "
            "LEFT 60%: a richly detailed hand-drawn multi-agent network diagram — "
            "10-14 nodes scattered across the canvas, each node a small distinct icon with hand-lettered Chinese label "
            "(工具 / 记忆 / 上下文 / 运行时 / 验证 / 规划 / 推理 / 检索 / 执行 / 反思 / 评估), "
            "connected with a dense web of dashed and solid arrowed lines suggesting orchestration flow. "
            "Central LARGE glowing terracotta brain or core symbol labeled 「大模型」, with radiating connections to nodes. "
            "Decorative sketchnote flourishes: small gears, plants, sparkles, hand-drawn arrows curving between clusters, "
            "small ink-wash callout boxes annotating 2-3 nodes. "
            "Small floating cloud icon labeled 「云」 in top-left corner (signature). "
            "RIGHT 40%: title 「{TITLE}」 in thick brush stroke calligraphy for Chinese characters AND clean bold sans-serif type for any English/Latin words, "
            "yellow #F6AD55 highlighter marker swipe behind one keyword. "
            "Below title in a hand-drawn dashed rectangle frame with corner stars: subtitle 「{SUBTITLE}」. "
            "CRITICAL TEXT RENDERING — DO NOT MISSPELL: "
            "The exact title text is: 「{TITLE}」 — render every character precisely and legibly, no letter substitution, no letter dropout. "
            "The exact subtitle text is: 「{SUBTITLE}」 — render every character precisely and legibly. "
            "If the title contains English brand names, render them as crisp sans-serif type, NOT as hand-drawn wobble letters. "
            "Repeat for emphasis — title: 「{TITLE}」. Subtitle: 「{SUBTITLE}」. "
            "Final spelling check — title MUST read: 「{TITLE}」. "
            "AVOID: letter dropout, letter substitution, misspelling, fake-looking words, "
            "ANY human figure or cartoon character (network IS the subject), "
            "flat-vector minimalism, abstract blue, neural-net cliché, photorealism. "
            "Mood: intellectual warmth, orchestration of intelligence, baoyu sketchnote style."
        ),
    },
    "T2_research": {
        "aspect": "16:9",
        "size": "2K",
        "prompt": (
            "Aspect 16:9, hand-drawn sketchnote WeChat cover. "
            "Style: warm cream #F8F0E0 paper grain background, terracotta #D97757 + olive #788C5D accents, "
            "hand-drawn wobble strokes, rich detailed sketchnote dissection illustration. "
            "NO HUMAN FIGURE. NO cartoon character at a desk. The metaphor is the RESEARCH DISSECTION ITSELF. "
            "LEFT 55%: a large hand-drawn cross-section / dissection diagram of the research subject — "
            "either a stylized cutaway view of a chip / brain / system, OR an anatomical-style exploded diagram, "
            "with peeled-back layers exposing inner structure. "
            "Multiple labeled callout arrows pointing to specific parts with hand-lettered Chinese annotations "
            "(架构 / 原理 / 数据 / 训练 / 推理 / 输入 / 输出 / 关键). "
            "A large terracotta magnifying glass hovering over one zoomed-in detail in the diagram, "
            "showing 2-3x magnified inner pattern. "
            "Supporting elements scattered around: 3-4 small bar/line chart sketches, a stack of annotated paper notes "
            "with hand-drawn equations or pseudo-code snippets, an open notebook with bullet-point findings, "
            "small ink-wash insight bulb above the magnifier. "
            "Small floating cloud icon labeled 「云」 in top-left corner (signature). "
            "RIGHT 45%: title 「{TITLE}」 in thick brush stroke calligraphy for Chinese AND clean bold sans-serif type for English/Latin words, "
            "yellow #F6AD55 highlighter swipe behind one keyword. "
            "Subtitle in a hand-drawn dashed rectangle frame: 「{SUBTITLE}」. "
            "CRITICAL TEXT RENDERING — DO NOT MISSPELL: "
            "The exact title text is: 「{TITLE}」 — render every character precisely and legibly, no letter substitution, no letter dropout. "
            "The exact subtitle text is: 「{SUBTITLE}」 — render every character precisely and legibly. "
            "If the title contains English brand names, render them as crisp sans-serif type, NOT as hand-drawn wobble letters. "
            "Repeat for emphasis — title: 「{TITLE}」. Subtitle: 「{SUBTITLE}」. "
            "Final spelling check — title MUST read: 「{TITLE}」. "
            "AVOID: letter dropout, letter substitution, misspelling, fake-looking English words, "
            "ANY human figure or cartoon character (dissection IS the subject), "
            "empty whitespace, flat-vector single book icon, photorealism. "
            "Mood: deep dissection, peeling open the unknown, baoyu sketchnote warmth."
        ),
    },
    "T3_compare": {
        "aspect": "16:9",
        "size": "2K",
        "prompt": (
            "Aspect 16:9, hand-drawn sketchnote WeChat cover. "
            "Style: warm cream #F8F0E0 paper grain, terracotta #D97757 + olive green #788C5D accents, "
            "hand-drawn wobble strokes. "
            "NO HUMAN FIGURE. NO cartoon character pointing. The metaphor is the SIDE-BY-SIDE FACE-OFF ITSELF. "
            "LEFT 55%: 2-3 large hand-drawn product UI cards or windows arranged in a face-off composition "
            "(left-vs-right OR triangular standoff), each card detailed with a small icon, hand-lettered Chinese label, "
            "3-5 mini feature bullet points inside the card (短中文 keywords). "
            "Large central terracotta 「VS」 symbol or boxing-ring style divider between the cards, "
            "with crackling spark / collision lines around it. "
            "Above each card: small terracotta star rating (5 stars sketched in) and a hand-drawn checkmark or X "
            "marking pros / cons. Below the cards: a horizontal bar comparison chart with 3-4 metrics labeled in Chinese. "
            "Decorative confetti dots, dashed motion lines radiating from the VS center, small annotation arrows. "
            "Small floating cloud icon labeled 「云」 in top-left corner (signature). "
            "RIGHT 45%: title 「{TITLE}」 in thick brush stroke calligraphy for Chinese AND clean bold sans-serif type for English/Latin words, "
            "yellow #F6AD55 highlighter swipe behind comparison verb or key term. "
            "Subtitle in hand-drawn dashed rectangle frame: 「{SUBTITLE}」. "
            "CRITICAL TEXT RENDERING — DO NOT MISSPELL: "
            "The exact title text is: 「{TITLE}」 — render every character precisely and legibly, no letter substitution, no letter dropout. "
            "The exact subtitle text is: 「{SUBTITLE}」 — render every character precisely and legibly. "
            "If the title contains English brand names, render them as crisp sans-serif type, NOT as hand-drawn wobble letters. "
            "Repeat for emphasis — title: 「{TITLE}」. Subtitle: 「{SUBTITLE}」. "
            "Final spelling check — title MUST read: 「{TITLE}」. "
            "AVOID: letter dropout, letter substitution, misspelling, fake-looking English words, "
            "ANY human figure or cartoon character (the face-off IS the subject), "
            "flat tables, photorealistic product screenshots, sterile design. "
            "Mood: balanced comparison, objective face-off, friendly analysis."
        ),
    },
    "T4_news": {
        "aspect": "2.35:1",
        "size": "2K",
        "prompt": (
            "Aspect 2.35:1, hand-drawn sketchnote WeChat cover. "
            "Style: warm cream #F8F0E0 paper grain, terracotta #D97757 + warm orange + golden yellow #F6AD55 highlights, "
            "hand-drawn wobble strokes, dynamic scene. "
            "NO HUMAN FIGURE. NO cartoon character holding a tablet. The metaphor is the ANNOUNCEMENT EVENT ITSELF. "
            "LEFT 60%: dynamic announcement-stage composition — a large hand-drawn announcement billboard / news poster "
            "or a torn-open envelope releasing the news, prominently centered, with a glowing terracotta-orange "
            "central event symbol (a new logo placeholder, a key number badge, or a rising rocket icon). "
            "Bursting around it: fireworks, stars, sparks, exploding confetti, dashed motion lines radiating outward, "
            "small floating cloud puffs of energy rising. "
            "Supporting elements: 3-4 mini hand-drawn newspaper headline strips or speech-bubble reactions with "
            "short Chinese phrases (重磅 / 发布 / 全量 / 反超 / 突破 / 上线), a torn ticket-stub style label with the "
            "key number / amount / date hand-lettered in. A few smaller industry-logo placeholders watching from corners. "
            "Decorative ink-wash burst around the central symbol. "
            "Small floating cloud icon labeled 「云」 in top-left corner (signature). "
            "RIGHT 40%: large title 「{TITLE}」 in thick brush stroke calligraphy for Chinese AND clean bold sans-serif type for English/Latin words, "
            "yellow highlighter swipe behind number or key noun. "
            "Subtitle in hand-drawn dashed rectangle frame with corner stars: 「{SUBTITLE}」. "
            "CRITICAL TEXT RENDERING — DO NOT MISSPELL: "
            "The exact title text is: 「{TITLE}」 — render every character precisely and legibly, no letter substitution, no letter dropout. "
            "The exact subtitle text is: 「{SUBTITLE}」 — render every character precisely and legibly. "
            "If the title contains English brand names (e.g. Anthropic, OpenAI, Claude), render them as crisp sans-serif type, NOT as hand-drawn wobble letters. "
            "Repeat for emphasis — title: 「{TITLE}」. Subtitle: 「{SUBTITLE}」. "
            "Final spelling check — title MUST read: 「{TITLE}」. "
            "AVOID: letter dropout, letter substitution, misspelling, fake-looking English words like 'Antrompic' or 'Antropic', "
            "ANY human figure or cartoon character (the announcement IS the subject), "
            "photorealistic logos, neon colors, sci-fi grid background. "
            "Mood: anticipation, emergence, breakthrough news."
        ),
    },
    "T5_method": {
        "aspect": "16:9",
        "size": "2K",
        "prompt": (
            "Aspect 16:9, hand-drawn sketchnote WeChat cover. "
            "Style: warm cream #F8F0E0 paper grain background, terracotta #D97757 brush primary, "
            "hand-drawn wobble strokes with calligraphic flourish, friendly cartoon illustration. "
            "NO HUMAN FIGURE. NO cartoon character. The metaphor is the FRAMEWORK STRUCTURE ITSELF. "
            "LEFT 55%: a large detailed hand-drawn concentric-rings framework diagram filling the space — "
            "5-7 nested rings or layered hexagons / triangles, each ring with a hand-lettered Chinese layer name "
            "(底层 / 原理 / 方法 / 工具 / 应用 / 实践 / 反思), and 2-3 small icon-callouts dotted on each ring. "
            "At the center: a large glowing terracotta core symbol (book / brain / lantern / compass) labeled with "
            "the core concept in 1-3 Chinese characters. "
            "Radiating outward from the center: ink-wash light rays, sketchnote sparkles, and a few "
            "side-annotation arrows pointing to specific rings with explanatory hand-lettered notes. "
            "Decorative supporting elements: plants, stars, small geometry doodles, a hand-drawn compass-rose "
            "marker in one corner. "
            "Small floating cloud labeled 「云」 in top-left corner (风云 signature). "
            "RIGHT 45%: large title 「{TITLE}」 in thick brush stroke calligraphy for Chinese AND clean bold sans-serif type for English/Latin words, "
            "yellow #F6AD55 highlighter swipe behind key term. "
            "Subtitle in hand-drawn dashed rectangle frame: 「{SUBTITLE}」. "
            "CRITICAL TEXT RENDERING — DO NOT MISSPELL: "
            "The exact title text is: 「{TITLE}」 — render every character precisely and legibly, no letter substitution, no letter dropout. "
            "The exact subtitle text is: 「{SUBTITLE}」 — render every character precisely and legibly. "
            "If the title contains English brand names, render them as crisp sans-serif type, NOT as hand-drawn wobble letters. "
            "Repeat for emphasis — title: 「{TITLE}」. Subtitle: 「{SUBTITLE}」. "
            "Final spelling check — title MUST read: 「{TITLE}」. "
            "AVOID: letter dropout, letter substitution, misspelling, fake-looking English words, "
            "ANY human figure or cartoon character (framework structure IS the subject), "
            "empty 70%+ whitespace, single abstract cloud alone, minimalism cliché. "
            "Mood: clarity, systems thinking, calm intelligence, baoyu sketchnote warmth."
        ),
    },
    # ===== Phase 7 新增 =====
    "T6_portrait_concept": {
        "aspect": "2.35:1",
        "size": "2K",
        "prompt": (
            "Aspect 2.35:1, baoyu-style WeChat cover combining semi-vector cartoon portrait with concept scene. "
            "Style: warm cream #F8F0E0 paper grain background, terracotta #D97757 + dusty navy + warm orange accents, "
            "semi-vector clean line illustration (cleaner than hand-drawn wobble — closer to editorial cartoon), "
            "subtle paper texture overlay. "
            "LEFT 40%: a large semi-vector cartoon portrait BUST of an unnamed thoughtful figure — head and shoulders only, "
            "expressive eyes behind glasses (or without), gentle micro-expression suggesting deep thought or quiet confidence. "
            "Clean colored shapes with light cell-shading, NOT photorealistic, NOT photo, NOT realistic skin. "
            "RIGHT 60%: themed concept background — abstract circuit patterns OR architectural maze OR puzzle pieces "
            "OR scattered subject-matter icons (chess pieces / book / brain / chip), arranged loosely with terracotta lines. "
            "Title 「{TITLE}」 layered ON TOP of the concept background, in mixed typography: "
            "Chinese characters in thick brush stroke calligraphy, English/Latin words in crisp bold sans-serif. "
            "Subtitle 「{SUBTITLE}」 below the title, in a thinner brush stroke or a hand-drawn rounded badge. "
            "Optionally add 2-3 small rounded tag chips with topical Chinese labels at the bottom corner. "
            "Small floating cloud icon labeled 「云」 in top-left corner (signature). "
            "CRITICAL TEXT RENDERING — DO NOT MISSPELL: "
            "The exact title text is: 「{TITLE}」 — render every character precisely and legibly, no letter substitution, no letter dropout. "
            "The exact subtitle text is: 「{SUBTITLE}」 — render every character precisely and legibly. "
            "If the title contains English personal names or brand names (e.g. Hassabis, Anthropic, OpenAI, Amodei), "
            "render them as crisp sans-serif type, NOT as hand-drawn wobble. "
            "Repeat for emphasis — title: 「{TITLE}」. Subtitle: 「{SUBTITLE}」. "
            "Final spelling check — title MUST read: 「{TITLE}」. "
            "AVOID: letter dropout, letter substitution, misspelling, fake-looking English words like 'Antrompic' or 'Antropic', "
            "photorealistic skin, real-person photo realism, anime moe style, abstract blue futurism. "
            "Mood: editorial deep-dive interview, intellectual portrait, baoyu warmth."
        ),
    },
    "T7_flow_narrative": {
        "aspect": "2.35:1",
        "size": "2K",
        "prompt": (
            "Aspect 2.35:1, baoyu-style WeChat cover combining cartoon narrator with multi-node flow/narrative diagram. "
            "Style: warm cream #F8F0E0 paper grain background, terracotta #D97757 primary line + dusty teal + warm orange accents, "
            "semi-vector clean line illustration with friendly cartoon characters. "
            "NO HUMAN FIGURE as main subject. The metaphor is the FLOW/TIMELINE DIAGRAM ITSELF. "
            "FULL CANVAS: a rich multi-node narrative flow timeline filling 90%+ of the space — "
            "8-12 small rounded rectangle nodes (or icon cards), arranged as a horizontal-or-branching story sequence "
            "winding across the canvas, connected with arrowed lines (mix of dashed, solid, double-back loops). "
            "Each node contains a small topical icon (document / microphone / chess piece / building / logo placeholder / "
            "clock / coin / handshake / lightbulb / question-mark / flag) AND a short Chinese label (1-3 chars) below. "
            "Arrows indicate progression, branching choices, causation, and the occasional U-turn or fork. "
            "Sprinkle small accent illustrations between nodes: sparkles, question marks, exclamation marks, "
            "small ink-wash callouts highlighting 2-3 pivotal nodes (重磅 / 转折 / 关键). "
            "Add a hand-drawn time axis at the bottom with 3-4 milestone date stamps. "
            "Small floating cloud icon labeled 「云」 in top-left corner (signature). "
            "Title 「{TITLE}」 along the top in mixed typography: "
            "Chinese characters in thick brush stroke calligraphy, English/Latin words in crisp bold sans-serif. "
            "Subtitle 「{SUBTITLE}」 in a small handwritten note style below the title. "
            "CRITICAL TEXT RENDERING — DO NOT MISSPELL: "
            "The exact title text is: 「{TITLE}」 — render every character precisely and legibly, no letter substitution, no letter dropout. "
            "The exact subtitle text is: 「{SUBTITLE}」 — render every character precisely and legibly. "
            "If the title contains English personal names or brand names (e.g. Brockman, Anthropic, OpenAI), "
            "render them as crisp sans-serif type, NOT as hand-drawn wobble. "
            "Repeat for emphasis — title: 「{TITLE}」. Subtitle: 「{SUBTITLE}」. "
            "Final spelling check — title MUST read: 「{TITLE}」. "
            "AVOID: letter dropout, letter substitution, misspelling, fake-looking English words, "
            "ANY narrator cartoon figure taking up >15% canvas (timeline IS the subject), "
            "empty whitespace, flat info-graphic without character, sterile design, photorealism. "
            "Mood: narrative explainer, timeline storytelling, baoyu warmth, 'let me tell you what happened'."
        ),
    },
}


# ===== 工具函数 =====

def classify(text):
    text_lower = text.lower()
    scores = {tid: 0 for tid in CATEGORY_RULES}
    for tid, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                scores[tid] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return DEFAULT_TEMPLATE
    return best


def read_routing_text(draft_path, research_path):
    """优先研究材料前 400 字,fallback 草稿前 500 字"""
    if research_path and research_path.exists():
        text = research_path.read_text(encoding="utf-8")
        return text[:400]
    if draft_path.exists():
        text = draft_path.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                text = parts[2]
        return text[:500]
    return ""


def extract_title_subtitle(draft_path):
    """从 draft frontmatter 抽 title / digest 作为副标。
    标题 ≤ 12 字截断,副标 ≤ 18 字截断(Seedream 渲染稳定性)。
    """
    text = draft_path.read_text(encoding="utf-8")
    title = ""
    digest = ""

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            for line in fm.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "title" and not title:
                        title = v
                    elif k == "digest" and not digest:
                        digest = v

    # fallback:第一个 H1
    if not title:
        m = re.search(r"^#\s+(.+)$", text, flags=re.M)
        if m:
            title = m.group(1).strip()

    # 截断
    if len(title) > 14:
        title = title[:13] + "…"
    if len(digest) > 22:
        digest = digest[:20] + "…"

    return title, digest


import random


def _call_seedream_once(template_id, out_path, title, subtitle, seed=None):
    """单次调用 Seedream API,失败直接抛异常给上层 retry。"""
    if not ARK_KEY:
        raise RuntimeError("VOLCENGINE_IMAGE_KEY 未在 .env 配置")

    tpl = TEMPLATES[template_id]
    prompt = tpl["prompt"].replace("{TITLE}", title).replace("{SUBTITLE}", subtitle)

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "size": tpl["size"],
        "response_format": "url",
        "watermark": False,
    }
    if seed is not None:
        payload["seed"] = int(seed)

    headers = {
        "Authorization": f"Bearer {ARK_KEY}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        ARK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    t0 = time.time()
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    img_url = data["data"][0]["url"]
    resp_seed = data["data"][0].get("seed")
    elapsed = time.time() - t0

    urllib.request.urlretrieve(img_url, str(out_path))
    return {"seed": resp_seed, "elapsed": elapsed, "url": img_url}


def generate_image(template_id, out_path, title, subtitle, seed=None, max_retries=2):
    """调火山引擎方舟生图,失败 retry,换 seed。

    Phase 7 加固:
      - retry × max_retries(默认 2,总尝试 3 次)
      - 每次 retry 换随机 seed
      - 全失败时返回 ok=False + last_error,但不 crash 工作流
      - 返回 dict 里 attempts 记录每次尝试
    """
    tpl = TEMPLATES[template_id]
    print(f"[{template_id}] 调豆包 Seedream API (seed={seed or 'random'}, aspect={tpl['aspect']})", flush=True)
    print(f"  title='{title}'", flush=True)
    print(f"  subtitle='{subtitle}'", flush=True)

    attempts = []
    last_error = None
    current_seed = seed

    for attempt_idx in range(max_retries + 1):
        try:
            r = _call_seedream_once(template_id, out_path, title, subtitle, seed=current_seed)
            print(f"[{template_id}] OK (attempt {attempt_idx+1}, {r['elapsed']:.1f}s, seed={r['seed']})", flush=True)
            attempts.append({"attempt": attempt_idx + 1, "ok": True, "seed": r["seed"]})
            print(f"[{template_id}] ✓ {out_path.name}", flush=True)
            return {"ok": True, "template": template_id, "seed": r["seed"], "path": str(out_path),
                    "title": title, "subtitle": subtitle, "attempts": attempts}
        except Exception as e:
            last_error = str(e)
            attempts.append({"attempt": attempt_idx + 1, "ok": False, "error": last_error,
                             "seed": current_seed})
            print(f"[{template_id}] ✗ attempt {attempt_idx+1} 失败: {last_error}", flush=True)
            if attempt_idx < max_retries:
                # 换 seed
                current_seed = random.randint(1, 2**31 - 1)
                print(f"[{template_id}] ↻ retry,新 seed={current_seed}", flush=True)
                time.sleep(2)  # 短暂等避免 rate limit

    # 全失败
    print(f"[{template_id}] ❌ 全部 {max_retries+1} 次失败", flush=True)
    print(f"  最后错误: {last_error}", flush=True)
    print(f"  建议:风云手工指定 --template {template_id} --seed <新seed> 重跑;", flush=True)
    print(f"        或换模板 --template T1|T2|T3|T4|T5|T6|T7", flush=True)
    return {"ok": False, "template": template_id, "seed": None, "path": None,
            "title": title, "subtitle": subtitle, "attempts": attempts,
            "last_error": last_error}


def generate_candidates(template_id, out_base, title, subtitle, n=1, seed=None):
    """生成 N 张候选,并行 seed 不同。返回 result list。

    Phase 7 新增:让风云挑文字最准的一张。
    """
    results = []
    for i in range(n):
        candidate_seed = seed if (seed and n == 1) else random.randint(1, 2**31 - 1)
        if n == 1:
            out_path = out_base
        else:
            stem = out_base.stem
            out_path = out_base.with_name(f"{stem}_c{i+1}{out_base.suffix}")
        print(f"\n=== candidate {i+1}/{n} ===")
        r = generate_image(template_id, out_path, title, subtitle, seed=candidate_seed)
        results.append(r)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", required=True, help="markdown draft 路径")
    parser.add_argument("--research", default=None, help="研究材料路径(可选)")
    parser.add_argument("--out", default=None, help="输出 PNG 路径(可选)")
    parser.add_argument("--template", choices=list(TEMPLATES.keys()), default=None,
                        help="手动指定模板,不指定则自动路由")
    parser.add_argument("--title", default=None,
                        help="标题(≤ 12 字),默认从 frontmatter title 抽")
    parser.add_argument("--subtitle", default=None,
                        help="副标(≤ 18 字),默认从 frontmatter digest 抽")
    parser.add_argument("--seed", type=int, default=None, help="指定 seed,不指定则随机")
    parser.add_argument("--candidates", type=int, default=1,
                        help="生成 N 张候选(seed 不同),让用户挑文字最准的一张(Phase 7 新增)")
    parser.add_argument("--max-retries", type=int, default=2,
                        help="单张失败时 retry 次数(默认 2,即总尝试 3 次)")
    parser.add_argument("--skip-dedup", action="store_true",
                        help="跳过 7 天回看 cover dedup gate(默认开启 dedup)")
    args = parser.parse_args()

    draft_path = Path(args.draft)
    if not draft_path.exists():
        print(f"❌ draft 不存在: {draft_path}")
        sys.exit(1)

    # 决定 research
    research_path = Path(args.research) if args.research else None
    if research_path is None:
        stem = draft_path.stem
        candidate = ROOT / "output" / "research" / f"{stem}.md"
        if candidate.exists():
            research_path = candidate

    # 决定 out
    if args.out:
        out_path = Path(args.out)
    else:
        stem = draft_path.stem
        out_path = ROOT / "output" / "images" / f"{stem}-cover.png"
    out_path.parent.mkdir(exist_ok=True, parents=True)

    # 路由
    if args.template:
        template_id = args.template
        print(f"手动指定模板: {template_id}")
    else:
        text = read_routing_text(draft_path, research_path)
        template_id = classify(text)
        print(f"自动路由命中: {template_id}")

    # Round 15 · cover dedup gate(7 天回看,跟最近撞型则换次优)
    if not args.skip_dedup and not args.template:
        try:
            from cover_dedup import check_cover_template_overlap
            text_for_dedup = read_routing_text(draft_path, research_path)
            dedup_result = check_cover_template_overlap(
                new_template_id=template_id,
                new_draft_text=text_for_dedup,
                max_age_days=7,
                # Bug 4 修复(2026-05-25 Round 17):传当前 draft 排除自身
                # 否则正在 ship 的 draft 自己也进 history,导致 used_templates
                # 必然包含 new_template_id,触发误判换次优。
                current_draft_path=draft_path,
            )
            if dedup_result["is_too_similar"]:
                print(f"⚠️  cover dedup 命中撞型: {dedup_result['redo_feedback']}")
                template_id = dedup_result["alternative_template"]
                print(f"🔀 换次优模板: {template_id}")
            else:
                print(f"✅ cover dedup 通过: {dedup_result['redo_feedback']}")
        except Exception as e:
            print(f"⚠️  cover dedup 跑挂(不阻断 ship): {e}")

    # 抽 title / subtitle
    if args.title and args.subtitle:
        title, subtitle = args.title, args.subtitle
    else:
        title_fm, subtitle_fm = extract_title_subtitle(draft_path)
        title = args.title or title_fm
        subtitle = args.subtitle or subtitle_fm

    if not title:
        print(f"⚠️  title 为空,封面可能渲染失败")
        title = "（无标题）"
    if not subtitle:
        subtitle = title  # 用 title 当 subtitle fallback

    if args.candidates > 1:
        results = generate_candidates(template_id, out_path, title, subtitle,
                                       n=args.candidates, seed=args.seed)
        print(f"\n=== 完成({args.candidates} 张候选)===")
        ok_count = sum(1 for r in results if r["ok"])
        print(f"模板: {template_id}")
        print(f"成功: {ok_count}/{args.candidates}")
        for i, r in enumerate(results, 1):
            status = "OK" if r["ok"] else "FAIL"
            print(f"  [{i}] {status} seed={r.get('seed')} path={r.get('path')}")
        if ok_count == 0:
            sys.exit(2)
    else:
        result = generate_image(template_id, out_path, title, subtitle,
                                  seed=args.seed, max_retries=args.max_retries)
        print(f"\n=== 完成 ===")
        print(f"模板: {result['template']}")
        if result["ok"]:
            print(f"Seed: {result['seed']}")
            print(f"输出: {result['path']}")
            print(f"尝试次数: {len(result['attempts'])}/{args.max_retries + 1}")
            # Round 21 决策 2:输出 cover_style_anchor 给内文图共享
            # 7 模板共享同一 sketch-notes 底色 + 陶土橙 + 云签名风格
            # 内文图(huashu-image-curator Mode 2)读这个 anchor 保证篇内一致
            cover_anchor = (
                "warm sketchnote hand-drawn, cream paper #F8F0E0, "
                "terracotta #D97757 accent line, soft cloud signature, "
                "no human face, editorial illustration"
            )
            print(f"\ncover_style_anchor: {cover_anchor}")
            # 同时写到 sidecar 文件供下游读
            try:
                anchor_path = out_path.with_suffix(".style_anchor.txt")
                anchor_path.write_text(cover_anchor, encoding="utf-8")
                print(f"style_anchor sidecar: {anchor_path}")
            except Exception as _e:
                print(f"(style_anchor sidecar 写失败,不阻断: {_e})")
        else:
            print(f"❌ 全部 retry 失败")
            print(f"  attempts: {result['attempts']}")
            print(f"  last_error: {result['last_error']}")
            sys.exit(2)


if __name__ == "__main__":
    main()
