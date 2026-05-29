# Phase 9 · Task C · TrendRadar config.yaml 改动记录
*执行时间：2026-05-22 · Sonnet agent*

---

## Backup 路径

```
D:\Dev\TrendRadar\config\config.yaml.bak.20260522
```

---

## 改了哪些文件

| 文件 | 改动类型 |
|---|---|
| `D:\Dev\TrendRadar\config\config.yaml` | 主配置：删 1 条 / 改 1 条 / 新增 11 条 |
| `D:\Dev\TrendRadar\config\ai_interests.txt` | 末尾追加中文 AI 公司关键词段 |

---

## 新增 11 个信源（Day 1 批）

### 国际 Newsletter T1/T2（8 个）

| id | name | tier | URL | max_age_days |
|---|---|---|---|---|
| `one-useful-thing` | OneUsefulThing (Ethan Mollick) | T2 | `https://www.oneusefulthing.org/feed` | 7 |
| `ahead-of-ai` | Ahead of AI (Sebastian Raschka) | T2 | `https://magazine.sebastianraschka.com/feed` | 7 |
| `algorithmic-bridge` | The Algorithmic Bridge | T2 | `https://www.thealgorithmicbridge.com/feed` | 7 |
| `bens-bites` | Ben's Bites | T2 | `https://bensbites.beehiiv.com/feed` | 2 |
| `semianalysis` | SemiAnalysis (芯片+AI基础设施) | T2 | `https://newsletter.semianalysis.com/feed` | 7 |
| `simon-willison` | Simon Willison | T2 | `https://simonwillison.net/atom/everything/` | 3 |
| `github-trending-python` | GitHub Trending Python | T2 | `https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml` | 1 |
| `google-research-blog` | Google Research Blog | T1 | `https://research.google/blog/rss/` | 3 |

### 国内媒体 T3（3 个）

| id | name | tier | URL | max_age_days |
|---|---|---|---|---|
| `jiqizhixin` | 机器之心 | T3 | `https://www.jiqizhixin.com/rss` | 全局默认(1d) |
| `geekpark` | 极客公园 | T3 | `http://www.geekpark.net/rss` | 全局默认(1d) |
| `ithome` | IT之家 | T3 | `http://www.ithome.com/rss/` | 1 |

---

## HN URL 改动

| 字段 | 旧值 | 新值 |
|---|---|---|
| `hacker-news.url` | `https://hnrss.org/frontpage` | `https://hnrss.org/frontpage?points=100` |
| `hacker-news.name` | `Hacker News` | `[T3] Hacker News Top` |
| 新增 | — | `max_age_days: 1` |

**理由**：`?points=100` 过滤低质量条目（HN 得分 <100 的），减少信噪比。

---

## 删除的条目

| id | name | URL | 理由 |
|---|---|---|---|
| `nvidia-newsroom` | NVIDIA Newsroom | `https://nvidianews.nvidia.com/rss` | 营销稿为主，信噪比差（Phase 8 Musk 判断），保留 `nvidia-blogs` 即可 |

---

## ai_interests.txt 改动

在文件末尾追加了以下内容（Phase 8 Day 1，确保国内大模型不被英文 prompt 误过滤）：

```
# ——— Phase 8 Day 1 补充：国内 AI 公司关键词（2026-05-22）———
国内大模型动态（DeepSeek / Kimi / 通义 / 智谱 / MiniMax / 阶跃 / 百川）
中国 AI 公司发布 / 国产模型更新 / AI 产品上线
AI 创业融资（国内）/ AI 应用落地（国内）
```

---

## 验证结果

```
feeds count: 33（旧: 22，净增 11）
YAML 语法: 无报错
NVIDIA Newsroom: 已删除
HN URL: 已换 ?points=100
```

---

## Day 2 待办（风云人工操作，agent 不做）

### we-mp-rss 公众号层接入（需要 Docker + 扫码，约 2 小时）

**前提条件**：
- Docker Desktop 在线运行
- 微信账号准备好（扫码登录，账号有被封风险，建议用小号）

**Step 1：启动 we-mp-rss**
```bash
docker run -d --name we-mp-rss -p 8001:8001 ghcr.io/rachelos/we-mp-rss:latest
```
备选镜像（若 ghcr.io 拉取慢）：用 mp-proxy-worker 代理 `mp-proxy-worker.dufengyun12.workers.dev`

**Step 2：扫码登录**
浏览器打开 `http://localhost:8001`，扫码绑定微信账号

**Step 3：在 we-mp-rss 添加 P0 公众号**
- DeepSeek 官方
- Kimi (Moonshot)
- 智谱 AI
- 机器之心公众号（补充已有网页 RSS）
- 量子位公众号

**Step 4：获取 feed URL 并填入 config.yaml**

在 `D:\Dev\TrendRadar\config\config.yaml` 的公众号占位区块，取消注释并填入实际 atom URL：

```yaml
# ——— 📰 公众号 RSS（T1 国内一手）———
- id: "wechat-deepseek"
  name: "[T1] DeepSeek 官方"
  url: "http://localhost:8001/feed/deepseek.atom"
  max_age_days: 3

- id: "wechat-kimi"
  name: "[T1] Kimi (Moonshot)"
  url: "http://localhost:8001/feed/kimi.atom"
  max_age_days: 3

- id: "wechat-zhipu"
  name: "[T1] 智谱AI"
  url: "http://localhost:8001/feed/zhipu.atom"
  max_age_days: 3
```

**Step 5：验证**
```bash
python -c "import yaml; cfg = yaml.safe_load(open('D:/Dev/TrendRadar/config/config.yaml')); print('feeds:', len(cfg['rss']['feeds']))"
```

**Step 6：可选 — 在 ai_analysis_prompt.txt 加 Tier 权重指令**（等 Day 1 跑一次后再加，避免未测试配置叠加）：
```
信源权重规则：
- 名称包含[T1]的信源（官方发布）：优先展示，即使热度评分略低
- 名称包含[T2]的信源（高质量分析）：正常权重，着重提炼独特洞察
- 名称包含[T3]的信源（专业媒体）：标准处理
- 名称包含[T4]的信源（聚合/综合）：仅在与T1形成互补时展示，避免重复
```

**注意**：Fallback 方案是 `cooderl/wewe-rss`（基于微信读书，不依赖扫码账号，更稳定）。

---

*报告路径：`D:\Dev\ai-wechat-pipeline\reports\phase9_c_trendradar_changes.md`*
*生成时间：2026-05-22*
