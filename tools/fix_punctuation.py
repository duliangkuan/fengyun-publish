"""
半角→全角标点替换工具 v3(逐字符扫描)

策略:逐字符遍历 body,prev 是中文时,ASCII 标点替换为全角。
保护:frontmatter / 代码块(```) / 行内代码(`) / URL 不动。
"""
from __future__ import annotations
import sys, re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 用显式 unicode codepoint 避免 Claude 写时下意识半角的 bug
PUNCT_MAP = {
    ",": chr(0xFF0C),  # ,
    ";": chr(0xFF1B),  # ;
    ":": chr(0xFF1A),  # :
    "!": chr(0xFF01),  # !
    "?": chr(0xFF1F),  # ?
    "(": chr(0xFF08),  # (
    ")": chr(0xFF09),  # )
}
FULL_PERIOD = chr(0x3002)        # 。
FULL_DQUOTE_OPEN = chr(0x201C)   # "
FULL_DQUOTE_CLOSE = chr(0x201D)  # "
FULL_SQUOTE_OPEN = chr(0x2018)   # '
FULL_SQUOTE_CLOSE = chr(0x2019)  # '

# 句号单独处理(避免 3.14 file.txt)
# 双引号配对处理


def is_cn(ch):
    return "一" <= ch <= "鿿" or "　" <= ch <= "〿" \
           or "＀" <= ch <= "￯"


def main():
    if len(sys.argv) < 2:
        print("用法: python fix_punctuation.py <markdown_path>")
        sys.exit(1)

    path = Path(sys.argv[1])
    raw = path.read_text(encoding="utf-8")

    # 切 frontmatter
    fm = ""
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            fm = "---" + parts[1] + "---"
            body = parts[2]

    # 用占位符保护代码块 / URL
    placeholders = {}
    counter = [0]

    def stash(m):
        key = f"\x00STASH{counter[0]}\x00"
        placeholders[key] = m.group(0)
        counter[0] += 1
        return key

    body = re.sub(r"```[\s\S]*?```", stash, body)
    body = re.sub(r"`[^`\n]+`", stash, body)
    body = re.sub(r"https?://[^\s\)]+", stash, body)

    # 逐字符扫描
    chars = list(body)
    n_changes = 0
    quote_state = False  # 双引号配对状态

    for i, ch in enumerate(chars):
        # 跳过占位符
        if ch == "\x00":
            quote_state = False
            continue

        # 句号特殊
        if ch == ".":
            # 前一字符是中文,后一字符是 中文/空格/句末/标点
            prev_cn = i > 0 and is_cn(chars[i-1])
            next_ok = (i + 1 >= len(chars)) or chars[i+1] in " \n\t" or is_cn(chars[i+1]) \
                      or chars[i+1] in ",。;:!?「」『』"
            if prev_cn and next_ok:
                chars[i] = FULL_PERIOD
                n_changes += 1
            continue

        # 双引号配对
        if ch == '"':
            line_has_cn = any(
                is_cn(chars[j]) for j in range(max(0, i-30), min(len(chars), i+30))
                if chars[j] != "\x00"
            )
            if line_has_cn:
                chars[i] = FULL_DQUOTE_OPEN if not quote_state else FULL_DQUOTE_CLOSE
                quote_state = not quote_state
                n_changes += 1
            continue

        # 单引号
        if ch == "'":
            prev_alpha = i > 0 and chars[i-1].isalpha() and chars[i-1].isascii()
            next_alpha = (i + 1 < len(chars)) and chars[i+1].isalpha() and chars[i+1].isascii()
            if prev_alpha or next_alpha:
                continue
            line_has_cn = any(
                is_cn(chars[j]) for j in range(max(0, i-30), min(len(chars), i+30))
                if chars[j] != "\x00"
            )
            if line_has_cn:
                chars[i] = FULL_SQUOTE_CLOSE
                n_changes += 1
            continue

        # 一般 ASCII 标点(只在中文上下文里替换)
        if ch in PUNCT_MAP:
            # prev 或 next 是中文 → 替换
            prev_cn = i > 0 and is_cn(chars[i-1])
            next_cn = (i + 1 < len(chars)) and is_cn(chars[i+1])
            # 中文+标点 / 标点+中文 → 全角
            if prev_cn or next_cn:
                chars[i] = PUNCT_MAP[ch]
                n_changes += 1

    body = "".join(chars)

    # 恢复占位符
    for key, val in placeholders.items():
        body = body.replace(key, val)

    result = fm + body if fm else body

    # 备份 + 写入
    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(raw, encoding="utf-8")
    path.write_text(result, encoding="utf-8")

    print(f"✓ {path.name}: 替换 {n_changes} 处标点")
    print(f"  备份: {backup}")


if __name__ == "__main__":
    main()
