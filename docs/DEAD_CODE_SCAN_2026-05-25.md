# 死代码 + 系统冗余扫描报告

**扫描日期**:2026-05-25 Round 18
**扫描员**:调研 Agent
**范围**:`D:/Dev/ai-wechat-pipeline/tools/*.py` 共 99 个 .py 文件
**判定来源**:`WRITE_AGENT.md` 引用 + `~/.claude/skills/fengyun-publish/SKILL.md` 引用 + Python `from/import` 链 + 文件名/版本号

---

## 一、tools/ 文件总览表(99 个)

> 状态图例:✅ production / ⚠️ 支撑(被 production import)/ ❌ 死代码候选 / 🔄 重复

### A. ✅ Production(WRITE_AGENT 或 SKILL.md 直接引用)

| 文件 | 字节 | 最后改 | 引用方 |
|---|---|---|---|
| gate.py | 13606 | 05-25 10:52 | WRITE_AGENT:5/608/685/700 |
| iti_collect.py | 17204 | 05-24 22:08 | WRITE_AGENT:134, SKILL:71 (import) |
| iti_explore.py | 15605 | 05-24 22:03 | SKILL:303 (import) |
| topic_recommender.py | 13363 | 05-24 21:36 | SKILL:72 (import) |
| event_dedup.py | 11747 | 05-25 10:47 | SKILL:73/109 (import) |
| opening_signal.py | 17786 | 05-25 00:40 | SKILL:168/185/224/225 |
| opening_dedup.py | 10814 | 05-25 10:46 | SKILL:169/226 + 3 dedup import 它 |
| title_signal.py | 18175 | 05-25 10:46 | SKILL:368, WRITE_AGENT:715 |
| title_dedup.py | 10075 | 05-25 10:47 | SKILL:369 |
| ending_signal.py | 12905 | 05-24 23:06 | SKILL:452/470 |
| ending_dedup.py | 8857 | 05-25 10:47 | SKILL:453/507 |
| cover_dedup.py | 10714 | 05-25 10:48 | SKILL:985 |
| generate_cover_by_template.py | 36044 | 05-25 10:59 | WRITE_AGENT:581, SKILL:898/905 |
| illustrate_decider.py | 21344 | 05-25 10:54 | SKILL:1031/1053/1062 |
| fengyun_lint.py | 41703 | 05-25 10:54 | WRITE_AGENT:718-719, SKILL:523 |
| fix_punctuation.py | 4423 | 05-21 22:13 | SKILL:530 |
| score_draft.py | 13502 | 05-24 21:01 | SKILL:596/751 |
| critic_vote.py | 15220 | 05-24 11:03 | SKILL:624/854 |
| layout_rules.py | 45385 | 05-25 10:49 | SKILL:1119, post_fengyun_publish 透传 |
| post_fengyun_publish.py | 19528 | 05-25 10:49 | WRITE_AGENT:639/700, SKILL:1111 |
| fengyun_anchor.py | 9441 | 05-24 16:06 | score_draft.py 引用 + sop_v2_1 doc |
| safe_webfetch.py | 5305 | 05-24 20:58 | SKILL:314/328 |
| ship.py | 7700 | 05-21 23:13 | SKILL:54 (辅助 stub) |
| notify.py | 854 | 05-22 00:09 | headless_ship.ps1 (辅助) |

**小计:24 个 production / 总 401K 字节**

### B. ⚠️ 支撑工具(被 A 类 import,但本身不被 SKILL 直接引用)

| 文件 | 字节 | 引用方 |
|---|---|---|
| sop_v2_1.py | 12956 | score_draft.py:15 from sop_v2_1 import |
| sop_v2.py | 29614 | sop_v2_1.py:46 from sop_v2 import |

**小计:2 个 / 42.6K**

### C. ❌ 死代码候选(无 import 链 + 不被 WRITE_AGENT/SKILL 引用)

见第二节。

### D. 🔄 重复功能组

见第三节。

---

## 二、死代码候选(top 15)

> 判定标准:`from <file> import` / `import <file>` 全项目 0 命中 + WRITE_AGENT.md 不提 + SKILL.md 不提。

| # | 文件 | 字节 | 最后改 | 理由 |
|---|---|---|---|---|
| 1 | `flop_prediction.py` | 30069 | 05-21 09:09 | 5/21 那天写完后再没碰过;无 import;不在 SKILL/WRITE_AGENT;一次性的 ρ 探索脚本 |
| 2 | `semantic_features.py` | 29948 | 05-21 10:26 | 同上;line 712 自我宣传字符串都还在;数据探索遗物 |
| 3 | `viral_design_validation.py` | 26015 | 05-21 11:50 | 一次性 penetration test;无 import |
| 4 | `time_trend_analysis.py` | 26230 | 05-21 09:06 | 数据驱动 EDA;Phase 4 用过,Phase 8 之后 frozen |
| 5 | `topic_hotness_dynamic.py` | 27713 | 05-21 10:27 | 当年生成 topic_hotness.parquet 用的;parquet 已生成,脚本可归档 |
| 6 | `hook_power_validation.py` | 26252 | 05-21 11:47 | 一次性 penetration |
| 7 | `cover_color_deep_analysis.py` | 25825 | 05-21 09:05 | 一次性 color EDA;封面色已固化进 generate_cover_by_template |
| 8 | `brand_words_analysis.py` | 27594 | 05-21 09:03 | 一次性 brand words EDA |
| 9 | `comment_mining.py` | 23666 | 05-21 10:26 | 一次性 comment 挖掘 |
| 10 | `comments_insights.py` + `_v2.py` + `_v3.py` | 11494+12975+20597 = 45066 | 05-20 21:34 ~ 23:33 | v3 替代 v1/v2,但 v3 也没 production 引用;3 个一起死 |
| 11 | `eda.py` / `gen_data_overview.py` / `inspect_schema.py` | 10667+8970+7174 = 26811 | 05-20 19:55 ~ 20:45 | 早期数据探索 3 件套;PHASE1 跑完后 frozen |
| 12 | `extract_features.py` + `_v2.py` | 8712+6329 = 15041 | 05-20 01:51 + 05-20 20:13 | 旧版本,无 import;PHASE1 后被 sop_v2 系列取代 |
| 13 | `rigorous_validation.py` + `_v2.py` | 12964+13362 = 26326 | 05-21 07:59 ~ 08:15 | 当年的统计验证脚本,跑完一次后 frozen |
| 14 | `normalize_target.py` + `normalize_targets_v2.py` | 4302+7750 = 12052 | 05-20 01:50 + 20:15 | 旧 PHASE1 处理脚本,parquet 生成后没用 |
| 15 | `train_critic.py` + `_v0.py` + `_v1.py` + `_v2.py` | 6622+9185+7989+9516 = 33312 | 05-20 ~ 05-21 | 4 个 critic 训练历史版本,critic 路线已切 sop_v2_1 + critic_vote,这 4 个全死 |

**死代码候选小计:约 420K(15 项)**

补充次级候选(没排进 top 15 但也是死代码):
- `_e2e_inline_images.py` 5579 + `_sop_v2_corr_probe.py` 3505 + `test_fengyun_lint_huashu.py` 7888 + `test_layout_rules_cjk.py` 9331 + `test_layout_rules_huashu.py` 7610 + `test_post_fengyun_publish_*.py` 5470+6959(测试脚本可独立归类到 tests/)
- `sop_v2_penetration.py` 16936 + `sop_v2_1_penetration.py` 19803 + `sop_rules_penetration_test.py` 18674 + `penetration_test.py` 13154(4 套 penetration test,共 68.6K,全无 production 引用)
- `style_match_validation.py` 18282 + `single_var_scan.py` 10339 + `paragraph_structure_analysis.py` 16406 + `image_density_analysis.py` 11274 + `interaction_rate_analysis.py` 11016 + `publish_time_analysis.py` 11466 + `publish_time_pooled.py` 11811 + `title_deep_analysis.py` 17168 + `title_topic_analysis.py` 14617 + `title_x_content_quadrant.py` 10764 + `word_count_deep_dive.py` 13402 + `subcluster_topic0.py` 9280(12 个 PHASE1 EDA 脚本,共 156K)
- `extract_hook_formulas.py` 3903 + `dump_title_topics.py` 2516 + `fix_comment_topic_names.py` 5803 + `refill_img_count.py` 5147 + `compute_founder_anchor.py` 5025 + `check_corpus_quality.py` 1026 + `build_corpus_index.py` 5023 + `clean_corpus.py` 7525 + `clean_founder_corpus.py` 6322 + `pick_few_shot.py` 3947 + `merge_data.py` 10886 + `merge_to_sqlite.py` 9734 + `htm_to_md.py` 3171(数据 prep 一次性脚本,共 70K)
- `backup_20260521/` 整目录 50K(`sop_v2.py 29614 + sop_v2_penetration.py 16936 + _sop_v2_corr_probe.py 3505`)
- `post_fengyun_article.py` 8681 + `post_fengyun_v2.py` 8672 + `post_fengyun_v3.py` 7117 + `post_to_wechat.py` 9527 + `publish_draft.py` 9241(5 套 post,共 43.2K,WRITE_AGENT/SKILL 只用 `post_fengyun_publish.py`,且 SKILL line 1263 自己写了 "post_fengyun_publish 由 post_fengyun_v3.py 通用化")
- `generate_article_images.py` 5678 + `generate_fengyun_images.py` 4745 + `generate_fengyun_images_v2.py` 6045 + `generate_karpathy_images.py` 8754 + `inline_illustrations.py` 4774(5 套生图,SKILL 全部走 `illustrate_decider.py`,共 30K)
- `md_to_ocean_html.py` 5887 + `run_pipeline.py` 11917(旧渲染 + 旧 pipeline 编排,共 17.8K;现在走 layout_rules + SKILL.md)
- `r18_dashboard.py` 6672 + `weekly_metrics_report.py` 7195(数据飞轮 dashboard,**注意**:这俩可能是用户期望未来用到,需要风云确认)

**死代码候选总计**(top 15 + 次级):**约 870K / 99 文件中约 60 文件**

---

## 三、重复功能识别(🔄)

### 组 1:5 套 dedup 镜像(共 1447 行 / 49.4K)

| 文件 | 行数 | 字节 | base 来源 |
|---|---|---|---|
| `opening_dedup.py` | 307 | 10814 | **base**(被 title/ending import) |
| `ending_dedup.py` | 257 | 8857 | `from opening_dedup import ...` |
| `title_dedup.py` | 278 | 10075 | `from opening_dedup import ...` |
| `cover_dedup.py` | 303 | 10714 | `from generate_cover_by_template import ...`(独立,不复用 opening base) |
| `event_dedup.py` | 302 | 11747 | 独立(走 aihot 字段,不复用) |

**判定**:opening / ending / title 已经共享 base(opening_dedup 当 lib),**reasonable**;cover/event 独立合理。**不算冗余**,这 5 个全是 production。

### 组 2:critic 三件套(共 67K)

| 文件 | 字节 | 状态 |
|---|---|---|
| `score_draft.py` | 13502 | ✅ SKILL Step 6 入口 |
| `sop_v2_1.py` | 12956 | ⚠️ 被 score_draft import |
| `sop_v2.py` | 29614 | ⚠️ 被 sop_v2_1 import(legacy 底层) |
| `critic_vote.py` | 15220 | ✅ SKILL Step 6.5 入口 |

**判定**:`sop_v2.py` 29.6K 大半是 6 月以前的 PHASE1 数据来源注释 + 旧 DIM_WEIGHTS 字典,**sop_v2_1 用到的只是其中一部分**。建议把 sop_v2_1 真正用到的符号搬到自己内部,sop_v2 直接归档。

### 组 3:post_fengyun 五件套(共 43K)

| 文件 | 字节 | 最后改 |
|---|---|---|
| `post_fengyun_publish.py` | 19528 | 05-25 ✅ |
| `post_fengyun_v3.py` | 7117 | 05-21 (publish 的前身) |
| `post_fengyun_v2.py` | 8672 | 05-21 |
| `post_fengyun_article.py` | 8681 | 05-21 |
| `post_to_wechat.py` | 9527 | 05-21 |
| `publish_draft.py` | 9241 | 05-19 (用 md_to_ocean_html) |

**判定**:**只留 post_fengyun_publish**,其他 5 个共 43K 全部归档。SKILL.md line 1263 明确写了 "post_fengyun_publish 由 post_fengyun_v3 通用化",已经替代完毕。

### 组 4:generate images 五件套(共 30K)

| 文件 | 字节 | 用途 |
|---|---|---|
| `generate_cover_by_template.py` | 36044 | ✅ 封面(production) |
| `illustrate_decider.py` | 21344 | ✅ 内文图编排(production) |
| `generate_article_images.py` | 5678 | 早期内文图,无 import |
| `generate_fengyun_images.py` + `_v2.py` | 4745+6045 | 旧版,无 import |
| `generate_karpathy_images.py` | 8754 | 给 karpathy 那篇一次性写的,无 import |
| `inline_illustrations.py` | 4774 | 早期 ocean 模板用的,无 import |

**判定**:留前两个,其他 5 个共 30K 归档。

### 组 5:penetration test 四件套(共 68.6K)

| 文件 | 字节 |
|---|---|
| `penetration_test.py` | 13154 |
| `sop_v2_penetration.py` | 16936 |
| `sop_v2_1_penetration.py` | 19803 |
| `sop_rules_penetration_test.py` | 18674 |

**判定**:都是 5/21 那天的一次性验证脚本;sop_v2_1 已锁定后这些跑完没用了。全归档。

---

## 四、Top 5 优化机会(按 Idiot Index 排序)

> Idiot Index = 死代码字节 / 总字节;**越高越尴尬**(写了没用上)

### #1 一次性 PHASE1 EDA / penetration 大扫除 — 节省 ~450K

**改动**:把 `flop_prediction.py / semantic_features.py / viral_design_validation.py / time_trend_analysis.py / topic_hotness_dynamic.py / hook_power_validation.py / cover_color_deep_analysis.py / brand_words_analysis.py / comment_mining.py / comments_insights*.py / eda.py / gen_data_overview.py / inspect_schema.py / extract_features*.py / rigorous_validation*.py / normalize_target*.py / train_critic*.py / 12 个 deep analysis / 4 个 penetration_test` 全部移到 `tools/archive/phase1_eda/`。

**节省**:~450K 字节 / 30+ 文件
**心智**:开 tools/ 目录瞬间看到的文件数 99→30,production 一眼能找到
**风险**:零。这些脚本生成的 parquet/json 都在 corpus/ 已固化,脚本本身只是历史

### #2 干掉 4 个 post_fengyun 旧版本 — 节省 43K

**改动**:`post_fengyun_article.py / post_fengyun_v2.py / post_fengyun_v3.py / post_to_wechat.py / publish_draft.py` → `tools/archive/legacy_post/`

**节省**:43K / 5 文件
**心智**:Round 17 写 gate.py 防伪保安的时候,如果哪天有人误调 post_fengyun_v3.py 就**绕过 gate** 了(post_fengyun_v3 没有 gate.check_draft 调用),**这是真实的安全隐患**
**风险**:零。SKILL.md 明确说 v3 已被 publish 通用化

### #3 干掉 5 个旧 generate_images 脚本 — 节省 30K

**改动**:`generate_article_images.py / generate_fengyun_images.py / _v2.py / generate_karpathy_images.py / inline_illustrations.py` → `tools/archive/legacy_image_gen/`

**节省**:30K / 5 文件
**心智**:配图入口只有 `illustrate_decider.py` 一个,跟 SKILL.md Step 7 一致
**风险**:零。illustrate_decider 内置 fal/baoyu/jimeng 全栈

### #4 sop_v2.py 折叠进 sop_v2_1.py — 节省 ~20K(净)

**改动**:sop_v2_1.py 现在从 sop_v2.py import,但 sop_v2 是 29.6K 的 PHASE1 全表;把 sop_v2_1 真正用到的几个符号(`sop_score_v2 / DIM_WEIGHTS / 几个常量`)inline 进 sop_v2_1,然后归档 sop_v2.py 整个文件

**节省**:~20K 净
**心智**:critic 路径只剩 score_draft → sop_v2_1 → done,不再三层套娃
**风险**:低。需要小心 sop_v2 里被引用的符号别漏(grep `from sop_v2 import` 全项目只有 sop_v2_1 和已废 penetration)

### #5 数据 prep 一次性脚本归档 — 节省 ~70K

**改动**:`build_corpus_index.py / clean_corpus.py / clean_founder_corpus.py / pick_few_shot.py / merge_data.py / merge_to_sqlite.py / htm_to_md.py / fix_comment_topic_names.py / dump_title_topics.py / refill_img_count.py / compute_founder_anchor.py / check_corpus_quality.py / extract_hook_formulas.py` → `tools/archive/data_prep/`

**节省**:70K / 13 文件
**心智**:corpus/ 已 frozen,这些都是历史 prep 工具
**风险**:**中**。万一未来要重建 corpus 还得拉回来。建议 archive 不删

---

## 五、统计

| 指标 | 数值 |
|---|---|
| tools/ 总 .py 文件数 | **99** |
| tools/ 总字节(含 backup) | **约 1.18 MB** |
| ✅ Production 文件数 / 字节 | **24 / ~401 KB**(占 34%) |
| ⚠️ 支撑文件数 / 字节 | **2 / ~42.6 KB**(占 3.6%) |
| ❌ 死代码候选数 / 字节 | **~60 / ~870 KB**(占 **73.7% 字节、60.6% 文件**) |
| 🔄 重复功能组 | **5 组**(dedup 5 套 / critic 4 套 / post 5 套 / image gen 7 套 / penetration 4 套) |
| **Idiot Index** | **0.74**(870K 死代码 / 1180K 总;每写 10 行代码大约 7.4 行从此再没人 import) |

---

## 六、关键警示

> **真实安全隐患**:Round 17 写的 `gate.py` 防伪保安挂在 `post_fengyun_publish.py` 入口,但 `post_fengyun_v3.py / post_fengyun_v2.py / post_fengyun_article.py / post_to_wechat.py / publish_draft.py` **5 个旧 post 工具都没接 gate**。一旦风云或 Claude 误调,**绕过所有 gate 检查直接推草稿**。这跟 Round 18 P0-1「gate.py 加 fake-pass 防伪」是同一个性质的漏洞 — gate 兜不住「另一个调用入口」。建议优先级 P0:第一步先归档这 4 个旧 post,**而不是先动 EDA 脚本**。
