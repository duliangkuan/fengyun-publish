"""
cover_dedup.py — 近期封面模板去重(Round 15 · 2026-05-24)

Musk × Jobs 沙盒共识(详见 reports/round15_cover_diversity.md):
  - 撞型根因 = generate_cover_by_template.classify() 是 stateless 的
  - 物理下限 = 最近 7 天每模板至多用 1 次,7 模板 × 周 = 容量充足
  - 修法 = 加 history-aware gate,而不是加 21 个 composition variant

接口:
    from tools.cover_dedup import check_cover_template_overlap

    result = check_cover_template_overlap(
        new_template_id="T2_research",
        new_draft_text=draft_text,        # 用于算次优模板的 routing fallback
        max_age_days=7,
    )
    # {
    #   "is_too_similar": bool,
    #   "matched_draft": str | None,
    #   "matched_title": str | None,
    #   "matched_date": str | None,
    #   "alternative_template": str,       # 次优模板(关键词第二高分,跳过已用过)
    #   "history": [(date, draft_name, template_id), ...],   # 最近 N 天封面历史
    #   "redo_feedback": str,
    # }

跟 opening_dedup / ending_dedup 的对位:
  - opening/ending dedup 比的是「文本相似度」(token Jaccard + 5-gram)
  - cover dedup 比的是「模板使用历史」(同 template_id 在 7 天内复用即视为撞型)
  - 都是 N-day 回看 + 单触发 redo + 给 alternative

Fallback 链(读历史模板的策略):
  1. 优先读 draft frontmatter 里的 `cover_template_id`(generate_cover_by_template.py 未来会写)
  2. 没有则反向跑 classify(draft 前 500 字)推断 — 不准但够用
"""
from __future__ import annotations
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 复用 generate_cover_by_template 的路由表(避免重复造轮子)
sys.path.insert(0, str(Path(__file__).parent))
from generate_cover_by_template import (  # noqa: E402
    CATEGORY_RULES,
    DEFAULT_TEMPLATE,
    classify,
)


ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
DRAFTS_DIR = ROOT / "output" / "drafts"
IMAGES_DIR = ROOT / "output" / "images"

# 默认窗口:7 天(比 opening/ending 的 30 天短,因为容量 7/周已足够)
DEFAULT_MAX_AGE_DAYS = 7


# ============================================================
# 解析 draft frontmatter
# ============================================================

def _parse_draft_meta(draft_path: Path) -> dict:
    """读 draft frontmatter,返回 title / cover_template_id(若有) / 前 500 字 body."""
    try:
        text = draft_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    title = ""
    cover_template_id = ""
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            body = parts[2]
            for line in fm.splitlines():
                line = line.rstrip()
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("cover_template_id:") or line.startswith("cover_template:"):
                    cover_template_id = line.split(":", 1)[1].strip().strip('"').strip("'")
    return {
        "title": title,
        "cover_template_id": cover_template_id,
        "body_head": body.lstrip()[:500],
    }


def _infer_template(parsed: dict) -> str:
    """优先 frontmatter,fallback 跑 classify."""
    if parsed.get("cover_template_id"):
        return parsed["cover_template_id"]
    head = parsed.get("body_head", "")
    if not head:
        return DEFAULT_TEMPLATE
    return classify(head)


# ============================================================
# 次优模板(关键词命中分数第二高,跳过已用过的)
# ============================================================

def _rank_templates(text: str) -> list[tuple[str, int]]:
    """对文本算每个模板的命中关键词数,返回排序后的 [(tid, score), ...]."""
    text_lower = text.lower()
    scores = []
    for tid, keywords in CATEGORY_RULES.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        scores.append((tid, score))
    # 高分在前;分数为 0 的模板放最后(但仍保留,以防全 0 时也能选)
    scores.sort(key=lambda x: -x[1])
    return scores


def pick_alternative(
    new_text: str,
    skip_templates: set[str],
) -> str:
    """选次优模板:命中分数最高 + 不在 skip_templates 里.

    Args:
        new_text: 新草稿文本(用于算关键词分)
        skip_templates: 应该跳过的模板(最近用过的)

    Returns: 次优 template_id
    """
    ranked = _rank_templates(new_text)
    # 跳过 skip 集合
    for tid, score in ranked:
        if tid in skip_templates:
            continue
        # 即使 score=0 也接受 — 总比撞型好
        return tid
    # 全部模板都被 skip 了(7 天用了 7 个模板?极端情况)
    # 退回 default
    return DEFAULT_TEMPLATE


# ============================================================
# 主入口
# ============================================================

def check_cover_template_overlap(
    new_template_id: str,
    new_draft_text: str = "",
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    max_n_check: int = 10,
    drafts_dir: Optional[Path] = None,
    current_draft_path: Optional[Path] = None,
) -> dict:
    """检查新封面模板跟最近 ship 过的封面是否撞型.

    Args:
        new_template_id: 新文章打算用的模板(从 classify 出来)
        new_draft_text: 新文章前 500 字(用于算 alternative_template)
        max_age_days: 回看天数(默认 7)
        max_n_check: 最多比对几篇
        drafts_dir: 默认 output/drafts/

    Returns:
        见模块顶部 docstring.
    """
    if drafts_dir is None:
        drafts_dir = DRAFTS_DIR

    if not drafts_dir.exists():
        return {
            "is_too_similar": False,
            "matched_draft": None,
            "matched_title": None,
            "matched_date": None,
            "alternative_template": new_template_id,
            "history": [],
            "checked_n": 0,
            "redo_feedback": "(drafts/ 不存在,跳过)",
        }

    # Bug 4 修复(2026-05-25 Round 17):解析 current_draft_path 排除自身
    self_resolved = None
    if current_draft_path is not None:
        try:
            self_resolved = Path(current_draft_path).resolve()
        except Exception:
            self_resolved = None

    cutoff = datetime.now() - timedelta(days=max_age_days)
    drafts = []
    for p in drafts_dir.glob("*.md"):
        # Bug 4 修复:排除自身
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

    history = []
    used_templates = set()
    matched_path = None
    matched_title = None
    matched_date = None

    for mtime, p in drafts:
        parsed = _parse_draft_meta(p)
        if not parsed:
            continue
        old_tid = _infer_template(parsed)
        date_str = mtime.strftime("%Y-%m-%d")
        history.append({
            "date": date_str,
            "draft": p.name,
            "title": parsed.get("title", ""),
            "template_id": old_tid,
        })
        used_templates.add(old_tid)
        # 记录第一个命中(最新的)
        if old_tid == new_template_id and matched_path is None:
            matched_path = p
            matched_title = parsed.get("title", "")
            matched_date = date_str

    is_too_sim = new_template_id in used_templates

    # 算 alternative
    if is_too_sim and new_draft_text:
        # 跳过新模板 + 最近 3 天用过的所有模板(防连续撞)
        recent_3d_used = set()
        cutoff_3d = datetime.now() - timedelta(days=3)
        for mtime, p in drafts:
            if mtime >= cutoff_3d:
                parsed = _parse_draft_meta(p)
                if parsed:
                    recent_3d_used.add(_infer_template(parsed))
        alternative = pick_alternative(new_draft_text, skip_templates=recent_3d_used | {new_template_id})
    else:
        alternative = new_template_id

    # 反馈
    if is_too_sim:
        feedback = (
            f"封面模板 {new_template_id} 已在 {matched_date}「{matched_title}」用过 — "
            f"建议换 {alternative}(关键词第二高分 + 7 天内未用)"
        )
    else:
        feedback = f"封面模板 {new_template_id} 最近 {max_age_days} 天未用过,通过"

    return {
        "is_too_similar": is_too_sim,
        "matched_draft": matched_path.name if matched_path else None,
        "matched_title": matched_title,
        "matched_date": matched_date,
        "alternative_template": alternative,
        "history": history,
        "checked_n": len(drafts),
        "redo_feedback": feedback,
    }


# ============================================================
# CLI(测试用)
# ============================================================

def cli_demo():
    """直接测当前 drafts/ 里的真实历史."""
    print("\n=== 测试 case 1: 模拟新文打算用 T2_research(应该撞型,5/24 已用) ===")
    r = check_cover_template_overlap(
        new_template_id="T2_research",
        new_draft_text="今天调研一下 Karpathy 离开 OpenAI 加入 Anthropic 的事件,深度解析。",
    )
    print(f"  is_too_similar: {r['is_too_similar']}")
    print(f"  matched: {r['matched_date']} 「{r['matched_title']}」")
    print(f"  alternative: {r['alternative_template']}")
    print(f"  feedback: {r['redo_feedback']}")
    print(f"  history (最近 {r['checked_n']} 篇):")
    for h in r["history"]:
        print(f"    - {h['date']} [{h['template_id']}] {h['title'][:30]}")

    print("\n=== 测试 case 2: 模拟新文用 T6_portrait_concept(应该未撞,近期没用过) ===")
    r = check_cover_template_overlap(
        new_template_id="T6_portrait_concept",
        new_draft_text="独家专访 Anthropic CEO Dario Amodei 谈下一代模型。",
    )
    print(f"  is_too_similar: {r['is_too_similar']}")
    print(f"  matched: {r.get('matched_date')}")
    print(f"  alternative: {r['alternative_template']}")
    print(f"  feedback: {r['redo_feedback']}")


if __name__ == "__main__":
    cli_demo()
