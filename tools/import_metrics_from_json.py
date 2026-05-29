#!/usr/bin/env python3
# 把 wechat-article-exporter 导出的 JSON 灌进 db.sqlite。
# 用法:
#   python tools/import_metrics_from_json.py corpus/raw/fengyun/微信公众号文章.json --slug fengyun
#   python tools/import_metrics_from_json.py corpus/raw/fengyun/微信公众号文章.json --slug fengyun --dry-run

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "db.sqlite"

ARTICLE_FIELDS = [
    "aid", "appmsgid", "itemidx", "fakeid", "title", "author_name",
    "cover", "create_time", "update_time", "link", "digest",
    "copyright_type", "item_show_type", "is_pay_subscribe",
]

METRIC_FIELDS = ["readNum", "likeNum", "oldLikeNum", "shareNum", "commentNum"]

COMMENT_FIELDS = [
    "comment_id", "seq", "nick_name", "content", "create_time", "like_num",
    "is_elected", "is_from_friend", "identity_type", "party_flag",
    "ip_country", "ip_province", "ip_city", "reply_count",
]


def detect_field_version(snapshot_iso: str) -> str:
    # 2025-11 微信下线「阅读次数」字段,只剩「阅读人数」
    # 之前抓的 KOL 数据 readNum = 阅读次数,之后 = 阅读人数,语义不一样,必须标记
    return "v1_pre_2025_11" if snapshot_iso < "2025-11-01" else "v2_post_2025_11"


def detect_credential_failure(data):
    # 检测 ret=200022(appmsg_token 过期),全网调研报告里特别强调要拦
    # 全行业坑:token 过期 exporter 不报错继续跑,但拿不到数据,飞轮静默丢数
    if isinstance(data, dict):
        if data.get("base_resp", {}).get("ret") == 200022:
            return "凭证失效 ret=200022 — appmsg_token 已过期,请重抓 cookie"
        if data.get("ret") == 200022:
            return "凭证失效 ret=200022"
    return None


def ensure_field_version_column(conn):
    cur = conn.execute("PRAGMA table_info(metrics)")
    cols = {row[1] for row in cur.fetchall()}
    if "field_version" not in cols:
        conn.execute("ALTER TABLE metrics ADD COLUMN field_version TEXT")
        print("[migrate] metrics 表加列 field_version")


def import_json(json_path, slug, db_path, snapshot_at, dry_run):
    snapshot_at = snapshot_at or datetime.now().isoformat(timespec="seconds")
    field_version = detect_field_version(snapshot_at)

    print(f"[start] JSON  : {json_path}")
    print(f"        DB    : {db_path}")
    print(f"        slug  : {slug}")
    print(f"        snapshot_at  : {snapshot_at}")
    print(f"        field_version: {field_version}")
    print(f"        dry_run: {dry_run}")

    if not json_path.exists():
        print(f"[FATAL] JSON 文件不存在:{json_path}", file=sys.stderr)
        sys.exit(2)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    err = detect_credential_failure(data)
    if err:
        print(f"[FATAL] {err}", file=sys.stderr)
        sys.exit(2)

    if isinstance(data, dict) and "articles" in data:
        data = data["articles"]
    if not isinstance(data, list):
        print(f"[FATAL] JSON 顶层不是列表,也不是 {{'articles': [...]}}", file=sys.stderr)
        sys.exit(2)

    print(f"[parse] {len(data)} 篇文章")

    if dry_run:
        print("\n[DRY-RUN] 不写库,展示前 3 篇要插入的:")
        for art in data[:3]:
            print(f"  - aid={art.get('aid')}  title={(art.get('title') or '')[:40]}")
            print(f"    readNum={art.get('readNum')}  likeNum={art.get('likeNum')}"
                  f"  oldLikeNum={art.get('oldLikeNum')}  shareNum={art.get('shareNum')}")
        return

    conn = sqlite3.connect(db_path)
    ensure_field_version_column(conn)

    n_art_new = n_art_upd = n_metric = n_comment = 0

    try:
        for art in data:
            aid = art.get("aid")
            if not aid:
                continue

            # articles UPSERT
            existing = conn.execute("SELECT 1 FROM articles WHERE aid = ?", (aid,)).fetchone()
            article_data = {f: art.get(f) for f in ARTICLE_FIELDS if f in art}
            article_data["aid"] = aid
            article_data["account_slug"] = slug
            article_data["account_name"] = art.get("_accountName") or slug

            if existing:
                cols = [k for k in article_data if k != "aid"]
                setters = ", ".join(f"{c} = ?" for c in cols)
                conn.execute(
                    f"UPDATE articles SET {setters} WHERE aid = ?",
                    [article_data[c] for c in cols] + [aid],
                )
                n_art_upd += 1
            else:
                cols = list(article_data.keys())
                conn.execute(
                    f"INSERT INTO articles ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                    [article_data[c] for c in cols],
                )
                n_art_new += 1

            # metrics APPEND(每次跑都加一行快照,保留历史)
            metric_data = {
                "aid": aid,
                "snapshot_at": snapshot_at,
                "field_version": field_version,
            }
            for f in METRIC_FIELDS:
                metric_data[f] = art.get(f)
            cols = list(metric_data.keys())
            conn.execute(
                f"INSERT INTO metrics ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                [metric_data[c] for c in cols],
            )
            n_metric += 1

            # comments UPSERT
            for c in art.get("comments", []) or []:
                cid = c.get("comment_id")
                if not cid:
                    continue
                if conn.execute("SELECT 1 FROM comments WHERE comment_id = ?", (cid,)).fetchone():
                    continue
                comment_data = {col: c.get(col) for col in COMMENT_FIELDS if col in c}
                comment_data["aid"] = aid
                comment_data["comment_id"] = cid
                comment_data["raw_json"] = json.dumps(c, ensure_ascii=False)
                cols = list(comment_data.keys())
                conn.execute(
                    f"INSERT INTO comments ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                    [comment_data[c_] for c_ in cols],
                )
                n_comment += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"\n[done] articles:  +{n_art_new} 新, {n_art_upd} 更新")
    print(f"       metrics :  +{n_metric} 行(每次抓都追加)")
    print(f"       comments:  +{n_comment} 新评论")
    print(f"\n下次跑同一 slug 会自动 UPSERT,不会重复插 articles。")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("json_path", help="exporter 导出的 JSON 文件路径")
    p.add_argument("--slug", required=True, help="account_slug,如 fengyun")
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--snapshot-at", default=None, help="抓取时间(默认现在)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    import_json(
        json_path=Path(args.json_path),
        slug=args.slug,
        db_path=Path(args.db),
        snapshot_at=args.snapshot_at,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
