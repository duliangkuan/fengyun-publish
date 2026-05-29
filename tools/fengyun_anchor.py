"""
fengyun_anchor.py — 风云 IP style_match anchor bootstrap(Round 7 P0,2026-05-24)

用风云自己已 ship 的 draft 作 anchor pool,计算 style match score。
不再等用户提供"代表作"。

工作流:
  1. 扫 output/drafts/*.md(风云 fengyun-writer 出的稿)
  2. 对每篇算字符 n-gram 集合(轻量,不依赖外部库)
  3. 对每篇算"跟其它已 ship 的平均 Jaccard 相似度"
  4. 归一映射到 PHASE1 训练集 style_match_score 范围 [-0.221, 0.087]
  5. 输出 fengyun_anchor.parquet(aid + style_match_score)
  6. sop_v2_1._init_parquets 自动 merge 加载

CLI:
  python tools/fengyun_anchor.py rebuild              # 重建 anchor pool + 写 parquet
  python tools/fengyun_anchor.py score <draft.md>     # 单文件查 anchor score(不写 parquet)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
DRAFTS_DIR = ROOT / "output" / "drafts"
PARQUET_OUT = ROOT / "fengyun_anchor.parquet"
META_OUT = ROOT / "fengyun_anchor_meta.json"

# PHASE1 训练集 style_match_score min/max(从 sop_v2_1.py 抄)
PHASE1_MIN = -0.221321
PHASE1_MAX = 0.087404
PHASE1_RANGE = PHASE1_MAX - PHASE1_MIN


def _read_draft(path: Path) -> str:
    """读 draft,剥 frontmatter."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text


def _char_ngrams(text: str, n: int = 3) -> set:
    """字符 n-gram 集合(轻量,不依赖 sklearn / jieba)."""
    text = "".join(text.split())  # 去空白
    if len(text) < n:
        return set()
    return set(text[i:i + n] for i in range(len(text) - n + 1))


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def collect_anchors(exclude: Path | None = None) -> List[Path]:
    """扫所有 draft,选规模合理的(50+ 字符).

    Round 7 监督 review 修复:同一 slug(去 -v\\d+ 后缀)只保留 mtime 最新一个。
    避免同篇多版本(anthropic-mythos-v2/v3/v4)互相高 Jaccard 拉偏分布。
    """
    import re
    if not DRAFTS_DIR.exists():
        return []
    cands = []
    for p in sorted(DRAFTS_DIR.glob("*.md")):
        if exclude and p.resolve() == exclude.resolve():
            continue
        body = _read_draft(p)
        if len(body) >= 50:
            cands.append(p)

    # 去重:同 slug(去 -v\d+ / -revise-brief.* 后缀)只保留 mtime 最新一个
    by_slug = {}
    for p in cands:
        stem = p.stem
        slug = re.sub(r"-v\d+$", "", stem)
        slug = re.sub(r"-revise-brief.*$", "", slug)
        slug = re.sub(r"-LEGACY$", "", slug)
        mtime = p.stat().st_mtime
        if slug not in by_slug or by_slug[slug][1] < mtime:
            by_slug[slug] = (p, mtime)
    return sorted([p for p, _ in by_slug.values()])


def _rescale_dynamic(raw_scores: List[float]) -> List[float]:
    """
    动态校准:根据当前 anchor pool 的 Jaccard 分布,线性映射到 PHASE1 范围.

    理由:不同主题稿子的字符 Jaccard 本来就低(0.05-0.10),硬阈值
    映射会全部触发 PHASE1 下限 clip,等于退化为「无 anchor」状态.
    改用 z-score 风格的动态映射,让 pool 内**相对相似度**驱动 score 区分.

    映射:
      - pool 内 raw_jaccard min → PHASE1_MIN(-0.221)
      - pool 内 raw_jaccard max → PHASE1_MAX(0.087)
      - 中间稿子按线性插值分布

    边界情况:
      - pool size < 2 → 返回原值(无映射)
      - 所有 score 相同 → 全部映射到 PHASE1 中位
    """
    if len(raw_scores) < 2:
        return raw_scores

    s_min = min(raw_scores)
    s_max = max(raw_scores)
    target_range = PHASE1_MAX - PHASE1_MIN

    if s_max - s_min < 1e-9:
        mid = (PHASE1_MIN + PHASE1_MAX) / 2
        return [mid] * len(raw_scores)

    return [
        PHASE1_MIN + (s - s_min) / (s_max - s_min) * target_range
        for s in raw_scores
    ]


def _rescale_to_phase1(avg_jaccard: float, pool_stats: dict | None = None) -> float:
    """单个 score 的兜底映射(score_single 用,无 pool 上下文时).

    Round 7 监督修复:删掉硬编码 0.067 / 0.045 魔法常量.
    改为强制从 fengyun_anchor_meta.json 读 raw_jaccard_range,
    跟 rebuild 的 dynamic rescale 同源,避免分叉.
    """
    # 优先用传入的 pool_stats
    if pool_stats and "raw_min" in pool_stats and "raw_max" in pool_stats:
        s_min, s_max = pool_stats["raw_min"], pool_stats["raw_max"]
    else:
        # 从 meta JSON 读最新 rebuild 的范围
        if not META_OUT.exists():
            # meta 不存在 = 未 rebuild 过 → 没法映射,直接返回中位
            return (PHASE1_MIN + PHASE1_MAX) / 2
        try:
            meta = json.loads(META_OUT.read_text(encoding="utf-8"))
            rj = meta.get("raw_jaccard_range", {})
            s_min = rj.get("min")
            s_max = rj.get("max")
            if s_min is None or s_max is None:
                return (PHASE1_MIN + PHASE1_MAX) / 2
        except Exception:
            return (PHASE1_MIN + PHASE1_MAX) / 2

    if s_max - s_min < 1e-9:
        return (PHASE1_MIN + PHASE1_MAX) / 2
    scaled = PHASE1_MIN + (avg_jaccard - s_min) / (s_max - s_min) * (PHASE1_MAX - PHASE1_MIN)
    return max(PHASE1_MIN, min(PHASE1_MAX, scaled))


def compute_anchor_scores() -> pd.DataFrame:
    """对每篇 anchor 算 vs 其它的平均 Jaccard,归一映射到 PHASE1 范围."""
    anchors = collect_anchors()
    if len(anchors) < 2:
        print(f"⚠️  anchor pool 太小 ({len(anchors)} 篇),至少需要 2 篇")
        return pd.DataFrame(columns=["aid", "style_match_score"])

    ngrams = {p.stem: _char_ngrams(_read_draft(p)) for p in anchors}

    # 先算所有 raw_jaccard
    aids = []
    raw_jaccards = []
    n_anchors_list = []
    for stem, gram in ngrams.items():
        others = [g for s, g in ngrams.items() if s != stem]
        if not others:
            continue
        avg_jacc = sum(_jaccard(gram, o) for o in others) / len(others)
        aids.append(stem)
        raw_jaccards.append(avg_jacc)
        n_anchors_list.append(len(others))

    # 动态校准 → PHASE1 范围
    scaled_scores = _rescale_dynamic(raw_jaccards)

    rows = [{
        "aid": aid,
        "style_match_score": scaled,
        "raw_avg_jaccard": jacc,
        "n_anchors": n,
    } for aid, scaled, jacc, n in zip(aids, scaled_scores, raw_jaccards, n_anchors_list)]

    df = pd.DataFrame(rows)
    return df


def rebuild():
    df = compute_anchor_scores()
    if df.empty:
        print("anchor pool 太小,parquet 不写")
        return

    # 只保留 aid + style_match_score 写入 parquet(sop_v2_1 需要的列)
    out_df = df[["aid", "style_match_score"]].copy()
    out_df.to_parquet(PARQUET_OUT, index=False)

    meta = {
        "rebuild_at": pd.Timestamp.now().isoformat(),
        "anchor_count": len(df),
        "drafts": df["aid"].tolist(),
        "score_range": {
            "min": float(df["style_match_score"].min()),
            "max": float(df["style_match_score"].max()),
            "mean": float(df["style_match_score"].mean()),
        },
        "raw_jaccard_range": {
            "min": float(df["raw_avg_jaccard"].min()),
            "max": float(df["raw_avg_jaccard"].max()),
            "mean": float(df["raw_avg_jaccard"].mean()),
        },
    }
    META_OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ fengyun_anchor.parquet: {len(df)} rows")
    print(f"  style_match range [{df['style_match_score'].min():.4f}, "
          f"{df['style_match_score'].max():.4f}], mean={df['style_match_score'].mean():.4f}")
    print(f"  raw Jaccard range [{df['raw_avg_jaccard'].min():.3f}, "
          f"{df['raw_avg_jaccard'].max():.3f}], mean={df['raw_avg_jaccard'].mean():.3f}")
    print(f"  drafts: {len(df)} 篇 — {df['aid'].tolist()[:3]}{'...' if len(df) > 3 else ''}")


def score_single(draft_path: Path) -> float | None:
    """单文件 score(临时算,不写 parquet)."""
    if not draft_path.exists():
        print(f"⚠️  {draft_path} not found")
        return None
    anchors = collect_anchors(exclude=draft_path)
    if not anchors:
        print(f"⚠️  no anchors available (excluded current)")
        return None
    target_gram = _char_ngrams(_read_draft(draft_path))
    other_grams = [_char_ngrams(_read_draft(p)) for p in anchors]
    avg_jacc = sum(_jaccard(target_gram, og) for og in other_grams) / len(other_grams)
    scaled = _rescale_to_phase1(avg_jacc)
    return scaled


def main():
    args = sys.argv[1:]
    if not args:
        print("用法:")
        print("  python tools/fengyun_anchor.py rebuild")
        print("  python tools/fengyun_anchor.py score <draft.md>")
        sys.exit(1)

    if args[0] == "rebuild":
        rebuild()
    elif args[0] == "score" and len(args) >= 2:
        score = score_single(Path(args[1]))
        if score is not None:
            print(f"style_match_score: {score:.4f}")
            print(f"(PHASE1 range: [{PHASE1_MIN:.4f}, {PHASE1_MAX:.4f}])")
    else:
        print(f"未知命令: {args[0]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
