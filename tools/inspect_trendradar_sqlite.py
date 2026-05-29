"""
检查 TrendRadar 今日 RSS sqlite,看每个 source 实际入库多少条。
用法: python inspect_trendradar_sqlite.py [yyyy-mm-dd]
默认查今天。
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    db_path = Path(r"D:\Dev\TrendRadar\output\rss") / f"{date}.db"
    if not db_path.exists():
        print(f"DB 不存在: {db_path}")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print(f"=== DB: {db_path} ===")
    print("=== TABLES ===")
    for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        print(" ", r[0])
    print()
    print("=== SCHEMA ===")
    for r in cur.execute("SELECT sql FROM sqlite_master WHERE type='table'"):
        print((r[0] or "")[:500])
        print("---")
    print()
    # 试着按 source 统计(常见 column 名: source/source_id/feed_id/feed_name)
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    for tbl in tables:
        print(f"=== {tbl} 行数 ===")
        try:
            n = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  total: {n}")
        except Exception as e:
            print(f"  ERR: {e}")
            continue
        # 找候选 source 列
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info({tbl})")]
        for col in ("source", "source_id", "feed_id", "feed_name", "feed", "name"):
            if col in cols:
                print(f"  按 {col} 分组:")
                rows = cur.execute(
                    f"SELECT {col}, COUNT(*) FROM {tbl} GROUP BY {col} ORDER BY COUNT(*) DESC"
                ).fetchall()
                for src, cnt in rows:
                    print(f"    {cnt:>5}  {src}")
                break


if __name__ == "__main__":
    main()
