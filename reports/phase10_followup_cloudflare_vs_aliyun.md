# Phase 10 Follow-up — Cloudflare vs 阿里云客观对比
*Musk × Jobs 轻量反应 · sonnet · 2026-05-22*

---

## 背景继承

已锁定的 Verdict（不重做）：
- 上云 Y / 自建 RSSHub Y / 净增成本 ~5.7 元/月
- 主辩论推荐：阿里云轻量 2C2G，68 元/年活动价
- 第一轮 follow-up 修正：云端公众号层用 we-mp-rss（wewe-rss 已归档）

用户问题：「Cloudflare 比起阿里云来怎么样，是不是更好」

---

## 调研记录（3 次 WebFetch + 3 次 WebSearch）

| 调研 | 来源 | 关键发现 |
|------|------|---------|
| CF Workers 定价 | developers.cloudflare.com/workers/platform/pricing/ | 免费 10ms CPU/请求；付费 $5/月起，CPU 5 分钟/次 |
| CF Workers 限制 | developers.cloudflare.com/workers/platform/limits/ | 内存 128MB/isolate；无原生文件系统；无 Docker |
| CF Containers GA | developers.cloudflare.com/containers/ + /containers/pricing/ | **2026-04-13 正式 GA**；支持 Docker 镜像；需 Workers Paid $5/月；包含 375 vCPU-分钟/月 |
| CF Containers 限制 | developers.cloudflare.com/containers/platform-details/limits/ | 实例最大 12GiB RAM、20GB 磁盘、4 vCPU；但磁盘是**临时存储**，容器重启后清零 |
| CF Docker + Workers | WebSearch | Containers GA 后确认可跑 Docker 镜像，但 egress IP 来自 CF 全球边缘节点，**不固定** |
| CF Containers 持久化 | WebSearch | 「container instances use ephemeral storage」——持久化依赖外部 D1/R2/KV，不是本地文件系统 |

---

## 核心约束核实（截至 2026-05-22）

### Cloudflare Workers（纯 serverless 函数）

| 约束 | 数值 |
|------|------|
| 内存 | 128MB/isolate |
| CPU | 10ms（免费）/ 5 分钟（付费） |
| 文件系统 | **无**，只有 KV/D1/R2 |
| Docker 支持 | **否**（Workers 本身不支持） |
| 持久化 session | **否**，无法跑有状态服务 |
| 出口 IP | 全球边缘随机，**不固定** |

**结论**：Workers 无法跑 we-mp-rss / RSSHub / TrendRadar 中的任何一个。

---

### Cloudflare Containers（2026-04 GA，新产品）

| 约束 | 数值 |
|------|------|
| 支持 Docker | **是**，支持标准 Docker 镜像 |
| 内存上限 | 12 GiB/实例（最大） |
| 磁盘 | 20 GB/实例，但**临时存储**（重启清零） |
| CPU | 1-4 vCPU/实例 |
| 持久化文件系统 | **否**，需接 D1/R2/KV |
| sqlite 文件持久化 | **否**（sqlite 文件放本地磁盘 = 重启清零） |
| 出口 IP | 来自 CF 全球边缘节点，**不固定**（除非购买专属出口 IP，企业版） |
| 最低月费 | $5/月（Workers Paid 计划基础费） |
| 包含额度 | 375 vCPU-分钟/月 / 25 GiB-小时内存 / 200 GB-小时磁盘 |
| 超额计费 | CPU $0.000020/vCPU-秒，内存 $0.0000025/GiB-秒 |

**结论**：Containers 能跑 Docker，但两个硬约束卡死这个项目：

1. **磁盘临时化**：we-mp-rss 和 RSSHub 的 sqlite 数据库、微信扫码 session 存在本地文件系统，容器重启即清零——等于每次重启都要重新扫码、重新建库。
2. **出口 IP 不固定**：微信系统对异地 IP 敏感（主辩论已验证），CF 边缘节点每次可能来自不同城市/国家，触发微信安全验证的概率极高。

---

## Musk 视角（物理约束，≤ 200 字）

**Docker 能跑，但存储模型根本不匹配。**

Cloudflare Containers 能跑 Docker 镜像，这个信息在 2026-04-13 GA 后确实是真的。但把它用在这个项目上有两个物理死角：第一，容器磁盘是临时存储，重启即清——we-mp-rss 的 sqlite 和微信 session 文件不能住在临时磁盘里，否则每次冷启动都要重新扫码建库，这是自动化系统的灾难；第二，出口 IP 随全球边缘节点分配，不固定，这套系统的微信扫码层对 IP 稳定性有强依赖。

解决这两个问题需要：持久化用 D1/R2 改写 we-mp-rss 代码，加固定 IP 需要企业版专属 egress IP。两个改造都不是配置问题，是代码重写。Idiot Index：改写成本 >> 阿里云 68 元/年。**不选 Cloudflare 作主力 VPS 替代。**

---

## Jobs 视角（产品稳定性，≤ 200 字）

**边缘 IP 漂移是微信扫码的天敌。**

we-mp-rss 的核心风险是：微信检测到登录 IP 与使用 IP 不一致，触发重验证强制重新扫码。第一轮 follow-up 已验证「国内阿里云 IP 触发频率相对低」。Cloudflare Containers 的出口 IP 来自全球边缘节点，可能今天从北京 PoP 出，明天从新加坡 PoP 出——对微信来说这是持续的「异地登录」信号。

微信扫码不是一次性操作，是维持 session 的持续契约。IP 漂移打断这个契约。一个每天要稳定推送企微日报的系统，不能建在一个「IP 今天北京明天新加坡」的基础上。从产品稳定性角度，这个方案在 24/7 生产环境里会持续产生人工干预摩擦，不可接受。

---

## Q5 Verdict：Cloudflare 替代阿里云可行性

**Verdict：N（不替代）+ 有限辅助价值**

### 为什么是 N

| 问题 | Cloudflare Containers 表现 | 阿里云轻量表现 |
|------|---------------------------|--------------|
| Docker 支持 | ✅ 支持 | ✅ 支持 |
| sqlite 持久化 | ❌ 磁盘临时，重启清零 | ✅ 持久化本地磁盘 |
| 微信 session 文件持久化 | ❌ 同上 | ✅ 正常 |
| 出口 IP 稳定（微信扫码） | ❌ 全球边缘随机，不固定 | ✅ 固定国内 IP |
| 国内 IP（微信 API 友好） | ❌ 边缘节点含境外 | ✅ 国内节点 |
| 月度成本 | $5/月起（≈ 36 元），不含超量 | ~5.7 元/月（68 元/年活动） |
| 运维复杂度 | 高（需改写持久化层 + 处理 IP 漂移） | 低（标准 Docker Compose） |

### Cloudflare 在这个项目里有什么辅助价值

**有两个场景值得考虑**（不替代 VPS，作为辅助层）：

**场景 A：Cloudflare Tunnel（零成本，推荐）**
- 如果本地 we-mp-rss 保留作 fallback，可以用 Cloudflare Tunnel 把本地服务暴露为公网 HTTPS 端点
- 免费，不需要公网 IP，穿透到本地 MateBook 14
- 适合临时调试 / 备用通道，不适合 24/7 生产主力

**场景 B：Cloudflare CDN/DNS（可选）**
- 如果日报系统未来有网页版（静态报告展示），CF CDN 加速静态资源是标准操作
- 对当前纯企微推送的架构无价值

**场景 C：Cloudflare Workers 做轻量 webhook 中继（可选）**
- 企微 webhook 签名验证如果需要中间层处理，可以用 Workers 做轻量代理
- 但当前架构不需要，TrendRadar 直接打企微 webhook

### 混合方案（Month 2 可选，不影响 Day 3 决策）

```
主力 VPS（阿里云 2C2G，68 元/年）
  ├── TrendRadar（Python cron）
  ├── we-mp-rss（Docker，sqlite + session 持久化）
  ├── RSSHub（Docker，B站/微博 cookie 持久化）
  └── 企微 webhook 推送

辅助层（Cloudflare，可选，免费）
  ├── CF Tunnel → 本地 MateBook fallback 通道（按需）
  └── CF Workers → 未来静态报告页 CDN（Month 3+）
```

---

## 月度成本对比（客观数字）

| 方案 | 月费 | 年费 | 适合这个项目 |
|------|------|------|------------|
| 阿里云轻量 2C2G（活动价） | ~5.7 元 | **68 元** | ✅ 推荐 |
| 阿里云轻量 2C2G（常规年付） | ~14 元 | ~168 元 | ✅ 备选（抢不到活动价） |
| Cloudflare Containers（最低） | ~36 元（$5）起 | ~432 元 | ❌ 贵 6 倍 + 持久化/IP 硬约束 |
| Cloudflare Workers（免费额度） | 0 元 | 0 元 | ❌ 不支持 Docker/文件系统 |
| Cloudflare Tunnel（辅助） | **0 元** | **0 元** | ✅ 可作辅助，不作主力 |

---

## 综合结论

**Cloudflare ≠ VPS 替代品，在这个项目里是辅助工具，不是主力。**

- Cloudflare Workers：无法跑 Docker，无文件系统，直接排除。
- Cloudflare Containers（2026-04 GA）：能跑 Docker，但临时磁盘 + IP 不固定，卡死 sqlite 持久化和微信扫码两个核心需求。
- 价格也不占优：Containers 最低 $5/月（≈ 36 元），是阿里云活动价的 6 倍。
- 唯一免费价值：Cloudflare Tunnel 可作本地 fallback 穿透，不影响 Day 3 上阿里云的决策。

**Day 3 决策不变：抢阿里云 68 元/年，不用 Cloudflare 替代。**

---

## 调研统计

| 调研次数 | 方式 | 主题 |
|----------|------|------|
| 3 次 WebFetch | 官方文档 | CF Workers 定价/限制 + CF Containers 文档 + Containers 定价页 |
| 3 次 WebSearch | 全网 | CF Docker 支持现状 + we-mp-rss CF 部署案例 + CF Containers 持久化+IP |
| 1 次 WebFetch（失败） | 社区论坛 | CF 固定 egress IP 社区讨论（403 返回，改由搜索结果推断） |

---

*报告路径：`D:\Dev\ai-wechat-pipeline\reports\phase10_followup_cloudflare_vs_aliyun.md`*
*生成时间：2026-05-22*
*调研次数：6 次有效（3 WebFetch + 3 WebSearch）*
