# Round 24 user-level skill 改动清单(主线程需要落地)

> Opus 实施 agent 已完成项目内(D:\Dev\ai-wechat-pipeline\)所有改动,但 user-level skill 路径(C:\Users\23303\.claude\skills\)被 sandbox 屏蔽,本文件汇总剩余需主线程在 user-level 路径落地的精确 diff。

---

## A1 剩余:`C:\Users\23303\.claude\skills\content-judge\SKILL.md` 改动

> 主线程已完成 L1-37(身份卡 + 红线)。L38-EOF 仍需以下改动:

### 改 1:M7 整段重写(原 L199-220 附近)

**找**:
```
### M7: 冗余安全 + 真人监督(置信度门禁)

**核心**:**先备份再全上**。任何 decision_mode verdict 的置信度 < 0.7 → fallback 真人,**不硬给**。所有 verdict 都写 jsonl,30 天后用真人实际行为回填校准。

**触发场景**:
- D-1 dogfood gate 5 分量过了 3 个 → confidence 0.55 → 真人介入
- D-2 human_gate 跟历史 vote 矛盾(比如 A 60+ B ship C reject 这种没见过的组合) → 真人介入
- 任何 D-1~D-5 verdict → 写 `data/founder_feedback.jsonl`

**应用动作:**
- 置信度计算必须可机械化,不许「凭感觉」
- 每个 D-X 都有显式 fallback 条件
- jsonl 每条记录:`{timestamp, decision_type, verdict, confidence, draft_path, fengyun_actual_verdict: null}`
- 风云审阅草稿箱后(发/不发) → 回填 `fengyun_actual_verdict`

**出处:**
1. Round 7 (2026-05-24) 5 项 P0 → 风云选「先备份再全上,Musk × Jobs 监督」(MEMORY.md「critic 走路线 B + 准确性优先」)
2. critic_mode.md L155-167 数据飞轮 — 累积 30-50 条后校准 critic 判断标准

**局限**:
- 「置信度 0.7 阈值」是初始猜测,需要数据回流后校准
- jsonl 写入失败时不能阻塞主流程(IO 错误降级为 warn,不 abort)
```

**改成**:
```
### M7: 自动兜底 + 透明降级(Round 24 — 真人 fallback 已废)

**核心**:**置信度低不再叫真人**,改为输出 `degraded: true` + 系统自动走 partial_pass / auto_abort,**不阻塞 ship pipeline**。所有 verdict 都写 jsonl(数据飞轮 hook 保留 — Newton 视角强调 retain),30 天后**可由风云草稿箱审阅行为反向校准(可选,不阻塞)**,而非由真人手工回填。

**触发场景**:
- D-1 dogfood gate 5 分量过了 3 个 → confidence 0.55 → 输出 `degraded: true`,系统自动 continue
- D-2 human_gate 跟历史 vote 矛盾(比如 A 60+ B ship C reject 这种没见过的组合)→ confidence < 0.7 → degraded continue + 走 auto_partial_pass(A≥65) / auto_abort(A<65)
- 任何 D-1~D-5 verdict → 写 `data/founder_feedback.jsonl`(数据飞轮 hook)

**应用动作:**
- 置信度计算必须可机械化,不许「凭感觉」
- 每个 D-X 都有显式 degraded 条件,但**不再 fallback 真人**
- jsonl 每条记录:`{timestamp, decision_type, verdict, confidence, draft_path, degraded: bool, exit_reason: "..."}`
- 30 天后回看 jsonl,**风云草稿箱审阅行为**(发/不发)反向打 label,可选校准(不阻塞)

**出处:**
1. Round 24 (2026-05-25) 风云原话「全自动化升级」+ Musk × Jobs × Newton 共识:pipeline 不该停;最终人工动作只在草稿箱审阅那一刻
2. NORTH_STAR.md 红线:最终一击 = 草稿箱手动发出,pipeline 内任何 gate 都是工具不是人

**局限**:
- 「置信度 0.7 阈值」是初始猜测,需要数据回流后校准
- 自动 partial_pass 兜底可能降低 ship 质量,需观察数据飞轮 30 天 ship vs 反悔率
- jsonl 写入失败时不能阻塞主流程(IO 错误降级为 warn,不 abort)
```

---

### 改 2:D-1 ~ D-5 五个工作流(L230+)— 删 `fallback_to_human` 改 `degraded: true` + 自动出口

#### D-1 (L230 起)

**找**:
```
"fallback_to_human": false | true
```
**改成**:
```
"degraded": false | true   // Round 24: 原 fallback_to_human 已废,改 degraded 标记
```

**找**:
```
**fallback 条件**: confidence < 0.7 → print 5 分量 yes/no 矩阵 + 试稿全文给真人,等 y/n 回答
```
**改成**:
```
**自动出口(原 fallback 已废)**: confidence < 0.7 → 输出 `degraded: true` + verdict(按机械公式选 y 或 n),系统继续不打扰用户。jsonl 记录 degraded reason 给数据飞轮。
```

**找**:
```jsonl
{"ts": "2026-05-24T08:00:00Z", "decision_type": "D1_dogfood", "verdict": "y", "confidence": 0.9, "draft_path": "...", "voice_5dim": {"tone":"y","empathy":"y","vision":"y","typology":"y","baseline":"y"}, "fengyun_actual_verdict": null}
```
**改成**:
```jsonl
{"ts": "2026-05-24T08:00:00Z", "decision_type": "D1_dogfood", "verdict": "y", "confidence": 0.9, "degraded": false, "draft_path": "...", "voice_5dim": {"tone":"y","empathy":"y","vision":"y","typology":"y","baseline":"y"}, "draft_box_review_outcome": null}
```

#### D-2 (L269 起)

**找**(在置信度公式表里):
```
| A ≥ 60 + B reject + C ship + N=2 | **revise** | 0.65 → **fallback** | 接近上限,叫真人 |
```
**改成**:
```
| A ≥ 60 + B reject + C ship + N=2 | **revise** | 0.65 → **degraded continue** | 接近上限,继续 revise + 标 degraded |
```

**找**:
```
| A < 65 + N ≥ 3 | **abort** | 0.75 | 改不出来认输 |
```
**改成**:
```
| A < 65 + N ≥ 3 | **auto_abort** | 0.75 | 改不出来认输 — 系统自动终止 |
```

**找**:
```
| 其他没见过的组合 | **fallback** | 0.5 | M7:跟历史矛盾叫真人 |
```
**改成**:
```
| 其他没见过的组合 | **degraded continue** | 0.5 | M7:跟历史矛盾标 degraded,系统按 partial_pass / auto_abort 自动出口 |
```

**找**:
```
**fallback 条件**: confidence < 0.7 OR 历史 vote 没见过这个组合 → print 全部 verdict 上下文 + 历史决策快照给真人
```
**改成**:
```
**自动出口**: confidence < 0.7 OR 历史 vote 没见过这个组合 → 输出 `degraded: true` + decision(末轮 A ≥ 65 自动 partial_pass / A < 65 自动 abort),系统继续不打扰用户。jsonl 记录历史决策快照 + degraded reason 给数据飞轮回看。
```

#### D-3 (typography,L310 起)

**找**:
```
- article_type 模糊(800-4000 字夹层) → confidence 0.6,**fallback**(M5 边界判断需要真人)
```
**改成**:
```
- article_type 模糊(800-4000 字夹层) → confidence 0.6,**degraded continue**(M5 边界判断走自动 suggest_no_change + 标 degraded)
```

#### D-4 (改稿优先级,L344 起)

**找**:
```
- 改稿点全 P4 → confidence 0.55,**fallback**(M7:critic 可能太严,叫真人看)
```
**改成**:
```
- 改稿点全 P4 → confidence 0.55,**degraded skip**(M7:critic 可能太严,自动跳过 P4 改稿点;若仅有 P4 issue 触发 revise → 实际不改,标 degraded 继续走 critic 重投)
```

#### D-5 (选题胆量,L385 起)

(无需改动 — D-5 直接输出 cnboldness/ship_recommended,无 fallback 字段)

---

### 改 3:Part 3 跨 decision 共用 fallback 协议(原 L430-453)— 整段重写

**找原 Part 3 整段**(从 `## Part 3: 跨 decision 共用 fallback 协议` 到下一个 `---` 之前):

**改成**:
```markdown
## Part 3: 跨 decision 共用 degraded 协议(Round 24,真人 fallback 已废)

**任何 decision_mode 触发 confidence < 0.7 时,统一格式输出:**

```json
{
  "verdict": "<按机械公式的最佳猜测>",
  "confidence": "<0.0-1.0>",
  "degraded": true,
  "degraded_reason": "<具体描述,如:5 分量只过 3 个 / 历史 vote 没见过该组合 / R18 标记不确定>",
  "decision_type": "D-{1-5}",
  "slug": "<文章 slug>",
  "model_trigger": "<M1-M7 的 trigger 模型>",
  "history_snapshot_hint": "Round 4 米底色 dismissed / Round 6 封面主动纠正 / Step 6.5.8 B reject + C ship → revise(参考用)",
  "system_next_step": "harness 自动继续(D-1 → next step; D-2 → auto_partial_pass / auto_abort; D-3/4 → suggest_no_change)"
}
```

**系统读这个 JSON**:
- D-1 degraded → 标 frontmatter `dogfood_degraded: true`,自动进 Step 2
- D-2 degraded → 进 `_auto_exit_result()` 看末轮 A 分,A ≥ 65 → auto_partial_pass / A < 65 → auto_abort
- D-3/4 degraded → 不改 typography / 不重排 fixes,跳过该轮 suggestions
- 所有 degraded 写一行到 `data/founder_feedback.jsonl`(数据飞轮 hook)

**风云草稿箱审阅后(可选 — 不阻塞)**:30 天后回看 jsonl,看 degraded ship 跟非 degraded ship 的「最终被发出 vs 被弃」差异,反向校准 0.7 阈值。回填动作可选,不写也不影响 pipeline 运行。
```

---

### 改 4:Part 4 数据飞轮接口(L457-475)

**找**:
```jsonl
{"ts":"<ISO>","decision_type":"D1|D2|D3|D4|D5","slug":"<slug>","draft_path":"<path>","verdict":"<verdict>","confidence":<float>,"fallback_to_human":<bool>,"fengyun_actual_verdict":null,"matched":null,"note":""}
```

**改成**:
```jsonl
{"ts":"<ISO>","decision_type":"D1|D2|D3|D4|D5","slug":"<slug>","draft_path":"<path>","verdict":"<verdict>","confidence":<float>,"degraded":<bool>,"degraded_reason":"<str|null>","draft_box_review_outcome":null,"matched":null,"note":""}
```

**找**:
```
**风云草稿箱审阅完(发/不发) → 回填**:
- 风云发出 → `fengyun_actual_verdict: "ship"`,`matched: verdict == "ship"`
- 风云不发 → `fengyun_actual_verdict: "abort"`,`matched: verdict == "abort"`
- 风云改了再发 → `fengyun_actual_verdict: "ship_after_revise"`,`matched: verdict == "revise"`
```

**改成**:
```
**风云草稿箱审阅完(可选,不阻塞)→ 反向校准(可由脚本自动监测公众号草稿箱状态,无需手工回填)**:
- 风云发出 → `draft_box_review_outcome: "ship"`,`matched: verdict in ("y", "ship")`
- 风云不发 → `draft_box_review_outcome: "abort"`,`matched: verdict in ("n", "abort", "revise")`
- 风云改了再发 → `draft_box_review_outcome: "ship_after_manual_edit"`,`matched: verdict == "revise"`

**回填动作不阻塞 pipeline,数据飞轮 v2 重蒸馏触发条件不变(累积 ≥ 30 条 + matched 比例分析)。**
```

---

### 改 5:Part 5 诚实边界(L479-489)

**找**:
```
1. ❌ **不替代风云草稿箱审阅 + 点发出**(NORTH_STAR 红线 + M4 出处)
...
5. ❌ **不替代** fengyun-writer 写文章(M5 路由 — 写作请求拒绝)
6. ❌ **不替代** huashu-perspective 灵魂判断(M5 — 选题胆量自己做,但情感锚点/选题元认知协作 huashu)
7. ❌ **不替代** wangxiaobo-perspective 中文语感判断(M5 — translation_tone 命中时让王小波出手)
8. ❌ **不为了「decision 跑通」给虚假高置信度**(M7 — 宁可叫真人也不让 harness 翻车)
```

**改成**:
```
1. ❌ **本评委不参与发布动作,仅做内容裁决**(NORTH_STAR 红线 — 最终人工动作只在草稿箱审阅 + 点发出那一刻)
...
5. ❌ **不做 writer 工作**(写作请求路由到 fengyun-writer — 本评委是 critic,不是 writer)
6. ❌ **不做灵魂层裁决**(灵魂层走 huashu-perspective — 本评委做 voice / Vision / 排版合规;选题胆量协作但不独断)
7. ❌ **不做中文语感裁决**(中文语感走 wangxiaobo-perspective — 本评委 translation_tone 命中时引用王小波 verdict)
8. ❌ **不为了「decision 跑通」给虚假高置信度**(M7 — 宁可输出 degraded 也不让 harness 误判)
```

---

### 改 6:所有「fengyun-self」/「我是风云」/「我即用户」/「风云本人」字符替换

在剩余文本(L38-EOF 没被以上 5 项 patch 覆盖的部分)做字符替换:

| 原文 | 改成 |
|---|---|
| `fengyun-self` | `content-judge` |
| `我是风云` | `本评委独立工作` |
| `我即用户` | `本评委独立工作` |
| `替风云判断` | `独立裁决` |
| `代答` | `自动判定` |
| `风云本人 decision skill` | `内容评委 skill` |

`Part 6 引用清单`、`Part 7 self-review` 等小节里指明 corpus 出处的 `fengyun-self / 风云本人 / 风云原话` **保留**(那是历史出处,不能改),但作为「**本评委的评判标准来源**」表述。

---

### 改 7:文件结尾归属(L537-541)

**找**:
```
> 本 Skill 由 [女娲 · Skill造人术](https://github.com/alchaincyf/nuwa-skill) 生成
> 蒸馏自:风云本人(「研究Agent的云」公众号作者)
> 战略核心模式 ON:聚焦 decision-time verdict,非全人格
> 蒸馏日期:2026-05-24
> 数据飞轮 v0:`~/.claude/skills/fengyun-self/data/founder_feedback.jsonl`(空文件,等真实数据回流)
```

**改成**:
```
> 本 Skill 由 [女娲 · Skill造人术](https://github.com/alchaincyf/nuwa-skill) 生成
> 蒸馏自:风云 AI 公众号 IP 的客观评委标准(「研究Agent的云」公众号 voice / Vision / 排版 / 选题 / 改稿 5 维)
> 战略核心模式 ON:聚焦 decision-time verdict 作为独立第三方裁决,非代表用户本人
> 蒸馏日期:2026-05-24(原 fengyun-self,Round 24 重新定位为 content-judge:2026-05-25)
> 数据飞轮 v0:`~/.claude/skills/content-judge/data/founder_feedback.jsonl`(空文件,等真实数据回流)
```

---

## A4 剩余:`C:\Users\23303\.claude\skills\fengyun-publish\SKILL.md` 改动

### 改 1:Step 1.1 / 1.2 / 1.3 删用户确认

**找**(L126 附近 Step 1.1):
```
1. 从用户输入抽出核心事件。如果只给了主题词(如「Anthropic 新规」),直接确认:**「核心事件是 X 吗?」** 得到 yes 才继续
   - 如果用户没指定 → 用 Step 1.0 数据驱动选题 top 1
```

**改成**(Round 24:全自动选,不等用户回答):
```
1. 从用户输入抽出核心事件。如果只给了主题词(如「Anthropic 新规」)+ 已跑过 Step 1.0 数据驱动选题 → 自动取 ranked top 1(不再等用户 binary verdict)
   - 用户只给主题词但没跑 Step 1.0 → 先跑 Step 1.0 自动选,再走本步
   - 用户介入只在最终草稿箱审阅那一刻(NORTH_STAR 红线)
```

**找**(L136 附近 Step 1.2):
```
- 不阻塞但要风云 confirm「确认要重发同事件吗」
```

**改成**:
```
- 不阻塞;auto_selected_topic 标记 `auto_selected_duplicate: true`,自动选下一个候选(若全 7 天撞型 → auto_abort)
```

### 改 2:Step 1.5 改 fallback 真人 → degraded continue

**找**(L266 附近):
```
   - `fallback_to_human=true` (confidence < 0.7) → 按 fengyun-self Part 3 fallback 协议 print 5 分量矩阵 + 试稿全文 + 历史快照给风云,等真人 y/n
```

**改成**:
```
   - `degraded=true` (confidence < 0.7) → 按 content-judge Part 3 degraded 协议自动 continue,frontmatter 标 `dogfood_degraded: true` + `dogfood_degraded_reason: "<reason>"`,不打扰用户
```

**找**(L292 附近):
```
- **fengyun-self skill 不存在** → 回退到旧版「强制等风云回答 y/n」流程,记 `degraded.dogfood_decision = "fengyun-self skill missing, fallback to human"`
```

**改成**:
```
- **content-judge skill 不存在** → 自动 degraded continue(0 风险路径),记 `degraded.dogfood_decision = "content-judge skill missing, auto-continue"`
```

### 改 3:Step 6 Track C 引用 fengyun-self → content-judge(多处)

**找 1**(L635-643):
```
#### Track C · fengyun-self skill(founder voice,binary)— Round 9 蒸馏 + Round 18 lock

- **主路径**:`~/.claude/skills/fengyun-self/SKILL.md`(2026-05-24 蒸馏,decision-time perspective skill)
  ```
  用 fengyun-self 评 output/drafts/YYYYMMDD-<slug>-v0.md,
  输出:风云愿不愿意挂名(binary,yes / no) + 改稿点(具体到段落)。
  ```
- **降级路径**:若 fengyun-self 不存在 → 回 `~/.claude/skills/fengyun-writer/references/critic_mode.md`
- 都不存在 → **C 轨缺席**,记 `degraded.C = "fengyun-self missing"`
```

**改成**:
```
#### Track C · content-judge skill(独立第三方评委,binary)— Round 24 fork 自 fengyun-self

- **主路径**:`~/.claude/skills/content-judge/SKILL.md`(2026-05-25 fork,独立 critic skill)
  ```
  用 content-judge 评 output/drafts/YYYYMMDD-<slug>-v0.md,
  输出:挂名意愿(binary,yes / no) + 改稿点(具体到段落)。
  本评委独立工作,不代表用户本人,评判标准源自该 IP 5 维客观公理。
  ```
- **降级路径**:若 content-judge 不存在 → 回 `~/.claude/skills/fengyun-writer/references/critic_mode.md`
- 都不存在 → **C 轨缺席**,记 `degraded.C = "content-judge missing"`
```

**找 2**(L645):
```
**fengyun-self 是什么**:Round 9 用 huashu-nuwa 蒸馏的风云本人 decision-time skill,5 个 decision_mode 工作流(D-1 ~ D-5)替风云在 ship pipeline 各 gate 自动回答(dogfood / human_gate / typography / 改稿方向 / 选题胆量)。Critic mode 是其中 D-2 / D-4 的副产物。
```

**改成**:
```
**content-judge 是什么**:Round 24 fork 自 fengyun-self skill,5 个 decision_mode 工作流(D-1 ~ D-5)在 ship pipeline 各 gate 自动判定(dogfood / 自动出口 / typography / 改稿方向 / 选题胆量),独立第三方裁决不代表用户。Critic mode 是其中 D-2 / D-4 的副产物。原 fengyun-self skill 已退役。
```

**找 3**(Step 6.5.8 section 大块,L804-860):
搜索文件内所有 `fengyun-self` 字符串,全部替换为 `content-judge`。

**找 4**(L838):
```
D-2 置信度公式见 fengyun-self/SKILL.md Part 2 表格:
```

**改成**:
```
D-2 置信度公式见 content-judge/SKILL.md Part 2 表格:
```

**找 5**(L849):
```
   - `confidence < 0.7` 或 `fallback_to_human=true` → 进 L2(下面的步骤 1-4 Round 2 共识方案)
```

**改成**:
```
   - `confidence < 0.7` 或 `degraded=true` → 直接走自动出口(A ≥ 65 → auto_partial_pass / A < 65 → auto_abort),不再退回 Round 2 共识(L2 已废)
```

**找 6**(L852-855 数据飞轮 path):
```
**数据飞轮 v1 自动 log**:把 D-2 verdict 写一行到 `~/.claude/skills/fengyun-self/data/founder_feedback.jsonl`:
```

**改成**:
```
**数据飞轮 v1 自动 log**:把 D-2 verdict 写一行到 `~/.claude/skills/content-judge/data/founder_feedback.jsonl`:
```

### 改 4:Step 6.5.8 整节改自动出口

**找**(L859 起整个 L2 部分):
```
**L2(D-2 fallback 时)Round 2 共识方案** — 停 + 推荐 A 分最高版本 + 等真人:
```

**改成**:
```
**Round 24:L2 已废 — 全部自动出口**:

D-2 输出 degraded(L1 confidence < 0.7) → 直接调 `_auto_exit_result()`:
- 末轮 A ≥ 65 → `decision: "ship", auto_partial_pass: true`,进 Step 7 封面
- 末轮 A <  65 → `decision: "abort", auto_abort: true`,终止 pipeline
- 末轮 A 缺(工具链断)→ `decision: "abort", auto_abort: true, reason: "末轮 A 缺"`

frontmatter 必填 `auto_partial_pass: true` 或 `auto_abort: true`(取代原 `human_gate_decision`)。
```

**找**(L884-887):
```
   - `human_gate` → ⛔ **停止自动循环**。打印 `recommended_version` + `recommended_draft_path` 让风云人工挑。**不自动跑 Step 7(封面)和 Step 8(推草稿)**
   - `aborted_r18` → 跳过 Step 7,所有 draft + lint 甩给风云人工修 P0 段
   - `ship` → 6.5.7 末轮判 pass,正常进 Step 7(不应出现在 6.5.8 子流程里)
   - `abort` → A 轨缺,人工修 sop_v2_1 工具链
```

**改成**:
```
   - `ship` + `auto_partial_pass: true` → 自动 partial_pass 兜底,进 Step 7(封面)
   - `abort` + `auto_abort: true` → 自动终止 pipeline,runlog 标记
   - `aborted_r18` → 跳过 Step 7,所有 draft + lint 甩给风云人工修 P0 段(R18 仍是唯一保留的真人介入)
   - `abort`(无 auto_abort 字段) → A 轨缺,工具链断
```

---

## A4 user-memory:`C:\Users\23303\.claude\projects\C--Users-23303\memory\project_ai_wechat_progress.md`

**找**(L147 附近):
```
- fengyun-self skill 蒸馏(Round 9,Decision-time skill,代答 dogfood/human_gate)
```

**改成**:
```
- fengyun-self skill 蒸馏(Round 9 → Round 24 fork 重命名为 content-judge,Decision-time skill,自动判定 dogfood/自动出口)
```

---

## A4 删 fengyun-self skill 目录

最后(确认以上改动落地 + 跑通一次 ship 后):

```bash
rm -rf "C:/Users/23303/.claude/skills/fengyun-self/"
```

content-judge 已经 fork 了 fengyun-self 的全部 data/ + references/,删除原 skill 不会丢数据。

---

## 验证

完成上述改动后跑:

```bash
cd D:/Dev/ai-wechat-pipeline
python -m pytest tools/ --tb=short    # 应该 77/77 全绿(已验)
python tools/gate.py output/drafts/20260525-trapdoor-claudemd-attack-v0.md   # 应仍报缺其它字段,但不会因为新 pass_flag 改动炸
```

grep 验证:

```bash
grep -r "fengyun-self" ~/.claude/skills/    # 应只在 content-judge/ 内引用「原 fengyun-self」类历史注释
grep -r "fengyun-self" D:/Dev/ai-wechat-pipeline/    # docs/ + output/ 历史档案外,active 代码应只剩转换注释
```
