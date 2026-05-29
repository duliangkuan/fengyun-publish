# 系统全景审计 · 2026-05-25 EOD

> 给风云明早 5 分钟看懂今天做完什么 + 明天该干什么。
> Round 17 + 18 + 19 三轮密集修缮后,33 个 .py 现在的分工 + 风险点。

---

## 一、tools/ 33 文件分类矩阵

| # | 文件 | 类别 | WRITE_AGENT 引用 | 被谁 import | 备注 |
|---|---|---|---|---|---|
| 1 | `gate.py` | **PROD-direct** | Step 8 守门 | `post_fengyun_publish` | Round 17/18 新生宪法保安 |
| 2 | `iti_collect.py` | **PROD-direct** | Step 1.0 | — | I-1 广搜 6 信源 |
| 3 | `iti_explore.py` | **PROD-direct** | Step 2 | — | I-2 深搜 |
| 4 | `topic_recommender.py` | **PROD-direct** | Step 1.x | — | PHASE1 数据驱动排序 |
| 5 | `event_dedup.py` | **PROD-direct** | Step 1.x | — | 7 天事件去重 |
| 6 | `opening_signal.py` | **PROD-direct** | Step 1.5 | — | 5 维评分 + 物理约束 |
| 7 | `opening_dedup.py` | **PROD-direct + support** | Step 1.5 | `ending_dedup`, `title_dedup` | 三个 dedup 共享 base |
| 8 | `title_signal.py` | **PROD-direct** | Step 3.3 | — | hook hard gate |
| 9 | `title_dedup.py` | **PROD-direct** | Step 3.3 | — | 复用 opening_dedup |
| 10 | `ending_signal.py` | **PROD-direct** | Step 3.5 | — | viral 评分 |
| 11 | `ending_dedup.py` | **PROD-direct** | Step 3.5 | — | 复用 opening_dedup |
| 12 | `fengyun_lint.py` | **PROD-direct** | Step 4 | `test_fengyun_lint_huashu` | R0/R8/R13 已修(Round 17/19) |
| 13 | `sop_v2_1.py` | **PROD-direct** | Step 6 critic A | `score_draft` | critic v2.1 数字分 |
| 14 | `critic_vote.py` | **PROD-direct** | Step 6 | — | 门控树 |
| 15 | `illustrate_decider.py` | **PROD-direct** | Step 7.1 / 7.3 | — | 日额度兜底已加(Round 18) |
| 16 | `generate_cover_by_template.py` | **PROD-direct + support** | Step 7-cover | `cover_dedup` | classify 词典已收(Round 19) |
| 17 | `cover_dedup.py` | **PROD-direct** | Step 7-cover | — | 7 天封面去重 |
| 18 | `layout_rules.py` | **PROD-direct** | Step 8 | `test_layout_rules_*` × 2 | huashu 默认 |
| 19 | `post_fengyun_publish.py` | **PROD-direct** | Step 8 | `test_post_fengyun_publish_*` × 2 | draft/update API(Round 19) |
| 20 | `safe_webfetch.py` | **PROD-direct** | Step 2 | — | UA 轮换 wrapper |
| 21 | `sop_v2.py` | **PROD-support** | — | `sop_v2_1` | v2 老核心,被 v2.1 继承 |
| 22 | `fengyun_anchor.py` | **PROD-support** | — | (sop_v2_1 在 Round 7 改造里调,运行期) | style anchor bootstrap |
| 23 | `score_draft.py` | **PROD-support** | — | — | sop_v2_1 CLI 入口 |
| 24 | `build_corpus_index.py` | **CORPUS-tools** | — | — | CLAUDE.md 引用 |
| 25 | `pick_few_shot.py` | **CORPUS-tools** | — | — | CLAUDE.md 引用 |
| 26 | `clean_corpus.py` | **CORPUS-tools** | — | — | corpus 清洗 |
| 27 | `htm_to_md.py` | **CORPUS-tools** | — | — | .htm → .md 备胎 |
| 28 | `test_fengyun_lint_huashu.py` | **TEST** | — | — | |
| 29 | `test_layout_rules_cjk.py` | **TEST** | — | — | |
| 30 | `test_layout_rules_huashu.py` | **TEST** | — | — | |
| 31 | `test_post_fengyun_publish_image_cache.py` | **TEST** | — | — | |
| 32 | `test_post_fengyun_publish_style.py` | **TEST** | — | — | |
| 33 | `notify.py` | **❓ UNCLEAR** | — | — | Windows 弹窗,开发期辅助;若 Round 17 之后没被任何 hook / script 调,建议下次归档 |

**汇总**:PROD-direct 20 / PROD-support 3 / CORPUS 4 / TEST 5 / UNCLEAR 1 = **33** ✓
(`opening_dedup` 和 `generate_cover_by_template` 同时承担 direct + support,矩阵里归 direct。)

---

## 二、架构图

### 图 A · 数据流(选题 → 草稿箱)

```
[用户主题词]
    │
    ├─ Step -1  北极星填空 ────────────────────── (runlog.jsonl)
    │
[选 题] Step 1.0/1.x/1.1
    │   iti_collect ─► topic_recommender ─► event_dedup ─► chosen
    │
[试 稿] Step 1.5
    │   fengyun-writer (200 字) ─► opening_signal ─► opening_dedup ─► fengyun-self
    │   ↺ harness × 3
    │
[深 搜] Step 2
    │   iti_explore ─► safe_webfetch ─► output/research/<slug>.md
    │
[写 稿] Step 3 / 3.3 / 3.5
    │   fengyun-writer → title_signal+title_dedup → ending_signal+ending_dedup
    │
[清 洁] Step 4 / 4.5 / 5
    │   fengyun_lint ─► humanizer-zh ─► wangxiaobo-perspective
    │
[评 审] Step 6 / 6.5 / 6.5.8
    │   sop_v2_1 (A) ║ huashu-perspective (B) ║ fengyun-self (C)
    │            ──► critic_vote.gate_tree ──► ship / revise / human_gate
    │
[视 觉] Step 7.1 / 7.2 / 7.3 / 7-cover  (并行)
    │   illustrate_decider.pick_candidates → huashu-image-curator → Seedream
    │   generate_cover_by_template → cover_dedup → Seedream
    │
[出 版] Step 8  ⛔ gate.py 守门
        layout_rules (huashu) ─► post_fengyun_publish ─► 微信草稿箱
                                                            │
                                                       (风云人工 ship)
```

### 图 B · 物理保险栈(6 层防御)

```
Layer 1 · BLOCKING step 标记       ── WRITE_AGENT.md 19 个 step 写死
Layer 2 · frontmatter pass_flag    ── 每 step 必落一字段(writer_pass / lint_pass…)
Layer 3 · PreToolUse hook          ── ~/.claude/settings.json → tools/gate.py
                                       (拦截任何 Bash 调 post_fengyun_publish.py)
Layer 4 · gate.py 字段 + 文件检查  ── 11 个 pass_flag + cover/image 物理存在
Layer 5 · preflight assertion      ── post_fengyun_publish.main() 第一行兜底
                                       (hook 失效 / 别窗口跑也守住)
Layer 6 · fake-pass 防伪 (R18)     ── gate.py 验「有 pass_flag 但跑过的 step」
                                       (Round 18 P0-1 新加,防 LLM 撒谎填字段)

           ▲ 风云人工最后一击 ◄── NORTH_STAR 红线(永不变)
```

---

## 三、WRITE_AGENT.md 同步度

**A. 宪法提了 + tools/ 都在(✅ 完全同步)**:gate / iti_collect / iti_explore / topic_recommender / event_dedup / title_signal / title_dedup / ending_signal / ending_dedup / opening_signal / opening_dedup / fengyun_lint / sop_v2_1 / critic_vote / illustrate_decider / generate_cover_by_template / cover_dedup / layout_rules / post_fengyun_publish / safe_webfetch — **20/20**。

**B. 宪法漏写但 PROD-direct 在跑**:
- ⚠️ `fengyun_anchor.py` — Round 7 P0 style anchor bootstrap,sop_v2_1 critic A 跑时会调,但宪法 Step 6 只写 `from tools.sop_v2_1 import score_draft as critic_a`,没说明 anchor 池数据从哪来。建议 Step 6 加一句「critic A 隐式依赖 fengyun_anchor 提供的 anchor pool」。
- ⚠️ `score_draft.py` — sop_v2_1 的 CLI wrapper,实际生产期能直接 import sop_v2_1.score_draft,但跑批量回填时会用 score_draft.py CLI。宪法没提,不影响 ship 主链路。

**C. 宪法提了但 tools/ 找不到**:
- ❗ `tools/verify_audit.py` — WRITE_AGENT.md Step 9 第 2 步明确写「跑 tools/verify_audit.py」,但 `ls tools/` 不存在该文件,_archive/ 也没有。**这是个 placeholder,Step 9 audit 目前其实跑不了**。明天可能要么写出来要么从宪法删掉。

**D. 已废弃工具(7 + 9 = 16 个).bak)**:_archive/ 9 个旧 post/generate 脚本 + _archive/research/ 56 个研究期废稿,Round 17/18 用 .bak 阻断 import。

---

## 四、外部资源依赖(明天可能卡的点)

| 资源 | 依赖位置 | 已知风险 |
|---|---|---|
| **豆包 Seedream API** | `illustrate_decider._call_seedream` + `generate_cover_by_template` | ⚠️ 今天实测已触发 daily quota,Round 18 兜底已 abort 后续 retry,但**明天首推可能仍在 24h 内**,继续 daily quota 兜底走 0 张图 degraded ship。**应在白天 reset 后再 ship 才能拿到内文图**。 |
| **微信公众号 API** | `post_fengyun_publish` | draft/update API 已落地(Round 19),fallback 到 draft/add 也兜住;cover_media_id 用 `https://mp-proxy-worker.dufengyun12.workers.dev` Cloudflare Worker 代理 |
| **Anthropic API**(Claude 主线程 + skills) | 全程 | 标准 anthropic-api 依赖,1M context Opus 4.7 |
| **aihot.virxact.com** | `iti_collect` | 公开 REST,无 key,挂了 → I-1 候选 -1 信源,iti_collect 自动跳过 |
| **arxiv / smol.ai / we-mp-rss / TrendRadar** | `iti_collect` | RSS / 本地缓存,通常稳;`safe_webfetch` UA 轮换兜底 |
| **corpus/{kazik,baoyu,saiboshanxin}/** | `pick_few_shot`, `build_corpus_index` | 本地静态,**不在 ship 主链路**,只在 Step 0 Voice DNA 时调 fengyun-writer skill 自己的 corpus(不是这个目录) |
| **PHASE1_FACTS + topic_hotness.parquet** | `topic_recommender`, `fengyun_anchor` | 本地 parquet,2026-05-24 之前的快照,**老化风险**:对最新主题(< 7 天)排序信号会偏弱 |

---

## 五、明日开工 — Top 3 P0 建议

### 🥇 P0-1 · 补 `tools/verify_audit.py`(宪法承诺但缺失)

WRITE_AGENT.md Step 9 写「跑 `tools/verify_audit.py` 对照 19 step 清单」,文件不存在。要么:
- (A) 写一个 ~50 行的脚本,读 `output/runs/<slug>.runlog.jsonl` + frontmatter,对照宪法 19 个 step 出报告;
- (B) 从宪法删掉这条,Step 9 简化成「打印 media_id + 草稿箱链接」。

倾向 (A),因为它是宪法承诺的 audit 闭环,Layer 6 的 fake-pass 防伪需要这条线。

### 🥈 P0-2 · Seedream daily quota reset 后跑一篇有图 ship

今天 TrapDoor 文是 0 图 degraded ship。明早 quota reset 后(豆包通常 UTC 0 点 = 北京 8 点)跑一篇完整 5 步走通 Step 7.3,验证:
- 内文图真生成 + 写 frontmatter `image_paths` + gate 物理 check 通过
- draft/update API 重推路径(因为有今天的 media_id 已在 frontmatter)
- 端到端没回归

### 🥉 P0-3 · 决定 `notify.py` 去留 + 给 `fengyun_anchor` / `score_draft` 在宪法补一句

`notify.py` 是 Windows 弹窗,Round 17 之后是否还有 hook 在用?如无,归档进 _archive/。
`fengyun_anchor` 和 `score_draft` 在 PROD chain 里实际有用,但宪法没写,Step 6 加一行就行。

---

## 六、一句话总结(系统当前健康度)

**🟢 健康**:Round 17/18/19 把宪法 + 物理 gate + 6 层保险 + 日额度兜底 + draft/update API + 3 个老 bug 一次性闭环,33 个文件分工清晰、99→33 的死代码扫荡完成,**ship pipeline 已经能在主线程跳过任意 step 时被物理拦住**。唯一遗留:`verify_audit.py` 是宪法 placeholder 还没造,Seedream daily quota 是外部依赖。

---

> 文档版本:v1.0 · 2026-05-25 EOD
> 编写依据:Read WRITE_AGENT.md + Grep tools/ 33 文件 + ls _archive/ 65 个 .bak + Read gate.py + 历史 task list 119 项
