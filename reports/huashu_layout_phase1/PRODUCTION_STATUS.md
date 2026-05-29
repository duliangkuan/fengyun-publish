# 花叔(huashu)排版模板 — 生产状态

**最后更新**:2026-05-24(Round 2 砍刀后)
**状态**:✅ 生产可用
**测试**:54/54 通过(layout huashu 8 + cjk 18 + lint huashu 13 + publish style 10 + image cache 5)
**零回归保证**:已实测(不写 `style: huashu` 时,所有行为完全等同于改动前)

## 砍刀历史(2026-05-24)

**Musk × Jobs 沙盒决议**:用户重新定位"核心是 huashu,后续追加都是锦上添花,要敢砍会砍"。两人共识 Jobs 砍刀更彻底:**砍掉 P0-1 anti-slop lint(R26-R37) + P0-4 design_directives.md**;**保留 P0-2 CJK 预处理 + P0-3 图片去重**。

**砍掉理由**:风云用 huashu 风格已经有强 style discipline(emoji=0 / CTA=0 / 色板克制),12 条"防别人乱设计"的规则用不上;writer 已有 voice-dna + huashu_rhythm + h2_patterns,第四份 reference 反而稀释注意力。

**保留理由**:CJK 预处理直接服务 huashu 视觉(中英文盘古之白本来就是 huashu 真品特征);图片去重是 10 行纯物理优化,不影响灵魂。

**净效果**:从 4 项 P0 减到 2 项 P0,fengyun_lint.py 减 422 行(1330 → 908)。

## 图片间距 bug 终修(v6 → v10,2026-05-24)

实测发现 huashu 渲染图片在**微信手机端**下方留白比上方大(桌面对称)。盲推 4 次未修(v6 加 max-width / v7 砍 img margin / v8 section → figure / v9 加 font-size 0 + line-height 0)。

**Round 3 用 huashu-nuwa 蒸馏 wechat-style-engineer skill**(综合 wenyan + baoyu + huashu-md-html 三家经验),派 2 个 Sonnet agent 调研找到真因:

**真因**:**inline style 让 margin collapse 失效** — wrapper inline `style="margin: 20px 0"` 在微信 webview 不跟相邻 H1/p 的 margin collapse,导致下方 figure.margin-bottom (20) + p.margin-top (20) = 40px;上方因为 H1.margin-bottom 在微信被压缩,只剩 figure.margin-top = 20px。**「上 20 下 40」的不对称由此产生**。

**修法**(Round 3 锁定):`_huashu_wrap_img` 的 figure style 把 `margin: 20px 0` 改成 `padding: 24px 0`(padding 算在 figure 内部,不跟相邻元素 margin 干扰)。

**v10 结果**:用户认可,10/10 测试通过,bug 真正 closed。

**配套产出**:
- `~/.claude/skills/wechat-style-engineer/SKILL.md` — 公众号样式 debug 主题 skill
- `~/.claude/skills/wechat-style-engineer/references/research/01-opensource-image-handling.md`
- `~/.claude/skills/wechat-style-engineer/references/research/02-wechat-internals.md`
- user-level memory:`feedback_inline_margin_no_collapse.md` + `reference_wechat_style_engineer.md`

---

## 使用方式(给 writer 看)

在 draft frontmatter 加 3 个字段:

```yaml
---
title: 文章标题
style: huashu                   # 触发花叔风格(可选,不写=走风云默认 voice)
theme: A                        # huashu 模板:A(默认)或 B(深红专题,显式触发)
article_type: thought_essay     # tech_demo(4-5 段/图)或 thought_essay(8-9 段/图)
---
```

然后正常跑 `tools/post_fengyun_publish.py <draft.md>` 即可。

---

## 当前 T-A 视觉配方(克制版花叔)

| 维度 | 值 | 来源 |
|---|---|---|
| 容器背景 | `#faf9f7` 暖米黄 | 花叔真品 |
| 容器 padding | `20px 24px 40px 24px` + max-width 700px | 花叔真品 |
| 正文 | 17px / 行高 1.8 / `#2b2b2b` / 字间距 -0.005em | 花叔真品 |
| 段间距 | `margin: 20px 0` | 花叔真品 |
| **H1 章节标题** | **20px / `#222` / 橙左竖边 `3px solid #C15F3C`** | **default 风格 + huashu 主色,2026-05-24 用户偏好** |
| Strong 加粗 | `#C15F3C` 文字 + `rgba(193,95,60,0.08)` 底 + 2px 6px padding + 3px radius | 花叔真品 |
| 图片 | max-height 500px / border-radius 10px / box-shadow 橙阴影 | 花叔真品 |
| `<span leaf="">` 文字包裹 | 自动 71+ 处 | 花叔真品(微信编辑器产物) |

## T-B 深红专题(显式触发,极少用)

| 维度 | 值 |
|---|---|
| 容器背景 | `#ffffff` 纯白 |
| 主色 | `#d32f2f` 深红 |
| H2 | 白字 + 红色块背景(`background-color: #d32f2f` + `padding: 12px 20px`) |

---

## 文件清单(已落地)

### 代码层

| 文件 | 改动 | 状态 |
|---|---|---|
| `tools/layout_rules.py` | 加 `_render_huashu` + 7 个 helper 函数 + yaml 加载 | ✅ |
| `tools/layout_rules_huashu.yaml` | 规则配置(template_A / template_B / common / lint_rules) | ✅ |
| `tools/fengyun_lint.py` | 加 R19-R25 huashu 规则,仅 `style: huashu` 触发 | ✅ |
| `tools/post_fengyun_publish.py` | 透传 frontmatter style / theme / article_type | ✅ |
| `tools/test_layout_rules_huashu.py` | 8/8 测试 | ✅ |
| `tools/test_fengyun_lint_huashu.py` | 13/13 测试 | ✅ |
| `tools/test_post_fengyun_publish_style.py` | 10/10 测试 | ✅ |

### Skill 文档层

| 文件 | 改动 | 状态 |
|---|---|---|
| `~/.claude/skills/fengyun-writer/SKILL.md` | 加 Step 0.1 Style 路由块 | ✅ |
| `~/.claude/skills/fengyun-writer/references/huashu_rhythm.md` | 节奏目标 + 翻译句 + 开头结尾 | ✅ |
| `~/.claude/skills/fengyun-writer/references/h2_patterns.md` | H2 三选一模板 | ✅ |
| `~/.claude/skills/fengyun-publish/SKILL.md` | Step 8 加 Style 分支表 | ✅ |

### 报告层

| 文件 | 用途 |
|---|---|
| `reports/huashu_layout_phase1/agent1-6_*.md` | 6 份调研报告 |
| `reports/huashu_layout_phase1/debate_and_verdict.md` | Musk × Jobs 辩论 + 审判官裁决 |
| `reports/huashu_layout_phase1/injection_plan.md` | 落地步骤 |
| `reports/huashu_layout_phase1/PRODUCTION_STATUS.md` | 本文 |

---

## lint 规则(R19-R25)— 只在 `style: huashu` 触发

| ID | 触发条件 | severity | 行为 |
|---|---|---|---|
| R19_huashu_avg_para_length | 平均段长 ∉ [50, 80] 字 | medium | warn |
| R20_huashu_solo_lines | <20 字独段成行 < 4 处 | medium | warn |
| R21_huashu_h2_pattern | H2 不命中 3 种模式之一 | medium | warn |
| **R22_huashu_emoji_zero** | emoji 数 > 0 | **high** | **必改** |
| **R23_huashu_cta_zero** | 含「点赞/转发/关注/扫码/二维码…」 | **high** | **必改** |
| R24_huashu_long_para_ratio | >200 字段落占比 > 8% | medium | warn |
| R25_huashu_ellipsis | 省略号 > 1 处 | medium | warn |

**关键已知 false positive**:R23 用纯关键词匹配,任何提到"转发""关注"等词的叙事句都会触发(例:「没人转发你的工作」)。改文字最快。

---

## 回滚

writer 不写 `style: huashu` 字段 → 系统**完全回到改动前的行为**。零影响。

如果发现 huashu 模板本身有 bug,临时关闭:把 draft frontmatter 的 `style: huashu` 行删除即可。

如果要从代码层关闭整条分支(极少需要):注释 `tools/layout_rules.py` 第 332 行附近 `if style == "huashu": return _render_huashu(...)` 一行。

---

## 已知限制

1. **R23 false positive**:见上,纯关键词匹配。
2. **HTML 大小逼近 20K 上限**:huashu 渲染因为 `<span leaf="">` 包裹和 inline style 重复,HTML 体积比 default 大约 3 倍。一篇 4000-5000 字的文章会到 18-22K HTML。`layout_rules.lint()` 会在 >20K 时打 warn,但不阻塞推草稿(微信实际限制更高)。
3. **首篇视觉曾偏离真品**:Phase 2 Round 1(原 32px 三色渐变)曾完整复刻真品,但 2026-05-24 用户偏好调整为 left-border。这版称为**克制版花叔**,跟真品花叔有意识区分。
4. **R21 false positive**:H2 不命中三种模式时报 warn,但实际写其他模板的文章也可以用 huashu 视觉(只是 lint 有提示)。

---

## 端到端实测(2026-05-24)

| 测试 | draft | 推送 media_id | 结果 |
|---|---|---|---|
| 简短 huashu 测试稿 | `test-huashu-draft.md`(1108 字) | (本地 preview 验证) | layout 视觉 OK |
| 真实草稿 huashu 渲染 v1 | karpathy-joins-anthropic v1 + style:huashu | `f5xAnh6tT5u4aYGYiST-AOL2qmQnHunOTScc2gzOO26O5KzTwb60MxcMQyapyM6S` | 缺暖米黄底(已修复) |
| 真实草稿 huashu 渲染 v2 | 同上 | `f5xAnh6tT5u4aYGYiST-AHlzjF0fF5D79nwjGHY6IR5Tozm0a1yufAo85Gpgpg-o` | 1:1 复刻真品(32px 三色渐变) |
| 真实草稿 huashu 渲染 v3(最终) | 同上 | `f5xAnh6tT5u4aYGYiST-AKZg-LCVfZbDB2q7_4maRjsMFg7cNXuwMjmbPHLuZA3n` | 克制版(20px left-border)— **用户认可** |

---

## 关联文档

- 辩论 + 裁决:`debate_and_verdict.md`
- 落地步骤:`injection_plan.md`
- 6 份调研:`agent1-6_*.md`
- 用户给的视觉参考:用户附件(2026-05-24 截图,3 张)
- 真品 corpus:`D:\Dev\ai-wechat-pipeline\corpus\huashu_layout_reverse\` 6 篇
