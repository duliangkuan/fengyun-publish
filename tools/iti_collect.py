"""
iti_collect.py — ITI 架构第一段 Information(广搜)

风云自创 ITI 架构(Information-Title-Information)2026-05-24 落地。
I-1 实现:从 6 个搜索工具循环拉候选,去重后给 Title 层排序。

硬约束(用户 2026-05-24 锁定):
- ≥ 10 条候选(两位数,Musk × Jobs 共识及格线)
- 目标 15-25 条(甜蜜点)
- 上限 30 条(防用户挑花眼)

6 个信源:
1. aihot 24h selected(公网 SaaS)
2. we-mp-rss 16 公众号最近 N 天(本地 docker sqlite)
3. TrendRadar latest_daily.md(本地文件,mtime > 24h 跳过)
4. arxiv cs.AI 最新(公网 API)
5. smol.ai AINews RSS(公网 newsletter)
6. WebSearch — 主线程负责(脚本接 list 参数)

去重:URL normalize + title fingerprint(复用 event_dedup.event_fingerprint)
失败处理:任意源失败不影响其他,标记 degraded

接口:
    from tools.iti_collect import collect_pool

    pool = collect_pool(hours=24)
    # 每条 dict 含 title / summary / url / source / publishedAt / category / _origin
"""
from __future__ import annotations
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
TRENDRADAR_LATEST = Path(r"D:\Dev\TrendRadar\output\latest_daily.md")

UA_DEFAULT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 候选池硬约束(用户 2026-05-24 锁定)
TARGET_MIN = 10
TARGET_MAX = 30
TARGET_SWEET = (15, 25)


# ============================================================
# 信源 1: aihot 公网 SaaS
# ============================================================

def fetch_aihot(hours: int = 24, take: int = 30) -> list[dict]:
    """从 aihot.virxact.com 拉精选 items.

    aihot 需要浏览器 UA(API 端点 nginx UA 黑名单),不给会 403.
    """
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    url = (
        "https://aihot.virxact.com/api/public/items"
        f"?mode=selected&since={since}&take={take}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA_DEFAULT})
    with urllib.request.urlopen(
        req, context=ssl.create_default_context(), timeout=30
    ) as resp:
        data = json.loads(resp.read())
    out = []
    for it in data.get("items", []):
        out.append({
            "title": it.get("title", ""),
            "summary": it.get("summary") or "",
            "url": it.get("url", ""),
            "source": f"aihot:{it.get('source', '?')}",
            "category": it.get("category"),
            "publishedAt": it.get("publishedAt"),
            "_origin": "aihot",
        })
    return out


# ============================================================
# 信源 2: we-mp-rss 本地 sqlite(docker exec)
# ============================================================

# we-mp-rss 16 个公众号 biz_id(MEMORY 锁定 2026-05-22 实测)
WMP_FEEDS = [
    ("MP_WXS_3949607775", "DeepSeek"),
    ("MP_WXS_3931685224", "Kimi 智能助手"),
    ("MP_WXS_3923277442", "智谱"),
    ("MP_WXS_3948884294", "通义千问"),
    ("MP_WXS_3191077711", "MiniMax 稀宇科技"),
    ("MP_WXS_3925617892", "阶跃星辰"),
    ("MP_WXS_3937549843", "百川智能"),
    ("MP_WXS_3073282833", "机器之心"),
    ("MP_WXS_3236757533", "量子位"),
    ("MP_WXS_3271041950", "新智元"),
    ("MP_WXS_3572959446", "晚点 LatePost"),
    ("MP_WXS_3895742803", "Founder Park"),
    ("MP_WXS_3223096120", "数字生命卡兹克"),
    ("MP_WXS_3957812448", "宝玉 AI"),
    ("MP_WXS_3934419561", "赛博禅心"),
    ("MP_WXS_3926568365", "硅星人 Pro"),
]

_ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


def _fetch_one_feed(biz_id: str, mp_name: str, days: int) -> list[dict]:
    """单个 atom feed 拉取(< 1 秒)."""
    url = f"http://localhost:8001/feed/{biz_id}.atom"
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA_DEFAULT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        for entry in root.findall("a:entry", _ATOM_NS):
            title_el = entry.find("a:title", _ATOM_NS)
            link_el = entry.find("a:link", _ATOM_NS)
            updated_el = entry.find("a:updated", _ATOM_NS)
            summary_el = entry.find("a:summary", _ATOM_NS)
            if title_el is None or link_el is None:
                continue
            # 用 updated 过滤 N 天内
            updated_str = (updated_el.text or "").strip() if updated_el is not None else ""
            in_window = True
            if updated_str:
                # atom 格式 "Fri, 22 May 2026 10:21:12 +0800"
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(updated_str)
                    if dt.tzinfo:
                        # naive 对比,统一转 naive UTC
                        dt = dt.astimezone().replace(tzinfo=None)
                    in_window = dt >= cutoff
                except Exception:
                    pass
            if not in_window:
                continue
            href = link_el.get("href", "")
            out.append({
                "title": (title_el.text or "").strip(),
                "summary": ((summary_el.text or "").strip()[:200]
                            if summary_el is not None else ""),
                "url": href,
                "source": f"we-mp-rss:{mp_name}",
                "category": None,
                "publishedAt": updated_str,
                "_origin": "we-mp-rss",
            })
    except Exception:
        pass  # 单个 feed 失败不影响其他
    return out


def fetch_we_mp_rss(days: int = 3, max_workers: int = 4) -> list[dict]:
    """通过 we-mp-rss HTTP atom feed 拉最近 N 天的公众号文章.

    并发拉 16 个 feed(降至 4 worker 避免容器过载),合并返回.
    比 docker exec + sqlite 简单(容器没装 sqlite3 CLI).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    days = max(1, int(days))
    out = []
    fail_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_one_feed, biz, name, days): name
                   for biz, name in WMP_FEEDS}
        for f in as_completed(futures, timeout=60):
            try:
                items = f.result()
                out.extend(items)
            except Exception:
                fail_count += 1
    if fail_count > 0 and not out:
        print(f"  [we-mp-rss] {fail_count}/{len(WMP_FEEDS)} feed 失败", file=sys.stderr)
    return out


# ============================================================
# 信源 3: TrendRadar latest_daily.md
# ============================================================

_TRENDRADAR_LINK_PATTERN = re.compile(
    r"\[(?P<source>[^\]]+?)\]\s*🆕?\s*\[(?P<title>[^\]]+?)\]\((?P<url>https?://[^)]+)\)"
)


def fetch_trendradar(max_age_hours: int = 36) -> list[dict]:
    """读 TrendRadar latest_daily.md,提取每条新闻.

    mtime > max_age_hours 视为过期,跳过这个源(降级).
    """
    if not TRENDRADAR_LATEST.exists():
        return []
    mtime = datetime.fromtimestamp(TRENDRADAR_LATEST.stat().st_mtime)
    age = datetime.now() - mtime
    if age > timedelta(hours=max_age_hours):
        print(
            f"  [trendradar] latest_daily.md 已过期 ({age.total_seconds() / 3600:.1f}h > {max_age_hours}h),跳过",
            file=sys.stderr,
        )
        return []
    text = TRENDRADAR_LATEST.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in _TRENDRADAR_LINK_PATTERN.finditer(text):
        out.append({
            "title": m.group("title"),
            "summary": "",
            "url": m.group("url"),
            "source": f"trendradar:{m.group('source')}",
            "category": None,
            "publishedAt": mtime.isoformat(),
            "_origin": "trendradar",
        })
    return out


# ============================================================
# 信源 4: arxiv cs.AI 公网 API
# ============================================================

ARXIV_API = "http://export.arxiv.org/api/query"
_ARXIV_NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_arxiv(category: str = "cs.AI", max_results: int = 10) -> list[dict]:
    """arxiv API 拉最新 cs.AI papers."""
    params = {
        "search_query": f"cat:{category}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA_DEFAULT})
    with urllib.request.urlopen(
        req, context=ssl.create_default_context(), timeout=20
    ) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes)
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
            "summary": ((summary_el.text or "").strip().replace("\n", " ")[:200]
                        if summary_el is not None else ""),
            "url": (id_el.text or "").strip(),
            "source": "arxiv:cs.AI",
            "category": "paper",
            "publishedAt": (published_el.text or "").strip() if published_el is not None else None,
            "_origin": "arxiv",
        })
    return out


# ============================================================
# 信源 5: smol.ai AINews RSS
# ============================================================

SMOL_AI_RSS = "https://buttondown.email/ainews/rss"


def fetch_smol_ai(max_items: int = 10) -> list[dict]:
    """smol.ai AINews newsletter RSS."""
    req = urllib.request.Request(SMOL_AI_RSS, headers={"User-Agent": UA_DEFAULT})
    with urllib.request.urlopen(
        req, context=ssl.create_default_context(), timeout=20
    ) as resp:
        xml_bytes = resp.read()
    root = ET.fromstring(xml_bytes)
    # RSS 2.0:rss/channel/item
    channel = root.find("channel")
    if channel is None:
        return []
    out = []
    for item in channel.findall("item")[:max_items]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()[:200]
        if not title or not link:
            continue
        out.append({
            "title": title,
            "summary": re.sub(r"<[^>]+>", "", description),  # 剥 HTML
            "url": link,
            "source": "smol.ai:AINews",
            "category": None,
            "publishedAt": pub_date,
            "_origin": "smol.ai",
        })
    return out


# ============================================================
# 去重(URL normalize + title fingerprint)
# ============================================================

def _normalize_url(url: str) -> str:
    """URL normalize:去 utm/fbclid 等 tracker 参数,去 fragment."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return url.strip().lower()
    # 删 tracker 参数
    if parsed.query:
        kept = []
        for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
            if k.lower().startswith(("utm_", "fbclid", "gclid", "spm", "from")):
                continue
            kept.append((k, v))
        new_query = urllib.parse.urlencode(kept)
    else:
        new_query = ""
    # 重建(去 fragment)
    return urllib.parse.urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        parsed.params,
        new_query,
        "",
    ))


def dedup_pool(pool: list[dict]) -> list[dict]:
    """URL + title 双重去重.

    1. URL normalize 后相同 → 同一条
    2. title fingerprint 相似度 ≥ 0.6 → 同一条(用 event_dedup 算法)
    """
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        from event_dedup import event_fingerprint, event_similarity
    except ImportError:
        # 没装 event_dedup,只用 URL 去重
        event_fingerprint = None
        event_similarity = None

    seen_urls = set()
    seen_fps = []  # list of (frozenset, kept_dict)
    deduped = []
    for item in pool:
        norm = _normalize_url(item.get("url", ""))
        if norm and norm in seen_urls:
            continue
        # title 指纹去重
        if event_fingerprint:
            fp = event_fingerprint(item.get("title", "") or "", item.get("summary", "") or "")
            is_dup = False
            for prev_fp, _ in seen_fps:
                if event_similarity(fp, prev_fp) >= 0.6:
                    is_dup = True
                    break
            if is_dup:
                continue
            seen_fps.append((fp, item))
        if norm:
            seen_urls.add(norm)
        deduped.append(item)
    return deduped


# ============================================================
# 主入口:collect_pool
# ============================================================

def collect_pool(
    hours: int = 24,
    target_min: int = TARGET_MIN,
    target_max: int = TARGET_MAX,
    verbose: bool = True,
) -> dict:
    """ITI I-1 广搜主入口.

    Args:
        hours: 回看时间窗(默认 24h)
        target_min: 候选池最少条数(默认 10,两位数硬约束)
        target_max: 上限(默认 30)
        verbose: 打印每个源的拉取情况

    Return:
        {
          "items": list[dict],          # 去重后的候选池(已截到 target_max)
          "n_total": int,               # 去重前总数
          "n_unique": int,              # 去重后总数
          "sources_ok": list[str],      # 成功的源
          "sources_failed": list[dict], # 失败的源 + 原因
          "degraded": bool,             # 是否 < target_min
          "stats_per_source": dict,     # 每个源拉到多少
        }
    """
    sources = [
        ("aihot", lambda: fetch_aihot(hours=hours)),
        ("we-mp-rss", lambda: fetch_we_mp_rss(days=max(3, hours / 24))),
        ("trendradar", lambda: fetch_trendradar()),
        ("arxiv", lambda: fetch_arxiv()),
        ("smol.ai", lambda: fetch_smol_ai()),
    ]
    all_items = []
    sources_ok = []
    sources_failed = []
    stats = {}
    if verbose:
        print(f"=== ITI I-1 广搜 ({hours}h 窗口,目标 {target_min}-{target_max} 条)===")
    for name, fetcher in sources:
        try:
            items = fetcher()
            n = len(items)
            stats[name] = n
            if n > 0:
                sources_ok.append(name)
                if verbose:
                    print(f"  [{name:<14}] {n:>3} 条 ✓")
            else:
                if verbose:
                    print(f"  [{name:<14}] {n:>3} 条 ⚠ (空)")
            all_items.extend(items)
        except Exception as e:
            stats[name] = 0
            sources_failed.append({"name": name, "error": str(e)[:120]})
            if verbose:
                print(f"  [{name:<14}] FAIL: {str(e)[:80]}")

    n_total = len(all_items)
    deduped = dedup_pool(all_items)
    n_unique = len(deduped)
    deduped = deduped[:target_max]

    degraded = len(deduped) < target_min
    if verbose:
        print(f"  → 合计 {n_total} 条,去重后 {n_unique} 条")
        if degraded:
            print(
                f"  ⚠️  候选池 {n_unique} < {target_min} 两位数硬约束,降级 "
                f"(失败源:{[f['name'] for f in sources_failed]})"
            )
        else:
            print(f"  ✓ 满足两位数硬约束 (≥{target_min})")

    return {
        "items": deduped,
        "n_total": n_total,
        "n_unique": n_unique,
        "sources_ok": sources_ok,
        "sources_failed": sources_failed,
        "degraded": degraded,
        "stats_per_source": stats,
    }


# ============================================================
# CLI(测试用)
# ============================================================

def cli():
    # Round 22 #1:支持 --out 写 candidates.json,默认写到 output/candidates/YYYYMMDD.json
    import argparse
    ap = argparse.ArgumentParser(description="ITI I-1 广搜聚合 6 信源")
    ap.add_argument("--hours", type=int, default=24, help="时间窗(小时)")
    ap.add_argument("--out", default=None,
                    help="写 candidates.json 路径(默认 output/candidates/YYYYMMDD.json)")
    ap.add_argument("--no-write", action="store_true",
                    help="只 stdout,不写文件")
    args = ap.parse_args()

    result = collect_pool(hours=args.hours, verbose=True)
    print()
    print("=== Top 15 候选(按拉取顺序,未排序)===")
    for i, item in enumerate(result["items"][:15], 1):
        title = item["title"][:60]
        src = item["source"][:30]
        print(f"  [{i:>2}] {title:<60}  ({src})")

    # Round 22 #1:写文件供下游(topic_recommender)读
    if not args.no_write:
        import json
        from datetime import datetime
        if args.out:
            out_path = Path(args.out)
        else:
            today = datetime.now().strftime("%Y%m%d")
            out_path = Path(__file__).parent.parent / "output" / "candidates" / f"{today}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now().isoformat(),
            "hours_window": args.hours,
            "n_total": result["n_total"],
            "n_unique": result["n_unique"],
            "degraded": result["degraded"],
            "sources_ok": result["sources_ok"],
            "sources_failed": result["sources_failed"],
            "stats_per_source": result["stats_per_source"],
            "items": result["items"],
        }
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n候选已写: {out_path} ({len(result['items'])} 条)")

    if result["degraded"]:
        sys.exit(3)


if __name__ == "__main__":
    cli()
