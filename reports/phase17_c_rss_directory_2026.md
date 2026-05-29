# Phase 17-C · AI 信源 RSS 大盘点 2026-05
*调研日期：2026-05-25 · 执行：Sonnet 4.6*

---

## 说明

本报告基于以下方法：WebSearch 多轮搜索候选 URL → WebFetch 验证（本次 WebFetch 权限在执行过程中被沙盒拒绝，降级处理：依赖搜索引擎返回的权威来源 + GitHub 开源 RSS 清单 + 第三方 RSS 阅读器发现的 alive 状态，每条标注验证来源和置信度）。

**已收入 config.yaml 的 60 个 feed 不在本报告推荐范围内。**

置信度说明：
- **[高]** — 搜索结果直接返回了 RSS XML 内容或权威来源明确说 alive，有近期（2025-2026）文章
- **[中]** — 从官网结构 / 第三方 RSS 发现工具推断，URL 模式可信但未直接拿到 XML
- **[低]** — 候选 URL 推断，未经任何间接验证

---

## 1. 国际新增推荐（17 个）

| # | name | URL | 类型 | 推荐理由 | 验证状态 |
|---|---|---|---|---|---|
| 1 | BAIR Berkeley AI Blog | `https://bair.berkeley.edu/blog/feed.xml` | T1 学术 | 伯克利 AI 实验室官方博客，2025-2026 有持续更新，覆盖 LLM/RL/Robotics 等一手研究；多个 RSS 目录均收录且标注 alive | [高] 搜索结果明确：2026 年 5 月有最新文章 |
| 2 | Stanford HAI News | `https://hai.stanford.edu/news/rss.xml` | T1 学术 | 斯坦福 HAI 是 AI 政策+学术权威机构，产出 AI governance / 社会影响类深度内容；第三方 Feeder.co 收录 | [中] URL 来自 Feedspot 权威 RSS 目录，结构标准 |
| 3 | The Gradient | `https://thegradient.pub/rss/` | T2 深度 | AI 学术与工业交叉的深度 essay 平台（非 newsletter），文章质量高，面向从业者；搜索结果直接返回其 RSS XML | [高] 搜索结果直接命中 RSS XML，2026-02 有最新文章 |
| 4 | LessWrong Curated | `https://www.lesswrong.com/feed.xml?view=curated-rss` | T2 洞察 | AI alignment / rationality 社区精选，Anthropic / DeepMind 研究员聚集地，国内几乎无人覆盖；官方 RSS 有多个参数化版本 | [高] 官方 GitHub 源码 + 社区帖子明确此 URL 有效 |
| 5 | AI Safety Newsletter (CAIS) | `https://feeds.type3.audio/cais--newsletter-ai-safety.rss` | T2 洞察 | Center for AI Safety 官方周刊，Hinton/Bengio 背书机构，AI safety 视角是中文圈极稀缺信源 | [高] 搜索结果直接命中此 RSS URL，CAIS 官网确认 |
| 6 | Last Week in AI | `https://lastweekin.ai/feed` | T3 聚合 | 百万级订阅 Substack，每周精选最重要 AI 新闻 + 评论，与 smol.ai 互补（周 vs 日）；Substack 标准 feed 路径 | [中] Substack 标准 `/feed` 路径，官网存在且活跃 |
| 7 | TechCrunch AI Category | `https://techcrunch.com/category/artificial-intelligence/feed/` | T3 聚合 | 科技媒体头牌，AI 分类每日更新，第三方 Feeder.co 收录且标注 alive；2026 年有持续报道 | [高] Feeder.co 收录 + 搜索结果确认 2026 活跃 |
| 8 | VentureBeat AI | `https://venturebeat.com/category/ai/feed/` | T3 聚合 | AI 商业落地报道权威媒体，与 TechCrunch 互补（VB 更偏企业应用），官网明确宣布此为新 RSS URL | [高] VentureBeat 官方文章宣布此 feed URL |
| 9 | Lex Fridman Podcast | `https://lexfridman.com/feed/podcast/` | T2 深度 | 最具影响力 AI 播客，嘉宾含 Musk/Altman/Lecun/Karpathy 等；官网明确 RSS 地址 | [高] 官网直接列出 `lexfridman.com/feed/podcast/` |
| 10 | Dwarkesh Patel Podcast | `https://api.substack.com/feed/podcast/69345.rss` | T2 深度 | 2024-2026 迅速崛起的深度 AI 访谈播客，采访 Sutskever/Karpathy/Altman 等；Substack 托管 podcast RSS | [高] 搜索结果直接命中此 RSS URL |
| 11 | Machine Learning Mastery Blog | `https://machinelearningmastery.com/blog/feed/` | T2 深度 | 最大的 ML 教程博客，开发者向；2025-2026 仍在更新，适合追踪 LLM 应用教程方向 | [中] 官网活跃，WordPress 标准 feed 路径 |
| 12 | CMU Machine Learning Blog | `https://blog.ml.cmu.edu/feed` | T1 学术 | 卡内基梅隆 ML 系官方博客，研究一手发布；多个 RSS 目录收录 | [中] 来自 RSS 目录工具推断，URL 结构标准 |
| 13 | MIT News AI/CSAIL | `https://news.mit.edu/topic/computer-science-and-artificial-intelligence-laboratory-csail.rss` | T1 学术 | MIT CSAIL 通过 MIT News 发布的 AI 研究新闻；MIT News 有完整 RSS 体系，CSAIL 专题页存在 | [中] MIT News 官网 RSS 体系确认，CSAIL topic 页存在 |
| 14 | The Gradient (Podcast RSS) | `https://thegradientpub.substack.com/feed` | T2 深度 | The Gradient 播客 + 新文章 Substack 镜像，与 thegradient.pub/rss/ 互补，可捕获迁移到 Substack 的内容 | [中] Substack 页面确认，标准 `/feed` 路径 |
| 15 | Alignment Forum | `https://www.alignmentforum.org/feed.xml` | T2 深度 | AI alignment 研究者专用发布平台（比 LessWrong 更专业），Anthropic/DeepMind 安全团队成员活跃；与 LessWrong 共用 ForumMagnum 引擎，feed 路径一致 | [中] 基于 LessWrong 相同引擎推断，论坛已确认存在 |
| 16 | GitHub Trending All Languages | `https://mshibanami.github.io/GitHubTrendingRSS/daily/unknown.xml` | T3 聚合 | 补充现有 Python Trending，捕获不限语言的 AI 项目爆发（如 Rust/Go 写的 LLM 工具）；与已有 Python Trending 同一 RSS 生成器 | [高] 与已收录的 `python.xml` 同源，生成器已验证 alive |
| 17 | ProductHunt AI | `https://www.producthunt.com/feed?category=artificial-intelligence` | T3 聚合 | AI 产品上线最快信号，每日精选新产品，与 HF Spaces Trending 互补（更偏 SaaS/应用层） | [低] URL 为推断，ProductHunt 支持 RSS 但 AI 分类参数未独立验证 |

---

## 2. 国内新增推荐（7 个）

| # | name | URL | 类型 | 推荐理由 | 验证状态 |
|---|---|---|---|---|---|
| 1 | RSSHub 掘金 AI 分类 | `https://rsshub.app/juejin/category/ai` | T3 聚合 | 掘金是国内最活跃的开发者社区，AI 分类日更量大；RSSHub 官方路由 `/juejin/category/ai` 已在 GitHub 源码确认 | [高] RSSHub 源码 `lib/routes/juejin/category.ts` 确认路由存在 |
| 2 | RSSHub 掘金 AI 标签 | `https://rsshub.app/juejin/tag/AI` | T3 聚合 | 与分类路由互补，捕获更精准的 AI 标签内容；RSSHub `/juejin/tag/:tag` 路由已在 GitHub 源码确认 | [高] RSSHub 源码 `lib/routes/juejin/tag.ts` 确认路由存在 |
| 3 | 少数派全站 | `https://rsshub.app/sspai/index` | T2 深度 | 国内高质量科技+效率媒体，定期发布 AI 工具评测和使用深度文章；RSSHub 官方路由 `/sspai/index` 已确认 | [高] RSSHub 文档明确列出 `/sspai/index` 路由 |
| 4 | CSDN AI 频道 | `https://www.csdn.net/nav/ai.xml` | T3 聚合 | 国内最大开发者社区 AI 频道；CSDN 传统上支持 RSS，URL 为标准模式 | [低] URL 为推断，需实测验证 |
| 5 | 开源中国 AI 资讯 | `https://www.oschina.net/news/rss` | T3 聚合 | 国内最大开源社区，AI 相关开源项目报道第一时间；开源中国长期维护 RSS | [中] 开源中国 RSS 历史上稳定，社区共识 alive |
| 6 | RSSHub 知乎话题 AI | `https://rsshub.app/zhihu/topic/19828946` | T3 聚合 | 知乎 AI 话题（ID 19828946）；作为现有知乎圆桌路由的补充，覆盖话题下全部热门回答；RSSHub `/zhihu/topic/:id` 路由已在文档确认 | [中] RSSHub 文档确认 `/zhihu/topic` 路由，话题 ID 需验证 |
| 7 | 博客园 AI 专区 | `https://feed.cnblogs.com/blog/sitehome/rss` | T3 聚合 | 国内老牌开发者博客社区，有稳定 RSS 输出；AI 方向文章质量参差但量大，可作为噪音容忍度高的补充信源 | [中] 博客园长期维护 RSS 服务，URL 为已知格式 |

---

## 3. 死链黑名单（本次调研发现）

| URL | 死法 | 发现时间 | 备注 |
|---|---|---|---|
| `https://distill.pub/rss.xml` | 停刊 (hiatus)，feed 可能仍存在但无新内容 | 2026-05-25 | Distill 宣布休刊，最后更新约 2021 年，**不要添加** |
| `http://www.fast.ai/atom.xml` | 404 File not found | 2026-05-25 | fast.ai 博客 RSS 已失效；Jeremy Howard 内容已迁移，无稳定公共 RSS |
| `http://www.sentient.ai/blog/feed` | 公司已关闭 | 2026-05-25 | Sentient Technologies 已解散 |
| `https://a16z.com/feed/` | 404，内容迁 Substack 私有 | 2026-05-22（Phase 8 已记录）| 已在 config.yaml 注释 |
| `https://www.anthropic.com/engineering/rss.xml` | 404 | 2026-05-22（Phase 8 已记录）| 已在 config.yaml 注释 |
| `http://feeds.feedburner.com/AIInTheNews` | Feedburner 2023-10 停服，全部 Feedburner URL 失效 | 2026-05-25 | AITopics 等依赖 Feedburner 的旧 feed 一律视为死链 |
| `https://machinelearnings.co/feed` | 站点已停更（最后更新约 2018）| 2026-05-25 | 信息太旧，不要添加 |

---

## 4. 备选「需要中转转 RSS」的信号源

以下信号源本身没有公开 RSS，但信息价值高，建议通过工具中转：

### 4.1 OpenAI Changelog
- **原因**：OpenAI 的 `openai.com/news/rss.xml` 收录博客，但 Changelog（产品更新日志）不在其中
- **中转方案**：用 [Inoreader](https://www.inoreader.com/) 的「网页监控」功能监控 `https://platform.openai.com/docs/changelog`，或用 [FetchRSS](https://fetchrss.com/) 生成 RSS
- **备选**：RSSHub 若有 `/openai/changelog` 路由可直接用

### 4.2 Anthropic Changelog
- **原因**：Anthropic 官方变更日志未提供 RSS
- **中转方案**：监控 `https://docs.anthropic.com/changelog`（FetchRSS / ChangeDetection.io）
- **置信度**：[低] 需实测页面是否可抓取

### 4.3 X/Twitter 名人列表（Karpathy / Yann LeCun / Sam Altman 等）
- **原因**：X 官方已关闭公共 API，Nitter 实例 2024 年底基本全灭
- **中转方案**：
  - [RSSHub Radar](https://chrome.google.com/webstore/detail/rsshub-radar/kefjpfngnndepjbopdmoebkipbgkggaa)：浏览器插件自动发现 RSS
  - `https://rsshub.app/twitter/user/:id`（公共实例高概率 403，需自建 + 配置 Twitter cookie）
  - [Bird.makeup](https://bird.makeup/)：Mastodon 桥接，可转 RSS（稳定性一般）
  - **推荐暂缓**：X 平台反爬变得和小红书一样严，等合法方案成熟

### 4.4 HuggingFace Spaces Trending
- **原因**：HF Spaces 无官方 RSS
- **中转方案**：`https://rsshub.app/huggingface/spaces` 若路由存在可用；或用 GitHub Actions 每日 scrape HF API `https://huggingface.co/api/spaces?sort=trending&limit=20` 输出 Atom
- **置信度**：[低] RSSHub 对 HF Spaces 的路由支持待验证

### 4.5 The Batch (Andrew Ng / DeepLearning.AI)
- **原因**：无公开 RSS（Phase 8 已确认）
- **中转方案**：[Kill the Newsletter](https://kill-the-newsletter.com/) — 生成一个邮箱地址，订阅 The Batch 后自动转 Atom feed
- **置信度**：[高] Kill the Newsletter 是成熟工具，原理可靠

### 4.6 即刻 AI 圈精选
- **原因**：即刻无官方 RSS，但 AI 圈用户的即时讨论是国内共鸣源
- **中转方案**：`https://rsshub.app/jike/topic/:id`（RSSHub 路由），找即刻 AI 相关话题 ID
- **置信度**：[中] RSSHub 有即刻路由，但话题 ID 需人工查找

---

## 5. 优先级推荐（Top 10 立即可加）

按「信息价值 × 接入成本 / 信噪比」排序，建议下次 config.yaml 更新时优先添加：

| 优先级 | name | URL | 理由 |
|---|---|---|---|
| P0 | BAIR Berkeley AI Blog | `https://bair.berkeley.edu/blog/feed.xml` | 学术一手，高质量，已有多方验证 alive |
| P0 | TechCrunch AI | `https://techcrunch.com/category/artificial-intelligence/feed/` | 媒体头牌，AI 分类 alive，与现有媒体层互补 |
| P0 | RSSHub 掘金 AI 分类 | `https://rsshub.app/juejin/category/ai` | 填补国内开发者社区空白，路由已确认 |
| P0 | LessWrong Curated | `https://www.lesswrong.com/feed.xml?view=curated-rss` | AI alignment 独家视角，中文圈无人覆盖 |
| P1 | The Gradient | `https://thegradient.pub/rss/` | 高质量 AI 长文，直接验证 alive |
| P1 | VentureBeat AI | `https://venturebeat.com/category/ai/feed/` | AI 商业应用视角，官方确认 URL |
| P1 | AI Safety Newsletter (CAIS) | `https://feeds.type3.audio/cais--newsletter-ai-safety.rss` | Safety 视角差异化，RSS URL 直接命中 |
| P1 | 少数派全站 | `https://rsshub.app/sspai/index` | 国内精品科技媒体，RSSHub 路由已确认 |
| P2 | Lex Fridman Podcast | `https://lexfridman.com/feed/podcast/` | 播客层补充，顶级 AI 嘉宾访谈 |
| P2 | GitHub Trending All | `https://mshibanami.github.io/GitHubTrendingRSS/daily/unknown.xml` | 与已有 Python Trending 同源，补全语言覆盖 |

---

## 6. 调研方法说明

1. 读取 `D:\Dev\TrendRadar\config\config.yaml` 提取现有 60 个 feed（去重基准）
2. 读取 `D:\Dev\ai-wechat-pipeline\reports\phase8_sandbox_information_intake.md`（前序调研参考）
3. WebSearch × 12 轮：学术机构 RSS、AI Safety RSS、播客 RSS、国内社区 RSS、VC/媒体 RSS、RSSHub 路由、awesome-AI-feeds GitHub 清单
4. WebFetch × 1 次成功（awesome-AI-feeds README，提取了 15 个候选 URL）
5. WebFetch 验证：本次沙盒拒绝直接 WebFetch 大多数 URL，降级使用搜索引擎返回内容 + 第三方 RSS 发现工具（Feeder.co / Feedspot）的 alive 标注 + 官方文档明确说明作为置信度依据
6. 死链判断：基于搜索结果明确提及「停刊」「404」「停服」或最后更新日期 > 2年

---

*报告结束 · phase17_c_rss_directory_2026.md*
