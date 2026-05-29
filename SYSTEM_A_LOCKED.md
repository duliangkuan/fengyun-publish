# System A · 卡兹克对标系统(已冻结)

*冻结时间:2026-05-21 下午第一篇草稿推送后*
*冻结决策:由风云做出,选择「双轨制」 — System A 保留,System B 新建*

---

## 系统定位

数据驱动 + 80 维 SOP + 模仿对标账号风格,在对标圈竞争。

## 冻结点

**冻结状态**:刚发完第一篇草稿(20260521-anthropic-mythos),
还没引入 Musk / Jobs 视角的「极简」之前。

之所以冻结这里,因为之后我们花大量讨论在:
- Musk「删 95%」简化建议
- Jobs「灵性 metadata 化」批判
- 「founder-driven」转型
- FengyunWriter skill 5 文件版

这些**全部属于 System B 的方向**,跟 System A 路径不同。
System A 不需要这些修正,保持原方向。

## 保留组件清单

### 文档
- `PHASE1_FACTS.md` — 1268 行,所有数据规律
- `WRITING_SOP_PRIORITIES.md` — 298 行 P0/P1/P2 SOP
- `reports/` — 全部深挖报告 / 调研 brief
- `reports/anthropic_mythos_brief.md` — 第一篇文章 brief

### 代码 / 工具
- `tools/sop_v2_1.py` — critic 主代码(ρ=0.393)
- `tools/sop_v2.py` — v2 备份
- `tools/backup_20260521/` — 完整 v2 备份
- `tools/score_draft.py` — feature extraction + 评分入口
- `tools/post_to_wechat.py` — 微信 API 推送(.env 安全版)
- `tools/generate_article_images.py` — 火山方舟出图
- 各 `tools/*_validation.py` — feature 验证脚本

### 数据
- `corpus/raw/` — 2759 篇 4 号对标(卡兹克 / 宝玉 / 赛博 / 花叔)
- `db.sqlite` — 437MB 主数据库
- `features.parquet` — 48 维结构特征
- `targets.parquet` — composite_pct 等 target
- `*_features.parquet` — 各深挖产出的派生 feature
- `style_match_features.parquet` — style_match anchor
- `topic_hotness.parquet` — 主题热度动态
- `comment_features.parquet` — 评论挖掘
- `semantic_features.parquet` — 强观点/第一手/时事

### Skills(System A 专用)
- `~/.claude/skills/wechat-ai-pubaccount-writer/`
- `~/.claude/skills/wechat-ai-pubaccount-critic/`
- 协作:khazix-writer / humanizer-zh / baoyu-cover-image / md2wechat

### 产出物
- `output/drafts/20260521-anthropic-mythos.md`
- `output/images/20260521-anthropic-mythos-cover.png` + 5 张内文图
- `output/html/20260521-anthropic-mythos.html`
- 草稿已推送公众号(media_id 在 `output/images/20260521-anthropic-mythos-cover.media_id.txt`)

## System A 后续可做的事(可选,不强制)

(这些都是 System A 路线的延伸,可以做也可以不做,不影响 System B)

- 数据飞轮自动 retrain(每月新数据)
- writer↔critic 自动循环编排
- 主题热度自动选题
- 多对标号扩充(从 4 → 10+)
- 真发布 + 真粉数据回收

## 不做的事(已切到 System B 路径)

❌ 不再追求 97 项 audit 系统性修复
❌ 不再讨论「字数 / 段长 / 排版完美」
❌ 不再引入 Musk / Jobs 极简简化
❌ 不再做 founder-driven 改造
❌ 不再讨论「风云 voice」

System A 路径就是「数据驱动 + 对标卡兹克 + 80 维 SOP」的纯粹版。

## 重启 System A 的入口

```bash
# 查看完整状态
cat PHASE1_FACTS.md

# 跑 critic 评分
python tools/score_draft.py <article.md>

# 写新文章用 writer skill
# 在 Claude 里说"用 wechat-ai-pubaccount-writer 写 X 主题"
```

## 跟 System B 的关系

```
共享:
  - corpus/raw/(对标号数据,System B 可参考但不必跟随)
  - .env / 微信 AppID + Secret(技术资源)
  - 图片生成 API key(技术资源)

互不污染:
  - 评分代码各自独立
  - Skills 各自独立
  - 产出物各自有目录
  - 数据飞轮各自有(System A 用对标 metrics,System B 用 founder feedback)
```

System A 路线**到此为止** — 后面所有讨论的转型 / 简化 / 风云化,都属于 System B。
