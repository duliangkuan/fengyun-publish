# -*- coding: utf-8 -*-
"""Run fengyun_lint"""
import sys, json
sys.path.insert(0, 'D:/Dev/ai-wechat-pipeline')

from pathlib import Path
from tools.fengyun_lint import lint_article

draft_path = Path('D:/Dev/ai-wechat-pipeline/output/drafts/20260525-skillopt-self-evolving-agent-v0.md')
r = lint_article(draft_path)

violations = r.get('violations', [])
print(f'Total violations: {len(violations)}')
high_count = sum(1 for v in violations if v.get('severity') == 'high')
med_count = sum(1 for v in violations if v.get('severity') in ('medium', 'mid'))
print(f'High severity: {high_count}')
print(f'Medium severity: {med_count}')

for v in violations:
    sev = v.get('severity', '')
    rid = v.get('rule_id', '')
    msg = v.get('message', '')[:100]
    print(f'  [{sev}] {rid}: {msg}')
