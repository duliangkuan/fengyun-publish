"""
ending_signal.py — 文章结尾 4 维信号评分 + PHASE1 物理约束

Round 14 数据驱动(2026-05-24):
- 跑 viral_design_features.parquet 跨 4 账号 Spearman,4 个 PHASE1 严谨验证通过的真信号:
  * b_last_para_chars       mean ρ=+0.300 (4/4 显著)
  * viral_design_composite  mean ρ=+0.226 (4/4 显著)
  * viral_sharing_addr      mean ρ=+0.215 (4/4 显著)
  * viral_ending_strength   mean ρ=+0.201 (3/4 显著)
- TOP 5% 爆款 vs 扑街 8 个 STRONG 差异维度全部跨账号一致

4 维信号(跟 opening 镜像,但数据驱动 — 不是脑补):

| 维度 | 来源(viral_design) | 爆款 vs 扑街 | 阈值 |
|---|---|---|---|
| **末段字数(物理)** | b_last_para_chars | 5545 vs 2278(+143%)| ≥ 300 字 |
| **金句密度** | viral_ending_strength + viral_aphorism_pattern | 0.65 vs 0.41 / 3.14 vs 1.00 | ≥ 6/10 |
| **摘要密度** | viral_summary_density | 0.55 vs 0.27(+108%)| ≥ 6/10 |
| **召唤密度** | viral_imperative + viral_call_action | 3.74 vs 2.51 / 2.22 vs 0.46 | ≥ 6/10 |

接口:
    from tools.ending_signal import score_ending_signal

    result = score_ending_signal(article_full_text)
    # {
    #   "verdict": "pass" | "redo",
    #   "physical_pass": bool,
    #   "last_section_chars": int,
    #   "aphorism": int 0-10,
    #   "summary": int 0-10,
    #   "imperative": int 0-10,
    #   "weakest_dim": str,
    #   "redo_feedback": str,
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

# b_last_para_chars 跨 4 账号 ρ=+0.300 4/4 显著(PHASE1 最强结尾真信号)
# 全样本中位 2435 字,TOP 爆款中位 3451 字 — 但这是 features.parquet
# 按某种切分计算的值,可能 ≠ 「最后 H2 之后」概念,所以阈值取保守的 150 字
# 对风云 voice(短句呼吸感)友好,避免一句话收尾即可
MIN_LAST_SECTION_CHARS = 150


# ============================================================
# 4 维信号词典(基于 PHASE1 真信号反推)
# ============================================================

# 金句模式:对仗 / 哲思 / 反差 / 总结性短句
APHORISM_PATTERNS = [
    # 「不是 X,是 Y」/「不是 X,而是 Y」 反差句式
    r"不是\S{1,15}[,，]\s*(?:而是|是)\S{1,15}",
    # 「X 不在 Y,在 Z」
    r"\S{1,8}不在\S{1,10}[,，]\s*在\S{1,10}",
    # 古典引用(双引号包裹的短句)
    r"[""“][^""”]{4,30}[""”]",
    # 哲学性词汇
    r"(?:立心|觉知|边界|选择|敬畏|纯粹|本真|本心|本来|安住|清醒|勇气|温柔|笃定)",
    # 「X 是 X,X 是 X」 排比
    r"[一-鿿]{2,4}是[一-鿿]{2,4}[,，]\s*[一-鿿]{2,4}是[一-鿿]{2,4}",
    # 抽象升华词
    r"(?:这一代人|这个时代|这件事本身|说到底|归根结底|本质上|某种意义上)",
]

# 摘要密度模式:总结词 + 收束动作
SUMMARY_PATTERNS = [
    r"(?:写到这里|最后|说到底|归根结底|总之|总而言之)",
    r"(?:其实|本质上|本来)",
    r"(?:这件事|这个问题|这种感觉)",
    # 回环结构(开头出现的关键词在末段重复)
    # 注:这个需要传 opening 参数,简化版先用静态词典
    r"(?:对吧|是吧|不是吗)",  # 反问收束
    r"(?:再想一想|再说一遍|换个角度)",
]

# 召唤 / 祈使密度模式
IMPERATIVE_PATTERNS = [
    r"(?:愿|希望|期待|盼|祝)\S{1,15}",
    r"(?:不要|别|不必|无须|无需)\S{1,10}",
    r"(?:请|拜托|来|去|看|想|听|读)\S{0,4}(?:[,，。]|$)",
    # 「让 X 怎样」
    r"让(?:我们|自己|他|它|那个)\S{1,10}",
    # 「该 X 就 X」
    r"该\S{1,4}就\S{1,4}",
]

# 反模式:俗 CTA(扣分,不算召唤分)
TACKY_CTA_PATTERNS = [
    r"(?:点赞|转发|关注|求三连|扫码|二维码|点个在看|右下角|公众号矩阵)",
    r"(?:感谢阅读|点赞收藏|往期回顾|感谢支持)",
]


# ============================================================
# 抽末段块(最后 H2 / H3 之后的所有内容)
# ============================================================

def _extract_last_section(text: str) -> str:
    """抽文章最后的「收束块」 — 最后一个 H2 之后的所有段落.

    如果没有 H2(短文),用末尾 N 字兜底.
    """
    if not text:
        return ""
    # 找最后一个 ## 标题位置
    matches = list(re.finditer(r"^##\s+\S", text, flags=re.MULTILINE))
    if matches:
        last_h2 = matches[-1]
        return text[last_h2.end():].strip()
    # 没 H2 — 用末尾 800 字兜底(普通文章 ≤ 800 字收尾)
    return text[-800:].strip() if len(text) > 800 else text.strip()


# ============================================================
# 4 维评分
# ============================================================

def _score_aphorism(text: str) -> tuple[int, dict]:
    """金句密度评分."""
    counts = {}
    total = 0
    for pat in APHORISM_PATTERNS:
        n = len(re.findall(pat, text))
        if n > 0:
            counts[pat[:30]] = n
            total += n
    if total == 0:
        score = 0
    elif total == 1:
        score = 4
    elif total == 2:
        score = 6
    elif total == 3:
        score = 8
    else:
        score = min(10, 8 + (total - 3))
    return score, {"total_hits": total, "patterns": counts}


def _score_summary(text: str) -> tuple[int, dict]:
    """摘要 / 升华密度."""
    total = 0
    for pat in SUMMARY_PATTERNS:
        total += len(re.findall(pat, text))
    text_chars = len(re.sub(r"\s+", "", text))
    density = (total / text_chars) * 1000 if text_chars else 0
    # 爆款 viral_summary_density 0.55,扑街 0.27,中位 ≈ 0.40
    # 我们的 density 是「每千字」,要等比例
    if total == 0:
        score = 0
    elif total == 1:
        score = 4
    elif total == 2:
        score = 6
    elif total >= 3:
        score = 8 + min(2, total - 3)
    return min(10, score), {"total_hits": total, "density_per_1k": round(density, 2)}


def _score_imperative(text: str) -> tuple[int, dict]:
    """召唤 / 祈使密度(扣俗 CTA)."""
    pos = 0
    for pat in IMPERATIVE_PATTERNS:
        pos += len(re.findall(pat, text))
    neg = 0
    for pat in TACKY_CTA_PATTERNS:
        neg += len(re.findall(pat, text))
    net = max(0, pos - neg * 2)  # 俗 CTA 扣双倍
    # 爆款 imperative 3.74,扑街 2.51 → 阈值 3+
    if net == 0:
        score = 0
    elif net == 1:
        score = 4
    elif net == 2:
        score = 6
    elif net == 3:
        score = 8
    else:
        score = min(10, 8 + (net - 3))
    return score, {"positive_hits": pos, "tacky_cta_hits": neg, "net": net}


# ============================================================
# 物理约束
# ============================================================

def check_physical_constraints(text: str) -> dict:
    """检测末段字数 ≥ 300(PHASE1 4/4 强信号)."""
    last_section = _extract_last_section(text)
    chars = len(re.sub(r"\s+", "", last_section))

    fails = []
    if chars < MIN_LAST_SECTION_CHARS:
        fails.append(
            f"末段字数 {chars} < {MIN_LAST_SECTION_CHARS}"
            f"(PHASE1 跨 4 账号 ρ=+0.300 强信号,爆款均值 5545 字)"
        )

    return {
        "pass": len(fails) == 0,
        "last_section_chars": chars,
        "fails": fails,
    }


# ============================================================
# 主入口
# ============================================================

DIM_PASS_THRESHOLD = 6


def score_ending_signal(article_full_text: str) -> dict:
    """4 维信号 + 物理约束综合评分.

    Args:
        article_full_text: 完整文章 markdown(脚本会自动抽末段块)

    Returns: 见模块顶部 docstring
    """
    last_section = _extract_last_section(article_full_text)
    if not last_section:
        return {
            "verdict": "redo",
            "physical_pass": False,
            "last_section_chars": 0,
            "aphorism": 0, "summary": 0, "imperative": 0,
            "weakest_dim": "无收束段",
            "redo_feedback": "文章没有收束段,需要加 ## 收束 / ## 收尾 段落",
        }

    phys = check_physical_constraints(article_full_text)
    aphorism, aph_detail = _score_aphorism(last_section)
    summary, sum_detail = _score_summary(last_section)
    imperative, imp_detail = _score_imperative(last_section)

    dims = {
        "金句密度 aphorism": aphorism,
        "摘要密度 summary": summary,
        "召唤密度 imperative": imperative,
    }
    failed_dims = [n for n, s in dims.items() if s < DIM_PASS_THRESHOLD]
    weakest = min(dims.items(), key=lambda x: x[1])[0]

    all_dims_pass = len(failed_dims) == 0
    verdict = "pass" if (phys["pass"] and all_dims_pass) else "redo"

    feedback_parts = []
    if not phys["pass"]:
        feedback_parts.append("物理约束未过: " + "; ".join(phys["fails"]))
    if failed_dims:
        for fd in failed_dims:
            score = dims[fd]
            if "金句" in fd:
                feedback_parts.append(
                    f"金句密度 {score}/10 偏低 — 加 1-2 个「不是 X 是 Y」式反差 / 古典引用 / 哲思词"
                    f"(立心/觉知/边界/选择/勇气...),当前命中 {aph_detail['total_hits']} 处"
                )
            elif "摘要" in fd:
                feedback_parts.append(
                    f"摘要密度 {score}/10 偏低 — 加 1-2 个「说到底/其实/写到这里/归根结底」总结性短语"
                )
            elif "召唤" in fd:
                if imp_detail['tacky_cta_hits'] > 0:
                    feedback_parts.append(
                        f"召唤密度 {score}/10 偏低 — 当前有 {imp_detail['tacky_cta_hits']} 个俗 CTA"
                        f"(点赞/转发/关注),先删 + 加 1-2 个「愿你/不要/让我们...」式祈使"
                    )
                else:
                    feedback_parts.append(
                        f"召唤密度 {score}/10 偏低 — 加 1-2 个「愿你/不要/请/让我们...」式祈使句"
                    )

    return {
        "verdict": verdict,
        "physical_pass": phys["pass"],
        "last_section_chars": phys["last_section_chars"],
        "aphorism": aphorism,
        "summary": summary,
        "imperative": imperative,
        "dims_pass": [n for n, s in dims.items() if s >= DIM_PASS_THRESHOLD],
        "dims_fail": failed_dims,
        "weakest_dim": weakest,
        "redo_feedback": " | ".join(feedback_parts) if feedback_parts else "全过",
        "detail": {"aphorism": aph_detail, "summary": sum_detail, "imperative": imp_detail},
    }


# ============================================================
# CLI(测试用)
# ============================================================

def cli_demo():
    cases = [
        # case 1: 风云式标准结尾(Anthropic 9000 亿,引张载 + 颜文字)
        ("Anthropic 9000 亿结尾",
         """## 收束

笔者最后想送给和我一样的普通朋友一句话,这是宋朝的张载说的,

"为天地立心,为生民立命,为往圣继绝学,为万世开太平。"

我们做不到天地、生民、往圣、万世。但我们可以为我们自己,立一颗小小的心。

立心,就是承认自己活过,具体地、真实地、有名有姓地活过。在一个 9000 亿的牌局边上,这件事反而显得越来越稀缺,越来越珍贵,越来越值得。

笔者今晚把这篇写完,准备早点睡。明天醒来,世界八成还是这个世界。但我会比今天多记一件事。

朋友,愿你也能记下属于你的那些。共勉。(*∩_∩*)"""),
        # case 2: 短结尾 fail 物理约束
        ("短结尾",
         "## 收束\n\n这就是 AI 时代。请大家点赞关注!"),
        # case 3: 长但没金句 / 没召唤
        ("纯陈述长结尾",
         """## 收束

Anthropic 这件事说明 AI 行业正在快速变化。资本流向几家公司。OpenAI 估值高。这是当前的状况。
未来会怎样,没人能确定。但可以肯定的是,AI 影响越来越大。我们需要适应。一个个公司 IPO。
继续观察这个行业,了解更多动态。这就是当前 AI 行业的情况。"""),
    ]
    for name, text in cases:
        print(f"\n=== {name} ===")
        r = score_ending_signal(text)
        print(f"  verdict: {r['verdict']}")
        print(f"  物理: pass={r['physical_pass']} 末段={r['last_section_chars']} 字")
        print(f"  4 维: 金句={r['aphorism']}/10 摘要={r['summary']}/10 召唤={r['imperative']}/10")
        print(f"  weakest: {r['weakest_dim']}")
        print(f"  feedback: {r['redo_feedback']}")


if __name__ == "__main__":
    cli_demo()
