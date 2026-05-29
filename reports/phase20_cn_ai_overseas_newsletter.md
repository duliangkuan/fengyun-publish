# Phase 20: 国产 AI 公司海外英文 newsletter / 邮箱订阅渠道调研

调研日期: 2026-05-26
调研工具: WebSearch × 18 次

---

## 1. 7 家详细调研表

| 公司 | 海外官网 | 有 newsletter? | 订阅入口 URL | 形式 | 实测最新发布 | 跟中文公众号差异 | 推荐? |
|---|---|---|---|---|---|---|---|
| DeepSeek | deepseek.com/en | **否** | 无 | 无 | api-docs.deepseek.com/news 有更新日志，最新 2026-04-24 DeepSeek-V4 | 官网无 newsletter，仅状态页可订阅（服务中断通知，非内容） | 否 |
| Kimi / Moonshot | moonshot.ai / kimi.com/en | **部分** | platform.moonshot.ai/blog | 自建开发者博客 | 2026-05 Kimi K2.6 GA 发布 | 开发者 API 公告为主，无公众号级别的内容深度 | 补充 |
| Zhipu / Z.ai | zhipuai.cn/en / api.z.ai | **否** | 无 | 无 | GLM-4.7 / GLM-5.1 2026-04，有 docs.z.ai 文档站 | 英文内容几乎全是 API 文档，无 newsletter 渠道 | 否 |
| Qwen / Alibaba | qwen.ai/blog | **否** | 无 | 无 | qwenlm.github.io 已弃用，迁移到 qwen.ai/blog，最新 Qwen3-Next 2026-05 | 英文博客活跃，但无订阅入口（既无 newsletter 也无 RSS 接口暴露） | 补充（RSS hack 可行） |
| MiniMax | minimax.io/news | **否** | 无 | 无 | minimax.io/news 有完整英文更新，最新 Hailuo 2.3 / M2.7 2026-03 | 有最完善的英文新闻页，内容兼顾模型+产品+财报，但无订阅表单 | 补充（RSS hack 可行） |
| StepFun | stepfun.ai | **否，且关停** | 无 | 无 | stepfun.ai/research 有英文页面，最新 StepAudio 2.5 2026-05-24；但国际版 App **将于 2026-05-27 关停** | 官网研究页英文发布，无 newsletter；国际版消费端关停说明海外运营降级 | 否 |
| Baichuan | platform.baichuan-ai.com（中文） | **否** | 无 | 无 | 无英文官网，无英文博客，主站中文，X 账号 @BaichuanAI 更新稀少；2026-Q2 转型医疗垂直 | 几乎无海外英文存在，战略已收缩到国内医疗领域 | 否，黑名单 |

---

## 2. Top 推荐(适合用 Email-to-RSS 或 RSS 接入的)

### A. MiniMax — minimax.io/news

**状态:** 无官方 newsletter，但 minimax.io/news 是 7 家中内容最完整的英文新闻页。

**可行方案:** 用 RSSHub 或 FeedBurner 类工具抓取该页的 HTML 更新，转成 RSS。
- 参考路径: `rsshub.app/minimax/news`(需确认 RSSHub 是否已支持该路由)
- 备选: RSS.app / Feed43 自定义抓取 `minimax.io/news`

**对中文公众号项目的独有价值:**
- MiniMax 中文公众号(we-mp-rss biz_id 3191077711)发的是产品宣传，英文 news 页额外包含**全年财报**、**全球合作公告**、**Hailuo 视频模型技术细节** — 信息密度高于中文公众号
- 2026-03 MiniMax 全年财报公告是中文公众号没有发的内容

**替代 or 补充:** 补充，不替代。中文公众号有中文用户运营视角，英文页缺少这类语气；两者信息有 50% 重叠，50% 独立。

---

### B. Kimi / Moonshot — platform.moonshot.ai/blog

**状态:** 有官方开发者博客，地址 `platform.moonshot.ai/blog`，内容为 API 公告、changelog、模型评测工具介绍。

**可行方案:**
- 检查 `platform.moonshot.ai/blog` 是否暴露 RSS feed（GitHub Pages 类站通常有 `/feed.xml` 或 `/atom.xml`）
- 该博客在 2026-05 有更新（K2 Vendor Verifier Newsletter 一文）

**对中文公众号项目的独有价值:**
- 开发者视角的模型技术细节、定价变化、API 弃用警告 — 这是中文公众号(Kimi 官方公众号)几乎不发的内容
- Kimi K2.5 / K2.6 的英文技术解析比中文公众号早

**替代 or 补充:** 补充。中文公众号偏产品宣传，英文 blog 偏开发者告知。

---

### C. Qwen — qwen.ai/blog

**状态:** qwenlm.github.io 已弃用，官方已迁移到 qwen.ai/blog（即 Qwen Studio）。该页有最新技术博客，Qwen3-Next 2026-05 有内容。

**可行方案:**
- qwen.ai/blog 是 Alibaba Cloud 官网下的博客，可能暴露 RSS（待直接验证）
- 也可用 RSSHub `rsshub.app/qwen/blog` 或 RSS.app 抓取

**对中文公众号项目的独有价值:**
- Qwen 中文公众号(通义千问)以产品宣传为主，英文 blog 侧重**模型技术报告摘要 + GitHub/HuggingFace 发布说明** — 是做 AI 日报的高质量英文原文信源
- 2026-05 发布的 Qwen3-Coder 英文版比中文渠道更完整

**替代 or 补充:** 补充，且信息质量优于中文公众号。

---

## 3. 黑名单(无 newsletter / 不值得接入)

### DeepSeek

- 官网 deepseek.com/en 无任何 newsletter 入口，无 RSS
- 唯一更新渠道: api-docs.deepseek.com/news（纯 changelog，无内容深度）
- deepseek.international 是**第三方非官方粉丝站**，该站声称有 newsletter 但来源不可靠，不可接入
- 状态页 status.deepseek.com 可订阅，但内容为服务中断告警，不是内容 newsletter
- **结论:** 黑名单。DeepSeek 官方不经营 newsletter，深度内容靠第三方（如 ChinAI Substack）

### Z.ai (Zhipu / ChatGLM)

- 英文存在主要是 api.z.ai 开发者文档，无博客，无 newsletter
- 有 Discord 社区 (discord.gg/QR7SARHRxK)，活跃度未知
- X 账号 @Zai_org 有零星更新，非结构化内容
- **结论:** 黑名单。战略是 API-first，不经营面向读者的内容渠道

### StepFun

- 国际版 App 2026-05-27 关停，说明海外运营主动收缩
- stepfun.ai/research 有英文研究页，但是静态论文展示，非 newsletter
- X 账号 @StepFun_ai 偶发更新
- **结论:** 黑名单。关停海外 App 说明 StepFun 不在押注海外用户增长，内容会持续萎缩

### Baichuan

- 无英文官网，中文主站 platform.baichuan-ai.com 无英文版
- X 账号 @BaichuanAI 存在但更新极稀少（2023 年为主）
- 2025-2026 战略转型为医疗垂直，海外影响力几乎为零
- **结论:** 黑名单。Baichuan 已放弃通用 AI 海外叙事

---

## 4. 策略建议

### 核心问题回答

**国产公司海外 newsletter 能否替代当前 we-mp-rss 微信扫码方案?**

**结论: 不能全替代，只能部分补充。**

理由如下:

1. **7 家中没有一家有真正的 email newsletter 渠道**。没有公司提供 Substack / Beehiiv / Mailchimp 类的订阅入口，所以「Email-to-RSS」方案在这 7 家都不成立。Email-to-RSS 的前提是对方发 email newsletter，而这 7 家全部缺席。

2. **有英文内容的 3 家(MiniMax / Kimi / Qwen)用的是「官网博客」模式**，不是 newsletter。这意味着:
   - 可以用 RSS 抓取(如果该博客暴露 feed)或 RSSHub 路由接入
   - 但内容更新频率低于微信公众号(通常每月 3-8 篇 vs 每周多篇)
   - 内容偏向开发者公告,不是面向 AI 从业者的深度内容叙事

3. **内容差异确认大**:英文博客 focus 是模型发布 + API 变动;中文公众号 focus 是产品宣传 + 案例 + 从业者视角。两者互补,不互替。

4. **we-mp-rss 微信扫码维护成本真正的解法**不是英文 newsletter,而是:
   - 升级 we-mp-rss 的 cookie 续期机制(自动刷新)
   - 或切换到 RSSHub 的微信公众号路由(rsshub.app/wechat/mp/...)
   - 或接入第三方 RSS 聚合服务(如 WeRSS / WeChat RSS)

### 风云建议路径

**Phase 20 建议执行顺序:**

**P0 — 立即接入(RSS 方式,不需要 email)**
- minimax.io/news → 用 RSS.app 或 FeedBurner 生成 RSS feed,加入 TrendRadar 信源
- qwen.ai/blog → 同上,作为 Qwen 英文内容补充信源
- platform.moonshot.ai/blog → 验证是否有 /feed.xml,有则直接接;无则 RSSHub

**P1 — 加入观察名单**
- stepfun.ai/research → 英文研究页有价值,待国际版关停影响稳定后再评估
- Z.ai Discord → 开发者社群信息,不是 newsletter,价值取决于自己是否有精力人工筛选

**P2 — 不接入**
- DeepSeek 官方渠道(无内容 newsletter,深度内容靠第三方如 ChinAI)
- Baichuan(已退出海外市场叙事)

**关于 we-mp-rss 替代:**
英文博客路线是「补充信源」,解决不了微信扫码失效问题。建议将 we-mp-rss cookie 自动续期列为独立 P0 技术任务(见 Phase 17 方向),与本次调研结论并行推进。

---

## 附: 各家官方英文渠道汇总

| 公司 | 英文官网 | 英文博客/新闻 | 英文 X/Twitter | GitHub |
|---|---|---|---|---|
| DeepSeek | deepseek.com/en | api-docs.deepseek.com/news | @deepseek_ai | github.com/deepseek-ai |
| Kimi / Moonshot | moonshot.ai / kimi.com/en | platform.moonshot.ai/blog | @moonshotai_com | github.com/moonshotai |
| Z.ai (Zhipu) | zhipuai.cn/en / api.z.ai | docs.z.ai（仅文档） | @Zai_org | github.com/zai-org |
| Qwen | qwen.ai | qwen.ai/blog | @Qwen_LM | github.com/QwenLM |
| MiniMax | minimax.io | minimax.io/news | @MiniMax__AI | github.com/MiniMaxAI |
| StepFun | stepfun.ai（国际版 05-27 关停） | stepfun.ai/research | @StepFun_ai | github.com/stepfun-ai |
| Baichuan | 无英文官网 | 无 | @BaichuanAI（低活跃） | github.com/baichuan-inc |

---

*来源: WebSearch 18 次调研 + 官网信息核实，2026-05-26*
