# GitHub 公众号模板开源生态调研（2026-05-24）

> 调研 Agent：Claude Sonnet 4.6 | 调研时间：2026-05-24
> 目标：为 fengyun-publish 系统寻找可借鉴/复用的开源项目

---

## 1. 4 位 KOL 的开源仓库

### 花叔（alchaincyf / 赛博禅心）

- **GitHub 主页**：https://github.com/alchaincyf
- **备注**：花叔 = 花生 = 赛博禅心，同一人，独立开发者，「小猫补光灯」App Store 付费榜 Top1

| 仓库 | Star | 最近更新 | 定位 | 跟我们相关 |
|---|---:|---|---|---|
| nuwa-skill | 21,000 | 2026-05-23 | 蒸馏任何人的思维方式 → 可运行 Skill | 低（认知框架，非排版） |
| huashu-design | 14,800 | 2026-04-21（v2.0）| HTML 原生设计 Skill：原型/幻灯/动画/MP4 导出 | 中（生成视觉资产） |
| zhangxuefeng-skill | 7,296 | 2026-05-22 | 张雪峰认知 OS（高考/考研/职规）| 无 |
| darwin-skill | 2,695 | 2026-05-22 | 自动化 Skill 优化（评估→改进→回滚）| 低 |
| huashu-skills | 802 | 2026-04-21 | 内容创作 Skills 合集（21 个 skill）| **高** |
| huashu-md-html | 659 | 2026-05-11 | md/html 双向流水线 + 4 套反 AI slop 主题 | **高** |
| hermes-agent-orange-book | 3,850 | 2026-04-21 | Hermes Agent 框架实战指南 | 低 |

**跟我们直接相关的 skill：**

- **huashu-wechat-image**（在 huashu-skills 里）：公众号配图，生成封面+正文图（AI 渲染或 HTML 渲染）
- **huashu-proofreading**：三轮 AI 痕迹检测降至 <30%，降低 AI slop
- **huashu-md-html**（独立仓库）：4 套反 AI slop 主题（article/report/reading/interactive），通过 `--theme` 参数切换，每套主题一个自包含 CSS 文件，无外部 CDN 依赖，有专门 `reading` 主题适配公众号转接。**没有 frontmatter 触发**，是 CLI 参数。

---

### 宝玉（JimLiu / Jim Liu 宝玉）

- **GitHub 主页**：https://github.com/jimliu
- **主仓库**：https://github.com/JimLiu/baoyu-skills

| 仓库 | Star | 最近更新 | 定位 |
|---|---:|---|---|
| baoyu-skills | **19,300** | 2026-05-18（v1.117.2）| 多 Skill 合集，覆盖内容创作/图片/发布 |

**所有 Skill 清单（跟我们相关度标注）：**

| Skill | 定位 | 相关度 |
|---|---|---|
| **baoyu-post-to-wechat** | 公众号发布：API/浏览器/SSH 隧道三模式 | ⭐⭐⭐ 最高 |
| **baoyu-markdown-to-html** | Markdown→HTML：4 主题×13 颜色，WeChat 优化，frontmatter+CLI 双控 | ⭐⭐⭐ 最高 |
| baoyu-cover-image | 封面图生成（5 维可定制）| ⭐⭐ 高 |
| baoyu-article-illustrator | 文章配图（Type×Style×Palette）| ⭐⭐ 高 |
| baoyu-format-markdown | Markdown 格式化 + frontmatter | ⭐ 中 |
| baoyu-infographic | 信息图（21 布局×21 风格）| ⭐ 中 |
| baoyu-diagram | SVG 流程图/结构图 | ⭐ 中 |
| baoyu-xhs-images | 小红书卡片 | 低 |
| baoyu-url-to-markdown | URL→Markdown | 低 |
| baoyu-youtube-transcript | YouTube 字幕下载 | 无 |

**baoyu-markdown-to-html 主题系统详解（重点）：**
- 4 主题：`default`（居中经典）/ `grace`（文字投影优雅）/ `simple`（极简非对称）/ `modern`（大圆角胶囊标题）
- 13 颜色预设 + 自定义 hex
- 优先级链：CLI 参数 → frontmatter → EXTEND.md 配置文件（可跨项目共享）
- 外链自动转脚注引用，保留 mp.weixin.qq.com 链接不转换
- 全 inline CSS（公众号兼容）
- 支持 Mermaid / PlantUML / 代码高亮 / 表格 / 脚注

**baoyu-post-to-wechat 发布机制：**
- API 模式：需本地 IP 加白名单，速度最快
- 浏览器模式：需 Chrome + 登录态，无需 IP 白名单
- SSH 隧道模式：本地 IP 未白名单时通过 SOCKS5 中转
- 安全：所有 Markdown 渲染/图片处理/草稿组装在本地，只有 HTTPS 请求走隧道
- 配置文件：`.baoyu-skills/baoyu-post-to-wechat/EXTEND.md`，支持多账号隔离

---

### 卡兹克（KKKKhazix / 数字生命卡兹克）

- **GitHub 主页**：https://github.com/KKKKhazix
- **主仓库**：https://github.com/KKKKhazix/khazix-skills

| 仓库 | Star | Fork | 更新 | 许可证 |
|---|---:|---:|---|---|
| khazix-skills | **11,600** | 1,600 | 30 commits（无精确日期）| MIT |

**所有 Skill 清单：**

| Skill | 触发词 | 定位 | 相关度 |
|---|---|---|---|
| **khazix-writer** | /khazix-writer | 公众号长文写作，「有见识的普通人认真聊一件打动他的事」| ⭐⭐⭐ 写作层最高 |
| hv-analysis | /hv-analysis | 横纵分析法，1-3 万字研究报告 | ⭐⭐ 选题调研层 |
| neat-freak | /neat-freak | 任务后同步文档/CLAUDE.md/Agent 记忆 | ⭐ 工程维护层 |
| aihot | /aihot | AI HOT 日报（无需 API Key）| ⭐ 信源层 |

**khazix-writer 写作规则摘要（跟 fengyun-writer 竞品对比）：**
- 5 种文章原型（调查实验/产品体验/现象分析/工具分享/方法论教学）
- 4 层自检（L1 硬规则/L2 风格/L3 内容质量/L4 人性感）
- 禁用：子标题（除编号方法论）、bullet points、markdown 格式符
- 禁词：说白了/本质上/赋能/抓手
- 用「」代替""，禁用破折号
- **纯写作 Skill，完全不含排版/HTML/发布逻辑**

---

### 其他相关（nexu-io / html-anything）

虽非 4 位 KOL 之一，但在调研中发现这个项目高度相关：

- **仓库**：https://github.com/nexu-io/html-anything
- **Star**：4,700 | **Fork**：488 | **许可证**：Apache 2.0
- **定位**：Agentic HTML 编辑器，75 Skills × 9 输出表面，支持 WeChat/XHS/X/Zhihu 一键导出
- **WeChat 发布原理**：引入 `juice` 库将 CSS 内联到 HTML `style` 属性，保留 `data-tool` 标记 → 可直接粘贴到微信编辑器保留样式
- **主题系统**：每个 Skill 的 SKILL.md 定义硬约束（8px 基线网格/CJK 字体栈/色彩对比 ≥4.5），防止模型随意发挥
- **与我们的差异**：无 API 草稿推送，仍是复制粘贴模式

---

## 2. 公众号模板/排版/渲染相关开源项目 TOP

| 仓库 | URL | Star | 最近活跃 | 用途 | 主题系统 | 草稿 API | 相关度 |
|---|---|---:|---|---|---|---|---|
| doocs/md | https://github.com/doocs/md | **12,600** | 2025-10（v2.1.0）| Web 编辑器，Markdown→公众号 HTML | 自定义 CSS | 无 | ⭐⭐ |
| wechat-article/wechat-article-exporter | https://github.com/wechat-article/wechat-article-exporter | **10,700** | 活跃（458 commits）| 批量下载公众号文章（含 HTML 100% 保真）| 无 | 无（抓取）| ⭐⭐⭐ 语料采集 |
| mdnice/markdown-nice | https://github.com/mdnice/markdown-nice | **4,600** | 较早 | Web 编辑器，多平台主题 | CSS 主题库 | 无 | ⭐ |
| lyricat/wechat-format | https://github.com/lyricat/wechat-format | **4,500** | 已停维护 | Markdown→微信特制 HTML | 无 | 无 | ❌ 停更 |
| nexu-io/html-anything | https://github.com/nexu-io/html-anything | **4,700** | 2026 活跃 | Agentic HTML，75 Skill，WeChat inline CSS | Skill 硬约束 | 无（复制粘贴）| ⭐⭐ |
| caol64/wenyan | https://github.com/caol64/wenyan | **~1,000** | 2026-03（v4.0.0）| 多平台排版美化（含公众号）| Typora 主题改编 | 复制粘贴 | ⭐⭐ |
| caol64/wenyan-mcp | https://github.com/caol64/wenyan-mcp | **1,200** | 2026-04（v2.0.3）| MCP Server，AI 自动排版+发布公众号 | Default/OrangeHeart/phycat | **有 API 草稿** | ⭐⭐⭐ |
| caol64/wenyan-cli | https://github.com/caol64/wenyan-cli | **170** | 2026-03 | CLI 工具，frontmatter 控制，CI/CD | CSS 主题 | **有 API 草稿** | ⭐⭐⭐ |
| xiaohuailabs/xiaohu-wechat-format | https://github.com/xiaohuailabs/xiaohu-wechat-format | **496** | 较新（8 commits）| 30 套主题，`--theme` 参数，可视化画廊 | **30 套 CSS 主题** | **有 API 草稿** | ⭐⭐⭐ |
| tyrchen/wechat-pub-rs | https://github.com/tyrchen/wechat-pub-rs | **18** | 2026-03（v0.7.0）| Rust SDK，frontmatter theme 字段，8 主题 | 8 主题 + frontmatter | **有 API 草稿** | ⭐⭐⭐（架构参考）|
| alchaincyf/huashu-md-html | https://github.com/alchaincyf/huashu-md-html | **659** | 2026-05-11 | md/html 双向，4 套反 slop 主题 | 4 套 CSS | 无 | ⭐⭐ |
| insula1701/maxpress | https://github.com/insula1701/maxpress | **117** | 2018（停更）| Python，JSON 配置，单主题 | JSON config | 无 | ❌ 停更 |
| caol64/wenyan-core | https://github.com/caol64/wenyan-core | **36** | 活跃 | TypeScript 核心库，npm 包，可嵌入 | CSS 主题 | 有 | ⭐⭐（可嵌入）|

---

## 3. 精筛 5 个最有价值的项目（展开分析）

### 3.1 baoyu-post-to-wechat + baoyu-markdown-to-html（JimLiu/baoyu-skills）

**为什么最相关：** 这是目前唯一已经把「主题切换 + 颜色预设 + frontmatter 控制 + CLI 参数 + 共享配置文件 + 三模式发布」都做到位的 Skill 级方案，跟 fengyun-publish 的技术路线最接近。

**思路 vs 我们：**
- baoyu 用 EXTEND.md 配置文件做全局默认，CLI 参数做覆盖，frontmatter 做文章级控制 → 三层优先级链
- 我们是 frontmatter `style: huashu` → 触发 layout_rules.py 里的分支 → 只有文章级控制，缺「系统默认」层
- baoyu 的 4 主题（default/grace/simple/modern）是通用风格，我们是基于特定 KOL 的风格逆向（huashu 风格），思路不同但互补

**可直接复用代码/配置：**
- EXTEND.md 三级优先级链的配置文件设计思路（可学习）
- SSH SOCKS5 隧道的发布中转方案（直接解决我们的 IP 白名单问题，如果以后有此需求）
- 外链转脚注的 `--no-cite` 开关设计

**风险/限制：**
- 许可证：未见 LICENSE 文件（调研时未明确），需要实地确认
- baoyu 的 4 主题都是通用审美，没有「逆向特定 KOL 风格」的模板机制
- 依赖 Node.js/TypeScript 运行时，与我们 Python 技术栈不同

---

### 3.2 wenyan-mcp + wenyan-cli（caol64 文颜生态）

**为什么最相关：** 2026 年最活跃的 MCP 原生公众号发布方案，有完整的「主题注册 → 自定义 CSS → API 草稿推送」链路，且开放「服务器模式」供团队/CI-CD 使用。

**思路 vs 我们：**
- 文颜 MCP 的主题注册机制（通过 CSS URL 动态注册）比我们的 yaml inline-style 更轻量
- wenyan-cli 的 frontmatter 要求 `title`（必填）+ `cover` + `author` + `source_url`，跟我们的 frontmatter 设计高度兼容
- 文颜生态分层清晰：core（npm 库）→ cli（命令行）→ mcp（AI 接入）→ pc（桌面应用），可以只接 cli 层

**可直接复用代码/配置：**
- `wenyan-core` npm 包：`npm install @wenyan-md/core`，直接调用其 Markdown→HTML 渲染（避免自己写渲染逻辑）
- 主题 CSS 格式：文颜的主题是自包含 CSS 文件（Default/OrangeHeart/phycat），我们可以把「huashu 风格 CSS」打包成文颜主题，然后用 `wenyan-cli` 发布
- server 模式：解决动态 IP / 云端部署的中转问题

**风险/限制：**
- wenyan-mcp star 数（1,200）和 wenyan-cli（170）偏低，社区不够大，维护风险存在
- 内置主题只有 3 个（Default/OrangeHeart/phycat），主题库没有 baoyu 丰富
- 许可证：Apache 2.0（✅ 商业友好）

---

### 3.3 xiaohu-wechat-format（xiaohuailabs/xiaohu-wechat-format）

**为什么相关：** 30 套 CSS 主题是目前公开调研中最大的主题库，有「可视化画廊预览」机制，且已对接公众号草稿 API。

**思路 vs 我们：**
- 30 主题分 3 层：独立样式（9 套）/ 策划样式（7 套）/ 模板系列（14 套 = 4 布局 × 多色系）
- 「4 布局 × 色系变体」的矩阵设计跟我们的「style 触发」思路高度吻合——我们完全可以借鉴这个分类框架
- `--theme newspaper` 的 CLI 参数风格，跟 baoyu/wenyan 类似

**可直接复用代码/配置：**
- 30 套主题的 CSS 文件（MIT 许可证，需实地确认）
- 主题矩阵分类框架（Minimal/Focus/Elegant/Bold × 色系）
- 可视化画廊预览机制（可以帮我们给 huashu / other 风格做预览）

**风险/限制：**
- Star 只有 496，维护频次低（仅 8 commits），项目成熟度存疑
- `--theme` 未支持 frontmatter（仅 CLI 参数），需要适配
- 30 套主题质量参差不齐，需要人工筛选

---

### 3.4 wechat-article-exporter（wechat-article/wechat-article-exporter）

**为什么相关：** 这是我们「数据飞轮」环节的关键工具——下载竞品/对标号文章的 HTML（100% 保真），用于逆向工程 KOL 的排版风格。

**思路 vs 我们：**
- 我们已有「corpus 真品 HTML → 抽 inline style → yaml 配置 → render 分支」的逆向工程流程
- wechat-article-exporter 是这条链路的**数据采集入口**，批量下载 + 支持阅读量/评论数导出
- HTML 导出 100% 保真（包含图片打包和 style 文件），可直接拿来做逆向工程素材

**可直接复用：**
- 直接部署（支持 Docker/Cloudflare）来批量采集对标号文章 HTML
- 用它的 JSON 格式导出来统计文章互动数据（阅读量/评论数），扩充数据飞轮指标

**风险/限制：**
- 许可证：MIT（✅），但需注意「内容版权属于原作者」的条款，仅可用于研究/逆向工程，不可翻版
- 依赖微信公众号编辑器的内置搜索 API，存在被封禁风险

---

### 3.5 tyrchen/wechat-pub-rs（Rust SDK）

**为什么相关：** Star 只有 18，但它是目前所有调研项目里**唯一用 frontmatter `theme` 字段**直接控制主题切换的方案，架构设计上跟我们最接近。

**思路 vs 我们：**
```yaml
# 它的 frontmatter 设计（直接对应我们的 style 字段）
theme: orangeheart
highlight_theme: github
```
- `available_themes()` / `has_theme()` 的主题注册 API 设计
- 8 个主题：`default / lapis / maize / orangeheart / phycat / pie / purple / rainbow`
- `client.upload()` → 返回 `draft_id`，`update_draft()` / `delete_draft()` 的草稿管理接口

**可直接复用：**
- frontmatter `theme:` 字段的命名约定（与我们的 `style:` 字段相似，可统一）
- 主题注册 + 查询的 API 设计模式（translate 到 Python 版本）
- 草稿管理接口设计

**风险/限制：**
- Rust 语言，与我们 Python 技术栈不兼容，只能借鉴设计，不能复用代码
- Star 极少，维护风险高

---

## 4. 横向对比表

| 维度 | fengyun-publish（我们）| baoyu-skills | wenyan 生态 | khazix-skills | 花叔 skills | xiaohu-wechat-format | doocs/md |
|---|---|---|---|---|---|---|---|
| **写作层（persona/voice）** | fengyun-writer Skill（风云语调）| 无 | 无 | khazix-writer（卡兹克语调）⭐ | huashu-proofreading（去 AI 痕迹）| 无 | 无 |
| **排版层（style template）** | layout_rules.py + yaml + huashu 风格 ✅ | baoyu-markdown-to-html（4 主题）⭐ | wenyan-core（3 主题）| 无 | huashu-md-html（4 反 slop 主题）| 30 套 CSS 主题 ⭐ | 自定义 CSS |
| **视觉层（cover/插图）** | baoyu-cover-image（已接）✅ | baoyu-cover-image ⭐ / baoyu-article-illustrator | 无 | 无 | huashu-wechat-image | 无 | 无 |
| **发布层（API/草稿箱）** | post_fengyun_publish.py（直推 API）✅ | baoyu-post-to-wechat（3 模式）⭐⭐ | wenyan-cli/mcp（API 草稿）⭐ | 无 | 无 | 有 API 草稿 | 无 API |
| **数据层（回流/飞轮/metric）** | **规划中（差异化）⭐⭐⭐** | 无 | 无 | 无 | 无 | 无 | 无 |
| **harness 编排（多步串联）** | fengyun-publish 9 步 LIVE ✅⭐⭐⭐ | 无（单 Skill 独立）| 无 | 无 | 无 | 无 | 无 |
| **三 perspective critic** | Musk + Jobs + 王小波 ✅⭐⭐⭐ | 无 | 无 | 无 | 无 | 无 | 无 |
| **信源聚合层** | 22 个 RSS（Phase 8 升 52）✅ | 无 | 无 | aihot（日报）| 无 | 无 | 无 |
| **主题数量** | 1（huashu）→扩展中 | 4 | 3 | 0 | 4 | **30** | 自定义 |
| **frontmatter 触发** | ✅（style: huashu）| ✅（theme + color）| ✅（frontmatter）| ❌ | ❌（CLI 参数）| ❌（CLI 参数）| ❌ |
| **开源许可证** | 私有 | 未见 LICENSE | Apache 2.0 | MIT | MIT | MIT | Apache 2.0 |
| **维护活跃度** | ✅ 高 | ✅ 高（每周更新）| ✅ 高 | 中 | ✅ 高 | ❓ 低 | ✅ 高 |

**我们的差异化点（他们没做的）：**
1. **harness 编排层**：所有竞品都是单 Skill 独立调用，我们是 9 步串联的编排器
2. **数据飞轮**：没有任何竞品在做「发布→阅读数回流→选题优化」的闭环
3. **三 perspective 内容评审**：Musk（物理约束）+ Jobs（整体灵魂）+ 王小波（中文语感）三路 critic，竞品无
4. **KOL 风格逆向工程**：从真实语料抽取 inline style → yaml 配置 → 分支渲染，竞品的「主题」都是自制，不是逆向 KOL
5. **frontmatter 驱动风格切换**：我们实现了 `style: huashu` 触发分支，tyrchen/wechat-pub-rs 有类似设计但 star 极少且 Rust 语言

---

## 5. 给风云的建议

### P0 立刻可接（≤1 天，高价值低成本）

1. **部署 wechat-article-exporter** 批量采集对标号文章 HTML（用 Docker 一键部署），用来持续扩充 corpus → 支撑后续更多 KOL 风格逆向。URL：https://github.com/wechat-article/wechat-article-exporter

2. **学习 baoyu-post-to-wechat 的 SSH SOCKS5 隧道方案**：如果将来上云（Phase 10-16），IP 白名单问题可以用这个方案解决，无需买固定 IP 服务器。参考：https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-post-to-wechat/SKILL.md

3. **把花叔 huashu-md-html 的 4 套反 AI slop 检查清单**移植进 fengyun_lint.py（排除：紫渐变、赛博霓虹色、深蓝底色 #0D1117、emoji 作正式图标），作为新增 lint 规则。

### P1 中期可考虑（1 周内，需要一定适配成本）

4. **从 xiaohu-wechat-format 的 30 套 CSS 主题里筛选 3-5 套**添加到我们的主题库，扩展 `style:` frontmatter 的可选值。重点看 Minimal/Elegant 系列（审美最接近 AI 圈调性）。

5. **接入 wenyan-cli 作为备用发布通道**：当我们自己的 `post_fengyun_publish.py` 出问题时，用 `wenyan publish -f article.md` 做 fallback。它的 frontmatter 结构兼容，对接成本低。

6. **参考 baoyu-markdown-to-html 的 EXTEND.md 三层优先级链**：在我们的 `layout_rules.py` 里加一层「系统默认」配置（目前只有文章级 frontmatter 控制），让多篇文章能共享默认风格而不用每篇都写 frontmatter。

### 不建议引入（理由）

7. **doocs/md**：Web 编辑器，需要人工操作，跟我们「全自动 harness」的定位冲突
8. **mdnice/markdown-nice**：停更迹象，且 Web 编辑器模式，无法 API 集成
9. **maxpress**：2018 年停更，JSON 单主题无切换，技术债太重
10. **lyricat/wechat-format**：作者已明确停维护，推荐用 Quaily 替代
11. **nexu-io/html-anything**：复制粘贴模式，无 API 草稿，跟全自动目标相悖

### 我们的差异化点（5 条核心护城河）

1. **harness 编排**：9 步串联是系统，竞品都是散装 skill，这是我们最大护城河
2. **数据飞轮**：唯一在做发布→回流→迭代闭环的方案
3. **三 perspective critic**：内容评审质量最高，竞品无此设计
4. **KOL 风格逆向**：从语料抽 inline style 的方法论独特，可以持续新增风格
5. **frontmatter 统一接口**：`style:` + `critic:` + `publish_time:` 等字段构成声明式控制层，是未来多风格/多平台扩展的基础

---

*调研 Agent：Claude Sonnet 4.6 | 2026-05-24*
*数据来源：GitHub 实时 fetch（当日数字）+ WebSearch 交叉验证*
*主要参考项目已全部提供 GitHub URL，可直接点击核实*
