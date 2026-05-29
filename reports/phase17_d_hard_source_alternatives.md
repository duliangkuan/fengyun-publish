# Phase 17-D: 难抓信源的 2026-05 替代路径调研

**日期**: 2026-05-25
**背景**: 「研究Agent的云」AI 公众号项目,部分高价值信源因反爬升级 / 平台限制变成"难抓"。本报告横向调研 2026-05 当下各难抓平台的有效替代路径,**免费优先**。
**注**: 完整报告由 Agent D 调研产出,sub-agent Write 权限被拒,本文件基于调研摘要落地;如需更详细原始内容可重派 agent。

---

## A. 公众号补充路径

主力 we-mp-rss(2026-05-18 仍活跃)继续。

| 方案 | 类型 | 状态 / 成本 | 注意 |
|---|---|---|---|
| we-mp-rss(ghcr.io/rachelos) | 开源,需扫码 | 当前在用,本机 / 国内 VPS | cookie 1-3 天失效 |
| wewe-rss | 开源,需扫码 | **2026-05-11 archived 停止维护** | 不推荐 |
| Wechat2RSS(xlab,wechat2rss.xlab.app) | 商业服务,**非扫码** | 服务商代维护 token,平均 6 小时延迟 | 费用需注册查价 |
| wechat-download-api(tmwgsicp) | 开源,需扫码,内置 IP 代理池 | v1.4.0,2026-05-18 | we-mp-rss 同类替代 |

**结论**:非扫码的开源免费方案目前不存在。**走 we-mp-rss + 国内 VPS** 仍是最优,Wechat2RSS 是付费免维护的兜底。

---

## B. X / Twitter

| 方案 | 类型 | 成本 | 状态 |
|---|---|---|---|
| 公共 Nitter 实例 | 公共服务 | 0 | **基本失效** |
| xcancel.com RSS | 公共镜像 | 0 | User-Agent 限制问题,不适合生产 |
| twscrape 账号池 | 自建 | 5-10 账号 + 住宅代理 ≈ $20-50/月 | 可行,每 2-4 周跟库更新 |
| RSS.app | 商业 SaaS | 付费 | 稳定 |
| Twitter 官方 API | 官方 | $42,000/年起 | 排除 |

**风云建议路径**:轻量需求用 xcancel 摸着用,正式生产用 twscrape 自建账号池(同步阅读 `D:\Dev\TrendRadar\docs\twitter_intake_design.md` 已有方案)。商业 SaaS 是兜底。

---

## C. 小红书

| 方案 | 类型 | 成本 | 状态 |
|---|---|---|---|
| TikHub V7(`xiaohongshu_web_get_note_info_v7`) | 商业 API | 已付费 $5 | **当前唯一稳定路径** |
| Playwright + 代理池 + 指纹 | 自建 | 工程成本高 | 2026-05 小红书升级多维指纹(Canvas+WebGL+字体)+ x-sx-t 签名 5 分钟轮换,工程门槛高 |
| Bright Data | 商业服务 | $1.50/1K 请求 | 高预算备选 |
| Apify zhorex | 商业服务 | — | **已废**(memory [[feedback_zhorex_dead]] 2026-05-20) |

**风云建议路径**:**继续 TikHub V7 主力**,不要自建 Playwright(memory [[feedback_xhs_anti_crawl_2026_05]] 已锁定);只有 TikHub 失效后才考虑 Bright Data 高预算兜底。

---

## D. 抖音 / 视频号

| 平台 | 方案 |
|---|---|
| 抖音 | TikHub 已覆盖(同一付费账号) |
| 视频号 | 无可行自动化路径,**暂不纳入信源体系** |

---

## E. Email Newsletter 转 RSS

| 方案 | 类型 | 成本 | 注意 |
|---|---|---|---|
| Kill the Newsletter | 公共服务 | 0 | **Substack 过滤其域名**,部分 newsletter 拿不到 |
| Email-to-RSS(github.com/yl8976/Email-to-RSS) | 自建 | 0(Cloudflare Workers + ForwardEmail + 自有域名) | 2024-2025 新出现的最优自建路径,**能绕过 Substack 过滤** |
| Inoreader Web Feeds / Feedbin Newsletter | 商业 SaaS | 付费 | 兜底 |

**风云建议路径**:**自建 Email-to-RSS**(Cloudflare Workers + 自有域名,免费 + 绕 Substack 过滤),用来订 The Batch / Stratechery 免费版 / 各种 Substack。

---

## F. Reddit / HackerNews

| 平台 | 方案 | 成本 |
|---|---|---|
| Reddit subreddit | 官方 `reddit.com/r/<sub>/.rss` 直接订(如 `reddit.com/r/LocalLLaMA/.rss`) | 0,无需 API key |
| HackerNews | **HNRSS.org**(可配置积分阈值,如 `?points=100`)替代官方 RSS | 0 |

**风云建议路径**:
- 当前 config 里 `r/LocalLLaMA` 已用官方 RSS,正确
- 当前 HN 已用 `hnrss.org/frontpage?points=100`,正确
- 可补:`r/MachineLearning`、`r/singularity`、`r/OpenAI`、`r/Anthropic` 等 subreddit 直接拼 `.rss`

---

## 总体策略

1. **公众号**:we-mp-rss + 国内 VPS,不另寻替代(开源圈无突破)
2. **X / Twitter**:轻量 xcancel,正式 twscrape 账号池
3. **小红书**:TikHub V7 不动,不自建
4. **抖音**:TikHub;视频号放弃
5. **Email Newsletter**:**自建 Email-to-RSS**(0 成本拿到 Substack 私有 feed)
6. **Reddit / HN**:官方 RSS / HNRSS 已最优,补订几个 subreddit 即可

---

*调研次数: 30 次工具使用(WebSearch + WebFetch)*
*来源标注见 agent 原始摘要*
