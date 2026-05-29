"""
verify_audit.py — WRITE_AGENT.md Step 9 audit 闭环工具

Round 20 补的工具(SYSTEM_AUDIT_2026-05-25_EOD 报告指出 WRITE_AGENT 承诺但缺失)。

作用:
  扫 output/runs/gate_audit.jsonl,做 3 件事:
    1. 系统级周报(默认):pass 率 / 平均尝试次数 / force_skip 预警 / hot spot 排行
    2. 单 draft 审计(--draft <path>):某稿子的全部 gate 拦截历史
    3. Hot spot 排行(--hot-spots):跨所有 draft 最常缺的 step

跟 gate.py 配套 — gate.py 拦,verify_audit.py 复盘。

CLI:
  python tools/verify_audit.py                           # 全部周报
  python tools/verify_audit.py --days 7                  # 近 7 天周报
  python tools/verify_audit.py --draft output/drafts/xxx.md
  python tools/verify_audit.py --hot-spots
  python tools/verify_audit.py --json                    # JSON 输出(给 dashboard 用)
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
AUDIT_LOG = ROOT / "output" / "runs" / "gate_audit.jsonl"


# ============================================================
# 加载 + 过滤
# ============================================================

def load_audit(days: Optional[int] = None) -> list[dict]:
    """加载 gate_audit.jsonl,可按时间窗过滤."""
    if not AUDIT_LOG.exists():
        return []

    entries = []
    cutoff = None
    if days is not None:
        cutoff = datetime.now() - timedelta(days=days)

    with AUDIT_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            if cutoff is not None:
                try:
                    ts = datetime.fromisoformat(row.get("ts", ""))
                    if ts < cutoff:
                        continue
                except (ValueError, TypeError):
                    continue

            entries.append(row)

    return entries


# ============================================================
# 聚合
# ============================================================

def _normalize_draft_key(draft: str) -> str:
    """统一 draft 路径 key — resolve 失败时退化到 basename."""
    if not draft:
        return "<unknown>"
    try:
        return str(Path(draft).resolve()).lower()
    except Exception:
        return Path(draft).name.lower()


def aggregate_by_draft(entries: list[dict]) -> dict[str, dict]:
    """按 draft 聚合 — 拿每篇最新一次尝试 + 总尝试次数."""
    by_draft: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        draft = e.get("draft", "<unknown>")
        key = _normalize_draft_key(draft)
        by_draft[key].append(e)

    agg = {}
    for key, attempts in by_draft.items():
        # 按 ts 排序,取最后一次
        try:
            attempts.sort(key=lambda x: x.get("ts", ""))
        except Exception:
            pass
        latest = attempts[-1]
        # 用最后一次的 raw draft 字符串做展示名(便于人读)
        display = latest.get("draft", key)
        agg[display] = {
            "attempts": len(attempts),
            "latest_passed": latest.get("passed", False),
            "latest_ts": latest.get("ts", ""),
            "latest_missing": latest.get("missing", []),
            "latest_force_skip": latest.get("force_skip", False),
            "all_attempts": attempts,
        }
    return agg


def hot_spots(entries: list[dict]) -> Counter:
    """统计 missing step 的分布 — 哪个 step 最常被拦."""
    counter: Counter = Counter()
    for e in entries:
        for m in e.get("missing", []):
            # missing 字段是「缺 pass_flag:xxx=描述」或「⚠️ Fake-pass 风险:...」
            # 抽 step 名做 key
            key = _extract_step_key(m)
            counter[key] += 1
    return counter


def _extract_step_key(missing_line: str) -> str:
    """从 missing 行抽出可聚合的 step key.

    形如:
      "缺 pass_flag:cover_pass=Step 7-cover 封面生成" → "cover_pass"
      "⚠️  Fake-pass 风险:Step 6 Track A sop_v2_1 ... 缺 critic_a_real_run:true ..." → "critic_a_real_run"
      "缺 frontmatter 字段:slug" → "frontmatter:slug"
    """
    s = missing_line.strip()
    # fake-pass 行 — 抽 critic_X_real_run
    if "Fake-pass" in s or "critic_" in s and "_real_run" in s:
        for token in ("critic_a_real_run", "critic_b_real_run", "critic_c_real_run"):
            if token in s:
                return f"fake_pass:{token}"

    # pass_flag 行 — 抽 = 号前的 flag 名
    if "缺 pass_flag:" in s:
        try:
            tail = s.split("缺 pass_flag:", 1)[1]
            flag = tail.split("=", 1)[0].strip()
            return f"pass_flag:{flag}"
        except Exception:
            pass

    # frontmatter 字段
    if "缺 frontmatter 字段" in s:
        try:
            tail = s.split(":", 1)[1].strip()
            return f"frontmatter:{tail}"
        except Exception:
            pass

    # 其他 — 截前 40 字做 key
    return s[:40]


# ============================================================
# 渲染:周报
# ============================================================

def render_summary(entries: list[dict], scope: str = "all") -> str:
    """系统级周报."""
    if not entries:
        return f"(无 audit 记录 — scope={scope})"

    agg = aggregate_by_draft(entries)
    total_attempts = len(entries)
    total_drafts = len(agg)
    passed_drafts = sum(1 for d in agg.values() if d["latest_passed"])
    pass_rate = passed_drafts / total_drafts if total_drafts else 0.0
    avg_attempts = total_attempts / total_drafts if total_drafts else 0.0
    force_skip_drafts = [
        d for d, info in agg.items() if info["latest_force_skip"]
    ]

    hot = hot_spots(entries)
    top_hot = hot.most_common(10)

    # 未 ship 的 draft(最新一次 failed)
    pending = [
        (d, info) for d, info in agg.items()
        if not info["latest_passed"]
    ]
    pending.sort(key=lambda x: x[1]["latest_ts"], reverse=True)

    lines = []
    lines.append("=" * 64)
    lines.append(f"verify_audit.py — gate_audit 复盘({scope})")
    lines.append("=" * 64)
    lines.append("")
    lines.append(f"总尝试: {total_attempts}  |  draft 数: {total_drafts}  |  pass率: {pass_rate:.1%}")
    lines.append(f"平均尝试/draft: {avg_attempts:.2f}")
    if force_skip_drafts:
        lines.append(f"⚠️  force_skip 触发 draft: {len(force_skip_drafts)}(必须人工 review)")
        for d in force_skip_drafts[:5]:
            lines.append(f"    - {Path(d).name}")
    lines.append("")

    lines.append("-" * 64)
    lines.append("Hot Spots(最常被拦的 step, Top 10)")
    lines.append("-" * 64)
    if not top_hot:
        lines.append("  (无)")
    else:
        for key, count in top_hot:
            lines.append(f"  {count:>3}x  {key}")
    lines.append("")

    lines.append("-" * 64)
    lines.append(f"未 ship draft(最新一次 fail, {len(pending)} 篇)")
    lines.append("-" * 64)
    if not pending:
        lines.append("  ✅ 全部 ship")
    else:
        for draft, info in pending[:10]:
            name = Path(draft).name
            lines.append(f"  [{info['attempts']}次尝试] {name}")
            for m in info["latest_missing"][:3]:
                lines.append(f"      ↳ {m[:80]}")
            if len(info["latest_missing"]) > 3:
                lines.append(f"      ... 还有 {len(info['latest_missing']) - 3} 条")
    lines.append("")
    lines.append("=" * 64)
    return "\n".join(lines)


# ============================================================
# 渲染:单 draft 详细审计
# ============================================================

def render_draft_audit(entries: list[dict], draft_path: str) -> str:
    """单 draft 详细审计."""
    # 路径 normalize — 都用绝对路径比
    target = str(Path(draft_path).resolve()).lower()

    matched = []
    for e in entries:
        d = e.get("draft", "")
        try:
            if str(Path(d).resolve()).lower() == target:
                matched.append(e)
        except Exception:
            # 模糊匹配 — 看 basename
            if Path(d).name.lower() == Path(draft_path).name.lower():
                matched.append(e)

    if not matched:
        return f"(未找到 draft 的 audit 记录: {draft_path})"

    matched.sort(key=lambda x: x.get("ts", ""))

    lines = []
    lines.append("=" * 64)
    lines.append(f"draft 审计: {Path(draft_path).name}")
    lines.append("=" * 64)
    lines.append(f"总尝试: {len(matched)}")
    final = matched[-1]
    final_status = "✅ PASS" if final.get("passed") else "❌ FAIL"
    lines.append(f"最新状态: {final_status} @ {final.get('ts', '')}")
    if final.get("force_skip"):
        lines.append("⚠️  force_skip — 该 draft 触发兜底拦截")
    lines.append("")

    for i, e in enumerate(matched, 1):
        status = "✅" if e.get("passed") else "❌"
        lines.append(f"[{i}/{len(matched)}] {status} {e.get('ts', '')}")
        missing = e.get("missing", [])
        if missing:
            lines.append(f"    missing_count={e.get('missing_count', 0)}")
            for m in missing:
                lines.append(f"    - {m[:100]}")
        lines.append("")

    lines.append("=" * 64)
    return "\n".join(lines)


# ============================================================
# 渲染:hot spots 单独输出
# ============================================================

def render_hot_spots(entries: list[dict]) -> str:
    """hot spot 排行(详细版,全部不截断)."""
    hot = hot_spots(entries)
    if not hot:
        return "(无 missing 数据)"

    lines = []
    lines.append("=" * 64)
    lines.append("Hot Spots — 全部 step 拦截频次")
    lines.append("=" * 64)
    total = sum(hot.values())
    lines.append(f"总 missing 次数: {total}")
    lines.append("")
    for key, count in hot.most_common():
        pct = count / total * 100
        lines.append(f"  {count:>4}x  ({pct:5.1f}%)  {key}")
    lines.append("")
    lines.append("=" * 64)
    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="gate_audit 复盘工具 — WRITE_AGENT Step 9 闭环"
    )
    parser.add_argument("--days", type=int, default=None,
                        help="只看最近 N 天(默认全部)")
    parser.add_argument("--draft", type=str, default=None,
                        help="审计单篇 draft 路径")
    parser.add_argument("--hot-spots", action="store_true",
                        help="只输出 hot spot 排行")
    parser.add_argument("--json", action="store_true",
                        help="输出 JSON(给 dashboard 用)")
    args = parser.parse_args()

    entries = load_audit(days=args.days)
    scope = f"近 {args.days} 天" if args.days else "全部历史"

    if args.json:
        agg = aggregate_by_draft(entries)
        hot = hot_spots(entries)
        out = {
            "scope": scope,
            "total_attempts": len(entries),
            "total_drafts": len(agg),
            "passed_drafts": sum(1 for d in agg.values() if d["latest_passed"]),
            "force_skip_drafts": [
                Path(d).name for d, info in agg.items() if info["latest_force_skip"]
            ],
            "hot_spots": dict(hot.most_common(20)),
            "pending": [
                {
                    "draft": Path(d).name,
                    "attempts": info["attempts"],
                    "latest_missing": info["latest_missing"],
                }
                for d, info in agg.items()
                if not info["latest_passed"]
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if args.draft:
        print(render_draft_audit(entries, args.draft))
        return

    if args.hot_spots:
        print(render_hot_spots(entries))
        return

    # 默认:周报
    print(render_summary(entries, scope))


if __name__ == "__main__":
    main()
