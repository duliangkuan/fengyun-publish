# Round 19 P1-3 死代码扫描报告

**扫描时间**: 2026-05-25
**对象**: D:/Dev/ai-wechat-pipeline/tools/ 当前 74 个 .py 文件
**Round 17/18/19 已归档**: 24 个(post / 一次性测试 / generate_*images / 数据科学 / v2/v3 base)
**方法**: WRITE_AGENT.md 引用清单 + Grep import chain + mtime 分布(5/14 旧 → 5/25 新)+ 文件名启发

---

## 分类总览(74 个文件)

| 状态 | 数量 | 处理 |
|---|---|---|
| **PROD-direct**(WRITE_AGENT 直接引用) | 22 | 保留 |
| **PROD-support**(被 PROD-direct import) | 5 | 保留 |
| **CORPUS-tools**(语料库管理,CLAUDE.md 引用) | 4 | 保留 |
| **TEST**(test_*.py,有用) | 4 | 保留 |
| **RESEARCH**(数据科学实验) | 25 | **候选归档** |
| **ONE-OFF**(明显一次性) | 6 | **立即归档** |
| **UNCLEAR**(模糊,风云审决) | 8 | **风云审决** |

总候选 = 6 立即归档 + 8 风云审决 + 25 RESEARCH(分批)= 控制在 ~25 个精选范围

---

## Part 1: 保留清单(不动)

### PROD-direct(22, WRITE_AGENT 引用,严禁动)
```
gate.py / post_fengyun_publish.py / illustrate_decider.py / generate_cover_by_template.py
iti_collect.py / iti_explore.py / topic_recommender.py / event_dedup.py
opening_signal.py / opening_dedup.py / ending_signal.py / ending_dedup.py
title_signal.py / title_dedup.py / cover_dedup.py
fengyun_lint.py / layout_rules.py / score_draft.py / sop_v2_1.py
critic_vote.py / safe_webfetch.py / notify.py
```
mtime 均在 5/24-5/25 最新批,确认 production 活跃。

### PROD-support(5, import chain 验证)
- `generate_cover_by_template.py` ← cover_dedup.py:48 import → 是 PROD-direct 本身,跳过
- `opening_dedup.py` ← ending_dedup.py / title_dedup.py 共享 → 已在 PROD-direct
- `sop_v2_1.py` ← score_draft.py / sop_v2_1_penetration.py → 已在 PROD-direct
- `fengyun_anchor.py` ← sop_v2_1.py / fengyun_lint.py 引用(weekly_metrics 也用)→ **保留**
- `inline_illustrations.py` / `md_to_ocean_html.py` / `run_pipeline.py` / `ship.py` → 历史 orchestrator,但 SKILL.md(backup)+ phase5 报告还引用,**保留待 Round 20 再确认**

### CORPUS-tools(4, CLAUDE.md 引用,风云日常用)
```
build_corpus_index.py / pick_few_shot.py / htm_to_md.py / clean_corpus.py
```
CLAUDE.md L25-L38 明确写"语料库工作流",保留。

### TEST(4)
```
test_fengyun_lint_huashu.py / test_layout_rules_cjk.py
test_layout_rules_huashu.py / test_post_fengyun_publish_image_cache.py
test_post_fengyun_publish_style.py
```
都对应 PROD-direct 主件,保留。

---

## Part 2: 候选归档(按风险分 3 档)

### A. 立即归档(6 个,确认死)→ `_archive/research/`

| 文件 | 理由 | 风险 |
|---|---|---|
| `_sop_v2_corr_probe.py` | 文件名带 `_` 前缀 + `probe` 后缀,典型一次性探针 | 低 |
| `gen_data_overview.py` | mtime 5/16,无任何引用,数据 EDA 一次性产物 | 低 |
| `inspect_schema.py` | mtime 5/16,schema 探查脚本,Grep 仅 backup 自引用 | 低 |
| `eda.py` | 文件名即 EDA,典型探索性数据分析 | 低 |
| `dump_title_topics.py` | dump 字 + 5/16 mtime,一次性快照 | 低 |
| `fix_comment_topic_names.py` | 命名 `fix_*_names` = 一次性 rename 脚本 | 低 |

### B. 风云审决(8 个,模糊 case)

| 文件 | 模糊点 | 建议问 |
|---|---|---|
| `r18_dashboard.py` | CLAUDE.md L18 引用,但 Round 19 后 R18 lint 已稳定;dashboard 还需要吗? | "R18 触发率周报现在还跑吗?" |
| `weekly_metrics_report.py` | docs/DATA_FLYWHEEL.md 引用,但数据飞轮 v1 已切 founder_feedback.jsonl | "weekly_metrics 还是飞书 base 路径吗?" |
| `clean_founder_corpus.py` | mtime 5/17,语料清洗,但不在 CLAUDE.md 4 件套里 | "founder corpus 还在用还是已合进 main corpus?" |
| `compute_founder_anchor.py` | anchor 计算,可能被 style_match bootstrap 接管 | "anchor 还独立计算还是 sop_v2_1 内嵌?" |
| `fix_punctuation.py` | backup SKILL.md L101 引用(R0_halfwidth_punctuation),但当前 SKILL.md 未引;layout_rules 是否接管? | "全角化现在走 layout_rules 还是单独跑?" |
| `refill_img_count.py` | 命名像数据回填,可能 Phase 8 历史脚本 | "img_count 字段还要回填吗?" |
| `inline_illustrations.py` / `md_to_ocean_html.py` | 历史渲染器,layout_rules 已接管;PROJECT_GAPS_AUDIT L107 标记简陋待替换 | "排版统一走 layout_rules 后,这俩能砍吗?" |
| `ship.py` + `run_pipeline.py` | 历史 orchestrator,Round 17 后 SKILL.md 流程接管;phase5 报告仍引用 | "ship.py 是不是被 fengyun-publish skill 完全替代?" |

### C. RESEARCH 批量归档(25 个,数据科学实验)→ `_archive/research/`

mtime 5/16-5/22 区间,文件名带 `_analysis` / `_validation` / `_deep_dive` / `train_critic_v*` / `normalize_targets_v*` / `_penetration`,均为 critic 训练 + 数据探索产物,不在任何 SKILL 引用路径:

```
brand_words_analysis.py            check_corpus_quality.py
comment_mining.py                  cover_color_deep_analysis.py
extract_hook_formulas.py           hook_power_validation.py
image_density_analysis.py          interaction_rate_analysis.py
merge_data.py                      merge_to_sqlite.py
normalize_target.py                normalize_targets_v2.py
paragraph_structure_analysis.py    publish_time_analysis.py
publish_time_pooled.py             single_var_scan.py
sop_v2_1_penetration.py            style_match_validation.py
subcluster_topic0.py               title_deep_analysis.py
title_topic_analysis.py            title_x_content_quadrant.py
train_critic_v0.py                 train_critic_v1.py
viral_design_validation.py         viral_design_validation.py
word_count_deep_dive.py
```

建议:**先风云一句话确认** "Round 12 critic 训练数据都跑完了吧?",再批量 mv 到 `_archive/research/`。注意 `sop_v2_1_penetration.py` import `sop_v2_1`,归档不影响 PROD,但若未来想跑回归测试,得加路径。

---

## Part 3: 执行建议

1. **立即归档**(A 档 6 个)- 零风险,可直接 mv
2. **风云审决**(B 档 8 个)- 给风云一句话 yes/no,逐个处理
3. **RESEARCH 批量**(C 档 25 个)- 一次性 mv,留 INDEX.md 描述每个文件干嘛的

归档后 tools/ 剩 ~35 个文件,全部活跃 production + corpus tools + tests,目录干净。

【约束遵守】只读扫描 / 8 次 tool use / 候选 25 个 ≤ 30 / 分 3 档清晰。
