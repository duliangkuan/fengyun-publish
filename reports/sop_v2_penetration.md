# SOP v2 多维度规则系统:穿透测试报告

*生成时间:2026-05-21 10:43:56*

## 测试设计

- **测试集**:2026 H1 hold-out(617 篇,所有模型/规则训练时均未见过)
- **target**:composite_pct = 0.40·read + 0.20·share + 0.15·like + 0.15·old_like + 0.10·comment
- **SOP v1**:单维度规则,基于深挖 5-10 方向性结论,11 类规则
- **SOP v2**(本次):5 维度规则(read/share/like/old_like/comment),feature 分配基于 pre-2026 训练集 ρ(feat, sub-target) 真实大小,**不在 hold-out 上调参**
- **critic v2**:LGB 近 12 个月窗口训练(n=1383)

## SOP v2 五维度设计

总分公式(同 composite_pct 权重):
```
total = 0.40·read + 0.20·share + 0.15·like + 0.15·old_like + 0.10·comment
```

### Feature → 维度分配(基于 pre-2026 训练集 ρ vs 各 sub-target)

| 维度 | 主要 features(ρ vs 该 sub-target) | ρ 出处 |
|---|---|---|
| read (40%) | t_chars / t_english_chars / 品牌词 / 封面色 / topic_hotness_30d (ρ=0.32) / current_event_words_in_title | brand_words.md + title_deep.md + cover_color_deep.md + topic_hotness 探针 |
| share (20%) | b_chars (ρ=0.29) / b_para_avg_chars (ρ=0.30) / jb_lexical_diversity (ρ=-0.26) / tb_ratio (ρ=-0.24) / cover_brightness (ρ=0.32) / img_per_1k_chars / topic_hotness_90d (ρ=0.38) / comment_long_ratio | word_count_analysis + paragraph_structure + image_density |
| like (15%) | topic_hotness_90d (ρ=0.42) / topic_hotness_30d (ρ=0.40) / action_verb_count (ρ=0.21) / opinion_strength_markers / cultural_meme / comment_ip_diversity / comment_avg_length | topic_hotness_dynamic.md + semantic_features.md |
| old_like (15%) | controversy_markers / first_person_density (ρ=0.17) / jb_avg_word_len (ρ=-0.20) / comment_long_ratio (ρ=0.20) / cultural_meme | semantic_features.md + 探针 |
| comment (10%) | comment_question_ratio (ρ=0.24) / comment_ip_diversity (ρ=0.23) / comment_sentiment_neg_ratio / personal_pronoun_in_title / interaction_call_in_title / first_person_density / opinion_strength_markers | comments_insights_v3.md + 探针 |

*所有 ρ 数值在 pre-2026 训练集 n=2106 上计算,详见 `reports/_sop_v2_feature_rho.csv`*

## 三方对比(2026 H1 hold-out)

| 指标 | SOP v1 | SOP v2 | critic v2 | 最优 |
|---|---|---|---|---|
| R² | -1.208 | **-0.471** 🏆 | -2.188 | SOP v2 |
| Spearman ρ | +0.247 | **+0.337** 🏆 | +0.158 | SOP v2 |
| MAE(越低越好) | 18.4 | **16.7** 🏆 | 24.8 | SOP v2 |
| Top 10% 精度 | 13.1% | **24.6%** 🏆 | 11.5% | SOP v2 |
| Top 30% 精度 | 40.5% | **45.9%** 🏆 | 36.8% | SOP v2 |
| Bottom 10% 精度 | 23.0% | **32.8%** 🏆 | 19.7% | SOP v2 |
| 分箱准确率 | **56.7%** 🏆 | 47.5% | 29.0% | SOP v1 |
| 预测 std | **22.3** 🏆 | 8.6 | 11.7 | SOP v1 |

## SOP v2 各维度 vs 各 sub-target ρ(穿透诊断)

(每个维度应该在自己对应的 sub-target 上 ρ 最强,验证维度切分有效性)

| 维度评分 | vs read | vs share | vs like | vs old_like | vs comment |
|---|---|---|---|---|---|
| read_score | +0.235 | +0.381 | +0.255 | +0.217 | +0.104 |
| share_score | +0.150 | +0.272 | +0.244 | +0.170 | +0.027 |
| like_score | +0.212 | +0.268 | +0.223 | +0.206 | +0.217 |
| old_like_score | +0.094 | +0.118 | +0.204 | +0.200 | +0.323 |
| comment_score | +0.059 | +0.108 | +0.078 | +0.082 | +0.300 |

## SOP v2 反馈样例:5 爆款 + 5 扑街

### Top 5 爆款(真实 composite_pct 最高)

### 爆款 1: [baoyu] Vibe Coding 是中年男人的钓鱼

- **真实 composite_pct**:99.8
- **SOP v2 总分**:67.5(read=77, share=69, like=62, old_like=55, comment=53)
- SOP v1=83.0,critic v2=54.3

**加分项**(做对的地方):
  - [read] 标题字数 20 在 20-40 区间(+3)
  - [read] 标题英文字数 10 (≥8)(+8)
  - [read] 标题含 Vibe Coding(+10)
  - [read] 封面色家族=white(+6)
  - [share] 平均段长 590 ≥200(+8)
  - [share] tb_ratio 0.017 <0.05(+3)

**扣分项**(踩坑):
  - [share] 词汇多样性 0.52 >0.5(短文)(-3)

**改进建议**(按预期收益排序):
  - [old_like] 加 2-3 处明确立场/反共识观点(预期 +8)
  - [like] 加 3-5 个动作动词(做了/试了/写了/拆了),提升 av 密度到 1.5+(预期 +6)
  - [comment] 标题末尾加问句或互动召唤(预期 +5)
  - [comment] 标题加「你」或「我」唤起对话(预期 +4)

### 爆款 2: [huashu] 开源「女娲.skill」，你现在可以去蒸馏任何人！

- **真实 composite_pct**:99.5
- **SOP v2 总分**:77.0(read=85, share=94, like=68, old_like=55, comment=57)
- SOP v1=100.0,critic v2=60.0

**加分项**(做对的地方):
  - [read] 标题字数 25 在 20-40 区间(+3)
  - [read] 标题英文字数 5 (≥3)(+3)
  - [read] 标题含 Skills(88.9%爆款率)(+15)
  - [read] 封面色家族=white(+6)
  - [read] 主题 30d 热度 1.00 前 10%(+8)
  - [share] 正文 4103字 在 3500-5500 黄金区(+12)

**扣分项**(踩坑):
  (无)

**改进建议**(按预期收益排序):
  - [old_like] 加 2-3 处明确立场/反共识观点(预期 +8)
  - [like] 加 3-5 个动作动词(做了/试了/写了/拆了),提升 av 密度到 1.5+(预期 +6)
  - [comment] 标题末尾加问句或互动召唤(预期 +5)
  - [comment] 标题加「你」或「我」唤起对话(预期 +4)

### 爆款 3: [baoyu] 燃尽、重启、爆火：Clawdbot 创始人的 35 分钟访谈实录

- **真实 composite_pct**:99.3
- **SOP v2 总分**:73.4(read=71, share=98, like=67, old_like=65, comment=56)
- SOP v1=100.0,critic v2=44.0

**加分项**(做对的地方):
  - [read] 标题字数 32 在 20-40 区间(+3)
  - [read] 标题英文字数 8 (≥8)(+8)
  - [read] 封面色家族=white(+6)
  - [read] 主题 30d 热度 0.65 中等偏热(+4)
  - [share] 正文 6816字 (5500-8000)(+10)
  - [share] 平均段长 3407 ≥200(+8)

**扣分项**(踩坑):
  (无)

**改进建议**(按预期收益排序):
  - [read] 标题加 1 个热门品牌词(Skills/Claude/Anthropic)(预期 +10)
  - [comment] 标题末尾加问句或互动召唤(预期 +5)
  - [comment] 标题加「你」或「我」唤起对话(预期 +4)

### 爆款 4: [saiboshanxin] 我们，已迈过奇点

- **真实 composite_pct**:99.2
- **SOP v2 总分**:58.2(read=49, share=76, like=59, old_like=57, comment=60)
- SOP v1=72.0,critic v2=66.4

**加分项**(做对的地方):
  - [read] 封面色家族=dark(+5)
  - [share] 正文 3295字 (2500-3500)(+5)
  - [share] 平均段长 1646 ≥200(+8)
  - [share] 词汇多样性 0.39 <0.42(长文)(+4)
  - [share] tb_ratio 0.002 <0.05(+3)
  - [share] 图片密度 2.7/千字 在 2-6(+6)

**扣分项**(踩坑):
  - [read] 标题过短(8字)(-3)
  - [read] 标题英文字数仅 0(-3)
  - [share] 封面亮度 32 <80(暗)(-3)

**改进建议**(按预期收益排序):
  - [read] 标题加 1 个英文产品名/品牌(如 Claude Code/Skills)(预期 +11)
  - [read] 标题加 1 个热门品牌词(Skills/Claude/Anthropic)(预期 +10)
  - [share] 封面换更亮的图(亮度≥200)(预期 +8)
  - [old_like] 加 2-3 处明确立场/反共识观点(预期 +8)
  - [share] 再加 1000-2000 字案例/数据,推到 3500-5500(预期 +7)

### 爆款 5: [baoyu] Harness 工程就是控制论

- **真实 composite_pct**:99.2
- **SOP v2 总分**:62.1(read=59, share=84, like=53, old_like=58, comment=50)
- SOP v1=82.0,critic v2=54.2

**加分项**(做对的地方):
  - [read] 标题英文字数 7 (≥3)(+3)
  - [read] 封面色家族=white(+6)
  - [share] 正文 2660字 (2500-3500)(+5)
  - [share] 平均段长 1329 ≥200(+8)
  - [share] 词汇多样性 0.38 <0.42(长文)(+4)
  - [share] tb_ratio 0.006 <0.05(+3)

**扣分项**(踩坑):
  (无)

**改进建议**(按预期收益排序):
  - [read] 标题加 1 个热门品牌词(Skills/Claude/Anthropic)(预期 +10)
  - [share] 再加 1000-2000 字案例/数据,推到 3500-5500(预期 +7)
  - [like] 加 3-5 个动作动词(做了/试了/写了/拆了),提升 av 密度到 1.5+(预期 +6)
  - [comment] 标题末尾加问句或互动召唤(预期 +5)
  - [like] 加 2-3 处强观点表态(我认为/必须/绝对)(预期 +4)

### Bottom 5 扑街(真实 composite_pct 最低)

### 扑街 1: [saiboshanxin] 70万奖金，邀你写算法：代码将合入 SGLang 主线

- **真实 composite_pct**:22.0
- **SOP v2 总分**:60.1(read=61, share=80, like=53, old_like=45, comment=50)
- SOP v1=91.0,critic v2=53.2

**加分项**(做对的地方):
  - [read] 标题字数 27 在 20-40 区间(+3)
  - [read] 标题英文字数 6 (≥3)(+3)
  - [read] 封面色家族=dark(+5)
  - [share] 正文 4494字 在 3500-5500 黄金区(+12)
  - [share] 平均段长 2246 ≥200(+8)
  - [share] 词汇多样性 0.38 <0.42(长文)(+4)

**扣分项**(踩坑):
  - [share] 封面亮度 29 <80(暗)(-3)
  - [old_like] 第一人称密度 0.00(低,缺共鸣)(-3)
  - [old_like] 平均词长 2.11 偏书面(-4)

**改进建议**(按预期收益排序):
  - [read] 标题加 1 个热门品牌词(Skills/Claude/Anthropic)(预期 +10)
  - [old_like] 加 5-10 处第一人称体验(我试了/我发现)(预期 +9)
  - [old_like] 把长术语换成日常说法,降低词长(预期 +9)
  - [share] 封面换更亮的图(亮度≥200)(预期 +8)
  - [old_like] 加 2-3 处明确立场/反共识观点(预期 +8)

### 扑街 2: [saiboshanxin] 这几个月，太快了…快到什么程度呢，快到每天早上醒来，昨天的消息已经不重要了

一

- **真实 composite_pct**:23.2
- **SOP v2 总分**:44.9(read=46, share=22, like=52, old_like=55, comment=60)
- SOP v1=22.0,critic v2=48.8

**加分项**(做对的地方):
  - [read] 标题英文字数 5 (≥3)(+3)
  - [read] 标题含 Agent/智能体(+3)
  - [like] 强观点密度 4.29(中)(+2)
  - [old_like] 第一人称密度 4.29(中)(+3)
  - [old_like] 长评论比 20%(+2)
  - [comment] 评论 IP 多样性 0.70(+3)

**扣分项**(踩坑):
  - [read] 无封面(-10)
  - [share] 正文仅 477字 太短(-8)
  - [share] 平均段长 38 <50 太碎(-4)
  - [share] 词汇多样性 0.53 >0.5(短文)(-3)
  - [share] tb_ratio 0.954 >0.15 标题占比过大(-5)

**改进建议**(按预期收益排序):
  - [share] 扩到 3000+ 字,加完整案例/数据(预期 +20)
  - [read] 补一张暖橙/白底封面图(预期 +16)
  - [read] 标题加 1 个热门品牌词(Skills/Claude/Anthropic)(预期 +10)
  - [share] 段落合并/扩写到平均 100+ 字(预期 +8)
  - [share] 封面换更亮的图(亮度≥200)(预期 +8)

### 扑街 3: [saiboshanxin] 英伟达 CES 2026：六款芯片，一台 AI 超算

- **真实 composite_pct**:24.7
- **SOP v2 总分**:57.6(read=61, share=67, like=53, old_like=43, comment=54)
- SOP v1=79.0,critic v2=45.9

**加分项**(做对的地方):
  - [read] 标题字数 26 在 20-40 区间(+3)
  - [read] 标题英文字数 5 (≥3)(+3)
  - [read] 封面色家族=dark(+5)
  - [share] 正文 3456字 (2500-3500)(+5)
  - [share] 平均段长 1727 ≥200(+8)
  - [share] 词汇多样性 0.41 <0.42(长文)(+4)

**扣分项**(踩坑):
  - [share] 封面亮度 11 <80(暗)(-3)
  - [old_like] 第一人称密度 0.57(低,缺共鸣)(-3)
  - [old_like] 平均词长 2.49 偏书面(-4)

**改进建议**(按预期收益排序):
  - [read] 标题加 1 个热门品牌词(Skills/Claude/Anthropic)(预期 +10)
  - [old_like] 加 5-10 处第一人称体验(我试了/我发现)(预期 +9)
  - [old_like] 把长术语换成日常说法,降低词长(预期 +9)
  - [share] 封面换更亮的图(亮度≥200)(预期 +8)
  - [old_like] 加 2-3 处明确立场/反共识观点(预期 +8)

### 扑街 4: [saiboshanxin] 史诗级突破：用 GLM-5 完整复刻 GBA 模拟器（附：长任务 Prompt 

- **真实 composite_pct**:25.2
- **SOP v2 总分**:68.2(read=66, share=91, like=63, old_like=54, comment=60)
- SOP v1=93.0,critic v2=63.3

**加分项**(做对的地方):
  - [read] 标题英文字数 12 (≥8)(+8)
  - [read] 封面色家族=white(+6)
  - [read] 主题 30d 热度 0.68 中等偏热(+4)
  - [read] 标题含时事词(+3)
  - [share] 正文 3606字 在 3500-5500 黄金区(+12)
  - [share] 平均段长 1802 ≥200(+8)

**扣分项**(踩坑):
  - [read] 标题含 GLM/智谱(冷标签)(-5)
  - [share] 无配图(-3)

**改进建议**(按预期收益排序):
  - [read] 标题加 1 个热门品牌词(Skills/Claude/Anthropic)(预期 +10)
  - [share] 加 3-6 张说明图(密度 2-6/千字)(预期 +9)
  - [old_like] 加 2-3 处明确立场/反共识观点(预期 +8)
  - [comment] 标题末尾加问句或互动召唤(预期 +5)
  - [comment] 标题加「你」或「我」唤起对话(预期 +4)

### 扑街 5: [saiboshanxin] OpenAI 的 ARPU 困境：用户遍全球，钱不好赚

- **真实 composite_pct**:25.2
- **SOP v2 总分**:57.4(read=62, share=63, like=53, old_like=45, comment=53)
- SOP v1=67.0,critic v2=43.4

**加分项**(做对的地方):
  - [read] 标题字数 27 在 20-40 区间(+3)
  - [read] 标题英文字数 10 (≥8)(+8)
  - [read] 封面色家族=white(+6)
  - [share] 平均段长 465 ≥200(+8)
  - [share] tb_ratio 0.029 <0.05(+3)
  - [share] 封面亮度 255 ≥200(明亮)(+5)

**扣分项**(踩坑):
  - [read] 标题含 OpenAI/GPT(冷标签)(-5)
  - [share] 词汇多样性 0.51 >0.5(短文)(-3)
  - [old_like] 第一人称密度 0.00(低,缺共鸣)(-3)
  - [old_like] 平均词长 2.03 偏书面(-4)

**改进建议**(按预期收益排序):
  - [read] 主品牌词换成 Claude/Anthropic(预期 +15)
  - [read] 标题加 1 个热门品牌词(Skills/Claude/Anthropic)(预期 +10)
  - [old_like] 加 5-10 处第一人称体验(我试了/我发现)(预期 +9)
  - [old_like] 把长术语换成日常说法,降低词长(预期 +9)
  - [old_like] 加 2-3 处明确立场/反共识观点(预期 +8)

## 学术诚实结论

- 🟡 SOP v2 ρ=0.337 未达 0.35 目标
- SOP v2 ρ - SOP v1 ρ = +0.090(多维度提升)
- ✅ SOP v2 ρ=0.337 > critic v2 ρ=0.158 — 规则系统胜过 ML

**SOP v2 预测 std=8.6,真实 std=16.3** — 仍较保守

## 反馈机制说明

sop_score_v2(row) 输出结构:
```python
{
  'total_score': float,
  'read_score' / 'share_score' / 'like_score' / 'old_like_score' / 'comment_score': float,
  'rules_triggered': [{'dim','rule','delta','type':'bonus|penalty'}, ...],
  'suggestions': [{'dim','action','expected_delta'}, ...] # 按 expected_delta 降序
}
```
- `rules_triggered`:让 writer 看到每个维度做对/做错的地方
- `suggestions`:针对扣分项和未拿到的 bonus 给出可执行 action
- 单条建议附带预期收益,writer 可按 ROI 取舍
