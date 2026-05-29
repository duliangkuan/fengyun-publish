"""Compute ρ of every feature vs each sub-target on TRAIN ONLY (pre-2026).
Used to anchor SOP v2 dimension assignment with real data rather than guesswork.
"""
from __future__ import annotations
import sys, sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")

feat = pd.read_parquet(ROOT / "features.parquet")
targ = pd.read_parquet(ROOT / "targets.parquet")
cmt = pd.read_parquet(ROOT / "comment_features.parquet")
top = pd.read_parquet(ROOT / "topic_hotness.parquet")
sem = pd.read_parquet(ROOT / "semantic_features.parquet")

con = sqlite3.connect(ROOT / "db.sqlite")
meta = pd.read_sql_query("SELECT aid, account_slug AS acc_m, title, create_time AS ct, itemidx FROM articles", con)

df = feat.merge(targ, on="aid", suffixes=("", "_t"))
df = df.merge(meta, on="aid")
df["create_time"] = df["ct"]
df = df.merge(cmt, on="aid", how="left", suffixes=("", "_cf"))
df = df.merge(top, on="aid", how="left", suffixes=("", "_tf"))
df = df.merge(sem, on="aid", how="left", suffixes=("", "_sf"))

df["composite_pct"] = (0.40*df["read_pct"] + 0.15*df["like_pct"] + 0.15*df["old_like_pct"]
                       + 0.20*df["share_pct"] + 0.10*df["comment_pct"])

df["dt"] = pd.to_datetime(df["create_time"], unit="s")
df = df.dropna(subset=["composite_pct"]).reset_index(drop=True)

train = df[df["dt"] < pd.Timestamp("2026-01-01")].reset_index(drop=True)
print(f"Train size (pre-2026): {len(train)}")

subtargets = ["read_pct", "share_pct", "like_pct", "old_like_pct", "comment_pct", "composite_pct"]

# build candidate features (numeric only, drop targets and ids)
ban = set(["aid", "create_time", "hour", "dow", "itemidx", "is_headline"] + subtargets +
          ["readNum","likeNum","oldLikeNum","shareNum","commentNum",
           "log_readNum","log_likeNum","log_oldLikeNum","log_shareNum","log_commentNum",
           "read_residual","like_residual","old_like_residual","share_residual","comment_residual",
           "read_capped", "topic_id"])

cand = []
for c in train.columns:
    if c in ban: continue
    if train[c].dtype.kind not in "biufc": continue
    if train[c].nunique(dropna=True) < 3: continue
    cand.append(c)

rows = []
for c in cand:
    x = train[c].astype(float)
    rec = {"feat": c, "n_nonnull": int(x.notna().sum())}
    for t in subtargets:
        y = train[t].astype(float)
        mask = x.notna() & y.notna()
        if mask.sum() < 30:
            rec[t] = np.nan
        else:
            rho, _ = stats.spearmanr(x[mask], y[mask])
            rec[t] = rho
    rec["best_sub"] = max(["read_pct","share_pct","like_pct","old_like_pct","comment_pct"],
                         key=lambda k: abs(rec[k]) if not pd.isna(rec[k]) else 0)
    rec["best_abs"] = abs(rec[rec["best_sub"]]) if not pd.isna(rec[rec["best_sub"]]) else 0
    rows.append(rec)

out = pd.DataFrame(rows).sort_values("best_abs", ascending=False)
out.to_csv(ROOT / "reports" / "_sop_v2_feature_rho.csv", index=False, encoding="utf-8")

# print summary
print("\nTop 40 by best-sub |ρ|:")
print(out.head(40).to_string(index=False))
print("\n--- assignments by best_sub ---")
for sub in ["read_pct","share_pct","like_pct","old_like_pct","comment_pct"]:
    sub_df = out[out["best_sub"]==sub].head(15)
    print(f"\n[{sub}] top 15 (best_sub == {sub}):")
    print(sub_df[["feat", sub, "best_abs"]].to_string(index=False))
