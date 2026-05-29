"""
feed 健康度诊断 - 列出每个 feed 的 fetch status / error / items 数。
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    db = Path(r"D:\Dev\TrendRadar\output\rss") / f"{date}.db"
    if not db.exists():
        print(f"DB 不存在: {db}")
        sys.exit(1)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    # 拿最新一次 crawl record,只看那一次的状态(避免累积重复)
    latest = cur.execute(
        "SELECT id, crawl_time FROM rss_crawl_records ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if latest is None:
        print("还没有 crawl 记录"); sys.exit(1)
    crawl_id, crawl_time = latest
    print(f"=== 最新 crawl record id={crawl_id} time={crawl_time} ===\n")

    sql = """
    SELECT
        f.id AS feed_id,
        f.name AS name,
        s.status,
        COALESCE(s.error_message, '') AS error,
        (SELECT COUNT(*) FROM rss_items WHERE feed_id = f.id) AS n_items
    FROM rss_feeds f
    LEFT JOIN rss_crawl_status s ON s.feed_id = f.id AND s.crawl_record_id = ?
    ORDER BY n_items ASC, f.id ASC
    """
    rows = cur.execute(sql, (crawl_id,)).fetchall()
    n_total = len(rows)
    n_dead = sum(1 for r in rows if r[4] == 0)
    n_alive = n_total - n_dead

    print(f"=== Feed 健康度报告 ({date}) ===")
    print(f"配置总数: {n_total}")
    print(f"有数据: {n_alive} ({n_alive*100//n_total}%)")
    print(f"0 数据: {n_dead} ({n_dead*100//n_total}%)")
    print()
    print(f"=== 完全失败的 {n_dead} 个 feed(0 条入库) ===")
    print(f"{'feed_id':30} {'status':10} {'name':50}  error")
    print("-" * 130)
    for r in rows:
        if r[4] == 0:
            err = (r[3] or "")[:50]
            name = (r[1] or "")[:50]
            print(f"{r[0]:30} {(r[2] or '-'):10} {name:50}  {err}")
    print()
    print(f"=== 有数据的 {n_alive} 个 feed ===")
    print(f"{'feed_id':30} {'n_items':>7}  {'name'}")
    print("-" * 100)
    for r in rows:
        if r[4] > 0:
            name = (r[1] or "")[:60]
            print(f"{r[0]:30} {r[4]:>7}  {name}")


if __name__ == "__main__":
    main()
