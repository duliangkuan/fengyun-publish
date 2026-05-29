# RSSHub Cookie 配置指南 — 救活 7 个 503 feed

**目的**:你本机 Docker 跑的 `rsshub`(`diygod/rsshub:chromium-bundled`,端口 1200)已经在跑,微博 feed 正常,但 **6 个 B 站 UP + 1 个知乎话题全 503**。原因:容器里**没注入登录 cookie**,RSSHub 进不了 B 站 / 知乎的「会员区」。

**为什么这是真问题**:
- 微博 keyword 不需要登录 → 直接拿到数据
- B 站用户视频列表 需要 cookie(2024 反爬升级后)
- 知乎话题 需要 cookie(z_c0)

**这次只解决一件事**:把你的 B 站 / 知乎 cookie 抓出来塞进容器,重启 → 7 个 feed 立刻活。

**月成本**:**¥0**(还是本机 Docker,什么都不变)

---

## Step 1 · 抓 B 站 cookie

1. 浏览器登录 https://www.bilibili.com (随便点开一个 UP 主主页都行)
2. F12 打开 DevTools → **Application** 标签 → 左侧 **Cookies** → `https://www.bilibili.com`
3. 复制下面 4 个字段的 **Value**,**用 `; ` 拼成一行**:
   - `SESSDATA`
   - `bili_jct`
   - `DedeUserID`
   - `DedeUserID__ckMd5`
4. 最终格式:
   ```
   SESSDATA=xxx; bili_jct=xxx; DedeUserID=xxx; DedeUserID__ckMd5=xxx
   ```

**注意**:`SESSDATA` 是关键字段,**不要漏**。

---

## Step 2 · 抓知乎 cookie

1. 浏览器登录 https://www.zhihu.com
2. F12 → Application → Cookies → `https://www.zhihu.com`
3. 复制 `z_c0` 字段的 **Value**(这是知乎主 token)
4. 最终格式:
   ```
   z_c0=2|1:0:0:10:abc...xyz
   ```

知乎相对宽松,**单 `z_c0` 一个字段就够**。

---

## Step 3 · 重启 RSSHub 容器(注入 cookie)

RSSHub 容器是无状态的,直接 stop + 重新 run 不会丢数据(它本来就不存数据)。

**先停掉旧容器**:
```powershell
docker stop rsshub
docker rm rsshub
```

**重新启动(把 Step 1 / 2 抓的 cookie 填进去)**:

```powershell
docker run -d `
  --name rsshub `
  --restart unless-stopped `
  -p 1200:1200 `
  -e TZ=Asia/Shanghai `
  -e "BILIBILI_COOKIE_1567748478=SESSDATA=xxx; bili_jct=xxx; DedeUserID=xxx; DedeUserID__ckMd5=xxx" `
  -e "BILIBILI_COOKIE_1900783=同上" `
  -e "BILIBILI_COOKIE_1741797=同上" `
  -e "BILIBILI_COOKIE_12566101=同上" `
  -e "BILIBILI_COOKIE_371846699=同上" `
  -e "BILIBILI_COOKIE_163637592=同上" `
  -e "ZHIHU_COOKIES=z_c0=2|1:0:0:10:abc...xyz" `
  diygod/rsshub:chromium-bundled
```

**说明**:
- 6 个 B 站环境变量对应 config.yaml 里 6 个 UP 主的 UID(李沐 1567748478 / 子豪 1900783 / 歸藏 1741797 / 秋葉 12566101 / 图灵的猫 371846699 / 何同学 163637592)
- **同一个 cookie 字符串可以用于 6 个 UID**(只要你登录账号,B 站允许这个 cookie 抓任意公开 UP 主),所以 6 行的 cookie 值是**完全一样**的
- ZHIHU_COOKIES 是 RSSHub 官方文档要求的变量名(注意是复数 `COOKIES`,不是 `COOKIE`)

---

## Step 4 · 验证

```powershell
# 看容器跑起来没
docker ps --filter name=rsshub

# 测 B 站秋葉(应该返回 200 + XML)
curl -s -o $null -w "HTTP %{http_code}  size %{size_download}B`n" http://localhost:1200/bilibili/user/video/12566101

# 测知乎话题
curl -s -o $null -w "HTTP %{http_code}  size %{size_download}B`n" http://localhost:1200/zhihu/topic/19828946
```

**预期**:都返回 `HTTP 200` + 几十 KB 数据。

如果仍 503:
- 看 logs:`docker logs rsshub --tail 50`
- 常见错误:cookie 字段拼错 / 漏 `SESSDATA` / 知乎 cookie 用了单数 `ZHIHU_COOKIE`(错,应该是 `ZHIHU_COOKIES`)

---

## Step 5 · 再跑一次 preflight + TrendRadar 验证

```powershell
cd D:\Dev\ai-wechat-pipeline
.\tools\preflight.ps1
.\tools\run_trendradar.ps1
```

**预期**:
- preflight 第 5 项(RSSHub 自建)从 SKIP / FAIL 变 PASS
- TrendRadar 抓完后 inspect_feed_health 7 个 RSSHub feed 全部 alive

---

## Cookie 维护(以后)

| 事件 | 怎么处理 |
|---|---|
| B 站 cookie 过期(约 3-5 天,根据 memory) | 重新抓,docker stop/rm/run 再来一次。**这是常态,不是 bug** |
| 知乎 cookie 过期(约 1-3 个月,比 B 站宽松) | 同上 |
| RSSHub 升级 | `docker pull diygod/rsshub:chromium-bundled` + 重启 |

**建议**:把上面 Step 3 的 `docker run` 命令存成 `tools/run_rsshub.ps1`,以后重启只跑这一个脚本。后续可以做。

---

## 关联

- 当前 config.yaml line 345-408 8 个 RSSHub feed 配置
- RSSHub 官方 Bilibili 路由文档:https://docs.rsshub.app/routes/social-media#bilibili
- RSSHub 官方 Zhihu 路由文档:https://docs.rsshub.app/routes/social-media#zhihu
- memory [[ai-wechat-information-intake]] 信源层进度
- preflight 第 5 项即将加入 localhost:1200 实测
