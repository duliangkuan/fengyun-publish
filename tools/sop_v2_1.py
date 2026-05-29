# -*- coding: utf-8 -*-
"""
SOP v2.1 多维度评分系统(可被其他脚本 import)

在 v2 基础上整合 2 个独立的重磅特征：

Feature 1: style_match_score (独立第六维度, 25% 混合权重)
  - 来源: style_match_features.parquet (TF-IDF cosine 与爆款/扑街锚文章相似度差)
  - 验证: hold-out LOO 4/4 账号正向显著 (ρ=0.27-0.37)
  - 赛博禅心(saiboshanxin) hold-out ρ=-0.24，作保护性 clip: max(0, raw_score)
  - 综合公式: total_v21 = 0.75 × (5维加权) + 0.25 × style_match_normalized

Feature 2: viral_ending_strength (加进 share_score 维度)
  - 来源: viral_design_features.parquet
  - 验证: mean_ρ=+0.235, 4/4 跨账号一致
  - 与 SOP v2 重叠 0%
  - 训练集(pre-2026)阈值(仅用训练集分位):
      q50=q75=q90=0.667(三档离散: 0.333/0.667/1.0)
      使用: >= 0.667 → +5; >= 1.0 (实际 q97) → +8

数据文件:
  - D:/Dev/ai-wechat-pipeline/style_match_features.parquet
  - D:/Dev/ai-wechat-pipeline/viral_design_features.parquet

签名兼容 v2:
  sop_score_v2_1(row) 输出与 sop_score_v2 兼容，额外新增 style_match_score / style_match_normalized

# 不在 hold-out 上调参——所有阈值来自 pre-2026 训练集
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ============================================================
# 从 sop_v2 直接复用所有子函数 + 常量（不修改 sop_v2.py）
# ============================================================
import sys
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "tools"))

from sop_v2 import (  # noqa: E402
    BRAND_HOT, BRAND_COLD, cover_family, _g,
    score_read, score_share, score_like, score_old_like, score_comment,
    DIM_WEIGHTS,
)

# ============================================================
# 加载 style_match 和 viral_design parquet（模块级一次性加载）
# ============================================================
_STYLE_MATCH_PATH = _ROOT / "style_match_features.parquet"
_VIRAL_DESIGN_PATH = _ROOT / "viral_design_features.parquet"
# Round 7 P0(2026-05-24): 风云 IP anchor bootstrap parquet
_FENGYUN_ANCHOR_PATH = _ROOT / "fengyun_anchor.parquet"

_style_match_df: pd.DataFrame | None = None
_viral_design_df: pd.DataFrame | None = None

# style_match_score 的全量（2025 训练集）min/max，用于 normalize
# 由 _init_parquets() 计算
_SM_TRAIN_MIN: float = -0.221321
_SM_TRAIN_MAX: float = 0.087404  # pre-2026 训练集上的极值（已提前计算）

# viral_ending_strength 阈值（pre-2026 训练集分位，已计算）
# q75=q90=0.667，最高档 1.0（~q97）
_VES_Q75: float = 0.6667
_VES_Q97: float = 1.0   # 实际最高离散值


def _init_parquets():
    """Bug 4 修复 2026-05-24:silent fall back 改 fail-loud warning.

    当 style_match / fengyun_anchor parquet 缺失时,以前是 silent 给空 DataFrame,
    导致 style_match_normalized 全是 null 但用户看不到任何报错。
    现在显式 print 警告到 stderr + 给 rebuild 提示,
    用户可设 env FENGYUN_SUPPRESS_STYLE_MATCH_WARN=1 静默(测试场景).
    """
    global _style_match_df, _viral_design_df
    import os
    import sys
    suppress = os.environ.get("FENGYUN_SUPPRESS_STYLE_MATCH_WARN", "").lower() in ("1", "true", "yes")

    if _style_match_df is None:
        if _STYLE_MATCH_PATH.exists():
            _style_match_df = pd.read_parquet(_STYLE_MATCH_PATH).set_index("aid")
        else:
            _style_match_df = pd.DataFrame(columns=["style_match_score"])
            if not suppress:
                print(
                    f"⚠️  [sop_v2_1] style_match_features.parquet 不存在 ({_STYLE_MATCH_PATH}),\n"
                    f"   style_match_normalized 将全为 None。\n"
                    f"   修复:跑 tools/build_style_match_features.py 生成,\n"
                    f"   或设 env FENGYUN_SUPPRESS_STYLE_MATCH_WARN=1 静默.",
                    file=sys.stderr,
                )

        # Round 7 P0(2026-05-24): 合并风云 IP anchor bootstrap parquet
        # 风云本人已 ship 的稿子用 tools/fengyun_anchor.py rebuild 算 score 入此 parquet
        if _FENGYUN_ANCHOR_PATH.exists():
            try:
                fy_df = pd.read_parquet(_FENGYUN_ANCHOR_PATH)
                if "aid" in fy_df.columns:
                    fy_df = fy_df.set_index("aid")
                if "style_match_score" in fy_df.columns:
                    # 合并:风云 aid 的 score 不会和 PHASE1 4 KOL 的 aid 冲突
                    _style_match_df = pd.concat([_style_match_df, fy_df[["style_match_score"]]])
            except Exception as e:
                print(f"⚠️  [sop_v2_1] failed loading fengyun_anchor.parquet: {e}", file=sys.stderr)
        else:
            if not suppress:
                print(
                    f"⚠️  [sop_v2_1] fengyun_anchor.parquet 不存在 ({_FENGYUN_ANCHOR_PATH}),\n"
                    f"   风云 IP anchor 维度缺失。\n"
                    f"   修复:跑 python tools/fengyun_anchor.py rebuild,\n"
                    f"   或设 env FENGYUN_SUPPRESS_STYLE_MATCH_WARN=1 静默.",
                    file=sys.stderr,
                )
    if _viral_design_df is None:
        if _VIRAL_DESIGN_PATH.exists():
            _viral_design_df = pd.read_parquet(_VIRAL_DESIGN_PATH).set_index("aid")
        else:
            _viral_design_df = pd.DataFrame(columns=["viral_ending_strength"])
            if not suppress:
                print(
                    f"⚠️  [sop_v2_1] viral_design_features.parquet 不存在 ({_VIRAL_DESIGN_PATH}),\n"
                    f"   viral_ending_strength 维度缺失.",
                    file=sys.stderr,
                )


# ============================================================
# Feature 2: viral_ending_strength 注入到 share_score
# (share 是"转发意愿"维度，结尾强度与分享行为最相关)
# ============================================================

def score_share_v21(row) -> tuple[float, list, list]:
    """share_score v2.1：在 v2 基础上加 viral_ending_strength 规则。"""
    _init_parquets()

    # 先调原始 v2 share_score
    score, triggered, missed = score_share(row)

    # 取 aid
    aid = _g(row, "aid", None) or (row.name if hasattr(row, "name") else None)

    # 查 viral_ending_strength
    ves = None
    if aid is not None and _viral_design_df is not None and aid in _viral_design_df.index:
        raw = _viral_design_df.at[aid, "viral_ending_strength"]
        if not (isinstance(raw, float) and np.isnan(raw)):
            ves = float(raw)

    if ves is not None:
        if ves >= _VES_Q97 - 1e-6:  # == 1.0
            score += 8
            triggered.append({
                "dim": "share",
                "rule": f"结尾强度 viral_ending_strength={ves:.3f} (顶级 ~q97)",
                "delta": +8,
                "type": "bonus",
            })
        elif ves >= _VES_Q75 - 1e-6:  # >= 0.667
            score += 5
            triggered.append({
                "dim": "share",
                "rule": f"结尾强度 viral_ending_strength={ves:.3f} (≥q75)",
                "delta": +5,
                "type": "bonus",
            })
        else:
            # 低于 q75(0.667) → 提示改进
            missed.append({
                "action": "加强文章结尾爆款设计(号召/金句/互动召唤),提升 viral_ending_strength 到 0.667+",
                "dim": "share",
                "expected_delta": +5,
            })

    return max(0, min(100, score)), triggered, missed


# ============================================================
# Feature 1: style_match_score 独立第六维度
# ============================================================

def _get_style_match_normalized(aid, account_slug: str) -> tuple[float | None, float | None]:
    """
    返回 (raw_score, normalized_score)：
      - raw_score: 原始 style_match_score（余弦相似度差）
      - normalized_score: 线性映射到 [0, 100]（基于训练集 min/max）
      - 赛博禅心账号: raw_score → max(0, raw_score) 保护性 clip（避免反向负贡献）
    """
    _init_parquets()
    if aid is None or _style_match_df is None or aid not in _style_match_df.index:
        return None, None
    raw = _style_match_df.at[aid, "style_match_score"]
    if isinstance(raw, float) and np.isnan(raw):
        return None, None

    raw = float(raw)

    # 赛博禅心账号: hold-out ρ=-0.24，保护性 clip
    if account_slug == "saiboshanxin":
        raw = max(0.0, raw)

    # 线性 normalize 到 [0, 100]
    denom = _SM_TRAIN_MAX - _SM_TRAIN_MIN
    if denom < 1e-10:
        norm = 50.0
    else:
        norm = (raw - _SM_TRAIN_MIN) / denom * 100.0
        norm = max(0.0, min(100.0, norm))

    return raw, norm


# ============================================================
# 顶层接口 v2.1
# ============================================================

# v2.1 综合权重：5维 × 0.75 + style_match × 0.25
V21_BLEND_5DIM = 0.75
V21_BLEND_STYLE = 0.25


def sop_score_v2_1(row) -> dict[str, Any]:
    """SOP v2.1 多维度评分 + 反馈结构（兼容 v2 签名）

    输入：一行（dict 或 pandas Series），须含 aid + 所有 features.parquet 字段。
    输出：{ total_score, read_score, share_score, like_score, old_like_score, comment_score,
           style_match_score, style_match_normalized,   ← 新增
           rules_triggered, suggestions }
    """
    r_s, r_tr, r_ms = score_read(row)
    s_s, s_tr, s_ms = score_share_v21(row)   # 含 viral_ending_strength
    l_s, l_tr, l_ms = score_like(row)
    o_s, o_tr, o_ms = score_old_like(row)
    c_s, c_tr, c_ms = score_comment(row)

    five_dim = (DIM_WEIGHTS["read"] * r_s
                + DIM_WEIGHTS["share"] * s_s
                + DIM_WEIGHTS["like"] * l_s
                + DIM_WEIGHTS["old_like"] * o_s
                + DIM_WEIGHTS["comment"] * c_s)

    # style_match 维度
    aid = _g(row, "aid", None) or (row.name if hasattr(row, "name") else None)
    account_slug = str(_g(row, "account_slug", "") or
                       _g(row, "acc_m", "") or "")
    raw_sm, norm_sm = _get_style_match_normalized(aid, account_slug)

    if norm_sm is not None:
        total = V21_BLEND_5DIM * five_dim + V21_BLEND_STYLE * norm_sm
    else:
        # 无 style_match 数据时退化为 v2
        total = five_dim
        norm_sm = None

    all_triggered = r_tr + s_tr + l_tr + o_tr + c_tr
    all_missed = r_ms + s_ms + l_ms + o_ms + c_ms
    all_missed.sort(key=lambda x: -x.get("expected_delta", 0))

    return {
        "total_score": round(total, 1),
        "read_score": round(r_s, 1),
        "share_score": round(s_s, 1),
        "like_score": round(l_s, 1),
        "old_like_score": round(o_s, 1),
        "comment_score": round(c_s, 1),
        "style_match_score": round(raw_sm, 4) if raw_sm is not None else None,
        "style_match_normalized": round(norm_sm, 1) if norm_sm is not None else None,
        "rules_triggered": all_triggered,
        "suggestions": all_missed,
    }


def sop_score_v2_1_total(row) -> float:
    """便捷：只取 total_score（用于 df.apply 求总分向量）"""
    return sop_score_v2_1(row)["total_score"]


if __name__ == "__main__":
    # 自检
    dummy = {
        "aid": "test_aid_001",
        "account_slug": "kazik",
        "title": "Claude Code Skills 完全指南：我用 vibe coding 做了 3 个 agent",
        "t_chars": 32, "t_english_chars": 15,
        "b_chars": 4200, "b_para_avg_chars": 220, "b_one_liner_ratio": 0.05,
        "jb_lexical_diversity": 0.40, "jb_avg_word_len": 1.6, "tb_ratio": 0.03,
        "has_cover_color": 1, "cover_r": 250, "cover_g": 200, "cover_b": 110,
        "cover_brightness": 210, "img_per_1k_chars": 3.5,
        "topic_hotness_30d": 0.85, "topic_hotness_90d": 0.82,
        "current_event_words_in_title": 1, "action_verb_count": 4,
        "opinion_strength_markers": 3, "cultural_meme": 1,
        "controversy_markers": 2, "first_person_density": 0.025,
        "personal_pronoun_in_title": 1, "interaction_call_in_title": 0,
        "comment_question_ratio": 0.25, "comment_ip_diversity": 0.72,
        "comment_avg_length": 35, "comment_long_ratio": 0.42,
        "comment_sentiment_neg_ratio": 0.10,
    }
    out = sop_score_v2_1(pd.Series(dummy))
    print(f"total={out['total_score']}, read={out['read_score']}, share={out['share_score']},"
          f" like={out['like_score']}, old_like={out['old_like_score']}, comment={out['comment_score']}")
    print(f"style_match_score={out['style_match_score']}, normalized={out['style_match_normalized']}")
    print(f"triggered={len(out['rules_triggered'])} rules, suggestions={len(out['suggestions'])}")
    for s in out["suggestions"][:5]:
        print(f"  → [{s['dim']}] {s['action']} ({s['expected_delta']:+d})")
