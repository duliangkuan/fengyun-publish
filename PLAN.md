# AI 公众号 IP 自动化系统 · v2 实施方案

> **目标**:做 AI 赛道公众号 IP,对标数字生命卡兹克。
> **核心定位**:不是堆 agent,而是用对 harness;不是抓得多,而是抓得对;不是写得快,而是有反馈环。
> **生成日期**:2026-05-19
> **基于**:两轮共 9 个并行研究 Agent 的 GitHub 深度调研

---

## 1. 7 层架构

```
L0 触发层    cron + webhook
L1 信源层    TrendRadar(启用 AI 简报/MCP) + we-mp-rss + 8 个新护城河信源
L2 选题层    BERTopic 聚类 + MediaCrawler 评论信号 + 爆款拆解表
L3 Harness   Claude Agent SDK Python(CLAUDE.md/MEMORY/Skills/Subagents/Hooks)
L4 创作层    khazix-writer 底座 + Viral_Writer 11 维度 + article-writer 11 步
L5 自评合规  deepeval G-Eval + Humanizer-zh + houbb 敏感词 + 朱雀验证
L6 视觉层    baoyu-skills 全家桶(可选 LoRA 训练做 IP 视觉护城河)
L7 排发反馈  md2wechat 排版 + baoyu-post-to-wechat 发布 + 飞书 Base 数据回流
```

---

## 2. 项目目录(必装 8 个,推荐 6 个,弃用 5 个)

### 必装(1k+ star,2026 仍活跃)
| 项目 | star | 角色 | License |
|---|---|---|---|
| `JimLiu/baoyu-skills` | 18.8k | 视觉武器全家桶 | - |
| `confident-ai/deepeval` | 15.5k | LLM-as-judge 自评 | Apache 2.0 |
| `KKKKhazix/khazix-skills` | 11.1k | 卡兹克 DNA 底座 | MIT |
| `wechat-article/wechat-article-exporter` | 10.3k | 语料采集 + 反馈环 | MIT |
| `op7418/Humanizer-zh` | 7.9k | 去 AI 味 24 模式 | - |
| `MaartenGr/BERTopic` | 7k | 选题聚类 | MIT |
| `anthropics/claude-agent-sdk-python` | 6.9k | Harness 主框架 | MIT |
| `houbb/sensitive-word` | 5.8k | 敏感词主引擎 | Apache 2.0 |

### 推荐(增强能力)
- `NanmiCoder/MediaCrawler` (45.1k) — 评论区情绪信号
- `vladkens/twscrape` (2.4k) — Twitter 抓取
- `oaker-io/wewrite` (2k) — SICO 风格学习
- `iliane5/Meridian` (2.4k) — embedding 聚类思路
- `Thysrael/Horizon` (3.9k) — 国人作飞书原生
- `caol64/wenyan-mcp` (1.2k) — md2wechat 排版备选
- `geekjourneyx/md2wechat-skill` (2.3k) — 已 clone,主排版器

### 抄思路不直接用
- `iniwap/AIWriteX` (1k) — Pipeline 骨架可抄
- `OpenAISpace/ai-trend-publish` (2.9k) — 模板系统可抄
- `nashsu/Viral_Writer_Skill` (507) — 11 维度爆款 prompt 借走
- `wordflowlab/article-writer` (263) — 11 步工作流借走
- `assafelovic/gpt-researcher` (27k) — editor/reviewer 循环架构借走

### 弃用 / 警告
- `microsoft/autogen` (58k) — **maintenance mode,新项目不要用**
- `dyyz1993/twitter-monitor` — 停滞,换 twscrape
- `iamzifei/wechat-article-publisher-skill` — 中转方案不稳,主链路弃用
- `iniwap/AIWriteX` 整套直接用 — 禁商用 + 偷卖纠纷
- `PapersWithCode` — **2025-07 已被 Meta 关闭并重定向**

---

## 3. 8 个核心 AI 圈护城河信源(你当前 17 个 RSS 没覆盖)

1. **smol.ai AINews** (news.smol.ai/rss.xml) — Karpathy 钦点,356 Twitter+21 Discord
2. **HF Daily Papers** (huangboming/huggingface-daily-paper-feed feed.xml)
3. **Latent Space** (latent.space/feed)
4. **Import AI** (jack-clark.net/feed.xml)
5. **The Batch** (deeplearning.ai/the-batch)
6. **r/LocalLLaMA RSS**
7. **@_akhaliq Twitter**(twscrape 自建)
8. **HF Trending Models RSS** (zernel/huggingface-trending-feed)

---

## 4. Claude Code 5 层架构 → 项目映射

| Claude Code 概念 | 项目内具体实现 |
|---|---|
| CLAUDE.md | `WRITER.md`(人设+禁词+卡兹克对标分析) |
| MEMORY.md | `memory/hits.md`(爆款历史) + `memory/blacklist.md`(重复角度) |
| Skills | md2wechat + publisher + khazix-style + hot-topic-radar + humanizer + title-ab-tester |
| Subagents | researcher / writer / editor / seo / qa(Editorial Mesh 五角色) |
| Hooks | PostToolUse(Write)→humanizer;Stop→敏感词扫描;SessionStart→注入今日热点 top10 |
| Plan Mode | 每天 07:00 cron 跑选题策划,产 5 候选 |
| Sessions Fork | A/B 测标题/lead 段 |
| Permissions | researcher 只 WebSearch;publisher 才有 wechat-article-publisher |
| MCP Server | TrendRadar / CowAgent / we-mp-rss 都包成 MCP server(关键解耦点) |

---

## 5. 执行 Roadmap

### Phase 1 — 半天 · 建语料库 + 核心 skill 装机
- [x] ~~Docker 自部署 wechat-article-exporter~~ → 改用在线版 https://down.mptext.top 抓语料(一次性,不需要部署)。Cloudflare Pages 部署留作 Phase 1.6(可选后置)
- [x] 用户已有公众号,可直接扫码登录在线版 exporter
- [x] 扫码登录在线版 → 导出语料(Markdown 格式) → 保存到 `D:\Dev\ai-wechat-pipeline\corpus\{kazik,baoyu,saiboshanxin}\`(橘鸦已弃,用户判定写得不好)。**实抓:卡兹克 175 + 宝玉AI 52 + 赛博禅心 50 = 277 篇**。中途公共代理池配额耗尽,改用自部署 Cloudflare Worker `mp-proxy-worker.dufengyun12.workers.dev` 解决
- [x] 写 tools/ 4 个脚本(clean_corpus / build_corpus_index / pick_few_shot / htm_to_md),277 篇全部清洗完毕(CSS 残渣剥离),frontmatter 规范化
- [x] 写项目级 CLAUDE.md(写新文流程 / 关键路径 / 决策记录 / 弃用警告)
- [x] 装 khazix-skills 4 个子 skill 到 `~/.claude/skills/`:khazix-writer / aihot / hv-analysis / neat-freak
- [x] 装 baoyu-skills 9 个核心子 skill:baoyu-cover-image / -article-illustrator / -infographic / -diagram / -comic / -image-cards / -xhs-images(deprecated 但保留) / -post-to-wechat / -format-markdown
- [x] 装 op7418/Humanizer-zh 到 `~/.claude/skills/humanizer-zh/`
- [x] 清理 ~/.claude/skills/ 散落 .md 文件,归档到 `_staging/_archived/`
- [x] TrendRadar 配置加 7 个新护城河信源(Twitter 走 twscrape,Phase 3 单独搭)
- [x] 验证 7 个新 RSS URL 可达性 → 5 个 OK,2 个有问题:
  - ✅ `smol-ainews` / `latent-space` / `import-ai` / `hf-daily-papers`(URL 修正为 raw.githubusercontent.com) / `hf-trending-models`
  - ❌ `the-batch` — deeplearning.ai 不开放公共 RSS,所有候选 URL 都 404/500。已注释,需用 Kill the Newsletter 或 RSSHub 替代
  - ❌ `r-localllama` — Reddit 屏蔽 TrendRadar 默认 UA(浏览器 UA 测试 200 OK)。已注释,需改 `trendradar/crawler/rss/fetcher.py:74` 全局 UA 或走 RSSHub

**Phase 1 关键发现**:
- `md2wechat` 和 `wechat-article-publisher` 这两个 skill **之前就装在 user-level `~/.claude/skills/`**,不需要从 `D:\Dev\ai-wechat-pipeline\md2wechat-skill\` 单独装。后者只是用来下载/编译 `bin/md2wechat.exe`
- `aihot` skill 是卡兹克自己开源的 AI 资讯查询 API,直接 curl 不用 API key — **等于免费精简版日报底层**,可以做底层抓取的轻量替代
- `hv-analysis` 是卡兹克的横纵分析法,**可以直接用于 Phase 4 的爆款拆解**
- `baoyu-xhs-images` 已 deprecated,正式版是 `baoyu-image-cards`

### Phase 2 — 1 天 · 端到端手工验证
- [ ] 挑一条 TrendRadar 当天热点
- [ ] 手动喂给 khazix-writer 出稿
- [ ] Humanizer-zh 跑去 AI 味
- [ ] houbb 敏感词扫
- [ ] md2wechat 排版
- [ ] 验证味道:像不像卡兹克、过不过朱雀(用网页版工具或人工评)
- [ ] 申请公众号 AppID/Secret + IP 白名单
- [ ] baoyu-post-to-wechat 跑通发草稿(替换 wechat-article-publisher-skill)

### Phase 3 — 2-3 天 · 自动化 + 自评层
- [ ] TrendRadar/we-mp-rss 包成 MCP server
- [ ] Claude Agent SDK Python 串联:plan → researcher → writer → editor → qa → publisher
- [ ] deepeval G-Eval 把 khazix L1-L4 翻译成 metric(hook/金句/AI 味/节奏 4 维)
- [ ] BERTopic 接入 TrendRadar 输出,每天产出 5-8 个选题集群
- [ ] 飞书 Base 字段:选题集群标签 / 标题模板 / 首图风格 / 阅读量 / 转发率
- [ ] hooks 配置:PostToolUse(Write)→humanizer / Stop→敏感词扫描

### Phase 4 — 持续 · 反馈环 + 护城河
- [ ] wewrite extract_exemplar.py 跑你自己的修改稿,产出 persona YAML
- [ ] BGE-M3(FlagEmbedding) + Chroma 把 100+ 篇卡兹克语料做向量库
- [ ] 写作时按"主题+标题"召回 top-5 卡兹克原文做 few-shot
- [ ] wechat-article-exporter 抓自己 48h/7d 阅读量回流飞书 Base
- [ ] 每周 Claude 跑分析:哪种选题集群×标题模板组合阅读量最高
- [ ] 3 个月数据足够后,微调"标题阅读量打分器"小模型(中文圈护城河)
- [ ] (可选) Nano Banana 2 / Flux.2 出参考图 + ComfyUI-Lora-Manager 训练 IP 视觉 LoRA

---

## 6. 关键决策记录(Decision Log)

| 决策 | 选择 | 理由 |
|---|---|---|
| Harness 主框架 | Claude Agent SDK Python | Anthropic 官方押注(2026-06-15 单独计费额度),skill 资产复用,避免双 harness 维护 |
| 排版主器 | md2wechat-skill(已 clone) | 已编译,40+ 主题,确定性输出,自有 writer YAML 机制 |
| 发布主链路 | baoyu-post-to-wechat | 直连官方 API,18.8k star 稳定 |
| 发布备份 | 弃用 wechat-article-publisher | wx.limyai.com 中转长期不稳 |
| 卡兹克 skill 改造 | SKILL.md 不二改 | 只往 references/style_examples.md 追加语料,保持卡兹克 DNA 纯度 |
| 创作 agent 底座 | khazix-writer | 卡兹克本人开源,五类原型+L1-L4+36 禁词,MIT 可商用 |
| 自评框架 | deepeval G-Eval | 自然语言定义 metric,把 L1-L4 翻译成评分 rubric |
| Twitter 抓取 | vladkens/twscrape | 2.4k 活跃,带账号轮换 |
| 不引入第二个 harness | 拒绝 CrewAI/agno/mastra/langgraph | 跟 Skill/Subagent 同构竞争,引入等于双倍维护 |
| 不上 Dify | 拒绝 | 偏离 Claude Code skill + Python 脚本路线 |
| 数据回流 | 飞书 Base | 用户已有飞书栈 |

---

## 7. 风险与卡点

1. **朱雀 AI 检测无开源 API** — 微信实际用的检测算法不公开,只能 web 自动化(headless 浏览器)或人工抽检。共识阈值:AI 率 < 25-30% 才安全
2. **公众号 2025-07 后非认证号只能发草稿** — 你的链路本来就是"发草稿+人工最终发",合规
3. **AppID/Secret + IP 白名单** — 一次性配置,但需要公众号已经申请下来
4. **khazix-writer references 是核心资产** — 别二改 SKILL.md,只追加 style_examples
5. **规则去 AI 味会损失信息** — Humanizer-zh 改完要 LLM 做一致性校验
6. **wechat-article-exporter 风控** — 建议私有化 Docker 部署,扫码用专门小号
7. **CTR/阅读量预测无中文开源工具** — 只能用 deepeval + GPT/Claude 软评估,直到自己数据够训小模型
8. **段落 ≤150 字 linter 不存在** — 需要自己写 ~20 行 Python,放在 markdown 渲染**之前**做

---

## 8. 可以倒过来做 IP 露脸的动作(差异化护城河)

- [ ] 给 `md2wechat-skill` 提 `writers/khazix.yaml` PR(目前只有 1 个 writer,通过率高)
- [ ] 整理"AI 圈公众号 30+ 大 V 监控源 + 爆款拆解表"开源到 GitHub
- [ ] 卡兹克风格池(BGE-M3 + Chroma)若效果好,开源(中文圈唯一)
- [ ] 3 个月数据后训出的"标题阅读量打分器"小模型 — 中文圈没人做过

---

## 9. 关键路径(快速回想)

- 项目根目录:`D:\Dev\ai-wechat-pipeline\`
- 已 clone:`md2wechat-skill/`(编译好的 `bin/md2wechat.exe`) + `wechat-article-publisher-skill/`(弃用)
- 底层信源系统:`D:\Dev\TrendRadar\` + `D:\Dev\CowAgent\` + `D:\Dev\we-mp-rss\`
- TrendRadar 配置:`D:\Dev\TrendRadar\config\config.yaml`(加新 RSS 源)
- CowAgent 定时:`C:\Users\23303\cow\scheduler\tasks.json`
- DeepSeek key:在 TrendRadar config.yaml(不要 git commit)
- Claude skill 安装位置:`~/.claude/skills/`(Windows 实际是 `C:\Users\23303\.claude\skills\`)
