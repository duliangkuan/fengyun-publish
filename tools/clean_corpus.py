"""
清洗 wechat-article-exporter 导出的 .md 文件。

问题:
  - 首行混入了 CSS 残渣(`* { margin: 0; } body { font-family: ... }` 等)
  - 标题、日期、原文 URL 散落在前几行,没有结构化
  - Few-shot 召回时这些垃圾会污染 Claude 的 context

清洗策略:
  1. 第一次清洗:原文备份到 corpus/.raw/<account>/<file>.raw.md
  2. 提取:title, author, date, source_url
  3. 重写:frontmatter + "# 标题" + 干净正文
  4. 已清洗的文件(frontmatter 含 cleaned: true)默认跳过,--force 强制重做

用法:
  python tools/clean_corpus.py                # 清洗所有未清洗的
  python tools/clean_corpus.py --account kazik  # 只处理卡兹克
  python tools/clean_corpus.py --force        # 强制重洗(从备份恢复后重洗)
  python tools/clean_corpus.py --dry-run      # 只看会改什么不实际改
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
RAW_BACKUP = CORPUS_DIR / ".raw"

ACCOUNTS = ["kazik", "baoyu", "saiboshanxin"]

# CSS 残渣特征:第一行末尾常以 } 结束,且包含 { ... } 块
CSS_BLOCK_RE = re.compile(r"[\\\*\.\w][^{}]*\{[^{}]*\}")

# 元数据行:"原创 数字生命卡兹克 数字生命卡兹克 2026-05-15 10:29 北京"
META_LINE_RE = re.compile(
    r"^(?:原创\s+)?(\S+?)\s+\S+\s+(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{1,2}\s*(\S*)\s*$"
)

URL_LINE_RE = re.compile(r"^>\s*原文地址[:：]\s*\[([^\]]+)\]\(([^)]+)\)")


def has_frontmatter_cleaned(text: str) -> bool:
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end < 0:
        return False
    return "cleaned: true" in text[:end]


def strip_css(line: str) -> str:
    """从首行中剥离 CSS 块,只留下真正的文本内容(通常是标题)。"""
    # 删除所有 ".class { ... }" 或 "tag { ... }" 之类的 CSS 块
    cleaned = CSS_BLOCK_RE.sub("", line)
    # 删除残留 backslash-escape (markdown 转义)
    cleaned = re.sub(r"\\([*_{}\[\]()#+\-.!])", r"\1", cleaned)
    return cleaned.strip()


def parse_article(text: str) -> dict:
    """从 exporter 原始 .md 文本里抽出结构化字段 + 干净正文。"""
    lines = text.splitlines()

    title = None
    author = None
    date = None
    source_url = None
    body_start = 0

    # Step 1: 找标题 — 通常在 "====" 下划线分隔上方
    for i, line in enumerate(lines[:20]):
        if re.match(r"^={5,}\s*$", line.strip()) and i > 0:
            raw_title_line = lines[i - 1]
            # 这行可能是 "标题。" 或 "缩进 标题。 CSS 残渣"
            title = strip_css(raw_title_line).rstrip("。.")
            break

    # 如果没找到 ===,降级用第一行(去 CSS 后)
    if not title:
        for line in lines[:5]:
            cleaned = strip_css(line)
            if cleaned:
                title = cleaned.rstrip("。.")
                break

    # Step 2: 扫前 25 行找元数据 + URL
    for i, line in enumerate(lines[:25]):
        if not author or not date:
            m = META_LINE_RE.match(line.strip())
            if m:
                author = m.group(1)
                date = f"{m.group(2)}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
        if not source_url:
            m = URL_LINE_RE.match(line.strip())
            if m:
                source_url = m.group(2)
                body_start = i + 1

    # Step 3: 正文从 body_start 开始(如果没找到 URL 行,降级:从 === 后面开始)
    if body_start == 0:
        for i, line in enumerate(lines[:20]):
            if re.match(r"^={5,}\s*$", line.strip()):
                body_start = i + 1
                break

    body_lines = lines[body_start:]
    # 跳过开头连续空行
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    body = "\n".join(body_lines).strip()
    # 折叠多空行
    body = re.sub(r"\n{3,}", "\n\n", body)

    return {
        "title": title or "未知标题",
        "author": author or "",
        "date": date or "",
        "source_url": source_url or "",
        "body": body,
    }


def render_cleaned(parsed: dict) -> str:
    fm_lines = ["---"]
    fm_lines.append(f'title: "{parsed["title"]}"')
    if parsed["author"]:
        fm_lines.append(f'author: "{parsed["author"]}"')
    if parsed["date"]:
        fm_lines.append(f'date: {parsed["date"]}')
    if parsed["source_url"]:
        fm_lines.append(f'source_url: {parsed["source_url"]}')
    fm_lines.append("source: wechat-article-exporter")
    fm_lines.append("cleaned: true")
    fm_lines.append("---")
    fm_lines.append("")
    fm_lines.append(f"# {parsed['title']}")
    fm_lines.append("")
    fm_lines.append(parsed["body"])
    return "\n".join(fm_lines) + "\n"


def clean_file(md_path: Path, account: str, force: bool, dry_run: bool) -> str:
    text = md_path.read_text(encoding="utf-8", errors="ignore")

    if has_frontmatter_cleaned(text) and not force:
        return "skip"

    parsed = parse_article(text)

    if dry_run:
        return f"would-clean (title={parsed['title'][:30]}, date={parsed['date']})"

    # 第一次清洗:备份原文
    backup_dir = RAW_BACKUP / account
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / (md_path.stem + ".raw.md")
    if not backup_path.exists():
        shutil.copy2(md_path, backup_path)

    cleaned_text = render_cleaned(parsed)
    md_path.write_text(cleaned_text, encoding="utf-8")
    return "cleaned"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", choices=ACCOUNTS + ["all"], default="all")
    parser.add_argument("--force", action="store_true", help="强制重洗已清洗的")
    parser.add_argument("--dry-run", action="store_true", help="只看不动")
    args = parser.parse_args()

    targets = ACCOUNTS if args.account == "all" else [args.account]

    total_stats = {"cleaned": 0, "skip": 0, "error": 0}

    for account in targets:
        account_dir = CORPUS_DIR / account
        if not account_dir.exists():
            print(f"⚠ {account}/ 不存在,跳过")
            continue
        files = sorted(account_dir.glob("*.md"))
        if not files:
            print(f"⚠ {account}/ 没有 .md 文件")
            continue
        print(f"\n>>> {account}/ ({len(files)} 篇)")
        for md in files:
            try:
                result = clean_file(md, account, args.force, args.dry_run)
                if result == "cleaned":
                    total_stats["cleaned"] += 1
                    print(f"  ✓ {md.name}")
                elif result == "skip":
                    total_stats["skip"] += 1
                elif result.startswith("would-clean"):
                    print(f"  · {md.name} — {result}")
            except Exception as e:
                total_stats["error"] += 1
                print(f"  ✗ {md.name}: {e}")

    print(f"\n汇总: 清洗 {total_stats['cleaned']}, 跳过(已清洗) {total_stats['skip']}, 失败 {total_stats['error']}")
    if not args.dry_run and total_stats["cleaned"] > 0:
        print(f"原文备份在: {RAW_BACKUP}")
        print(f"建议接着跑: python tools/build_corpus_index.py")


if __name__ == "__main__":
    main()
