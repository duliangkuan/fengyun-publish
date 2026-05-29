# -*- coding: utf-8 -*-
"""Check ending signal"""
import sys
sys.path.insert(0, 'D:/Dev/ai-wechat-pipeline')

from tools.ending_signal import score_ending_signal
from tools.ending_dedup import check_ending_overlap

with open('D:/Dev/ai-wechat-pipeline/output/drafts/20260525-skillopt-self-evolving-agent-v0.md', encoding='utf-8') as f:
    text = f.read()

sig = score_ending_signal(text)
print('=== ending_signal ===')
for k, v in sig.items():
    if isinstance(v, float):
        print(f'  {k}: {v:.2f}')
    elif isinstance(v, dict):
        print(f'  {k}:')
        for k2, v2 in v.items():
            print(f'    {k2}: {v2}')
    else:
        print(f'  {k}: {v}')

print(f'\nverdict: {sig.get("verdict", "N/A")}')
