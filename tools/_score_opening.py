# -*- coding: utf-8 -*-
"""Score the opening for dogfood gate - v3 (final retry)"""
import sys, json, os
sys.path.insert(0, 'D:/Dev/ai-wechat-pipeline')

from tools.opening_signal import score_opening_signal

opening_text = """我们停下来想一个问题：写 prompt 这件事，到底算手艺还是玄学？

说它是手艺吧，我们心里都清楚——同样的需求，换几个词，输出天差地别；说它是玄学吧，好像又真有那么些隐形的规律在。我们每个人跟 AI 打交道的朋友，都在这个灰色地带里摸爬滚打。这不丢人，因为我们不是第一批，也不会是最后一批。

但今天，我们看到了一个不同的答案。

微软亚洲研究院联合上海交大、同济、复旦，发了一篇论文叫 SkillOpt。不是什么 fancy 的新模型、新框架——它的想法出奇的朴素：把技能文档当成"外部状态"，像训练深度学习一样去优化它。有学习率、有验证集、有动量机制。不是玄学改 prompt，而是系统化训练 skill。

结果呢？6 个测试基准，7 个模型，3 种执行框架，52 个测试单元，全部最优。GPT-5.5 平均提升 23.5 分。小模型 Qwen3.5-4B 在 ALFWorld 上从 30.6 分跳到 81.3 分。

我们不是第一次听到"AI 自己优化自己"这种说法了。但看到数据的那一刻，我们还是愣了一愣。

如果这篇论文的方向是对的，那写 prompt 这件事，可能会从手工时代撞进自动化时代。而我们这些一直手动调 prompt 的人，该作何感想？"""

sig = score_opening_signal(opening_text)
print('=== opening_signal v3 ===')
for k, v in sig.items():
    if isinstance(v, float):
        print(f'{k}: {v:.2f}')
    elif isinstance(v, dict):
        print(f'{k}:')
        for k2, v2 in v.items():
            print(f'  {k2}: {v2}')
    else:
        print(f'{k}: {v}')

print(f'\n=== 判定 ===')
dims = {'concreteness': '具体性', 'reframe': '反差感', 'emotion_anchor': '情绪锚点', 'info_density': '信息密度'}
for k, cn in dims.items():
    v = sig.get(k, 0)
    print(f'  {cn}: {"✅" if isinstance(v, (int, float)) and v >= 6 else "❌"} ({v})')
fp = sig.get("first_person_density", 0)
print(f' 第一人称密度: {fp:.1f}/千字 {"✅" if fp >= 5 else "❌"}')
print(f' 首段字数: {sig.get("first_para_chars", 0)}')
print(f' 新鲜度: {sig.get("formula_freshness", 0)}')
print(f' verdict: {sig.get("verdict", "")}')
