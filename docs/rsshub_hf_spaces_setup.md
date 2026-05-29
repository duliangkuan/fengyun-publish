> ## ⛔ 此文档已 DEPRECATED(2026-05-26)
>
> **不要走这条路。** 原因:
> 1. Hugging Face 在中国大陆 IP 实测返回 **HTTP 418**(地区屏蔽,2026-05-26 实测确认)
> 2. 用户已在本机 Docker 自建 RSSHub(`diygod/rsshub:chromium-bundled` 端口 1200),不需要云端
>
> **主路径见**:[docs/rsshub_cookie_setup.md](rsshub_cookie_setup.md) — 给本机 Docker 注入 cookie 救活 7 个 503 feed
>
> 本文留档作为「将来上云的备选方案」(如果本机 Docker 关机就停 → Zeabur 是更合适的国内可达替代,见 reports/phase17_b_rsshub_freehost.md)。

---

# 自建 RSSHub 到 Hugging Face Spaces — 免费部署指南

**目的**:把当前 config.yaml 里 8 个走 `rsshub.app` 公共实例的 feed 改走你自己的 RSSHub 实例。

**为什么必须做**:2026-05-25 实测,`rsshub.app` 公共实例对你的 IP **完全 403**,8 个 feed 已经实际拉空。

**为什么选 HF Spaces**:Docker 原生 + 完全免费 + 2 vCPU/16GB RAM + 4 个真实部署案例。
**唯一坑**:48 小时无访问会休眠 → 用 cron-job.org 每天 ping 一次解决。

**月成本**:**¥0**

---

## 前置

- 一个 Hugging Face 账号(huggingface.co 注册免费)
- 一个 cron-job.org 账号(防休眠用,免费)
- B 站登录态 cookie(后面教抓)

---

## Step 1:创建 HF Space

1. 去 https://huggingface.co/new-space
2. **Owner**:你的用户名
3. **Space name**:`rsshub`(或别的,记住即可)
4. **License**:MIT
5. **SDK**:选 **Docker**
6. **Visibility**:Public(私有需要 HF Pro)
7. 点 Create Space

---

## Step 2:上传 Dockerfile

在你 Space 页面 → Files → Add file → Create new file → 文件名输入 `Dockerfile`,粘下面内容:

```dockerfile
FROM diygod/rsshub:latest
ENV PORT=7860
EXPOSE 7860
```

**重要**:`PORT=7860` 不能改,HF Spaces 硬要求监听 7860 端口。

点 Commit。HF Spaces 会自动开始构建,**等几分钟** Space 状态变成 Running。

---

## Step 3:验证基础部署

Space 状态 Running 后,你的实例 URL 类似:
```
https://<你的用户名>-rsshub.hf.space
```

浏览器打开:
```
https://<你的用户名>-rsshub.hf.space/bilibili/user/video/1567748478
```
能看到 XML 内容就 OK(B 站需要 cookie 才能完整拉,无 cookie 也会返回但内容空)。

---

## Step 4:注入 cookie(B 站必做,微博可选)

### 抓 B 站 cookie

1. 用你的微信登录 https://www.bilibili.com
2. 任意点开一个 UP 主主页
3. F12 打开 DevTools → Application → Cookies → https://www.bilibili.com
4. 复制下面字段拼成一行(空格 + 分号分隔):
   - `SESSDATA=xxx`
   - `bili_jct=xxx`
   - `DedeUserID=xxx`
   - `DedeUserID__ckMd5=xxx`
5. 最终格式:`SESSDATA=xxx; bili_jct=xxx; DedeUserID=xxx; DedeUserID__ckMd5=xxx`

### 注入到 HF Spaces

回 Space → Settings → Variables and secrets → **New secret**

**6 个 B 站 UP 主用同一个 cookie 就够**(都是你自己账号),只配一个变量:

| Variable name | Value |
|---|---|
| `BILIBILI_COOKIE_0` | 上面拼好的 cookie 字符串(`0` 表示默认,所有 UP 用同一个) |

点 Save。Space 会自动 restart。

### 微博 cookie(可选)

如果你想恢复微博 AI 关键词路由,同理:登录 weibo.com,F12 抓 `SUB=xxx; SUBP=xxx` 这两个字段,新增 secret:

| Variable name | Value |
|---|---|
| `WEIBO_COOKIE` | `SUB=xxx; SUBP=xxx; ...` |

---

## Step 5:配 cron-job.org 防休眠

HF Spaces 免费层 **48 小时无访问会休眠**,休眠后冷启动要等 30-60 秒。TrendRadar 拉的时候撞冷启动会超时。

解决方案:每天 ping 一次。

1. 注册 https://cron-job.org(免费)
2. Dashboard → CREATE CRONJOB
3. **Title**:`RSSHub HF Spaces keepalive`
4. **URL**:`https://<你的用户名>-rsshub.hf.space/`(根路径就行)
5. **Schedule**:Every day at 03:00(凌晨 3 点,任意时段都行,避开 TrendRadar 高峰)
6. **Save**

完事。

---

## Step 6:改 TrendRadar config.yaml

把原来 8 个 `https://rsshub.app/...` 全部替换成你的 HF Space URL。

打开 `D:\Dev\TrendRadar\config\config.yaml`,找到 8 个 feed:

| feed id | 原 URL | 新 URL |
|---|---|---|
| rsshub-weibo-keyword-ai | `https://rsshub.app/weibo/keyword/AI` | `https://<你>-rsshub.hf.space/weibo/keyword/AI` |
| rsshub-zhihu-roundtable-aitools | `https://rsshub.app/zhihu/roundtable/aitools` | `https://<你>-rsshub.hf.space/zhihu/roundtable/aitools` |
| bilibili-limu-ai | `https://rsshub.app/bilibili/user/video/1567748478` | `https://<你>-rsshub.hf.space/bilibili/user/video/1567748478` |
| bilibili-tongji-zihao | `https://rsshub.app/bilibili/user/video/1900783` | `https://<你>-rsshub.hf.space/bilibili/user/video/1900783` |
| bilibili-guizang-ai | `https://rsshub.app/bilibili/user/video/1741797` | `https://<你>-rsshub.hf.space/bilibili/user/video/1741797` |
| bilibili-qiuye-aaaki | `https://rsshub.app/bilibili/user/video/12566101` | `https://<你>-rsshub.hf.space/bilibili/user/video/12566101` |
| bilibili-tuling-cat | `https://rsshub.app/bilibili/user/video/371846699` | `https://<你>-rsshub.hf.space/bilibili/user/video/371846699` |
| bilibili-hetongxue | `https://rsshub.app/bilibili/user/video/163637592` | `https://<你>-rsshub.hf.space/bilibili/user/video/163637592` |

把 Space URL 告诉我,我可以**帮你一次 sed 全替换**。

---

## Step 7:激活之前注释掉的掘金 AI 信源

config.yaml 我之前注释了一行:
```yaml
# 掘金 AI 分类 (rsshub.app/juejin/category/ai) — RSSHub 公共实例 403,等自建 RSSHub on HF Spaces 后激活
```

自建好之后追加这一条:
```yaml
    - id: "rsshub-juejin-ai"
      name: "[T3] 掘金 AI 分类"
      url: "https://<你>-rsshub.hf.space/juejin/category/ai"
      max_age_days: 1
```

---

## Step 8:验证

跑 TrendRadar 一次,看 8 + 1 个 feed 是不是都有数据:
```powershell
cd D:\Dev\TrendRadar
python main.py --doctor
```

或直接看输出 HTML 报告。

---

## 维护

| 事件 | 怎么处理 |
|---|---|
| B 站 cookie 过期(3-5 天) | 重新抓 cookie → HF Space Settings → 更新 `BILIBILI_COOKIE_0` → Restart |
| HF Space 长时间没反应 | cron-job 失效?去 cron-job.org 看 Execution History |
| RSSHub 升级 | HF Space → Settings → Factory rebuild(会拉最新 diygod/rsshub:latest 镜像) |
| Space 报错 | Space → Logs 看错误 |

---

## 关联

- 调研报告:`D:\Dev\ai-wechat-pipeline\reports\phase17_b_rsshub_freehost.md`
- 真实参考 Dockerfile:https://huggingface.co/spaces/Orion-zhen/rsshub/blob/main/Dockerfile
- RSSHub 官方文档:https://docs.rsshub.app/deploy/
- memory 关联:[[ai-wechat-information-intake]] [[feedback_no_speculation]]
