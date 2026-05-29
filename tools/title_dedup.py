"""
title_dedup.py — 近期标题双重去重(Round 16 · 2026-05-25)

镜像 opening_dedup / ending_dedup 架构。标题撞型问题:
  - 风云近 6 篇标题用过的句式 / 钩子 / 品牌词组合不能反复用
  - 比开头 / 结尾 dedup 更严 — 因为标题只有 20-40 字,撞型识别更敏感

阈值(标题文本短,Jaccard 阈值要降):
  - token Jaccard ≤ 0.40(比 opening 的 0.30 略宽,因为标题短词重叠率天然高)
  - 字面 5-gram 重叠 ≤ 0.25(同理略宽)
  - 钩子类型 7 天内不能撞 2 次(从 PHASE1 7 钩子分类)

接口:
    from tools.title_dedup import check_title_overlap

    result = check_title_overlap(new_title, hook_type="颠覆认知", max_age_days=14, max_n=10)
    # {
    #   "is_too_similar": bool,
    #   "max_jaccard": float,
    #   "max_ngram_overlap": float,
    #   "matched_draft": str | None,
    #   "matched_title": str | None,
    #   "hook_clash": bool,         # 钩子类型 7 天内已用过 ≥2 次
    #   "recent_hooks": list[str],
    #   "redo_feedback": str,
    # }
"""
from __future__ import annotations
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 复用 opening_dedup 的算子
sys.path.insert(0, str(Path(__file__).parent))
from opening_dedup import (  # noqa: E402
    tokenize,
    char_5grams,
    jaccard,
    overlap_ratio,
)


ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
DRAFTS_DIR = ROOT / "output" / "drafts"

# 标题阈值比开头略宽(标题字数少,词重叠天然高)
TITLE_JACCARD_THRESHOLD = 0.40
TITLE_NGRAM_OVERLAP_THRESHOLD = 0.25
HOOK_CLASH_WINDOW_DAYS = 7        # 钩子撞型窗口
HOOK_CLASH_MAX_REPEAT = 1         # 7 天内同钩子最多用 1 次


# ============================================================
# 解析 draft frontmatter
# ============================================================

def _parse_draft_title(draft_path: Path) -> dict:
    """读 draft frontmatter,返回 title + hook_type(若有标记)."""
    try:
        text = draft_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    title = ""
    hook_type = ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                line = line.rstrip()
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("hook_type:") or line.startswith("title_hook:"):
                    hook_type = line.split(":", 1)[1].strip().strip('"').strip("'")
    return {"title": title, "hook_type": hook_type}


def _infer_hook_type_from_title(title: str) -> Optional[str]:
    """无 frontmatter 标记时,反推钩子类型(用 title_signal 的 HOOK_PATTERNS)."""
    try:
        from title_signal import HOOK_PATTERNS
        for hook_name, patterns in HOOK_PATTERNS.items():
            for pat in patterns:
                try:
                    if re.search(pat, title):
                        return hook_name
                except re.error:
                    continue
        return None
    except ImportError:
        return None


# ============================================================
# 主入口
# ============================================================

def check_title_overlap(
    new_title: str,
    hook_type: Optional[str] = None,
    max_age_days: int = 14,
    max_n_check: int = 10,
    drafts_dir: Optional[Path] = None,
    current_draft_path: Optional[Path] = None,
) -> dict:
    """检查新标题跟最近 ship 过的标题是否过于相似.

    Args:
        new_title: 新标题文本
        hook_type: 新标题命中的钩子类型(可选,有助于钩子撞型检测)
        max_age_days: 回看天数(默认 14 天,比 opening 30 天短)
        max_n_check: 最多比对几篇
        drafts_dir: 默认 output/drafts/

    Returns: 见模块顶部 docstring.
    """
    if drafts_dir is None:
        drafts_dir = DRAFTS_DIR

    if not drafts_dir.exists():
        return {
            "is_too_similar": False,
            "max_jaccard": 0.0,
            "max_ngram_overlap": 0.0,
            "matched_draft": None,
            "matched_title": None,
            "hook_clash": False,
            "recent_hooks": [],
            "checked_n": 0,
            "redo_feedback": "(drafts/ 不存在,跳过)",
        }

    new_tokens = tokenize(new_title)
    new_5grams = char_5grams(new_title)

    # Bug 4 修复(2026-05-25 Round 17):解析 current_draft_path 排除自身
    self_resolved = None
    if current_draft_path is not None:
        try:
            self_resolved = Path(current_draft_path).resolve()
        except Exception:
            self_resolved = None

    # 扫描最近 N 天 drafts
    cutoff = datetime.now() - timedelta(days=max_age_days)
    hook_cutoff = datetime.now() - timedelta(days=HOOK_CLASH_WINDOW_DAYS)
    drafts = []
    for p in drafts_dir.glob("*.md"):
        # Bug 4 修复:排除自身(避免 self-match Jaccard 1.0)
        if self_resolved is not None:
            try:
                if p.resolve() == self_resolved:
                    continue
            except Exception:
                pass
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
            if mtime >= cutoff:
                drafts.append((mtime, p))
        except Exception:
            continue
    drafts.sort(key=lambda x: -x[0].timestamp())
    drafts = drafts[:max_n_check]

    max_jac = 0.0
    max_ngram = 0.0
    matched_path = None
    matched_title = None
    recent_hooks_7d = []  # 7 天内已用过的钩子

    for mtime, p in drafts:
        parsed = _parse_draft_title(p)
        if not parsed or not parsed.get("title"):
            continue
        old_title = parsed["title"]
        old_hook = parsed.get("hook_type") or _infer_hook_type_from_title(old_title)

        # 钩子撞型检测(7 天窗口)
        if mtime >= hook_cutoff and old_hook:
            recent_hooks_7d.append(old_hook)

        # token / 5-gram 相似度
        old_tokens = tokenize(old_title)
        old_5grams = char_5grams(old_title)
        jac = jaccard(new_tokens, old_tokens)
        ng = overlap_ratio(new_5grams, old_5grams) if (new_5grams and old_5grams) else 0.0

        score = max(
            jac / TITLE_JACCARD_THRESHOLD,
            ng / TITLE_NGRAM_OVERLAP_THRESHOLD,
        )
        prev_score = max(
            max_jac / TITLE_JACCARD_THRESHOLD,
            max_ngram / TITLE_NGRAM_OVERLAP_THRESHOLD,
        )
        if score > prev_score:
            max_jac = jac
            max_ngram = ng
            matched_path = p
            matched_title = old_title

    # 钩子撞型判断
    if hook_type and recent_hooks_7d:
        same_hook_count = sum(1 for h in recent_hooks_7d if h == hook_type)
        hook_clash = same_hook_count > HOOK_CLASH_MAX_REPEAT
    else:
        hook_clash = False

    is_too_sim = (
        (max_jac > TITLE_JACCARD_THRESHOLD)
        or (max_ngram > TITLE_NGRAM_OVERLAP_THRESHOLD)
        or hook_clash
    )

    feedback_parts = []
    if max_jac > TITLE_JACCARD_THRESHOLD:
        feedback_parts.append(
            f"标题 token Jaccard {max_jac:.2f} > {TITLE_JACCARD_THRESHOLD}(用词太像)"
        )
    if max_ngram > TITLE_NGRAM_OVERLAP_THRESHOLD:
        feedback_parts.append(
            f"标题 5-gram 重叠 {max_ngram:.2f} > {TITLE_NGRAM_OVERLAP_THRESHOLD}(句式太像)"
        )
    if hook_clash:
        feedback_parts.append(
            f"钩子类型「{hook_type}」7 天内已用 {sum(1 for h in recent_hooks_7d if h == hook_type)} 次 — 换另一种钩子"
        )
    if matched_title and (max_jac > TITLE_JACCARD_THRESHOLD or max_ngram > TITLE_NGRAM_OVERLAP_THRESHOLD):
        feedback_parts.append(f"跟「{matched_title}」标题太像 — 换公式 / 换角度切入")
    if not feedback_parts:
        feedback_parts.append("跟近期标题都不像,通过")

    return {
        "is_too_similar": is_too_sim,
        "max_jaccard": round(max_jac, 3),
        "max_ngram_overlap": round(max_ngram, 3),
        "matched_draft": matched_path.name if matched_path else None,
        "matched_title": matched_title,
        "hook_clash": hook_clash,
        "recent_hooks": recent_hooks_7d,
        "checked_n": len(drafts),
        "redo_feedback": " | ".join(feedback_parts),
    }


# ============================================================
# CLI(测试用)
# ============================================================

def cli_demo():
    cases = [
        # case 1: 跟 5/24 Karpathy 标题极像(同样「X 转身的那笔账」公式)
        ("克隆 Karpathy 公式", "Karpathy 转身的那笔账", None),
        # case 2: 完全不同标题
        ("全新公式", "别再用提示词去 AI 味了,方向就是错的", "颠覆认知"),
        # case 3: 主题撞但句式不同
        ("Anthropic 主题但不同句式", "Anthropic 的下一个十年:从 Claude 到 ASI", "未来预言"),
        # case 4: 钩子撞型(假设 7 天内已多次用「颠覆认知」)
        ("颠覆认知钩子撞", "为什么我看空 OpenAI 股票", "颠覆认知"),
    ]
    for name, title, hook in cases:
        print(f"\n=== {name} ===")
        r = check_title_overlap(title, hook_type=hook, max_age_days=14, max_n_check=10)
        print(f"  is_too_similar: {r['is_too_similar']}")
        print(f"  max_jaccard: {r['max_jaccard']} (阈值 {TITLE_JACCARD_THRESHOLD})")
        print(f"  max_ngram_overlap: {r['max_ngram_overlap']} (阈值 {TITLE_NGRAM_OVERLAP_THRESHOLD})")
        print(f"  hook_clash: {r['hook_clash']}  recent_hooks: {r['recent_hooks']}")
        print(f"  checked: {r['checked_n']} 篇")
        print(f"  matched: {r.get('matched_title')}")
        print(f"  feedback: {r['redo_feedback']}")


if __name__ == "__main__":
    cli_demo()
