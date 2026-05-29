# mp-proxy-worker

微信公众号文章反向代理 Cloudflare Worker。配合 [`wechat-article-exporter`](https://down.mptext.top) 的"私有代理列表"功能使用,绕开作者公共代理池的每日配额限制。

## 协议

来自 `BaseDownloader.ts:159`:

```
GET /?url=<urlencoded微信URL>&headers=<JSON>&authorization=<可选>
```

## 部署

```bash
# 1. 登录 Cloudflare (浏览器扫码)
npx wrangler login

# 2. 部署
npx wrangler deploy
```

部署后会得到 `https://mp-proxy-worker.<你的子域>.workers.dev`。

## 配置 exporter

去 [https://down.mptext.top](https://down.mptext.top) → 设置 → 私有代理列表 → 填入 Worker URL。

之后所有抓取走的都是你的 Worker,**不再受公共代理池配额限制**。

## 安全(可选)

默认 Worker 公开可用——如果你不想被陌生人滥用 Cloudflare 免费 quota,在 `wrangler.toml` 里取消 `SHARED_SECRET` 注释,然后在 exporter 偏好的"私有代理 authorization"里填同一串密钥。

## 配额

Cloudflare Workers 免费版:每天 10w 请求。一个人用绰绰有余。
