# WRITE_AGENT.md · 风云 AI 公众号 ship pipeline 系统级宪法

**文档定位**:这是整个 ship pipeline 的**最高执行标准**,优先级高于任何 SKILL.md 描述。
**适用范围**:风云 AI 公众号「研究 Agent 的云」每一篇 ship。
**强制执行机制**:`tools/gate.py`(PreToolUse hook)+ `post_fengyun_publish.py` preflight assertion 双保险。
**版本**:v1.5 · 2026-05-25(Round 25 — 文内图强制必选 + placeholder fallback + spec-first 监督机制)
**写作前必读**:本文档,不读不允许动手 — 主线程 Claude 包括本人。

---

## 版本变更日志(读完才往下看)

### v1.5(2026-05-25 Round 25 — 文内图强制必选 + audit pass)

- **Step 7.2/7.3 强制必选**:任何 ship 必须 `image_paths` 非空 + 每张文件 size ≥ 5 KB
- **0 图 ship 路径删除**:旧 Round 9 `should_illustrate: false` 已废
  - `huashu-image-curator` skill 永远返回 `count ≥ 1`(即使灵魂建议 0 图也强制 1 张 fallback)
  - `illustrate_decider.py` 删 3 个 `return []` 路径
- **Seedream Fallback 链**:retry × 3 指数退避(`time.sleep 1s/2s/4s`)→ daily_quota → `assets/placeholder-sketch.png` × N
- **gate.py 物理硬约束**:`image_paths` 必填非空 + 文件存在 + size ≥ 5 KB
- **`image_generation_degraded=true` 已废**:Seedream 失败走 placeholder,不再 degraded ship
- **audit 修复**(Newton/Musk 二轮 review 后补):
  - Bug B1:`illustrate_decider` docstring 旧示例 `else: image_paths = []` 删
  - Bug B2:`write_metadata` 入口 `assert image_paths` fail-fast
  - Bug B3:3 个 placeholder fallback 路径强制写 `image_at_h2_indices`(防 gate 自阻塞)
  - Bug B4:`fallback_reason` 字段写入 frontmatter(audit trail)
  - G5:retry 真实现 `time.sleep` 指数退避(原 SPEC 描述无代码实现)
  - 字段重命名 `_zero_reason/_round25_placeholder → fallback_reason`(去版本号前缀)
  - placeholder 视觉重做:删「图片生成中」文案 + 删「云」签名 + 删内部 metadata,改抽象 sketch
- **开发监督机制(三人共识)**:spec-first + CI 测试 + 关键节点 diff review,不开会

### v1.4(2026-05-25 Round 24 — 全自动化升级)

> Musk × Jobs × Newton 共识:北极星红线只在草稿箱审阅那一刻。pipeline 内部不再因「等真人确认」停下。

- **Step 1.1 删用户确认**:`topic_recommender` 排序后自动选第 1,pass_flag `user_confirmed_topic` → `auto_selected_topic`(无 binary verdict 阻塞)
- **Step 1.5 删 fallback 真人**:dogfood gate confidence < 0.7 → 自动 `degraded: true` + continue,不再 print 等回答
- **Step 6.5.8 自动出口**:原 human_gate 已废,改自动判:
  - 3 轮未过 + A ≥ 65 → `auto_partial_pass: true`(ship)
  - 3 轮未过 + A <  65 → `auto_abort: true`(终止 pipeline)
- **gate.py REQUIRED_PASS_FLAGS** 加 `auto_partial_pass / auto_abort` 作为合法 pass_flag(任一为 true 即满足 critic 类要求)
- **fengyun-self → content-judge 重命名**:Track C critic skill 改名(原 skill 是「风云本人 decision perspective」,Round 24 重新定位为「独立第三方评委」)。引用 `critic_c_source` 描述同步更新

### v1.3(2026-05-25 Round 23 — huashu 高亮 2 bug)
- **Bug 1 punct 错位**:`_fix_cjk_bold_punctuation` 拆分末尾(激进 ASCII 全套)+ 开头(保守只引号/冒号)集合,加 lookbehind 防 `**A**,**B**` 连续 bold 误判
- **Bug 2 高亮过密**:新增 R26(每段 bold ≤ 1)+ R27(全文 ≤ 5,短文 ≤ 3),Musk × Jobs 物理约束(working memory + spotlight)。**用户偏好「比花叔更克制」**:花叔 corpus 抽样 20% 篇单段 ≥ 2 处 / 40% 全文 > 5 处,Round 23 主动选择更严的阈值

### v1.2(2026-05-25 Round 22 收尾)
- **Round 22 P0-6**:gate 防伪扩面到 8 项(原 critic 三轨 + Round 21 humanizer/wangxiaobo + Round 22 新增 writer / huashu_image_curator) — 主线程任何 step「假装跑 skill」都会被当场抓
- **Round 22 #1**:`iti_collect.py` 默认写 `output/candidates/YYYYMMDD.json`,Step 1.x 可读
- **Round 22 #2**:`event_dedup` 扫两个 source(drafts + runs 含 media_id 的存档),解决「已发还推荐」
- **Round 22 #5**:`iti_explore.py` CLI 新增 `--main-source-urls`,Step 2 WebSearch 找的 URL 可显式注入
- **Round 22 #3**:Step -1 / 0 / 0.1 编号歧义澄清 + 允许「TBD 占位 + Step 1.1 后回填」

### v1.1(2026-05-25 Round 21)
- **Round 21 决策 1**:排版统一花叔 — `--render-mode legacy` 砍 + `style=default/classic` 分支砍(78 行 + 13 个 helper)。**huashu 是唯一活跃渲染路径**
- **Round 21 决策 2**:封面 + 内文图风格强制一致 — `generate_cover_by_template.py` 出 `<slug>-cover.style_anchor.txt` sidecar,Step 7.2 huashu-image-curator 必须读这个 anchor 作为输入
- **Round 21 P0-14**:`illustrate_decider` 加 SetLimitExceeded / safe_experience 关键词(火山新错误码)
- **Round 21 P0-16**:`gate.py parse_frontmatter` 支持多行 YAML list(image_paths / image_at_h2_indices)
- **Round 21 P0-9**:gate 防伪加 humanizer / wangxiaobo
- **Round 21 P0-4**:`opening_signal` reframe regex 允许空格 / 逗号
- **Round 21 P0-17**:layout_rules HTML 上限 20000 → 60000(对齐微信真实 65000 物理上限);fengyun_lint 加 R12b html_size_warn

### v1.0(2026-05-25 Round 17 落地)
- 系统宪法首版 + gate.py PreToolUse hook + 19 step 全流程颗粒度

---

## ⛔ 北极星红线(NORTH_STAR)— 永不变

> **最终人工动作只有一个:风云在公众号草稿箱审阅 + 手动发出。**

任何环节的「自动决策 / 自动 ship」不得替代这条。gate 拦的是「半成品推草稿」,不是风云的最终一击。

---

## ⛔ Preflight 红线 — 系统启动前置自检(2026-05-25 v1.0 落地)

> **每次「开始用系统」前必跑 `.\tools\preflight.ps1`,P0 全绿才允许进入任何 Step。**

### 为什么有这条红线

整套链路是 7 个独立服务的**串联**(Docker → we-mp-rss → cookie → TrendRadar → HF Spaces RSSHub → Email-to-RSS Worker → 公网 RSS)。任意一环挂掉 fengyun-publish 都会**静默 degraded**(信源数减少但不 abort),最终推到草稿箱的文章信息不全 / 角度偏。

2026-05-25 实测发现:Docker Desktop 没开 + TrendRadar 3 天没跑 + rsshub.app 公共实例对本机 IP 403 → 这三件事**任何一件单独发生**,文章质量都会肉眼可见地下降,但 pipeline 不会停。所以**必须前置 hard check**,把"系统启动"这一步本身物理化。

### Preflight 7 项检查

| # | 项 | 优先级 | 失败 = 后果 |
|---|---|---|---|
| 1 | Docker Desktop daemon | **P0** | 整套链路死透 |
| 2 | we-mp-rss 容器 (localhost:8001) | **P0** | 16 个公众号 feed 全空 |
| 3 | we-mp-rss cookie 新鲜度(抽 1 feed 看 entry) | **P0** | 即使容器活,cookie 死也拉空 |
| 4 | TrendRadar `latest_daily.md` mtime ≤ 36h | **P0** | iti_collect 跳过这个信源,选题候选池减少 1/6 |
| 5 | 本机 RSSHub 容器(localhost:1200)+ B/知乎 cookie 双测 | **P0** | 7 个 B 站/知乎 feed 503 拉空(2026-05-26 HF Spaces 路径已 deprecated:HF 中国大陆 IP 返回 418) |
| 6 | Email-to-RSS Worker(配置后激活) | P1 | Substack 私有 newsletter 拿不到 |
| 7 | `rsshub.app` 公共实例(已知挂,提醒用) | P1 | 提示自建迁移进度 |

### 强制执行机制

| 层 | 机制 |
|---|---|
| **L1 lint 层(本红线)** | `.\tools\preflight.ps1` 跑出 P0 FAIL → 退出码 1 → 主线程禁止进入 fengyun-publish Step 1 |
| **L2 hook 层** | `tools/gate.py` PreToolUse 在 ship 推草稿前再抽 1 项 P0 复查(防止启动后服务挂掉) |
| **L3 人格层** | 主线程 Claude 必读本红线;任何「我先跳过 preflight 直接开干」的行为视同破坏宪法 |

### 救场命令(常见 P0 失败)

```powershell
# Docker Desktop 没开
# → 系统托盘点 Docker 图标启动 GUI;等鲸鱼变绿(约 10-30 秒)

# we-mp-rss 容器没跑
docker start we-mp-rss
# 或首次部署
docker run -d --name we-mp-rss -p 8001:8001 ghcr.io/rachelos/we-mp-rss:latest

# cookie 过期(约 80 小时一次)
# → 浏览器开 http://localhost:8001 重新扫码

# TrendRadar latest_daily.md 过期
# 推荐入口(已修 Windows GBK 编码 emoji 崩):
.\tools\run_trendradar.ps1
# 或后台跑:
.\tools\run_trendradar.ps1 -Background
```

### 部署完 HF Spaces / Email-to-RSS 后

把 URL 填进 `tools/preflight.ps1` 顶部的 `$HF_RSSHUB_URL` / `$EMAIL_RSS_URL` 两个变量,**P1 项自动从 SKIP 升为实际检查**。

### 关联

- 一键脚本:`tools\preflight.ps1`
- HF Spaces 部署指南:`docs\rsshub_hf_spaces_setup.md`
- Email-to-RSS 部署指南:`docs\email_to_rss_setup.md`
- 信源现状报告:`reports\phase17_*.md` 4 份

---

## ⛔ 商业机密三级红线(R18)— 永不变

P0(致命) → 立即 abort,不进任何兜底:
1. 自暴 AI 生成(「本文由 AI 写 / 作为 AI / Claude 帮我写」)
2. 自暴架构(harness / writer / critic / lint / 三轨 / vote / 飞轮 / pipeline)
3. 自暴 skill 名 / 模型名 / prompt 配方
4. 自暴工具栈(「我的豆包 / 我的 DeepSeek / 我的 Cloudflare Worker」)
5. 自暴自动化(「自动 ship / cron 发布」)

P1 / P2 严重度递降,但任何级别命中都不允许过 gate。

---

## 全流程 19 个 Step 总览

**编号约定(Round 22 #3 澄清)**:
- **Step -1 / 0 / 0.1 全是「写作前置层」L0** — 不管负号还是 0,**全部都是 ship 开始的第一批动作**,顺序就是文档列出的(L0 → L1 → L2 ...)。负号**不是「在 0 之前才存在」**,而是「比 0 更先于内容(选题前的元意图)」的语义标记。
- 流程实际执行顺序:Step -1(填北极星) → Step 0(读 voice-dna) → Step 0.1(style 路由) → Step 1.0(广搜) → ...
- 隔壁 e2e 实测发现 Step -1 可能要在 Step 1.x 选定主题后才能填(因为不知道主题没法填北极星)。**这种情况允许「占位 + 回填」**:Step -1 先用「TBD」占位通过 gate,选完主题后回 Step -1 真填(runlog 记录回填动作)。

```
Step -1   北极星填空(BLOCKING,允许 TBD 占位 + Step 1.1 后回填)
Step 0    Voice DNA + corpus 必读(BLOCKING)
Step 0.1  Style 路由(Round 21 后 huashu 唯一活跃路径,default/classic 已砍)
─── 选题层(ITI 第一段)───
Step 1.0  ITI I-1 广搜聚合候选(BLOCKING)
Step 1.x  topic_recommender 排序 + event_dedup 去重(BLOCKING)
Step 1.1  选定单一主题 + entities + slug
─── 试稿层 ───
Step 1.5  dogfood gate + opening harness(BLOCKING,上限 3 retry)
─── 调研层(ITI 第二段)───
Step 2    ITI I-2 深搜调研 → research.md(BLOCKING)
─── 写作层 ───
Step 3    fengyun-writer 写完整稿 4000-5000 字(BLOCKING)
Step 3.3  标题 harness(BLOCKING,上限 3 retry)
Step 3.5  ending harness(BLOCKING,上限 3 retry)
─── 清洁层 ───
Step 4    fengyun_lint 机械层(BLOCKING)
Step 4.5  humanizer-zh 去 AI 味(BLOCKING)
Step 5    wangxiaobo-perspective 语感预审(BLOCKING)
─── 评审层 ───
Step 6    三轨 critic vote(BLOCKING)
Step 6.5  critic-revise loop(条件 BLOCKING,上限 3 轮)
Step 6.5.8 human_gate(只在 3 轮未过)
─── 视觉层 ───
Step 7.1  函数预筛内文图候选位置
Step 7.2  花叔 Mode 2 配图决策(BLOCKING)
Step 7.3  内文图 Seedream 生成 + write_metadata(BLOCKING)
Step 7-cover 封面生成 + cover_dedup(BLOCKING)
─── 出版层 ───
Step 8    layout_rules 渲染 + post_fengyun_publish(BLOCKING · gate 守门)
Step 9    报告 + audit log
```

---

## Step -1 · 北极星填空

**触发**:任何 ship 开始的第一动作。

**输入**:用户的主题描述。

**执行**:写下 `读完应该感受到 ____` 一句话填空(≤ 30 字)。

**输出**:`output/runs/<slug>.runlog.jsonl` 第一行 `{"step": -1, "north_star": "..."}`

**BLOCKING**:不填,所有后续 step 全部 abort。

**pass_flag**(frontmatter):`north_star: "..."`

**失败回退**:无 — 必须填。

---

## Step 0 · Voice DNA + corpus 必读

**触发**:Step -1 通过后。

**输入**:`~/.claude/skills/fengyun-writer/references/voice-dna.md` + `~/.claude/skills/fengyun-writer/corpus/growth/*.md`

**执行**:
1. Read voice-dna.md 完整版
2. 随机 Read 3-5 篇 corpus 文章

**输出**:仅上下文加载,无文件产物。

**BLOCKING**:跳过 = 用 Claude 默认语调 = 失败。

**pass_flag**(runlog):`{"step": 0, "voice_dna_loaded": true, "corpus_samples": ["A.md", "B.md", "C.md"]}`

**失败回退**:无。

---

## Step 0.1 · Style 路由

**触发**:Step 0 完成后。

**输入**:用户偏好(默认 huashu)。

**执行**:决定 frontmatter `style:` 字段。
- 不写 → 默认 huashu(花叔暖象牙 + 陶土橙,**当前默认**)
- `style: huashu` + `theme: A|B` 显式
- `style: default` opt-out 回原蓝灰

**输出**:无(暂存待写 frontmatter)。

**pass_flag**:`style_routed: true`(frontmatter 在 Step 3 创建时一并写)

---

## Step 1.0 · ITI I-1 广搜

**触发**:Step 0.1 完成后。

**输入**:用户主题词或「拉今天热点」。

**执行**:
```bash
# Round 22 #1 升级:iti_collect 默认写 output/candidates/YYYYMMDD.json
python tools/iti_collect.py --hours 24
# 可指定 --out 自定义路径,或 --no-write 只 stdout
# 同时主线程必跑 WebSearch 中英文各 1-2 次补位
```

主线程调用 `aihot` skill 拉 24h 精选 + `iti_collect.py` 拉 6 信源(aihot + we-mp-rss + TrendRadar + arxiv + smol.ai + WebSearch)。

**输出**:
- `output/candidates/YYYYMMDD.json`(Round 22 #1 默认路径,Step 1.x topic_recommender 读这个)
- 候选 ≥ 10 条(硬约束),目标 15-25 条(甜蜜点),上限 30 条

JSON schema:`{generated_at, hours_window, n_total, n_unique, degraded, sources_ok, sources_failed, stats_per_source, items: [...]}`

**BLOCKING**:候选 < 10 → 主线程必须再跑 WebSearch 补足。

**pass_flag**(runlog):`{"step": "1.0", "candidates_n": 22, "sources": ["aihot", "we-mp-rss", ...], "candidates_json": "output/candidates/YYYYMMDD.json"}`

**失败回退**:某个信源挂 → 跳过该信源,但总数仍要 ≥ 10。

---

## Step 1.x · topic_recommender 排序 + event_dedup 去重

**触发**:Step 1.0 完成后。

**输入**:候选 JSON。

**执行**:
```python
from tools.topic_recommender import rank_aihot_candidates
from tools.event_dedup import check_event_dedup

ranked = rank_aihot_candidates(candidates)  # PHASE1 数据驱动评分
for item in ranked[:5]:
    # Bug 4 注释(Round 17):Step 1.x 时还没写 draft,无自身可排除 → 不传 current_draft_path
    # Round 22 #2 升级:include_published=True 默认开启,扫 drafts/ + runs/*.json 有 media_id 的存档
    ddp = check_event_dedup(item, days=7, include_published=True)
    if not ddp["is_duplicate"]:
        chosen = item; break
```

**输出**:`chosen_candidate` 单条 dict + entities 提取。

**BLOCKING**:event_dedup 7 天内撞型 → 弃用该候选,选下一个。

**Round 22 #2 升级**:event_dedup 现在扫两个 source —
1. `output/drafts/*.md` 最近 days 天 mtime 的草稿
2. `output/runs/*.json` 含 media_id 字段的已发布存档(避免「TrapDoor 已发还推荐」)

**pass_flag**(runlog):`{"step": "1.x", "chosen_title": "...", "event_dedup_pass": true}`

**Round 17 验证结果**(2026-05-25):此前怀疑的「score 全 0」**误诊** — cli_demo 实测候选评分正常分布 0.08-1.00,aihot 字段名 `title`/`summary` 跟 `rank_aihot_candidates` 取值一致,逻辑无 bug。继续正常使用。

---

## Step 1.1 · 自动选题 + slug + entities

**触发**:Step 1.x 完成后。

**输入**:chosen_candidate(`topic_recommender` 排序 + `event_dedup` 过滤后的 top 1)。

**执行**(Round 24:全自动,不等用户):
1. 主线程提取 slug(`yyyymmdd-<key-words>` 格式)
2. 提取 entities(2-5 个核心关键词)
3. **直接采用 ranked top 1**(`topic_recommender` 已给出客观排序;`event_dedup` 已过滤 7 天撞型)
   - 用户介入只在最终草稿箱审阅那一刻(NORTH_STAR 红线)— pipeline 内部不再等 binary verdict

**输出**:`output/runs/<slug>.runlog.jsonl` 写 `{"step": "1.1", "slug": "...", "entities": [...], "auto_selected": true, "selection_rank": 1}`

**BLOCKING**:`event_dedup` 全 7 天撞型(连备选都撞)→ 报警 + auto_abort;非用户确认问题。

**pass_flag**:`auto_selected_topic: true`(取代原 `user_confirmed_topic`)

---

## Step 1.5 · dogfood gate + opening harness

**触发**:Step 1.1 完成后。

**输入**:slug + entities + north_star。

**执行**:
1. 调 `fengyun-writer` skill 出 200 字试稿开头(只开头,不完整稿)
2. 跑 `score_opening_signal()` 5 维评分(物理约束 + 4 信号 + R28 公式新鲜度)
3. 跑 `check_opening_overlap()` 30 天回看 dedup
4. **content-judge skill** binary verdict「这是不是风云会写的开头」(原 fengyun-self,Round 24 改名为独立第三方评委)
5. 任一 fail → revise → 上限 3 retry

**评分阈值**:
- 物理约束:首段 ≥ 50 字 + 第一人称密度 ≥ 5/千字
- 5 维:每维 ≥ 6/10
- dedup:token Jaccard ≤ 0.30 + 5-gram ≤ 0.20
- 公式新鲜度:撞型 buckets ≤ 1

**输出**:`output/runs/<slug>_opening_v{1-3}.md`(每轮试稿)+ 最终 200 字试稿。

**BLOCKING**:3 轮都 fail → 走 partial_pass(用最后一版,记 degraded)。

**pass_flag**(frontmatter):`dogfood_pass: true`(content-judge 挂名意愿 = yes 才算 pass)

**Round 24 自动出口(取代旧 fallback 真人)**:
- content-judge 输出 confidence < 0.7 → frontmatter 写 `dogfood_pass: true` + `dogfood_degraded: true` + `dogfood_degraded_reason: "content-judge confidence=<x> < 0.7"`,**自动继续**不等用户回答
- content-judge skill 不存在 → 同样自动 degraded continue(`dogfood_degraded_reason: "content-judge skill missing"`)
- pipeline 内部任何 confidence 不足的判断都走 degraded continue,不阻塞 ship。最终人工动作只在草稿箱审阅那一刻(NORTH_STAR 红线)。

---

## Step 2 · ITI I-2 深搜调研

**触发**:Step 1.5 dogfood 通过。

**输入**:slug + entities + chosen_candidate。

**执行**(**严禁主线程偷懒手工组装**,必须真调):
```python
from tools.iti_explore import explore_topic
# 主线程必跑 WebSearch ≥ 4 次(中英文各 2 次)
ws_items = [...]
main_urls = [item["url"] for item in ws_items[:4]]

result = explore_topic(
    slug=slug, title=title, entities=entities, main_source_urls=main_urls
)
# result["facts"] = 本地 + API 拉到的事实(corpus grep / arxiv / topic_hotness / we-mp-rss / safe_webfetch)
```

**CLI 用法(Round 22 #5 升级,新增 --main-source-urls)**:
```bash
python tools/iti_explore.py <slug> <title> \
    --entities Anthropic Karpathy pre-training \
    --main-source-urls https://example.com/a https://example.com/b
```

**输出**:`output/research/<slug>.md`,含:
- 北极星(从 Step -1)
- 核心事件 3 句话摘要
- **5-10 条带 URL 的事实清单**(不是 manual 凑数)
- 3-5 条「我的角度可以是 ___」候选

**BLOCKING**:facts 少于 5 条 → 必须再跑 WebSearch / WebFetch 补足。

**pass_flag**(runlog):`{"step": 2, "research_facts_n": 12, "research_path": "output/research/<slug>.md", "websearch_count": 4}`

**失败回退**:某个 API 挂 → safe_webfetch UA 轮换 + retry × 2。

---

## Step 3 · fengyun-writer 写完整稿

**触发**:Step 2 完成 + research.md 存在 + facts ≥ 5。

**输入**:research.md + north_star + style 路由。

**执行**:invoke `fengyun-writer` skill 完整写作模式。

**输出**:`output/drafts/<slug>-v0.md`,字数 4000-5000(硬约束)。

frontmatter 必带:
```yaml
title: "..."
digest: "..."
author: "研究Agent的云"
slug: "..."
date: "yyyy-mm-dd"
style: huashu  # 或不写默认 huashu
north_star: "..."  # 从 Step -1
```

**BLOCKING**:
- 字数 < 4000 或 > 5000 → revise
- R18 P0 命中 → abort
- 5-6 个 H2 章节缺失 → revise
- 金句标注 < 3 处 → revise(R28 强制):writer 必须在写作时用 `**...**` 标注 3-5 处核心金句(读者可以「带走」的句子:核心洞察 / 情感锚点 / 收尾金句)。**不是事后手动补,是 writer 在 Step 3 写作时就标好**。lint R28 会在 Step 4 检查,低于 3 处直接阻断

**pass_flag**(frontmatter):
- `writer_pass: true` + `writer_word_count: 4200`
- **Round 22 P0-6 防伪扩展**(必填,gate 强制):
  - `writer_real_run: true` — **必须真 invoke fengyun-writer skill**,不许主线程拍脑袋写
  - `writer_source: "fengyun-writer skill 3 retry round=1"` — 真实出处描述(版本/round/时间戳)
- gate 看到 `writer_pass: true` 但缺 `writer_real_run / writer_source` → fake-pass 防伪触发 → 阻断 ship

**失败回退**:fengyun-writer skill 不存在 → 降级到 khazix-writer(且后续 critic 切单轨)。

---

## Step 3.3 · 标题 harness

**触发**:Step 3 完成。

**输入**:draft frontmatter title + topic entities + body word count。

**执行**(上限 3 retry):
```python
from tools.title_signal import score_title
from tools.title_dedup import check_title_overlap

for attempt in range(3):
    sig = score_title(title, topic_keywords=entities, body_chars=body_chars)
    # Bug 4 修复(Round 17):Step 3.3 时 draft 已存在,传 current_draft_path 排除自身
    ddp = check_title_overlap(
        title, hook_type=sig.get("hook_type"),
        current_draft_path=draft_path,
    )
    if sig["verdict"] == "pass" and not ddp["is_too_similar"]:
        break
    # writer 改标题(只改 frontmatter,不改正文)
    title = invoke_writer_change_title(draft, old_title=title, feedback=sig["redo_feedback"])
```

**评分**(总分 100,≥ 65 PASS):
- 字数 ∈ [20, 40](20 分)
- 数字组数 ≤ 1(10 分)
- 命中 PHASE1 7 钩子任一(20 分)— **Round 17 改为 hard gate**
- 品牌词白名单(20 分,主题相关时)
- 反品牌词黑名单(20 分,扣分)
- 4 共同特质 ≥ 2/4(10 分)

**BLOCKING**:3 轮不过 → 用最后一版。

**pass_flag**(frontmatter):`title_pass: true` + `title_hook: "颠覆认知"` + `title_score: 95`
- **Round 25 防伪**(gate 强制):
  - `title_real_run: true` — 必须真跑 title_signal.py + title_dedup.py
  - `title_source: "title_signal score=X, hook_type=Y, dedup pass"` — 真实评分证据

---

## Step 3.5 · ending harness

**触发**:Step 3.3 完成。

**输入**:draft 全文。

**执行**(**严禁偷懒只 import**):
```python
from tools.ending_signal import score_ending_signal
from tools.ending_dedup import check_ending_overlap

esig = score_ending_signal(text)
# Bug 4 修复(Round 17):Step 3.5 时 draft 已存在,传 current_draft_path 排除自身
eddp = check_ending_overlap(
    text, max_age_days=30, max_n_check=5,
    current_draft_path=draft_path,
)
# 不通过 → revise 末段(只改末段)
```

**BLOCKING**:撞「愿你也能 + 颜文字」公式 → revise。

**pass_flag**(frontmatter):`ending_pass: true`
- **Round 25 防伪**(gate 强制):
  - `ending_real_run: true` — 必须真跑 ending_signal.py + ending_dedup.py
  - `ending_source: "ending_signal score=X, dedup pass"` — 真实评分证据

---

## Step 4 · fengyun_lint 机械层

**触发**:Step 3.5 完成。

**输入**:draft path。

**执行**:
```python
from tools.fengyun_lint import lint_article
r = lint_article(draft_path)
violations = r["violations"]
# high severity > 0 → revise
```

**已知 bug**(Round 17-23 全修):
- R0 半角标点误报技术标识符 `.env / .md / .cursorrules`
- R8 / R13 关于「替代」自相矛盾(Round 19 P0-5 修)
- R12 vs HTML 上限 20000 结构性冲突(Round 21 P0-17 修:HTML 上限抬到 60000)
- **Bug 1 标点错位(Round 23 修,2026-05-25)**:`**xxx**` 高亮框前的 ASCII 引号 / 半角冒号被吸进框。修法:`_fix_cjk_bold_punctuation` 用拆分集合 — 末尾踢出激进(全套 ASCII + 全角),开头踢出保守(只全角 + ASCII 引号 + 冒号,避免 `**A**,**B**` 连续 bold 误判)
- **Bug 2 高亮过密(Round 23 修,2026-05-25)**:新增 R26 + R27 双密度规则。Musk × Jobs 共识硬约束:每段 bold ≤ 1 处 + 全文 ≤ 5 处(短文 < 1000 字按比例缩放到 ≤ 3)

**Round 21 P0-17 新增 R12b**:`html_size_warn` — markdown × 5 倍膨胀估算超 50000 → low severity warn(不阻断,但提示离 60000 硬上限近)

**Round 23 新增 R26 / R27**:
- `R26_huashu_bold_per_para`(medium):每段 bold ≥ 2 处 → 阻断 ship。物理依据:单段注意力 spotlight 1 chunk
- `R27_huashu_bold_total`(medium):全文 bold > 5 处(短文 > 3 处)→ 阻断 ship。物理依据:working memory 4±1 chunk 上限
- 跟 R21_bold_ai_padding 互补不替代:R21 看全文总数 + 平均长度;R26 看单段;R27 看全文上限

**Round 24 新增 R28(B 类长文粗体下限)**:
- `R28_huashu_bold_minimum`(medium):B 类长文(≥ 3000 总字数)全文 bold < 3 处 → 阻断 ship
- 跟 R27 互补:R27 设上限(防堆砌),R28 设下限(防裸文)
- e2e 实测发现:主线程跳过内文图后连带跳过 bold 意愿。R28 确保长文至少有 3 处核心金句
- Round 25 修:阈值从 3500 CJK 降为 3000 总字数(技术文 CJK 占比低,如 TrapDoor 文 4358 总字但仅 2810 CJK,原阈值漏检)
- 短文(< 3500 字)不触发,R26 段密度兜底即可

**BLOCKING**:high severity > 0 → revise。**partial_pass 允许**:连改 3 轮还 high → 走 6.5 partial_pass + 记 degraded。

**pass_flag**(frontmatter):`lint_pass: true` 或 `lint_partial_pass: true` + `lint_high_count: 0`

---

## Step 4.5 · humanizer-zh 去 AI 味

**触发**:Step 4 通过(或 partial_pass)。

**输入**:draft 全文。

**执行**:invoke `humanizer-zh` skill。返回去 AI 味后的版本。

**输出**:更新 draft(增量 replace,不是整篇重写)。

**BLOCKING**:**严禁主线程跳过**(Round 17 hook 拦截)。

**pass_flag**(frontmatter):
- `humanizer_pass: true` + `humanizer_version: "wikipedia-signs-of-ai-writing-2025"`
- **Round 21 P0-9 防伪**(必填,gate 强制):
  - `humanizer_real_run: true` — **必须真 invoke humanizer-zh skill**
  - `humanizer_source: "humanizer-zh skill v1, applied N changes"` — 真实出处 + 改动数
- gate 看到 `humanizer_pass: true` 但缺 `humanizer_real_run / humanizer_source` → fake-pass 防伪触发 → 阻断 ship

**失败回退**:humanizer-zh skill 不存在 → 降级到 humanizer(英文版,作用有限)。

---

## Step 5 · wangxiaobo-perspective 语感预审

**触发**:Step 4.5 完成。

**输入**:draft 全文。

**执行**:invoke `wangxiaobo-perspective` skill。

**输出**:王小波诊断报告(≤ 300 字),含具体翻译腔位置 + 母语替代。

**BLOCKING**:发现翻译腔 → 主线程必须按建议修正,然后 re-invoke 验证 pass。

**pass_flag**(frontmatter):
- `wangxiaobo_pass: true` + `wangxiaobo_revisions: 2`(改了几处)
- **Round 21 P0-9 防伪**(必填,gate 强制):
  - `wangxiaobo_real_run: true` — **必须真 invoke wangxiaobo-perspective skill**
  - `wangxiaobo_source: "wangxiaobo-perspective skill, found N translation-tone hits"` — 真实出处
- gate 看到 `wangxiaobo_pass: true` 但缺 `wangxiaobo_real_run / wangxiaobo_source` → fake-pass 防伪触发 → 阻断 ship

---

## Step 6 · 三轨 critic vote

**触发**:Step 5 通过。

**输入**:draft 全文 + Step 5 pass 状态。

**执行**(**严禁主线程偷懒**):
```python
# Track A: critic v2.1 数字分(0-100)
from tools.sop_v2_1 import score_draft as critic_a
score_a = critic_a(draft_path)

# Track B: huashu-perspective binary
# invoke huashu-perspective skill → ship/not_ship + 灵魂位置

# Track C: content-judge skill binary(Round 24 改名,原 fengyun-self)
# invoke content-judge → 挂名意愿 yes/no(独立第三方评委,不再代表用户本人)

# 门控树
from tools.critic_vote import gate_tree
verdict = gate_tree(score_a, b_verdict, c_verdict)
# ship / revise / human_gate / aborted_r18
```

**BLOCKING**:任一 R18 P0 命中 → aborted_r18,强制人工。

⚠️ **全流程不中断**:三轨 vote 必须在同一轮消息内连续完成(Track A → B → C),
不许在 Track A 输出后停下来等用户。三轨完成后直接进入 gate_tree 判定,
不许中间暂停。

**pass_flag**(frontmatter):
- `critic_vote_pass: true`(verdict = ship)
- `critic_a_score: 72`
- `critic_b_verdict: "ship"`
- `critic_c_verdict: "ship"`
- **Round 18 P0-1 fake-pass 防伪**(必填,gate 强制 — `critic_vote_pass=true` 时必查):
  - `critic_a_real_run: true` — **必须真跑 sop_v2_1.score_draft()**
  - `critic_b_real_run: true` — **必须真 invoke huashu-perspective skill**
  - `critic_b_source: "huashu-perspective skill v1, ship verdict, 灵魂 ✓"` — 真实出处 + binary verdict
  - `critic_c_real_run: true` — **必须真 invoke content-judge skill**(Round 24 改名,原 fengyun-self)
  - `critic_c_source: "content-judge skill, 挂名意愿 yes, ..."` — 真实出处
- gate 任一缺失 → fake-pass 防伪触发 → 阻断 ship
- **审计实证**(2026-05-25):此防伪当场抓住主线程之前的 fake-pass(三轨 verdict 直接拍脑袋写「ship」没真调 skill)

---

## Step 6.5 · critic-revise loop

**触发**:Step 6 verdict = revise。

**输入**:critic 反馈 + draft。

**执行**:
1. 生成 `revise_brief.md`(critic 反馈 → 具体段落改稿指南)
2. invoke fengyun-writer skill「改稿模式」(±10% 字数硬约束,不大改重写)
3. 重跑 Step 4 → 4.5 → 5 → 6
4. 上限 3 轮

**BLOCKING**:
- 3 轮未过 → 走 Step 6.5.8 human_gate
- R18 P0 命中 → aborted_r18 立即跳出

**pass_flag**(frontmatter):`revise_rounds: 0/1/2/3` + `revise_loop_pass: true`

---

## Step 6.5.8 · 自动出口(原 human_gate 已废)

**触发**:Step 6.5 三轮 revise 仍未过 critic vote。

**执行**(Round 24,不再等真人):
看末轮 Track A 综合分(critic_v2.1 total):

| 末轮 A 分 | decision | pass_flag |
|---|---|---|
| `A ≥ 65` | `ship`(走 auto_partial_pass 兜底) | `auto_partial_pass: true`(进 Step 7 封面)|
| `A <  65` | `abort`(终止 pipeline) | `auto_abort: true`(不进 Step 7/8,runlog 标终止)|
| `A` 缺(工具链断)| `abort` | `auto_abort: true` + `reason: "末轮 A 缺"` |

**实现位置**:`tools/critic_vote.py::_auto_exit_result()` 函数,3 轮 revise 后或末轮 gate_tree 判 human_gate 时统一调用。

**BLOCKING**:无 — Round 24 不再为人工裁决暂停;最终人工动作只在草稿箱审阅那一刻。

**pass_flag**(frontmatter):`auto_partial_pass: true` 或 `auto_abort: true`(二选一)+ `auto_exit_reason: "<critic_vote.py 返回的 reason>"`

**理论依据(Musk × Jobs × Newton 共识)**:
- Musk: pipeline 物理上不该停 — 真过 vs 兜底走两条不同的 jsonl 飞轮记录,事后回查
- Jobs: force_skip 警报已加(P1-1),auto_partial_pass 跟 critic_vote_pass 不同字段,审计可追
- Newton: 不变量是「最终一击在草稿箱」,中间所有 gate 都是工具不是人

---

## Step 7.1 · 函数预筛内文图候选

**触发**:Step 6 verdict = ship(或 6.5 partial_pass)。

**输入**:draft 全文。

**执行**:
```python
from tools.illustrate_decider import pick_candidates
candidates = pick_candidates(article_md, min_para_chars=80)
# 函数预筛 H2 + 段落 ≥ 80 字
```

**输出**:候选 list[Position](h2_idx / h2_title / position_idx / paragraph_preview / word_count)。

**pass_flag**(frontmatter):`illustration_candidates_n: 6`

---

## Step 7.2 · 花叔 Mode 2 配图决策

**触发**:Step 7.1 完成。

**输入**:draft 全文 + candidates + 可选 style_anchor。

**执行**(**严禁主线程偷懒跳过**):invoke `huashu-image-curator` skill Mode 2,输出 JSON:

⚠️ **Round 25 强制必选(2026-05-25 用户方案 A)**:**图片不再是「可选项」,也不是「0 图也合法」**。
- 不论 R20 lint 结果如何,不论 article_type 是什么,Step 7.1 → 7.2 → 7.3 必须完整执行
- **0 图路径已删**:花叔 skill 永远返回 `should_illustrate=true, count ≥ 1`(灵魂建议 0 图时也强制 1 张 fallback)
- **没调花叔就跳过 = 违规**:gate.py 强制检查 `huashu_image_curator_real_run` + `huashu_image_curator_source` 模式匹配
- **全流程不许中断**:7.1 → 7.2 → 7.3 连续执行,不在中间等用户确认
```json
{
  "should_illustrate": true,
  "count": 3,
  "style_anchor": "warm sketchnote ...",
  "image_at_h2_indices": [1, 3, 5],
  "positions": [...],
  "prompts": ["...", "...", "..."],
  "alts": [...],
  "self_check": {...}
}
```

**BLOCKING**(Round 25 升级):
- skill 不存在 → abort(不再允许 0 图 ship,旧 Round 9 决策已废)
- R18 P0 命中 prompt → abort
- skill 返回 `should_illustrate: false` → `illustrate_decider.py` 强制 placeholder fallback(双保险)

**Round 21 决策 2:封面 + 内文图风格强制一致** —
调 huashu-image-curator 之前先读 `<cover-image>.style_anchor.txt`(Step 7-cover 输出的 sidecar),把这个 anchor 作为 `style_anchor` 输入传给花叔。花叔输出的 style_anchor **必须等于或扩展自封面 anchor**(基底:warm sketchnote / cream paper #F8F0E0 / terracotta #D97757 / cloud signature),不允许另起炉灶。

```python
cover_anchor_path = OUT_DIR / "images" / f"{slug}-cover.style_anchor.txt"
cover_style_anchor = cover_anchor_path.read_text(encoding="utf-8").strip() if cover_anchor_path.exists() else None
# 传给 huashu-image-curator Mode 2 的 style_anchor 输入
```

**pass_flag**(frontmatter):
- `huashu_decision_pass: true` + `image_decision: {<完整 JSON>}`
- **Round 22 P0-6 防伪**(必填,gate 强制):
  - `huashu_image_curator_real_run: true` — **必须真 invoke huashu-image-curator skill**
  - `huashu_image_curator_source: "huashu-image-curator Mode 2, decided count=N, style inherited from cover"` — 真实出处 + 决策摘要
- gate 看到 `huashu_decision_pass: true` 但缺这两个字段 → fake-pass 防伪触发 → 阻断 ship

---

## Step 7.3 · 内文图 Seedream 生成 + write_metadata

**触发**:Step 7.2 完成 + `should_illustrate: true` + `count > 0`。

**输入**:Step 7.2 的 decision JSON。

**执行**:
```python
from tools.illustrate_decider import generate_from_decision, write_metadata
paths = generate_from_decision(
    decision, OUT_DIR, slug=slug, max_workers=3, retry_failed=True
)
write_metadata(draft_path, decision, paths)
```

**BLOCKING + 错误分类策略**(Round 25 升级 — placeholder fallback 替代 0 图 degraded):

`illustrate_decider._call_seedream` 把错误分四类,**Round 25 起所有失败路径都走 placeholder fallback**:

| error_type | 判定关键词 | Round 25 策略 |
|---|---|---|
| **daily_quota** | "daily" / "quota" / "quota_exceeded" / "RPD_LIMIT" / "SetLimitExceeded" / "safe experience mode" | 立即 abort retry → **`assets/placeholder-sketch.png` × N 复制到 output/images/**(不再 0 图 degraded ship) |
| **rps_limit** | "429" / "too many requests"(无 daily 字样)| retry × 2 + exponential backoff → 仍失败则 **placeholder fallback** |
| **transient** | "timeout" / "ssl" / "connection" | retry × 2 换 seed → 仍失败则 **placeholder fallback** |
| **other** | 其它(HTTP 500 / API 异常)| retry × 1 → 仍失败则 **placeholder fallback** |

**Round 25 invariant**(出口保证):`generate_from_decision` 永远不返回空 list — 任何失败路径都至少返回 N 张 placeholder(N = decision.count)。

**pass_flag**(frontmatter):
- 成功路径:
  - `image_at_h2_indices: [1, 3, 5]` ✅(从 Step 7.2)
  - `image_paths: ["output/images/<slug>-01-...png", ...]`(真图)
  - `image_generation_pass: true`
- Placeholder 路径(任何 Seedream 失败):
  - `image_at_h2_indices: [1, 3, 5]` ✅
  - `image_paths: ["output/images/<slug>-01-placeholder.png", ...]`(placeholder 副本)
  - `image_zero_reason: "seedream_daily_quota_round25_placeholder"`(或其它 reason)
  - **gate 允许 ship**(placeholder 文件 size 36 KB ≥ 5 KB threshold,通过 Newton 有效性检查)
- ❌ **不再有「0 图 degraded」路径**(Round 25 删):`image_generation_degraded: true` 会被 gate 当场拦

---

## Step 7-cover · 封面生成

**触发**:Step 6 verdict = ship(跟 Step 7.1 并行启动)。

**输入**:draft + research.md。

**执行**:
```bash
python tools/generate_cover_by_template.py \
    --draft output/drafts/<slug>-v0.md \
    --research output/research/<slug>.md
```

内部流程:
1. classify(text) → template_id
2. cover_dedup gate(7 天回看 template_id 撞型)→ 撞型自动换 alternative
3. Seedream 生成 1 张 + retry × 2
4. 7 模板 Rand 路线 metaphor(Round 16 重写)

**输出**:
- `output/images/<slug>-cover.png`
- **Round 21 决策 2 新增**:`output/images/<slug>-cover.style_anchor.txt` — sidecar 文件,给 Step 7.2 huashu-image-curator 读,确保内文图风格继承封面
  - 固定基底:`"warm sketchnote hand-drawn, cream paper #F8F0E0, terracotta #D97757 accent line, soft cloud signature, no human face, editorial illustration"`
  - 7 模板共享同一基底(场景不同但视觉语言一致)

**BLOCKING**:
- cover 文件不存在 → Step 8 abort
- R18 P0 命中 prompt → abort

**pass_flag**(frontmatter):`cover_path: "output/images/<slug>-cover.png"` + `cover_template_id: "T4_news"` + `cover_pass: true`

---

## Step 8 · 排版 + 推草稿(⛔ gate 守门)

**触发**:Step 7.3 + Step 7-cover 都完成。

**输入**:draft path + cover path + inline image paths。

**🛡️ Gate 检查**(`tools/gate.py` 由 PreToolUse hook + post_fengyun_publish preflight 双重触发):

必填 frontmatter 字段(缺一不让推):
```yaml
# ===== 基础字段 =====
title: "..."             # 必填,字数 ≤ 64
digest: "..."            # 必填
author: "研究Agent的云"   # 必填,固定
slug: "..."              # 必填
date: "..."              # 必填
north_star: "..."        # Step -1 产物

# ===== pass_flag(每个 step 产物)=====
writer_pass: true        # Step 3 产物
title_pass: true         # Step 3.3 产物
ending_pass: true        # Step 3.5 产物
lint_pass: true | lint_partial_pass: true   # Step 4
humanizer_pass: true     # Step 4.5
wangxiaobo_pass: true    # Step 5
critic_vote_pass: true   # Step 6(或 revise_loop_pass: true)
huashu_decision_pass: true        # Step 7.2(0 张图也算 pass)
image_at_h2_indices: [...]        # Step 7.2 产物(空 list 允许;支持多行 YAML list 或 inline JSON)
cover_pass: true                  # Step 7-cover
cover_path: "output/images/<slug>-cover.png"   # Step 7-cover

# ===== Round 18 / 21 / 22 fake-pass 防伪字段(8 项)=====
# 任一 *_pass: true 时,对应的 *_real_run + *_source 必须填,否则 gate 阻断
# 三轨 critic(Round 18 P0-1)— critic_vote_pass=true 时必查
critic_a_real_run: true
critic_a_score: 72                # 必填(替代 source,因为 A 轨是数字)
critic_b_real_run: true
critic_b_source: "huashu-perspective skill, ship verdict, 灵魂 ✓"
critic_c_real_run: true
critic_c_source: "content-judge skill, 挂名意愿 yes"   # Round 24 改名,原 fengyun-self
# Skill 真调(Round 21 P0-9 + Round 22 P0-6)— 对应 pass_flag=true 时必查
writer_real_run: true                 # writer_pass=true 时必查
writer_source: "fengyun-writer skill v1, round=1, 4200 字"
humanizer_real_run: true              # humanizer_pass=true 时必查
humanizer_source: "humanizer-zh skill, applied N changes"
wangxiaobo_real_run: true             # wangxiaobo_pass=true 时必查
wangxiaobo_source: "wangxiaobo-perspective skill, found 2 hits"
huashu_image_curator_real_run: true   # huashu_decision_pass=true 时必查
huashu_image_curator_source: "huashu-image-curator Mode 2, count=3, style inherited from cover"
# ⛔ Round 24 P0-7 升级:source 内容必须匹配工具真调用模式,非空不够
#   huashu_image_curator_source 必须匹配: ^huashu-image-curator Mode 2,
#   critic_b_source 必须含 ship/verdict/灵魂 之一
#   critic_c_source 必须含 挂名/verdict/ship 之一
#   writer_source 必须含 fengyun-writer/mode/round 之一
#   「first push, 0 inline images, conscious decision」这类主线程拍脑袋写的占位文字 → gate 拦截
```

**外部文件存在性检查**:
- cover_path 文件真存在(物理 check)
- 所有 image_paths 文件真存在

**Gate 失败 → `sys.exit(2)` + 把 missing fields 打到 stderr → Claude 必须回去补**。

**执行**(gate 通过后):
```bash
# 首推 — 走 draft/add
python tools/post_fengyun_publish.py \
    output/drafts/<slug>-v0.md \
    --html-out output/render/<slug>.html

# 补内文图后重推 — 自动走 draft/update(从 frontmatter 读 media_id)
python tools/post_fengyun_publish.py \
    output/drafts/<slug>-v0.md
# 或显式传 --update-media-id <existing_media_id>
```

内部(Round 19 P0-2 + Round 21 决策 1 + Round 21 P0-17 升级,2026-05-25):
1. **layout_rules huashu 渲染(唯一活跃路径)** — Round 21 决策 1.1+1.2 砍 legacy/default/classic 分支后,任何 style 输入都强制走 huashu 模板。`--render-mode` argparse 已删除
2. **HTML 上限 60000 bytes**(Round 21 P0-17 升级,原 20000 是 layout_rules 内部历史值,无外部出处;微信真实上限 ~65000,留 5000 缓冲到 60000)
3. **fengyun_lint R12b html_size_warn**:markdown × 5 倍膨胀估算,> 50000 → warn(留 10k 到 60k 硬上限)
4. 上传封面到微信 → cover_media_id
5. 上传内文图 → 替换 markdown 里 placeholder
6. **草稿路由**(优先级):
   - CLI `--update-media-id <existing>` → 走 `cgi-bin/draft/update`,沿用原 media_id
   - frontmatter `media_id: "..."` 字段存在 → 自动走 update
   - 都没有 → 走 `cgi-bin/draft/add` 新建
7. **首推后**:自动把 `media_id` 写回 frontmatter,下次重推自动走 update
8. **update 失败兜底**:微信侧 media_id 已被清理 → 自动 fallback 到 draft/add 新建

**意义**:风云补内文图重推时,**草稿箱不会出现重复同名草稿**。原 media_id 保持稳定,审阅 + 发出动作不变。

**输出**:`media_id` 已落微信公众号草稿箱。

**pass_flag**(runlog):`{"step": 8, "media_id": "...", "render_html_path": "...", "shipped_at": "..."}`

**失败回退**:微信 API 失败 retry × 2 → 仍失败 → 报警 + 不重试。

---

## Step 9 · 报告 + audit log

**触发**:Step 8 完成。

**输入**:全程 runlog.jsonl。

**执行**:
1. 生成 `output/runs/<slug>.json` 最终报告(每 step 状态汇总)
2. 跑 `tools/verify_audit.py`(对照本 WRITE_AGENT.md 19 step 清单,缺 step 报警)
3. 打印给风云:media_id + 公众号草稿箱链接 + audit 结果

**pass_flag**:`pipeline_complete: true`

---

## 强制执行机制(双保险)

### B 主力:PreToolUse hook(物理拦截)

**`~/.claude/settings.json`** PreToolUse 块:
```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "if": "Bash(*post_fengyun_publish.py*)",
    "hooks": [{
      "type": "command",
      "command": "python D:/Dev/ai-wechat-pipeline/tools/gate.py"
    }]
  }]
}
```

`gate.py` 行为:
- 从 Bash 命令里解析出 draft 文件路径
- 读 frontmatter,检查 Step 8 要求的全部必填字段
- 检查 cover_path / image_paths 文件存在性
- 缺一 → `sys.exit(2)` + stderr 打印「缺 Step X 的 <field>,先去跑 Y 命令」
- 全通过 → exit 0

### C 兜底:post_fengyun_publish preflight assertion

`tools/post_fengyun_publish.py` `main()` 第一行调用 `gate.check_draft(draft_path)`,跟 hook 同样的检查。即使 hook 失效 / 没装 / 别的窗口跑都兜住。

### Escape hatch(紧急情况)

`gate.py` 接受 `--force-skip-gate` flag,但**只允许风云本人显式传**。日志记录每次 force-skip,审计可追。

---

## 已知 bug + Round 17 修复清单

**2026-05-25 全部修复**(代码已落地,见每行「位置 + 改动」)。

| Bug | 位置 | 严重度 | 状态 |
|---|---|---|---|
| 1 topic_recommender score 全 0 | tools/topic_recommender.py | P0 | ✅ **误诊** — cli_demo 实测正常(0.08-1.00),aihot 字段名 `title`/`summary` 跟代码一致,不存在此 bug |
| 2 title hook 软分,无 hard gate | tools/title_signal.py:326-336 | P0 | ✅ 已修(无 hook_type 直接 verdict=redo) |
| 3 classify「事件」误命中 T7 | tools/generate_cover_by_template.py:78 | P1 | ✅ 已修(删「事件」单字 → 改「事件始末/宫斗事件」词组) |
| 4 dedup self-match Jaccard 1.0 | tools/{opening,title,ending,event,cover}_dedup.py | P1 | ✅ 已修(5 个 dedup 加 `current_draft_path` 参数 + 排除自身),**调用方须传 `current_draft_path` 才生效** |
| 5 lint R0 误报技术标识符 | tools/fengyun_lint.py:391 | P1 | ✅ 已修(period_pat 加 `(?![a-zA-Z0-9])` lookahead 排除扩展名) |
| 6 lint R8/R13 矛盾 | tools/fengyun_lint.py:41-50 | P0 | ✅ 已修(R8 词典「替代/落后」从字面字符串改为「指着读者吓」精确 regex,中性焦虑词归 R13) |
| 7 fengyun_lint vs layout_rules lint 混用 | 两套 lint | P1 | ✅ 已修(两端加分工注释 + post_fengyun_publish 把 layout_rules.lint 致命级 issue 升级为 RuntimeError 阻断) |

---

## 主线程跳过环节追责机制

任何主线程 LLM 都受本宪法约束。**「我已经在历史 round 验证过,这次跳过 sanity check」是不可接受的借口**。Round 17 起:

1. 跳过任何 BLOCKING step → Step 8 gate 必然拦截
2. 试图改 frontmatter pass_flag 而不真跑前置 step → 视为 R18 P1 违规(`fake pass flag`)
3. 试图 `--force-skip-gate` → 只能风云本人在最终草稿箱审稿时显式触发,**主线程不允许自行触发**

---

## 总结一句话

**这份宪法把「请你跑完整 19 个 step」从 prose 提示词升级成了机器可执行的 invariant。Step 8 gate 是物理约束,不是劝告。**

> 文档版本:v1.0 · 2026-05-25
> 编写:Round 17 Musk × Jobs 共识 + 调研 Agent 报告
> 主要受益人:风云 + 任何接手 ship pipeline 的人(包括主线程 Claude 自己)
