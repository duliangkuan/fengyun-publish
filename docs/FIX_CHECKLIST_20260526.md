# fengyun-publish 修复清单 · 基于 2026-05-26 实测

*生成时间: 2026-05-26 · 基于首次端到端实测 9 处偏差*

---

## 修复总览

| 优先级 | 编号 | 问题 | 影响 | 改动范围 |
|---|---|---|---|---|
| **P0** | F-1 | dedup 自匹配 bug | 标题/结尾 harness 必现 Jaccard=1.0 | SKILL.md |
| **P0** | F-2 | WebSearch 不可用无降级路径 | I-1/I-2 信源覆盖率 50% | SKILL.md |
| **P0** | F-3 | gate.py 缺字段拦截 | 推草稿被阻断 | SKILL.md + gate.py |
| **P1** | F-4 | 字数振荡 | 7 次调整浪费时间 | SKILL.md |
| **P1** | F-5 | Opening harness 反差感阈值 | 3 次才过 | opening_signal.py |
| **P1** | F-6 | R18-P1 skill 名暴露 | lint 3 轮才清零 | fengyun-writer SKILL.md |
| **P2** | F-7 | Critic 双否决触发 revise | 1 轮改稿 +5min | writer corpus |
| **P2** | F-8 | Cover dedup 撞型 | 自动换模板(设计行为) | 无需修,记录即可 |
| **P2** | F-9 | B/C 轨 revise 后未重跑 | 省时间但不合规 | SKILL.md |

---

## P0 · 必须修（影响 pipeline 可靠性）

### F-1 · dedup 自匹配 bug

**现象**: opening_dedup 和 ending_dedup 调用时没传 `current_draft_path`，导致草稿跟自己比较，Jaccard=1.0 必然 "is_too_similar=true"。

**根因**: SKILL.md 的 Step 1.5/3.3/3.5 伪代码里写了 `current_draft_path=draft_path`，但只在代码注释里，没有作为 ⛔ BLOCKING 规则强调。Agent 执行时容易忽略注释。

**代码现状**:
- `tools/opening_dedup.py:165` — 参数存在，`Optional[Path] = None`
- `tools/ending_dedup.py:102` — 同上
- 功能本身没问题，问题是 SKILL.md 调用指导不够强

**修复方案**:

> **文件**: `~/.claude/skills/fengyun-publish/SKILL.md`
>
> **改动 1**: 在 Step 1.5 伪代码块前加 ⛔ BLOCKING 规则:
> ```
> ⛔ Bug 4 铁律: 所有 dedup 调用(current_draft_path 存在时)必须传 current_draft_path=draft_path。
> 不传 = 自匹配 Jaccard=1.0 = 假阳性。Step 1.5 试稿阶段 draft 尚未写入文件,可不传;
> Step 3.3 / 3.5 / 6.5 已有 draft 文件,必须传。
> ```
>
> **改动 2**: 在 Step 3.3 和 Step 3.5 的 `check_title_overlap` / `check_ending_overlap` 调用处,
> 把 `current_draft_path=draft_path` 从代码注释提升为显式参数(已有,但需加醒目注释)。

**验证方式**: 跑一次 pipeline，确认 title_dedup 和 ending_dedup 的 `max_jaccard < 0.5`。

---

### F-2 · WebSearch 不可用无降级路径

**现象**: WebSearch 在当前 Claude Code 环境返回 "no web search tool available"，4 次调用全部失败。SKILL.md 说"I-1 和 I-2 都必须用 WebSearch"，但没有处理 WebSearch 不存在的情况。

**根因**: SKILL.md 的降级表只覆盖了 "aihot 拿不到 → 走 WebSearch"（反方向），没有覆盖 "WebSearch 本身不可用" 的情况。

**修复方案**:

> **文件**: `~/.claude/skills/fengyun-publish/SKILL.md`
>
> **改动**: 在 Step 1.0 和 Step 2 的 WebSearch 伪代码前加降级块:
> ```
> ⚠️ WebSearch 降级协议:
> 如果 WebSearch 调用返回 "no web search tool available" 或连续 2 次超时:
>   1. 标记 degraded.websearch = "unavailable"
>   2. I-1 降级: iti_collect 的 5 个 Python 源仍正常跑,只是少了 WebSearch 补位
>   3. I-2 降级: 用 aihot API 的 ?q= 关键词搜索替代 WebSearch(覆盖率约 60-70%)
>   4. 不阻塞主流程,但 run log 必须标记
>   5. 如果 iti_collect 也只有 < 10 条候选 → 报警但继续(用户硬约束 ≥10)
> ```

**补充改动**: 在 `tools/iti_collect.py` 的 `collect_pool()` 函数里，如果 WebSearch 不可用，自动 fallback 到 aihot API `?q=<entities>` 关键词搜索。

**验证方式**: 在无 WebSearch 的环境下跑一次 Step 1，确认 `degraded.websearch = "unavailable"` 且候选 ≥ 10。

---

### F-3 · gate.py 缺字段拦截

**现象**: `post_fengyun_publish.py` 被 gate.py 拦截，缺 4 个字段: `slug`、`date`、`north_star`、`image_paths`。这些字段在 pipeline 各步骤中产出，但没有在 frontmatter 里提前写入。

**根因**: SKILL.md 的各 Step 都有 "→ 立即写入 frontmatter" 的指引，但 `slug`/`date`/`north_star` 这三个字段只在 Step 1 产出，没有显式要求写入 frontmatter。`image_paths` 由 `illustrate_decider.write_metadata()` 写入，但 0 图场景下不会写。

**修复方案**:

> **文件**: `~/.claude/skills/fengyun-publish/SKILL.md`
>
> **改动 1**: 在 Step 1.1 末尾加:
> ```
> → 立即写入 frontmatter(Step 1.1 完成后):
> slug: <slug>
> date: <YYYY-MM-DD>
> north_star: "<北极星填空>"
> ```
>
> **改动 2**: 在 Step 8 之前加一个 "前置字段自检" 步骤:
> ```
> ⛔ Step 7.9 · 前置字段自检(推草稿前必跑)
> gate.py 会检查以下字段,缺任何一个都会 BLOCK:
>   - slug (Step 1.1)
>   - date (Step 1.1)
>   - north_star (Step 1.1)
>   - image_paths (Step 7.3, 0 图场景需显式写空数组 [])
>   - title / digest / author (Step 3)
>   - 所有 _pass / _real_run / _source 三件套 (各 Step)
> ```

**可选增强**: 在 `gate.py` 里把错误信息改得更友好，指出缺的字段应该在哪个 Step 写入。

**验证方式**: 故意删掉一个 frontmatter 字段，跑 gate.py，确认报错信息包含 "在 Step X 写入" 的指引。

---

## P1 · 应该修（影响效率）

### F-4 · 字数振荡

**现象**: 初稿→扩写→精简→再扩写，字数经历 4042→4671→3642→3900→3981→3995→3999→4001 共 7 次调整。

**根因**: fengyun-writer 写初稿时没有精确字数目标（只说了 4000-5000 的区间），扩写/精简时缺乏 "当前差多少字" 的反馈。

**修复方案**:

> **文件**: `~/.claude/skills/fengyun-publish/SKILL.md`
>
> **改动**: Step 3 写初稿的触发语里加字数硬约束:
> ```
> 约束: 目标字数 4200 字(不含 frontmatter)。上限 4500，下限 4100。
> 写完后用 python -c "import re; ..." 自动计数，不足 4100 则补写，超过 4500 则精简。
> 不要把 "4000-5000" 当目标——那是 lint 硬约束区间，不是写作目标。
> ```
>
> **补充**: 在 Step 6.5 改稿循环里也加类似约束："改稿后字数变动 ≤ ±10%，目标维持在 4100-4500"。

**验证方式**: 跑一次 pipeline，确认字数调整次数 ≤ 2。

---

### F-5 · Opening harness 反差感阈值

**现象**: 反差感(reframe)维度连续 2 次评分 5/10（阈值 6），直到第 3 次加入 "不是 X 是 Y" 句式才到 7/10 通过。

**根因**: `opening_signal.py` 的反差感评分逻辑可能对 "否定/转折句式" 权重过高，而对 "类比/迁移" 类反差给分偏低。"手机 App → Agent 技能" 的类比迁移被评低分。

**修复方案**:

> **文件**: `tools/opening_signal.py`
>
> **改动**: 在 `_score_reframe()` 函数里，增加 "类比迁移" 作为反差感的合法来源:
> ```python
> # 当前: 只认 "不是X而是Y" / "否定+重述" 句式
> # 新增: 认 "从A领域迁移到B领域" 的类比反差
> analogy_patterns = [
>     r"(就像|好比|类似于|跟.{2,8}一样)",
>     r"从.{2,10}(到|变成|转)",
> ]
> ```
>
> **阈值调整**: 考虑把 reframe 的及格线从 6 降到 5（观察 3 次 pipeline 数据后再决定）。

**验证方式**: 用本次 3 个试稿版本重跑 `score_opening_signal`，确认 attempt 1 的 reframe 分 ≥ 6。

---

### F-6 · R18-P1 skill 名暴露

**现象**: 初稿里出现了 "fengyun-writer"、"khazix-writer"、"wechat-ai-pubaccount-writer" 三个内部 skill 名。lint R18-P1 命中，需要改稿删掉。

**根因**: fengyun-writer SKILL.md 顶部有 ⛔ 商业机密禁令，但写初稿时 Agent 把 "自己装了哪些 skill" 的经历直接写进了文章，把内部名称暴露了。

**修复方案**:

> **文件**: `~/.claude/skills/fengyun-writer/SKILL.md`
>
> **改动**: 在 Step 2 写作约束里加一条:
> ```
> ⛔ 写个人经历时，内部工具名必须泛化:
> - "fengyun-writer" → "写文章的 skill"
> - "khazix-writer" → "另一个写作风格的 skill"
> - "wechat-ai-pubaccount-writer" → "发公众号的 skill"
> - 任何 ~/.claude/skills/ 下的目录名 → 不出现在正文里
> ```
>
> **补充**: 在 fengyun_lint.py 的 R18-P1 检测词表里加上这三个名字，确保自动化兜底。

**验证方式**: 跑 lint 确认 R18-P1 命中数 = 0。

---

## P2 · 可以修（长期优化）

### F-7 · Critic 双否决（writer persona 系统性问题）

**现象**: B 轨(huashu)和 C 轨(content-judge)都判 not_ship，理由高度一致："五项检查读起来像产品文档翻译" + "lived stake 几乎为零"。

**根因**: 这不是单篇 bug，是 fengyun-writer 在 "技术工具介绍" 类题材上的系统性弱点——容易滑入功能罗列，丢失个人叙事。

**修复方案（长期）**:

> **文件**: `~/.claude/skills/fengyun-writer/references/` (新增)
>
> **改动 1**: 新增 `tech_tool_voice.md`，收录 "技术工具类" 题材的写作模式:
> - 每个功能点必须配一个 "我跑出来的结果"
> - 禁止连续 3 段以上无第一人称
> - "它会……它会……它会……" 式被动叙述 ≤ 2 处
>
> **改动 2**: 在 corpus/growth/ 里找 1-2 篇风云写技术体验的文章作为参考样本。
>
> **改动 3**: 在 voice-dna.md Part 4 迁移规则里加:
> ```
> ### 4.9 工具体验文 → 必须有 "我跑了一遍发现了什么"
> 不写 "这个工具有 X 功能"，写 "我跑了 X 功能，发现……"
> 不写 "它支持 Y"，写 "我试了 Y，结果让我愣了一下"
> ```

**验证方式**: 下次写工具类题材时，critic B/C 至少一个判 ship。

---

### F-8 · Cover dedup 撞型（无需修）

**现象**: T1_agent 模板 7 天内用过，自动换 T3_compare。

**判定**: 这是 **设计行为**，cover_dedup.py 正确触发了替代模板。无需修复。

**建议**: 记录到 run log，30 天后统计撞型频率。如果 T1/T2 撞型率 > 50%，考虑扩充到 10 模板。

---

### F-9 · B/C 轨 revise 后未重跑

**现象**: Step 6.5 改稿后只重跑了 A 轨(score_draft=73.5)，没有重跑 B 轨(huashu)和 C 轨(content-judge)。

**根因**: 节省时间的临时决定。SKILL.md Step 6.5.6 明确要求 "回 Step 6 重跑三轨 critic"。

**修复方案**:

> **文件**: `~/.claude/skills/fengyun-publish/SKILL.md`
>
> **改动**: 在 Step 6.5.6 加 ⛔ 标记:
> ```
> ⛔ 三轨全部重跑，不许只跑 A 轨。
> B 轨和 C 轨是 binary 判断，跑一次只需要 1-2 分钟。
> 省这 2 分钟的风险是: 改稿引入了新问题但没被 B/C 抓到。
> ```
>
> **可选**: 写一个 `tools/rerun_critics.sh` 脚本，一键重跑 A+B+C。

**验证方式**: 下次 revise 循环时，确认三轨全部重跑。

---

## 实施顺序建议

```
Week 1 (P0):
  F-1 dedup 自匹配   → 改 SKILL.md, 30 min
  F-2 WebSearch 降级  → 改 SKILL.md + iti_collect.py, 1 h
  F-3 gate.py 字段    → 改 SKILL.md + gate.py 报错信息, 30 min

Week 2 (P1):
  F-4 字数振荡        → 改 SKILL.md Step 3 触发语, 15 min
  F-5 反差感阈值      → 改 opening_signal.py, 30 min
  F-6 R18-P1 skill名  → 改 fengyun-writer SKILL.md + lint 词表, 15 min

Week 3+ (P2):
  F-7 writer persona  → 新增 tech_tool_voice.md + voice-dna.md, 2 h
  F-9 三轨重跑        → 改 SKILL.md + 可选脚本, 30 min
```

## 验收标准

修完后跑一次端到端实测，目标:

| 指标 | 本次实测 | 目标 |
|---|---|---|
| 信源覆盖率 | 3/6 (50%) | ≥ 5/6 (83%) |
| Opening harness 通过次数 | 3 | ≤ 2 |
| Dedup 自匹配 | 2 次 | 0 次 |
| Lint 修复轮数 | 3 | ≤ 2 |
| Critic 首轮否决率 | 100% (B+C) | ≤ 50% |
| 字数调整次数 | 7 | ≤ 2 |
| 总耗时 | 35 min | ≤ 30 min |

---

*本清单基于 2026-05-26 首次端到端实测数据。建议 30 天后用 3 次实测数据的中位数校准阈值。*
