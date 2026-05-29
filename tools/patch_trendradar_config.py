"""
精准改 TrendRadar config.yaml:
1. 给 16 个 wechat-* feed URL 末尾加 ?limit=3(救 timeout 大坑)
2. 全局 rss.timeout 30 → 60
3. 不动其他 feed
"""
import re
import sys
from pathlib import Path

CONFIG = Path(r"D:\Dev\TrendRadar\config\config.yaml")
text = CONFIG.read_text(encoding="utf-8")

# 1) 给 wechat-* feed 的 URL 加 ?limit=3(如果已加则跳过)
# 匹配: url: "http://localhost:8001/feed/MP_WXS_<digits>.atom"
pattern = re.compile(
    r'(url:\s*"http://localhost:8001/feed/MP_WXS_\d+\.atom)(")'
)
def add_limit(m):
    return f"{m.group(1)}?limit=3{m.group(2)}"
new_text, n_url = pattern.subn(add_limit, text)
print(f"加 ?limit=3 的 URL 数: {n_url}")

# 防御:如果有的 URL 已经带 ?limit=N,不要重复加。先看是否已经带
already = re.findall(r'localhost:8001/feed/MP_WXS_\d+\.atom\?limit=\d+', new_text)
print(f"现在带 ?limit= 的 URL 总数: {len(already)}")

# 2) 全局 rss.timeout 30 → 60
# 找 "timeout: 30" 注释里写过 "2026-05-22 加:从默认 15s 调高到 30s"
# 但要小心只改 rss.timeout 不改 advanced.rss.timeout 或 ai.timeout
# config 里 line 95 附近的 rss: 下面的 timeout: 30
timeout_pattern = re.compile(
    r'(^rss:\s*\n\s+enabled:.*?\n\s+timeout:\s*)30(\s)',
    re.MULTILINE | re.DOTALL
)
new_text2, n_to = timeout_pattern.subn(r'\g<1>60\g<2>', new_text)
print(f"rss.timeout 30→60 改了 {n_to} 处")

# 备份原文件
backup = CONFIG.with_suffix(".yaml.bak.phase18_limit3")
backup.write_text(text, encoding="utf-8")
print(f"原文件备份: {backup}")

# 写入新内容
CONFIG.write_text(new_text2, encoding="utf-8")
print(f"已更新: {CONFIG}")

# 校验:打印改动 diff(上下文 1 行)
print("\n=== 改动 sample(前 3 个 wechat URL)===")
for m in list(pattern.finditer(text))[:3]:
    line_start = text.rfind("\n", 0, m.start()) + 1
    line_end = text.find("\n", m.end())
    old_line = text[line_start:line_end]
    new_line = new_text[line_start:line_end + len("?limit=3")]
    print(f"  - {old_line.strip()}")
    print(f"  + {new_line.strip()}")
