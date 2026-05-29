# wechat-ai-pubaccount-critic Skill 设计报告

生成时间: 2026-05-21
Skill 路径: C:\Users\23303\.claude\skills\wechat-ai-pubaccount-critic\

---

## 1. SKILL.md 主文件结构

```
SKILL.md 章节:
  - 触发条件(评分/打分/critic/SOP 等关键词)
  - 3 层评分体系图(ASCII 树形图)
  - Step 1: 调用 SOP v2 (Layer 1)
  - Step 2: LLM 内容质量评分 (Layer 2) + 完整 Prompt 模板
  - Step 3: 综合 final_score (Layer 3)
  - Step 4: 输出格式(JSON 结构)
  - Step 5: 与 writer skill 协作
  - 参考文件索引表
  - 关键约束(P0 铁律)
```

---

## 2. LLM-judge 4 维评分 Prompt 模板摘要

Prompt 模板核心结构(完整版在 SKILL.md Step 2):

```
你是 AI 公众号内容质量评审。评以下 4 维,每维 1-10 分。

规则:每维必须从原文摘录 1-3 条证据句(格式:「引文」— 第N段)
     找不到证据 → 评分上限 4 分
     评分锚点:1-3=差 / 4-6=中 / 7-8=好 / 9-10=极好

4 维:
  opinion_depth   — 独立判断?反驳主流?论证充分?
  narrative_rhythm — 英雄之旅弧?自然转折?段落连贯?
  authenticity    — 第一手体验?具体细节?自嘲承认?
  logic           — 主线清晰?论点站得住?无矛盾?

输出:纯 JSON,含每维 score + evidence 数组
```

---

## 3. Final Score 综合公式

```
final_score = round(0.80 × sop_v2_total + 0.20 × llm_avg_100, 1)

其中:
  sop_v2_total = sop_score_v2(row)["total_score"]   (0-100)
  llm_avg_100  = (opinion_depth + narrative_rhythm + authenticity + logic) / 4 × 10
```

**权重说明**:80/20 为先验设定,待积累 50+ 篇 hold-out 数据后用 OLS 回归校准。

---

## 4. 与 writer skill 协作方式

```
writer 生成初稿
     ↓
critic 返回 JSON → writer 读 suggestions[0:3] + dimension_breakdown
     ↓
writer 按 Top-3 ROI 修改文章
     ↓
critic 再次评分(输出 delta 对比)
     ↓
最多 3 轮循环 → publish_recommendation
```

writer 强制规则:
- authenticity ≤ 4 → 必须补第一手体验段
- opinion_depth ≤ 4 → 必须补"我认为 X,因为 Y"观点段
- final_score < 60 → 不建议发布,提示用户

---

## 5. 文件清单

| 路径 | 内容 |
|------|------|
| `skills/wechat-ai-pubaccount-critic/SKILL.md` | 主入口,触发条件+3层体系+完整流程 |
| `references/sop-v2-integration.md` | Python 调用方式+feature 字段对照表 |
| `references/llm-judge-rubric.md` | 4维细则+锚点+正负向信号+证据示例 |
| `references/final-score-composition.md` | 综合公式+权重说明+区间解读+校准计划 |
| `references/feedback-template.md` | 用户展示格式+JSON结构+writer协作协议 |
| `examples/score-example-1.md` | 高分案例(Vibe Coding 钓鱼,actual=99.8) |
| `examples/score-example-2.md` | 低分案例(70万奖金通告,actual=22.0) |

---

## 6. 关键设计决策

- **LLM 权重上限 20%**:用户 P0 铁律,不可突破
- **证据必须摘原文**:防止 LLM 编造评分理由
- **权重标"可调"**:等待 hold-out 校准,不宣称"最优"
- **sop_v2.py 不修改**:规则层和 LLM 层完全解耦
- **3 轮迭代上限**:防止 writer-critic 无限 loop

---

## 7. 样例验证结果

| 文章 | actual | sop_v2 | llm_judge | final | 误差改善 |
|------|--------|--------|-----------|-------|----------|
| Vibe Coding 钓鱼 | 99.8 | 67.5 | 85.0 | 71.0 | 误差从 32.3 → 28.8 |
| 70万奖金通告 | 22.0 | 60.1 | 27.5 | 53.6 | 误差从 38.1 → 31.6 |

结论:LLM-judge 在两个样例上均缩小了预测误差,方向正确。
