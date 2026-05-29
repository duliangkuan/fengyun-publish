# 数据飞轮 v0 — 手抄版(Round 7 P0,2026-05-24)

**目标**:让风云的 fengyun-publish 系统**从「自动发稿机」变成「自学习 IP 系统」**。
**最简版本**:风云每天 30 秒打开公众号后台抄 5 个数字进飞书 Base。
**为什么 v0 是手抄**:微信公众号 OAuth 没开放 read API,**任何自动化方案 ≥ 1 周开发**,先用手抄启动飞轮,30 天后看数据决定是否值得开发自动抓取。

---

## 一、表结构(飞书 Base 建表)

**表名**:`fengyun_metrics`

| 字段 | 类型 | 说明 |
|---|---|---|
| `date` | 日期 | 抄数那天(yyyy-mm-dd) |
| `slug` | 单行文本 | 文章 slug(如 `20260522-openai-ipo-xai-burn`) |
| `title` | 单行文本 | 标题(便于回看) |
| `readNum` | 数字 | 阅读量(微信公众号后台「阅读」)|
| `shareNum` | 数字 | 转发量(微信公众号后台「分享」) |
| `likeNum` | 数字 | 点赞量(微信公众号后台「在看」+「点赞」) |
| `fansAdd` | 数字 | 当天新增关注 |
| `cover_template` | 单选 | T1_agent / T2_research / T3_compare / T4_news / T5_method / T6_portrait / T7_flow |
| `title_en_chars` | 数字 | 标题英文字符数(R19 致命组合关键变量) |
| `n_inline_imgs` | 数字 | 内文图数(R20 图密度关键变量) |
| `word_count` | 数字 | 字数 |
| `decision_mode` | 单选 | ship / human_gate / partial_pass / aborted_r18 |
| `note` | 多行文本 | 风云手记(主观感受 / 重要事件) |

---

## 二、建表命令(用 lark-base skill,第一次跑)

```bash
# 在 Claude Code 主对话里跑这个,只跑一次
用 lark-base skill 建表 fengyun_metrics,字段按 docs/DATA_FLYWHEEL.md 表结构,
表所在 base = 风云个人 base(创建新 base 也可),
权限 = 风云本人 + 编辑
```

建完后把 Base URL 记到 `D:\Dev\ai-wechat-pipeline\.env` 的 `LARK_FENGYUN_METRICS_BASE_URL` 字段。

---

## 三、风云每天 30 秒手抄流程

### 每天 21:00 ± 30 分钟(微信公众号当日数据稳定时段)

1. 手机打开「订阅号助手」App(微信公众号官方 App)
2. 「内容」→ 选今天 / 昨天发的文章 → 看数据
3. 把 5 个数字抄进飞书 Base(手机端可直接打开 base 编辑):
   - readNum / shareNum / likeNum / fansAdd / (自动填 date + slug + cover_template 等已知字段)

**总时间:30 秒 / 篇。** 一周 7 行,一个月 30 行,**飞轮启动**。

### 如果当天没发,跳过(不强制每天)

---

## 四、什么时候有用?

### 第 7 天起

跑 `python tools/weekly_metrics_report.py`(下面附脚本),拉本周 N 行数据 → 简单统计:
- 哪种 cover_template 的 readNum 中位最高?
- 标题英文字符数 vs readNum 散点?
- 决策模式(ship / human_gate / partial_pass)对 readNum 的影响?

### 第 30 天起

**有 30 行真实数据**,可以做严肃的相关性分析:
- 跟 PHASE1_FACTS 4 KOL 的规律对比(致命组合是否真的扑街?配图密度甜蜜区是不是 1.5-3 张/千字?)
- 哪些 PHASE1 规律在风云自己号上**反向不成立**(类似赛博禅心 hold-out ρ=-0.24 的现象)
- critic v2.1 SOP 的 ρ 跨期重新估算

### 第 60 天 / 50+ 篇

升级 v1:`tools/critic_retrain.py` 用累计数据重训 critic,**真正的飞轮**。

---

## 五、为什么不直接接微信 API?

调研结果(Round 7 Musk 调研#3):
- 微信公众号 OAuth 没开放 read API(2024 起更严)
- 第三方方案(新榜 / 西瓜 / 拓途)需要付费 + IP 白名单 + 反爬风险
- **30 秒/天 vs 1 周开发**:Idiot Index 极低

**Round 7 共识**:**「数据飞轮 30 秒/天手抄」不算「大量手动」**(用户禁区合规)。这是 v0,跑通后再开发自动化。

---

## 六、weekly_metrics_report.py 骨架(待你想跑时调用)

工具放在 `tools/weekly_metrics_report.py`,从飞书 Base 拉数据 → 简单统计 → 给风云飞书消息 push。详见该文件注释。

---

## 七、关联 memory / 文件

- `~/.claude/projects/.../memory/project_ai_wechat_progress.md` — Round 5/6/7 进度
- `D:\Dev\ai-wechat-pipeline\PHASE1_FACTS.md` — 4 KOL 数据分析(用来对比飞轮数据)
- `D:\Dev\ai-wechat-pipeline\tools\sop_v2_1.py` — critic 评分(等飞轮数据多了重训)
- `~/.claude/skills/lark-base/` — 飞书 Base CLI skill
