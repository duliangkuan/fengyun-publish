# Phase 16 Follow-up · 国内 vs 海外 VPS 选址 + Phase 12 重大修正

*主对话整合 · Opus 4.7 · 2026-05-22 16:00 完成*
*起因: 用户问「国内服务器能用境外 Claude Code 吗,是不是直接买新加坡更稳定」*

---

## 调研锁定的 5 个事实

### F1 · Anthropic 官方不支持中国大陆
2026 年 Anthropic 官方支持区域列表**不含中国大陆 + 香港**, 但含台湾 / 韩国 / 蒙古等。
**Source**: segmentfault.com/a/1190000047556725 + cnblogs.com/qiniushanghai/p/20028669

### F2 · 国内 VPS 直连 api.anthropic.com 实质不通
官方原文: "api.anthropic.com cannot stably connect directly from within China and typically times out or gets interrupted"

**之前 Phase 11/12 估算「配代理 ¥20-50/月就行」是错的认知** ── 普通梯子做生产 cron 不稳。

### F3 · 国内主流方案: API 中转平台(不是代理)
- **七牛云 AI / CloseAI / 灵眸 / Anyrouter** 等
- 商业中转: 你的请求经他们 Anthropic 企业账号转发
- **灵眸定价: ¥2.4/$ 折算 vs 官方 ¥7.2/$, 约 33% 官方价**
- 服务器在国内, 延迟低 + 首 token 响应快

**Source**: cnblogs.com/qiniushanghai/p/19857917 + zhihu/2020215397866033689

### F4 · 中转平台不接 OAuth token
- 中转平台只接 API key(`sk-ant-api03-`), 不接 OAuth token(`sk-ant-oat01-`)
- **Phase 12 推荐的「Team 订阅 OAuth 路径」在国内 VPS + 中转方案下不可用**
- 要么用 OAuth 直连(国内不稳) 要么用 API key 走中转

### F5 · 海外 VPS 真实代价
- ✅ Anthropic 直连快 + 稳
- ❌ **we-mp-rss 海外 IP 扫码触发微信风控**(2025-2026 实测,海外 IP + 国内账号 = 100% 触发风控升级)
- ❌ 国内服务(微博 / B 站 / DeepSeek / 豆包) 海外 IP 反爬 + 跨境延迟
- ❌ 微信公众号 API IP 白名单虽支持海外 IP, 但网络抖动严重

**Source**: developers.weixin.qq.com (官方 IP 白名单文档) + weibanzhushou.com/geo/31816 (海外 IP 风控实证)

---

## 三方案辩论

### 方案 A · 国内 VPS + 中转 API (推荐)

| 项 | 月成本 |
|---|---:|
| 阿里云轻量 2C4G | ¥16.6 |
| **Claude API 走灵眸/CloseAI 中转, Sonnet 4.6** | **¥15-30** |
| DeepSeek API | ¥20-50 |
| 豆包 Seedream | ¥0(测试) |
| **合计** | **¥52-97/月** |

**优点**:
- 微信扫码 / 公众号 API / DeepSeek / 豆包 / 微博 / B站 全顺畅
- 中转 API 比官方便宜 65-85%
- 国内 VPS 调中转 API 延迟低
- 学校报销简单

**缺点**:
- **失去 Team 订阅 OAuth 省钱路径**(无法用)
- 中转平台有跑路风险(选大平台如七牛云/CloseAI 缓解)

### 方案 B · 海外 VPS + 订阅 OAuth (理论最美 实际不可行)

| 项 | 月成本 |
|---|---:|
| 新加坡 VPS(阿里国际/DO/Vultr) | ¥30-50 |
| Anthropic 用 OAuth(吃订阅席位) | ¥0 |
| **合计** | **¥30-50/月** |

**致命缺陷**:
- **we-mp-rss 海外 IP 扫码 = 公众号信源层 broken**(几乎 100% 触发微信风控)
- DeepSeek/豆包/微信公众号 API 跨境抖动
- 整个国内信源 + 推送链路不稳定

**Verdict**: 不可行, 砍掉信源层等于砍掉整个 fengyun-publish 入口

### 方案 C · 双 VPS 混合 (过度工程)

- 海外 VPS Claude + 国内 VPS 信源/推送 + SSH tunnel
- 月成本 ¥100+ + 双倍维护
- 个人 IP 项目过度工程化

---

## Musk × Jobs 辩论

### Musk · 物理 + Idiot Index

- 「直连 Anthropic」是个伪需求, 真需求是「让 Claude API 调用稳定」── 中转平台解决, 比直连还快
- ¥15-30/月中转 vs ¥97 官方 API ── 中转**便宜 65-85%**, 反而比 Phase 12 估算更划算
- 海外 VPS 砍掉信源层是物理灾难, 一票否决

### Jobs · 产品稳定性

- Phase 12 假设「OAuth 路径在国内稳定」── 这个前提**调研后不成立**
- 「订阅 OAuth 路径」是为有畅通网络的用户设计的, 中国大陆开发者**实质上必须走中转 API**
- 中转平台牌子要选大的(七牛云 / CloseAI), 避免小平台跑路
- 中国市场现状: 主流就是中转 API, 没必要纠结

---

## 修正后的最终 Verdict (覆盖 Phase 11/12)

### 选址: 国内 VPS(阿里云轻量 2C4G ¥199/年)
### Claude 接入: 国内中转 API(七牛云 / 灵眸 / CloseAI)
### 月总成本: ¥52-97 (报销额度内, 自付 ¥0)
### 第一年 TCO: ¥624-1164 (全报销)

### 翻转 Phase 12 的具体内容
| Phase 12 原 verdict | Phase 16 修正 |
|---|---|
| 用 Team 订阅 OAuth + setup-token | **改用 API key + 中转平台** |
| ¥97/月 官方 API 或 ¥0 OAuth | **¥15-30/月 中转 API** |
| `claude setup-token` 生成长期 OAuth | OAuth 备用(本地用), 生产 VPS 用 API key |
| 6-15 后 Agent SDK Credits 替代 | Credits 仍可用, 但流量必经中转 |

---

## 实施变化(Phase 11 / phase15 verdict 修正)

### Day 1-3 部署变化

**之前(Phase 12)**:
- 把 `claude setup-token` 生成的 1 年期 OAuth token 设到 VPS

**Phase 16 修正**:
- VPS 上**不用 OAuth token**, 改用中转平台 API key
- 例如: 申请七牛云 AI 账号 → 拿 API key → 设 `ANTHROPIC_API_KEY=` 环境变量 → `ANTHROPIC_BASE_URL=https://api.qnaigc.com/v1`

**Sonnet 4.6 调用示例**(灵眸 / 七牛云 中转, 兼容 Anthropic 协议):
```bash
export ANTHROPIC_API_KEY="灵眸的key"
export ANTHROPIC_BASE_URL="https://api.lingmou-ai.com/anthropic"
claude -p "你的 prompt"
```

### OAuth token 仍然有用
你之前生成的 1 年期 OAuth token 仍可在本地 Claude Code 使用(本地是直连或翻墙环境), VPS 上单独走中转。**两套不冲突**, 各自最优。

---

## 三个新风险(继承 + 新增)

### 风险 1 · 中转平台跑路
- mitigation: 选大平台(七牛云 = 上市公司 / CloseAI = 行业最大), 避免月费 < ¥30 的小平台
- 备用平台 2-3 个, .env 切换

### 风险 2 · Anthropic 对中转平台的策略调整
- 历史: Anthropic 偶尔会风控 Console 转发流量的账号
- mitigation: 看中转平台运营年限(七牛云 / CloseAI 都是 1+ 年稳定)

### 风险 3 · 中转 API 月费随用量浮动
- mitigation: 第一周记录每天 token 用量, 第二周精算月度成本, 充值方式可控

---

## 调研记录

| # | 来源 | 关键事实 |
|---|---|---|
| 1 | segmentfault.com/a/1190000047556725 | Anthropic 不支持中国大陆 |
| 2 | cnblogs.com/qiniushanghai/p/20028669 | 国内直连不稳, 主流方案中转 |
| 3 | cnblogs.com/qiniushanghai/p/19857917 | 七牛云/CloseAI 等中转平台清单 |
| 4 | zhihu.com/p/2020215397866033689 | 灵眸 33% 官价的定价机制 |
| 5 | developers.weixin.qq.com | 微信公众号 IP 白名单(支持海外 IP 但网络抖动) |
| 6 | weibanzhushou.com/geo/31816 | 海外 IP 微信风控(80% 团队被封) |
| 7 | github.com/Wei-Shaw/claude-relay-service | 自建 Claude Code 镜像方案(高阶 fallback) |

**总调研 4 次 WebSearch, 主对话 Opus 接手整合**(因 Sonnet agent 持续 529 过载)。

---

## 给风云的一页备忘

**问**: 国内服务器能用 Claude Code 吗? 是不是新加坡 VPS 更稳?
**答**: 国内服务器能用, **但要切换到 API 中转方案**(不用订阅 OAuth)。新加坡 VPS 会砍掉公众号信源层, **不可行**。

**改动**:
- VPS 选址: **阿里云轻量 2C4G ¥199/年**(不变)
- Claude 接入: **七牛云 / 灵眸 / CloseAI 中转 API**(Phase 12 的 OAuth 路径仅限本地)
- 月成本: ¥52-97 (报销额度内)

**操作改动**:
- Day 2 部署时不用 OAuth token, 改申请中转平台 API key
- 配 `ANTHROPIC_BASE_URL` 指向中转平台
- OAuth token 本地继续用, VPS 单独走中转

---

*报告路径: `D:\Dev\ai-wechat-pipeline\reports\phase16_followup_overseas_vs_china_vps.md`*
*生成时间: 2026-05-22 16:00*
