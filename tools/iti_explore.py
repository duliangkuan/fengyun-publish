"""
iti_explore.py — ITI 架构第二段 Information(深搜)

风云自创 ITI 架构 I-2 实现:基于选题反向激活相关搜索源,拉 15-25 条带 URL 事实.

设计原则(用户原话 2026-05-24):
- 「搜索工具调用没那么复杂」 — 不做 entity-aware 动态路由,就调一遍工具
- 「够用就停」 — 拿到 15-25 条 unique 事实就够,不浪费 API

5 个本地+API 源(WebSearch 留给主线程):
1. we-mp-rss sqlite 查同主题历史文章
2. corpus grep 4 对标号(huashu/baoyu/saiboshanxin/kazik)
3. arxiv 主题搜索(如果选题含论文/技术)
4. topic_hotness 查这个主题的历史 burst_rate 数据
5. safe_webfetch 反爬抓主源原文(主线程传 URL list)

WebSearch 中英文:**主线程 Claude 负责**(脚本无法调 WebSearch),
然后通过 `merge_with_websearch(facts, websearch_results)` 合并.

接口:
    from tools.iti_explore import explore_topic, merge_with_websearch

    # 主线程在 Step 2 工作流:
    # 1. 调 WebSearch 中英文 拿 raw items
    # 2. 调 iti_explore.explore_topic(slug, title, entities) 拿本地+API facts
    # 3. 调 merge_with_websearch 合并去重 → research.md
"""
from __future__ import annotations
import json
import re
import ssl
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
CORPUS_DIR = ROOT / "corpus"
TOPIC_HOTNESS_PATH = ROOT / "topic_hotness.parquet"

UA_DEFAULT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 深搜目标(用户「够用就停」原则)
TARGET_FACTS_MIN = 10
TARGET_FACTS_MAX = 25


# ============================================================
# 源 1: we-mp-rss sqlite 同主题历史查询
# ============================================================

def fetch_we_mp_rss_by_topic(entities: list[str], days: int = 180) -> list[dict]:
    """从 we-mp-rss sqlite 查含 entity 关键词的历史文章."""
    if not entities:
        return []
    # 构造 LIKE 条件(每个 entity OR 关系)
    likes = " OR ".join(f"articles.title LIKE '%{e.replace(chr(39), chr(39)*2)}%'" for e in entities)
    sql = (
        "SELECT articles.title, articles.url, articles.publish_time, feeds.mp_name "
        "FROM articles JOIN feeds ON articles.mp_id = feeds.id "
        f"WHERE ({likes}) "
        f"AND articles.publish_time >= datetime('now', '-{int(days)} days') "
        "ORDER BY articles.publish_time DESC LIMIT 20"
    )
    cmd = ["docker", "exec", "we-mp-rss", "sqlite3", "/app/data/db.db", "-json", sql]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=20,
            encoding="utf-8", errors="replace"
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        rows = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"  [we-mp-rss topic] FAIL: {e}", file=sys.stderr)
        return []
    out = []
    for r in rows:
        out.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "source": f"we-mp-rss:{r.get('mp_name', '?')}",
            "date": r.get("publish_time"),
            "_origin": "we-mp-rss-topic",
        })
    return out


# ============================================================
# 源 2: corpus grep 4 对标号
# ============================================================

CORPUS_KOL_DIRS = ["huashu", "baoyu", "saiboshanxin"]
# kazik 在 corpus/.raw/ 下


def fetch_corpus_grep(entities: list[str]) -> list[dict]:
    """grep 4 对标号 corpus 找同主题已写过的文章."""
    if not entities:
        return []
    out = []
    for kol in CORPUS_KOL_DIRS:
        kol_dir = CORPUS_DIR / "raw" / kol
        if not kol_dir.exists():
            continue
        for entity in entities[:5]:  # 限前 5 个 entity 避免太慢
            pattern = re.escape(entity)
            try:
                for md_file in kol_dir.glob("*.md"):
                    text = md_file.read_text(encoding="utf-8", errors="replace")
                    if re.search(pattern, text, re.IGNORECASE):
                        # 抽前 200 字作 summary
                        clean = re.sub(r"[#*`>\[\]()!]", "", text)
                        clean = re.sub(r"\s+", " ", clean)
                        out.append({
                            "title": md_file.stem.replace("_", " "),
                            "url": f"corpus://{kol}/{md_file.name}",
                            "source": f"corpus:{kol}",
                            "summary": clean[:200],
                            "date": None,
                            "_origin": "corpus-grep",
                        })
                        break  # 同一个 KOL 同一个 entity 最多 1 条避免膨胀
            except Exception:
                continue
    # 全文去重 by url
    seen = set()
    unique = []
    for it in out:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        unique.append(it)
    return unique[:10]  # cap 10


# ============================================================
# 源 3: arxiv 主题搜索
# ============================================================

ARXIV_API = "http://export.arxiv.org/api/query"
_ARXIV_NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_arxiv_by_topic(entities: list[str], max_results: int = 5) -> list[dict]:
    """arxiv 按 entity 关键词搜索 cs.AI 论文."""
    if not entities:
        return []
    # 只取前 3 个 entity,OR 连接
    query_terms = " OR ".join(f"all:{e}" for e in entities[:3])
    params = {
        "search_query": f"({query_terms}) AND cat:cs.AI",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA_DEFAULT})
    try:
        with urllib.request.urlopen(
            req, context=ssl.create_default_context(), timeout=20
        ) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        print(f"  [arxiv topic] FAIL: {e}", file=sys.stderr)
        return []
    out = []
    for entry in root.findall("a:entry", _ARXIV_NS):
        title_el = entry.find("a:title", _ARXIV_NS)
        summary_el = entry.find("a:summary", _ARXIV_NS)
        id_el = entry.find("a:id", _ARXIV_NS)
        published_el = entry.find("a:published", _ARXIV_NS)
        if title_el is None or id_el is None:
            continue
        out.append({
            "title": (title_el.text or "").strip().replace("\n", " "),
            "url": (id_el.text or "").strip(),
            "source": "arxiv:cs.AI",
            "summary": ((summary_el.text or "").strip().replace("\n", " ")[:200]
                        if summary_el is not None else ""),
            "date": (published_el.text or "").strip() if published_el is not None else None,
            "_origin": "arxiv-topic",
        })
    return out


# ============================================================
# 源 4: topic_hotness 历史数据
# ============================================================

def fetch_topic_hotness_facts(slug: str, entities: list[str]) -> list[dict]:
    """从 topic_hotness.parquet 拿主题相关的爆款率数据.

    返回的 facts 形态:不是文章 url,而是「这个主题历史爆款数据」的事实条目.
    """
    if not TOPIC_HOTNESS_PATH.exists():
        return []
    try:
        import pandas as pd
        df = pd.read_parquet(TOPIC_HOTNESS_PATH)
    except Exception as e:
        print(f"  [topic_hotness] FAIL: {e}", file=sys.stderr)
        return []

    # 这里只能给数据级 facts(主题 N 篇文章 / 平均爆款率)
    # 因为 parquet 是 aid 索引,没法直接按 entity 查
    out = []
    by_topic = df.groupby("topic_id").agg(
        n=("aid", "count"),
        mean_hot30=("topic_hotness_30d", "mean"),
        mean_hot90=("topic_hotness_90d", "mean"),
    )
    top_topics = by_topic.sort_values("mean_hot90", ascending=False).head(3)
    for tid, row in top_topics.iterrows():
        if tid in (-1, 0):  # 离群/巨型杂类跳过
            continue
        out.append({
            "title": f"主题 #{int(tid)} 跨账号热度数据(参考)",
            "url": f"data://topic_hotness/topic_{int(tid)}",
            "source": "topic_hotness.parquet",
            "summary": (
                f"topic_id={int(tid)} / n={int(row['n'])} 篇 / "
                f"mean_hotness_30d={row['mean_hot30']:.2f} / "
                f"mean_hotness_90d={row['mean_hot90']:.2f}"
            ),
            "date": None,
            "_origin": "topic-hotness",
        })
    return out[:3]


# ============================================================
# 源 5.5: TrendRadar latest_daily.md 主题过滤
# ============================================================

def fetch_trendradar_topic(
    entities: list[str],
    max_age_hours: int = 36,
    top_k: int = 20,
) -> list[dict]:
    """从 TrendRadar latest_daily.md 提取跟当前主题相关的新闻.

    复用 iti_collect.fetch_trendradar() 拿全量 170 条,然后用 entities 关键词过滤.

    Args:
        entities: 主题实体词列表(如 ["Anthropic", "Claude", "Skills"])
        max_age_hours: 透传给 fetch_trendradar 的过期阈值
        top_k: 返回前 N 条匹配

    Returns:
        list[dict],每个 dict 含 title/url/source/publishedAt/_origin 字段(沿用 fetch_trendradar 的 schema)
    """
    # 复用 iti_collect.fetch_trendradar(),避免重复实现 markdown 解析
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        from iti_collect import fetch_trendradar
    except ImportError as e:
        print(f"  [trendradar topic] import FAIL: {e}", file=sys.stderr)
        return []

    all_items = fetch_trendradar(max_age_hours=max_age_hours)
    if not all_items:
        return []

    # 按 title 命中任一 entity 过滤(大小写不敏感)
    entities_lower = [e.lower() for e in entities if e]
    if not entities_lower:
        # 没 entities 就给前 top_k 条(降级,不报错)
        return all_items[:top_k]

    matched = []
    for item in all_items:
        title_lower = (item.get("title") or "").lower()
        if any(e in title_lower for e in entities_lower):
            matched.append(item)
    return matched[:top_k]


# ============================================================
# 源 5: safe_webfetch 反爬抓主源原文
# ============================================================

def fetch_main_sources(urls: list[str], timeout: int = 30) -> list[dict]:
    """用 safe_webfetch 反爬抓主线程提供的主源 URL list."""
    if not urls:
        return []
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        from safe_webfetch import safe_fetch
    except ImportError:
        return []
    out = []
    for url in urls[:4]:  # 限前 4 个,避免过度调用
        try:
            r = safe_fetch(url, timeout=timeout, max_retries=1)
            if r["ok"]:
                # 提取 <title> + 前 800 字正文
                html = r["html"]
                title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
                title = title_m.group(1).strip() if title_m else url
                # 粗暴去 HTML(给主线程后续 LLM 处理)
                text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                out.append({
                    "title": title,
                    "url": url,
                    "source": "safe_webfetch:main",
                    "summary": text[:600],
                    "date": None,
                    "_origin": "safe-webfetch",
                })
            else:
                print(f"  [main-source] {url} FAIL: {r.get('error')}", file=sys.stderr)
        except Exception as e:
            print(f"  [main-source] {url} EXC: {e}", file=sys.stderr)
    return out


# ============================================================
# 主入口:explore_topic
# ============================================================

def explore_topic(
    slug: str,
    title: str,
    entities: list[str],
    main_source_urls: Optional[list[str]] = None,
    verbose: bool = True,
) -> dict:
    """ITI I-2 深搜主入口(主线程 Step 2 调用).

    Args:
        slug: 选题 slug
        title: 选题标题
        entities: 关键 entity list,例 ["Anthropic", "Karpathy", "pre-training"]
        main_source_urls: 主源 URL list(可选,主线程从 WebSearch 拿到的 top URL)
        verbose: 打印每个源拉到多少

    Return:
        {
          "facts": list[dict],   # 本地+API 源的事实条目
          "stats": dict,         # 每个源拉到多少
          "n_unique": int,
        }

    主线程使用模式:
        # Step 2 工作流(在 SKILL.md 里):
        # 1. 主线程调 WebSearch 中英文 → ws_items
        # 2. 主线程提取 ws_items[:4] 的 url → main_urls
        # 3. 调 explore_topic(slug, title, entities, main_urls) → local_facts
        # 4. 合并 ws_items + local_facts['facts'] → research.md
    """
    facts = []
    stats = {}
    if verbose:
        print(f"=== ITI I-2 深搜:{title} ===")
        print(f"  entities: {entities[:8]}")

    # 6 个本地+API 源,each 失败不影响其他
    # trendradar 放第 2 位(紧跟 we-mp-rss,同为本地稳定缓存源),
    # 避免「够用就停」机制把它跳过.170 条本地数据是高价值源,优先级要前置.
    for name, fetcher in [
        ("we-mp-rss", lambda: fetch_we_mp_rss_by_topic(entities)),
        ("trendradar", lambda: fetch_trendradar_topic(entities)),
        ("corpus", lambda: fetch_corpus_grep(entities)),
        ("arxiv", lambda: fetch_arxiv_by_topic(entities)),
        ("topic_hotness", lambda: fetch_topic_hotness_facts(slug, entities)),
        ("main-sources", lambda: fetch_main_sources(main_source_urls or [])),
    ]:
        try:
            items = fetcher()
            n = len(items)
            stats[name] = n
            if verbose:
                print(f"  [{name:<14}] {n} 条")
            facts.extend(items)
            # 「够用就停」原则
            if len(facts) >= TARGET_FACTS_MAX:
                if verbose:
                    print(f"  → 已 {len(facts)} 条 ≥ {TARGET_FACTS_MAX},提前停")
                break
        except Exception as e:
            stats[name] = 0
            if verbose:
                print(f"  [{name:<14}] FAIL: {str(e)[:80]}")

    # URL 去重
    seen = set()
    unique = []
    for f in facts:
        u = f.get("url", "")
        if u and u in seen:
            continue
        if u:
            seen.add(u)
        unique.append(f)
    unique = unique[:TARGET_FACTS_MAX]

    if verbose:
        print(f"  → 合计本地+API: {len(facts)} 条,去重 {len(unique)} 条")
        if len(unique) < TARGET_FACTS_MIN:
            print(
                f"  ⚠️  本地+API 源 {len(unique)} < {TARGET_FACTS_MIN},"
                "主线程 WebSearch 必须补足"
            )

    return {
        "facts": unique,
        "stats": stats,
        "n_unique": len(unique),
    }


def merge_with_websearch(
    local_facts: list[dict],
    websearch_results: list[dict],
    max_total: int = TARGET_FACTS_MAX,
) -> list[dict]:
    """合并 WebSearch 结果(主线程拉的)+ explore_topic 本地 facts.

    Args:
        local_facts: explore_topic 返回的 facts
        websearch_results: 主线程 WebSearch 结果,每项 dict 含 title / url / summary
        max_total: 合并后上限

    Return:
        去重合并后的 list,主线程写到 research.md
    """
    combined = list(websearch_results) + list(local_facts)
    seen = set()
    out = []
    for f in combined:
        u = f.get("url", "")
        if u and u in seen:
            continue
        if u:
            seen.add(u)
        out.append(f)
    return out[:max_total]


# ============================================================
# CLI(测试用)
# ============================================================

def cli():
    # Round 22 #5:用 argparse 替换 sys.argv 切片,加 --main-source-urls
    # 隔壁 e2e 报告:CLI 不接 main_source_urls,Step 2 WebSearch 找到的 URL 没法注入深搜
    import argparse
    ap = argparse.ArgumentParser(description="ITI I-2 深搜")
    ap.add_argument("slug", help="选题 slug")
    ap.add_argument("title", nargs="?", default=None, help="选题标题(可空,默认用 slug)")
    ap.add_argument("--entities", nargs="*", default=None,
                    help="关键 entity list,例 --entities Anthropic Karpathy pre-training")
    ap.add_argument("--main-source-urls", nargs="*", default=None,
                    help="主源 URL list(主线程从 WebSearch 拿到的 top URL)")
    ap.add_argument("-v", "--verbose", action="store_true", default=True)
    args = ap.parse_args()

    slug = args.slug
    title = args.title or slug
    entities = args.entities or [slug]
    main_source_urls = args.main_source_urls or None

    result = explore_topic(
        slug, title, entities,
        main_source_urls=main_source_urls,
        verbose=args.verbose,
    )
    print()
    print(f"=== 本地+API 拿到 {result['n_unique']} 条事实 ===")
    for i, f in enumerate(result["facts"][:20], 1):
        title = (f.get("title") or "")[:60]
        src = (f.get("source") or "")[:30]
        print(f"  [{i:>2}] {title}  ({src})")


if __name__ == "__main__":
    cli()
