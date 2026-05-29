# we-mp-rss Cookie 重扫指引

**目的**:把 we-mp-rss 容器里过期的微信扫码 cookie 重新激活,让 16 个公众号 feed 恢复抓新文章。

**触发时机**:`/feed/MP_WXS_xxx.atom` 拉到的文章日期停在 2 天前以上;TrendRadar 推送里公众号源全部"无新内容"。

**月成本**:¥0(本机 Docker,什么都不变)

---

## 背景:为什么会过期

- we-mp-rss 通过移动版微信公众号搜索接口抓文章,需要一份"已登录"的 wechat session
- 这份 session 持久化在容器内 `/app/data/wx.lic`(加密文件)
- 微信侧 session **1-3 天**自动失效;失效后所有 feed 的 sync_time 还会推进(容器活着),但 articles 表停止新增

---

## Step 0 · 确认容器在跑

```
docker ps --filter "name=we-mp-rss" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
```

期望输出:
```
we-mp-rss   Up xxx hours   0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
```

如果**容器不在**:
```
docker start we-mp-rss
# 如果连容器都没了(系统重启 / 手动删过),重新跑:
docker run -d --name we-mp-rss -p 8001:8001 \
  -v ${PWD}/we-mp-rss-data:/app/data \
  ghcr.io/rachelos/we-mp-rss:latest
```

注意:不挂数据卷会丢失所有 feed 订阅,得重新加 16 个公众号。

---

## Step 1 · 打开 admin UI

浏览器访问 http://localhost:8001

**登录凭证**(见 user memory `reference_wemp_rss_credentials`):
- 用户名:`admin`
- 密码:`admin123`

注意:旧版 README 写的 `admin@123` 是误导,真 hash 在 `data/db.db` users 表,实际密码就是 `admin123`。

---

## Step 2 · 扫码授权

登录 admin UI 后:

1. 顶部导航或侧边栏找"**授权管理**" / "**扫码授权**"(具体菜单名因 we-mp-rss 版本可能不同;找带二维码图标的入口)
2. 页面会显示一张**微信二维码**
3. 用**手机微信** App 扫码 → 在手机上**确认登录**
4. 后台会自动:
   - 拿到新的 session token
   - 加密写入 `/app/data/wx.lic`(可以从宿主机看时间戳确认)
5. 页面提示"授权成功"

---

## Step 3 · 验证 cookie 写入

宿主机执行:

```
docker exec we-mp-rss sh -c "ls -la /app/data/wx.lic"
```

期望:`wx.lic` 的 mtime 是**刚才几分钟内**。如果 mtime 还是过期时间 → 扫码失败,见 Step 5 排错。

---

## Step 4 · 验证 feed 能抓新文章

任选一个**真活跃**的公众号 feed(比如量子位):

```
docker exec we-mp-rss python3 -c "import sqlite3,json; c=sqlite3.connect('/app/data/db.db').cursor(); c.execute('SELECT MAX(publish_time) FROM articles WHERE mp_id=\"MP_WXS_3236757533\"'); print('量子位 last:', c.fetchone()[0])"
```

然后**等 5-10 分钟**让 we-mp-rss 内部的 job 跑一轮(`interval` 默认 10s/篇,扫一遍 16 个公众号要几分钟),再跑一次同样的查询。

如果 `last` 推进到**今天**的 unix 时间戳(可以 `date +%s` 比对),cookie 重扫成功。

也可以直接拉 RSS:
```
curl -s "http://localhost:8001/feed/MP_WXS_3236757533.atom?limit=3" | head -40
```
看 `<updated>` 字段是不是今天。

---

## Step 5 · 排错

### 5.1 扫码后页面卡住 / 没反应

- 看容器日志:`docker logs we-mp-rss --tail 100`
- 找 `error` / `失败` / `exception` 关键字
- 常见原因:微信侧风控,**换台手机** / **换个微信账号**重试

### 5.2 wx.lic 时间戳没更新

- 容器内 `/app/data` 是只读挂载?查 `docker inspect we-mp-rss | grep -A 3 Mounts`
- 数据卷应该是 `rw`,不是 `ro`
- 修复:停容器 + 重新 `docker run` 时去掉 `:ro`

### 5.3 cookie 写入成功但 feed 还是 0 新文章

- 等够时间(>10 分钟)了吗?
- 该公众号本身真停更?对比另外 15 个 feed 是不是同步恢复
- 该公众号自己被微信封了?浏览器搜公众号验证

### 5.4 容器在跑但 admin UI 打不开

- 端口被占?`netstat -ano | findstr :8001`
- 容器内 8001 是不是真起来:`docker exec we-mp-rss curl -s http://localhost:8001/ | head -5`

### 5.5 扫码二维码本身刷不出来

- 网页加载失败?可能 `SEND_CODE=True` 但没配通知渠道导致前端报错
- 看 admin UI 设置里 `WERSS_AUTH_WEB`,确认是 `True`(web 授权模式)
- 或直接看容器日志:`docker logs we-mp-rss --tail 200 | grep -i "qr\|code\|auth"`

---

## 频率与自动化

- **建议**:每 2-3 天主动检查一次(脚本可以查 articles 表最大 publish_time)
- **彻底解决**:we-mp-rss 支持邮件 / webhook 推送过期提醒(`SEND_CODE=True` + 配 `NOTICE_*` 渠道)
- **暂时不做的事**:不写自动重扫脚本——扫码必须人工持手机确认,无法绕过

---

## 历史记录

| 日期 | 事件 |
|---|---|
| 2026-05-22 10:16 | 上次扫码,wx.lic 写入 |
| 2026-05-22 10:21~10:37 | 16 个 feed 最后一次拿到新文章 |
| 2026-05-26 22:00+ | 全 16 feed 停止 4 天,确认 cookie 过期,需重扫 |
