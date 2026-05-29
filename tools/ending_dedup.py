"""
ending_dedup.py — 近期文章结尾双重去重(跟 opening_dedup 镜像)

Jobs syntactic 反复读检测 — 跟最近 ship 过的结尾不能太像。
两个指标互补:
  - token Jaccard:粗粒度,抓「同主题词集」重复
  - 5-gram 字面重叠:细粒度,抓「同句式 / 同公式」重复(如「愿你 / 颜文字收尾」)

阈值(跟 opening_dedup 一致):
  - token Jaccard ≤ 0.30
  - 字面 5-gram 重叠 ≤ 0.20

接口:
    from tools.ending_dedup import check_ending_overlap

    result = check_ending_overlap(article_full_text, max_age_days=30, max_n=5)
    # {
    #   "is_too_similar": bool,
    #   "max_jaccard": float,
    #   "max_ngram_overlap": float,
    #   "matched_draft": str | None,
    #   "matched_title": str | None,
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

# 复用 opening_dedup 的算子(避免重复造轮子)
sys.path.insert(0, str(Path(__file__).parent))
from opening_dedup import (  # noqa: E402
    tokenize,
    char_5grams,
    jaccard,
    overlap_ratio,
    JACCARD_THRESHOLD,
    NGRAM_OVERLAP_THRESHOLD,
)


ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
DRAFTS_DIR = ROOT / "output" / "drafts"


# ============================================================
# 抽末段(最后 H2 之后的所有段落,跟 ending_signal 一致)
# ============================================================

def extract_ending(text: str, max_chars: int = 400) -> str:
    """抽文章末段块(最后一个 H2 之后的所有内容,截到 max_chars)."""
    if not text:
        return ""
    # 剥 frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    matches = list(re.finditer(r"^##\s+\S", text, flags=re.MULTILINE))
    if matches:
        last_h2 = matches[-1]
        ending = text[last_h2.end():].strip()
    else:
        ending = text[-max_chars:].strip() if len(text) > max_chars else text.strip()
    return ending[:max_chars]


def _parse_draft_ending(draft_path: Path, max_chars: int = 400) -> dict:
    """解析 draft,返回 title + 末段."""
    try:
        text = draft_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    title = ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            for line in fm.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break
    ending = extract_ending(text, max_chars=max_chars)
    return {"title": title, "ending": ending}


# ============================================================
# 主入口
# ============================================================

def check_ending_overlap(
    article_full_text: str,
    max_age_days: int = 30,
    max_n_check: int = 5,
    drafts_dir: Optional[Path] = None,
    current_draft_path: Optional[Path] = None,
) -> dict:
    """检查新文章末段跟最近 ship 过的末段是否过于相似.

    Args:
        article_full_text: 新文章完整 markdown(脚本自动抽末段)
        max_age_days: 回看天数
        max_n_check: 最多比对几篇
        drafts_dir: 默认 output/drafts/

    Returns: 见模块顶部 docstring
    """
    if drafts_dir is None:
        drafts_dir = DRAFTS_DIR

    new_ending = extract_ending(article_full_text, max_chars=400)
    if not new_ending:
        return {
            "is_too_similar": False,
            "max_jaccard": 0.0,
            "max_ngram_overlap": 0.0,
            "matched_draft": None,
            "matched_title": None,
            "checked_n": 0,
            "redo_feedback": "无末段可比对",
        }

    if not drafts_dir.exists():
        return {
            "is_too_similar": False,
            "max_jaccard": 0.0,
            "max_ngram_overlap": 0.0,
            "matched_draft": None,
            "matched_title": None,
            "checked_n": 0,
            "redo_feedback": "(drafts/ 不存在,跳过)",
        }

    new_tokens = tokenize(new_ending)
    new_5grams = char_5grams(new_ending)

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

    max_jac = 0.0
    max_ngram = 0.0
    matched_path = None
    matched_title = None

    for mtime, p in drafts:
        parsed = _parse_draft_ending(p, max_chars=400)
        if not parsed or not parsed["ending"]:
            continue
        old_tokens = tokenize(parsed["ending"])
        old_5grams = char_5grams(parsed["ending"])
        jac = jaccard(new_tokens, old_tokens)
        # 5-gram 用 overlap(min 分母,对长度鲁棒)
        if new_5grams and old_5grams:
            ng = len(new_5grams & old_5grams) / min(len(new_5grams), len(old_5grams))
        else:
            ng = 0.0
        score = max(jac / JACCARD_THRESHOLD, ng / NGRAM_OVERLAP_THRESHOLD)
        prev_score = max(max_jac / JACCARD_THRESHOLD, max_ngram / NGRAM_OVERLAP_THRESHOLD)
        if score > prev_score:
            max_jac = jac
            max_ngram = ng
            matched_path = p
            matched_title = parsed["title"]

    is_too_sim = (max_jac > JACCARD_THRESHOLD) or (max_ngram > NGRAM_OVERLAP_THRESHOLD)

    feedback_parts = []
    if max_jac > JACCARD_THRESHOLD:
        feedback_parts.append(
            f"末段 token Jaccard {max_jac:.2f} > {JACCARD_THRESHOLD}(用词太像)"
        )
    if max_ngram > NGRAM_OVERLAP_THRESHOLD:
        feedback_parts.append(
            f"末段 5-gram 重叠 {max_ngram:.2f} > {NGRAM_OVERLAP_THRESHOLD}(句式太像 — 「不是 X 是 Y / 愿你也能 / 颜文字」可能撞了)"
        )
    if is_too_sim and matched_title:
        feedback_parts.append(f"跟「{matched_title}」结尾太像 — 换收束角度")
    if not feedback_parts:
        feedback_parts.append("跟近期结尾都不像,通过")

    return {
        "is_too_similar": is_too_sim,
        "max_jaccard": round(max_jac, 3),
        "max_ngram_overlap": round(max_ngram, 3),
        "matched_draft": matched_path.name if matched_path else None,
        "matched_title": matched_title,
        "checked_n": len(drafts),
        "redo_feedback": " | ".join(feedback_parts),
    }


# ============================================================
# CLI(测试用)
# ============================================================

def cli_demo():
    # 之前 ship 的两篇都用了「愿你也能 + 颜文字」公式,本 case 测能否抓到
    cases = [
        ("套同样「愿你也能 + 颜文字」公式",
         """## 收束

写到这里,笔者觉得 AI 时代每个人都该有自己的位置。

我们做不到所有事,但我们可以做好自己的小事。

亲爱的朋友,愿你也能在这个时代,找到属于你的小舞台。(*∩_∩*)"""),
        ("全新结尾公式(无重复)",
         """## 收束

事实摆在那:300 亿美元、4 个领投方、3 个月内估值翻 2.4 倍。这些数字是冷的。

但今天写到最后,我想留一个具体的问题给你:你最近 30 天里,有没有为别人做过一件 zero 经济回报的事?
如果有,记下来。这就是你的「9000 亿牌局之外」的资产。"""),
    ]
    for name, text in cases:
        print(f"\n=== {name} ===")
        r = check_ending_overlap(text, max_age_days=30, max_n_check=5)
        print(f"  is_too_similar: {r['is_too_similar']}")
        print(f"  max_jaccard: {r['max_jaccard']} (阈值 {JACCARD_THRESHOLD})")
        print(f"  max_ngram_overlap: {r['max_ngram_overlap']} (阈值 {NGRAM_OVERLAP_THRESHOLD})")
        print(f"  checked: {r['checked_n']} 篇")
        print(f"  matched: {r.get('matched_title')}")
        print(f"  feedback: {r['redo_feedback']}")


if __name__ == "__main__":
    cli_demo()
