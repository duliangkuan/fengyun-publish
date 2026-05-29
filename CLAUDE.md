# AI 公众号 IP 自动化系统

**目标**:做 AI 赛道公众号 IP,对标数字生命卡兹克。

## ⛔ 启动系统前必跑 Preflight(2026-05-25 v1.0)

**任何 fengyun-publish / 调研 / 写文章动作之前,先跑:**
```powershell
.\tools\preflight.ps1
```

7 项自检(Docker / we-mp-rss / cookie / TrendRadar / HF Spaces / Email-to-RSS / rsshub.app)。**P0 全绿才允许进入任何 Step**。详情见 `WRITE_AGENT.md` Preflight 红线段。

## ⛔ 写新文前必读(2026-05-25 Round 25 锁定)

`D:\Dev\ai-wechat-pipeline\WRITE_AGENT.md` 是**系统级宪法**,优先级高于本文档和 SKILL.md。19 个 Step 颗粒度最细的执行标准,主线程 Claude 包括 ship 前必读。**gate.py PreToolUse hook 物理拦截**任何不符合宪法的推送。

**当前关键约束**(摘要):
- **文内图强制必选(Round 25)**:任何 ship 必须 `image_paths` 非空 + 每张文件 size ≥ 5 KB;Seedream 失败 → `assets/placeholder-sketch.png` × N 复制兜底;**0 图路径已删**(详见 `docs/SPEC_ROUND25_IMAGE_MANDATORY.md`)
- 8 项 fake-pass 防伪:writer / humanizer / wangxiaobo / huashu_image_curator + 三轨 critic(real_run + source 字段必填)
- 排版统一花叔(Round 21):layout_rules huashu T-A 是唯一活跃渲染路径,legacy / default / classic 全砍
- 封面 + 内文图风格强制一致:封面输出 style_anchor sidecar → Step 7.2 huashu-image-curator 必须读
- 内容评委 skill = `content-judge`(Round 24 fork 自 fengyun-self,Track C 独立第三方评委;原 fengyun-self skill 完成历史使命已删)
- 选题去重:event_dedup 扫 drafts + runs 含 media_id 存档(Round 22)
- **三人监督机制(Round 25)**:spec-first + CI 测试 + 关键节点 diff review,**不开会**(Newton + Musk + Jobs 共识反对委员会决策模式)

**完整蓝图**:见 `PLAN.md`(7 层架构 / 项目目录 / Roadmap / Decision Log)。

## 关键路径

| 模块 | 路径 | 备注 |
|---|---|---|
| 完整方案文档 | `D:\Dev\ai-wechat-pipeline\PLAN.md` | 必读 |
| 资讯抓取底层 | `D:\Dev\TrendRadar\` | 17 + 7 个新源,需保留 fetcher.py:74 + parser.py:210 浏览器 UA 修改 |
| 创作发布层 | `D:\Dev\ai-wechat-pipeline\` | 本目录 |
| 卡兹克风格 cookbook | `~/.claude/skills/khazix-writer/references/style_examples.md` | **绝不修改**——卡兹克本人 curate 的 12 章风格 DNA |
| 全文语料池 | `D:\Dev\ai-wechat-pipeline\corpus\{kazik,baoyu,saiboshanxin}\` | 通过 wechat-article-exporter 抓取的 .md |
| 索引/挑选工具 | `D:\Dev\ai-wechat-pipeline\tools\` | Python 脚本 |
| **排版规则 layout_rules** | `D:\Dev\ai-wechat-pipeline\tools\layout_rules.py` | Round 21 决策 1:**huashu T-A 唯一活跃路径**,legacy / default / classic 已物理砍(详见 `docs/LAYOUT_RULES_ROUND3.md`)。HTML 上限 60000(Round 21 P0-17)|
| **系统宪法** | `D:\Dev\ai-wechat-pipeline\WRITE_AGENT.md` | 19 Step 全流程 + 8 项 fake-pass 防伪 + gate.py PreToolUse hook 物理拦截 |
| **Gate 保安** | `D:\Dev\ai-wechat-pipeline\tools\gate.py` | PreToolUse hook,验证 frontmatter 11 个 pass_flag + 8 项 real_run + source 防伪 |
| **内容评委 skill** | `~/.claude/skills/content-judge/` | Round 24 fork 自 fengyun-self(2026-05-25),5 个 decision_mode(D-1 ~ D-5)做独立第三方裁决;原 fengyun-self skill 完成历史使命已删 |
| **critic 决策**(Round 2) | `D:\Dev\ai-wechat-pipeline\tools\critic_vote.py` | 门控树 + human_gate + R18 分级 |
| **R18 防御**(Round 2) | `tools/fengyun_lint.py` R18-P0/P1/P2 + `tools/r18_dashboard.py` | 三级分级 + 白名单 + 触发率周报 |
| 反向代理 Worker | `D:\Dev\ai-wechat-pipeline\mp-proxy-worker\` | 已部署 `https://mp-proxy-worker.dufengyun12.workers.dev` |

## tools/ 用法

```bash
# 1. 扫 corpus/ 产元数据索引(每次新抓完语料后跑)
python tools/build_corpus_index.py

# 2. 写新文时挑代表作做 few-shot 召回
python tools/pick_few_shot.py --topic "Claude Code"
python tools/pick_few_shot.py --kazik-only --per-account 10

# 3. 备胎:浏览器另存的 .htm 批量转 .md
python tools/htm_to_md.py --src C:/Users/23303/Downloads --dst corpus/kazik
```

## 写新文的标准流程(Phase 2)

1. `aihot` skill 或 TrendRadar 拉今天 AI 圈热点 → 选题
2. `python tools/pick_few_shot.py --topic "<选题关键词>"` → 召回卡兹克相关 5-8 篇全文
3. 把召回的全文 + `style_examples.md` 一起喂给 `khazix-writer` skill → 出稿
4. `humanizer-zh` skill 去 AI 味
5. `baoyu-cover-image` + `baoyu-infographic` 出视觉
6. `md2wechat` 排版 → `baoyu-post-to-wechat` 推草稿
7. 人工最终把关 → 发布

## 关键决策记录

- **Harness 主框架**: Claude Agent SDK Python(不引入 CrewAI/agno/langgraph)
- **风格分层**: 卡兹克 cookbook(不动)+ corpus 全文池(增长式)+ Phase 4 BGE-M3 向量召回
- **代理方案**: 自建 Cloudflare Worker `mp-proxy-worker.dufengyun12.workers.dev`(不依赖作者公共代理池)
- **发布通路**: `baoyu-post-to-wechat` 直连官方 API(不用 wechat-article-publisher-skill 的 wx.limyai.com 中转)
- **TrendRadar 侵入修改**: `fetcher.py:74` + `parser.py:210` UA 改成浏览器(git pull 时保留)+ `senders.py` `dump_markdown_snapshot` 保留

## 弃用警告

- `microsoft/autogen`(58k)— maintenance mode
- `dyyz1993/twitter-monitor`— 停滞,换 `vladkens/twscrape`
- `iamzifei/wechat-article-publisher-skill`— wx.limyai.com 中转不稳
- `PapersWithCode`— Meta 已 2025-07 关停

## Phase 1 已跑出的客观事实

→ 详见 `PHASE1_FACTS.md`(2730 篇/80k 评论;字数 3000-8000 甜蜜点;转发 critic R² 0.32;标点是假相关)

## Round 10-13 新工具入口(2026-05-24)

### 选题层(System A 数据驱动)
- `tools/topic_recommender.py` — 用 PHASE1 + topic_hotness.parquet 给候选打分(Anthropic Skills 92% / Claude Code 87% / OpenAI -9.3pp)
- `tools/event_dedup.py` — 同一事件 7 天去重(token Jaccard + containment 双指标)

### ITI 架构(风云自创 · I-1 广搜 → T 选题 → I-2 深搜)
- `tools/iti_collect.py` — I-1 广搜 6 信源(aihot + we-mp-rss atom + TrendRadar + arxiv + smol.ai + WebSearch 补位)
- `tools/iti_explore.py` — I-2 深搜 5 本地+API 源(corpus grep + arxiv + topic_hotness + we-mp-rss + safe_webfetch)
- 两位数候选硬约束 ≥ 10(目标 15-25,上限 30)

### 开头多样性 harness 循环
- `tools/opening_signal.py` — 4 维评分(具体性 / 反差感 / 情绪锚点 / 信息密度)+ PHASE1 物理约束(首段 ≥ 50 字 + 第一人称 ≥ 5/千字)
- `tools/opening_dedup.py` — token Jaccard ≤ 0.30 + 5-gram ≤ 0.20 双重去重
- Step 1.5 集成 harness 循环(写 → 评 → 反馈 → 重写,上限 3 次)

### 排版主力切 huashu(Round 10 break change)
- frontmatter 不写 style → 默认 huashu T-A 暖米黄
- 显式 `style: default` → opt-out 回原蓝灰

### 工具栈
- `tools/safe_webfetch.py` — UA 轮换 + retry 反爬 wrapper(Bug 6)
- huashu-image-curator skill — 配图决策 Mode 2(Bug 2 闭环用)

详细落地文档:`docs/HUASHU_DEFAULT_2026-05-24.md` + project memory `ai-wechat-progress`
