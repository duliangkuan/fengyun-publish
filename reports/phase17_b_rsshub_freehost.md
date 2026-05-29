# Phase 17-B: RSSHub 自建免费托管平台横向对比

**日期**: 2026-05-25
**背景**: TrendRadar 当前依赖 rsshub.app 公共实例跑 8 个 feed,该实例为脆弱依赖。本报告评估各免费平台自建 RSSHub 的可行性。
**已排除**: Cloudflare Containers(见 phase10 报告,IP 漂移 + 临时磁盘已结论 N)。

## 1. 候选平台对比表

| 平台 | 免费额度 | Docker 支持 | Node.js 运行时 | 内存/CPU 上限 | 冷启动 | 国内可达 | RSSHub 实际案例 | 适合本项目? |
|---|---|---|---|---|---|---|---|---|
| Cloudflare Workers | Free: 100K req/天,CPU 10ms/req | 否(Workers 模式) | Workers Runtime(非标准 Node) | 128MB / 10ms CPU | 无(边缘常驻) | 是 | 官方 2026-01-04 合并,但必须 Paid Plan($5/月) | N(非免费) |
| Vercel Hobby | 免费,100GB 带宽/月 | 否 | Node.js,函数超时 10 秒 | 1024MB / 10s | 有 | 部分(vercel.app 被 DNS 污染,需绑自定义域) | 大量中文博客案例 | 有条件可用 |
| Render | 免费层实质消失($7/月起) | 是 | Node.js/Docker | 512MB / 0.1CPU | 15min 无请求休眠,冷启 30-60s | 是 | 少量英文案例 | N |
| Fly.io | 无持久免费层(2024 年移除),仅 7 天试用 | 是 | Docker | 256MB 共享 CPU | 有 | 是 | 有 FreshRSS on Fly.io 可参考 | N |
| Railway | 仅 30 天 $5 试用,之后最低 $5/月 | 是 | Docker/Node.js | 512MB / 1vCPU | 无(常驻) | 是 | 官方多个一键模板(含 Redis 完整版) | 有条件可用(非免费) |
| Deno Deploy | 免费,1000 req/分钟 | 否(Deno 运行时) | Deno(非 Node) | 512MB | 无 | 是 | 无 RSSHub 官方适配 | N(运行时不兼容) |
| Netlify Functions | 免费,125K req/月,10s timeout | 否 | Node.js | 1024MB / 10s | 有 | 是 | 无完整部署案例 | N(超时风险) |
| GitHub Codespaces | 60 小时/月免费 | 是 | 任意 | 2vCPU / 4GB | 每次手动启动 | 是(需端口转发) | 适合开发调试 | N(非持久) |
| Hugging Face Spaces | CPU-basic 完全免费(48h 无访问后休眠) | 是(Docker Space) | 任意(Docker 内) | 2vCPU / 16GB | 有(休眠唤醒) | 是 | 4 个真实案例 | 推荐(免费最优解) |
| Zeabur | Free Plan $5/月免费额度,有休眠 | 是 | Docker/Node.js | 1vCPU / 2GB | 有(冷启动几秒) | 是(中文友好) | 官方 Marketplace 模板 + 中文文档 | 推荐 |
| 阿里云函数计算 | 100 万次调用/月 + 400K GB·s 免费 | 是(FC 容器镜像) | Node.js/Docker | 128MB-3GB | 有(1-3s) | 是(国内最稳) | CSDN 博客案例,配置复杂 | 备选(国内访问) |

## 2. Top 3 推荐 + 部署要点

### 推荐 A: Hugging Face Spaces(Docker Space) — 免费首选

HF Spaces CPU-basic 完全免费,2 vCPU / 16GB RAM,Docker 原生。

**部署 Dockerfile 最小模板**:
```dockerfile
FROM diygod/rsshub:latest
ENV PORT=7860
EXPOSE 7860
```
注意: HF Spaces 强制要求应用监听 7860 端口。

**步骤**:
1. huggingface.co → New Space → SDK 选 Docker
2. 在 Files 里上传 Dockerfile
3. Space Settings → Variables 注入 cookie 环境变量
4. 用 cron-job.org 每 24 小时 ping 一次 Space URL 防休眠

**参考 Dockerfile**: https://huggingface.co/spaces/Orion-zhen/rsshub/blob/main/Dockerfile

### 推荐 B: Zeabur(中文一键模板)

**步骤**:
1. 注册 Zeabur → 新建 Project → 添加服务 → Service Marketplace → 搜索 RSSHub
2. 一键部署模板: https://zeabur.com/templates/X46PTP
3. Variables 面板注入 cookie 环境变量
4. Domains 块绑定自定义域名(或使用 `.zeabur.app` 二级域名)

Free Plan $5/月额度,低流量 RSSHub 实例月消耗约 $1-2,够用。

**官方中文文档**: https://zeabur.com/docs/zh-TW/marketplace/rsshub

### 推荐 C: Vercel Hobby(轻量路由适用)

**步骤**:
1. Fork `DIYgod/RSSHub` 到自己的 GitHub
2. Vercel 导入 Repo 即可部署
3. 添加环境变量
4. 必须绑定自定义域名(`.vercel.app` 在国内 DNS 污染严重)
5. 遇到 ERR_REQUIRE_ESM 错误时加 `NODE_OPTIONS=--experimental-require-module`

**限制**: 函数 10 秒超时硬限,微博关键词路由有超时风险。

## 3. RSSHub 官方推荐部署方式

来源: docs.rsshub.app/deploy/ + commit 1131350b

| 方式 | 免费友好 | 说明 |
|---|---|---|
| Docker Compose | 否(需 VPS) | 官方最推荐,含 Redis 缓存 |
| Cloudflare Workers | 否(Paid Plan 必须) | 2026-01-04 官方合并,免费层包大小 3MB 不足 |
| Railway | 部分($5/月) | 官方维护一键模板,完整版含 Redis + Browserless |
| Vercel | 是(有限制) | 官方支持,无 Redis,函数 10s 超时 |

## 4. 真实部署案例

### HF Spaces 案例
- https://huggingface.co/spaces/Orion-zhen/rsshub — 含 Dockerfile
- https://huggingface.co/spaces/solitudeLin/rsshub
- https://huggingface.co/spaces/xmjer1/rsshub
- https://huggingface.co/spaces/sdniu/rsshub

### 中文社区坑记录
| 坑 | 平台 | 说明 |
|---|---|---|
| B站 Cookie 3-5 天过期 | 全平台 | 手动更新,无自动刷新方案(Issue #18019 未合并) |
| Vercel 函数 10s 超时 | Vercel | 微博关键词搜索最易触发 |
| vercel.app DNS 污染 | Vercel | 必须绑自定义域 |
| HF Spaces 端口必须 7860 | HF Spaces | 需 ENV PORT=7860 |
| HF Spaces 48h 休眠 | HF Spaces | 需 cron-job 保活 |
| CF Workers 3MB 包限制 | CF Workers | 免费层不够,必须 $5/月 |
| Fly.io 无持久免费层 | Fly.io | 2024 年移除 |

## 5. Cookie 注入方案(B站 / 微博)

所有平台统一用环境变量注入:

```
# B站(每个 UID 一个变量)
BILIBILI_COOKIE_2267573=SESSDATA=xxx; bili_jct=xxx; DedeUserID=xxx; ...

# 微博
WEIBO_COOKIE=SUB=xxx; SUBP=xxx; ...

# 微博图片防盗链(必须配置,否则图片在 RSS 阅读器不显示)
HOTLINK_TEMPLATE=https://image.baidu.com/search/down?url=${href_ue}
HOTLINK_INCLUDE_PATHS=/weibo
```

B站 Cookie 获取: 登录后打开 `https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?uid=0&type=8`,DevTools Network 面板抓 Cookie Header。

## 6. 决策建议

本项目(8 个 feed: B站 6 UP + 微博 + 知乎)推荐 **Hugging Face Spaces**:
- 完全免费
- 4 个真实案例验证可用
- Docker 原生,16GB 内存充裕
- 环境变量注入方便
- Cookie 到期后只需更新 Variables → Restart,不用重新部署

---
*来源: RSSHub GitHub commit 1131350b / Railway 官方模板 / HF Spaces 公开案例 / Zeabur 官方文档 / 中文技术博客 / 各平台 pricing 页*
