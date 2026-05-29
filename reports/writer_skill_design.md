# wechat-ai-pubaccount-writer Skill 设计报告

*创建时间：2026-05-21*
*Skill 路径：C:\Users\23303\.claude\skills\wechat-ai-pubaccount-writer\*

---

## 设计决策

### 定位

- 补充 khazix-writer（不替代）
- khazix-writer = 风格层（卡兹克人格）
- 本 skill = 策略层（数据驱动 SOP）

### 数据来源

- PHASE1_FACTS.md（1200 行，2,730 篇文章）
- 深挖 2/5/6/7/8/9/10 + 严谨性 v2 calibration
- 所有数字均按 v2 降级为方向性建议

---

## 文件结构

```
wechat-ai-pubaccount-writer/
  SKILL.md                    ← 主入口，工作流 + 硬规则 + 选题热点 + 协作图
  references/
    topic-selection.md        ← 2026 热点主题详细数据 + 品牌词爆款率
    title-formulas.md         ← 7 钩子公式详解 + 标题校验 + 反面教材
    paragraph-strategy.md     ← 段落 SOP + 分桶数据 + 与 khazix-writer 关系
    cover-strategy.md         ← 色族排序 + 色相分析 + 亮度警告 + baoyu 协作
    fatal-combos.md           ← 致命组合 Top 3 + 单项阈值 + 假爆款识别
    sop-v2-integration.md     ← 调用方式 + 输出解读 + 真实样例 + 死角说明
```

---

## 关键提炼（v2 严谨性后的稳健结论）

### 最高置信度（跨 4 号 4/4 显著）

1. **字数方向性偏好**：3000-8000 字甜蜜点，20000+ 死亡区（2.0%）
2. **封面必须有色彩**：has_cover_color=1，效应量 d=0.69
3. **词汇多样性负相关**：爆款用词简单（目标 0.35）
4. **一行一段是劣势**：>70% 爆款率断崖至 18%

### 2026 新增高置信度

5. **Anthropic Skills / Claude Code 是唯一安全选题**：88-92% 爆款率
6. **标题必带英文产品名**：双高 89.8% vs 假爆款 70.6%，p=0.0006
7. **OpenAI/GPT 标题扣分**：Δ=-9.3pp，2026 已退出热点

### 方法论

- SOP v2（ρ=0.337）> critic ML v2（ρ=0.158）
- SOP 死角：时事热点 / 节日盘点 / 文化梗需人工加权
- 数据飞轮：每 3 月 retrain，只用近 12 个月数据

---

## Skill 协作链路

```
wechat-ai-pubaccount-writer（本 skill，策略层）
  ↓ 风格润色
khazix-writer（人格层）
  ↓ 配图
baoyu-article-illustrator
  ↓ 封面生成
baoyu-cover-image
  ↓ 排版
md2wechat
  ↓ 发布
wechat-article-publisher
```

---

## 触发场景

用户说以下任意一类时激活：

1. 写文章类：「帮我写一篇关于 Claude Skills 的公众号文章」
2. 选题类：「给我出几个 AI 公众号选题」「这个方向能爆吗」
3. 评估类：「帮我评一下这篇文章」「跑 SOP 评分」「这篇能发吗」
4. 策略类：「标题怎么写」「段落结构有问题吗」「封面用什么颜色」
5. 全流程：「从选题到发布帮我规划一下」
