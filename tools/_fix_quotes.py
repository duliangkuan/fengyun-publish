import sys
from pathlib import Path

p = Path(r"D:\Dev\ai-wechat-pipeline\output\drafts\20260525-trapdoor-ai-supply-chain.md")
text = p.read_text(encoding="utf-8")
parts = text.split("---", 2)
body = parts[2]

new_body = []
toggle = False
for c in body:
    if c == chr(0x22):  # ASCII double quote
        if not toggle:
            new_body.append(chr(0x201C))  # left "
            toggle = True
        else:
            new_body.append(chr(0x201D))  # right "
            toggle = False
    else:
        new_body.append(c)

parts[2] = "".join(new_body)
p.write_text("---".join(parts), encoding="utf-8")
print("Fixed all ASCII quotes to Chinese quotes")
