# 自建 Email-to-RSS 到 Cloudflare Workers — 免费部署指南

**目的**:解锁 Substack 上的 newsletter(像 a16z / Stratechery 免费版 / The Batch / Last Week in AI 等),把这些只通过邮件发送的内容**自动转成 RSS** 接入 TrendRadar。

**为什么必须做**:
- a16z 等 newsletter 把内容迁到 Substack,公共 RSS 全部 404
- Kill the Newsletter 是免费方案但**被 Substack 域名过滤**,拿不到 Substack 类
- Email-to-RSS 用你自己的域名收邮件,**Substack 过滤不掉**

**为什么免费**:Cloudflare Workers 免费层每天 10 万请求 + KV 免费层 1GB 存储,够订几十个 newsletter 用。

**月成本**:**¥0**(你已有域名 + Cloudflare 账号)

**前置**:
- 域名已托管在 Cloudflare(你已有 ✓)
- 本机有 Node.js + npm + git(没装的话先装 LTS:nodejs.org)
- Cloudflare 账号(域名已在就有了)

---

## Step 1:克隆仓库 + Cloudflare 认证

```powershell
cd D:\GitHub
git clone https://github.com/yl8976/Email-to-RSS.git
cd Email-to-RSS
npx wrangler login
```

浏览器会自动打开,登录你的 Cloudflare 账号点 Allow。

---

## Step 2:跑 setup.sh

```powershell
bash setup.sh
```

> 如果 Windows 报 `bash 不识别`:用 Git Bash 或 WSL 跑,或者用 PowerShell 一行行手动跑(`npm install` + 创建 KV 等)。

`setup.sh` 自动做这几件事:
- 装 npm 依赖
- 验证 Cloudflare 认证
- 创建 KV 命名空间 `EMAIL_STORAGE`(存邮件内容)
- 让你设置一个 `ADMIN_PASSWORD`(后台登录用,**记住这个密码**)
- 从模板生成 `wrangler.toml` 配置文件

---

## Step 3:配 Cloudflare DNS(关键)

去 Cloudflare → 你的域名 → DNS → Records,加 4 条:

| 类型 | 名称 | 内容 | 优先级 |
|---|---|---|---|
| MX | @ | `mx1.forwardemail.net` | 10 |
| MX | @ | `mx2.forwardemail.net` | 10 |
| TXT | @ | `forward-email=https://你的域名.com/api/inbound` | — |
| TXT | @ | `v=spf1 include:spf.forwardemail.net -all` | — |

**注意第 3 条的 `你的域名.com` 换成你真实域名**(比如 `forward-email=https://abc.xyz/api/inbound`)。

这 4 条做的事:
- MX 告诉全世界「发到 @你的域名 的邮件丢给 ForwardEmail」
- 第 3 条 TXT 告诉 ForwardEmail「收到的邮件 POST 到 Workers 这个 URL」
- 第 4 条 TXT 是 SPF,防止你域名被当垃圾邮件

DNS 生效通常几分钟。

---

## Step 4:部署 Worker

```powershell
npm run deploy
```

Wrangler 会把代码发布到 Cloudflare Workers,完事会显示你的 Worker URL,大概长这样:
```
https://email-to-rss.<你的子域>.workers.dev
```

但你**实际用的是你自己域名** `https://你的域名.com` — 因为 DNS 已经把邮件路由过来了。

---

## Step 5:创建第一个 newsletter feed

1. 浏览器打开 `https://你的域名.com/admin`
2. 用 Step 2 设的 `ADMIN_PASSWORD` 登录
3. **Create new feed** → 给个名字(比如「a16z newsletter」)
4. 系统生成一个唯一邮箱地址,比如:`apple.mountain.42@你的域名.com`
5. **复制这个邮箱地址**

---

## Step 6:用这个邮箱订 newsletter

去你想订的 newsletter 网站(比如 a16z / Stratechery / The Batch 等),用 Step 5 拿到的邮箱**订阅**。

订阅确认邮件会发到你的 Worker → 自动解析 → 存 KV。

---

## Step 7:拿 RSS URL,接 TrendRadar

每个 feed 的 RSS URL 是:
```
https://你的域名.com/rss/<feedId>
```

`<feedId>` 在 admin 面板能看到。

把这个 URL 加到 `D:\Dev\TrendRadar\config\config.yaml`:

```yaml
    # ——— 📧 Email-to-RSS 自建,Substack 私有 newsletter ———
    - id: "email-rss-a16z"
      name: "[T2] a16z newsletter(via email)"
      url: "https://你的域名.com/rss/<feedId>"
      max_age_days: 7
```

---

## Step 8:推荐订哪些 newsletter(P0)

订阅前用 Email-to-RSS 各自生成独立邮箱(方便管理 / 删除):

| Newsletter | 订阅入口 | 价值 |
|---|---|---|
| **a16z** | a16z.com/newsletter | a16z 自从 RSS 404 后唯一通路 |
| **Stratechery 免费版**(Weekly Articles) | stratechery.com/free | Ben Thompson 战略分析,免费版每周一篇 |
| **The Batch** | deeplearning.ai/the-batch | Andrew Ng 周刊,memory 标过的「无公开 RSS」 |
| **Last Week in AI** | lastweekin.ai | 百万级订阅,每周精选 |
| **Import AI**(已有 RSS,可跳过) | jack-clark.net | Jack Clark Anthropic 联创 |
| **Ben's Bites**(已有 RSS,可跳过) | bensbites.com | — |

---

## 维护

| 事件 | 怎么处理 |
|---|---|
| Worker 异常 | Cloudflare dashboard → Workers → 你的 Worker → Logs 看错误 |
| KV 满了(到 1GB 限) | 删除老 feed / 升级 Workers Paid($5/月,够用一辈子) |
| 邮件没来 | Cloudflare → Email Routing 看 DNS 状态;确认 MX 记录生效 |
| Substack 退订 | admin 面板删除对应 feed,生成的邮箱地址同时失效 |

---

## 关联

- 调研报告:`D:\Dev\ai-wechat-pipeline\reports\phase17_d_hard_source_alternatives.md`
- 项目 README:https://github.com/yl8976/Email-to-RSS
- Cloudflare Workers 免费层文档:https://developers.cloudflare.com/workers/platform/pricing/
- ForwardEmail 文档:https://forwardemail.net/
- memory 关联:[[ai-wechat-information-intake]]
