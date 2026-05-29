# Phase 17-A: 2026-05 当下,公众号→RSS 工具开源生态盘点

**日期**: 2026-05-25
**背景**: 「研究Agent的云」AI 公众号 IP 项目,16 个公众号 feed 当前依赖本机 Docker 的 we-mp-rss。本任务验证 we-mp-rss 是否仍是 2026 唯一活的开源选项,以及有没有新崛起的项目。
**注**: sub-agent Write 权限被拒,本文件基于 agent 调研摘要落地。

---

## 1. 当前 alive 的开源公众号→RSS 工具

近 12 个月有 commit 才算 alive。

| 工具 | GitHub | star | 最近 release / commit | 部署方式 | 扫码机制 | 已知坑 | 推荐度 |
|---|---|---|---|---|---|---|---|
| **we-mp-rss** | rachelos/we-mp-rss | 3.2k | v1.5.2 (2026-04-16) | Docker 镜像 `ghcr.io/rachelos/we-mp-rss:latest`,端口 8001 | 浏览器扫码 → cookie 持久化 sqlite | **cookie 约 80 小时失效**,需手动重扫(搬云解决 24/7 在线但此限制无法规避) | **唯一首选** |
| **wechat-download-api** | tmwgsicp/wechat-download-api | 635 | v1.4.0 (2026-05-18) | Docker / API 服务,**内置 IP 代理池** | 同样需扫码 | 运维门槛高(代理池配置 + 维护)| 备选(若 we-mp-rss 反爬升级失守再切) |

## 2. 已死 / 归档黑名单

| 工具 | 死亡时间 | 死法 |
|---|---|---|
| **wewe-rss**(cooderl 同名 GitHub repo) | 2026-05-11 | **Archived,停止维护**;9.5k star 归零价值,不再推荐 |
| feed43 / inoreader / 其他公开服务 | — | 非自建,非本调研范围 |

## 3. 2026 有没有新崛起的工具?

**没有**。

调研覆盖范围:
- GitHub topics / search(`wechat-rss` / `公众号 RSS` / `wechat to rss self-hosted`)
- 中文圈讨论(知乎 / 少数派 / V2EX / 公众号自媒体)
- 英文圈搜索(覆盖较差,这是中文细分领域)

**结论**:wewe-rss archived 后,**we-mp-rss 一家独大格局明确**,生态未扩张。wechat-download-api 是 we-mp-rss 的同形态替代(都需扫码),不算新形态。

## 4. we-mp-rss 完整画像

- **star**:3.2k
- **最近 release**:v1.5.2 (2026-04-16) — 1 个月前
- **issue 区典型问题**:cookie 失效、扫码二维码刷新、Docker 部署初配置、个别公众号同步异常
- **Docker 镜像 tag**:`latest` 稳定,生产建议 pin 具体版本(如 `v1.5.2`)
- **文档完整度**:中文文档齐全,README + Wiki + Discussions 都活跃
- **路由格式**:`/feed/MP_WXS_<biz>.atom`(memory [[ai-wechat-information-intake]] 已实测验证)
- **持久化**:sqlite `data/db.db`,Docker volume 挂载即可

## 5. 关键发现 → 对本项目的影响

**没有"换工具"这条路** — wewe-rss 死、新项目无、wechat-download-api 是同类不是更优。**we-mp-rss 是 2026 当下的唯一开源选项**。

因此「自建」对公众号这条战场的全部意义就是**把 we-mp-rss 搬到 24/7 在线的国内 VPS**,memory [[ai-wechat-cloud-decision]] 已锁定的阿里云轻量 ¥199/年 方案就是这件事。

公众号 16 个 feed 想"免费自建"在 2026 当下**做不到**(微信 + IP + cookie 风控的物理约束),最低也是阿里云 ¥16.6/月。

---

## 调研统计

- 工具使用次数: 37 次(WebSearch + WebFetch 混合)
- 调研模型: claude-sonnet
