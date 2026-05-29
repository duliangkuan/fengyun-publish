"""
看每个 feed 拿到的 items 的发布时间分布,
判断是新数据还是历史 cache 残留。
"""
import sqlite3
from pathlib import Path

db = Path(r"D:\Dev\TrendRadar\output\rss\2026-05-26.db")
conn = sqlite3.connect(db)
cur = conn.cursor()

# 看 RSSHub 那 2 个可疑的 feed
print("=== 微博 + B站秋葉aaaki — 数据是新还是老?===\n")
for fid in ("rsshub-weibo-keyword-ai", "bilibili-qiuye-aaaki"):
    print(f"--- {fid} ---")
    rows = cur.execute(
        "SELECT title, published_at, first_crawl_time FROM rss_items "
        "WHERE feed_id = ? ORDER BY first_crawl_time DESC LIMIT 5",
        (fid,)
    ).fetchall()
    for r in rows:
        print(f"  published: {r[1]}  crawled: {r[2]}")
        print(f"    {(r[0] or '')[:60]}")
    print()

# 全表 first_crawl_time 范围,判断是不是这次跑新插的
print("=== rss_items 总体 crawl 时间分布(Top 10)===")
rows = cur.execute(
    "SELECT first_crawl_time, COUNT(*) FROM rss_items "
    "GROUP BY first_crawl_time ORDER BY first_crawl_time DESC LIMIT 10"
).fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]} 条")
