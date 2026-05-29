"""
opening_signal.py — 文章开头 4 维信号评分 + PHASE1 物理约束

Musk 第一性原理(2026-05-24 Round 13):
- 开头的物理目的 = 读者 0.5 秒决定继续滑屏
- 不预设「该长啥样」,只 enforce「该有什么效果」
- 4 维客观计数(不主观判断):具体性 / 反差感 / 情绪锚点 / 信息密度

PHASE1 数据校准(2026-05-21 严谨性验证 v2):
- 跨 4 账号同向的唯一开头真规律 = 首段字数 ≥ 50 字
- TOP 5% 爆款 vs 扑街:第一人称密度 +12.5pp(强信号)
- 其它「事件引入 / 疑问 / 情绪开头」等 4 个 binary 特征 4/4 同向 = 0(普适规律不存在)

接口:
    from tools.opening_signal import score_opening_signal

    result = score_opening_signal(text_first_200_chars)
    # {
    #   "verdict": "pass" | "redo",
    #   "physical_pass": bool,          # 物理约束
    #   "first_para_chars": int,
    #   "first_person_density": float,
    #   "concreteness": int 0-10,
    #   "reframe": int 0-10,
    #   "emotion_anchor": int 0-10,
    #   "info_density": int 0-10,
    #   "weakest_dim": str,
    #   "redo_feedback": str,           # 给 writer 改稿的具体反馈
    # }
"""
from __future__ import annotations
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# 物理约束(PHASE1 数据锁定)
# ============================================================

MIN_FIRST_PARA_CHARS = 50            # PHASE1 跨 3/4 账号同向,首段 <50 字爆款率掉到 41.9%
MIN_FIRST_PERSON_DENSITY = 5.0       # 千字密度,实测 top 5% 爆款 +12.5pp


# ============================================================
# 4 维信号关键词词典(客观计数,不主观判断)
# ============================================================

# 反差感:转折词 + 否定 + 颠覆句式
REFRAME_PATTERNS = [
    r"但是", r"然而", r"不过", r"可是", r"只是",
    r"其实", r"反而", r"反倒", r"恰恰",
    # Round 21 P0-4:\S 不匹配空格,「不是 demo,是 Agent」漏判
    # 改成 [^。\n] 允许空格/逗号/英文/数字,但不允许跨句(句号)或换行
    r"不是[^。\n]{1,15}是",     # 不是 X,是 Y 句式(允许空格 + 中文/英文逗号)
    r"原以为[^。\n]{1,20}",     # 原以为...
    r"以为[^。\n]{1,15}才发现", # 以为...才发现
    # Round 26 补漏(2026-05-26):本次 E2E R3 开头「你以为...直到」漏判
    # 4 个新模式都是 \"以为 X, Y\" 的经典反差句式,跟现有 \"以为X才发现\" 同类
    # 长度 1,25(实测「以为写好一个 agent skill 就完事了,直到」中间 17 字符,15 卡死)
    r"以为[^。\n]{1,25}直到",   # 以为...直到(本次 R3 命中)
    r"以为[^。\n]{1,25}没想到", # 以为...没想到
    r"以为[^。\n]{1,25}结果",   # 以为...结果
    r"以为[^。\n]{1,25}后来",   # 以为...后来才
    r"看似[^。\n]{1,15}实际",   # 看似...实际
    r"表面上[^。\n]{1,15}事实", # 表面上...事实
    r"出乎.{0,5}意料",
    r"意想不到",
    r"截然", r"恰好相反",
    r"颠覆", r"打破",
    # Round 26 P0 补漏(2026-05-26 E2E Fix 6):补充常见反差句式
    r"看似[^。\n]{1,15}实则",     # 看似 X 实则 Y(跟上面「看似...实际」互补)
    r"看上去[^。\n]{1,15}实际上", # 看上去 X 实际上 Y
    r"明明[^。\n]{1,15}却",       # 明明 X 却 Y
    r"不是[^。\n]{1,15}而是",     # 不是 X 而是 Y(跟上面「不是...是」互补)
]

# 情绪锚点:具体动作动词 + 感受词(风云 voice DNA + 通用爆款词)
EMOTION_ACTION_WORDS = [
    "愣了", "停了", "停下来", "停一下", "停顿",
    "想了想", "想起", "想到",
    "看着", "盯着", "盯了", "看了一遍",
    "念了", "读了", "听了",
    "发了一会儿呆", "发呆",
    "心里一沉", "心里一紧", "心里一动",
    "突然", "猛地", "一下子",
    "皱眉", "眯眼", "深呼吸",
]

# 信息密度:中文实词检测的近似 — 排除常见停用词
STOPWORDS_CN = {
    "的", "了", "是", "和", "在", "我", "你", "他", "她", "它",
    "我们", "你们", "他们", "这", "那", "什么", "怎么", "什么的",
    "也", "都", "就", "还", "又", "或", "再", "也是", "就是",
    "可以", "可能", "应该", "需要", "要", "用", "给", "把", "被",
    "让", "使", "对", "对于", "关于", "因为", "所以", "如果",
    "比如", "例如", "等等", "一些", "一个", "一种", "一直",
    "已经", "正在", "曾经", "将", "会", "能", "想", "知道", "觉得",
}

# 反差感命中数 → 分(0-10)
def _score_reframe(text: str) -> int:
    n_hits = 0
    for pat in REFRAME_PATTERNS:
        n_hits += len(re.findall(pat, text))
    # 命中 0 → 0 分, 1 → 5 分, 2 → 7 分, 3+ → 9 分
    if n_hits == 0:
        return 0
    elif n_hits == 1:
        return 5
    elif n_hits == 2:
        return 7
    else:
        return min(10, 7 + n_hits)


# 具体性:数字 / 时间 / 英文专名 / 中文人名(粗略)
def _score_concreteness(text: str) -> tuple[int, dict]:
    counts = {}
    # 数字 + 单位(亿 / 万 / 千 / 百 / % / 美元 等)
    counts["number_unit"] = len(re.findall(
        r"\d+(?:[.,]\d+)?\s*(?:亿|万亿|千亿|百亿|万|千|百|%|％|美元|元|美刀|台|个|人|条|次|篇|年|月|日|小时|分钟|秒|倍|岁)",
        text
    ))
    # 纯数字(独立出现)
    counts["pure_number"] = len(re.findall(r"\b\d{2,}\b", text)) - counts["number_unit"]
    counts["pure_number"] = max(0, counts["pure_number"])
    # 时间表达
    counts["time_phrase"] = len(re.findall(
        r"(?:前几天|昨天|今天|刚才|那天|\d+\s*月\s*\d+\s*日|\d{4}\s*年|上周|本周|周\S)",
        text
    ))
    # 英文专名(连续 2+ 字母,常见 AI 名词)
    counts["english_name"] = len(re.findall(r"\b[A-Z][a-zA-Z]{2,}", text))
    # 中文 2-4 字名词(粗略,可能含人名 / 机构名)
    # 这里只数「连续 2-4 字中文」出现的次数,作为信息锚点近似
    counts["chinese_noun_groups"] = len(re.findall(r"[一-鿿]{2,4}", text))

    # 综合打分:数字/时间/英文专名 是强信号
    strong = (counts["number_unit"] + counts["time_phrase"]
              + counts["english_name"] + counts["pure_number"])
    if strong == 0:
        score = 0
    elif strong == 1:
        score = 4
    elif strong == 2:
        score = 6
    elif strong <= 4:
        score = 8
    else:
        score = 10
    return score, counts


# 情绪锚点:第一人称密度 + 具体动作动词
def _score_emotion_anchor(text: str) -> tuple[int, dict]:
    # 第一人称密度(千字)
    text_chars = len(re.sub(r"\s+", "", text))
    if text_chars == 0:
        return 0, {"first_person_density": 0, "action_hits": 0}
    fp_count = len(re.findall(r"我(?!们)|我们(?!的)|笔者", text))
    fp_density = (fp_count / text_chars) * 1000
    # 具体动作动词命中
    action_hits = sum(text.count(w) for w in EMOTION_ACTION_WORDS)

    # 分:第一人称密度 ≥ 5 算物理及格,动作 ≥ 1 算锚点
    if fp_density < 1 and action_hits == 0:
        score = 0
    elif fp_density < 5 and action_hits == 0:
        score = 3
    elif fp_density >= 5 and action_hits == 0:
        score = 5
    elif fp_density < 5 and action_hits >= 1:
        score = 6
    elif fp_density >= 5 and action_hits >= 1:
        score = 8 + min(2, action_hits - 1)
    else:
        score = 5
    return min(10, score), {
        "first_person_density": round(fp_density, 1),
        "action_hits": action_hits,
    }


# 信息密度:实词 token 比 + 新概念引入数
def _score_info_density(text: str) -> tuple[int, dict]:
    # 抽 2-4 字中文 token
    cn_tokens = re.findall(r"[一-鿿]{2,4}", text)
    if not cn_tokens:
        return 0, {"content_ratio": 0, "new_concepts": 0}
    content_tokens = [t for t in cn_tokens if t not in STOPWORDS_CN]
    content_ratio = len(content_tokens) / max(1, len(cn_tokens))

    # 新概念引入:英文专名 + 4 字以上中文专名
    new_concepts = (
        len(re.findall(r"\b[A-Z][a-zA-Z]{2,}", text))
        + len(re.findall(r"[一-鿿]{4,8}", text))
    )

    if content_ratio < 0.4:
        score = 2
    elif content_ratio < 0.6:
        score = 5
    elif content_ratio < 0.75:
        score = 7
    else:
        score = 8

    # new_concepts 加成
    if new_concepts >= 3:
        score = min(10, score + 2)
    elif new_concepts >= 1:
        score = min(10, score + 1)

    return score, {
        "content_ratio": round(content_ratio, 2),
        "new_concepts": new_concepts,
    }


# ============================================================
# 公式骨架检测(R28 · Round 16 · 2026-05-25)
# ============================================================
# 数据驱动:
#   6 篇 ship 过的文章里,4 篇套同一公式:「时间锚 + 视觉动词 + 信息名词 三件套」
#   - 教皇: 「今天凌晨,我刷推的时候,看到一条新闻」
#   - Cursor: 「昨天凌晨,Cursor 发了新模型」(时间锚)
#   - 9000 亿: 「前几天晚上,我看到一条消息」
#   - Karpathy: 「前几天,看到一条新闻,我读了三遍」
#
# H2 opening_dedup 抓不到(各篇用词不同,Jaccard 分散),
# 但公式骨架完全一样 — 用 syntactic bucket 检测能抓到

OPENING_FORMULA_BUCKETS = {
    "time_anchor": [
        "今天", "昨天", "前几天", "这两天", "这几天",
        "今天凌晨", "昨天凌晨", "前几天晚上", "前几天早上",
        "刚刚", "刚才", "前两天", "上周", "本周",
    ],
    "visual_verb": [
        "看到", "读到", "读了", "刷到", "刷推", "瞄到",
        "听到", "翻到", "盯着", "盯了", "扫到",
        "看见", "瞄了", "扫过",
    ],
    "info_noun": [
        "一条新闻", "一条消息", "一条推", "一个帖子",
        "一条推文", "一个新闻", "新闻", "消息", "推文",
        "一篇文章", "一段话",
    ],
}


def detect_opening_formula(text_first_200: str) -> dict:
    """检测开头是否套「时间锚 + 视觉动词 + 信息名词」三件套公式.

    Returns:
        {
          "hit_buckets": int,                   # 命中几个 bucket(0-3)
          "hit_details": {bucket: [hit_words]}, # 每 bucket 的命中词
          "is_formulaic": bool,                 # 是否撞公式(≥ 2 bucket 命中)
        }
    """
    hits = {}
    for bucket, words in OPENING_FORMULA_BUCKETS.items():
        bucket_hits = [w for w in words if w in text_first_200]
        if bucket_hits:
            hits[bucket] = bucket_hits

    return {
        "hit_buckets": len(hits),
        "hit_details": hits,
        "is_formulaic": len(hits) >= 2,
    }


def _score_formula_freshness(text: str) -> tuple[int, dict]:
    """第 5 维:公式新鲜度评分(R28).

    0 bucket 命中 → 10/10(全新公式)
    1 bucket 命中 → 8/10(单件套,边缘)
    2 bucket 命中 → 4/10(撞公式)
    3 bucket 命中 → 0/10(典型撞公式)
    """
    detect = detect_opening_formula(text)
    n = detect["hit_buckets"]
    if n == 0:
        score = 10
    elif n == 1:
        score = 8
    elif n == 2:
        score = 4
    else:  # n == 3
        score = 0
    return score, detect


# ============================================================
# 物理约束检测(PHASE1 锁定)
# ============================================================

def check_physical_constraints(full_opening_text: str) -> dict:
    """检测 PHASE1 锁定的 2 个物理约束.

    Args:
        full_opening_text: 文章开头完整 intro 段落(直到第一个 H2 之前)

    Returns:
        {
          "pass": bool,
          "first_para_chars": int,
          "first_person_density": float,
          "fails": list[str],
        }
    """
    # PHASE1 `b_first_para_chars` 定义 = 整个 intro 块字数(直到 H2 之前),不是单段
    # 修正 2026-05-24:不要按 \n\n 切第一小段,要算整个 intro 总字数
    # 截到 H2(## ) 之前
    intro_text = full_opening_text
    m = re.search(r"\n##\s", intro_text)
    if m:
        intro_text = intro_text[:m.start()]
    first_para_chars = len(re.sub(r"\s+", "", intro_text))

    text_chars = first_para_chars  # 用 intro 块字数算密度
    fp_count = len(re.findall(r"我(?!们)|我们(?!的)|笔者", intro_text))
    fp_density = (fp_count / text_chars) * 1000 if text_chars else 0

    fails = []
    if first_para_chars < MIN_FIRST_PARA_CHARS:
        fails.append(f"首段字数 {first_para_chars} < {MIN_FIRST_PARA_CHARS}(PHASE1 锁定)")
    if fp_density < MIN_FIRST_PERSON_DENSITY:
        fails.append(
            f"第一人称密度 {fp_density:.1f}/千字 < {MIN_FIRST_PERSON_DENSITY}(实测 top 5% 爆款 +12.5pp)"
        )

    return {
        "pass": len(fails) == 0,
        "first_para_chars": first_para_chars,
        "first_person_density": round(fp_density, 2),
        "fails": fails,
    }


# ============================================================
# 主入口:综合评分
# ============================================================

DIM_PASS_THRESHOLD = 6  # 每维 ≥ 6 才算通过


def score_opening_signal(text_opening: str) -> dict:
    """4 维信号评分 + 物理约束综合评分.

    Args:
        text_opening: 文章开头(建议传前 200-300 字,或者完整 intro 段落)

    Returns: dict — 见模块顶部 docstring
    """
    text_first_200 = text_opening[:200] if len(text_opening) > 200 else text_opening

    # 物理约束(用完整 opening 算)
    phys = check_physical_constraints(text_opening)

    # 5 维信号(用前 200 字算;第 5 维 R28 公式新鲜度 2026-05-25 新增)
    concreteness, concreteness_detail = _score_concreteness(text_first_200)
    reframe = _score_reframe(text_first_200)
    emotion_anchor, emotion_detail = _score_emotion_anchor(text_first_200)
    info_density, info_detail = _score_info_density(text_first_200)
    formula_freshness, formula_detail = _score_formula_freshness(text_first_200)

    dims = {
        "具体性 concreteness": concreteness,
        "反差感 reframe": reframe,
        "情绪锚点 emotion_anchor": emotion_anchor,
        "信息密度 info_density": info_density,
        "公式新鲜度 formula_freshness": formula_freshness,
    }

    # 判断每维是否通过
    failed_dims = [name for name, score in dims.items() if score < DIM_PASS_THRESHOLD]
    weakest_dim = min(dims.items(), key=lambda x: x[1])[0]

    all_dims_pass = len(failed_dims) == 0
    verdict = "pass" if (phys["pass"] and all_dims_pass) else "redo"

    # 给 writer 改稿的具体反馈
    feedback_parts = []
    if not phys["pass"]:
        feedback_parts.append("物理约束未过: " + "; ".join(phys["fails"]))
    if failed_dims:
        for fd in failed_dims:
            score = dims[fd]
            if "具体性" in fd:
                feedback_parts.append(
                    f"具体性 {score}/10 偏低 — 加 1-2 个具体数字/时间/英文专名(命中 {concreteness_detail})"
                )
            elif "反差感" in fd:
                feedback_parts.append(
                    f"反差感 {score}/10 偏低 — 加 1 个转折/否定/「不是 X 是 Y」句式"
                )
            elif "情绪锚点" in fd:
                feedback_parts.append(
                    f"情绪锚点 {score}/10 偏低 — 加 1 个具体动作动词"
                    f"(愣了/停下来/想起...)+ 第一人称(当前密度 {emotion_detail['first_person_density']}/千字)"
                )
            elif "信息密度" in fd:
                feedback_parts.append(
                    f"信息密度 {score}/10 偏低 — 实词比 {info_detail['content_ratio']} 太低,"
                    "减虚词加具体概念"
                )
            elif "公式新鲜度" in fd:
                hits_str = " / ".join(
                    f"{b}({','.join(ws)})" for b, ws in formula_detail['hit_details'].items()
                )
                feedback_parts.append(
                    f"公式新鲜度 {score}/10 偏低 — 撞「时间锚+视觉动词+信息名词」三件套公式 "
                    f"[{hits_str}],换骨架 — 比如直接抛数字 / 直接进场景 / 第二人称对话"
                )

    return {
        "verdict": verdict,
        "physical_pass": phys["pass"],
        "first_para_chars": phys["first_para_chars"],
        "first_person_density": phys["first_person_density"],
        "concreteness": concreteness,
        "reframe": reframe,
        "emotion_anchor": emotion_anchor,
        "info_density": info_density,
        "formula_freshness": formula_freshness,
        "formula_hit_buckets": formula_detail["hit_buckets"],
        "formula_hit_details": formula_detail["hit_details"],
        "dims_pass": [n for n, s in dims.items() if s >= DIM_PASS_THRESHOLD],
        "dims_fail": failed_dims,
        "weakest_dim": weakest_dim,
        "redo_feedback": " | ".join(feedback_parts) if feedback_parts else "全过",
    }


# ============================================================
# CLI(测试用)
# ============================================================

def cli_demo():
    cases = [
        # case 1: 之前的 Anthropic 9000 亿开头
        ("Anthropic 9000 亿",
         "前几天晚上,我看到一条消息。\n\nAnthropic 这家公司,正在完成一轮 300 亿美元的融资。"
         "融完之后估值 9000 亿,反超了 OpenAI。\n\n我把这两个数字念了一遍,又念了一遍。九千亿。"
         "中国 GDP 的百分之一。\n\n第一反应当然是「这跟我有什么关系」。"),
        # case 2: 短首段(应该 fail 物理约束)
        ("短首段失败 case",
         "今天写一篇文章。\n\n这是关于 AI 的。"),
        # case 3: 完全无第一人称(物理 fail)
        ("无第一人称",
         "5 月 14 日,Anthropic 公布最新融资消息。300 亿美元落地,估值 9000 亿。"
         "这件事很重要,影响整个 AI 行业。"),
    ]
    for name, text in cases:
        print(f"\n=== {name} ===")
        r = score_opening_signal(text)
        print(f"  verdict: {r['verdict']}")
        print(f"  physical: pass={r['physical_pass']} first_para={r['first_para_chars']}字 "
              f"第一人称={r['first_person_density']}/千字")
        print(f"  5 维: 具体={r['concreteness']}/10 反差={r['reframe']}/10 "
              f"情绪={r['emotion_anchor']}/10 信息={r['info_density']}/10 "
              f"新鲜={r['formula_freshness']}/10")
        print(f"  公式撞型 buckets: {r['formula_hit_buckets']}/3 -> {r['formula_hit_details']}")
        print(f"  weakest: {r['weakest_dim']}")
        print(f"  feedback: {r['redo_feedback']}")


if __name__ == "__main__":
    cli_demo()
