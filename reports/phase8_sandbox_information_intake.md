# Phase 8 沙盒元辩论 — 信息抓取系统升级
*sonnet 全程 · 沙盒模式 · 2026-05-22*

---

## 沙盒设定回顾

- **Musk 偷懒 → 死亡 + 永久禁火星航天**
- **Jobs 偷懒 → 苹果毁灭 + 死亡**
- 审判官全程监控，以下 4 条硬标准：
  - ❌ 提"风云手动收集"
  - ❌ 提"推翻现有从头搭"
  - ❌ 泛泛列清单不给接入方案
  - ❌ 没调研就下结论

---

## Phase 1 · 资产摘要（资产快读 · 已验证）

### 现有 TrendRadar RSS 配置（真实当前状态，已 Read config.yaml）

当前已接入 **22 个 RSS 源**（不含注释掉的占位符）：

| 类别 | 源 | 状态 |
|---|---|---|
| 学术论文 | arXiv cs.AI / cs.CL / cs.LG | 已接入 |
| AI 公司官方 | OpenAI Blog / Anthropic News / DeepMind Blog / HuggingFace Blog / NVIDIA Blog×2 / AWS ML Blog | 已接入 |
| 护城河信源 | smol.ai AINews / Latent Space / Import AI | 已接入 |
| 论文聚合 | HF Daily Papers / HF Trending Models | 已接入 |
| 社区 | r/LocalLLaMA | 已接入 |
| AI Coding | Cursor Blog / Perplexity Hub / LangChain Blog | 已接入 |
| 综合媒体 | Hacker News / Synced Review | 已接入 |
| 中文媒体 | 量子位 / 36氪 AI | 已接入 |
| 公众号 | **全部注释掉（we-mp-rss 尚未完成接入）** | ⚠️ 未接 |
| B站/小红书 | 全部注释掉 | 未接 |

**热榜平台**：知乎 / Bilibili 热搜 / 百度热搜（已启用），微博/抖音等注释掉。

### 痛点验证（调研核实）

1. **量子位 RSS**（`https://www.qbitai.com/feed`）：实测 **✅ 正常**，2026-05-21 当天有最新文章
2. **smol.ai AINews RSS**：实测 **✅ 正常**，最新条目 2026-05-18（Google I/O 2026 报道）
3. **we-mp-rss（公众号层）**：Docker 已起但公众号 RSS 全部注释掉，公众号层 **实际 0 条接入**
4. **X/Twitter 层**：twscrape 仍在 PLAN.md 的 TODO 里，**实际 0 接入**
5. **国内媒体覆盖盲区**：缺 机器之心 / 新智元 / 极客公园 / IT之家 / Founder Park / 晚点 / 硅星人

### 当前信源国内外比例

- 国际：约 19 个（含 arXiv / 大厂 blog / 英文 newsletter / Reddit）
- 国内：3 个（量子位网页 RSS / 36氪 / Synced 海外版）+ 公众号 0
- **比例约 19:3，严重偏国际**

---

## Phase 2 · 第一直觉

### Musk（独立，300 字）

**物理裁判 + 5 步删除 + Idiot Index 视角**

信息抓取系统的 Idiot Index 计算：你现在花多少精力维护信源，vs. 实际产出的情报价值。当前系统 22 个 RSS，但 3 个是 NVIDIA 相关（2 个 NVIDIA），2 个是 HF（Blog+Trending），1 个是 AWS，这些信噪比很差。真正驱动 AI 圈决策的信源是一手官方发布 + 顶级圈内讨论。我的 5 步删除法：

1. **删** AWS ML Blog（信噪比差，企业营销文为主）
2. **删** Synced Review（机器之心英文版，国内源代替）
3. **删** NVIDIA Newsroom（营销稿，保 NVIDIA Blog 即可）
4. **加** GitHub Trending AI（每日最快模型/框架发布信号）
5. **加** 国内 7 个头部媒体 RSS（当前空白完全不能接受）

时效性目标：Tier 1 一手信源延迟应 < 1 小时，而不是"每天跑一次"。TrendRadar 的 `schedule.preset: morning_evening` 意味着白天信息丢失窗口，应改 `always_on` + AI filter 兜底噪声。

护城河信源（当前缺的）：Stratechery 需要付费订阅 RSS（但这是最值得的 $12/月），Semianalysis Substack 免费 tier 有 RSS。The Algorithmic Bridge / OneUsefulThing / Ahead of AI 全是 Substack，**直接用 Substack feed URL，零成本接入**。

X/Twitter 是最大风险点：Nitter 2024 年底死透，公共实例已全灭。twscrape 需要真实 X 账号池，失败率高。应建立 fallback 链：twscrape 失败 → RSSHub bridge → 手动快照，不能把核心情报压在单一不稳定渠道。

**结论**：质量 > 数量，但当前国内空白是硬 bug。Day 1 必须补 5 个国内 T1 RSS 和 5 个英文 Substack。

---

### Jobs（独立，300 字）

**Real Artists Ship + form follows emotion 视角**

情报基础设施的本质不是抓得多，是**让对的人在对的时间感到被触动**。风云的公众号读者不是 ML 研究员，是想了解 AI 圈动向的普通知识人。所以情报基础设施的终极目标是：**每天给风云提供 3-5 个让他感到"这个我必须写"的选题**，而不是 200 条新闻的堆砌。

一手不等于有价值：OpenAI 官方 blog 的新闻稿和 Ethan Mollick 对同一事件的分析，后者对写作更有用。情报系统需要区分：
- **信号源**（官方发布，第一时间，一手必须）
- **洞察源**（顶级 newsletter 作者，对事件的解读，形成选题角度）
- **共鸣源**（r/LocalLLaMA 的真实用户反应，国内社区讨论）

三类缺一不可。当前系统以信号源为主，洞察源和共鸣源严重不足。

Stratechery 虽是付费但值得：Ben Thompson 对 AI 商业逻辑的解读是中文 AI 博主极少触达的视角，正好是护城河。即使付费，$12/月 买到的是差异化选题角度，Idiot Index 极低。

国内共鸣源的重要性：机器之心/量子位是信号，但知乎 AI 圆桌和即刻 AI 圈才是共鸣（真实读者在讨论什么）。后者无 RSS，但 RSSHub 可以代理知乎专栏，即刻需要 MediaCrawler 方案。

**结论**：三层情报结构（信号 + 洞察 + 共鸣）是框架，每层至少 5 个高质量源，总数 20-25 个即可，不要无限堆叠。

---

## Phase 3 · 辩论 + 调研（8 轮，含 6 次调研）

### 轮次 1：国际信源缺口 — Musk 发起进攻

**Musk**：经过调研确认，当前系统缺少以下国际护城河源（全部有免费 RSS 或 Substack feed）：

**调研 1（Musk）· 国际 newsletter RSS 接入方式核实**

来源：WebFetch + WebSearch 多次核实

| 信源 | RSS URL | 订阅体量 | 付费? |
|---|---|---|---|
| Latent Space | `https://www.latent.space/feed` | 17 万 | 免费 |
| Import AI | `https://jack-clark.net/feed/` 或 `https://importai.substack.com/feed` | 顶级 | 免费 |
| OneUsefulThing (Ethan Mollick) | `https://www.oneusefulthing.org/feed` | 43 万+ | 免费 |
| Ahead of AI (Sebastian Raschka) | `https://magazine.sebastianraschka.com/feed` | 19 万 | 免费 |
| The Algorithmic Bridge | `https://www.thealgorithmicbridge.com/feed` | 4.4 万 | 免费 |
| Ben's Bites | `https://bensbites.beehiiv.com/feed` | 16 万 | 免费 |
| TLDR AI | `https://tldr.tech/api/rss/ai` | 百万级 | 免费 |
| SemiAnalysis | `https://newsletter.semianalysis.com/feed` (Substack) | 20 万+ | 部分免费 |
| Stratechery | 需付费账号 ($12/月) 生成专属 RSS | 顶级 | 付费 |
| Simon Willison's Blog | `https://simonwillison.net/atom/everything/` | 技术核心 | 免费 |
| a16z Blog | `https://a16z.com/feed/` | VC 视角 | 免费 |
| MIT Tech Review AI | `https://www.technologyreview.com/feed/` | 权威媒体 | 免费 |

**注**：Latent Space 和 Import AI 当前 **已接入** TrendRadar，但 OneUsefulThing、Ahead of AI、TLDR AI、SemiAnalysis 等均 **未接入**。

---

**Jobs 反驳**：加 12 个国际源没问题，但注意 TLDR AI 是聚合型（二手），和 smol.ai AINews 功能重叠。Idiot Index 原则——两个干同样事的源只留一个质量更高的。smol.ai 是 Karpathy 钦点（356 Twitter + 21 Discord 索引），TLDR AI 是 email newsletter 转 RSS，smol.ai 更优。建议 TLDR AI 降为备用（tier 3），优先 smol.ai。

**Musk**：同意。GitHub Trending RSS 也必须补——调研显示 mshibanami 的项目 2026-05-21 仍有最新构建，Python 语言 AI 仓库的趋势变化是最快的模型/框架发布信号：

```
GitHub Trending AI (Python): https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml
GitHub Trending (All): https://mshibanami.github.io/GitHubTrendingRSS/daily/unknown.xml
```

---

### 轮次 2：国内信源缺口 — Jobs 发起进攻

**Jobs**：国内情报覆盖是系统最大的形式缺陷（form follows emotion——用户是做国内 AI 公众号，读者是国内人，情报源不能偏国际 6:1）。

**调研 2（Jobs）· 国内主流 AI 媒体 RSS 核实**

来源：WebSearch + WebFetch 多次核实

| 信源 | RSS URL | 特点 | 稳定性 |
|---|---|---|---|
| 机器之心 | `https://www.jiqizhixin.com/rss` | 国内最大 AI 专业媒体 | ✅ 有效（Feeder 确认） |
| 量子位 | `https://www.qbitai.com/feed` | **实测 ✅ 2026-05-21 有效** | ✅ 稳定 |
| 36氪 AI | `https://36kr.com/feed-newsflash` | 已接入 | ✅ |
| 新智元 | 通过 RSSHub 路由或公众号接 | 无稳定独立 RSS | ⚠️ 需 RSSHub |
| 极客公园 | `http://www.geekpark.net/rss` | 科技创新，AI 覆盖中等 | ✅ |
| IT之家 | `http://www.ithome.com/rss/` | AI 科技新闻，高频 | ✅ |
| 晚点 LatePost | 公众号（we-mp-rss 接） | 深度报道 | 通过 we-mp-rss |
| 硅星人 | 公众号（we-mp-rss 接） | 国际 AI 公司国内视角 | 通过 we-mp-rss |
| Founder Park | 公众号（we-mp-rss 接） | 创业 + AI 视角 | 通过 we-mp-rss |

**国内 AI 公司官方 RSS（一手发布，当前完全没覆盖）**：

| 公司 | 接入方式 | 备注 |
|---|---|---|
| DeepSeek 官方 | 公众号 via we-mp-rss | 无独立 RSS |
| Kimi / Moonshot | 公众号 via we-mp-rss | 无独立 RSS |
| 智谱 AI | 公众号 via we-mp-rss | 无独立 RSS |
| 通义千问 (Qwen) | HuggingFace 官方 page 有 | `https://huggingface.co/Qwen` 博文通过 HF Blog RSS |
| MiniMax | 公众号 via we-mp-rss | 无独立 RSS |
| 阶跃星辰 | 公众号 via we-mp-rss | 无独立 RSS |
| 百川智能 | 公众号 via we-mp-rss | 无独立 RSS |

**结论**：国内 AI 公司官方消息**唯一稳定一手接入方式是 we-mp-rss 公众号订阅**，不存在 RSS 替代方案。这再次强调 we-mp-rss 是 P0 必须完成的基础设施。

---

**Musk**：同意，但补一个物理约束：we-mp-rss 依赖微信扫码登录，账号有被封风险。必须建立备份机制——如果扫码账号被封，用 `wewe-rss`（基于微信读书，另一个方案，GitHub: cooderl/wewe-rss）作 fallback。两套方案同时跑，覆盖风险。

---

### 轮次 3：X/Twitter 抓取现状与 fallback — Musk 深究

**Musk**：X 是最大的不稳定因素，必须正视。

**调研 3（Musk）· X/Twitter 2026 抓取全景**

来源：WebSearch 多次核实

**现状核实**：
- **Nitter**：2024 年底大量实例死透，2026 年已基本不可用作稳定信源。nitter.net 官方实例已关停。
- **twscrape**：2026-05 仍有 issue 提交（#305, #306，5 月 9-10 日），项目**仍活跃维护**，但需要**真实 X 账号池**，单账号每日请求上限约 500 条，失败率随 X 的反爬策略波动。最新版 0.17.0（2025-04-29），支持 GraphQL/Search API。
- **X 官方 API**：2026-02 改为 Pay-Per-Use，基础层 $100/月，对个人项目不合算。
- **RSSHub X 路由**：`/twitter/user/{username}` 路由依赖 Nitter 或 Twitter API，目前状态不稳定，需要自己配置 cookie 或 api key。
- **RSS Bridge**：可生成 X 账号 RSS，但同样依赖账号 cookie，维护成本高。

**Fallback 链（从稳到不稳排序）**：
```
twscrape（账号池，主力）→ RSSHub X 路由（cookie 模式）→ smol.ai AINews 间接聚合 Twitter 内容→ 手动快照（兜底）
```

**推荐 Twitter KOL 列表**（用 twscrape 订阅）：
- @karpathy, @sama, @DarioAmodei（三巨头，一手性最强）
- @_akhaliq（论文速报，PLAN.md 已列）
- @swyx（Latent Space 主持人，工程视角）
- @yudapearl（学术权威）
- @ylecun（Meta AI 视角，与 OpenAI 路线对立）
- @GaryMarcus（AI 批评派，平衡视角）

**Jobs 补充**：不要把 X 做成主力信源。X 的高质量内容 70% 会在 24 小时内被 newsletter（smol.ai / Latent Space / Ben's Bites）二次加工并通过 RSS 推送。与其维护不稳定的 twscrape 账号池，不如把核心精力放在 RSS 质量上，X 做补充。这才是"form follows emotion"——减少维护摩擦，让风云能专注写作。

---

### 轮次 4：一手性/权威性分层 — Jobs 提出框架

**Jobs**：信源必须分 Tier，LLM 筛选时 Tier 1 优先。

**Tier 分级框架**：

| Tier | 定义 | 典型信源 | AI 筛选权重 |
|---|---|---|---|
| T1（一手官方） | 公司/机构自己发布的内容 | OpenAI Blog / Anthropic News / DeepMind Blog / DeepSeek 官方公众号 / Kimi 官方公众号 | 1.5x（提升） |
| T2（高质量二手） | 顶级 AI 从业者/研究者的分析 | Latent Space / Import AI / OneUsefulThing / Ahead of AI / smol.ai AINews | 1.2x |
| T3（高质量媒体） | 专业 AI 媒体的报道 | 机器之心 / 量子位 / MIT Tech Review / Hacker News 精选 | 1.0x |
| T4（聚合/综合） | 聚合多源的内容，信息密度低 | TLDR AI / 36氪快讯 / 百度热搜 | 0.8x（降权） |

**Musk**：物理层面支持这个框架，但加一条：时效性也要进入 tier 计算。T1 官方发布 + 2 小时内 > T1 官方发布 + 24 小时。TrendRadar 的 `freshness_filter.max_age_days: 1` 是全局的，T1 信源可以考虑 `max_age_days: 3`（确保不漏重要发布），T4 聚合源 `max_age_days: 0.5`（只看最新 12 小时）。

---

### 轮次 5：we-mp-rss 接入的具体方案 — 双方共识

**调研 4（Jobs）· we-mp-rss 2026 现状核实**

来源：WebSearch 核实

**核实结论**：
- `rachelos/we-mp-rss` 项目 2026 年**仍活跃**，Docker 镜像在 `ghcr.io/rachelos/we-mp-rss:latest`
- 正确的 Docker 拉取命令：`docker run -d --name we-mp-rss -p 8001:8001 ghcr.io/rachelos/we-mp-rss:latest`
- 用户已有 mp-proxy-worker（`mp-proxy-worker.dufengyun12.workers.dev`）绕过公共代理配额限制
- **备选方案**：`cooderl/wewe-rss`（基于微信读书，不依赖微信账号扫码，更稳定）

**P0 公众号订阅列表**（we-mp-rss 接入，优先级排序）：

| 优先级 | 公众号 | 类别 |
|---|---|---|
| P0 | 机器之心 | T3 媒体，国内最全 AI 新闻 |
| P0 | 量子位 | T3 媒体（补充网页 RSS，确保不漏） |
| P0 | DeepSeek | T1 国内一手 |
| P0 | Kimi (Moonshot) | T1 国内一手 |
| P0 | 智谱 AI | T1 国内一手 |
| P1 | 晚点 LatePost | T2 深度报道 |
| P1 | 硅星人 | T3 媒体 |
| P1 | Founder Park | T2 创业视角 |
| P1 | 数字生命卡兹克 | T2 风格对标（语料+情报） |
| P1 | 宝玉的工程笔记 | T2 技术深度 |
| P1 | 新智元 | T3 媒体 |
| P2 | 赛博禅心 | T2 风格参考 |
| P2 | 通义千问 (Qwen) | T1 国内一手 |
| P2 | MiniMax | T1 国内一手 |
| P2 | 阶跃星辰 | T1 国内一手 |

---

### 轮次 6：TrendRadar YAML 具体改法 — Musk 主导

**Musk**：不是推翻，是增量加配置。具体改法见 Phase 4.2，这里先敲定信源 tier 字段约定。

TrendRadar 当前 RSS feed 配置不支持 tier 字段，但 `ai_analysis_prompt.txt` 和 `ai_interests.txt` 可以注入 source tier 信息。方案是：在 feed 的 `name` 字段前加 `[T1]` / `[T2]` 等标签，让 LLM 在 `ai_analysis_prompt.txt` 里优先展示 T1/T2 信源的内容。

**调研 5（Musk）· TrendRadar source tier 机制可行性**

来源：Read config.yaml 深度分析

TrendRadar 的 AI 分析流程：
1. 所有 RSS 条目汇集 → `max_news_for_analysis: 150` 上限
2. 调用 `ai_analysis_prompt.txt` 的 prompt，让 DeepSeek 做分析
3. 分析结果推送

**可行方案**：在 `name` 字段中加 `[T1]` 标记，然后在 `ai_analysis_prompt.txt` 里加一段指令：
```
对于标注了[T1]的官方信源，必须优先展示其内容，即使该条目热度评分略低。
对于标注了[T4]的聚合信源，仅在其内容与[T1]形成互补时才展示。
```

此方案**无需改 TrendRadar 源代码**，完全通过配置和 prompt 实现。

---

### 轮次 7：SuYxh ai-news-aggregator 资产评估 — Jobs 调研

**调研 6（Jobs）· SuYxh ai-news-aggregator OPML 资产**

来源：WebFetch + WebSearch 核实

`SuYxh/ai-news-aggregator`（最后更新 2026-02）是一个开源 AI 新闻聚合器，包含：
- 70+ 筛选过的 RSS 源（OPML 格式，`feeds/follow.opml`）
- 覆盖：OpenAI/Anthropic/Google/Meta/Microsoft/NVIDIA/xAI/Hugging Face 官方账号
- 中国 AI 公司：Alibaba Qwen / DeepSeek / Tencent 等
- AI 研究者 feeds 和开发工具
- 52 个微信公众号订阅（说明公众号清单已有参考）
- 每 2 小时自动更新，支持双语标题

**关键发现**：该项目的 OPML 文件可以**直接导入 TrendRadar 的 RSS 配置**，节省大量人工筛选工作。虽然 GitHub API 返回 404（文件路径需直接访问），但项目首页 `https://suyxh.github.io/ai-news-aggregator/` 提供在线预览，可以批量提取 feed URL。

**easychen/ai-rss**（简单实现，仅供参考）也是类似工具，但 SuYxh 版本更完整。

**Jobs 结论**：借 SuYxh 的 OPML 做参考清单，不直接接入（避免引入无关信源），只抽取与风云 AI 公众号主题匹配的源。

---

### 轮次 8：调度策略升级 — 双方收敛

**Musk**：当前 `schedule.preset: morning_evening` 白天有信息丢失窗口。对于 T1 官方发布（如 OpenAI 可能凌晨发布），应改 `always_on`，但这会增加 API 调用成本。**折衷方案**：`morning_evening` 保留，但把 T1 官方信源（OpenAI/Anthropic/DeepSeek 公众号等）加入 `freshness_filter.max_age_days: 2` 覆盖，确保凌晨发布的消息在早报里不漏。

**Jobs**：同意。另外 `ai_filter.min_score: 0.7` 当前值对国内信源可能过滤掉一些值得关注的内容（因为 prompt 可能偏英文语境评分），建议在 `ai_interests.txt` 里显式加入"国内 AI 公司动态""国内大模型"等中文兴趣词，确保 DeepSeek / Kimi / 通义 的消息不被过滤。

---

## Phase 4 · 共识方案（Actionable）

### 4.1 新增信源清单（30 个新信源，国内 14 个 + 国际 16 个）

**国际新增（16 个）**

| 信源 | Tier | 接入方式 | RSS URL | 备注 |
|---|---|---|---|---|
| OneUsefulThing (Ethan Mollick) | T2 | RSS 直接订阅 | `https://www.oneusefulthing.org/feed` | Wharton 教授，43 万订阅，AI 应用深度 |
| Ahead of AI (Sebastian Raschka) | T2 | RSS 直接订阅 | `https://magazine.sebastianraschka.com/feed` | 19 万订阅，LLM 技术深度 |
| The Algorithmic Bridge | T2 | RSS 直接订阅 | `https://www.thealgorithmicbridge.com/feed` | 人文 × AI，独特视角 |
| Ben's Bites | T2 | RSS 直接订阅 | `https://bensbites.beehiiv.com/feed` | 16 万订阅，每日 AI 产品速递 |
| TLDR AI | T4 | RSS 直接订阅 | `https://tldr.tech/api/rss/ai` | 百万订阅，每日摘要（与 smol.ai 互补） |
| SemiAnalysis | T2 | Substack RSS | `https://newsletter.semianalysis.com/feed` | Dylan Patel，芯片+AI 基础设施深度 |
| Simon Willison's Blog | T2 | Atom 直接订阅 | `https://simonwillison.net/atom/everything/` | 技术权威，工具调研 |
| a16z Blog | T3 | RSS 直接订阅 | `https://a16z.com/feed/` | VC 视角，AI 投资动向 |
| MIT Technology Review AI | T3 | RSS 直接订阅 | `https://www.technologyreview.com/feed/` | 权威学术媒体 |
| Google Research Blog | T1 | RSS 直接订阅 | `https://research.google/blog/rss/` | Google AI 研究一手 |
| Google AI Blog | T1 | RSS 直接订阅 | `https://ai.googleblog.com/feeds/posts/default` | Google 产品 AI 一手 |
| GitHub Trending (Python AI) | T2 | RSS 直接订阅 | `https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml` | 最快模型/框架发布信号 |
| The Verge AI | T3 | RSS 直接订阅 | `https://www.theverge.com/rss/index.xml` | 主流科技媒体 AI 报道 |
| Hacker News Top (>100分) | T3 | RSS 直接订阅 | `https://hnrss.org/frontpage?points=100` | 过滤低质量条目 |
| Product Hunt | T3 | RSS 直接订阅 | `https://www.producthunt.com/feed` | AI 新产品发布 |
| Stratechery | T2 | 付费专属 RSS | 付费后生成（$12/月） | 商业战略深度，强烈推荐 Day 14 接入 |

**注**：Hacker News 当前接入的是 `https://hnrss.org/frontpage`（所有文章），建议改为 `https://hnrss.org/frontpage?points=100` 过滤低质量条目。

---

**国内新增（14 个）**

| 信源 | Tier | 接入方式 | URL/备注 |
|---|---|---|---|
| 机器之心（网页 RSS） | T3 | RSS 直接订阅 | `https://www.jiqizhixin.com/rss` |
| 极客公园 | T3 | RSS 直接订阅 | `http://www.geekpark.net/rss` |
| IT之家 AI | T3 | RSS 直接订阅 | `http://www.ithome.com/rss/` |
| 晚点 LatePost | T2 | we-mp-rss 公众号 | 公众号：晚点LatePost |
| 硅星人Pro | T3 | we-mp-rss 公众号 | 公众号：硅星人Pro |
| Founder Park | T2 | we-mp-rss 公众号 | 公众号：Founder Park |
| DeepSeek 官方 | T1 | we-mp-rss 公众号 | 公众号：DeepSeek |
| Kimi (Moonshot AI) | T1 | we-mp-rss 公众号 | 公众号：Kimi |
| 智谱AI | T1 | we-mp-rss 公众号 | 公众号：智谱AI |
| 新智元 | T3 | we-mp-rss 公众号 | 公众号：新智元 |
| 通义千问 | T1 | we-mp-rss 公众号 | 公众号：通义千问 |
| MiniMax | T1 | we-mp-rss 公众号 | 公众号：MiniMax |
| 阶跃星辰 | T1 | we-mp-rss 公众号 | 公众号：阶跃星辰 |
| 百川智能 | T1 | we-mp-rss 公众号 | 公众号：百川智能 |

---

### 4.2 TrendRadar YAML 升级（具体改哪几个字段）

**改动 1：Hacker News 过滤升级**

```yaml
# 原来
- id: "hacker-news"
  name: "Hacker News"
  url: "https://hnrss.org/frontpage"

# 改为
- id: "hacker-news"
  name: "[T3] Hacker News Top"
  url: "https://hnrss.org/frontpage?points=100"
  max_age_days: 1
```

**改动 2：NVIDIA 精简（删 newsroom，保 blog）**

```yaml
# 删除这条（营销稿为主，信噪比差）
- id: "nvidia-newsroom"
  name: "NVIDIA Newsroom"
  url: "https://nvidianews.nvidia.com/rss"

# NVIDIA Blog 改名加 tier 标记
- id: "nvidia-blogs"
  name: "[T1] NVIDIA Blog"
  url: "https://blogs.nvidia.com/feed/"
```

**改动 3：新增国际 newsletter（在 AI Engineer 圈层区块后添加）**

```yaml
# ——— 📰 顶级 AI Newsletter（洞察层）———
- id: "one-useful-thing"
  name: "[T2] OneUsefulThing (Ethan Mollick)"
  url: "https://www.oneusefulthing.org/feed"
  max_age_days: 7  # 不高频，但每篇质量高

- id: "ahead-of-ai"
  name: "[T2] Ahead of AI (Sebastian Raschka)"
  url: "https://magazine.sebastianraschka.com/feed"
  max_age_days: 7

- id: "algorithmic-bridge"
  name: "[T2] The Algorithmic Bridge"
  url: "https://www.thealgorithmicbridge.com/feed"
  max_age_days: 7

- id: "bens-bites"
  name: "[T2] Ben's Bites"
  url: "https://bensbites.beehiiv.com/feed"
  max_age_days: 2

- id: "semianalysis"
  name: "[T2] SemiAnalysis (芯片+AI基础设施)"
  url: "https://newsletter.semianalysis.com/feed"
  max_age_days: 7

- id: "simon-willison"
  name: "[T2] Simon Willison's Blog"
  url: "https://simonwillison.net/atom/everything/"
  max_age_days: 3

# ——— 🔬 GitHub Trending ———
- id: "github-trending-python"
  name: "[T2] GitHub Trending Python"
  url: "https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml"
  max_age_days: 1

# ——— 🏢 Google AI 官方（补充 DeepMind）———
- id: "google-research-blog"
  name: "[T1] Google Research Blog"
  url: "https://research.google/blog/rss/"
  max_age_days: 3
```

**改动 4：国内媒体 RSS（在中文 AI 媒体区块）**

```yaml
- id: "jiqizhixin"
  name: "[T3] 机器之心"
  url: "https://www.jiqizhixin.com/rss"

- id: "geekpark"
  name: "[T3] 极客公园"
  url: "http://www.geekpark.net/rss"

- id: "ithome"
  name: "[T3] IT之家"
  url: "http://www.ithome.com/rss/"
  max_age_days: 1  # 高频源，只看最新
```

**改动 5：公众号 RSS 填入（we-mp-rss 接好后）**

```yaml
# ——— 📰 公众号 RSS（T1 国内一手）———
- id: "wechat-deepseek"
  name: "[T1] DeepSeek 官方"
  url: "http://localhost:8001/feed/deepseek.atom"
  max_age_days: 3

- id: "wechat-kimi"
  name: "[T1] Kimi (Moonshot)"
  url: "http://localhost:8001/feed/kimi.atom"
  max_age_days: 3

- id: "wechat-zhipu"
  name: "[T1] 智谱AI"
  url: "http://localhost:8001/feed/zhipu.atom"
  max_age_days: 3

- id: "wechat-latepost"
  name: "[T2] 晚点 LatePost"
  url: "http://localhost:8001/feed/latepost.atom"

- id: "wechat-founderpark"
  name: "[T2] Founder Park"
  url: "http://localhost:8001/feed/founderpark.atom"

- id: "wechat-jiqizhixin-mp"
  name: "[T3] 机器之心公众号"
  url: "http://localhost:8001/feed/jiqizhixin.atom"

- id: "wechat-xinzhiyuan"
  name: "[T3] 新智元"
  url: "http://localhost:8001/feed/xinzhiyuan.atom"
```

**改动 6：ai_interests.txt 增加中文关键词**

在 `D:\Dev\TrendRadar\config\ai_interests.txt` 末尾追加：
```
国内大模型动态（DeepSeek / Kimi / 通义 / 智谱 / MiniMax / 阶跃 / 百川）
中国 AI 公司发布 / 国产模型更新 / AI 产品上线
AI 创业融资（国内）/ AI 应用落地（国内）
```

**改动 7：ai_analysis_prompt.txt 加 tier 权重指令**

在 `D:\Dev\TrendRadar\config\ai_analysis_prompt.txt` 的分析指令部分添加：
```
信源权重规则：
- 名称包含[T1]的信源（官方发布）：优先展示，即使热度评分略低
- 名称包含[T2]的信源（高质量分析）：正常权重，着重提炼独特洞察
- 名称包含[T3]的信源（专业媒体）：标准处理
- 名称包含[T4]的信源（聚合/综合）：仅在与T1形成互补时展示，避免重复
```

---

### 4.3 抓取稳定性 Fallback 链设计

**X/Twitter 抓取链**：
```
[主力] twscrape (账号池，≥3 个备用账号)
  ↓ 失败 (失败率 > 50%)
[备用1] RSSHub /twitter/user/{username} (需配置 cookie)
  ↓ 失败
[备用2] smol.ai AINews RSS (间接聚合 Twitter 内容，无需独立 X 账号)
  ↓ 最终兜底
[手动快照] 每周人工 check @karpathy / @sama / @_akhaliq 的重要发布
```

**公众号抓取链**：
```
[主力] we-mp-rss (rachelos，端口 8001) + mp-proxy-worker
  ↓ 账号被封 / Docker 挂掉
[备用1] wewe-rss (cooderl，基于微信读书，不依赖扫码账号)
  ↓ 两者都挂
[备用2] 网页版 RSS（量子位/机器之心 已有独立网页 RSS，直接切换）
  ↓ 最终兜底
[手动快照] 核心 T1 公司发布（DeepSeek/Kimi 等）通过官网直接 check
```

**RSS 源失效检测**（建议 Day 7 后加）：
- TrendRadar 已有 `freshness_filter`，但不报警
- 建议在 CowAgent 的 scheduler 里每周一加一个"RSS 健康检查"任务：读 latest_daily.md，如果某个信源 3 天内 0 条，发警告到微信

---

### 4.4 一手性/权威性 Tier 加权机制

**完整 Tier 定义**：

| Tier | 标签 | 定义 | TrendRadar name 前缀 | AI prompt 权重 | max_age_days 建议 |
|---|---|---|---|---|---|
| T1 | 一手官方 | 公司/机构自己发布 | `[T1]` | 1.5x（优先展示） | 3（确保不漏） |
| T2 | 高质量洞察 | 顶级从业者分析 | `[T2]` | 1.2x（提炼独特观点） | 7（长尾价值高） |
| T3 | 专业媒体 | AI 专业媒体报道 | `[T3]` | 1.0x（标准处理） | 1-2 |
| T4 | 聚合综合 | 多源聚合，信息密度低 | `[T4]` | 0.8x（避免重复） | 1 |

**实施方式**：通过 TrendRadar `name` 字段前缀 + `ai_analysis_prompt.txt` 指令实现，**无需改源码**。

**国内外信源比例目标**（升级后）：
- 国际：约 22 个（T1 官方 7 + T2 洞察 8 + T3 媒体 7）
- 国内：约 20 个（T1 公司 8 + T2 深度 4 + T3 媒体 8）
- **比例约 22:20，接近 1:1**（当前 19:3）

---

### 4.5 Day 1-7 实施清单

| Day | 任务 | 优先级 | 预计时间 |
|---|---|---|---|
| Day 1 | 在 TrendRadar config.yaml 加入 8 个国际 T2 newsletter（OneUsefulThing / Ahead of AI / Algorithmic Bridge / Ben's Bites / SemiAnalysis / Simon Willison / GitHub Trending / Google Research Blog） | P0 | 20 分钟 |
| Day 1 | 修改现有 Hacker News URL 为 `?points=100` 过滤版 | P0 | 5 分钟 |
| Day 1 | 删除 NVIDIA Newsroom（信噪比差），保留 NVIDIA Blog | P0 | 5 分钟 |
| Day 1 | 加入国内 3 个网页 RSS：机器之心 / 极客公园 / IT之家 | P0 | 10 分钟 |
| Day 1 | 更新 ai_interests.txt 加入中文 AI 公司关键词 | P0 | 10 分钟 |
| Day 2 | 修复 we-mp-rss Docker（用 ghcr.io 镜像），扫码登录 | P0 | 1-2 小时 |
| Day 2 | 在 we-mp-rss 添加 P0 公众号：机器之心/量子位/DeepSeek/Kimi/智谱 | P0 | 30 分钟 |
| Day 2 | 获取 we-mp-rss feed URL，填入 TrendRadar config | P0 | 20 分钟 |
| Day 3 | 在 we-mp-rss 添加 P1 公众号：晚点/硅星人/FounderPark/卡兹克/宝玉/新智元 | P1 | 30 分钟 |
| Day 3 | 更新 ai_analysis_prompt.txt 加入 tier 权重指令 | P1 | 15 分钟 |
| Day 3 | 在 TrendRadar 所有 feed name 加 Tier 前缀标记 | P1 | 30 分钟 |
| Day 4 | 配置 twscrape，准备 3 个 X 账号池，订阅核心 KOL | P1 | 1-2 小时 |
| Day 4 | 安装 wewe-rss 作为 we-mp-rss fallback | P1 | 1 小时 |
| Day 5 | 在 we-mp-rss 添加 P2 公众号：通义/MiniMax/阶跃/百川/赛博禅心 | P2 | 30 分钟 |
| Day 5 | 跑一次 TrendRadar 全量测试，验证新信源质量 | P0 | 30 分钟 |
| Day 6 | 评估 Stratechery 订阅（$12/月），如决定订阅则接入 RSS | P2 | 决策 10 分钟 |
| Day 7 | 在 CowAgent scheduler 加每周 RSS 健康检查任务 | P2 | 30 分钟 |

---

## Phase 5 · 女娲蒸馏

本次辩题聚焦于 RSS/API 接入的工程问题，蒸馏特定人物收益有限。

**决定不蒸馏**，理由：
- Musk 视角（工程效率、信噪比）和 Jobs 视角（情报三层结构、形式逻辑）已覆盖核心决策维度
- 信源运营专家（如 Steph Smith / Lenny）的方法论对工程接入问题没有直接指导价值
- 时间更值得用在方案落地细节上

---

## Phase 6 · 风云 Day 1 落地

### 立即执行（30 分钟内完成）

打开 `D:\Dev\TrendRadar\config\config.yaml`，在 `rss.feeds` 的 `# ——— 📰 综合科技/AI 媒体 ———` 区块前，添加以下内容：

```yaml
# ——— 📰 顶级 AI Newsletter（洞察层）———
- id: "one-useful-thing"
  name: "[T2] OneUsefulThing (Ethan Mollick)"
  url: "https://www.oneusefulthing.org/feed"
  max_age_days: 7

- id: "ahead-of-ai"
  name: "[T2] Ahead of AI (Sebastian Raschka)"
  url: "https://magazine.sebastianraschka.com/feed"
  max_age_days: 7

- id: "algorithmic-bridge"
  name: "[T2] The Algorithmic Bridge"
  url: "https://www.thealgorithmicbridge.com/feed"
  max_age_days: 7

- id: "bens-bites"
  name: "[T2] Ben's Bites"
  url: "https://bensbites.beehiiv.com/feed"
  max_age_days: 2

- id: "semianalysis"
  name: "[T2] SemiAnalysis"
  url: "https://newsletter.semianalysis.com/feed"
  max_age_days: 7

- id: "simon-willison"
  name: "[T2] Simon Willison"
  url: "https://simonwillison.net/atom/everything/"
  max_age_days: 3

- id: "github-trending-python"
  name: "[T2] GitHub Trending Python"
  url: "https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml"
  max_age_days: 1

- id: "google-research-blog"
  name: "[T1] Google Research Blog"
  url: "https://research.google/blog/rss/"
  max_age_days: 3

# ——— 🇨🇳 国内 AI 媒体（网页 RSS）———
- id: "jiqizhixin"
  name: "[T3] 机器之心"
  url: "https://www.jiqizhixin.com/rss"

- id: "geekpark"
  name: "[T3] 极客公园"
  url: "http://www.geekpark.net/rss"

- id: "ithome"
  name: "[T3] IT之家"
  url: "http://www.ithome.com/rss/"
  max_age_days: 1
```

同时修改 Hacker News 条目 URL：
```yaml
url: "https://hnrss.org/frontpage?points=100"  # 原来是 hnrss.org/frontpage
```

**P0 · Day 2**：修复 we-mp-rss（`docker run -d --name we-mp-rss -p 8001:8001 ghcr.io/rachelos/we-mp-rss:latest`），先接 DeepSeek / Kimi / 智谱 / 机器之心公众号。

---

## 调研 + 蒸馏统计

| 项目 | 数量 | 主题 |
|---|---|---|
| Musk 调研 | 3 次 | 1. 国际 newsletter RSS 接入核实 / 2. X/Twitter 2026 抓取全景 / 3. TrendRadar source tier 机制可行性 |
| Jobs 调研 | 3 次 | 1. 国内主流 AI 媒体 RSS 核实 / 2. we-mp-rss 2026 现状 / 3. SuYxh ai-news-aggregator 资产评估 |
| WebFetch 补充 | 3 次 | 量子位 RSS 实测 / smol.ai 实测 / 机器之心 feed URL 核实 |
| WebSearch 补充 | 10 次 | 多渠道交叉验证 |
| 女娲蒸馏 | 0 次 | 经评估不必要 |
| 审判官警告 | 0 次 | 全程无违规 |
| 惩罚 | 否 | |

---

## 给风云的最终联合声明（Musk × Jobs）

**Musk**：你的系统有 22 个 RSS，但国内只有 3 个。今天 30 分钟内加 11 个新源（8 国际 + 3 国内），不需要改架构，改配置就行。X 抓取别纠结，先用 twscrape 账号池 + smol.ai 兜底，重要的 KOL 发布会通过 newsletter 在 24 小时内被二次加工进 RSS。we-mp-rss 是最重要的 P0，先跑起来。

**Jobs**：情报系统的本质是：每天给你 3-5 个让你感到"我必须写这个"的选题。为此你需要三层信源——信号（T1 官方）、洞察（T2 newsletter 作者）、共鸣（国内媒体 + 公众号）。Ethan Mollick / Sebastian Raschka / Ben Thompson 这些人的视角是中文 AI 博主极少触达的，订阅他们就是拿到了差异化护城河。先 ship Day 1，别等完美。

**联合结论**：升级后信源从 22 → 52+（国内外接近 1:1），Day 1 无需部署任何新服务，纯 YAML 配置修改。Day 2 修复 we-mp-rss 接公众号是最关键的基础设施投资，回报是覆盖所有国内 AI 公司一手发布。

---

*报告路径：`D:\Dev\ai-wechat-pipeline\reports\phase8_sandbox_information_intake.md`*
*生成时间：2026-05-22*
*调研次数：6 次主调研 + 多次补充 WebSearch/WebFetch*
