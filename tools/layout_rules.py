"""
layout_rules.py — Musk × Jobs 沙盒辩论 2026-05-23 共识 + 风云品牌色

9 维度自动化排版规则,可直接接入 fengyun-publish Step 8 排版。

【规则出处】
- 中文眼动论文(14-16px 最优):
  https://www.researchgate.net/publication/330051180
- Pew Research 117M 移动阅读:
  https://www.pewresearch.org/journalism/2016/05/05/long-form-reading-shows-signs-of-life-in-our-mobile-news-world/
- Apple HIG Typography:
  https://developer.apple.com/design/human-interface-guidelines/typography
- WCAG 2.2 Contrast Minimum:
  https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- Light/Dark Mode Visual Fatigue:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12027292/
- 本地 PHASE1_FACTS.md + WRITING_SOP_PRIORITIES.md(Phase 1+3 实测)

【品牌色对齐(风云"研究Agent的云"封面三件套)】
- 暖象牙底 #FAF9F5(辩论原案 #FFF8F0,采品牌色)
- 陶土橙强调 #D97757(辩论原案 #FFA500,采品牌色 Anthropic 同族)
- 文本灰 #333 / strong 纯黑 #000
- 主色蓝 #1E6FFF(链接)/ CTA 红 #FF4D4D

【调用方式】
  from tools.layout_rules import render_to_wechat_html, lint
  html = render_to_wechat_html(markdown_text, section_image_urls=[url1, url2, ...])
  issues = lint(html)
"""
from __future__ import annotations

import re
from typing import List, Optional


# ============================================================
# LAYOUT_RULES — 9 维度全规则常量
# ============================================================
LAYOUT_RULES = {
    "image_strategy": {
        "words_per_image": 1100,         # 每 1100 字 1 张(目标值)
        "tolerance": 100,                 # ±100 字容差
        "hero_image": True,               # 首图必须(钩子)
        "section_head_image": True,       # 每个 H2 章节首
        "caption_allowed": False,         # 禁图注(微信压缩成噪音)
        "img_style": ("max-width:100%;width:100%;height:auto;display:block;"
                      "border-radius:6px;"),
        "source": "本地 PHASE1_FACTS.md L209 + Musk#3 Idiot Index(每 1000-1200 字 1 张为物理最优)",
    },
    "font": {
        "body_px": 15,                    # 中文眼动 14-16 + 微信 14-17 交集
        "body_color": "#333",             # WCAG AA + 暗黑模式可见
        "body_weight": "normal",
        "letter_spacing": "0.3px",        # 中文字间气口
        "h2_px": 20,
        "h2_color": "#222",
        "h2_weight": "bold",
        "h2_tag": "p",                    # 不用 h1-6,防微信覆盖字号
        "quote_px": 14,                   # 降一档制造层级
        "quote_color": "#666",
        "strong_color": "#000",           # 纯黑制造重点反差
        "font_family": None,              # 不设,让系统接管(Jobs 让字体消失)
        "source": "Musk#1 中文眼动 14-16px + Jobs#1 Apple HIG",
    },
    "color": {
        "bg": "#FFFFFF",                  # 纯白(灰底反色后会失明)
        "primary": "#6A9BCC",             # 链接 / 章节标识(Anthropic 实际蓝,Round 5 P1 共识)
        "accent_bg": "#FAF9F5",           # 引用块底(风云品牌)
        "accent_border": "#D97757",       # 引用块边 + H2 边(风云品牌,Anthropic 同族)
        "cta": "#FF4D4D",                 # CTA 按钮
        "max_non_gray_colors": 4,         # 封顶
        "source": "Jobs#3 WCAG + 风云封面三件套品牌锁定",
    },
    "line_height": {
        "body": 1.75,                     # 中文方块字密度 +25-30%
        "quote": 1.7,                     # 引用块稍紧凑
        "h2": 1.4,
        "source": "中文方块字 +25-30% over Apple 1.36 + 本地 Phase 3-1 实测",
    },
    "paragraph": {
        "avg_chars_range": (80, 150),     # 平均段长目标
        "max_chars": 200,                  # 超即自动拆
        "margin_bottom_px": 20,            # 显式覆盖微信默认 24pt
        "punchy_interval": (3, 5),         # 每 3-5 段插 1 个短段
        "punchy_chars_range": (20, 40),
        "source": "Musk#2 Pew 117M reads + Jobs 删减测试",
    },
    "divider": {
        "use_hr": False,                   # 禁 <hr>(微信渲染丑)
        "marker": "· · ·",                 # 三点居中
        "marker_color": "#ccc",            # 装饰性灰(#ccc 在分割线允许)
        "margin_y_px": 32,
        "count_range": (3, 5),             # 全文 3-5 个(对应 3-5 章节)
        "source": "物理约束(微信 hr 渲染丑)",
    },
    "callout": {
        "count_range": (2, 4),             # 每篇 2-4 个引用块
        "max_chars": 60,                   # 超 60 字说明不是金句
        "cta_in_body": False,              # CTA 不在正文中段
        "source": "Jobs#2 情感锚点",
    },
    "intro": {
        "first_para_max_chars": 80,        # 首段 ≤ 80 字(易入口)
        "value_promise_within_chars": 100, # 100 字内出现价值承诺
        "hook_image_within_chars": 200,    # 200 字内首图
        "ban_phrases": [
            "大家好", "今天聊聊", "话说", "今天来聊",
            "朋友们", "各位朋友", "今天我们来",
        ],
        "duplicate_title": False,          # 禁正文重复标题
        "source": "本地 SOP + Jobs#1 Apple ≤12 词首句",
    },
    "ending": {
        "summary_chars_range": (80, 120),
        "cta_count": 1,                    # 1 个具体问题 CTA
        "cta_must_be_question": True,
        "signature_required": True,
        "ban_phrases": [
            "感谢阅读", "点赞收藏", "往期回顾", "感谢支持",
            "求点赞", "求转发", "求关注",
        ],
        "source": "Jobs 删减测试 + Apple 风格 CTA",
    },
}


# ============================================================
# Round 21 决策 1.2:default-only 派生样式 / signature 已砍
# huashu 走自己的 _huashu_* 系列(见下方),不依赖这些
# ============================================================


# ============================================================
# Markdown inline 元素处理
# ============================================================

INLINE_IMG_PAT = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
BOLD_PAT = re.compile(r"\*\*([^*\n]+)\*\*")
ITALIC_PAT = re.compile(r"(?<![\*])\*([^*\n]+)\*(?!\*)")
CODE_PAT = re.compile(r"`([^`\n]+)`")
LINK_PAT = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


# ============================================================
# CJK 中英文混排预处理(2026-05-24 接入)
# source: xiaohuailabs/xiaohu-wechat-format (MIT)
# original: scripts/format.py:232-282
# ported 2026-05-24 — 渲染前对原始 markdown 做两步规整,
# default 与 huashu 分支共享(在 render_to_wechat_html 入口统一调用)
# ============================================================

def _fix_cjk_spacing(text: str) -> str:
    """中英文/中数字之间自动加空格(跳过代码块、行内代码、URL、链接).

    source: xiaohu-wechat-format format.py:232-268 (MIT)
    """
    lines = text.split("\n")
    result = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            result.append(line)
            continue
        if in_code_block:
            result.append(line)
            continue

        # 保护不应修改的片段
        protected: List[str] = []

        def _protect(m):
            protected.append(m.group(0))
            return f"\x00P{len(protected) - 1}\x00"

        line = re.sub(r"`[^`]+`", _protect, line)              # 行内代码
        line = re.sub(r"https?://\S+", _protect, line)         # URL
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", _protect, line) # 图片
        line = re.sub(r"\[[^\]]*\]\([^)]*\)", _protect, line)  # 链接

        cjk = r"[一-鿿㐀-䶿豈-﫿]"
        latin = r"[a-zA-Z0-9]"
        line = re.sub(f"({cjk})({latin})", r"\1 \2", line)
        line = re.sub(f"({latin})({cjk})", r"\1 \2", line)

        for i, p in enumerate(protected):
            line = line.replace(f"\x00P{i}\x00", p)
        result.append(line)

    return "\n".join(result)


def _fix_cjk_bold_punctuation(text: str) -> str:
    """把中文标点移到加粗/斜体标记外面.

    **文字,** → **文字**,        (末尾标点踢出)
    **,文字** → ,**文字**        (开头标点踢出,Bug 1 修复 2026-05-24)
    *文字。*  → *文字*。

    source: xiaohu-wechat-format format.py:271-282 (MIT)
    Bug 1 修复 2026-05-24:加开头标点踢出,handoff 提到的「:**xxx**」边界 case
    """
    # Round 23 Bug 1 修(2026-05-25):开头 / 末尾用不同 punct 字符集,避免连续 bold 误判
    # 末尾踢出可以激进(全角 + ASCII 全套)— 不会跨 bold 误匹配,因 `[^*]+?` 拒绝跨 `*`
    # 开头踢出必须保守(全角 + ASCII `"` `'` `:` 这种「真正能开头」的)—
    #   排除 ASCII `,` `.` `!` `?`(逗号开头是病句,且会让 `**A**,**B**` 的 `,**B**` 误判成「,开头 bold」)
    cjk_punct_end = (
        r"[，。！？、；：“”‘’（）【】《》…—"  # 原全角
        r'":\,.!?\''                              # ASCII 全套(末尾踢出安全)
        r"]"
    )
    cjk_punct_start = (
        r"[，。！？、；：“”‘’（）【】《》…—"  # 原全角
        r'":\''                                    # 只 ASCII 引号 + 冒号(开头保守)
        r"]"
    )
    # === 末尾标点踢出(激进集合)===
    # **text+标点** → **text**+标点
    text = re.sub(rf"\*\*([^*]+?)({cjk_punct_end}+)\*\*", r"**\1**\2", text)
    # *text+标点* → *text*+标点(不匹配 **)
    text = re.sub(
        rf"(?<!\*)\*(?!\*)([^*]+?)({cjk_punct_end}+)\*(?!\*)",
        r"*\1*\2",
        text,
    )
    # === 开头标点踢出(保守集合 + lookbehind)===
    # Round 23 (2026-05-25):lookbehind (?<!\*) 防止上个 bold 闭合 `**` 后接的标点
    #   误当成下个 bold 的开头标点。但 lookbehind 只防 `*` 紧邻 case,
    #   保守集合是真正的 root cause 防御。
    # **标点+text** → 标点+**text**
    text = re.sub(rf"(?<!\*)\*\*({cjk_punct_start}+)([^*]+?)\*\*", r"\1**\2**", text)
    # *标点+text* → 标点+*text*(不匹配 **)
    text = re.sub(
        rf"(?<!\*)\*(?!\*)({cjk_punct_start}+)([^*]+?)\*(?!\*)",
        r"\1*\2*",
        text,
    )
    return text


def _preprocess_cjk(markdown: str) -> str:
    """中英文混排空格 + 加粗标点位置修正.

    2026-05-24 抄自 xiaohu-wechat-format(MIT). 在 render_to_wechat_html
    入口、style 分支之前调用,default 和 huashu 都受益.
    """
    markdown = _fix_cjk_spacing(markdown)
    markdown = _fix_cjk_bold_punctuation(markdown)
    return markdown


def _render_inline(text: str) -> str:
    """markdown inline → HTML inline"""
    f = LAYOUT_RULES["font"]
    c = LAYOUT_RULES["color"]

    # 链接(必须先处理,避免与图片正则冲突 — 已用 negative lookbehind 排除 !)
    text = LINK_PAT.sub(
        lambda m: (f'<a href="{m.group(2)}" '
                   f'style="color:{c["primary"]};text-decoration:none;">'
                   f'{m.group(1)}</a>'),
        text,
    )
    # 加粗(strong 用纯黑)
    text = BOLD_PAT.sub(
        lambda m: (f'<strong style="color:{f["strong_color"]};'
                   f'font-weight:bold;">{m.group(1)}</strong>'),
        text,
    )
    # 斜体(轻量,不强加色)
    text = ITALIC_PAT.sub(lambda m: f'<em>{m.group(1)}</em>', text)
    # 内联代码
    text = CODE_PAT.sub(
        lambda m: (f'<code style="background:{c["accent_bg"]};'
                   f'color:{c["accent_border"]};padding:2px 6px;'
                   f'border-radius:4px;font-size:13px;'
                   f'font-family:Consolas,Monaco,monospace;">'
                   f'{m.group(1)}</code>'),
        text,
    )
    return text


# ============================================================
# Round 21 决策 1.2:default-only 处理函数已砍
# _split_long_paragraph / _strip_banned_intro / _wrap_p / _wrap_h2 /
# _wrap_quote / _wrap_img / _process_paragraph
# huashu 走自己的 _huashu_* 系列(见下方),不依赖这些
# ============================================================


# ============================================================
# 主渲染函数
# ============================================================

def _resolve_padded_urls(
    section_image_urls: Optional[List[str]],
    image_at_h2_indices: Optional[List[int]],
) -> List[Optional[str]]:
    """Bug 2 修复 2026-05-24:把花叔指定的 slot 位置 + urls 配对成 padded list.

    slot 编号约定:
      0 = intro hero(首段后)
      1 = H2[0] 章节首图
      2 = H2[1] 章节首图
      ...

    Args:
        section_image_urls: 图片 URL 列表(顺序对应 image_at_h2_indices)
        image_at_h2_indices: 花叔指定的 slot 列表(如 [0, 3, 4])

    Return:
        padded list,长度 = max(indices) + 1,
        命中 slot 位置是 url 字符串,非命中位置是 None
        如果 image_at_h2_indices 为 None,返回原 urls(向后兼容)

    Examples:
        urls=["a","b","c"], indices=[0,3,5] → ["a",None,None,"b",None,"c"]
        urls=["a","b"], indices=None       → ["a","b"](老行为)
    """
    section_image_urls = section_image_urls or []
    if image_at_h2_indices is None:
        return list(section_image_urls)
    if not image_at_h2_indices:
        return []
    image_by_slot: dict[int, str] = {}
    for img_pos, slot in enumerate(image_at_h2_indices):
        if img_pos < len(section_image_urls):
            image_by_slot[slot] = section_image_urls[img_pos]
    if not image_by_slot:
        return []
    max_slot = max(image_by_slot.keys())
    return [image_by_slot.get(i) for i in range(max_slot + 1)]


def render_to_wechat_html(
    markdown: str,
    section_image_urls: Optional[List[str]] = None,
    signature_html: Optional[str] = None,
    strip_frontmatter: bool = True,
    *,
    style: Optional[str] = "huashu",
    theme: str = "A",
    article_type: str = "thought_essay",
    image_at_h2_indices: Optional[List[int]] = None,
) -> str:
    """
    把 markdown 渲染为微信公众号 inline-style HTML.

    Args:
        markdown: 输入 markdown 全文(含 frontmatter)
        section_image_urls: 图片 URL 列表(必须是 mmbiz.qpic.cn 来源)
            - 默认行为(image_at_h2_indices=None):第 0 张作 hero,后续按 H2 顺序
            - 指定 image_at_h2_indices 时:严格按 slot 编号插
        signature_html: 自定义结尾签名 HTML;None 用默认风云签名
        strip_frontmatter: 是否剥除顶部 frontmatter(默认 True)
        style: 排版风格,**默认 "huashu"**(2026-05-24 主力切 huashu)
            - "huashu" / None(兼容旧 caller) → 花叔风格(默认)
            - "default" / "classic" → 原蓝灰风格(回退用)
        theme: huashu 模板 "A"(暖橙默认)或 "B"(深红专题);仅 style=huashu 生效
        article_type: huashu 文章类型,"tech_demo" 或 "thought_essay";仅 style=huashu 生效
        image_at_h2_indices: Bug 2 修复 2026-05-24:花叔指定的图位置列表
            - None(默认) → 老行为:hero + 连续 H2 顺序
            - list[int] → 严格指定 slot:0=intro hero,1=H2[0],2=H2[1]...

    Returns:
        微信公众号 inline-style HTML 字符串
    """
    # CJK 预处理(2026-05-24 接入,style 分支前先跑)
    # 中英文混排自动加空格 + `**xxx,**` 标点位置修正
    markdown = _preprocess_cjk(markdown)

    # Round 21 决策 1.2:default / classic 分支已砍,排版统一走 huashu
    # style 参数保留只为向后兼容旧 caller,任何值都路由到 huashu
    if style not in (None, "huashu"):
        print(f"⚠️  [layout_rules] style={style!r} 已废弃(Round 21 砍 default/classic),"
              f"强制走 huashu")
    return _render_huashu(
        markdown,
        section_image_urls=section_image_urls,
        signature_html=signature_html,
        strip_frontmatter=strip_frontmatter,
        theme=theme,
        article_type=article_type,
        image_at_h2_indices=image_at_h2_indices,
    )


# ============================================================
# 花叔(赛博禅心)风格分支 — style: huashu
# 配置外置在 layout_rules_huashu.yaml
# ============================================================

_HUASHU_RULES_CACHE = None


def _load_huashu_rules() -> dict:
    """Load huashu rules from layout_rules_huashu.yaml. Cached after first load."""
    global _HUASHU_RULES_CACHE
    if _HUASHU_RULES_CACHE is not None:
        return _HUASHU_RULES_CACHE
    import yaml  # 延迟 import,避免对未启用 huashu 的流程引入硬依赖
    from pathlib import Path
    yaml_path = Path(__file__).parent / "layout_rules_huashu.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        _HUASHU_RULES_CACHE = yaml.safe_load(f)
    return _HUASHU_RULES_CACHE


def _huashu_template(theme: str) -> dict:
    """按 theme 取 template_A/template_B,缺失则回落 A."""
    rules = _load_huashu_rules()
    if theme == "B" and "template_B" in rules:
        return rules["template_B"]
    return rules.get("template_A", {})


# ------------------------------------------------------------
# huashu 真品 1:1 inline-style 复刻
# 真品参考:
#   T-A: corpus/huashu_layout_reverse/公司可能是一个300年的临时实验/index.html
#   T-B: corpus/huashu_layout_reverse/微信读书出官方skill了_但它还差关键一步/index.html
# 微信编辑器特征:文字外层包 <span leaf=""> + 外层 <section data-pm-slice="0 0 []">
# ------------------------------------------------------------


def _huashu_body_paragraph_style(tpl: dict) -> str:
    """正文 <p> 的真品 inline style."""
    body = (tpl.get("typography") or {}).get("body") or {}
    fs = body.get("font_size", "17px")
    lh = body.get("line_height", "1.8 !important")
    color = body.get("color", "#2b2b2b !important")
    ls = body.get("letter_spacing")
    margin = body.get("margin", "20px 0 !important")
    parts = [
        f"margin: {margin}",
        f"line-height: {lh}",
        f"color: {color}",
        f"font-size: {fs}",
    ]
    if ls:
        parts.append(f"letter-spacing: {ls}")
    return ";".join(parts) + ";"


def _huashu_h1_style(tpl: dict) -> str:
    """T-A 章节标题 — left-border 风格(2026-05-24 用户偏好:用 default 模板的橙竖边 + 黑字,不用渐变)."""
    h1 = (tpl.get("typography") or {}).get("h1") or {}
    fs = h1.get("font_size", "20px")
    fw = h1.get("font_weight", 600)
    color = h1.get("color", "#222")
    lh = h1.get("line_height", "1.4")
    margin = h1.get("margin", "32px 0 14px 0")
    padding = h1.get("padding", "0 0 0 12px")
    border_left = h1.get("border_left", "3px solid #C15F3C")
    return (
        f"font-size: {fs};"
        f"font-weight: {fw};"
        f"color: {color};"
        f"line-height: {lh};"
        f"margin: {margin};"
        f"padding: {padding};"
        f"border-left: {border_left};"
    )


def _huashu_h2_style(tpl: dict) -> str:
    """T-B 章节标题 <h2> 真品 inline style — 白字 + 红底色块."""
    h2 = (tpl.get("typography") or {}).get("h2") or {}
    fs = h2.get("font_size", "20px")
    fw = h2.get("font_weight", 600)
    color = h2.get("color", "#fff !important")
    lh = h2.get("line_height", "1.4 !important")
    margin = h2.get("margin", "32px 0 16px")
    padding = h2.get("padding", "12px 20px")
    bg = h2.get("background_color", "#d32f2f !important")
    br = h2.get("border_radius", "4px")
    return (
        f" font-size: {fs};"
        f"font-weight: {fw};"
        f"color: {color};"
        f"line-height: {lh};"
        f"margin: {margin};"
        f"padding: {padding};"
        f"background-color: {bg};"
        f"border-radius: {br};  "
    )


def _huashu_strong_style(tpl: dict) -> str:
    """strong 真品 inline style — 主色 + 半透明同色背景胶囊."""
    s = (tpl.get("typography") or {}).get("strong") or {}
    fw = s.get("font_weight", 600)
    color = s.get("color", "#C15F3C !important")
    bg = s.get("background_color", "rgba(193, 95, 60, 0.08) !important")
    padding = s.get("padding", "2px 6px")
    br = s.get("border_radius", "3px")
    return (
        f"font-weight: {fw};"
        f"color: {color};"
        f"background-color: {bg};"
        f"padding: {padding};"
        f"border-radius: {br};"
    )


def _huashu_img_style(tpl: dict) -> str:
    """<img> 真品 inline style.

    2026-05-24 修 bug 1: 真品依赖微信 CDN 自动 resize,我们直传原图必须加 max-width 100%
    防止溢出容器(实测 v5 草稿出现图片右溢出 container 边界)。

    2026-05-24 修 bug 2: 真品 img margin: 24px auto + 外层 section margin: 20px 0,
    在微信手机端两个 margin 没 collapse → 图下方留白比图上方大(实测 v6 草稿)。
    砍掉 img 自身的上下 margin(改 0 auto),让外层 section margin: 20px 独家决定
    上下间距,保证对称。水平 auto 保留(居中)。
    """
    img = tpl.get("images") or {}
    mh = img.get("max_height", "500px !important")
    mw = img.get("max_width", "100%")
    br = img.get("border_radius", "10px")
    margin = img.get("margin", "0 auto")  # 默认砍掉上下,让 section 控制
    out = (
        f"max-width: {mw};"
        f"max-height: {mh};"
        f"height: auto;"
        f"display: block;"
        f"margin: {margin};"
        f"border-radius: {br};"
    )
    if img.get("box_shadow"):
        out += f"box-shadow: {img['box_shadow']};"
    if img.get("border"):
        out += f"border: {img['border']};"
    return out


def _huashu_quote_style(tpl: dict) -> str:
    """blockquote 样式 — 花叔几乎不用,给简洁默认即可."""
    colors = tpl.get("colors") or {}
    primary = colors.get("primary", "#C15F3C")
    bg = colors.get("background", "#faf9f7")
    text = colors.get("text_main", "#2b2b2b")
    return (
        f"margin: 20px 0;padding: 14px 18px;"
        f"border-left: 3px solid {primary};background: {bg};"
        f"color: {text};font-size: 15px;line-height: 1.7;"
    )


def _huashu_divider_html(tpl: dict) -> str:
    """分割线 — 三点居中,沿用主线规则."""
    return (
        f'<p style="text-align:center;color:#ccc;'
        f'margin:32px 0;padding:0;'
        f'font-size:14px;letter-spacing:8px;">'
        f'<span leaf="">· · ·</span></p>'
    )


def _huashu_container_style(tpl: dict) -> str:
    """最外层 section 容器 — 真品的暖米黄/白底 + 700px 容器."""
    c = tpl.get("container") or {}
    bg = c.get("background_color", "#faf9f7")
    padding = c.get("padding", "20px 24px 40px 24px")
    mw = c.get("max_width", "700px")
    margin = c.get("margin", "0 auto")
    bs = c.get("box_sizing", "border-box")
    ww = c.get("word_wrap", "break-word")
    return (
        f"background-color: {bg} !important;"
        f"padding: {padding};"
        f"max-width: {mw};"
        f"margin: {margin};"
        f"box-sizing: {bs};"
        f"word-wrap: {ww};"
    )


def _huashu_render_inline(text: str, tpl: dict) -> str:
    """huashu inline 处理 — 真品产物:文字外层包 <span leaf="">,strong 内也包."""
    strong_style = _huashu_strong_style(tpl)
    colors = tpl.get("colors") or {}
    primary = colors.get("primary", "#C15F3C")
    bg = colors.get("background", "#faf9f7")

    # 链接(链接文字也按真品包 span leaf)
    text = LINK_PAT.sub(
        lambda m: (f'<a href="{m.group(2)}" '
                   f'style="color:{primary};text-decoration:none;">'
                   f'<span leaf="">{m.group(1)}</span></a>'),
        text,
    )
    # 加粗:strong 内 <span leaf="">文字</span>
    text = BOLD_PAT.sub(
        lambda m: (f'<strong style="{strong_style}">'
                   f'<span leaf="">{m.group(1)}</span></strong>'),
        text,
    )
    # 斜体
    text = ITALIC_PAT.sub(lambda m: f'<em>{m.group(1)}</em>', text)
    # 内联代码
    text = CODE_PAT.sub(
        lambda m: (f'<code style="background:{bg};'
                   f'color:{primary};padding:2px 6px;'
                   f'border-radius:4px;font-size:13px;'
                   f'font-family:Consolas,Monaco,monospace;">'
                   f'{m.group(1)}</code>'),
        text,
    )
    return text


def _huashu_wrap_text_in_span_leaf(html_inline: str) -> str:
    """
    真品产物:<p> 内裸文字也要用 <span leaf=""> 包.
    inline 处理后 html_inline 已经把 strong/link 等包好了 — 这里把剩下的裸文字段切片包 span leaf.
    简单策略:用正则把不在 <a>/<strong>/<em>/<code> 内的裸文字段切出来包 span leaf.
    """
    # 用正则切出 inline 标签和裸文字交替
    # 已包标签:<a ...>...</a> / <strong ...>...</strong> / <em>...</em> / <code ...>...</code>
    tag_pat = re.compile(
        r'(<(?:a|strong|em|code)\b[^>]*>.*?</(?:a|strong|em|code)>)',
        re.DOTALL,
    )
    out_parts: List[str] = []
    last = 0
    for m in tag_pat.finditer(html_inline):
        raw_before = html_inline[last:m.start()]
        if raw_before:
            out_parts.append(f'<span leaf="">{raw_before}</span>')
        out_parts.append(m.group(1))
        last = m.end()
    tail = html_inline[last:]
    if tail:
        out_parts.append(f'<span leaf="">{tail}</span>')
    return "".join(out_parts)


def _huashu_wrap_p(text: str, tpl: dict) -> str:
    rendered = _huashu_render_inline(text, tpl)
    wrapped = _huashu_wrap_text_in_span_leaf(rendered)
    return f'<p style="{_huashu_body_paragraph_style(tpl)}">{wrapped}</p>'


def _huashu_wrap_h1(text: str, tpl: dict) -> str:
    """T-A 章节标题 → <h1> 真品三色渐变."""
    # 标题文字内不渲染 strong/link,直接 span leaf 包文字
    return f'<h1 style="{_huashu_h1_style(tpl)}"><span leaf="">{text}</span></h1>'


def _huashu_wrap_h2(text: str, tpl: dict) -> str:
    """T-B 章节标题 → <h2> 红底白字色块."""
    return f'<h2 style="{_huashu_h2_style(tpl)}"><span leaf="">{text}</span></h2>'


def _huashu_wrap_heading(text: str, tpl: dict) -> str:
    """按模板分支:T-A 用 h1 渐变,T-B 用 h2 色块."""
    h1_cfg = (tpl.get("typography") or {}).get("h1")
    h2_cfg = (tpl.get("typography") or {}).get("h2")
    if h1_cfg:
        return _huashu_wrap_h1(text, tpl)
    if h2_cfg:
        return _huashu_wrap_h2(text, tpl)
    # fallback
    return _huashu_wrap_h1(text, tpl)


def _huashu_wrap_quote(text: str, tpl: dict) -> str:
    rendered = _huashu_render_inline(text, tpl)
    return f'<blockquote style="{_huashu_quote_style(tpl)}">{rendered}</blockquote>'


def _huashu_wrap_img(url: str, alt: str, tpl: dict) -> str:
    """图片:用 <figure> 包 + padding 取代 margin 绕过 inline margin 不 collapse 陷阱.

    2026-05-24 Round 3 修(wechat-style-engineer skill 蒸馏后诊断):
    v6-v9 4 版盲推 figure margin/font-size/line-height 全失败,真因是 Agent A 调研出来的:
    inline style 让 margin collapse 失效 → figure 上下 margin 跟相邻 H1/p inline margin 不 collapse,
    两侧 margin 直接相加,导致 mobile 看「上 20 下 40」不对称(desktop 编辑器看不出来,真机才暴露).
    详见 C:\\Users\\23303\\.claude\\skills\\wechat-style-engineer\\references\\research\\01-opensource-image-handling.md
    修法 = margin 完全砍掉,改用 padding(padding 不参与 inline margin collapse 混乱,行为可预测):
    - figure margin: 0 砍 margin,避免跟相邻元素 inline margin 不 collapse 翻倍
    - figure padding: 24px 0 内部上下 padding(不 collapse,均匀对称分布)
    - font-size: 0 + line-height: 0 保留(防御性 hardening,Agent B 即使不是主因也无害)
    - img 不再需要 vertical-align: top(figure padding 已托管垂直 spacing)
    """
    figure_style = (
        "margin: 0;"                # 砍 margin,避免跟相邻元素 inline margin 不 collapse 翻倍
        "padding: 24px 0;"          # 内部 padding 取代 margin,均匀上下对称
        "font-size: 0;"             # 防 strut(防御性 hardening)
        "line-height: 0;"           # 同上,双保险
    )
    img_style = _huashu_img_style(tpl)  # 移除 vertical-align: top(figure padding 后不再需要)
    alt_attr = f' alt="{alt}"' if alt else ""
    return (
        f'<figure style="{figure_style}">'
        f'<img class="rich_pages wxw-img" style="{img_style}" src="{url}"{alt_attr} />'
        f'</figure>'
    )


def _huashu_default_signature(tpl: dict) -> str:
    """huashu 风格签名 — 用模板背景色和主色."""
    colors = tpl.get("colors") or {}
    bg = colors.get("background", "#faf9f7")
    return (
        f'<p style="margin:24px 0 8px 0;padding:14px 18px;'
        f'background:{bg};border-radius:8px;'
        f'font-size:13px;color:#666;line-height:1.7;text-align:center;">'
        f'<span leaf="">研究Agent的云 · 风云</span><br/>'
        f'<span leaf="">若有共鸣,愿你转给那位你想到的朋友</span><br/>'
        f'<span leaf="">邮箱 2330304961@qq.com · 微信 FengYunAgent</span>'
        f'</p>'
    )


def _huashu_process_paragraph(p: str, html_parts: List[str], tpl: dict) -> None:
    """huashu 版 _process_paragraph — 不强拆长段(花叔会自然出长段),不剥 banned intro."""
    # markdown 分割线 ---
    if re.match(r"^-{3,}\s*$", p):
        html_parts.append(_huashu_divider_html(tpl))
        return

    # 纯图片段
    only_imgs = INLINE_IMG_PAT.findall(p)
    cleaned = INLINE_IMG_PAT.sub("", p).strip()
    if only_imgs and not cleaned:
        for alt, url in only_imgs:
            html_parts.append(_huashu_wrap_img(url, alt, tpl))
        return

    # 引用块
    if p.startswith("> "):
        qtext = "\n".join(
            line.lstrip("> ").rstrip() for line in p.splitlines()
        ).strip()
        html_parts.append(_huashu_wrap_quote(qtext, tpl))
        return

    # 段内含图片:文本 + 图分开成段
    if INLINE_IMG_PAT.search(p):
        text_only = INLINE_IMG_PAT.sub("", p).strip()
        imgs = INLINE_IMG_PAT.findall(p)
        if text_only:
            html_parts.append(_huashu_wrap_p(text_only, tpl))
        for alt, url in imgs:
            html_parts.append(_huashu_wrap_img(url, alt, tpl))
    else:
        html_parts.append(_huashu_wrap_p(p, tpl))


def _render_huashu(
    markdown: str,
    section_image_urls: Optional[List[str]] = None,
    signature_html: Optional[str] = None,
    strip_frontmatter: bool = True,
    theme: str = "A",
    article_type: str = "thought_essay",
    image_at_h2_indices: Optional[List[int]] = None,
) -> str:
    """huashu 风格渲染主入口 — 真品 1:1 复刻(外层 section + h1 渐变 / h2 色块).

    Bug 2 修复 2026-05-24:加 image_at_h2_indices 支持花叔指定 slot.
    """
    # Bug 2:padded urls(花叔指定的 slot 位置)
    section_image_urls = _resolve_padded_urls(section_image_urls, image_at_h2_indices)
    tpl = _huashu_template(theme)

    # 1. 剥 frontmatter
    body = markdown
    if strip_frontmatter and body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()

    # 2. 切 ## 章节
    blocks = re.split(r"^##\s+", body, flags=re.MULTILINE)
    intro_block = blocks[0].strip()
    sections = blocks[1:]

    img_idx = 0
    html_parts: List[str] = []

    # 3. intro
    intro_paras = [p.strip() for p in re.split(r"\n\s*\n", intro_block) if p.strip()]

    if intro_paras:
        _huashu_process_paragraph(intro_paras[0], html_parts, tpl)
        # hero image:花叔风格首图在前 5 段、300 字内
        # Bug 2 修复:padded list None-check
        if img_idx < len(section_image_urls):
            url = section_image_urls[img_idx]
            if url is not None:
                html_parts.append(_huashu_wrap_img(url, "", tpl))
            img_idx += 1
        for p in intro_paras[1:]:
            _huashu_process_paragraph(p, html_parts, tpl)

    # 4. ## 章节 — T-A 渲染成 <h1> 真品三色渐变;T-B 渲染成 <h2> 红底色块
    for i, sec in enumerate(sections):
        lines = sec.split("\n", 1)
        title = lines[0].strip()
        section_body = lines[1] if len(lines) > 1 else ""

        html_parts.append(_huashu_wrap_heading(title, tpl))

        # 章节首图:tech_demo 密度更高,这层简单分配(每章 1 张直到耗尽)
        # Bug 2 修复:padded list None-check
        if img_idx < len(section_image_urls):
            url = section_image_urls[img_idx]
            if url is not None:
                html_parts.append(_huashu_wrap_img(url, "", tpl))
            img_idx += 1

        paras = [p.strip() for p in re.split(r"\n\s*\n", section_body) if p.strip()]
        for p in paras:
            _huashu_process_paragraph(p, html_parts, tpl)

    # 5. 结尾签名(包在最外层 section 内)
    html_parts.append(_huashu_default_signature(tpl) if not signature_html else signature_html)

    inner = "".join(html_parts)

    # 6. ⚠️ 关键:用外层 section 包裹整篇,带 background-color + data-pm-slice
    outer_style = _huashu_container_style(tpl)
    return (
        f'<section style="{outer_style}" data-pm-slice="0 0 []">'
        f'{inner}'
        f'</section>'
        f'<section><span leaf=""><br></span></section>'
        f'<p style="display: none;"><mp-style-type data-value="3"></mp-style-type></p>'
    )


# ============================================================
# Lint 自检
# ============================================================

def lint(html: str) -> List[str]:
    """
    渲染后 HTML 自检,返回违规清单.空 list = 全通过.

    ⚠️ Bug 7 分工注释(2026-05-25 Round 17 · WRITE_AGENT.md v1.0):
        本 lint 只检查 **渲染后 HTML** 的微信兼容性,跟 fengyun_lint.lint_article
        分工清晰、不重叠:
        - fengyun_lint.lint_article(md) → Step 4 内容 gate(R0-R25 二十多条规则)
        - layout_rules.lint(html)       → Step 8 HTML gate(本函数,6 条微信约束)
        两者都跑、各管一段,不要合并。调用方在 _render_html_layout_rules 里调本函数,
        致命级 issue(长度超限 / 禁用标签 / 绝对定位)由调用方阻断 ship。

    检查项:
    1. HTML 长度 ≤ 20000      [FATAL — 微信硬限制]
    2. 禁用标签 style/iframe/script/form/video/table/hr  [FATAL — 渲染异常]
    3. class/id 属性          [WARN  — 微信剥除,样式失效不破]
    4. 浅灰文字 #9XX/#aXX/#bXX [WARN  — 暗黑模式不可见]
    5. position absolute/fixed [FATAL — 布局会崩]
    6. 百分比 margin/transform [WARN  — 微信端失效]
    """
    issues: List[str] = []

    # 1. 长度上限
    # Round 21 P0-17:20000 是 layout_rules 内部历史值(非物理约束)
    # 微信草稿真实物理上限 ~65000 字节(实测公众号编辑器),为安全保留 5000 缓冲 → 60000
    # huashu 模板 inline style 膨胀 ~5x,4000 字 markdown ≈ 20000+ HTML 必爆原限制
    HTML_HARD_LIMIT = 60000
    if len(html) > HTML_HARD_LIMIT:
        issues.append(f"HTML {len(html)} chars > {HTML_HARD_LIMIT} 上限(微信硬限制)")

    # 2. 禁用标签
    for tag in ["<style", "<iframe", "<script", "<form", "<video", "<table"]:
        if tag in html.lower():
            issues.append(f"含禁用标签 {tag}(微信会剥除或渲染异常)")

    # <hr> 单独检查(更严格,可能被当 self-close 拼写)
    if re.search(r"<hr[\s/>]", html.lower()):
        issues.append("含 <hr> 标签(微信渲染丑,用 '· · ·' 替代)")

    # 3. class / id 属性
    if re.search(r'\sclass\s*=\s*["\']', html):
        issues.append("含 class 属性(微信会剥除,样式失效)")
    if re.search(r'\sid\s*=\s*["\']', html):
        issues.append("含 id 属性(微信会剥除)")

    # 4. 浅灰文字
    bad_grays = re.findall(
        r'color:\s*#(?:9[0-9a-f]{2}|a[0-9a-f]{2}|b[0-9a-f]{2})',
        html, re.IGNORECASE,
    )
    if bad_grays:
        issues.append(f"含浅灰文字颜色 {set(b.lower() for b in bad_grays)} "
                      f"(暗黑模式不可见,需 ≥ #333)")

    # 5. position 绝对定位
    if re.search(r'position:\s*(absolute|fixed)', html, re.IGNORECASE):
        issues.append("含 position:absolute/fixed(微信剥除,布局会崩)")

    # 6. 百分比 margin/transform(失效)
    if re.search(r'(margin|transform):[^;]*%', html):
        issues.append("含百分比 margin/transform(微信端会失效)")

    return issues


# ============================================================
# CLI 入口
# ============================================================

def main() -> None:
    import argparse
    import sys
    from pathlib import Path

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(
        description="layout_rules.py — Musk × Jobs 共识自动化排版")
    ap.add_argument("input", help="输入 markdown 文件")
    ap.add_argument("output", nargs="?", default=None,
                    help="输出 HTML 文件(默认 <input>.html)")
    ap.add_argument("--image", action="append", default=[],
                    help="章节图片 URL(按顺序对应 hero + 各章节,可多次)")
    ap.add_argument("--no-strip-fm", action="store_true",
                    help="不剥除 frontmatter")
    ap.add_argument("--lint-only", action="store_true",
                    help="只跑 lint 不输出 HTML")
    ap.add_argument("--preview", action="store_true",
                    help="生成本地浏览器 preview HTML(带 <html><body> 包装)")
    args = ap.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"[FATAL] 输入文件不存在: {src}")
        sys.exit(2)

    md = src.read_text(encoding="utf-8")
    html = render_to_wechat_html(
        md,
        section_image_urls=args.image,
        strip_frontmatter=not args.no_strip_fm,
    )

    issues = lint(html)
    print(f"=== layout_rules.py render ===")
    print(f"input:    {src} ({len(md)} chars)")
    print(f"output:   {len(html)} chars HTML")
    print(f"images:   {len(args.image)} URL given")
    print(f"lint:     {len(issues)} issues")
    for i in issues:
        print(f"  ⚠️  {i}")

    if args.lint_only:
        sys.exit(0 if not issues else 1)

    dst = Path(args.output) if args.output else src.with_suffix(".html")
    dst.parent.mkdir(parents=True, exist_ok=True)

    if args.preview:
        # 包装成可在浏览器打开的完整 HTML(模拟微信公众号宽度)
        preview = (
            f'<!DOCTYPE html><html lang="zh-CN"><head>'
            f'<meta charset="utf-8"><title>{src.stem}</title>'
            f'</head><body style="max-width:677px;margin:20px auto;padding:20px;'
            f'background:#fff;font-family:-apple-system,BlinkMacSystemFont,'
            f"'PingFang SC','Microsoft YaHei',sans-serif;\">"
            f'{html}</body></html>'
        )
        dst.write_text(preview, encoding="utf-8")
    else:
        dst.write_text(html, encoding="utf-8")

    print(f"✓ written: {dst}")
    sys.exit(0 if not issues else 1)


if __name__ == "__main__":
    main()
