# Session Handoff — huashu 排版模板生产嵌入 + 开源生态借鉴

**日期**:2026-05-24
**项目**:`D:\Dev\ai-wechat-pipeline\`(fengyun-publish)
**用户**:风云(笔名),「研究Agent的云」公众号主理人
**目的**:这份报告把本次会话的系统升级交代清楚,让接手的 Claude 实例不用从头看对话就能继续。

---

## 0. TL;DR — 一段话快进版

本次会话给 fengyun-publish 系统加了「**花叔(huashu)排版模板**」,frontmatter `style: huashu` 触发分支渲染,**完全零回归**(不写 style 字段时行为与改动前一致)。逆向工程从 6 篇花叔真品 HTML 抽 inline style,1:1 复刻外层 section 容器 + body + strong + img,但 **H1 章节标题用 default 模板的 left-border 风格而非真品的 32px 三色橙渐变**(2026-05-24 用户偏好调整,称「克制版花叔」)。同时调研了 GitHub 开源公众号生态,从 baoyu-skills / xiaohu-wechat-format 借鉴了 2 项小改动(CJK 中英文混排预处理 + 图片上传 dict cache),其他借鉴(anti-slop lint / SHARED_DESIGN_DIRECTIVES)被 Musk × Jobs 沙盒辩论砍掉。**54/54 测试通过**,**6 篇草稿已推到微信草稿箱实测**,最后一篇 v6 修了一个图片溢出容器的 bug(`max-width: 100%`)。

---

## 1. 入口键(给下一个会话的 writer 看)

writer 在 markdown frontmatter 加 3 个可选字段触发 huashu 模板:

```yaml
---
title: 文章标题
style: huashu                   # 触发花叔风格(不写 = 走风云默认 voice,零回归)
theme: A                        # huashu 模板:A(默认暖橙)/ B(深红专题,显式触发,极少用)
article_type: thought_essay     # tech_demo(4-5 段/图) / thought_essay(8-9 段/图)
---
```

**不写 style 字段** → 整套 fengyun-publish 9 步流程行为完全等同于本次会话之前。

---

## 2. 当前 huashu T-A 视觉配方(克制版花叔)

| 维度 | 值 | 来源 |
|---|---|---|
| 容器 | `<section style="background-color: #faf9f7 !important; padding: 20px 24px 40px 24px; max-width: 700px; margin: 0 auto;">` | 花叔真品 1:1 |
| 正文 `<p>` | 17px / 行高 1.8 / `#2b2b2b` / 字间距 -0.005em / margin 20px 0 | 花叔真品 1:1 |
| **H1 章节** | **20px / `#222` / 橙左竖边 `3px solid #C15F3C`**(default 模板风格,非真品渐变) | **2026-05-24 用户偏好** |
| `<strong>` 加粗 | `#C15F3C` 文字 + `rgba(193,95,60,0.08)` 底 + 2px 6px padding + 3px radius | 花叔真品 1:1 |
| `<img>` | max-width 100% + max-height 500px + 圆角 10px + 橙阴影 | 真品 + max-width fix |
| 文字包裹 | 所有文字外包 `<span leaf="">`(微信编辑器原生产物) | 花叔真品 1:1 |
| 文末标记 | `<section><span leaf=""><br></span></section>` + `<p style="display: none;"><mp-style-type data-value="3"></mp-style-type></p>` | 花叔真品 1:1 |

**Why H1 不用真品渐变**:用户偏好「克制」,觉得真品 32px 三色渐变(`#C15F3C 0% → #e97d5b 50% → #CC8B7A 100%`)太抢眼。改成 default 模板的 left-border + huashu 主色作为 border 颜色,保持色系一致。

---

## 3. 关键文件清单(全部生产路径,LIVE)

### 代码层

| 文件 | 关键改动 |
|---|---|
| `D:\Dev\ai-wechat-pipeline\tools\layout_rules.py` | + `_render_huashu` + 8 个 huashu helper(_huashu_container_style / _huashu_h1_style / _huashu_strong_style / _huashu_img_style 等) + `_preprocess_cjk`(中英文盘古之白) + render 入口的 style 分支 |
| `D:\Dev\ai-wechat-pipeline\tools\layout_rules_huashu.yaml` | 新文件,template_A / template_B / common 配置,8.7KB |
| `D:\Dev\ai-wechat-pipeline\tools\fengyun_lint.py` | + R19-R25 huashu 规则(仅 frontmatter style=huashu 触发);R26-R37 anti-slop 一度添加后被 Jobs 砍刀砍掉(净 908 行) |
| `D:\Dev\ai-wechat-pipeline\tools\post_fengyun_publish.py` | + `--style/--theme/--article-type` argparse;frontmatter > CLI > default 三级优先;`_IMAGE_UPLOAD_CACHE` 图片上传去重 |

### Skill 文档层(`~/.claude/skills/` user-level)

| 文件 | 改动 |
|---|---|
| `fengyun-writer/SKILL.md` | + Step 0.1 Style 路由块(说明 frontmatter style 字段触发额外加载 references) |
| `fengyun-writer/references/huashu_rhythm.md` | 新建:段单位 59 字 / 三件套节奏波形 / 翻译句 / 开头钩子 / 结尾零 CTA |
| `fengyun-writer/references/h2_patterns.md` | 新建:H2 三选一模板(概念陈述句 / 口语动词句 / 汉字数字编号) |
| `fengyun-publish/SKILL.md` | Step 8 加 Style 分支表 |

### 测试(全部通过)

| 文件 | 状态 |
|---|---:|
| `test_layout_rules_huashu.py` | 8/8 |
| `test_layout_rules_cjk.py` | 18/18 |
| `test_fengyun_lint_huashu.py` | 13/13 |
| `test_post_fengyun_publish_style.py` | 10/10 |
| `test_post_fengyun_publish_image_cache.py` | 5/5 |
| **合计** | **54/54** |

---

## 4. lint 规则全清单

### 通用规则(始终触发,不依赖 style)
- R0-R18(default 规则,本次会话未动)

### huashu 规则(仅 frontmatter `style: huashu` 触发)
- R19_huashu_avg_para_length warn:平均段长 50-80 字
- R20_huashu_solo_lines warn:<20 字独段成行 ≥ 4 处
- R21_huashu_h2_pattern warn:H2 命中 3 种模式之一
- **R22_huashu_emoji_zero error**:emoji 必须为 0
- **R23_huashu_cta_zero error**:不含 CTA 模式(点赞/转发/关注/扫码/二维码等)
- R24_huashu_long_para_ratio warn:>200 字段落占比 ≤ 8%
- R25_huashu_ellipsis warn:省略号 ≤ 1 处

**R23 已知 false positive**:纯关键词匹配,叙事句里出现「转发」「关注」会触发(例:「没人转发你的工作」)。改文字最快。

**已砍**:R26-R37 anti-slop(12 条,曾添加约 300 行)— Musk × Jobs 沙盒辩论砍刀决议:风云用 huashu 风格已自带强 style discipline,12 条「防别人乱设计」规则用不上。

---

## 5. 借鉴的开源项目(已 clone 到 vendor/)

`D:\Dev\ai-wechat-pipeline\vendor\` 下:

| 仓库 | star | 用途 |
|---|---:|---|
| `baoyu-skills` | 19.3k | 4 主题 × 13 颜色 × frontmatter + EXTEND.md 三层优先级(JimLiu) |
| `wenyan` | ~1k | Apache 2.0,MCP 原生公众号发布生态(caol64) |
| `huashu-md-html` | 659 | 花叔本人的 md/html 双向流水线 + 4 套反 AI slop 主题(alchaincyf) |
| `xiaohu-wechat-format` | 496 | 30 套 CSS 主题(xiaohuailabs) |
| `html-anything` | 4.7k | 75 Skills × 9 输出表面 + juice CSS inline(nexu-io) |

**深读报告**:`reports/vendor_codedive_baoyu_huashu.md` + `reports/vendor_codedive_wenyan_xiaohu_htmlanything.md`

### 借鉴落地(保留 2 项)

| 项 | 来源 | 落地位置 |
|---|---|---|
| **CJK 中英文混排预处理** | xiaohu-wechat-format `format.py:232-282` (MIT) | `layout_rules.py` `_preprocess_cjk` |
| **图片上传 dict cache** | baoyu-skills `wechat-api.ts:196-228` | `post_fengyun_publish.py` `_IMAGE_UPLOAD_CACHE` |

### 借鉴被砍(2 项)

| 项 | 来源 | 砍掉原因 |
|---|---|---|
| **R26-R37 anti-slop lint** | huashu-md-html `anti-ai-slop.md` | Jobs 砍刀:huashu 已自带 emoji=0 / CTA=0 / 色板克制,12 条规则用不上 |
| **SHARED_DESIGN_DIRECTIVES 前置注入** | html-anything `shared.ts:6-38` | Jobs 砍刀:writer 已有 voice-dna + huashu_rhythm + h2_patterns,第四份 reference 稀释注意力 |

---

## 6. 已推草稿箱实测记录(全部用 karpathy-joins-anthropic-huashu-test.md)

| 版本 | media_id | 验证点 | 结果 |
|---|---|---|---|
| v1 | `f5xAnh6tT5u4aYGYiST-AOL2qmQnHunOTScc2gzOO26O5KzTwb60MxcMQyapyM6S` | 首推 huashu 风格 | 缺暖米黄背景 → 用户反馈不行 |
| v2 | `f5xAnh6tT5u4aYGYiST-AHlzjF0fF5D79nwjGHY6IR5Tozm0a1yufAo85Gpgpg-o` | 1:1 复刻真品(32px 三色渐变) | 用户嫌渐变太抢眼 |
| v3 | `f5xAnh6tT5u4aYGYiST-AKZg-LCVfZbDB2q7_4maRjsMFg7cNXuwMjmbPHLuZA3n` | left-border H1 | **用户认可** |
| v4 | `f5xAnh6tT5u4aYGYiST-AIKZRx-9laDQ3Ms56SL59pIIswug7d-hbfwEkrlAtSma` | + CJK + 图片去重(纯文字稿) | 零回归(0.8% byte diff 只是 CJK 处理) |
| v5 | `f5xAnh6tT5u4aYGYiST-AOD7SqQm7oh2wl3Fx8TRzHs1plP8ac6Pdi00kTwF_zkM` | + 5 张内文图(1 张重复测去重) | 去重 cache ✅ 但图片溢出容器 ❌ |
| v6 | `f5xAnh6tT5u4aYGYiST-APqmC5q-s8fmc2D8wjT2SNeKS5bg_oF4CCYjlsQd7hRY` | 修 max-width 100% | **最新,待用户手机确认** |

测试稿:`D:\Dev\ai-wechat-pipeline\output\test-huashu\20260524-karpathy-joins-anthropic-huashu-test.md`

封面:`D:\Dev\ai-wechat-pipeline\output\images\20260524-karpathy-joins-anthropic-v1-cover.png`(及 01-05 五张内文图)

---

## 7. 已知 issue / TODO

### Open(影响小,未修)

1. **CJK `fix_cjk_bold_punctuation` false positive**:中文 `:**xxx**` 被改成 `**:xxx**`(全角冒号被错误搬进 strong)。视觉影响:冒号被加粗 + 橙底高亮。整篇文章触发 1 处。修法:调 regex 方向(应该把标点踢出加粗,不是搬入)。30 分钟工作量。
2. **HTML 体积接近 20K**:huashu 渲染因 `<span leaf="">` 包裹 + inline style 重复,HTML 体积约 default 的 3 倍。lint 在 >20K warn,但微信实际限制更高,不阻塞 push。
3. **`<img class="rich_pages wxw-img">` 微信会剥 class**:lint warn 但 inline style 都在(`max-width / max-height / border-radius / box-shadow`),class 被剥不影响视觉。这条 warn 可以忽略或在 lint 里把它 silence。

### Closed(本会话已修)

- ✅ huashu render 缺暖米黄背景 → 加外层 `<section>` 容器
- ✅ H1 渐变颜色错(原 agent 调研归纳成「橙绿」,真品是「橙→橙红→粉橙」)→ 1:1 复刻 → 后又改 left-border
- ✅ 图片溢出容器 → `_huashu_img_style` 加 `max-width: 100%`
- ✅ EMOJI_PATTERN 误把 CJK 汉字范围(U+4E00-U+9FFF)当 emoji → R22 那次修复保留区间到不重叠的 emoji block

---

## 8. 核心教训(已入 memory)

### `feedback_real_html_is_source_of_truth.md`(新建)

视觉风格逆向工程时,**真品 HTML inline style 才是 source of truth**。Agent 凭频率统计 / 归纳给出的「抽象规则」容易跑偏 — 本次会话第一次派 6 个调研 agent 归纳,完全漏掉最外层 `<section>` 容器的 background-color,导致首次渲染缺暖米黄底。**逆向必须包含最外层容器节点**,渲染产物要跟真品在浏览器并排做视觉 diff。

### `project_ai_wechat_huashu_status.md`(新建)

huashu 模板生产状态快照。下次问起「huashu 排版」/「调一下花叔风格」时,先读这条 + `PRODUCTION_STATUS.md`。

### `MEMORY.md` 索引已更新两条加入上述 memory。

---

## 9. 下次接续可选行动(P0 / P1 / P2)

### P0(本会话遗留,1 小时内可做)

- 修 CJK fix_cjk_bold_punctuation false positive(`tools/layout_rules.py` 调 regex 方向)
- 用户手机看 v6 后,如果图片溢出修复了 → 写一篇真正的新文章 huashu 风格 ship

### P1(中期,1-2 天)

- 借鉴 baoyu EXTEND.md 三级配置链 → 加「系统默认风格」层,免得每篇都写 frontmatter
- 借鉴 xiaohu `data-darkmode-*` 属性 → 微信深色模式适配(60 行)
- 借鉴 baoyu placeholder 两段式流水线 → 渲染/发布解耦(为未来跨平台铺路)

### P2(架构性,需要规划)

- 把 huashu 拆成 layout × palette 矩阵(借鉴 xiaohu)→ 新增 KOL 模板零代码
- 用 wechat-article-exporter Docker 持续采集对标号语料 → 数据飞轮素材库
- 逆向更多 KOL 风格(`style: khazix` / `style: baoyu`)

### 不建议

- ❌ 加新 lint 规则(huashu 已 7 条 + default 19 条够用)
- ❌ 引入 Pandoc / juice 等外部依赖(技术栈不匹配)
- ❌ doocs/md / mdnice 等 Web 编辑器模式(跟全自动 harness 冲突)

---

## 10. 给接手 Claude 的快速 onboarding 路径

按这个顺序读 5 个文件,15 分钟入门:

1. **本文**(SESSION_HANDOFF_2026-05-24.md)— 概览
2. `D:\Dev\ai-wechat-pipeline\reports\huashu_layout_phase1\PRODUCTION_STATUS.md` — 生产清单
3. `~/.claude/projects/C--Users-23303/memory/project_ai_wechat_huashu_status.md` — 用户偏好 + 状态
4. `~/.claude/projects/C--Users-23303/memory/feedback_real_html_is_source_of_truth.md` — 核心教训
5. `D:\Dev\ai-wechat-pipeline\tools\layout_rules_huashu.yaml` — 规则配置全貌

需要看代码实现:
- `D:\Dev\ai-wechat-pipeline\tools\layout_rules.py`(_render_huashu 函数在第 ~700-830 行)
- `D:\Dev\ai-wechat-pipeline\tools\fengyun_lint.py`(R19-R25 huashu 在 ~第 600+ 行)
- `D:\Dev\ai-wechat-pipeline\tools\post_fengyun_publish.py`(style 透传 + image cache)

需要看 vendor 参考:
- `D:\Dev\ai-wechat-pipeline\vendor\` 下 5 个项目
- `D:\Dev\ai-wechat-pipeline\reports\vendor_codedive_*.md` 两份深读报告

---

**报告结束**。任何疑问先 Read 本文档 + memory,不要凭印象。

— 2026-05-24,Claude(本次会话整理)
