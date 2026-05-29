# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, 'D:/Dev/ai-wechat-pipeline')
with open('D:/Dev/ai-wechat-pipeline/output/candidates/20260525.json', encoding='utf-8') as f:
    data = json.load(f)
from tools.topic_recommender import rank_aihot_candidates
items = data['items']
ranked = rank_aihot_candidates(items)
for i, item in enumerate(ranked[:15], 1):
    title = item.get('title', '')[:60]
    score = item.get('_score', 0)
    reason = (item.get('_reason', '') or '')[:80]
    print(f'{i}. [{score:.2f}] {title}')
    print(f'   理由: {reason}')
    print()
