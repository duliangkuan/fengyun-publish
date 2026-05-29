# fengyun-publish 新分支架构重构 v1 — 完整策略文档

> **生成时间**:2026-05-26
> **来源**:8 共识辩论 + 信源 6 层下钻 + Newton × Musk 全系统拷问 + Skills 规范深度调研 v2 + 用户决策
> **执行分支**:`arch-refactor-v1`(待开)
> **覆盖关系**:完工后整体覆盖主支(用「替换 + tag 备份」方式,旧主支打 tag `backup-pre-refactor-20260526` 保留)

---

## 0. 文档定位

这是 fengyun-publish 从 1480 行 SKILL.md「补丁堆叠态」走向「from scratch 重设计」的完整作战图。

**何时读这份文档**:
- 开始新分支重构工作前必读
- 任何「新分支上该不该做 X」的争议出现时回查
- 重构完工后做 retrospective 时对照「是否落地」

**不应读这份文档的时间**:
- 主支日常 ship 文章时不要看这份(主支冻结策略不动)
- 信源 cookie 重扫这种日常运维不要拿这份当指引

---

## 1. 触发背景(为什么要重构)

### 1.1 三次端到端实测共同问题

三次独立 CLI 窗口跑 fengyun-publish 端到端,出现 **8 个共识问题**(频次 ≥ 2/3):

| 频次 | 问题 |
|---|---|
| 3/3 | 信源覆盖崩塌(11 进 3) |
| 3/3 | Lint 修复轮数超预期(6 / 3 / 6 轮) |
| 2/3 | Opening 反差感卡死 |
| 2/3 | gate.py frontmatter 拦截 |
| 2/3 | 三轨 critic 非真并行 + revise 后没重跑 |
| 2/3 | Python 脚本未自动调用 + dedup self-match |
| 2/3 | 字数振荡 |
| 2/3 | writer 内部流程没真跑 + persona drift |

### 1.2 Musk × Jobs 沙盒辩论 verdict(8 → 6)

辩论收敛后:
- **砍 2 个伪问题**:Opening 反差感(无 PHASE1 出处 + 花叔 4.3% 命中)/ 信源 11 进 3 部分(读者不在乎信源数)
- **合并 2 对同根因**:问题 7+8(writer 没真跑导致字数振荡)/ 问题 4+6(SKILL.md 写法软)
- **剩 6 个独立修复**

### 1.3 Newton × Musk 全系统拷问额外发现

8 共识之外的 **额外架构包袱**:

**必砍清单**:
1. 5 个不真 invoke 的 perspective skill 引用(steve-jobs / elon-musk / newton / paul-rand / kenya-hara)
2. humanizer-zh 整个 Step 4.5
3. System A / System B 双轨切换
4. founder_feedback.jsonl 写入逻辑(3 条 D1 + 0 D2/D5,0 消费者)
5. 7 个 `_*.py` 临时脚本 + `tools/backup_20260521/` 目录

**简化清单**:
1. 9 步 → 4 阶段(Collect / Write / Verify / Publish)
2. 三轨 → 双轨 critic(砍 A 数字,留 B 灵魂 + C 挂名)
3. 29 lint 规则 → 6 RuleFamily(R12/R19/R20 重号修 + R26/R27/R28 合并)
4. 31 frontmatter 防伪 → 6 invocation log 文件
5. ITI I-2 不再镜像 I-1 4 query → 单 URL WebFetch + 1 补充
6. 7 cover 模板 → 单模板 + 随机 seed + brand DNA

### 1.4 Skills 规范深度调研 v2 核心发现

**Anthropic 官方承认**(GitHub issue #19308):「Claude systematically ignores Skill tool despite explicit BLOCKING REQUIREMENT」— **prompt 层的强制约束是 broken pattern**,要靠 hook + subagent + slash command 实现确定性。

**学术研究支撑**(arxiv 论文):
- 2307.03172 Lost in the Middle:中间位置 relevant info 性能掉 **30%+**
- 2410.03608 TICK:Checklist 比 holistic 评分对 instruction-following 显著更好
- 2305.11790 Pseudo-Code:伪代码对 reasoning 好 / 对 execution 反而被当 reference
- 2303.17651 Self-Refine:同 LLM 跑 generate→feedback→refine 平均 +20%
- 2402.11436 Self-Bias in Self-Refinement:self-refine 放大 self-bias,**外部反馈才能消偏**
- 2308.00352 MetaGPT:SOP 强制结构化中间产物 Pass@1 +85%

**Anthropic 官方推荐**:
- Building Effective Agents:5 模式(prompt chaining / routing / parallelization / orchestrator-worker / evaluator-optimizer),不用 LangGraph/CrewAI 复杂框架
- Multi-agent Research System:subagent 任务描述必须含 **objective + output format + tool guidance + task boundary** 四件套

---

## 2. 用户决策汇总(2026-05-26)

| # | 决策项 | 用户拍板 | 理由 |
|---|---|---|---|
| 1 | Cover retry | **砍**(新分支立刻砍) | 藏到客户端 wrapper,SKILL.md 不再有用户可见 retry 循环 |
| 2 | 维度精简时机 | **Musk 路:先实测后立刻砍** | 不等数据飞轮(已废),先派 agent 跑历史 corpus 实测 18 维度触发率,出报告给用户审决 |
| 3 | 新分支编排方式 | **Agent SDK** | 官方推荐 + 2026-06-15 独立计费 + Python callback 强 |
| 4 | ship.py 编排器架构 | **orchestrator-worker 模式重写** | 真并行 + 失败可重派 + 每个 worker 产结构化文件 |

---

## 3. 重构总策略(5 阶段)

### 阶段 A:架构层重构(P0,根因消除)

#### A1 · SKILL.md 1480 → ≤ 300 行 thin orchestrator + references/ 拆分

**当前**:`~/.claude/skills/fengyun-publish/SKILL.md` 1480 行,9 步全在一个文档里,违反官方 ≤ 500 行建议 + Lost in Middle 中段丢失 30%。

**目标结构**:
```
~/.claude/skills/fengyun-publish/
├── SKILL.md                              # ≤ 300 行,只放 Overview + 4 阶段骨架 + 关键不变量 + Output Format
├── references/
│   ├── stage_01_collect.md               # ~150 行,ITI 三段详解
│   ├── stage_02_write.md                 # ~120 行,writer + opening/ending/title harness
│   ├── stage_03_verify.md                # ~150 行,lint + 王小波 + 三轨 critic vote
│   ├── stage_04_publish.md               # ~100 行,cover + 排版 + push 草稿箱
│   ├── failure_modes.md                  # ~100 行,常见失败 + recovery
│   └── frontmatter_checklist.md          # ~50 行,单点 35 字段总表(防分散)
├── scripts/
│   └── validate_run_log.py               # ~80 行,PostToolUse hook 入口
└── assets/
    └── run_log.schema.json               # JSON Schema 强制 run_log 结构
```

**SKILL.md 主体章节**(目标 ≤ 300 行):
```
Frontmatter (5 行)
↓
# fengyun-publish
↓
## When to use(触发词 + 不触发反例,~30 行)
↓
## 4 阶段流程一览(每阶段 5-10 行,跳转 references/,~80 行)
↓
## 关键不变量(run_log.json 必含字段 / image_paths 非空 / R18 红线,~40 行)
↓
## 失败行为(每阶段 fallback,跳转 references/failure_modes.md,~30 行)
↓
## Output Format(草稿箱 URL + run_log 结构,~20 行)
↓
## References(目录跳转,~10 行)
```

**对外只 4 阶段**(子步骤是实现细节,不进入用户文档章节结构):
- **Collect**(ITI 调研 + 选题 + 北极星 + dogfood gate)
- **Write**(writer + opening/ending/title harness)
- **Verify**(lint + 王小波 + 双轨 critic vote)
- **Publish**(cover + 排版 + push 草稿箱)

#### A2 · 写 4-5 个 subagent + writer/critic 拆 subprocess invoke

**位置**:`.claude/agents/` 目录,每个 subagent 一个 `.md` 文件,frontmatter `name / description / model / tools` 四件套。

**subagent 清单**:

| subagent | 用途 | 输出 |
|---|---|---|
| `fengyun-iti` | Stage Collect(ITI 广搜 + 深搜) | `output/research/<slug>.md` |
| `fengyun-writer` | Stage Write(写完整稿) | `output/drafts/<slug>-v0.md` |
| `fengyun-critic-content-judge` | Track C(挂名意愿) | `output/verdicts/<slug>_content_judge.json` |
| `fengyun-critic-huashu` | Track B(灵魂判断) | `output/verdicts/<slug>_huashu.json` |
| `fengyun-cover` | Stage Publish(封面 + 内文图) | `output/images/<slug>-*.png` + 元数据 |

**关键工程模式**(来自 Anthropic Multi-agent Research System):
- 每个 subagent prompt 必含 **objective + output format + tool guidance + task boundary** 四件套
- subagent 之间真并行(Track B + C 同时跑,~3x 加速)
- 每个 subagent 产**结构化 JSON 文件**返回(不只是 string)
- subagent context 完全隔离防 self-bias(arxiv 2402.11436)

#### A3 · 31 frontmatter 防伪字段 → 6 invocation log 文件

**当前**:`tools/gate.py` 强制 31 个 frontmatter 字段(6 base + 11 pass_flag + 6 skill audit + 7 source pattern + 1 image_paths)。Newton × Musk verdict 是「这是 hypothesis non fingo 反面教材 — 把『主线程可能 fake pass』hypothesis 物化成 31 字段」。

**目标**:每个 subagent / skill 跑完自己写一个 `.skill_invocation.json` 文件,gate.py 检查文件存在 + 哈希校验 + 时间戳 < 1h。

**invocation log 文件清单**(6 个):
```
output/runs/<slug>/
├── iti.invocation.json          # fengyun-iti 跑完产
├── writer.invocation.json       # fengyun-writer 产
├── critic_b_huashu.invocation.json
├── critic_c_content_judge.invocation.json
├── cover.invocation.json
└── render.invocation.json
```

**每个 invocation.json 结构**:
```json
{
  "skill_name": "fengyun-writer",
  "started_at": "2026-05-26T14:00:00Z",
  "finished_at": "2026-05-26T14:08:23Z",
  "version": "v1.2",
  "round": 1,
  "input_hash": "sha256:abc...",
  "output_files": ["output/drafts/codex-v0.md"],
  "summary": "writer skill v1, voice-dna applied, 4296 字"
}
```

**frontmatter 回归本职** — 只记录文章 metadata,不记 pipeline state:
```yaml
title: ...
digest: ...
author: 研究Agent的云
slug: ...
date: ...
north_star: ...
```

#### A4 · Python 伪代码全换 bash + DEFAULT-on opt-out 全文清扫

**问题根因**:Anthropic 官方 issue #19308 — Claude 看到 Python 伪代码块当成 "reference 不是 command";看到「如果 ... 则 ...」条件触发会选省事的路。

**改造规则**:

1. **删所有 Python 伪代码块**,SKILL.md 里的代码全是 bash 真命令:
   ```bash
   # 改前(SKILL.md L70-113 现状):
   pool_result = collect_pool(hours=24)
   # pool_result["items"] = 15-30 条候选

   # 改后:
   python tools/iti_collect.py --hours 24 --out output/runs/<slug>/iti_pool.json
   ```

2. **删所有「如果用户没指定 → 跑 X」条件触发**,改 **DEFAULT-on opt-out**:
   ```
   # 改前:
   如果用户没指定具体事件 → 跑 ITI 数据驱动选题

   # 改后:
   **DEFAULT: 必跑 ITI**。**Opt-out**: 仅当用户消息**显式**包含「主题已定」/「跳过选题」/「用 X 主题」时跳过。
   ```

3. **删所有「BLOCKING REQUIREMENT」靠 prompt 的硬约束**,真要强制的改 hook 实现(见 A5)。

#### A5 · slash command `/ship` + PostToolUse hook 三层守门

**slash command**:`.claude/commands/ship.md`,用户必须显式 `/ship Codex` 才能触发,避免 LLM 自主挑路径偷懒。

**hook 三层**:

```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "command": "python tools/gate.py" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{ "command": "python tools/validate_run_log.py" }]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [{ "command": "python tools/ship_complete_check.py" }]
      }
    ]
  }
}
```

**exit code 语义**:0 通过 / 2 + stderr 阻断(stderr 当错误回 Claude) / 1 warning。

---

### 阶段 B:数据驱动重校

#### B1 · 砍 Opening 反差感维度(已锁)

**证据**:花叔 397 篇 corpus 仅 4.3% 命中 + PHASE1_FACTS L1216-1217 明确「不显著」+ Round 13 自创无外部出处。

**操作**:
- `tools/opening_signal.py` 删除 `_score_reframe()` 函数
- `opening_signal` 4 维 → 3 维
- 更新 SKILL.md Step 1.5 流程描述

#### B2 · R13 焦虑词典数据驱动重做

**证据**:花叔 corpus 87.9% 触发率(过严)。

**操作**:
- 词典换装:删通用词「断 / 速度 / 未知 / 不确定 / 落后」5 个
- 加强信号词:「攻破 / 被替代 / 失业 / 封禁 / 击穿 / 失控」
- 阈值 ≥ 3 → ≥ 2
- 严重度 medium → info(不阻断 ship)
- **具名 owner**:风云本人(每次修改必须 review)

#### B3 · 29 lint 规则 → 6 RuleFamily

**当前问题**:
- R12 / R19 / R20 重号(同名不同义)
- R26 + R27 + R28 三条同一公理(working memory 4±1)的三种推论

**目标**:按物理目的归并 6 类:
1. **标点规范**(R0 + 半角全角)
2. **字数控制**(R12 拆 R12a 短 / R12b 长)
3. **AI 语言污染**(R5 / R6 / R7 / R8 / R17)
4. **章节结构**(R10 / R11 / R21)
5. **R18 红线**(P0 自暴 / P1 架构 / P2 自动化)
6. **huashu 风格**(R19-R28 合并到 RuleFamily,带子规则参数)

#### B4 · 18 维度触发率实测(已完工 2026-05-26 + 用户拍板选项 A 激进路线)

**实测数据源**:321 篇真品文章(kazik 175 + baoyu 52 + saiboshanxin 50 + fengyun ship/trial 44)

**报告位置**:
- `reports/dim_trigger_rate_audit_20260526.md`(完整 markdown)
- `reports/dim_trigger_rate_audit_20260526.json`(原始数据)
- `tools/dim_trigger_rate_audit.py`(可重跑脚本)

##### 砍 5 个维度(命中率 100% 或 0% — 等于没卡)

| # | 维度 | 命中率 | 文件改动 | 根因 |
|---|---|---|---|---|
| 1 | **opening 反差感** | 6.6% | `tools/opening_signal.py` 删 `_score_reframe()` | 已锁(花叔 4.3% + PHASE1 不显著)|
| 2 | **opening 首段字数(intro 块)** | 100% 必过 | `tools/opening_signal.py` 删该维度 | 算法取「前 400 字 / 整个 intro 块」,字段名歧义,永远超阈值 |
| 3 | **opening 具体性** | 87.2% 必过 | `tools/opening_signal.py` 删 `_score_specificity()` | 阈值 6 跟分数曲线脱钩 |
| 4 | **opening 信息密度** | 100% 必过 | `tools/opening_signal.py` 删 `_score_info_density()` | 算法下界 ≥ 10,数据 min=10 — 物理永远必过 |
| 5 | **title 致命组合 risk** | 0/321 命中 | `tools/title_signal.py` 删致命组合检测块 | tb_ratio 阈值算错(标题永远达不到 150 字阈值) |

**结果**:
- `opening_signal` 4 维 → **0 维(全砍)** + R28 公式新鲜度独立留
- `title_signal` 10 维 → **9 维**
- 总计 18 维 → **13 维 + 4 个调阈值** = 9 健康维 + 4 调过维

##### 调 4 个维度阈值

| # | 维度 | 改前 | 改后 | 数据依据 |
|---|---|---|---|---|
| 1 | **title 7 钩子 hard gate** | hard gate 卡死 | **改软分加权** | 全样本 24.6% / 卡兹克爆款仅 28%,hard gate 卡掉 72% 卡兹克爆款 |
| 2 | **title 4 共同特质** | ≥ 2 | **≥ 1** | 95.5% 触发(过严) |
| 3 | **opening 真实首段字数** | ≥ 50 | **≥ 25** | median 26 字(57% 文章首段 < 50) |
| 4 | **opening 情绪锚点动词词典** | 风云 voice 窄 | **扩词典 + 加普适动词** | 风云 voice 放普适用太窄,误伤其他风格 |

##### 留 9 个维度(数据健康,不动)

- 第一人称密度
- R28 公式新鲜度(opening_signal 唯一保留维)
- fengyun-only ending 3 维(金句 / 摘要 / 召唤)— ⚠️ 见 B6 Caveat
- title 字数 ∈ [20-40]
- title 数字组 ≤ 1
- title 品牌词白名单
- title 品牌词黑名单不上
- title token Jaccard ≤ 0.40
- title 5-gram 重叠 ≤ 0.25

#### B5 · 维度精简方法论(锁定)

Musk 路硬标准(用户 2026-05-26 拍板,选项 A 激进路线):
- 命中率 > 95%(永远过,等于没卡) → **砍**
- 命中率 < 5%(永远过不了,过严)→ **砍 或 大幅调松**
- 命中率 50-90%(健康曲线) → **留**

误删兜底:任何砍掉的维度后续 ship 真发现卡不住某种问题,几行代码加回来不难(对应 invariant #4「0 消费者 = 0 生产」的逆方向)。

#### B6 · ⚠️ Caveat(必读,新分支落地前必看)

- **corpus 281/307 篇无 H2**,导致 ending 末段字数指标失真 → **ending 4 维只能信 fengyun-only(n=30,样本偏小)**。新分支落地 ending 维度时需要做 fengyun 数据扩样(等 ship 文章累计到 60+ 篇再重跑实测)
- **opening「首段字数」字段名歧义**:`score_opening_signal` 算的是整个 intro 块(不是真正第一段),报告加了「真实第一段字数」对照。砍维度时同步清理字段命名歧义

---

### 阶段 C:删冗余(Newton × Musk 6 件 P0)

| # | 砍什么 | 改动量 | 验证 |
|---|---|---|---|
| C1 | 5 个不真 invoke 的 perspective skill 引用从 SKILL.md 删除 | 文档 ~10 行 | grep verify 0 引用 |
| C2 | humanizer-zh skill 整个 Step 4.5(R17 lint + 王小波已覆盖) | SKILL.md ~30 行 + gate.py 1 行 + 3 frontmatter 字段 | E2E ship 一篇验证 humanizer 缺位无影响 |
| C3 | System A / B 双轨切换从 fengyun-publish 删除 | SKILL.md ~50 行 | 卡兹克风格用户直接调 khazix-writer skill,不走 fengyun-publish |
| C4 | founder_feedback.jsonl 写入逻辑(0 消费者) | content-judge skill + SKILL.md 5 处 + data/ 目录 | 真出现 30 天回看任务时再加回 |
| C5 | 7 个 `_*.py` 临时脚本 + `tools/backup_20260521/` 目录 | 10 个文件 | `grep _tmp_rank import` = 0 引用,直接删 |
| C6 | 三轨 critic → 双轨(砍 A 数字 Track) | critic_vote.py + score_draft.py 改 lint 辅助 + SKILL.md Step 6 | score_draft.py 保留作 lint 辅助,不进 vote tree |

---

### 阶段 D:cover 系统重做

**当前**:7 模板路由 + cover_dedup.py 7 天回看撞型 → 自动换模板。

**问题**:7 模板 ÷ 每周 ≥ 7 篇 → 必然撞型,撞型不是 bug 是设计冲突。

**新设计**(Rand 路线 + 用户拍板):
- 单模板(T5 method 通用)+ 随机 seed
- brand DNA 三件套做识别:**暖象牙 #FAF9F5 + 陶土橙 #D97757 + 云签名**
- shared DNA > 篇间区分(brand identity 优先)

**操作**:
- 删 `tools/cover_dedup.py`(~300 行)
- 简化 `tools/generate_cover_by_template.py`(砍 7 模板路由,保留 T5)
- 简化 SKILL.md Step 7(~80 行 → ~20 行)

**Cover retry**(用户拍板):
- 删 SKILL.md 中所有「重试 N 次」用户可见循环
- 把 retry 逻辑藏到 `tools/seedream_client.py` 内部
- 客户端 wrapper:`generate_cover(prompt)` 内部自动 retry × 2 + sleep 指数退避 + placeholder fallback
- AI 主流程感知不到 retry,只看到「成功路径」或「最终失败 → placeholder」

---

### 阶段 E:ITI 简化

#### E1 · I-2 不再镜像 I-1 4 query

**当前**:I-2 主线程跑 WebSearch 中英文各 2 次 = 4 query,跟 I-1 重复。

**新设计**:
- I-1 出 top 10 候选已带 URL + 摘要
- I-2 改为「对已选 topic 的主源 URL 做 WebFetch + 1 个补充 query」
- 不再镜像 I-1

#### E2 · TrendRadar wrapper 升级(信源 6 层下钻 P0)

**当前 bug**:`iti_collect.fetch_trendradar()` 只读 `latest_daily.md` 的 markdown 摘要 170 条,丢了 68 feed 全量数据「按 feed 维度取最新 N 条」能力。

**新设计**:
- 直接读 `D:\Dev\TrendRadar\output\rss\<date>.db`
- 拿 68 feed 各自的原始全量数据
- 支持「按 feed 维度过滤 / 排序」

#### E3 · I-2 接入新信源

- `fetch_trendradar_topic()` (已修,主对话上一轮 Agent 完工)
- `fetch_aihot_by_query(entities)` 接 aihot `?q=` 全池关键词搜索
- `fetch_smol_ai_by_topic(entities)` 接 smol.ai 按主题过滤

#### E4 · 死路信源砍掉

- X / Twitter / IT之家 反爬升级是死路,从信源表删
- 5 个僵尸 RSS(bilibili-qiuye-aaaki / synced-review / wechat-deepseek / bilibili-hetongxue / one-useful-thing)已删(主对话信源急修 agent 完工)

---

## 4. 五条架构 invariant(新分支硬约束)

1. **公理化层级**:对外 4 阶段(Collect / Write / Verify / Publish),子步骤是实现细节不进入用户文档章节结构
2. **统一语言**:同一物理目的(像不像人话 / 灵魂判断)只能一个组件负责,禁止 3 个 skill 重叠检测同一现象
3. **frontmatter 是文章 metadata,不是 pipeline state**:31 防伪字段迁到 invocation log 文件,frontmatter 回归 title / digest / author / north_star
4. **0 消费者 = 0 生产**:任何「将来回填」的 metric,没真消费者前不要写
5. **真公理优先**:非真 invoke 的 perspective skill 不在 SKILL.md 出现(包括 newton / musk / jobs / rand / hara)

---

## 5. 五条 Skills 工程硬原则(深度调研 v2)

1. **fengyun-publish SKILL.md 必须 ≤ 300 行 + references/ 拆分**:超长 = Claude L2 加载拖慢 + Lost-in-Middle 中段规则被忽略

2. **三轨 critic 用 subagent 而非 skill**:
   - context 隔离防 self-bias(arxiv 2402.11436)
   - 真并行 3 倍速
   - 每轨产 verdict JSON 文件,主 ship.py 读文件汇总

3. **每步必产结构化文件,不只传 string**(MetaGPT 思想):
   - `run_log.json` 字段 schema 用 JSON Schema 写进 `assets/run_log.schema.json`
   - PostToolUse hook 强制验

4. **hook 三层守门 + exit code 2 阻断**:
   - PreToolUse(Bash 跑禁忌命令时拦)
   - PostToolUse(写 run_log/draft 时验 schema)
   - Stop(确认 L7 完成)
   - validate_run_log.py / gate.py / ship_complete_check.py 三脚本各 ≤ 80 行

5. **改稿循环 = Self-Refine + CoVe + 外部 critic 联用**:
   - Self-Refine:writer 自检一遍 fix 简单问题
   - CoVe:列事实问题 → WebSearch 答 → 用答改稿,治 hallucination
   - 外部 critic(双轨):防 self-bias,防"嚼别人嚼过的"
   - **三者顺序**:writer → Self-Refine 自检 → CoVe 事实验 → 双轨 critic vote

---

## 6. 实施顺序 — Wave 0-10 SOP(11 wave 串行,Anthropic 官方 + 7 案例验证)

### 6.0 总策略一句话

**单 main agent 主 thread + 串行 wave + 每 wave 收尾 fresh-context reviewer + subagent 只用于 read-only 探索 / review,不用于并行写代码**。

**反直觉的核心发现**(调研支撑):
- Anthropic 官方 issue #10599 直接 closed not planned — **不支持 session 内并行写代码**
- Anthropic 官方原话:「most coding tasks involve fewer truly parallelizable tasks than research」 — 写代码可并行的部分远比研究类任务少
- multi-agent token 用量 = chat 的 15× / 单 agent 的 4×;Pro plan 5 subagent 并行 **15 分钟烧光配额**
- 7 个真实案例(SitePoint / Medium / Tembo / DEV.to / MindStudio 等)一致 verdict:**start with 1**,只有 context 隔离明显有价值才加 specialist
- 5 篇学术论文(arxiv 2511.03153 RefAgent 等)虽支持 multi-agent 但都是**批量重构**场景(千文件),不适用于 30 文件强耦合 epic

### 6.1 五个 subagent 角色定义(全程只用这 5 种)

| 角色 | 类比 | 用途 | 何时启动 |
|---|---|---|---|
| **主线程(orchestrator = 你)** | 总指挥 | 持 REFACTOR_PLAN.md / 决策记录 / wave 状态;每 wave 收尾 `/clear` 重启上下文 | 全程 |
| **explorer subagent** | 工地侦察兵 | **read-only**;读 corpus / 旧代码 / 真品 inline style,返回 summary | 每 wave 开始时按需 |
| **writer subagent**(可选) | 临时小工 | 单文件 / 小模块改写;返回 diff,主线程 review 后 apply | 每 wave 内**并发 ≤ 3**(配额警戒线) |
| **reviewer subagent** | 验房师 | **全新 session,不知道你怎么写的**;只看 diff + spec,输出 issues | 每 wave 收尾 |
| **verify subagent** | 监理 | 跑 lint / pytest / dry-run ship.py;返回 pass/fail | 每 wave 收尾 |

### 6.2 Wave 0-10 执行表

| Wave | 内容 | 模式 | 协调 / 兜底 |
|---|---|---|---|
| **W0 基线** | 开 `arch-refactor-v1` 分支(主支打 tag `backup-pre-refactor-20260526`);写 `REFACTOR_PLAN.md`;固化所有验收脚本(ship dry-run、lint、critic 跑分) | 你单干 | branch 即 rollback 点 |
| **W1 拆 SKILL.md** | 1480 → ≤ 300 行 + references/ 6 文件拆分 | 你 + 1 个 explorer subagent(读全文返 outline) | 跨内部 reference 强一致 → **不能并行,单 agent** |
| **W2 删 6 件冗余** | C1-C6 全删(humanizer / System A-B / founder_feedback / 临时脚本 / backup_20260521 / 三轨→双轨) | 你单干**串行**(每删 1 件跑 lint + ship dry-run) | **每删一件单独 commit**,坏 `git revert` 单个 |
| **W3 写 5 subagent + slash + hook** | `.claude/agents/` 5 个 .md + `.claude/commands/ship.md` + `.claude/settings.json` hook 三层 | **5 个文件独立 → 唯一可 fan-out 的 wave**:`claude -p` per file(每个文件一个独立 session) | reviewer subagent 收尾审一致性;**并发 ≤ 3** |
| **W4 frontmatter → invocation log** | A3:31 字段 → 6 invocation log 文件 + JSON Schema 强制 | 你单干(schema 强一致) | schema 测试脚本先写 |
| **W5 Python 伪代码 → bash + DEFAULT-on opt-out** | A4:全文清扫 + 删条件触发 | 你 + verify subagent(跑 dry-run) | 每文件 commit |
| **W6 用 Agent SDK 重写 ship.py** | orchestrator-worker 模式 + ship_legacy.py 保留 | **绝对你单干**(关键文件不并行) | 旧 ship.py 改名 ship_legacy.py;新的搞坏能换回去 |
| **W7 cover 系统重做** | D:7 模板 → 单模板 + brand DNA + Cover retry 藏 wrapper | 你 + explorer(读真品 inline style)+ writer(改文件) | 旧 7 模板移 `archived/` |
| **W8 ITI I-2 + TrendRadar wrapper** | E1-E4:I-2 不镜像 I-1 / TrendRadar wrapper 读 db / 接 aihot ?q= + smol.ai by topic | 你单干 | trendradar 抓不到 → fallback 旧 22 源 |
| **W9 砍 5 维度 + 调 4 阈值** | B1-B5:opening 4 维全砍 + title 致命组合 + R13 词典换装 + lint 29→6 RuleFamily | 你 + verify(K-fold 跑 critic 在 549 条 corpus) | **必须 K-fold**(memory `feedback_critic_route_b` 已规定)防 p-hacking |
| **W10 e2e 验收** | 跑一次完整 ship → 推草稿;跟主支 A/B 对比质量 | 你 + reviewer subagent(全新 session 审) | 失败 → branch 保留,主支 0 影响;通过 → 整体替换主支(`git branch -M arch-refactor-v1 main` + 旧 main 已 tag) |

### 6.3 关键规则(全程遵守)

1. **每个 wave 收尾 `/clear`** — 不让主线程累积 context 犯傻;`/clear` 后只 reload `REFACTOR_PLAN.md` + 下一 wave spec
2. **每 wave 干完先 commit** — 出问题 `git revert` 单个 commit,不破坏整体
3. **subagent 并发 ≤ 3** — 多了烧配额(Pro plan 5 个并发 15 分钟烧光)
4. **关键文件(ship.py / SKILL.md / Agent SDK 编排)绝对单 agent** — 不允许多 agent 同时改
5. **每个 wave 用 git worktree 隔离** — 如 W3 fan-out 时,每个 `claude -p` 用独立 worktree(`claude -w wave-3-agents`)防互相覆盖
6. **盲推 3 次没修好停手** — memory `feedback_3_blind_fixes_then_research` 已规定 → 派调研 agent

---

## 7. 风险与兜底

### 7.1 通用风险(跨 wave)

| 风险 | wave | 兜底 |
|---|---|---|
| 新分支大改后 ship 质量下降 | W10 | A/B 对比,新分支跑 1-2 篇后才切支;主支 tag 备份永远可回滚 |
| Agent SDK 计费独立后用量超预算 | W6+ | 先用 Sonnet,Opus 只在 critic / writer 这种关键节点;实测 1 周用量再决定 |
| 多 subagent 配额烧光 | W3 fan-out | **并发 ≤ 3**;监控 `/cost`,触限暂停转串行 |
| subagent 写出风格不一致代码 | W3 / W7 | **fresh-context reviewer 必跑**;不通过回到主线程改 |
| 主线程 context 累积犯傻 | 全程 | 每 wave 收尾 `/clear`,只 reload REFACTOR_PLAN.md + 下一 wave spec |
| 跨 wave reference 漂移 | W1-W4 | reviewer subagent 在 W4 末检查 SKILL.md ↔ subagent ↔ slash 三方 reference 一致 |
| 盲推 3 次没修好 | 全程 | memory `feedback_3_blind_fixes_then_research` 已规定 → 停 → 派调研 agent |

### 7.2 关键文件风险(单点失败)

| 风险 | wave | 兜底 |
|---|---|---|
| Agent SDK 重写 ship.py 出锅 | W6 | **ship_legacy.py 保留** + branch 不 merge 到 main 直到 W10 全过 |
| SKILL.md 拆 references/ 后 link 漏改 | W1 | W1 收尾跑 grep 验证所有 references/ link 都活;reviewer 全文审 |
| invocation log schema 破坏向后兼容 | W4 | 写 schema 测试脚本先验,再迁字段;旧 frontmatter 字段保留 2 wave 兼容 |
| critic 调参 p-hacking | W9 | **K-fold + held-out 50 条不参与训练**(memory 已规定) |

### 7.3 删冗余风险(可能误删)

| 风险 | wave | 兜底 |
|---|---|---|
| 删 humanizer-zh 后翻译腔逃过检测 | W2 | 王小波 skill 还在,R17 lint 也在;真发现 regression 再加回(0 消费者 = 0 生产原则) |
| 删 founder_feedback.jsonl 后真想做数据飞轮没数据 | W2 | invocation log 自动当数据源;30 天后真要做时已经有数据 |
| 砍 5 维度后某个失效维度其实有用 | W9 | 几行代码加回来不难;K-fold 验证前/后 critic 在 549 条 corpus 的 ROC 变化 |

### 7.4 信源风险

| 风险 | wave | 兜底 |
|---|---|---|
| TrendRadar wrapper 升级抓不到数据 | W8 | 保留旧 markdown 摘要 wrapper 作 fallback;新 wrapper 加 try/except + 24h soak |
| aihot ?q= API 限流 | W8 | safe_webfetch 加指数退避;失败时降级到 aihot daily 接口 |

---

## 8. 验收标准

新分支完工后跑 1-2 篇 ship,目标:

| 指标 | 主支基线 | 新分支目标 |
|---|---|---|
| SKILL.md 行数 | 1480 | ≤ 300(主体) |
| 端到端总耗时 | 45 min | ≤ 25 min(真并行 + 砍冗余) |
| Gate 拦截次数 | 1-3 次 | 0 次(hook 三层前移 + invocation log) |
| 三轨 critic 并行 | ❌ 串行 | ✅ 真并行 |
| Lint 修复轮数 | 6 / 3 / 6 | ≤ 2 |
| Cover 撞型 | 自动换模板 | 不会撞(单模板 + 随机 seed) |
| 信源覆盖 | 11 进 3 | 11 进 7+(TrendRadar wrapper 升级后) |
| Python 伪代码出现次数 | ~10 处 | 0 处 |

---

## 9. 引用文档清单

### 主对话产出
- 三次端到端测试对照(对话顶部 3 张截图)
- 三份独立修复清单交叉对比(`docs/FIX_CHECKLIST_20260526.md` 等)

### 子 agent 调研报告
- Musk × Jobs 沙盒辩论 8 共识 verdict
- 信源 6 层下钻 + TrendRadar 真跑实测
- Newton × Musk 全系统架构拷问
- Skills 规范深度调研 v2(本文档 §1.4 + §5 来源)
- 18 维度触发率实测(进行中,完工后追加)

### Anthropic 官方文档
- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [Subagents in the SDK](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [Hooks reference](https://code.claude.com/docs/en/hooks)
- [Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Multi-agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### 学术论文(arxiv)
- 2303.17651 Self-Refine
- 2402.11436 Self-Bias in Self-Refinement
- 2303.11366 Reflexion
- 2305.10601 Tree of Thoughts
- 2212.08073 Constitutional AI
- 2210.03629 ReAct
- 2305.04091 Plan-and-Solve
- 2302.04761 Toolformer
- 2305.16291 Voyager
- 2309.11495 Chain-of-Verification
- 2308.00352 MetaGPT
- 2303.17760 CAMEL
- 2305.11790 Pseudo-Code Instructions
- 2307.03172 Lost in the Middle
- 2410.03608 TICK

### 项目内文件
- `WRITE_AGENT.md`(系统级宪法,新分支需 sync)
- `~/.claude/skills/fengyun-publish/SKILL.md`(主重构目标)
- `tools/gate.py` / `tools/critic_vote.py` / `tools/fengyun_lint.py` / `tools/iti_collect.py` / `tools/iti_explore.py`(主要重构对象)
- `PHASE1_FACTS.md` / `topic_hotness.parquet`(数据真公理,加 mtime gate)

---

## 10. 文档维护

- **下次更新**:18 维度实测 agent 完工后,在 §3 阶段 B 的 B4-B5 加入最终砍维度清单
- **每次重构 wave 完工后**:在 §6 实施顺序对应 wave 标记完成 + 实际改动量
- **新分支切支后**:文档归档到 `docs/archive/ARCH_REFACTOR_V1_COMPLETED.md`,主目录开 v2 plan
