"""
title_signal.py — 标题多维信号评分(Round 16 · 2026-05-25)

用户原话(2026-05-25):「就做标题党 — PHASE1 数据有规律可以直接用 — title harness 是必要的」

为什么是 P0:
  最近几篇 ship 文章都是 AI 系统产出,「风云碰巧做对了」≠「风云本人判断力」
  AI 系统没有硬约束,下一次产出就可能翻车 — 必须 lock 数据规律

数据基础(全部 PHASE1 实证,反 p-hacking 合规):
  1. tb_ratio ρ -0.32(PHASE1_FACTS line 168)
  2. 字数 ∈ [20, 40](line 810,短于 10 是小样本陷阱)
  3. 数字数 ≤ 1(line 302,双高 0.36 vs 假爆款 0.70)
  4. 品牌词必上(line 691-698):Anthropic / Claude / Skills / Claude Code
  5. 反品牌词不上(line 698):OpenAI / GPT / Veo / GLM(2026 已脱热)
  6. 7 钩子公式之一(reports/title_hook_formulas.md,78 篇双高 LLM 提取)
  7. 4 共同特质(反常规 / 强行动 / 信息密度 / 情绪化)
  8. 致命组合(line 836-848)— 4.16-4.56 倍扑街:
       a. 标题英文 < 8 字符 + 一行一段堆叠 > 0.5 + 平均词长 > 1.8
       b. 同上 + 正文英文占比 > 0.2
       c. tb_ratio > 0 + 标题英文 < 8 + 一行一段 > 0.5

接口:
    from tools.title_signal import score_title

    result = score_title(title, topic_keywords=["Anthropic", "Karpathy"])
    # {
    #   "verdict": "pass" | "redo",
    #   "score_total": float (0-100),
    #   "char_count": int,
    #   "hook_type": "颠覆认知" | "实用指南" | ... | None,
    #   "brand_white_hit": list[str],
    #   "brand_black_hit": list[str],
    #   "digit_count": int,
    #   "traits_hit": dict (4 共同特质命中),
    #   "fatal_combo_risk": bool,
    #   "redo_feedback": str,
    # }
"""
from __future__ import annotations
import re
import sys
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# 物理约束(PHASE1 锁定)
# ============================================================

MIN_TITLE_CHARS = 20       # PHASE1 line 810
MAX_TITLE_CHARS = 40       # 同上,长于 40 进 critic 灰区
MAX_DIGIT_COUNT = 1        # 双高 0.36 vs 假爆款 0.70

# 致命组合阈值
FATAL_ENGLISH_CHARS_THRESHOLD = 8


# ============================================================
# 品牌词清单(PHASE1 line 691-698 跨账号验证)
# ============================================================

BRAND_WHITELIST = [
    "Anthropic", "Claude", "Skills", "Claude Code",
    "Sonnet", "Opus", "Haiku",                         # Claude 系列
]

BRAND_BLACKLIST_2026 = [
    "OpenAI", "GPT-5", "GPT-4", "GPT-3", "GPT ",
    "Veo", "GLM", "ChatGPT",                            # 2026 已脱热
]
# 注意:GPT 后跟空格,避免误伤 GPT-Image(Image 类未脱热)


# ============================================================
# 7 钩子公式 — syntactic 模式匹配(PHASE1 78 篇 LLM 提取)
# ============================================================

HOOK_PATTERNS = {
    "颠覆认知": [
        r"别再用?\S{1,15}",                             # 别再用提示词去 AI 味
        r"为什么\S{1,15}(错|不对|大错|看空|不该|没用)",  # 为什么我看空英伟达
        r"\S{1,10}已死",                                # 设计流程已死
        r"\S{1,10}是错的",                              # 方向就是错的
        r"\S{1,10}可能大错特错",                        # AI 优先战略大错特错
        r"没人(答|懂|知道|做对)",                       # 几乎没人答对
    ],
    "实用指南": [
        r"爆肝\d+\S{0,3}(时|小时|天)",                  # 爆肝 50 小时
        r"收藏(这一)?篇?(就够了|就行)",                # 收藏这一篇就够了
        r"保姆级\S{0,8}",                              # 保姆级教程
        r"(N|\d+)\s*步\S{0,8}框架",                    # 五步框架
        r"\d+\s*分钟(上手|学会|搞定|入门)",            # 20 分钟上手 Python
        r"写给\S{1,10}的你",                           # 写给不会代码的你
    ],
    "热点事件": [
        r"(发布|上线|宣布|全量|开源)\S{0,15}",         # X 发布 / 全量上线
        r"(首款|首次|全球第一|国产第一|首发)\S{0,10}",  # 全球首款通用型 Agent
        r"\S{1,8}收购\S{1,8}",                         # Meta 收购 Manus
        r"\d+\s*(亿|万|千)\S{0,5}(融资|估值|IPO|上市)",  # 9000 亿估值
        r"(重磅|官宣|官方)\S{0,10}",                   # 官宣 / 重磅
    ],
    "人物故事": [
        r"\S{2,6}(的)?\s*\d+\s*年\S{0,8}",             # 肖弘的十年狂飙
        r"从\S{1,8}到\S{1,8}",                         # 从 X 到 Y
        r"\S{2,6}访谈\S{0,8}",                         # Karpathy 最新访谈
        r"\S{2,6}离职(后)?\S{0,10}",                   # 林俊旸离职后
        r"\S{2,6}首发\S{0,8}",                         # 林俊旸首发长文
        r"(创始人|CEO|CTO|CPO|工程师)\S{0,15}(说|谈|讲|访谈|手册)",
    ],
    "思维比喻": [
        r"\S{2,10}\s*就是\s*\S{2,10}",                 # X 就是 Y
        r"\S{2,10}\s*=\s*\S{2,10}",                    # X = Y
        r"\S{2,10}时刻\s*来了",                        # Claude Code 时刻来了
        r"\S{2,8}是\S{2,8}的\s*\S{2,8}",              # Vibe Coding 是中年男人的钓鱼
    ],
    "深度拆解": [
        r"是怎么\S{1,8}的?",                           # 是怎么训练的
        r"深度(拆解|解读|解析)",                       # 深度拆解
        r"万字\S{0,8}",                                # 万字长文
        r"\d+\s*页\S{0,8}(论文|白皮书|手册|报告)",     # 58 页论文
        r"\S{2,8}完全指南",                            # DeepSeek 完全指南
        r"中学生(都)?能看懂",                          # 中学生能看懂
    ],
    "未来预言": [
        r"20\d{2}\s*\S{1,8}巨变",                      # 2026 编程巨变
        r"\d+\s*大趋势",                               # 八大趋势
        r"奇点",                                       # 我们已迈过奇点
        r"AI\s*时代\S{0,15}(最难|最重要|最关键)",      # AI 时代最难被替代
        r"(再不|不|没)\S{1,5}就(晚|完|废)了",          # 再不学就晚了(注意:可能跟焦虑词冲突,需 Vision check)
    ],
}


# ============================================================
# 4 共同特质 syntactic 模式
# ============================================================

TRAIT_PATTERNS = {
    "反常规认知": [
        r"别再", r"为什么\S{0,5}(错|不对|看空)", r"已死",
        r"是错的", r"\S+反\S+", r"没人", r"竟然",
        r"出乎.{0,3}意料", r"颠覆",
    ],
    "强行动指令": [
        r"收藏", r"\d+\s*分钟(上手|学会|搞定)",
        r"保姆级", r"完全指南", r"教程", r"\d+\s*步",
        r"看(完|这)就", r"读完", r"学(完|会)",
    ],
    "情绪化表达": [
        r"[!!]", r"[??]", r"~",
        r"[\U0001F300-\U0001F9FF]",                    # emoji 范围
        r"重磅", r"惊", r"爆", r"哇",
    ],
}


# ============================================================
# 评分子函数
# ============================================================

def _count_chars(title: str) -> int:
    """字符数(纯文本,空白不算)."""
    return len(re.sub(r"\s+", "", title))


def _count_digits(title: str) -> int:
    """数字组数(连续数字算 1 个)."""
    return len(re.findall(r"\d+", title))


def _count_english_chars(title: str) -> int:
    """英文字符总数(算字母,不算空格)."""
    return len(re.findall(r"[A-Za-z]", title))


def _detect_brand(title: str, whitelist: list[str], blacklist: list[str]) -> tuple[list[str], list[str]]:
    """检测品牌词命中(白 + 黑)."""
    title_lower = title.lower()
    white_hits = [w for w in whitelist if w.lower() in title_lower]
    black_hits = [b for b in blacklist if b.lower() in title_lower]
    return white_hits, black_hits


def _detect_hook(title: str) -> Optional[str]:
    """检测 7 钩子命中,返回最早匹配的 hook 类型(None = 不命中任何钩子)."""
    for hook_name, patterns in HOOK_PATTERNS.items():
        for pat in patterns:
            try:
                if re.search(pat, title):
                    return hook_name
            except re.error:
                continue
    return None


def _detect_traits(title: str) -> dict:
    """检测 4 共同特质命中.

    info_density 特别处理:title 里实体词 ≥ 3 个(公司/数字/人物/英文)算命中.
    """
    hits = {}
    for trait, patterns in TRAIT_PATTERNS.items():
        for pat in patterns:
            try:
                if re.search(pat, title):
                    hits[trait] = True
                    break
            except re.error:
                continue
        else:
            hits[trait] = False

    # info_density:实体词计数
    entity_count = (
        _count_digits(title) +                                          # 数字
        len(re.findall(r"[A-Z][a-z]{2,}", title)) +                     # 英文专名
        len(re.findall(r"\d+\s*(亿|万|千|百|页|步|分钟|小时|天|年)", title))  # 数量短语
    )
    hits["高信息密度"] = entity_count >= 2

    return hits


def _check_fatal_combo(title: str, body_chars: int = 5000) -> dict:
    """致命组合检测(PHASE1 line 836-848).

    title 英文 < 8 字 + tb_ratio > 0 = 一个 4.16x 扑街信号.
    单凭 title 不能完全判定(需要正文信息),但能给出 title-side 警告.
    """
    eng_chars = _count_english_chars(title)
    title_chars = _count_chars(title)
    tb_ratio = title_chars / body_chars if body_chars else 0

    risk = (eng_chars < FATAL_ENGLISH_CHARS_THRESHOLD) and (tb_ratio > 0.03)

    return {
        "english_chars": eng_chars,
        "tb_ratio": round(tb_ratio, 4),
        "risk": risk,
    }


# ============================================================
# 主入口
# ============================================================

def score_title(
    title: str,
    topic_keywords: Optional[list[str]] = None,
    body_chars: int = 5000,
    brand_whitelist: Optional[list[str]] = None,
    brand_blacklist: Optional[list[str]] = None,
) -> dict:
    """标题多维评分.

    Args:
        title: 标题文本
        topic_keywords: 文章主题关键词列表(用于判断品牌白名单是否「必上」)
        body_chars: 正文字数(用于算 tb_ratio,默认 5000)
        brand_whitelist: 自定义白名单(默认用 PHASE1 锁定)
        brand_blacklist: 自定义黑名单

    Returns: 见模块顶部 docstring
    """
    if brand_whitelist is None:
        brand_whitelist = BRAND_WHITELIST
    if brand_blacklist is None:
        brand_blacklist = BRAND_BLACKLIST_2026

    title = title.strip()
    char_count = _count_chars(title)
    digit_count = _count_digits(title)
    white_hits, black_hits = _detect_brand(title, brand_whitelist, brand_blacklist)
    hook_type = _detect_hook(title)
    traits = _detect_traits(title)
    fatal_combo = _check_fatal_combo(title, body_chars=body_chars)

    # ============================================================
    # 评分组件(总分 100)
    # ============================================================

    # 1. 字数(20 分):∈ [20, 40] → 20 / [10, 20) 或 (40, 50] → 10 / 其他 → 0
    if MIN_TITLE_CHARS <= char_count <= MAX_TITLE_CHARS:
        score_chars = 20
    elif 10 <= char_count < MIN_TITLE_CHARS or MAX_TITLE_CHARS < char_count <= 50:
        score_chars = 10
    else:
        score_chars = 0

    # 2. 数字数 ≤ 1(10 分)
    score_digits = 10 if digit_count <= MAX_DIGIT_COUNT else 0

    # 3. 品牌词命中(20 分):
    #    主题相关 + 白名单命中 → 20 分
    #    主题相关 + 白名单缺 → 0 分(失分)
    #    主题不相关 → 满分 20(不强求)
    if topic_keywords:
        # 判断主题是否跟白名单相关
        topic_lower = " ".join(topic_keywords).lower()
        topic_in_whitelist = any(w.lower() in topic_lower for w in brand_whitelist)
        if topic_in_whitelist:
            score_brand = 20 if white_hits else 0
        else:
            score_brand = 20  # 不强求
    else:
        score_brand = 20 if white_hits else 10  # 不知道主题给中间分

    # 4. 反品牌词扣分(20 分):命中 → -20
    score_anti_brand = 0 if black_hits else 20

    # 5. 7 钩子命中(20 分):命中任一 → 20 / 不命中 → 0
    score_hook = 20 if hook_type else 0

    # 6. 4 共同特质(10 分):每个 2.5 分
    score_traits = sum(2.5 for t, hit in traits.items() if hit)

    score_total = score_chars + score_digits + score_brand + score_anti_brand + score_hook + score_traits

    # ============================================================
    # verdict + 反馈
    # ============================================================

    # 致命组合直接 redo,不看总分
    if fatal_combo["risk"]:
        verdict = "redo"
    # Bug 2 修复(2026-05-25 Round 17 · WRITE_AGENT.md v1.0):
    #   7 钩子从软分 20 升级为 hard gate。
    #   宪法 Step 3.3:命中 PHASE1 7 钩子任一 → hard gate;不命中即 redo。
    #   理由:字数 + 品牌词 + 反品牌 + 特质都过但无钩子的标题 = 平淡叙述,
    #         CTR 数据归纳显示这类标题 0 爆款。
    elif not hook_type:
        verdict = "redo"
    else:
        verdict = "pass" if score_total >= 65 else "redo"

    feedback_parts = []
    if score_chars < 20:
        if char_count < MIN_TITLE_CHARS:
            feedback_parts.append(
                f"字数 {char_count} < {MIN_TITLE_CHARS}(PHASE1 line 810,小于 20 字小样本陷阱),补到 20-40 字"
            )
        else:
            feedback_parts.append(
                f"字数 {char_count} > {MAX_TITLE_CHARS}(超长进 critic 灰区),减到 20-40 字"
            )
    if digit_count > MAX_DIGIT_COUNT:
        feedback_parts.append(
            f"数字组数 {digit_count} > 1(双高 0.36 vs 假爆款 0.70,数字越多越假爆款),保留最关键 1 个数字"
        )
    if topic_keywords and score_brand == 0:
        feedback_parts.append(
            f"主题相关品牌词缺失 — 当文章涉及 {brand_whitelist} 时,标题必须含其中之一"
        )
    if black_hits:
        feedback_parts.append(
            f"标题含反品牌词 {black_hits} — 2026 已脱热(-9.3pp),换说法"
        )
    if not hook_type:
        feedback_parts.append(
            "未命中 7 钩子任一(颠覆认知/实用指南/热点事件/人物故事/思维比喻/深度拆解/未来预言),换钩子公式"
        )
    failed_traits = [t for t, hit in traits.items() if not hit]
    if len(failed_traits) >= 3:
        feedback_parts.append(
            f"4 共同特质命中 {4 - len(failed_traits)}/4 偏低 — 缺 {failed_traits},加感叹号 / 反问 / 实体词 / 颠覆词"
        )
    if fatal_combo["risk"]:
        feedback_parts.append(
            f"⚠️ 致命组合:英文 {fatal_combo['english_chars']} < 8 + tb_ratio {fatal_combo['tb_ratio']} > 0.03 "
            f"(PHASE1 4.16x 扑街),加英文产品名 / 删字数"
        )

    return {
        "verdict": verdict,
        "score_total": round(score_total, 1),
        "char_count": char_count,
        "digit_count": digit_count,
        "english_chars": fatal_combo["english_chars"],
        "tb_ratio": fatal_combo["tb_ratio"],
        "hook_type": hook_type,
        "brand_white_hit": white_hits,
        "brand_black_hit": black_hits,
        "traits_hit": traits,
        "traits_hit_count": sum(1 for v in traits.values() if v),
        "fatal_combo_risk": fatal_combo["risk"],
        "score_breakdown": {
            "字数": score_chars,
            "数字数": score_digits,
            "品牌白": score_brand,
            "反品牌黑": score_anti_brand,
            "7 钩子": score_hook,
            "4 特质": round(score_traits, 1),
        },
        "redo_feedback": " | ".join(feedback_parts) if feedback_parts else "全过",
    }


# ============================================================
# CLI 测试 — 用风云 6 篇真实标题
# ============================================================

def cli_demo():
    cases = [
        # case 1-6: 风云 6 篇 ship 真标题
        ("教皇要为 AI 发通谕了,他选的人不是 Sam Altman", ["AI", "教皇", "Anthropic"]),
        ("号称地表最强的 Cursor 2.5,大脑居然是 Kimi 的", ["Cursor", "Kimi"]),
        ("云谈神话:Anthropic 这一周,我看到了什么", ["Anthropic"]),
        ("AI巨头的三种活法——5月20日那一夜，三家公司给了三种答卷", ["AI", "OpenAI", "xAI"]),
        ("9000 亿的牌局,一个普通人的位置", ["Anthropic", "OpenAI", "融资"]),
        ("Karpathy 转身的那笔账", ["Karpathy", "OpenAI", "Anthropic"]),
        # case 7: 双高爆款示例 — 颠覆认知
        ("别再用提示词去 AI 味了,方向就是错的", ["AI"]),
        # case 8: 双高爆款示例 — 思维比喻
        ("Vibe Coding 是中年男人的钓鱼", ["Vibe Coding"]),
        # case 9: 致命组合 case
        ("我的小尝试", ["AI"]),
    ]
    for title, topics in cases:
        print(f"\n=== {title} ===")
        r = score_title(title, topic_keywords=topics)
        print(f"  verdict: {r['verdict']}  score: {r['score_total']}/100")
        print(f"  钩子: {r['hook_type']}  | 字数: {r['char_count']} | 数字: {r['digit_count']} | "
              f"英文: {r['english_chars']} | tb_ratio: {r['tb_ratio']}")
        print(f"  品牌白: {r['brand_white_hit']}  | 品牌黑: {r['brand_black_hit']}")
        print(f"  4 特质命中: {r['traits_hit_count']}/4 -> {[t for t, h in r['traits_hit'].items() if h]}")
        print(f"  致命组合 risk: {r['fatal_combo_risk']}")
        print(f"  breakdown: {r['score_breakdown']}")
        print(f"  feedback: {r['redo_feedback']}")


if __name__ == "__main__":
    cli_demo()
