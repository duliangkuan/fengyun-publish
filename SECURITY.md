# 安全说明 SECURITY

本项目涉及多个外部服务的 API 凭证,本文档说明:
1. 凭证清单与旋转周期
2. 凭证泄漏应急流程
3. pre-commit 钩子配置
4. 漏洞报告通道

---

## 一、凭证管理

所有凭证存在 `.env`(`.gitignore` 已拦截),从未直接 commit 到 git。模板见 [`.env.example`](.env.example)。

### 凭证清单与旋转周期

| 凭证 | 用途 | 自然旋转周期 | 怎么旋转 |
|---|---|---|---|
| `WECHAT_APPID` | 微信公众号身份 | 永久 | 不需要(关联公众号实体) |
| `WECHAT_SECRET` | 微信公众号鉴权 | 怀疑泄漏立即 | 公众号后台 → 设置与开发 → 基本配置 → 重置 |
| `WECHAT access_token` | 运行时缓存(`tools/.wechat_token.json`) | 7200 秒自动 | `tools/post_fengyun_publish.py` 自动处理 |
| `VOLCENGINE_IMAGE_KEY` | 火山引擎方舟 Seedream | 怀疑泄漏立即 | 火山控制台 → 方舟 → API Key 管理 → 删除重建 |
| `ANTHROPIC_API_KEY` | Claude API(所有 skill) | 怀疑泄漏立即 | console.anthropic.com → Settings → API Keys |
| `DEEPSEEK_API_KEY` | DeepSeek API(可选 lint) | 怀疑泄漏立即 | platform.deepseek.com → API Keys |
| `we-mp-rss cookie` | 公众号 feed(Docker 环境变量) | ~80 小时 | `docker exec we-mp-rss` 容器内扫码重抓 |
| `B 站 cookie` | RSSHub feed | 3-5 天 | 浏览器 F12 抓 → `docker stop/rm/run`,见 [`docs/rsshub_cookie_setup.md`](docs/rsshub_cookie_setup.md) |
| `知乎 cookie` | RSSHub feed | 1-3 月 | 同上(知乎宽松) |
| `LARK_APP_ID` / `LARK_APP_SECRET` | 飞书 Base 数据飞轮 | 永久 | 开放平台后台 → 应用管理 |

### 凭证存放原则

- ✅ 所有凭证只放在 `.env`(被 `.gitignore` 拦)
- ✅ Cookie 字符串只放在本地 Docker 环境变量(`docker run -e KEY=value`)
- ✅ 微信 `access_token` 运行时缓存到 `tools/.wechat_token.json`(已 ignore)
- ❌ **绝不**把任何凭证写进源码、文档、commit message、PR 描述
- ❌ **绝不**通过截图分享(token 会泄漏在 EXIF 或 OCR 里)
- ❌ **绝不**在公开频道(Twitter / GitHub Issue)粘贴

---

## 二、凭证泄漏应急流程

如果发现任何凭证已经误推 git / 截图泄漏 / 私聊外发:

### 立刻做(5 分钟内)

1. **revoke / 重置**泄漏的凭证(查上表第 4 列)
2. 如果是 `access_token`:删除 `tools/.wechat_token.json`,下次运行自动重新获取
3. 如果是 cookie:`docker stop` 涉事容器,旧 cookie 立即失效

### 然后做(30 分钟内)

4. 检查 git 历史是否有泄漏:
   ```bash
   git log --all --full-history -p -- .env
   git log --all --full-history -p -- tools/.wechat_token.json
   ```
5. 如果曾误推到 git history,用 [git-filter-repo](https://github.com/newren/git-filter-repo) 清除:
   ```bash
   git filter-repo --path .env --invert-paths
   git push --force-with-lease origin main
   ```
   (参考:[GitHub 官方移除敏感数据](https://docs.github.com/cn/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository))
6. 私有 repo 即使 force push 也安全,但需通知所有 collaborator 重新 clone

### 复盘

7. 写复盘 issue / 笔记:为什么 pre-commit 没拦住?加新规则到 `.pre-commit-config.yaml`
8. 如果是供应链问题(三方库泄漏):pin 版本 + 监控 CVE

---

## 三、pre-commit 钩子(自动防泄漏)

仓库根 `.pre-commit-config.yaml` 配置了:
- **gitleaks** — 扫描可疑凭证字符串(API key / token / private key)
- **detect-private-key** — 专扫 SSH / PGP / SSL 私钥
- **check-added-large-files**(5 MB 上限)— 防误推大文件
- **trailing-whitespace** / **end-of-file-fixer** — 代码卫生
- **check-yaml** / **check-json** — 配置文件语法

### 启用

```bash
pip install pre-commit
pre-commit install
```

之后每次 `git commit` 自动跑钩子,有问题会拦住 commit。

### **绝不 `--no-verify` 跳过钩子**

如果钩子误报,在 `.pre-commit-config.yaml` 加 `exclude` 规则,**而不是**绕过。

---

## 四、依赖安全

- 项目无 `requirements.lock.txt`(暂未锁版本),建议生产环境用 `pip freeze` 锁定
- 定期跑 `pip-audit`(`pip install pip-audit && pip-audit`)检查依赖 CVE
- `vendor/` 下的开源 clone 不受版本锁约束,使用前确认上游 release / security advisory

---

## 五、漏洞报告

发现安全问题:**直接邮件给作者,不要开公开 issue**。

- **邮箱**:2330304961@qq.com
- **微信**:FengYunAgent
- 标题前缀:`[SECURITY]`
- 描述:复现步骤 + 影响范围 + 建议修复

我会在 72 小时内回复确认。

---

## 六、KOL 语料的版权敏感

`corpus/raw/` 和 `corpus/.raw/` 是从公众号公开文章爬取的 raw 数据(数百 MB)。`.gitignore` 已拦截,**不会**进 git。

如果出于任何原因需要分享给作者圈外的人(包括 GitHub clone 链接):
- ✅ 分享代码 / 文档 / `corpus/baoyu/`、`corpus/kazik/` 等经过加工的 markdown(已脱敏)
- ❌ **绝不**分享 `corpus/raw/` 或 `corpus/.raw/` 的原文 JSON

详见 [`LICENSE`](LICENSE) 中 KOL Corpus Notice 一节。
