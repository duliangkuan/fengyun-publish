"""
扫描 D:\\Dev\\ai-wechat-pipeline\\corpus\\ 下的所有 .md 文件,产出索引。

每个公众号子目录(kazik/baoyu/saiboshanxin)被当成一个账号。
对每篇 .md:提取标题、发布日期、字数、首段预览。
输出:
  - corpus/corpus_index.json   机器读
  - corpus/corpus_index.md     人读

用法:
  python tools/build_corpus_index.py
"""

from __future__ import annotations

import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Windows GBK 控制台不认 Unicode 符号,强制 stdout/stderr 用 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
INDEX_JSON = CORPUS_DIR / "corpus_index.json"
INDEX_MD = CORPUS_DIR / "corpus_index.md"

ACCOUNT_NAMES = {
    "kazik": "数字生命卡兹克",
    "baoyu": "宝玉AI",
    "saiboshanxin": "赛博禅心",
}


def extract_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines()[:20]:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def extract_date(md_text: str, file_path: Path) -> str | None:
    # 1) frontmatter date: 2026-05-15
    m = re.search(r"^date:\s*(\d{4}-\d{1,2}-\d{1,2})", md_text, flags=re.MULTILINE)
    if m:
        return _normalize_date(m.group(1))
    # 2) 正文开头 8 行内的日期(yyyy-mm-dd 或 yyyy/mm/dd 或 yyyy年mm月dd日)
    head = "\n".join(md_text.splitlines()[:8])
    m = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", head)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # 3) 文件名前缀日期: 2026-05-15-xxx.md
    m = re.match(r"(\d{4})[-_](\d{1,2})[-_](\d{1,2})", file_path.stem)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def _normalize_date(s: str) -> str:
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return s


def first_paragraph(md_text: str, max_chars: int = 150) -> str:
    body = re.sub(r"^---.*?---", "", md_text, flags=re.DOTALL).strip()
    body = re.sub(r"^#+\s+.*$", "", body, flags=re.MULTILINE).strip()
    for para in body.split("\n\n"):
        para = para.strip()
        if len(para) >= 30:
            para = re.sub(r"\s+", " ", para)
            return para[:max_chars] + ("…" if len(para) > max_chars else "")
    return ""


def char_count(md_text: str) -> int:
    text = re.sub(r"!?\[.*?\]\(.*?\)", "", md_text)  # 去掉图片/链接
    text = re.sub(r"[#*`>\[\]\(\)\-]", "", text)
    text = re.sub(r"\s+", "", text)
    return len(text)


def scan_account(account_dir: Path) -> list[dict]:
    out = []
    for md in sorted(account_dir.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  ! 读取失败 {md.name}: {e}")
            continue
        out.append({
            "file": md.name,
            "path": str(md.relative_to(ROOT)).replace("\\", "/"),
            "title": extract_title(text, md.stem),
            "date": extract_date(text, md),
            "chars": char_count(text),
            "preview": first_paragraph(text),
        })
    return out


def main() -> None:
    if not CORPUS_DIR.exists():
        raise SystemExit(f"corpus 目录不存在: {CORPUS_DIR}")

    index = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "accounts": {}}

    for slug, cn_name in ACCOUNT_NAMES.items():
        account_dir = CORPUS_DIR / slug
        if not account_dir.exists():
            print(f"⚠ 跳过 {cn_name} ({slug}/) — 目录不存在")
            continue
        articles = scan_account(account_dir)
        index["accounts"][slug] = {
            "name": cn_name,
            "count": len(articles),
            "articles": articles,
        }
        print(f"✓ {cn_name}: {len(articles)} 篇")

    INDEX_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ JSON: {INDEX_JSON}")

    lines = [f"# 语料索引\n\n生成时间: {index['generated_at']}\n"]
    for slug, info in index["accounts"].items():
        lines.append(f"\n## {info['name']} ({slug}/, {info['count']} 篇)\n")
        articles = sorted(
            info["articles"],
            key=lambda a: (a["date"] or "0000-00-00"),
            reverse=True,
        )
        for a in articles:
            date = a["date"] or "????-??-??"
            lines.append(f"- **[{date}]** {a['title']} _({a['chars']:,} 字)_")
            lines.append(f"  - `{a['path']}`")
            if a["preview"]:
                lines.append(f"  - > {a['preview']}")
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"→ Markdown: {INDEX_MD}")


if __name__ == "__main__":
    main()
