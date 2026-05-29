# Phase 18: 10 个失败 feed 真实状态诊断

**日期**: 2026-05-26
**方法**: 本机 IP + 浏览器 UA curl(跟 TrendRadar 同环境)
**注**: 等 TrendRadar 后台跑完再补「修复 timeout 后的 TrendRadar 实际抓取结果」

## 1. 10 个 URL curl 实测结果

| feed_id | HTTP | size | redirect | 真实状态 | 推荐操作 |
|---|---:|---:|---|---|---|
| algorithmic-bridge | 200 | 722 KB | — | **A · alive** | 保留;TrendRadar 重跑后看 |
| arxiv-cs-lg | 200 | 1.6 MB | → https(原 http) | **A · alive** | 改成 https URL;timeout 60s 应该够 |
| deepmind-blog | 200 | 82 KB | — | **A · alive** | 保留;TrendRadar 重跑后看 |
| **geekpark** | **502** | 0 | — | **D · 服务端 502** | **删除**或观察一周后删 |
| google-research-blog | 200 | 78 KB | — | **A · alive** | 保留 |
| hacker-news | 200 | 13 KB | — | **A · alive** | 保留 |
| **jiqizhixin** | 200 | 6.8 KB | → `/data-service`(URL 失效) | **B · 重定向到非 RSS** | **删除**(原 rss 路径已废) |
| **langchain-blog** | 200 | 202 KB | → `langchain.com/blog`(非 RSS) | **B · 重定向到非 RSS** | **改 URL 或删** |
| r-localllama | 200 | 70 KB | — | **A · alive** | 保留 |
| smol-ainews | 200 | 1.9 MB | — | **A · alive(Karpathy 钦点)** | **保留必救**;timeout 60s 应该够 |

## 2. 分类汇总

| 类别 | 数 | feed_ids |
|---|---:|---|
| A · alive(TrendRadar 没抓到是其他原因) | 7 | algorithmic-bridge / arxiv-cs-lg / deepmind-blog / google-research-blog / hacker-news / r-localllama / smol-ainews |
| B · URL 失效(重定向走非 RSS) | 2 | jiqizhixin / langchain-blog |
| D · 服务端死 | 1 | geekpark(502) |

## 3. 推测 A 类失败原因

7 个 alive 但 TrendRadar 抓不到,候选根因:

| 原因 | 可能性 |
|---|---|
| timeout 30s 太短(smol.ai 1.9MB / arxiv-cs-lg 1.6MB) | **本次 60s 修复后大概率会解决 2 个** |
| TrendRadar feedparser 解析失败(非标准 RSS 格式) | 中(arXiv RSS 是 1.0 老格式,有些 parser 不兼容) |
| TLS / SSL 协议版本不匹配 | 低 |
| Cloudflare anti-bot(在 curl 层面没拦,fetcher.py 层面拦) | 中(deepmind / google-research / langchain 都走 Cloudflare) |
| HTTP/2 vs HTTP/1.1 协议问题 | 低 |
| 域名 DNS 临时解析失败 | 临时,重跑可见 |

## 4. 待修复 config 改动建议

### 4.1 立即改(确认死的 / URL 已变)

```yaml
# 1. 删 geekpark(服务端 502,死)
# 原:
- id: "geekpark"
  name: "[T3] 极客公园"
  url: "http://www.geekpark.net/rss"
# 改:删整段,或注释

# 2. 删 jiqizhixin 网页版(URL 重定向走 /data-service 非 RSS)
# 原:
- id: "jiqizhixin"
  name: "[T3] 机器之心"
  url: "https://www.jiqizhixin.com/rss"
# 改:删(已有 wechat-jiqizhixin 公众号版兜底,功能不缺失)

# 3. langchain-blog: 改用 GitHub mirror(如有)或 Substack
# 原:
- id: "langchain-blog"
  name: "LangChain Blog"
  url: "https://blog.langchain.dev/rss/"
# 改:待找替代 URL(LangChain 已迁 Substack?), 暂注释

# 4. arxiv-cs-lg: http → https
url: "https://export.arxiv.org/rss/cs.LG"   # 加 s
```

### 4.2 等 TrendRadar 重跑结果后再决定

A 类 7 个 feed,如果 timeout 60s 修复后:
- **变 alive** → 留着不用动
- **仍 0 数据** → 需要进一步排查 TrendRadar parser / Cloudflare 反爬

## 5. 后续 action 等 TrendRadar 跑完

跑完后:
1. 重新 inspect_feed_health,看 7 个 A 类有几个真活了
2. 仍挂的去看 TrendRadar 自己的日志(fetcher.py 抛了什么异常)
3. 更新本报告

---

*报告作者: 主对话 Claude(sub-agent 撞 WebFetch 权限拒,接手 curl)*
*关联 task: #13*
*关联 memory: [[ai-wechat-information-intake]] [[feedback_no_speculation]]*
