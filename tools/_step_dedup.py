# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, 'D:/Dev/ai-wechat-pipeline')
from tools.event_dedup import check_event_dedup

with open('D:/Dev/ai-wechat-pipeline/output/candidates/20260525.json', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
skillopt = None
for item in items:
    if 'SkillOpt' in item.get('title', ''):
        skillopt = item
        break

if skillopt:
    title = skillopt.get('title', '')
    dedup = check_event_dedup(skillopt, days=7, include_published=True)
    print(f'Title: {title}')
    print(f'is_duplicate: {dedup.get("is_duplicate", "N/A")}')
    print(f'reason: {dedup.get("reason", "N/A")}')
    print(f'max_similarity: {dedup.get("max_similarity", "N/A")}')
    info = dedup.get('dedup_info', {})
    for k, v in info.items():
        if isinstance(v, str):
            print(f'  {k}: {v[:100]}')
else:
    print('SkillOpt item not found')
    for item in items[:5]:
        print(f'  - {item.get("title", "")[:60]}')
