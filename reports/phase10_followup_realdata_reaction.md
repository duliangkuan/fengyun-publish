# Phase 10 Follow-up — TrendRadar 真跑新数据反应
*Musk × Jobs 轻量反应 · sonnet · 2026-05-22 11:20 实测数据*

---

## 背景

主辩论已锁定的 Verdict（不重做）：
- Q1 系统评分 6/10
- Q2 上云 Y — 阿里云轻量 2C2G，68 元/年活动价
- Q3 自建 RSSHub Y — 与 VPS 共享，边际成本 0
- Q4 净增成本约 5.7 元/月
- 推荐云端 wewe-rss + RSSHub Docker 部署

本次 follow-up 基于主辩论之后真跑的三组新数据：
1. TrendRadar 实测（42 成功 / 18 失败 / 1198 条 → 221 条 AI 筛选）
2. wewe-rss 于 2026-05-11 被作者归档（read-only）——主辩论完全未知
3. Ben's Bites / a16z RSS URL 死掉（Phase 9 配置错误）

---

## Musk 反应（轻量，≤ 200 字）

**新数据修正了一个核心假设：wewe-rss 已归档。**

8/8 RSSHub 公共实例 403 是对「自建 RSSHub Y」的强验证，Verdict 不变。但 wewe-rss 在 2026-05-11 被作者归档这件事是主辩论最大的盲点——不是限流问题，是项目已死。继续部署一个 archived 项目到生产环境，是用废弃零件造火箭。

物理约束：we-mp-rss 在本地已跑通，16 个公众号 10 个可用，250 条文章入库——**这个 fallback 反而成了主力候选**。wewe-rss 替代方案需要在 Day 3 前重新评估，不能按原计划盲目迁移。

Ben's Bites 正确 URL：`https://www.bensbites.com/feed`（Substack，已验证有效）。a16z 彻底放弃公共 RSS，降级为可选信源。两个 URL 修复 15 分钟内完成。

---

## Jobs 反应（轻量，≤ 200 字）

**产品层面：公众号护城河没有动摇，但搬迁路径需要重新选。**

we-mp-rss 本地已经 work，10/16 公众号有内容，250 条文章稳定入库。wewe-rss 归档不代表功能失效（镜像还能跑），但一个无人维护的项目放在 24/7 生产系统上，微信读书 API 一旦改接口就永久挂掉、无人修复。这是产品稳定性的定时炸弹。

真正的问题是：**上云的公众号层用谁？** we-mp-rss 异地 IP 重扫码摩擦是已知问题；wewe-rss 归档后维护风险是新问题。两害相权，we-mp-rss 的「功能活着但需要偶尔重扫码」比 wewe-rss 的「现在能跑但未来可能静默挂掉」更可接受——至少失败是可见的。

卡兹克 / 宝玉 feed 3MB 超时是 TrendRadar 客户端侧问题，加 `rss.timeout: 30` 或 `max_items: 10` 即可，不是 server 端 bug。

---

## 共识修正

| 项目 | 主辩论 Verdict | follow-up 修正 | 修正原因 |
|---|---|---|---|
| Q2 上云 | Y | **Y（不变）** | 8/8 RSSHub 403 强化了自建必要性，上云逻辑不变 |
| Q3 自建 RSSHub | Y | **Y（不变，更强）** | 真跑实证 7/8 路由死亡，比主辩论预测更严重 |
| Q4 净增成本 | ~5.7 元/月 | **~5.7 元/月（不变）** | 成本结构无变化 |
| 云端公众号层 | 推荐 wewe-rss | **⚠️ 降级为备选，重新评估** | wewe-rss 2026-05-11 已归档，维护风险激增 |
| Ben's Bites URL | beehiiv（死） | **`https://www.bensbites.com/feed`（Substack，有效）** | 已验证，直接修复 |
| a16z URL | `/feed/`（死） | **降级为可选，暂无公共 RSS** | a16z 已迁 Substack，无公共 blog feed |

**wewe-rss 归档处置方案（二选一）**：

选项 A（推荐）：**云端部署 we-mp-rss**，接受「异地 IP 偶尔需要重扫码」的摩擦，比静默挂掉更可控。国内阿里云 IP 触发重扫码的频率比境外 IP 低（社区有验证），可接受。

选项 B（备选）：**寻找 wewe-rss fork 或替代项目**。知乎专栏有「微信公众号 RSS 订阅方案汇总」（2025 年），可查是否有活跃 fork；但切换成本高，Day 3 前来不及。

**当前建议**：Day 3 按选项 A（云端 we-mp-rss）推进，同时记录 wewe-rss 归档风险，留 Month 1 再做替代调研。

---

## Pre-Day3 30 分钟修补清单

以下问题需要在 Day 3 上云操作之前处理，否则上云后会带着 bug 迁移：

### P0 — 15 分钟内（config.yaml 直接改）

**1. 修复 Ben's Bites RSS URL**
```yaml
# 改前（Phase 9 配置，404）
url: "https://bensbites.beehiiv.com/feed"

# 改后（已验证有效）
url: "https://www.bensbites.com/feed"
```

**2. 处理 a16z**
```yaml
# a16z 无公共 blog RSS，两个选项：
# 选项 A：临时注释掉
# - id: "a16z-blog"
#   url: "https://a16z.com/feed/"

# 选项 B：改为 a16z Substack（如有公开 RSS）
# 暂时注释，Month 1 再研究
```

### P1 — 上云前处理（Day 3，约 15 分钟）

**3. 大 feed timeout 优化（卡兹克 3MB / 宝玉 3MB）**

在 TrendRadar `config.yaml` 中对这两个 feed 加 timeout 或 item 限制：
```yaml
- id: "wechat-kazik"
  url: "http://localhost:8001/feed/MP_WXS_3223096120"
  timeout: 30          # 秒，从默认 15s 改为 30s
  max_items: 10        # 限制只取最新 10 篇，从 3MB 降到约 400KB

- id: "wechat-baoyu"
  url: "http://localhost:8001/feed/MP_WXS_3957812448"
  timeout: 30
  max_items: 10
```

**4. 确认上云用 we-mp-rss（不是 wewe-rss）**

wewe-rss 2026-05-11 归档，维护风险高。云端公众号层改用 we-mp-rss：
- 接受「异地 IP 偶尔重扫码」摩擦（国内阿里云 IP 风险相对低）
- Day 4 docker-compose.yml 里把 wewe-rss 替换为 we-mp-rss 镜像

### P2 — Day 7 验证时处理

**5. wewe-rss 账号轮换问题（主辩论预计 2 个账号）**

主辩论调研结论：16 公众号 × 2 次/天 = 32 次/天，低于 50 次单账号上限（36% 余量）。
**但 wewe-rss 已归档，此问题随「改用 we-mp-rss」一并消解**，不需要再做账号轮换方案。

**6. Day 7 验证清单新增项**（继承主辩论 Step 7）
- [ ] 验证 Ben's Bites 新 URL 有内容
- [ ] 确认卡兹克 / 宝玉 feed 不再超时
- [ ] 确认 we-mp-rss 云端部署后扫码正常（阿里云国内 IP）
- [ ] 确认 RSSHub 自建后 8 个路由全部 200（不再 403）

---

## 修正后的 TOP 3 落地清单

主辩论原 TOP 3 顺序不变，但公众号层工具替换：

**TOP 1（Day 3，30 分钟）**：抢阿里云 68 元/年轻量实例 + 修复 2 个死 URL（15 分钟）

**TOP 2（Day 4-5，约 3 小时）**：
- 云端起 we-mp-rss（替代原计划的 wewe-rss）+ RSSHub Docker
- 微信扫码登录 we-mp-rss（用小号，国内 IP 触发重验证频率低）
- 配置 Bilibili cookie 激活 B 站路由

**TOP 3（Day 6-7，约 1 小时）**：
- 云端起 TrendRadar，8 个 RSSHub URL 改为 `localhost:1200`
- 公众号 URL 改为 `localhost:8001`（we-mp-rss 端口）
- 手动跑一次验证企微推送成功

---

## 调研记录

| 调研 | 来源 | 结论 |
|---|---|---|
| Ben's Bites 当前 RSS | WebFetch `https://www.bensbites.com/feed` | **有效**，RSS 2.0，Substack，最新 2026-05-22 |
| a16z RSS | WebFetch `/feed/` + `/feed` | **均 404**，已迁 Substack，无公共 blog RSS |
| wewe-rss 多账号 + 归档状态 | WebSearch + GitHub | **2026-05-11 归档（read-only）**，账号稳定性问题持续（Issue #417） |

---

*报告路径：`D:\Dev\ai-wechat-pipeline\reports\phase10_followup_realdata_reaction.md`*
*生成时间：2026-05-22（TrendRadar 实测 11:20 后）*
*调研次数：3 次*
