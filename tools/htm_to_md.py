"""
备胎:浏览器"另存为 网页"得到的 .htm/.html 文件批量转 .md。

用法:
  python tools/htm_to_md.py --src "C:/Users/23303/Downloads" --dst corpus/kazik
  python tools/htm_to_md.py --src ./some-folder --dst corpus/baoyu --recursive

依赖: pip install markdownify
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from markdownify import markdownify as md_convert

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def slugify(s: str) -> str:
    s = re.sub(r"[\\/:*?\"<>|]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s[:80] if s else "untitled"


def extract_title(html: str, fallback: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()
        title = re.sub(r"\s*[-—–|]\s*微信公众号.*$", "", title)
        title = re.sub(r"\s*[-—–|]\s*\S+\s*$", "", title) if " - " in title else title
        return title or fallback
    return fallback


def convert_one(src: Path, dst_dir: Path) -> Path | None:
    try:
        html = src.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"  ! 读失败 {src.name}: {e}")
        return None

    title = extract_title(html, src.stem)
    # 抽正文 — 微信公众号文章正文在 <div id="js_content">
    m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*</div>', html, flags=re.DOTALL)
    body_html = m.group(1) if m else html

    md_text = md_convert(
        body_html,
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
    )
    md_text = re.sub(r"\n{3,}", "\n\n", md_text).strip()

    out_name = f"{slugify(title)}.md"
    dst = dst_dir / out_name
    if dst.exists():
        dst = dst.with_stem(dst.stem + f"-{src.stem[:8]}")

    dst.write_text(f"# {title}\n\n{md_text}\n", encoding="utf-8")
    return dst


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="HTM/HTML 文件所在目录")
    parser.add_argument("--dst", required=True, help="输出目录")
    parser.add_argument("--recursive", action="store_true", help="递归扫子目录")
    args = parser.parse_args()

    src_dir = Path(args.src).expanduser().resolve()
    dst_dir = Path(args.dst).expanduser().resolve()
    if not src_dir.is_dir():
        raise SystemExit(f"源目录不存在: {src_dir}")
    dst_dir.mkdir(parents=True, exist_ok=True)

    pattern = "**/*.htm*" if args.recursive else "*.htm*"
    files = list(src_dir.glob(pattern))
    if not files:
        raise SystemExit(f"在 {src_dir} 没找到 .htm/.html")

    ok = fail = 0
    for f in files:
        out = convert_one(f, dst_dir)
        if out:
            print(f"✓ {f.name} → {out.name}")
            ok += 1
        else:
            fail += 1

    print(f"\n完成: 成功 {ok} 篇, 失败 {fail} 篇")
    print(f"输出目录: {dst_dir}")


if __name__ == "__main__":
    main()
