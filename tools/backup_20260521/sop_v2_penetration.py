"""
SOP v2 多维度规则系统:2026 H1 hold-out 穿透测试

对比:
  - SOP v1 (单维度)        ← sop_rules_penetration_test.py 的 sop_score()
  - SOP v2 (多维度,本次)   ← sop_v2.sop_score_v2()
  - critic v2 (LGB ML)     ← 近 12 个月窗口重训

8 个指标:R² / Spearman ρ / MAE / Top 10% / Top 30% / Bottom 10% / 分箱准确率 / std
"""
from __future__ import annotations
import sys, sqlite3, json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats
import lightgbm as lgb
from sklearn.metrics import r2_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

from sop_v2 import sop_score_v2, DIM_WEIGHTS  # noqa: E402
# v1 evaluation: 重新导入避免名字冲突
import importlib.util
spec_v1 = importlib.util.spec_from_file_location("sop_v1_mod", ROOT / "tools" / "sop_rules_penetration_test.py")
sop_v1_mod = importlib.util.module_from_spec(spec_v1)
spec_v1.loader.exec_module(sop_v1_mod)
sop_score_v1 = sop_v1_mod.sop_score

REPORT = ROOT / "reports" / "sop_v2_penetration.md"


def all_metrics(name, pred, y_true):
    r2 = r2_score(y_true, pred)
    rho, p = stats.spearmanr(pred, y_true)
    mae = float(np.mean(np.abs(pred - y_true)))
    n = len(y_true)
    k10 = max(1, int(n * 0.1))
    k30 = max(1, int(n * 0.3))
    true_top10 = set(np.argsort(y_true)[-k10:])
    pred_top10 = set(np.argsort(pred)[-k10:])
    top10_p = len(true_top10 & pred_top10) / k10
    true_top30 = set(np.argsort(y_true)[-k30:])
    pred_top30 = set(np.argsort(pred)[-k30:])
    top30_p = len(true_top30 & pred_top30) / k30
    true_bot10 = set(np.argsort(y_true)[:k10])
    pred_bot10 = set(np.argsort(pred)[:k10])
    bot10_p = len(true_bot10 & pred_bot10) / k10
    bin_correct = 0
    for i in range(len(y_true)):
        true_bin = min(9, int(y_true[i] // 10))
        pred_bin = min(9, int(max(0, pred[i]) // 10))
        if abs(true_bin - pred_bin) <= 1:
            bin_correct += 1
    bin_acc = bin_correct / len(y_true)
    return {
        "name": name, "r2": float(r2), "rho": float(rho), "p": float(p), "mae": mae,
        "top10_p": top10_p, "top30_p": top30_p, "bot10_p": bot10_p,
        "bin_acc": bin_acc,
        "pred_range": (float(pred.min()), float(pred.max())),
        "pred_std": float(pred.std()),
    }


def main():
    print("=== 加载并合并所有 feature 表 ===")
    feat = pd.read_parquet(ROOT / "features.parquet")
    targ = pd.read_parquet(ROOT / "targets.parquet")
    cmt = pd.read_parquet(ROOT / "comment_features.parquet")
    top = pd.read_parquet(ROOT / "topic_hotness.parquet")
    sem = pd.read_parquet(ROOT / "semantic_features.parquet")
    con = sqlite3.connect(ROOT / "db.sqlite")
    meta = pd.read_sql_query(
        "SELECT aid, account_slug AS acc_m, title, create_time AS ct, itemidx FROM articles", con)

    df = feat.merge(targ, on="aid", suffixes=("", "_t")).merge(meta, on="aid")
    df = df.merge(cmt, on="aid", how="left", suffixes=("", "_cf"))
    df = df.merge(top, on="aid", how="left", suffixes=("", "_tf"))
    df = df.merge(sem, on="aid", how="left", suffixes=("", "_sf"))

    df["composite_pct"] = (0.40*df["read_pct"] + 0.15*df["like_pct"] + 0.15*df["old_like_pct"]
                           + 0.20*df["share_pct"] + 0.10*df["comment_pct"])
    df["dt"] = pd.to_datetime(df["ct"], unit="s")
    df["year"] = df["dt"].dt.year
    df = df.dropna(subset=["composite_pct"]).reset_index(drop=True)

    test_mask = (df["year"] == 2026).values
    test_df = df.loc[test_mask].reset_index(drop=True)
    y_test = test_df["composite_pct"].values
    print(f"  全数据 {len(df)} 篇 / 测试集 (2026 H1) {len(test_df)} 篇")
    print(f"  test composite_pct: range [{y_test.min():.1f}, {y_test.max():.1f}], std={y_test.std():.1f}")

    # ===== 1. SOP v1 =====
    print("\n=== SOP v1 (单维度) ===")
    # v1 的 sop_score 只需要 features.parquet 字段 + title;test_df 已经包含
    sop_v1_scores = test_df.apply(sop_score_v1, axis=1).values.astype(float)
    print(f"  ρ={stats.spearmanr(sop_v1_scores, y_test).correlation:+.3f}, std={sop_v1_scores.std():.2f}")

    # ===== 2. SOP v2 =====
    print("\n=== SOP v2 (多维度) ===")
    sop_v2_outputs = test_df.apply(sop_score_v2, axis=1).tolist()
    sop_v2_total = np.array([o["total_score"] for o in sop_v2_outputs])
    sop_v2_read = np.array([o["read_score"] for o in sop_v2_outputs])
    sop_v2_share = np.array([o["share_score"] for o in sop_v2_outputs])
    sop_v2_like = np.array([o["like_score"] for o in sop_v2_outputs])
    sop_v2_oldlike = np.array([o["old_like_score"] for o in sop_v2_outputs])
    sop_v2_comment = np.array([o["comment_score"] for o in sop_v2_outputs])
    print(f"  total ρ={stats.spearmanr(sop_v2_total, y_test).correlation:+.3f}, std={sop_v2_total.std():.2f}")
    # 各维度 vs 各 sub-target ρ
    print("  各维度 vs sub-target ρ(诊断):")
    for dim_name, dim_scores, sub in [
        ("read",  sop_v2_read,    "read_pct"),
        ("share", sop_v2_share,   "share_pct"),
        ("like",  sop_v2_like,    "like_pct"),
        ("old_like", sop_v2_oldlike, "old_like_pct"),
        ("comment",  sop_v2_comment, "comment_pct"),
    ]:
        sub_y = test_df[sub].values
        rho = stats.spearmanr(dim_scores, sub_y).correlation
        print(f"    {dim_name}_score vs {sub}: ρ={rho:+.3f}")

    # ===== 3. critic v2 =====
    print("\n=== critic v2 (LGB,近 12 月窗口) ===")
    feat_cols = [c for c in feat.select_dtypes(include="number").columns if c != "aid"]
    df["hour"] = df["dt"].dt.hour
    df["month"] = df["dt"].dt.month
    df["dow"] = df["dt"].dt.dayofweek
    time_cols = ["year", "month", "hour", "dow", "itemidx"]
    acc_dummy = pd.get_dummies(df["account_slug"], prefix="acc").astype(int)
    X = pd.concat([df[feat_cols + time_cols].fillna(0).reset_index(drop=True),
                   acc_dummy.reset_index(drop=True)], axis=1)
    y = df["composite_pct"].values
    X_test = X.loc[test_mask].reset_index(drop=True)

    v2_mask = ((df["dt"] < pd.Timestamp("2026-01-01")) &
               (df["dt"] >= pd.Timestamp("2025-01-01"))).values
    X_v2 = X.loc[v2_mask].reset_index(drop=True)
    y_v2 = y[v2_mask]
    model_v2 = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.04,
                                 num_leaves=15, min_child_samples=20, verbose=-1,
                                 random_state=42)
    model_v2.fit(X_v2, y_v2)
    pred_critic_v2 = model_v2.predict(X_test)
    print(f"  ρ={stats.spearmanr(pred_critic_v2, y_test).correlation:+.3f}")

    # ===== 三方对比 =====
    print("\n" + "="*80)
    print("三方对比:SOP v1 vs SOP v2 vs critic v2")
    print("="*80)
    results = [
        all_metrics("SOP v1", sop_v1_scores, y_test),
        all_metrics("SOP v2", sop_v2_total, y_test),
        all_metrics("critic v2", pred_critic_v2, y_test),
    ]
    metric_names = {
        "r2": "R²", "rho": "Spearman ρ", "mae": "MAE(越低越好)",
        "top10_p": "Top 10% 精度", "top30_p": "Top 30% 精度",
        "bot10_p": "Bottom 10% 精度", "bin_acc": "分箱准确率",
        "pred_std": "预测 std",
    }
    rows = []
    for key, label in metric_names.items():
        vals = [r[key] for r in results]
        best_idx = int(np.argmin(vals)) if key == "mae" else int(np.argmax(vals))
        cells = []
        for i, v in enumerate(vals):
            if key in ["r2", "rho"]:
                cell = f"{v:+.3f}"
            elif key == "mae":
                cell = f"{v:.1f}"
            elif key in ["top10_p", "top30_p", "bot10_p", "bin_acc"]:
                cell = f"{v:.1%}"
            else:
                cell = f"{v:.1f}"
            if i == best_idx:
                cell = f"**{cell}** 🏆"
            cells.append(cell)
        rows.append([label, *cells, results[best_idx]["name"]])
        print(f"  {label:18s} {cells[0]:>22s} {cells[1]:>22s} {cells[2]:>22s}  ← {results[best_idx]['name']}")

    # ===== 5 篇爆款 + 5 篇扑街 的 SOP v2 反馈样例 =====
    test_df_with_pred = test_df.copy()
    test_df_with_pred["sop_v2"] = sop_v2_total
    test_df_with_pred["sop_v1"] = sop_v1_scores
    test_df_with_pred["critic_v2"] = pred_critic_v2

    top5 = test_df_with_pred.nlargest(5, "composite_pct").reset_index(drop=True)
    bot5 = test_df_with_pred.nsmallest(5, "composite_pct").reset_index(drop=True)

    def format_feedback(row_idx, src_df, label):
        row = src_df.iloc[row_idx]
        # 重新算一遍 SOP v2 拿完整反馈
        ser_row = row.copy()
        out = sop_score_v2(ser_row)
        title = (row.get("title") or "")[:40]
        lines = [f"### {label}{row_idx+1}: [{row['account_slug']}] {title}\n"]
        lines.append(f"- **真实 composite_pct**:{row['composite_pct']:.1f}")
        lines.append(f"- **SOP v2 总分**:{out['total_score']:.1f}(read={out['read_score']:.0f}, "
                     f"share={out['share_score']:.0f}, like={out['like_score']:.0f}, "
                     f"old_like={out['old_like_score']:.0f}, comment={out['comment_score']:.0f})")
        lines.append(f"- SOP v1={row['sop_v1']:.1f},critic v2={row['critic_v2']:.1f}\n")

        bonus_rules = [r for r in out["rules_triggered"] if r["type"] == "bonus"]
        penalty_rules = [r for r in out["rules_triggered"] if r["type"] == "penalty"]

        lines.append("**加分项**(做对的地方):")
        if bonus_rules:
            for r in bonus_rules[:6]:
                lines.append(f"  - [{r['dim']}] {r['rule']}({r['delta']:+})")
        else:
            lines.append("  (无)")
        lines.append("\n**扣分项**(踩坑):")
        if penalty_rules:
            for r in penalty_rules[:5]:
                lines.append(f"  - [{r['dim']}] {r['rule']}({r['delta']:+})")
        else:
            lines.append("  (无)")
        lines.append("\n**改进建议**(按预期收益排序):")
        if out["suggestions"]:
            for s in out["suggestions"][:5]:
                lines.append(f"  - [{s['dim']}] {s['action']}(预期 {s['expected_delta']:+})")
        else:
            lines.append("  (无)")
        lines.append("")
        return lines

    print("\n=== 5 篇爆款 + 5 篇扑街反馈样例 ===")
    sample_lines = ["## SOP v2 反馈样例:5 爆款 + 5 扑街\n"]
    sample_lines.append("### Top 5 爆款(真实 composite_pct 最高)\n")
    for i in range(min(5, len(top5))):
        sample_lines.extend(format_feedback(i, top5, "爆款 "))
    sample_lines.append("### Bottom 5 扑街(真实 composite_pct 最低)\n")
    for i in range(min(5, len(bot5))):
        sample_lines.extend(format_feedback(i, bot5, "扑街 "))

    # ===== 写报告 =====
    lines = ["# SOP v2 多维度规则系统:穿透测试报告\n"]
    lines.append(f"*生成时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    lines.append("## 测试设计\n")
    lines.append(f"- **测试集**:2026 H1 hold-out({len(test_df)} 篇,所有模型/规则训练时均未见过)")
    lines.append("- **target**:composite_pct = 0.40·read + 0.20·share + 0.15·like + 0.15·old_like + 0.10·comment")
    lines.append("- **SOP v1**:单维度规则,基于深挖 5-10 方向性结论,11 类规则")
    lines.append("- **SOP v2**(本次):5 维度规则(read/share/like/old_like/comment),feature 分配基于 pre-2026 训练集 ρ(feat, sub-target) 真实大小,**不在 hold-out 上调参**")
    lines.append("- **critic v2**:LGB 近 12 个月窗口训练(n=1383)\n")

    lines.append("## SOP v2 五维度设计\n")
    lines.append("总分公式(同 composite_pct 权重):")
    lines.append("```")
    lines.append("total = 0.40·read + 0.20·share + 0.15·like + 0.15·old_like + 0.10·comment")
    lines.append("```\n")
    lines.append("### Feature → 维度分配(基于 pre-2026 训练集 ρ vs 各 sub-target)\n")
    lines.append("| 维度 | 主要 features(ρ vs 该 sub-target) | ρ 出处 |")
    lines.append("|---|---|---|")
    lines.append("| read (40%) | t_chars / t_english_chars / 品牌词 / 封面色 / topic_hotness_30d (ρ=0.32) / current_event_words_in_title | brand_words.md + title_deep.md + cover_color_deep.md + topic_hotness 探针 |")
    lines.append("| share (20%) | b_chars (ρ=0.29) / b_para_avg_chars (ρ=0.30) / jb_lexical_diversity (ρ=-0.26) / tb_ratio (ρ=-0.24) / cover_brightness (ρ=0.32) / img_per_1k_chars / topic_hotness_90d (ρ=0.38) / comment_long_ratio | word_count_analysis + paragraph_structure + image_density |")
    lines.append("| like (15%) | topic_hotness_90d (ρ=0.42) / topic_hotness_30d (ρ=0.40) / action_verb_count (ρ=0.21) / opinion_strength_markers / cultural_meme / comment_ip_diversity / comment_avg_length | topic_hotness_dynamic.md + semantic_features.md |")
    lines.append("| old_like (15%) | controversy_markers / first_person_density (ρ=0.17) / jb_avg_word_len (ρ=-0.20) / comment_long_ratio (ρ=0.20) / cultural_meme | semantic_features.md + 探针 |")
    lines.append("| comment (10%) | comment_question_ratio (ρ=0.24) / comment_ip_diversity (ρ=0.23) / comment_sentiment_neg_ratio / personal_pronoun_in_title / interaction_call_in_title / first_person_density / opinion_strength_markers | comments_insights_v3.md + 探针 |\n")
    lines.append("*所有 ρ 数值在 pre-2026 训练集 n=2106 上计算,详见 `reports/_sop_v2_feature_rho.csv`*\n")

    lines.append("## 三方对比(2026 H1 hold-out)\n")
    lines.append("| 指标 | SOP v1 | SOP v2 | critic v2 | 最优 |")
    lines.append("|---|---|---|---|---|")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## SOP v2 各维度 vs 各 sub-target ρ(穿透诊断)\n")
    lines.append("(每个维度应该在自己对应的 sub-target 上 ρ 最强,验证维度切分有效性)\n")
    lines.append("| 维度评分 | vs read | vs share | vs like | vs old_like | vs comment |")
    lines.append("|---|---|---|---|---|---|")
    for dim_name, dim_scores in [
        ("read_score",     sop_v2_read),
        ("share_score",    sop_v2_share),
        ("like_score",     sop_v2_like),
        ("old_like_score", sop_v2_oldlike),
        ("comment_score",  sop_v2_comment),
    ]:
        cells = [dim_name]
        for sub in ["read_pct","share_pct","like_pct","old_like_pct","comment_pct"]:
            rho = stats.spearmanr(dim_scores, test_df[sub].values).correlation
            cells.append(f"{rho:+.3f}")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    lines.extend(sample_lines)

    # 结论
    sop_v1_res = results[0]
    sop_v2_res = results[1]
    critic_v2_res = results[2]
    lines.append("## 学术诚实结论\n")
    if sop_v2_res["rho"] >= 0.35:
        lines.append(f"- ✅ **SOP v2 ρ={sop_v2_res['rho']:.3f} ≥ 0.35 目标** — 多维度切分有效")
    else:
        lines.append(f"- 🟡 SOP v2 ρ={sop_v2_res['rho']:.3f} 未达 0.35 目标")
    delta = sop_v2_res["rho"] - sop_v1_res["rho"]
    lines.append(f"- SOP v2 ρ - SOP v1 ρ = {delta:+.3f}({'多维度提升' if delta > 0 else '多维度未提升'})")
    if sop_v2_res["rho"] > critic_v2_res["rho"]:
        lines.append(f"- ✅ SOP v2 ρ={sop_v2_res['rho']:.3f} > critic v2 ρ={critic_v2_res['rho']:.3f} — 规则系统胜过 ML")
    else:
        lines.append(f"- 🟡 SOP v2 ρ={sop_v2_res['rho']:.3f} < critic v2 ρ={critic_v2_res['rho']:.3f}")
    lines.append(f"\n**SOP v2 预测 std={sop_v2_res['pred_std']:.1f},真实 std={y_test.std():.1f}** — "
                 f"{'敢区分极端值' if sop_v2_res['pred_std'] > y_test.std() * 0.6 else '仍较保守'}\n")

    lines.append("## 反馈机制说明\n")
    lines.append("sop_score_v2(row) 输出结构:")
    lines.append("```python")
    lines.append("{")
    lines.append("  'total_score': float,")
    lines.append("  'read_score' / 'share_score' / 'like_score' / 'old_like_score' / 'comment_score': float,")
    lines.append("  'rules_triggered': [{'dim','rule','delta','type':'bonus|penalty'}, ...],")
    lines.append("  'suggestions': [{'dim','action','expected_delta'}, ...] # 按 expected_delta 降序")
    lines.append("}")
    lines.append("```")
    lines.append("- `rules_triggered`:让 writer 看到每个维度做对/做错的地方")
    lines.append("- `suggestions`:针对扣分项和未拿到的 bonus 给出可执行 action")
    lines.append("- 单条建议附带预期收益,writer 可按 ROI 取舍\n")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ 报告:{REPORT}")

    # dump 一份 result json 方便检查
    (ROOT / "reports" / "sop_v2_metrics.json").write_text(
        json.dumps({"SOP_v1": results[0], "SOP_v2": results[1], "critic_v2": results[2]},
                   indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
