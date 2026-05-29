# Phase 9 · Task D · 全批信源接入执行记录
*执行时间：2026-05-22 · Sonnet agent · 全程严格增量保存*

---

## Backup 路径

```
D:\Dev\TrendRadar\config\config.yaml.bak.phase9.类2
```

（Day 1 Backup 路径：`config.yaml.bak.20260522`）

---

## Phase A · 类 2 — 直接 RSS（5 个候选，3 个成功）

| id | name | URL | 验证结果 |
|---|---|---|---|
| `tldr-ai` | [T2] TLDR AI | `https://tldr.tech/api/rss/ai` | ✅ 有效；最新条目 2026-05-21 |
| `a16z-blog` | [T2] a16z Blog | `https://a16z.com/feed/` | ✅ 有效（feed 可访问） |
| `mit-tech-review-ai` | [T2] MIT Tech Review AI | `https://www.technologyreview.com/feed/` | ✅ 有效（feed 可访问） |
| — | Anthropic Engineering | 候选 1: `.../engineering/rss.xml` / 候选 2: `.../news/feed` | ❌ 两个候选 URL 均 404；Anthropic 官网无公开 engineering blog RSS；**已跳过，写注释说明** |
| — | Stratechery 免费版 | `https://stratechery.com/feed/` | ⚠️ Feed 存在但混合付费内容（Passport token 系统）；风云明确 ❌ 付费；**已跳过，写注释说明** |

**净加入：3 个（类 2 有效 3/5）**

---

## Phase B · 类 3 — RSSHub + X/Twitter

### B-1 RSSHub 实例选择

- **主用**：`https://rsshub.app/`（公共主实例）
- **备用 fallback**：`https://rss.shab.fun/`（Sino-RSS 社区）
- 两个实例均写入 config 注释，供限流时切换

### B-2 RSSHub 新增国内路由（2 个）

| id | name | URL | 说明 |
|---|---|---|---|
| `rsshub-weibo-keyword-ai` | [T3] 微博 AI 热搜 | `https://rsshub.app/weibo/keyword/AI` | RSSHub `/weibo/keyword/:keyword` 路由 |
| `rsshub-zhihu-roundtable-aitools` | [T3] 知乎圆桌 AI用户手册 | `https://rsshub.app/zhihu/roundtable/aitools` | 圆桌 ID=aitools；9070 万浏览；国内 AI 讨论共鸣源 |

**新智元调研结论**：RSSHub 无 `/aiera/news` 或 `/xinzhiyuan` 官方路由；唯一稳定接法是 we-mp-rss 公众号订阅（已在 P1 公众号清单中）。

### B-3 X/Twitter Stub

- 文档已创建：`D:\Dev\TrendRadar\docs\twitter_intake_design.md`
- config.yaml 注释占位段：`# X/Twitter feeds — 等风云提供账号池后激活`
- 监控 KOL 清单：@karpathy / @sama / @gdb / @ylecun / @AndrewYNg / @DarioAmodei / @_akhaliq
- **今晚是 stub；需要风云提供 3 个 X 账号 cookies 才能真跑**

---

## Phase C · 类 4 — B 站 AI UP 主推荐（6 个接入）

RSSHub 路由格式：`/bilibili/user/video/<UID>`

### 推荐并接入的 UP 主（6 个）

| id | name（config） | UID | 内容方向 | tier | max_age_days |
|---|---|---|---|---|---|
| `bilibili-limu-ai` | 跟李沐学AI | 1567748478 | 论文精读/模型深度；亚马逊首席科学家；学术权威 | T3 | 7 |
| `bilibili-tongji-zihao` | 同济子豪兄 | 1900783 | AI/机器人科普；精读论文；教育向 | T3 | 7 |
| `bilibili-guizang-ai` | 歸藏 AI工具箱 | 1741797 | 全球最新 AI 工具追踪；高频更新；工具向核心信源 | T3 | 3 |
| `bilibili-qiuye-aaaki` | 秋葉aaaki | 12566101 | Stable Diffusion/AIGC 绘画第一 UP；AI 绘图/工具 | T3 | 7 |
| `bilibili-tuling-cat` | 图灵的猫 | 371846699 | 创意 AI 应用；高频更新；热点预测等创新内容 | T3 | 3 |
| `bilibili-hetongxue` | 老师好我叫何同学 | 163637592 | 2025 百大"年度最佳作品奖"；科技 + AI 应用；高传播 | T3 | 7 |

### 调研但未加入的 UP 主（留作 Day N 备选）

| UP主 | 原因 |
|---|---|
| 影视飓风（UID: 946974） | 非 AI 垂直，主要是影视/科技泛科普 |
| 王树森 | 强化学习学术向，内容更新频率低 |
| Genji是真想教会你 | 主打 ChatGPT/Midjourney 应用教程，与 歸藏 方向重叠 |
| 秋叶aaaki（重名确认）| 同 秋葉aaaki，已接入 |

**注**：bilibili RSSHub 路由有时出现 412 错误（反爬），建议风云后续自建 RSSHub 实例并配置 bilibili cookie 以提升稳定性。

---

## Phase D · 类 4 — P2 公众号占位（5 个）

已在 config.yaml 公众号注释段末尾追加 5 个 P2 公众号注释占位：

| id | name | atom URL 模板 |
|---|---|---|
| `wechat-saiboshanxin` | [T2] 赛博禅心 | `http://localhost:8001/feed/saiboshanxin.atom` |
| `wechat-qwen` | [T1] 通义千问 | `http://localhost:8001/feed/qwen.atom` |
| `wechat-minimax` | [T1] MiniMax | `http://localhost:8001/feed/minimax.atom` |
| `wechat-stepfun` | [T1] 阶跃星辰 | `http://localhost:8001/feed/stepfun.atom` |
| `wechat-baichuan` | [T1] 百川智能 | `http://localhost:8001/feed/baichuan.atom` |

**位置**：config.yaml 第 305 行后的注释段（P2 公众号区块）。扫码后取消注释 + 填入实际 atom URL 即可激活。

---

## 验证结果

```
feeds count: 44（旧: 33，净增 11）
YAML 语法: 无报错
```

**增量详情**：

| 批次 | 新增数 | 说明 |
|---|---|---|
| 类 2 直接 RSS | +3 | tldr-ai / a16z-blog / mit-tech-review-ai |
| 类 3 RSSHub 国内 | +2 | weibo-keyword-ai / zhihu-roundtable-aitools |
| 类 4 B 站 UP 主 | +6 | 6 个 bilibili UP 主（rsshub 路由） |
| **合计** | **+11** | **33 → 44** |

---

## 失败 / 跳过的源

| 源 | 原因 | 处理 |
|---|---|---|
| Anthropic Engineering RSS | 两个候选 URL 均 404，官网无公开 engineering blog RSS | 跳过 + config 注释 TODO |
| Stratechery 付费版 | 风云明确 ❌ 付费 | 跳过 + config 注释说明 |
| 新智元 RSSHub 路由 | RSSHub 无对应路由（/aiera/news / /xinzhiyuan 不存在） | 记录在案，走 we-mp-rss 公众号路线 |
| X/Twitter twscrape | 需风云提供账号池 | Stub 文档 + 注释占位 |

---

## 风云 Day 2 必做清单（only Docker + 扫码 + 给 atom URL）

1. **启动 we-mp-rss Docker**
   ```bash
   docker run -d --name we-mp-rss -p 8001:8001 ghcr.io/rachelos/we-mp-rss:latest
   ```

2. **浏览器打开 `http://localhost:8001`，微信扫码登录**（建议用小号）

3. **在 we-mp-rss 添加 P2 公众号**（5 个）：
   - 赛博禅心 / 通义千问 / MiniMax / 阶跃星辰 / 百川智能

4. **获取每个公众号的 atom URL**，格式为 `http://localhost:8001/feed/<公众号拼音>.atom`

5. **在 config.yaml 的 P2 区块取消注释**，替换 `.atom` 路径为实际值

6. **重新验证**：
   ```bash
   python -c "import yaml; cfg = yaml.safe_load(open('D:/Dev/TrendRadar/config/config.yaml', encoding='utf-8')); print('feeds:', len(cfg['rss']['feeds']))"
   ```
   应输出 `feeds: 49`（44 + 5 个 P2 公众号）

---

## 配置文件位置汇总

| 文件 | 说明 |
|---|---|
| `D:\Dev\TrendRadar\config\config.yaml` | 主配置（44 feeds） |
| `D:\Dev\TrendRadar\config\config.yaml.bak.phase9.类2` | 本次备份 |
| `D:\Dev\TrendRadar\config\config.yaml.bak.20260522` | Day 1 备份 |
| `D:\Dev\TrendRadar\docs\twitter_intake_design.md` | X/Twitter stub 设计文档 |

---

*报告路径：`D:\Dev\ai-wechat-pipeline\reports\phase9_d_full_intake_batch.md`*
*生成时间：2026-05-22*
