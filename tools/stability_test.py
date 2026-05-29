"""
stability_test.py — LLM critic 评分稳定性测试工具

测试 huashu-perspective 和 content-judge 同一文章评 3 次会不会飘。
(Round 24:Track C critic skill 从 fengyun-self 重命名为 content-judge)
因为无法真实 invoke skill,工具分两个 Mode:

  Mode 1 (--generate): 生成填空表格 markdown + jsonl 模板
  Mode 2 (--analyze):  读已回填 jsonl 算指标 + 报告
  Mode 3 (单文):       --draft <path> + --generate

指标:
  verdict_consistency  — 3 次 verdict 一致率(0.0~1.0)
  reasoning_jaccard    — 3 次理由的 token Jaccard 均值

判定:
  ≥ 0.95 → PASS
  0.80~0.95 → WARN
  < 0.80  → FAIL
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 路径常量 ───────────────────────────────────────────────────
ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
HUASHU_CORPUS = ROOT / "corpus" / "raw" / "huashu"
DRAFTS_DIR    = ROOT / "output" / "drafts"
STABILITY_DIR = ROOT / "output" / "stability"

CRITICS = ["huashu-perspective", "content-judge"]
N_RUNS  = 3

PASS_THRESHOLD = 0.95
WARN_THRESHOLD = 0.80


# ── 从 opening_dedup 复用算子 ─────────────────────────────────
try:
    sys.path.insert(0, str(ROOT / "tools"))
    from opening_dedup import tokenize, jaccard  # type: ignore
except ImportError:
    # fallback: 内联简化版(保证独立可跑)
    def tokenize(text: str) -> set:  # type: ignore
        tokens: set = set()
        text = text.lower()
        for w in re.findall(r"[a-z][a-z0-9\-]+", text):
            if len(w) >= 3:
                tokens.add(w)
        for block in re.findall(r"[一-鿿]+", text):
            for n in (3, 2):
                for i in range(len(block) - n + 1):
                    tokens.add(block[i:i + n])
        return tokens

    def jaccard(a: set, b: set) -> float:  # type: ignore
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)


# ── 辅助函数 ──────────────────────────────────────────────────

def _slug(path: Path) -> str:
    """文件名 → 安全 slug(≤40 字符)."""
    name = path.stem
    safe = re.sub(r"[^\w一-鿿\-]", "_", name)
    return safe[:40]


def _read_title(path: Path) -> str:
    """从 markdown frontmatter 读 title,或用文件名."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return path.stem
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if line.startswith("title:"):
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
    return path.stem[:60]


def _excerpt(path: Path, n: int = 150) -> str:
    """抽文章前 n 字作为预览."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].lstrip()
            return body[:n].replace("\n", " ")
    return text.lstrip()[:n].replace("\n", " ")


def verdict_consistency(verdicts: list[str]) -> float:
    """3 次 verdict 一致率.空字符串不计。"""
    filled = [v.strip() for v in verdicts if v.strip()]
    if len(filled) < 2:
        return 1.0  # 数据不足,暂不扣分
    counts: dict[str, int] = {}
    for v in filled:
        counts[v] = counts.get(v, 0) + 1
    majority = max(counts.values())
    return majority / len(filled)


def reasoning_avg_jaccard(reasonings: list[str]) -> float:
    """3 次理由的平均 pairwise token Jaccard."""
    filled = [r.strip() for r in reasonings if r.strip()]
    if len(filled) < 2:
        return 1.0
    token_sets = [tokenize(r) for r in filled]
    pairs = []
    for i in range(len(token_sets)):
        for j in range(i + 1, len(token_sets)):
            pairs.append(jaccard(token_sets[i], token_sets[j]))
    return sum(pairs) / len(pairs) if pairs else 1.0


def grade(score: float) -> str:
    if score >= PASS_THRESHOLD:
        return "PASS"
    if score >= WARN_THRESHOLD:
        return "WARN"
    return "FAIL"


# ── Mode 1: 生成填空模板 ──────────────────────────────────────

def generate_templates(article_paths: list[Path]) -> None:
    STABILITY_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for art in article_paths:
        slug   = _slug(art)
        title  = _read_title(art)
        excerpt = _excerpt(art, 150)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # ── jsonl 结构(每行一条 run 记录) ────────────────────
        jsonl_path = STABILITY_DIR / f"{slug}-stability.jsonl"
        md_path    = STABILITY_DIR / f"{slug}-stability.md"

        # 初始化 jsonl(若不存在)
        if not jsonl_path.exists():
            records = []
            for critic in CRITICS:
                for run_id in range(1, N_RUNS + 1):
                    records.append({
                        "slug":     slug,
                        "title":    title,
                        "critic":   critic,
                        "run_id":   run_id,
                        "verdict":  "",       # 待回填: "ship" / "不ship"
                        "reasoning": "",      # 待回填: 理由全文
                    })
            jsonl_path.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
                encoding="utf-8",
            )

        # ── 生成 markdown 填空表格 ────────────────────────────
        rows_huashu   = _table_rows("huashu-perspective")
        rows_fengyun  = _table_rows("content-judge")

        md = f"""# Stability Test — {title}

**生成时间**: {now_str}
**文章文件**: `{art.name}`

> **使用说明**: 用 huashu-perspective 和 content-judge skill 各跑 3 次,
> 把 verdict(ship/不ship)和理由填入下方表格对应行,
> 然后运行 `python tools/stability_test.py --analyze output/stability/` 算指标。

## 文章摘要

> {excerpt}…

---

## huashu-perspective × 3 runs

| run | verdict | reasoning(关键词即可) |
|-----|---------|----------------------|
{rows_huashu}

## content-judge × 3 runs

| run | verdict | reasoning(关键词即可) |
|-----|---------|----------------------|
{rows_fengyun}

---

## 回填 jsonl

填完上面表格后,把对应数据更新到:
`output/stability/{slug}-stability.jsonl`

每行格式:
```json
{{"slug": "{slug}", "critic": "huashu-perspective", "run_id": 1, "verdict": "ship", "reasoning": "..."}}
```
"""
        md_path.write_text(md, encoding="utf-8")
        generated.append(md_path)
        print(f"  [生成] {md_path.name}  ({jsonl_path.name})")

    print(f"\n共生成 {len(generated)} 个 stability template → {STABILITY_DIR}")


def _table_rows(critic: str) -> str:
    return "\n".join(f"| {i} |  |  |" for i in range(1, N_RUNS + 1))


# ── Mode 2: 读 jsonl 算指标 ───────────────────────────────────

def analyze_dir(stability_dir: Path) -> None:
    jsonl_files = sorted(stability_dir.glob("*-stability.jsonl"))
    if not jsonl_files:
        print(f"[WARN] 在 {stability_dir} 未找到 *-stability.jsonl 文件")
        return

    all_results: list[dict] = []

    for jf in jsonl_files:
        records = []
        for line in jf.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if not records:
            continue

        slug  = records[0].get("slug", jf.stem)
        title = records[0].get("title", slug)

        article_result = {"slug": slug, "title": title, "critics": {}}

        for critic in CRITICS:
            runs = [r for r in records if r.get("critic") == critic]
            verdicts   = [r.get("verdict", "")   for r in runs]
            reasonings = [r.get("reasoning", "") for r in runs]

            vc  = verdict_consistency(verdicts)
            rj  = reasoning_avg_jaccard(reasonings)
            article_result["critics"][critic] = {
                "verdicts":            verdicts,
                "verdict_consistency": round(vc, 3),
                "reasoning_jaccard":   round(rj, 3),
                "grade":               grade(min(vc, rj)),
            }

        all_results.append(article_result)

    _print_report(all_results)


def _print_report(results: list[dict]) -> None:
    print("\n" + "=" * 60)
    print("  Stability Test Report")
    print("=" * 60)

    total_critics = 0
    fail_count    = 0
    warn_count    = 0

    for art in results:
        print(f"\n【{art['title'][:40]}】")
        for critic, info in art["critics"].items():
            vc  = info["verdict_consistency"]
            rj  = info["reasoning_jaccard"]
            g   = info["grade"]
            vs  = " / ".join(v or "(空)" for v in info["verdicts"])
            print(f"  {critic:25s}  verdict一致率={vc:.3f}  reasoning_jaccard={rj:.3f}  [{g}]")
            print(f"    verdicts: {vs}")
            total_critics += 1
            if g == "FAIL":
                fail_count += 1
            elif g == "WARN":
                warn_count += 1

    print("\n" + "-" * 60)
    pass_count = total_critics - fail_count - warn_count
    print(f"总计: {total_critics} critic×文章组合")
    print(f"  PASS={pass_count}  WARN={warn_count}  FAIL={fail_count}")

    if fail_count > 0:
        overall = "FAIL — 稳定性不足,循环不可靠,需调 prompt"
    elif warn_count > 0:
        overall = "WARN — 部分组合飘移,建议增加 run 次数或固定 temperature"
    else:
        overall = "PASS — 稳定性达标,循环可靠"

    print(f"\n总体判定: {overall}")
    print("=" * 60)


# ── 选文章 ────────────────────────────────────────────────────

def pick_articles(corpus: Optional[str], n: int, draft: Optional[Path]) -> list[Path]:
    if draft:
        return [draft]
    if corpus == "huashu":
        corpus_dir = HUASHU_CORPUS
    else:
        corpus_dir = DRAFTS_DIR
    if not corpus_dir.exists():
        print(f"[ERROR] corpus 目录不存在: {corpus_dir}")
        sys.exit(1)

    files = sorted(corpus_dir.glob("*.md"))
    import random
    random.seed(42)
    sample = random.sample(files, min(n, len(files)))
    return sample


# ── CLI ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="LLM critic 评分稳定性测试")
    parser.add_argument("--generate", action="store_true",
                        help="Mode 1: 生成填空 markdown + jsonl 模板")
    parser.add_argument("--analyze", type=Path, metavar="DIR", default=None,
                        help="Mode 2: 读已回填 jsonl 算指标,传 output/stability/ 目录")
    parser.add_argument("--draft", type=Path, default=None,
                        help="Mode 3: 单文路径(搭配 --generate)")
    parser.add_argument("--corpus", type=str, default="huashu",
                        help="语料库名称: huashu | drafts (default: huashu)")
    parser.add_argument("--n", type=int, default=5,
                        help="随机抽取文章数量 (default: 5)")
    args = parser.parse_args()

    if args.analyze:
        analyze_dir(args.analyze)
    elif args.generate:
        articles = pick_articles(args.corpus, args.n, args.draft)
        generate_templates(articles)
    else:
        parser.print_help()
        print("\n[提示] 请指定 --generate 或 --analyze <dir>")
        sys.exit(1)


if __name__ == "__main__":
    main()
