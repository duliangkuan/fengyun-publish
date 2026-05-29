"""
从 corpus_index.json 里挑出"代表作",用作 khazix-writer 写新文时的 in-context few-shot。

代表性评分(简单可解释):
  - 字数:1500-8000 区间最高分(卡兹克 SKILL.md 目标范围)
  - 时效:越近越高(线性衰减,半年内满分,1 年外打折)
  - 公众号权重:kazik 1.0 / baoyu 0.7 / saiboshanxin 0.7

用法:
  python tools/pick_few_shot.py                     # 默认每个账号挑 8 篇,输出全文路径
  python tools/pick_few_shot.py --topic "Claude Code"  # 含该关键词的优先(标题或预览)
  python tools/pick_few_shot.py --kazik-only        # 只挑卡兹克

输出: stdout 打印挑中的篇目 + 全文路径,方便后续 cat 注入 LLM context。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
INDEX_JSON = ROOT / "corpus" / "corpus_index.json"

ACCOUNT_WEIGHTS = {"kazik": 1.0, "baoyu": 0.7, "saiboshanxin": 0.7}
TARGET_MIN_CHARS = 1500
TARGET_MAX_CHARS = 8000


def length_score(chars: int) -> float:
    if TARGET_MIN_CHARS <= chars <= TARGET_MAX_CHARS:
        return 1.0
    if chars < TARGET_MIN_CHARS:
        return max(0.0, chars / TARGET_MIN_CHARS)
    # 超长,衰减
    return max(0.2, 1.0 - (chars - TARGET_MAX_CHARS) / 10000)


def recency_score(date_str: str | None) -> float:
    if not date_str:
        return 0.3
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return 0.3
    days = (date.today() - d).days
    if days < 0:
        return 1.0
    if days <= 180:
        return 1.0
    if days <= 365:
        return 1.0 - (days - 180) / (365 - 180) * 0.3  # 0.7-1.0
    return max(0.4, 1.0 - days / 1000)


def topic_score(article: dict, topic: str | None) -> float:
    if not topic:
        return 1.0
    blob = (article.get("title", "") + " " + article.get("preview", "")).lower()
    hits = sum(1 for kw in topic.lower().split() if kw in blob)
    return 1.0 + 0.5 * hits  # 命中给加分,不命中保持 1.0


def score(article: dict, account_slug: str, topic: str | None) -> float:
    return (
        ACCOUNT_WEIGHTS.get(account_slug, 0.5)
        * length_score(article["chars"])
        * recency_score(article.get("date"))
        * topic_score(article, topic)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default=None, help="主题关键词(空格分隔多个),可选")
    parser.add_argument("--per-account", type=int, default=8, help="每个公众号挑几篇")
    parser.add_argument("--kazik-only", action="store_true", help="只挑卡兹克")
    parser.add_argument("--show-paths", action="store_true", default=True, help="打印全文路径")
    args = parser.parse_args()

    if not INDEX_JSON.exists():
        raise SystemExit(f"索引不存在: {INDEX_JSON}\n请先跑: python tools/build_corpus_index.py")

    index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))

    accounts = ["kazik"] if args.kazik_only else list(index["accounts"].keys())

    for slug in accounts:
        info = index["accounts"].get(slug)
        if not info:
            continue
        scored = [(score(a, slug, args.topic), a) for a in info["articles"]]
        scored.sort(key=lambda x: x[0], reverse=True)
        picked = scored[: args.per_account]

        print(f"\n## {info['name']} ({slug}/) — 挑 {len(picked)} 篇")
        for s, a in picked:
            date_str = a.get("date") or "????-??-??"
            print(f"- [{date_str}] {a['title']}  (score={s:.2f}, {a['chars']:,} 字)")
            if args.show_paths:
                print(f"    {ROOT / a['path']}")


if __name__ == "__main__":
    main()
