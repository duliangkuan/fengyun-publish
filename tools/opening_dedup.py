"""
opening_dedup.py — 近期文章开头双重去重 + de-facto 文本算子 base 库

**Round 19 调研结论(2026-05-25)**:
本模块同时承担两个角色 —
  ① 业务:opening harness 30 天回看 dedup(check_opening_overlap)
  ② **base 库**:导出 tokenize / char_5grams / jaccard / overlap_ratio
     被 ending_dedup / title_dedup 直接 `from opening_dedup import` 复用
     cover_dedup 比 template_id 不需要 token 算子(语义不同)
     event_dedup 用 frozenset fingerprint 是独立语义,合理不共用

Musk × Jobs Round 19 P1-2 调研结论:抽 `_lib/text_dedup.py` 物理收益 = 0,
反而增加 import 路径复杂度。**保持现状**,只加本文档注明双角色。

—————————————————————————————————————

Jobs 视角:跟最近 ship 过的开头 token + 字面 5-gram 都不能太像。
两个指标互补:
  - token Jaccard:粗粒度,抓「同主题词集」重复
  - 5-gram 字面重叠:细粒度,抓「同句式 / 同公式」重复

阈值:
  - token Jaccard ≤ 0.30(粗去重)
  - 字面 5-gram 重叠 ≤ 0.20(精去重)
  任一超阈值 → 触发 redo

接口:
    from tools.opening_dedup import check_opening_overlap

    result = check_opening_overlap(new_first_200, max_age_days=30, max_n=5)
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


ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
DRAFTS_DIR = ROOT / "output" / "drafts"

JACCARD_THRESHOLD = 0.30
NGRAM_OVERLAP_THRESHOLD = 0.20
NGRAM_SIZE = 5


# ============================================================
# Tokenize(粗粒度)
# ============================================================

CN_STOPWORDS = {
    "的", "了", "是", "和", "在", "我", "你", "他", "她", "它",
    "我们", "你们", "他们", "这", "那", "什么", "怎么", "也",
    "都", "就", "还", "又", "或", "也是", "就是", "可以", "可能",
    "应该", "需要", "要", "用", "给", "把", "被", "对", "因为",
    "所以", "比如", "例如", "一些", "一个", "一种", "已经", "会",
}

EN_STOPWORDS = {
    "the", "is", "a", "an", "of", "in", "on", "to", "for", "by",
    "and", "or", "but", "this", "that", "as", "be", "are", "was",
}


def tokenize(text: str) -> set[str]:
    """提取 2-4 字中文 token + 英文专名,去停用词."""
    tokens = set()
    text = text.lower()
    for w in re.findall(r"[a-z][a-z0-9-]+", text):
        if len(w) >= 3 and w not in EN_STOPWORDS:
            tokens.add(w)
    for block in re.findall(r"[一-鿿]+", text):
        if 2 <= len(block) <= 4 and block not in CN_STOPWORDS:
            tokens.add(block)
        elif len(block) > 4:
            for n in (3, 2):
                for i in range(len(block) - n + 1):
                    sub = block[i:i + n]
                    if sub not in CN_STOPWORDS and len(sub) == n:
                        tokens.add(sub)
    return tokens


# ============================================================
# 5-gram 字面重叠
# ============================================================

def char_5grams(text: str) -> set[str]:
    """5-gram 字面切片(去标点 / 空白,中英文都参与)."""
    clean = re.sub(r"[\s\W_]+", "", text.lower())
    if len(clean) < NGRAM_SIZE:
        return set()
    return {clean[i:i + NGRAM_SIZE] for i in range(len(clean) - NGRAM_SIZE + 1)}


# ============================================================
# 相似度算子
# ============================================================

def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def overlap_ratio(a: set, b: set) -> float:
    """5-gram 重叠率 = |a ∩ b| / min(|a|, |b|)

    跟 Jaccard 的差别:overlap 用 min,Jaccard 用 union。
    overlap 对长度差异鲁棒(适合「新短旧长」场景)。
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


# ============================================================
# 解析 draft frontmatter + 抽前 N 字
# ============================================================

def _parse_draft_opening(draft_path: Path, max_chars: int = 200) -> dict:
    """解析 draft,返回 frontmatter title + 前 max_chars 字开头."""
    try:
        text = draft_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    title = ""
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            body = parts[2]
            for line in fm.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break
    # 抽 body 前 max_chars(剥前导空行)
    body = body.lstrip()
    opening = body[:max_chars]
    return {"title": title, "opening": opening}


# ============================================================
# 主入口
# ============================================================

def check_opening_overlap(
    new_opening: str,
    max_age_days: int = 30,
    max_n_check: int = 5,
    drafts_dir: Optional[Path] = None,
    current_draft_path: Optional[Path] = None,
) -> dict:
    """检查 new_opening 跟最近 ship 过的开头是否过于相似.

    Args:
        new_opening: 新草稿开头(传前 200 字)
        max_age_days: 回看天数
        max_n_check: 最多比对几篇(按 mtime 倒序)
        drafts_dir: 默认 output/drafts/
        current_draft_path: 正在 ship 的草稿路径(Bug 4 修复:排除自身,
                            避免 self-match Jaccard 1.0)

    Returns:
        {
          "is_too_similar": bool,
          "max_jaccard": float,           # 最高 Jaccard 命中
          "max_ngram_overlap": float,     # 最高 5-gram overlap 命中
          "matched_draft": str | None,    # 命中的文件
          "matched_title": str | None,    # 命中的标题
          "checked_n": int,
          "redo_feedback": str,           # 给 writer 改稿反馈
        }
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
            "checked_n": 0,
            "redo_feedback": "(drafts/ 不存在,跳过)",
        }

    new_tokens = tokenize(new_opening)
    new_5grams = char_5grams(new_opening)

    # Bug 4 修复:解析 current_draft_path 用于排除自身
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
    matched_jac = None  # 命中时的 jaccard
    matched_ngram = None  # 命中时的 ngram overlap

    for mtime, p in drafts:
        parsed = _parse_draft_opening(p, max_chars=200)
        if not parsed:
            continue
        old_opening = parsed["opening"]
        if not old_opening:
            continue

        old_tokens = tokenize(old_opening)
        old_5grams = char_5grams(old_opening)
        jac = jaccard(new_tokens, old_tokens)
        ng = overlap_ratio(new_5grams, old_5grams)

        # 用「综合超阈值程度」比较找最相似的
        score = max(jac / JACCARD_THRESHOLD, ng / NGRAM_OVERLAP_THRESHOLD)
        if score > max(max_jac / JACCARD_THRESHOLD, max_ngram / NGRAM_OVERLAP_THRESHOLD):
            max_jac = jac
            max_ngram = ng
            matched_path = p
            matched_title = parsed["title"]
            matched_jac = jac
            matched_ngram = ng

    is_too_sim = (max_jac > JACCARD_THRESHOLD) or (max_ngram > NGRAM_OVERLAP_THRESHOLD)

    feedback_parts = []
    if max_jac > JACCARD_THRESHOLD:
        feedback_parts.append(
            f"token Jaccard {max_jac:.2f} > {JACCARD_THRESHOLD}(用词太像)"
        )
    if max_ngram > NGRAM_OVERLAP_THRESHOLD:
        feedback_parts.append(
            f"5-gram 重叠 {max_ngram:.2f} > {NGRAM_OVERLAP_THRESHOLD}(句式太像)"
        )
    if is_too_sim and matched_title:
        feedback_parts.append(f"跟「{matched_title}」开头太像 — 换公式 / 换角度切入")
    if not feedback_parts:
        feedback_parts.append("跟近期开头都不像,通过")

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
    cases = [
        # case 1: 跟最近的 Anthropic 9000 亿开头几乎一样(应该 too_similar)
        ("克隆 Anthropic 9000 亿开头",
         "前几天晚上,我看到一条消息。Anthropic 这家公司,正在完成一轮 300 亿美元的融资。"
         "融完之后估值 9000 亿,反超了 OpenAI。我把这两个数字念了一遍,又念了一遍。"),
        # case 2: 完全不同的开头(应该 pass)
        ("全新公式",
         "想象一下:你是斯坦福一个 PhD 学生,刚刚收到 Anthropic 的实习 offer。"
         "签字之前,导师让你看一组数据 — 那 4 个跨账号 ρ 验证的结果。"),
        # case 3: 公式相同但事件不同
        ("套同样开头公式但讲不同事件",
         "前几天,看到一条新闻,我读了三遍。OpenAI 宣布 GPT-6 上线。"
         "我把这个消息念了一遍,又念了一遍。"),
    ]
    for name, text in cases:
        print(f"\n=== {name} ===")
        r = check_opening_overlap(text, max_age_days=30, max_n_check=5)
        print(f"  is_too_similar: {r['is_too_similar']}")
        print(f"  max_jaccard: {r['max_jaccard']} (阈值 {JACCARD_THRESHOLD})")
        print(f"  max_ngram_overlap: {r['max_ngram_overlap']} (阈值 {NGRAM_OVERLAP_THRESHOLD})")
        print(f"  checked: {r['checked_n']} 篇")
        print(f"  matched: {r.get('matched_title')}")
        print(f"  feedback: {r['redo_feedback']}")


if __name__ == "__main__":
    cli_demo()
