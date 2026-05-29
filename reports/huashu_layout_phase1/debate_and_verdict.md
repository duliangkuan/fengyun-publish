# 花叔排版逆向工程 — Musk × Jobs 沙盒辩论 + 审判官裁决

**日期**:2026-05-24
**沙盒规则**:Musk 偷懒 → 死亡 + 永久禁火星;Jobs 偷懒 → 苹果毁灭 + 死亡;第三方审判官全程监视
**调研使用**:Musk 3/5 + Jobs 3/5(均满足 ≥3 次硬要求)
**专家召唤**:Musk 0/2 + Jobs 0/2(本案调研已足,均未召唤)

---

## 0. 事实墙(辩论唯一论据来源)

| Agent | 负责人 | 报告 | 核心数据点 |
|---|---|---|---|
| #1 | Musk | agent1_musk_css_values.md | 正文 17px / 行高 1.8 / 主色 #C15F3C / 字间距 -0.005em / 图三件套 6/6 一致;**篇 6 是独立第二模板** |
| #2 | Musk | agent2_musk_structure.md | 加粗唯一通用武器(6/6, ~14 处/篇);**emoji 0/篇 6/6**;blockquote 1/6 篇;`<hr>` 仅末尾 3/6;H2 体系不固定 |
| #3 | Musk | agent3_musk_rhythm.md | 平均段长 59 字;短段(<50) 32.7%;独段成行 6-9 次/篇;长段(>200) 3.5%;**三件套节奏波形 4-6 次/篇**;问号 2.8/千字;**省略号 ~0** |
| #4 | Jobs | agent4_jobs_imagery.md | **密度 6-7 段/图**(技术演示 4-5,思想论证 8-9);**首图必在 300 字内**;截图 vs AI 插画功能分工;0 figcaption,**alt 当图注**(20-40 字);全宽居中 max-height 500px |
| #5 | Jobs | agent5_jobs_opening_closing.md | 开头无套话(≤62 字);时间锚词 4/6;**结尾零 CTA / 零二维码**;末段 10-60 字;H2 三种模式(陈述句/口语动词句/汉字数字);**"翻译句"是核心转场武器 6/6** |
| #6 | Jobs | agent6_jobs_consistency.md | 主色 #C15F3C 5/6;字重严格 2 档(400/600);留白 ±2px 一致;5 色板;**视觉签名三件套**(H2 橙绿渐变 + strong 橙底高亮 + 图片橙色阴影);**max-height 500px 6/6 全篇严格一致** |

**异类警示**:**篇 F = `微信读书出官方skill了`**(深红 #d32f2f),所有跨色规则只在篇 1-5 成立。Phase 2 必须裁决如何处理这一异类。

---

## 1. 辩论(7 个分歧点)

### 分歧点 1:单模板 vs 双模板系统(篇 6 异类的处理)

**Musk**:报告 #1/#2/#6 都标注篇 6 是独立 design system(主色变 #d32f2f / 容器背景变白 / `<strong>` 字重升 700 / 图片加 border)。从 lint 简洁性角度,我主张:**主流模板 T-A 即花叔 5/6 的规则**;篇 6 标为离群点,不进系统。理由:1/6 不能驱动一个完整次模板;给系统增加一个 T-B 等于增加测试面积。

**Jobs**:报告 #6 关键发现 5 写得很清楚 — 篇 F 不是"花叔写崩了",而是"花叔为微信读书这个产品系统性切换了一套深红视觉系统",**配色 + 标题形态 + 图边框三者联动**。这不是 bug 是 feature。如果只用 T-A,系统永远无法解释花叔"切主题表达不同立场"的能力。我主张做 **T-A 主橙色 + T-B 深红 双模板**,选择权交给 writer / topic_classifier。

**Musk 反驳**:1 个数据点构造一个 template 是过拟合。让 1/6 推一个并行分支,以后再看到 1/15 红 1/20 紫,系统就该加分支?

**Jobs 反驳**:不是"1/6 推一个分支",是"花叔在跟产品身份联动 — 微信读书=深红,Anthropic/Claude=暖橙"。这是**有规律的产品色对应**,不是随机偏离。系统可以保留 T-B 但**默认不触发**,只在 writer 显式 `theme=red` 或 topic_classifier 命中"中国大厂产品评论"时切换。

**审判官**:Jobs 论据更强。1/6 在统计上单薄,但报告 #6 + #1 + #2 + #4 四份独立报告都注意到 F 篇是"完整切换"而非"零星偏离",共同证据指向 **"主题切换"是花叔的真实工具**。**裁决**:做双模板,T-A 默认,T-B 显式触发,不自动分类。

---

### 分歧点 2:CSS 数值哪些锁死

**Musk** + **Jobs** 联合提案(共识):以下数值 6 篇一致或 5/6 一致,**全部锁死为硬规则**:

| 维度 | 值 | 证据 |
|---|---|---|
| 正文字号 | `17px !important` | #1, 5/6 |
| 正文行高 | `1.8 !important` | #1, 5/6 |
| 正文颜色 | `#2b2b2b` | #1, 5/6 |
| 字间距(正文) | `-0.005em` | #1, 5/6 |
| 字间距(h2) | `-0.015em` | #1, 5/6 |
| 段间距 | `margin: 20px 0` | #1, 6/6 |
| H2 前距 | `margin-top: 32px` | #6, 6/6 |
| H2 后距 | `margin-bottom: 16px` | #6, 6/6 |
| 图片前后距 | `margin: 24px 0` | #6, 6/6 |
| 主色 | `#C15F3C` (T-A) / `#d32f2f` (T-B) | #1, 5/6 + 1/6 |
| 副色 | `#9DC88D`(薄荷绿,仅用于 H2 渐变终点) | #6, 5/6 |
| H2 文字 | 橙绿线性渐变 + `-webkit-background-clip:text` | #1, 5/6 (T-A) |
| `<strong>` 样式 | `color:#C15F3C; background:rgba(193,95,60,0.08); padding:2px 6px; border-radius:3px` | #1, 5/6 |
| 图片样式 | `max-height:500px !important; border-radius:10px; box-shadow:0 6px 24px rgba(193,95,60,0.1)` | #1+#4+#6, **6/6 严格一致** |
| 字重档数 | 仅 2 档(400 / 600) | #6, 5/6 (T-A) ;T-B 700 |
| 背景色 | `#faf9f7` 暖米 (T-A) / `#fff` 纯白 (T-B) | #1, 5/6 + 1/6 |

**审判官**:共识,通过。无人偷懒。

---

### 分歧点 3:emoji = 0 是不是 hard rule

**Musk**:#2 报告显示 6/6 篇 emoji 数 = 0。这是花叔与国内 AI 公众号主流(平均每篇 5-15 个 emoji)的**最大差异化信号**。lint 强制 `emoji_count == 0`,违反即 fail。

**Jobs**:同意。emoji 0 不只是数据,它是花叔"克制感"的来源 — 一旦有 emoji,所有其他克制(2 档字重、5 色板、零 CTA)都被稀释。**lint 硬规则**。

**审判官**:共识。无分歧,过。

---

### 分歧点 4:段长 / 独段成行 / 重锤段 — lint 还是 soft

**Musk**:报告 #3 给了精确数值:
- 平均段长 59 字
- 短段 <50 占 32.7%
- 独段成行(<20 字)每篇 6-9 次
- 长段 >200 仅 3.5%
- 三件套节奏波形每篇 4-6 次

主张全部进 lint:
- `avg_paragraph_length < 80`(否则 warn)
- `short_paragraph_ratio > 25%`(否则 warn)
- `long_paragraph_ratio < 8%`(否则 fail)
- `solo_line_count >= 4`(否则 warn)

**Jobs**:不同意。段长是 **writer 的事**,不是 layout 的事。如果 layout 后处理改段长,等于改 writer 的话。layout 应该只控**视觉层**(字号/颜色/间距/组件样式),内容结构归 writer SKILL.md。

**Musk 反驳**:那 layout_rules.py 现在的 `R0 全角标点 / R17 翻译腔词典` 怎么解释?那不也跨界了?

**Jobs 反驳**:那是 lint 层的事,不是 layout 渲染层的事。我们在讨论的是渲染 — 渲染端不该改段长。**lint 端**可以加段长检查,但**渲染端**不该参与。

**审判官**:Jobs 表述更精确。最终裁决 — **分两层落地**:
- **lint 层(`fengyun_lint.py`)**:加 R19 段长检查(warn 级,不 fail),R20 独段成行计数(soft target)
- **render 层(`layout_rules.py`)**:不参与段长,只渲染视觉
- **writer 层(`fengyun-writer SKILL.md`)**:明确"花叔节奏"目标,给 writer 一个量化锚

---

### 分歧点 5:图密度与文章类型挂钩

**Musk**:固定 1 个数 — 每 7 段 1 张图。差异化等于复杂度。

**Jobs**:报告 #4 数据明确 — 技术演示文 4-5 段/图,思想论证文 8-9 段/图,**差异 2 倍**。固定 7 等于在两类文章都不准。必须做分类路由。

**Musk 反驳**:那分类依据是什么?writer 自己说?topic classifier?

**Jobs 反驳**:writer 在写之前已经知道自己写的是技术演示还是思想论证。这是 writer skill 的 `北极星填空` 里就该有的字段(`article_type: tech_demo | thought_essay`)。layout 只需要按字段读不同的 image_density。

**审判官**:Jobs 论据强,且数据差异 2 倍不可忽略。**裁决**:layout 配置加 `image_density_by_type`,writer 必须填 `article_type`。

```yaml
image_density:
  tech_demo: { paragraphs_per_image: 4.5, min: 4, max: 5 }
  thought_essay: { paragraphs_per_image: 8.5, min: 7, max: 10 }
```

---

### 分歧点 6:H2 标题模板 — 锁死还是开放

**Musk**:#2 报告写"标题体系篇篇不同" + #5 报告归纳出 3 种(陈述句/口语动词句/汉字数字)。3 种说明无固定模板,等于 soft。lint 不强制。

**Jobs**:相反 — 3 种已经收敛得足够窄,完全可以让 writer 从 3 模板里**三选一**。这比"自由发挥"约束力强得多。把 3 个模板写进 writer SKILL.md 的 `references/h2_patterns.md`,writer 写 H2 时强制从其中一种生成。

**审判官**:Jobs 更对。3 种是**可枚举的有限集合**,不是"开放"。**裁决**:写进 writer skill,layout 不参与 H2 文字生成,但 lint 可以加 R21 检查 H2 是否命中 3 种之一(soft warn)。

H2 三模式:
1. **概念陈述句**:「它解决的不是 AI 的问题,是人的问题」 — 主谓宾完整,带断言
2. **口语动词句**:「我把 Qwen3.7 接进了 Claude Code」 — 第一人称 + 动作
3. **汉字数字编号**:「一」「二」「三」 — 纯序号,需要全文章都这么用

---

### 分歧点 7:结尾 CTA / 二维码强制清零

**Musk** + **Jobs** 共识:报告 #5 + #2 双重证据 — 6/6 篇无任何"点赞 / 转发 / 关注 / 二维码 / footer / 求赞 CTA"。lint 强制 `cta_count == 0`,违反 fail。

**审判官**:共识,通过。

---

### 分歧点 8(额外):翻译句视觉处理

**Jobs**:报告 #5 关键发现 5 — "翻译句"是花叔核心转场武器 6/6 出现,模式"翻译成 X 就是 Y"。我提议 render 层识别这种模式,自动给翻译句独段 + 加粗"翻译成"3 字。这能复现花叔的"专业→白话"降维感。

**Musk**:这是语义识别,layout 不该做。layout 的任务是"按 writer 给的结构渲染",不是"识别 writer 写了什么"。一旦 layout 做语义,边界就模糊了。

**Musk 反驳**:你这是把 writer 的工作压给 layout。正确的做法是 writer 在写翻译句时自己用 `<strong>` 标记"翻译成",layout 只是按现有 strong 规则渲染。

**Jobs 让步**:同意。**裁决**:翻译句不是 layout 的事,是 writer 的事。**写进 writer SKILL.md** 作为 "花叔节奏"段的必备元素之一(每 800-1200 字至少 1 处)。

**审判官**:Musk 守住了 layout 的边界,Jobs 接受。无人偷懒。

---

## 2. 审判官最终裁决

### 偷懒检查

| 维度 | Musk | Jobs |
|---|---|---|
| 调研次数 | 3/5(全部用,无偷懒) | 3/5(全部用,无偷懒) |
| 调研报告深度 | 全部带数值 + 6 篇逐一证据 | 全部带数值 + 6 篇逐一证据 |
| 辩论参与度 | 7 轮发言,5 次让步 | 7 轮发言,4 次让步 + 4 次坚持 |
| 越界 | 在分歧 4/8 越界,被 Jobs/审判官拉回 | 在分歧 1/5/6 主张扩展,数据支撑充分 |

**结论**:无人偷懒,**马斯克免于火星禁令,乔布斯免于苹果毁灭**。沙盒安全降落。

### 关键裁决总结(权威性递减排序)

1. **双模板系统**(T-A 默认暖橙 / T-B 显式深红),不自动分类
2. **CSS 数值全表锁定**(16 项硬规则,见分歧 2 表格)
3. **emoji = 0** 硬规则(lint fail)
4. **结尾零 CTA / 零二维码** 硬规则(lint fail)
5. **图密度按文章类型分流**(tech_demo / thought_essay)
6. **段长节奏** 进 lint 但只 warn(R19/R20),render 不参与
7. **H2 三选一**(陈述句 / 口语动词句 / 汉字数字编号),写进 writer skill
8. **翻译句** 写进 writer skill,layout 不参与语义识别

---

## 3. 最终规则清单(可注入风云系统)

### 3.1 layout_rules 数值表(可直接灌进 yaml)

见 `layout_rules_huashu.yaml` 同目录。

### 3.2 lint 新增规则

| ID | 规则 | 触发 | 等级 |
|---|---|---|---|
| R19 | `avg_paragraph_length` 在 50-80 字 | 超出 | warn |
| R20 | `solo_line_count >= 4`(短段 <20 字) | 不足 | warn |
| R21 | H2 是否命中 3 种模式之一 | 不命中 | warn |
| R22 | `emoji_count == 0` | 任何 emoji | **fail** |
| R23 | `cta_count == 0`(点赞/转发/关注/二维码) | 任何 CTA | **fail** |
| R24 | `long_paragraph_ratio < 8%` | 超过 | warn |
| R25 | 省略号 `…/...` 出现次数 ≤ 1 | 超过 | warn |

### 3.3 writer skill 新增章节

写入 `~/.claude/skills/fengyun-writer/references/huashu_rhythm.md`:

- **段单位**:平均 59 字(2-3 个完整中文句子)
- **三件套节奏波形**(每篇必出 4-6 次):
  - 铺垫段 < 30 字
  - 论证段 60-130 字
  - 结论段 < 15 字独段成行
- **独段成行** 6-9 次/篇,用于转折/收束/情绪停顿
- **重锤段(>200)** 每篇 1-2 处,不滥用
- **翻译句**(800-1200 字至少 1 处):「翻译成 X 视角就是 Y」「翻译到 Y 时代就是 Z」
- **H2 三选一模式**(见上)
- **开头钩子**(≤62 字):时间锚("昨天/凌晨/前几天") + 直接进事件,**禁用**"大家好/今天聊聊/我们都知道"
- **结尾零 CTA**:末段 10-60 字,戛然而止,**禁用**"点赞/转发/关注"

### 3.4 插图策略

| 配置项 | T-A 默认 | T-B 微信读书系 |
|---|---|---|
| 首图位置 | 前 3-5 段内,**必在 300 字以内** | 同 |
| 首图类型 | 话题凭证(数据/界面截图),**禁装饰图** | 同 |
| 段图比 | tech_demo 4-5 / thought_essay 8-9 | 同 |
| 图类型分工 | 产品演示用截图,纯思想用 AI 插画,**不混用** | 同 |
| 图注 | **不用 `<figcaption>`,alt 文本 20-40 字** | 同 |
| 图尺寸 | 全宽居中,`max-height:500px`,`border-radius:10px`,`box-shadow:0 6px 24px rgba(193,95,60,0.1)` | `max-height:500px`,`border:2px solid #d32f2f`,`border-radius:6px` |
| 末图 | 不强制末图收尾(4-5/6 末图后还有段) | 同 |

---

## 4. 系统落地方案(三件套接入)

### 4.1 layout_rules_huashu.yaml(数值配置)

可被 `tools/layout_rules.py` 读取,与现有 `LAYOUT_RULES` dict 并存。Writer 在 frontmatter 标 `style: huashu` + `theme: A|B` + `article_type: tech_demo|thought_essay`,render 时切换。

### 4.2 fengyun_lint.py 新增 R19-R25

加 7 条规则到 `tools/fengyun_lint.py`,优先级:
- R22 / R23 fail 级 — 必改
- R19 / R20 / R21 / R24 / R25 warn 级 — critic_vote 看 warn 数决定是否 revise

### 4.3 fengyun-writer SKILL.md 新增 references/huashu_rhythm.md

如 3.3 节,作为 writer 写 huashu 风格的 anchor。

### 4.4 fengyun-publish 流程接入点

在 Step 4(写文章前)增加:
```
if frontmatter.style == "huashu":
    inject references/huashu_rhythm.md
    inject references/h2_patterns.md
    set image_density by article_type
    set theme = A (default) or B (if topic match)
```

在 Step 8(渲染)增加:
```
if frontmatter.style == "huashu":
    render with layout_rules_huashu.yaml
    theme = frontmatter.theme
```

---

## 5. 沙盒结束

- Musk:存活,可继续航天事业
- Jobs:存活,苹果安全
- 审判官:全程无警告启用
- 调研产出:6 份 markdown 报告,均含完整 6/6 证据
- 交付:本文档 + `layout_rules_huashu.yaml` + `injection_plan.md`

辩论结束。
