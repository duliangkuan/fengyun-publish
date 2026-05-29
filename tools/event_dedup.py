"""
event_dedup.py — 同一事件 7 天去重(Round 11,2026-05-24)

设计原则:
- 不做「同一主题去重」(PHASE1 数据反对:Anthropic 系连写都在涨)
- 只做「同一事件去重」(7 天内同一新闻不重发)
- 事件指纹算法:title + summary 去数字 → 抽取核心名词 → frozenset Jaccard

接口:
    from tools.event_dedup import check_event_dedup, event_fingerprint

    item = {"title": "Anthropic 9000 亿融资", "summary": "..."}
    result = check_event_dedup(item, days=7)
    # {is_duplicate: bool, matched_draft: str | None, jaccard: float}

实现:
- 扫 D:/Dev/ai-wechat-pipeline/output/drafts/ 最近 7 天 mtime 的 *.md
- 解析每篇 frontmatter title + digest
- 跟新 item 算事件指纹的 Jaccard 相似度
- 阈值 >= 0.4 算同一事件

Why 0.4 阈值:
- "Anthropic 9000 亿融资" vs "Anthropic 300 亿轮估值反超 OpenAI" → Jaccard ~0.5(同事件,该去重)
- "Anthropic 9000 亿融资" vs "Karpathy 加入 Anthropic" → Jaccard ~0.2(同主题不同事件,不去重)
- "Anthropic 9000 亿融资" vs "DeepSeek R2 测评" → Jaccard ~0.0(完全不同)
"""
from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
DRAFTS_DIR = ROOT / "output" / "drafts"
# Round 22 #2:加查已发布存档(runs/*.json 含 media_id)
RUNS_DIR = ROOT / "output" / "runs"


# ============================================================
# 事件指纹生成
# ============================================================

def event_fingerprint(title: str, summary: str = "") -> frozenset[str]:
    """生成事件指纹 — 抽核心名词,去数字 + 单位.

    返回 frozenset of tokens(可用 Jaccard 算相似度).

    Examples:
        >>> event_fingerprint("Anthropic 9000 亿融资反超 OpenAI")
        frozenset({'anthropic', 'openai', '融资', '反超'})

        >>> event_fingerprint("Karpathy 加入 Anthropic 做 pre-training")
        frozenset({'karpathy', 'anthropic', '加入', 'pre-training'})
    """
    text = f"{title} {summary}".lower()

    # 去常见数字+单位组合
    text = re.sub(r"\d+(?:[.,]\d+)?\s*(亿|万亿|千亿|百亿|万|千|%|％|美元|元)", "", text)
    text = re.sub(r"\d+(?:[.,]\d+)?", "", text)  # 剩下的纯数字也去

    # 去标点
    text = re.sub(r"[,。!?;:'\"《》「」『』()()【】、—\-…—]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # 抽 token:中文 2-4 字整块 + 英文专名(不滑窗,避免碎片膨胀 union)
    tokens = set()
    # 英文:连续字母数字(允许 - 连接,如 "claude-3")
    for m in re.findall(r"[a-z][a-z0-9-]+", text):
        if len(m) >= 2 and m not in STOPWORDS_EN:
            tokens.add(m)
    # 中文:2-4 字整块(不滑窗,降噪)
    # 切分用空格/标点,得到「干净的」名词候选
    for block in re.findall(r"[一-鿿]+", text):
        if 2 <= len(block) <= 4 and block not in STOPWORDS_CN:
            tokens.add(block)
        elif 5 <= len(block) <= 8:
            # 长块拆 2-3 字滑窗但只保留没在停用词的(降噪)
            # 长度 5-8 才滑窗,避免「Anthropic 即将完成」这种被切爆
            for n in (3, 2):
                for i in range(len(block) - n + 1):
                    word = block[i:i + n]
                    if word not in STOPWORDS_CN and len(word) == n:
                        tokens.add(word)

    return frozenset(tokens)


# 中英文停用词(频次 token 不该参与去重)
STOPWORDS_EN = {
    "the", "is", "a", "an", "of", "in", "on", "at", "to", "for", "by",
    "and", "or", "but", "this", "that", "these", "those", "with", "as",
    "be", "been", "are", "was", "were", "from", "up", "out", "down",
}

STOPWORDS_CN = {
    "的", "了", "是", "和", "在", "我", "你", "他", "她", "它", "我们",
    "你们", "他们", "这", "那", "这个", "那个", "这些", "那些", "什么",
    "怎么", "怎样", "如何", "为什么", "因为", "所以", "但是", "不过",
    "然而", "可是", "也", "都", "就", "还", "也是", "就是", "还是",
    "只是", "不是", "或者", "或", "和", "跟", "与", "及", "对", "对于",
    "关于", "可以", "可能", "也许", "应该", "需要", "想要", "要", "用",
    "用来", "比如", "例如", "等等", "什么的", "之类", "一样", "一些",
    "一个", "一种", "一直", "一定", "一下", "什么时候", "已经", "正在",
    "还在", "将", "将要", "把", "被", "让", "使", "给", "给我", "我们的",
    "你的", "我的", "他的",
    # 风云 voice 高频 lived stake 词(几乎每篇都出现,不算事件特征)
    # 加进停用词,避免「一个普通人怎么用 AI」误判为跟其它「普通人 + AI」文章同事件
    "普通人", "一个普通人", "我们这一代", "这一代人", "我们这代",
    "站在", "位置", "时代", "年轻人", "朋友", "笔者",
    "这个时代", "这件事", "这种感觉", "这些事", "这条消息",
    "想法", "感觉", "感受", "心里", "突然", "原来", "其实",
    "AI", "ai",  # 选题里几乎必然出现,不是去重特征
}


# ============================================================
# Jaccard 相似度
# ============================================================

def jaccard_similarity(a: frozenset, b: frozenset) -> float:
    """Jaccard 相似度: |a ∩ b| / |a ∪ b|."""
    if not a or not b:
        return 0.0
    intersect = len(a & b)
    union = len(a | b)
    return intersect / union if union > 0 else 0.0


def containment(a: frozenset, b: frozenset) -> float:
    """Containment(不对称含量比):|a ∩ b| / |a|.

    比 Jaccard 更鲁棒于「新候选短,旧 draft 长」的场景。
    问的是:「新候选的 token 里,有多少比例在旧 draft 里也出现过」。
    """
    if not a:
        return 0.0
    return len(a & b) / len(a)


def event_similarity(a: frozenset, b: frozenset) -> float:
    """事件相似度 = max(Jaccard, containment_a_in_b).

    用 max:对短候选用 containment,对相似长度文本用 Jaccard。
    """
    return max(jaccard_similarity(a, b), containment(a, b))


# ============================================================
# 主入口:check_event_dedup
# ============================================================

def _parse_draft_frontmatter(draft_path: Path) -> dict:
    """解析 draft 顶部 frontmatter,返回 {title, digest, slug, date}."""
    try:
        text = draft_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            meta[k] = v
    return meta


def _scan_published_titles(runs_dir: Path, days: int) -> list[dict]:
    """Round 22 #2:扫已发布存档(runs/*.json 含 media_id 字段或 title 字段).

    Return: list of {title, summary, source, mtime}
    """
    if not runs_dir.exists():
        return []
    cutoff = datetime.now() - timedelta(days=days)
    items: list[dict] = []
    for jp in runs_dir.glob("*.json"):
        try:
            mtime = datetime.fromtimestamp(jp.stat().st_mtime)
        except Exception:
            continue
        if mtime < cutoff:
            continue
        try:
            with jp.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        # 提 title:支持几种历史 schema(顶层 title / step8 / slug)
        title = (data.get("title") or data.get("topic")
                 or data.get("slug") or jp.stem)
        summary = data.get("digest") or data.get("summary") or ""
        # 只把真推过的 run 算 published(含 media_id 字段)
        has_media = bool(
            data.get("media_id")
            or data.get("step8_media_id")
            or (isinstance(data.get("step8"), dict)
                and data.get("step8", {}).get("media_id"))
        )
        if not has_media:
            continue
        items.append({
            "title": str(title),
            "summary": str(summary),
            "source": jp.name,
            "mtime": mtime,
        })
    return items


def check_event_dedup(
    new_item: dict,
    days: int = 7,
    jaccard_threshold: float = 0.40,
    drafts_dir: Optional[Path] = None,
    current_draft_path: Optional[Path] = None,
    include_published: bool = True,
) -> dict:
    """检查 new_item 在最近 days 天 ship 过的草稿里是否有同事件.

    Args:
        new_item: 候选 item,dict 含 title / summary
        days: 回看天数(默认 7)
        jaccard_threshold: 算同事件的 similarity 阈值
            阈值实际是 event_similarity = max(Jaccard, containment) 的阈值
            ≥ 0.40 → 同事件
        drafts_dir: drafts 目录(默认 output/drafts/)

    Return:
        {
          "is_duplicate": bool,
          "matched_draft": str | None,     # 命中的 draft 文件名
          "matched_title": str | None,     # 命中的旧标题
          "jaccard": float,                # 最高 Jaccard 值
          "checked": int,                  # 实际比对了多少篇
          "new_fingerprint": list[str],    # 新事件指纹(给用户透明)
        }
    """
    if drafts_dir is None:
        drafts_dir = DRAFTS_DIR

    new_fp = event_fingerprint(
        new_item.get("title", "") or "",
        new_item.get("summary", "") or "",
    )

    if not drafts_dir.exists():
        return {
            "is_duplicate": False,
            "matched_draft": None,
            "matched_title": None,
            "jaccard": 0.0,
            "checked": 0,
            "new_fingerprint": sorted(new_fp),
        }

    # Bug 4 修复(2026-05-25 Round 17):解析 current_draft_path 排除自身
    self_resolved = None
    if current_draft_path is not None:
        try:
            self_resolved = Path(current_draft_path).resolve()
        except Exception:
            self_resolved = None

    cutoff = datetime.now() - timedelta(days=days)
    best_jaccard = 0.0
    best_match: Optional[tuple[str, str]] = None  # (draft_filename, title)
    checked = 0

    for draft_path in drafts_dir.glob("*.md"):
        # Bug 4 修复:排除自身
        if self_resolved is not None:
            try:
                if draft_path.resolve() == self_resolved:
                    continue
            except Exception:
                pass
        try:
            mtime = datetime.fromtimestamp(draft_path.stat().st_mtime)
        except Exception:
            continue
        if mtime < cutoff:
            continue
        meta = _parse_draft_frontmatter(draft_path)
        if not meta.get("title"):
            continue
        old_fp = event_fingerprint(meta["title"], meta.get("digest", ""))
        # 用 event_similarity = max(Jaccard, containment) 兼容长短文本
        j = event_similarity(new_fp, old_fp)
        checked += 1
        if j > best_jaccard:
            best_jaccard = j
            best_match = (draft_path.name, meta["title"])

    # Round 22 #2:扫已发布存档(runs/*.json 含 media_id),抓「已发还推荐」
    # 隔壁 e2e 抓的:event_dedup 没识别 TrapDoor 已发(只查 drafts 不查 publish)
    if include_published:
        published = _scan_published_titles(RUNS_DIR, days)
        for item in published:
            old_fp = event_fingerprint(item["title"], item["summary"])
            j = event_similarity(new_fp, old_fp)
            checked += 1
            if j > best_jaccard:
                best_jaccard = j
                best_match = (f"[published] {item['source']}", item["title"])

    is_dup = best_jaccard >= jaccard_threshold
    return {
        "is_duplicate": is_dup,
        "matched_draft": best_match[0] if best_match else None,
        "matched_title": best_match[1] if best_match else None,
        "similarity": round(best_jaccard, 3),  # 实际是 event_similarity = max(jaccard, containment)
        "checked": checked,
        "new_fingerprint": sorted(new_fp),
    }


# ============================================================
# CLI 测试入口
# ============================================================

def cli_demo():
    """跑几个 case 看是否能正确去重."""
    test_cases = [
        # 跟 anthropic-300b-overtake-openai 是同一事件
        {"title": "Anthropic 即将完成 300 亿融资估值反超 OpenAI", "summary": "9000 亿估值"},
        # 跟 karpathy-joins-anthropic 是同一事件
        {"title": "Karpathy 离开 OpenAI 加入 Anthropic", "summary": "pre-training 团队"},
        # 跟两者都不是
        {"title": "DeepSeek R2 测评深度解读", "summary": "新模型 benchmark"},
        # 完全新事件
        {"title": "Claude Code 实战 Skills 框架", "summary": "agent 编程"},
    ]
    print("=== event_dedup demo ===\n")
    for i, item in enumerate(test_cases, 1):
        result = check_event_dedup(item, days=30)  # demo 用 30 天回看更稳
        marker = "⛔" if result["is_duplicate"] else "✅"
        print(f"[{i}] {marker} {item['title']}")
        print(f"    fingerprint: {result['new_fingerprint'][:10]}...")
        print(f"    最高 similarity: {result['similarity']}  (checked {result['checked']} 篇)")
        if result["is_duplicate"]:
            print(f"    ⛔ 跟已 ship 的「{result['matched_title']}」是同事件")
            print(f"       (file: {result['matched_draft']})")
        print()


if __name__ == "__main__":
    cli_demo()
