"""
topic_recommender.py — System A 数据驱动选题层(Round 11,2026-05-24)

设计原则:
- 不再脑补「主题集中度」「类别轮换」等没数据支持的多样性约束
- 用 PHASE1_FACTS 跨 4 账号验证过的爆款主题家族 + topic_hotness.parquet 排序候选
- 关键词查表(KQL)→ 主题家族 → 爆款率预测
- 只做「同一事件 7 天去重」(event_dedup.py),不做「同一主题去重」

数据来源:
- D:/Dev/ai-wechat-pipeline/topic_hotness.parquet  (2730 篇 × 8 特征,BERTopic 21 主题)
- D:/Dev/ai-wechat-pipeline/PHASE1_FACTS.md  (品牌词清单,跨 4 账号 v2 严谨性验证)
- D:/Dev/ai-wechat-pipeline/reports/topic_hotness_dynamic.md  (BERTopic 主题命名)

接口:
    from tools.topic_recommender import rank_aihot_candidates

    items = [...]  # aihot 拉的候选 dict list
    ranked = rank_aihot_candidates(items)
    # 每项加 _predicted_burst_rate / _matched_family / _matched_keywords / _reason
    # 已按 _predicted_burst_rate 降序

输出示例:
    [
      {"title": "...", "_predicted_burst_rate": 0.92, "_matched_family": "Anthropic Skills", ...},
      {"title": "...", "_predicted_burst_rate": 0.68, "_matched_family": "Anthropic/Claude", ...},
      {"title": "...", "_predicted_burst_rate": 0.30, "_matched_family": "(基线)", ...},
      {"title": "...", "_predicted_burst_rate": 0.15, "_matched_family": "OpenAI/GPT(反规律)", ...},
    ]
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# PHASE1_FACTS 锁定的主题家族 → 爆款率
# 来源:PHASE1_FACTS.md 行 660-700「品牌词深挖 v2 严谨性验证」
# 验证标准:跨 4 账号 ρ 同向 + 标题命中爆款率 + 26H1 跃迁验证
# ============================================================

# 关键词 → (家族名,预测爆款率,验证强度)
# 验证强度:strong=4/4 同向 / moderate=3/4 / weak=2/4 / micro=小样本
# 长 keyword 优先匹配(避免 "code" 误匹配 "Claude Code")
KEYWORD_TO_FAMILY: dict[str, tuple[str, float, str]] = {
    # ============== 正规律:2026 真热点(必选优先) ==============
    # Skills(Anthropic):标题命中爆款率 88.9% / 26H1 跃迁 0→50 篇 / 4/4 同向
    "anthropic skills": ("Anthropic Skills 框架实战", 0.92, "strong"),
    "claude skills": ("Anthropic Skills 框架实战", 0.92, "strong"),
    " skills": ("Anthropic Skills 框架实战", 0.85, "strong"),  # 含空格避免误匹配
    "skill": ("Anthropic Skills 框架实战", 0.85, "strong"),
    # Claude Code:爆款率 73.2% / 26H1 6→48 / 3/4 同向
    "claude code": ("Claude Code", 0.875, "moderate"),
    "vibe coding": ("Vibe Coding", 0.857, "moderate"),
    # Anthropic/Claude 家族:爆款率 67.8% / 4/4 同向
    "anthropic": ("Anthropic/Claude 家族", 0.678, "strong"),
    "claude": ("Anthropic/Claude 家族", 0.678, "strong"),
    "dario": ("Anthropic/Claude 家族", 0.678, "strong"),
    "amodei": ("Anthropic/Claude 家族", 0.678, "strong"),
    # Karpathy:88.9% 但小样本
    "karpathy": ("Karpathy 人物", 0.889, "micro"),
    # Agent/智能体:+11.3pp 弱一致
    "agent": ("Agent/智能体", 0.55, "weak"),
    "智能体": ("Agent/智能体", 0.55, "weak"),
    "mcp": ("Agent/智能体", 0.55, "weak"),
    "harness": ("Agent/智能体", 0.55, "weak"),

    # ============== 反规律:标题里凸显反而扣分(避免) ==============
    # OpenAI/GPT:标题命中 -9.3pp(2026 已脱离热点)
    "openai": ("OpenAI/GPT(反规律)", 0.15, "strong-negative"),
    "gpt-5": ("OpenAI/GPT(反规律)", 0.15, "strong-negative"),
    "gpt-4": ("OpenAI/GPT(反规律)", 0.15, "strong-negative"),
    "chatgpt": ("OpenAI/GPT(反规律)", 0.15, "strong-negative"),
    "sam altman": ("OpenAI/GPT(反规律)", 0.18, "moderate-negative"),
    # 国产闭源:-23.2pp
    "智谱": ("国产闭源(反规律)", 0.12, "strong-negative"),
    "glm": ("国产闭源(反规律)", 0.12, "strong-negative"),
    "kimi": ("国产闭源(反规律)", 0.15, "weak-negative"),
    "deepseek": ("DeepSeek(过气)", 0.18, "moderate-negative"),
    # 视频模型:-47.2pp
    "veo": ("视频模型(反规律)", 0.05, "strong-negative"),
    "sora": ("视频模型(反规律)", 0.08, "strong-negative"),
    # 老素材
    "cursor": ("Cursor(过气)", 0.18, "moderate-negative"),

    # ============== BERTopic topic_id 3:提示词工程 ==============
    # 26-02 hotness 0.84 → 26-04 跌到 0.00(过气中)
    "提示词工程": ("提示词工程(过气中)", 0.20, "moderate-negative"),
    "prompt engineering": ("提示词工程(过气中)", 0.20, "moderate-negative"),
}

# 基线爆款率(没命中任何关键词)
BASELINE_BURST_RATE = 0.30

# PHASE1 跨账号验证爆款率来源备注(给用户透明)
PHASE1_REASONS = {
    "strong": "✅ PHASE1 v2 严谨性验证(跨 4 账号 ρ 4/4 同向)— 必选",
    "moderate": "✅ PHASE1 v2 验证(3/4 跨账号同向)— 优先",
    "weak": "🟡 PHASE1 v2 弱信号(2/4 一致 + 小幅 Δ)— 可选",
    "micro": "🟡 小样本(n<10),方向对但置信度低",
    "strong-negative": "❌ PHASE1 跨 4 账号反规律(标题命中 -9pp 起)— 避免",
    "moderate-negative": "⚠️  PHASE1 反规律(3/4 跨号扣分)— 不优先",
    "weak-negative": "⚠️  PHASE1 弱反规律 — 慎用",
    "baseline": "⚪ 未命中已知家族(基线 0.30)— 风云 lived stake 自决",
}


# ============================================================
# topic_hotness.parquet 主题级聚合(可选增强,不阻塞)
# 如果 parquet 存在 → 加一个 hotness 调权;不存在 → 只用 PHASE1 表
# ============================================================

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
_TOPIC_HOTNESS_PATH = ROOT / "topic_hotness.parquet"

# BERTopic 21 主题命名(来源:topic_hotness_dynamic.md)
# 只录已知映射,未知 topic_id 用 family 名兜底
BERTOPIC_NAMES: dict[int, str] = {
    12: "Anthropic Skills 框架实战",
    3: "提示词工程与翻译实战",
    # 其它 topic_id 暂时没在 dynamic.md 里显式命名,留作后续扩展
}


def _load_topic_hotness_lookup():
    """加载 topic_hotness.parquet 聚合表(family_name → mean_hotness_90d).

    Returns:
        dict {family_name: hotness_90d} 或 {} 如果 parquet 不存在
    """
    if not _TOPIC_HOTNESS_PATH.exists():
        return {}
    try:
        import pandas as pd
        df = pd.read_parquet(_TOPIC_HOTNESS_PATH)
        agg = df.groupby("topic_id")["topic_hotness_90d"].mean().to_dict()
        # 映射到 family 名
        family_hotness = {}
        for tid, hotness in agg.items():
            if tid in BERTOPIC_NAMES:
                family_hotness[BERTOPIC_NAMES[tid]] = float(hotness) if hotness == hotness else 0.0
        return family_hotness
    except Exception as e:
        print(f"warn: topic_hotness.parquet load fail: {e}", file=sys.stderr)
        return {}


_FAMILY_HOTNESS_CACHE: Optional[dict[str, float]] = None


def _family_hotness(family: str) -> Optional[float]:
    """查 family 的 mean_hotness_90d(从 parquet),不存在返回 None."""
    global _FAMILY_HOTNESS_CACHE
    if _FAMILY_HOTNESS_CACHE is None:
        _FAMILY_HOTNESS_CACHE = _load_topic_hotness_lookup()
    return _FAMILY_HOTNESS_CACHE.get(family)


# ============================================================
# 核心:候选打分 + 排序
# ============================================================

def _score_candidate(text: str) -> dict:
    """对一条候选文本(title + summary)打分.

    Return:
        {
          "predicted_burst_rate": float,
          "matched_family": str,
          "matched_keywords": list[str],
          "verification": str,        # strong / moderate / weak / micro / negative / baseline
          "reason": str,              # 人话解释
          "hotness_boost": float|None # parquet 加权(可选)
        }
    """
    text_lower = text.lower()
    matched_kws = []
    best_family = None
    best_rate = BASELINE_BURST_RATE
    best_verif = "baseline"

    # 长 keyword 优先,避免 "code" 抢掉 "claude code"
    sorted_kws = sorted(KEYWORD_TO_FAMILY.items(), key=lambda x: -len(x[0]))
    for kw, (family, rate, verif) in sorted_kws:
        if kw in text_lower:
            matched_kws.append(kw)
            # 取爆款率最高的家族作为主匹配(正规律 > 反规律)
            if abs(rate - 0.5) > abs(best_rate - 0.5) and rate > best_rate:
                best_family = family
                best_rate = rate
                best_verif = verif
            elif best_family is None:
                best_family = family
                best_rate = rate
                best_verif = verif

    # 反规律命中 → 用反规律的低分(不要被基线 0.30 盖过去)
    for kw, (family, rate, verif) in sorted_kws:
        if kw in text_lower and "negative" in verif and rate < best_rate:
            # 如果命中了反规律且没命中更强的正规律,降权
            if best_verif == "baseline" or (best_verif != "strong" and best_verif != "moderate"):
                best_family = family
                best_rate = rate
                best_verif = verif

    # parquet hotness boost(如果 family 在 BERTopic 命名表里)
    hotness_boost = _family_hotness(best_family) if best_family else None
    final_rate = best_rate
    if hotness_boost is not None and hotness_boost > 0.5:
        # parquet hotness ≥ 0.5 → 0-10% boost
        boost_factor = min(0.10, hotness_boost * 0.10)
        final_rate = min(1.0, best_rate + boost_factor)

    reason = PHASE1_REASONS.get(best_verif, "—")
    if hotness_boost is not None:
        reason += f" / hotness_90d={hotness_boost:.2f}"

    return {
        "predicted_burst_rate": round(final_rate, 3),
        "matched_family": best_family or "(基线)",
        "matched_keywords": matched_kws,
        "verification": best_verif,
        "reason": reason,
        "hotness_boost": hotness_boost,
    }


def rank_aihot_candidates(items: list[dict]) -> list[dict]:
    """对 aihot 拉的候选 list 打分排序,返回新 list(原 dict 加 _predicted_* 字段).

    Args:
        items: aihot items,每项 dict 含 title / summary / category / url / source 等

    Return:
        按 _predicted_burst_rate 降序排好的 list(每项加 _predicted_* / _matched_* / _reason)

    Examples:
        >>> items = [{"title": "Claude Skills 新功能", ...}, {"title": "GPT-5 发布", ...}]
        >>> ranked = rank_aihot_candidates(items)
        >>> ranked[0]["_matched_family"]  # 'Anthropic Skills 框架实战'
        >>> ranked[0]["_predicted_burst_rate"]  # 0.92
        >>> ranked[-1]["_matched_family"]  # 'OpenAI/GPT(反规律)'
    """
    scored = []
    for item in items:
        text = (item.get("title", "") or "") + " " + (item.get("summary", "") or "")
        score = _score_candidate(text)
        new_item = dict(item)
        new_item["_predicted_burst_rate"] = score["predicted_burst_rate"]
        new_item["_matched_family"] = score["matched_family"]
        new_item["_matched_keywords"] = score["matched_keywords"]
        new_item["_verification"] = score["verification"]
        new_item["_reason"] = score["reason"]
        new_item["_hotness_boost"] = score["hotness_boost"]
        scored.append(new_item)
    return sorted(scored, key=lambda x: -x["_predicted_burst_rate"])


# ============================================================
# CLI 入口(测试用)
# ============================================================

def cli_demo():
    """跑几个 demo case 验证逻辑."""
    test_items = [
        {"title": "Anthropic Skills 框架深度解读", "summary": "Claude 新增能力", "category": "ai-products"},
        {"title": "GPT-5 发布,OpenAI 王者归来", "summary": "新一代模型", "category": "ai-models"},
        {"title": "Karpathy 加入 Anthropic 做 pre-training", "summary": "...", "category": "industry"},
        {"title": "DeepSeek R2 测评", "summary": "国产开源模型", "category": "ai-models"},
        {"title": "Claude Code 新功能:Vibe Coding", "summary": "agent 编程新范式", "category": "ai-products"},
        {"title": "Anthropic 9000 亿融资反超 OpenAI", "summary": "...", "category": "industry"},
        {"title": "提示词工程是不是过时了", "summary": "...", "category": "tip"},
        {"title": "Sora 2 视频生成", "summary": "OpenAI 视频", "category": "ai-products"},
        {"title": "一个普通人怎么用 AI", "summary": "...", "category": "tip"},  # 基线 case
    ]
    ranked = rank_aihot_candidates(test_items)
    print(f"=== topic_recommender demo: {len(ranked)} 条候选按爆款率排序 ===\n")
    for i, it in enumerate(ranked, 1):
        rate = it["_predicted_burst_rate"]
        fam = it["_matched_family"]
        verif = it["_verification"]
        title = it["title"]
        kws = it["_matched_keywords"]
        print(f"[{i:2d}] {rate:.2f}  {title}")
        print(f"     家族: {fam}  ({verif})")
        if kws:
            print(f"     命中关键词: {kws}")
        print(f"     {it['_reason']}")
        print()


if __name__ == "__main__":
    cli_demo()
