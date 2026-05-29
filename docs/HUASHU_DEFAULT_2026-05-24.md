# Round 10 · 排版主力切 huashu + 7 bug 修复(2026-05-24)

## 一句话

排版从蓝灰 default 切到花叔暖米黄 huashu T-A,**内容 voice 不变**(风云本人 voice),7 个实测 bug 全修。

## 入口键变化

```yaml
---
# 2026-05-24 起的语义:
style: huashu     # 显式默认(等同不写)
# style:          # 不写也走 huashu(新默认)
# style: default  # opt-out 回原蓝灰(兼容回退路径)
---
```

## 改动文件清单

### 排版主力切 huashu

| 文件 | 改动 |
|---|---|
| `tools/layout_rules.py` | `render_to_wechat_html` 默认 `style="huashu"`,显式 `"default"` 才走原 default 渲染 |
| `tools/test_layout_rules_huashu.py` | 加新测试 `test_no_style_arg_defaults_to_huashu`;3 个老测试改成 `style="default"` 显式 opt-out |

### Bug 1 修复:CJK 冒号塞进加粗

| 文件 | 改动 |
|---|---|
| `tools/layout_rules.py:_fix_cjk_bold_punctuation` | 加开头标点踢出 regex,处理 `**标点+text**` → `标点+**text**` |

### Bug 2 修复(最致命):花叔配图位置 ↔ 渲染层闭环

| 文件 | 改动 |
|---|---|
| `tools/layout_rules.py` | 加 `_resolve_padded_urls` helper + `render_to_wechat_html` 和 `_render_huashu` 加 `image_at_h2_indices` 参数 |
| `tools/illustrate_decider.py` | 接 image_at_h2_indices(从 decision 派生 + 写 frontmatter) |
| `tools/post_fengyun_publish.py` | 从 frontmatter / CLI 读 image_at_h2_indices,透传 render_to_wechat_html |
| `~/.claude/skills/huashu-image-curator/SKILL.md` Mode 2 | JSON 输出 schema 加 `image_at_h2_indices` 字段 |

slot 编号约定:`0 = intro hero(引言后)`,`1 = H2[0]`,`2 = H2[1]`,...

### Bug 3 修复:score_draft 写错文件名

`tools/score_draft.py` 接受 CLI 第一个 argv 作为 draft 路径,无 hardcoded fallback。输出 `<slug>.scoring.json` 从 draft stem 派生(去 `-v\d+$` 后缀)。

### Bug 4 修复:style_match silent fail

`tools/sop_v2_1.py:_init_parquets` 加 stderr fail-loud warning。3 处 parquet 缺失都会显式打印警告 + 给 rebuild 提示。`tools/score_draft.py` 显示 None 时打 ⚠️ 警告。

可设 `FENGYUN_SUPPRESS_STYLE_MATCH_WARN=1` 静默(测试场景)。

### Bug 5 修复:封面路由缺财经关键词

`tools/generate_cover_by_template.py:CATEGORY_RULES["T4_news"]` 加 12 个 keyword:融资 / 估值 / 反超 / 收购 / IPO / 上市 / 烧钱 / 万亿 / 千亿 / 百亿 / 投资 / 领投。

### Bug 6 修复:WebFetch 反爬 retry wrapper

新建 `tools/safe_webfetch.py`(150 行)— urllib + 3 UA 轮换 + retry × 2,403/429 retry,其他状态直接 fail。CLI 入口 `python safe_webfetch.py <url>`。

### Bug 7 修复:R8 lint 不可替代白名单

`tools/fengyun_lint.py` ANXIETY_TRIGGERS 加 `±8 字白名单上下文检测`,豁免「不可替代 / 无可替代 / 难以替代 / 独一无二 / 不可或缺」等正面短语。

## 测试

55/55 全过(从 54 升 55,加 `test_no_style_arg_defaults_to_huashu`):

```
tools/test_layout_rules_cjk.py            18 passed
tools/test_post_fengyun_publish_image_cache.py  5 passed
tools/test_layout_rules_huashu.py          9 passed  ← +1
tools/test_post_fengyun_publish_style.py  10 passed
tools/test_fengyun_lint_huashu.py         13 passed
```

## SKILL 文档同步(Round 10)

| skill | 改动 |
|---|---|
| `fengyun-writer/SKILL.md` Step 0.1 | 说明排版默认 huashu;内容 voice 不变;style:default 是 opt-out |
| `huashu-image-curator/SKILL.md` Mode 2 | JSON 输出 schema 加 image_at_h2_indices,positions 加 h2_slot 字段 |
| `fengyun-publish/SKILL.md` Step 7-8 | Step 7 配图决策返回 image_at_h2_indices;Step 8 默认 huashu 渲染 |

## 借鉴混合后续

用户原话:「原排版作为参考给新排版补充」 — **借鉴混合方案后续单列讨论**,本次不做。

## 影响范围

- ✅ 默认 ship 走 huashu 排版(新文章自动暖米黄)
- ✅ 已 ship 草稿不动(微信草稿 media_id 不重推)
- ✅ 数据飞轮 v1 metadata 干净(bug 3/4 修了)
- ✅ 花叔配图决策真正落实(bug 2 修了)

## 不影响的部分

- ❌ Round 9 自动 dogfood gate(fengyun-self D-1 代答)— 仍未真验证
- ❌ 三轨 critic 真调 skill — 仍未真验证(本次实测我演绎了 B/C 轨)

留给下次 ship 真验证。

---

**报告人**:Claude(本次会话)
**Musk × Jobs 全程旁观**:见 ship 实测报告 + 修复报告(完整 verdict)
