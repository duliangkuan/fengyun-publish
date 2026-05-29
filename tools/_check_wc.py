# -*- coding: utf-8 -*-
import re

with open("D:/Dev/ai-wechat-pipeline/output/drafts/20260525-skillopt-self-evolving-agent-v0.md", encoding="utf-8") as f:
    content = f.read()

parts = content.split("---", 2)
body = parts[2] if len(parts) >= 3 else content

chinese_chars = len(re.findall(r"[一-鿿]", body))
english_words = len(re.findall(r"[a-zA-Z]+", body))
total = chinese_chars + english_words
print(f"Body Chinese chars: {chinese_chars}")
print(f"Body English words: {english_words}")
print(f"Body total (char+word): {total}")
print(f"Full file length: {len(content)}")
print(f"Body character count (incl spaces): {len(body)}")
