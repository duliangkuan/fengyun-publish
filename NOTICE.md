# NOTICE

`fengyun-publish` — **full-arch branch**(完整复杂版,Round 26 / Phase 18 累积态)
公众号「研究 Agent 的云」· 笔名「风云」

---

## 关于本分支

本分支是 `fengyun-publish` 仓库的 **完整复杂版**(原始累积架构),保留了 26 轮迭代 /
18 个 Phase 一路堆叠出来的全部代码与文档。**精简重构版**请见 `main` 分支(同一个仓库
的默认分支),那是经过 10 wave 重构后机制层精简的版本。

**两个分支的差异**:

- `main` 分支:重构精简版。代码量小、机制更清晰、对新读者友好。
- `full-arch` 分支(本分支):原始复杂版。Phase 1-18 全部历史决策与冗余路径都在。
  适合**深度二次开发**或想要了解「一个 AI 公众号 pipeline 真实演化过程」的读者。

风云本人 A/B 实测,两个版本在「单篇产出效果」上**感觉没什么差别**(机制层重构单篇
照不出来)。所以:
- 只想跑起来体验 → 用 `main`
- 想自己魔改 / 加新功能 / 研究架构演化 → 用 `full-arch`

---

## 关于本仓库的几点说明

1. **不附带 KOL 语料**:原项目的 `corpus/` 目录包含第三方 KOL 文章节选
   (用于本机风格分析),已在本开源版本中**完整移除**。
2. **不附带历史草稿**:`output/drafts/` 与 `output/research/` 不公开。
3. **不附带凭证**:`.env` / WeChat token / API key 已通过 `.gitignore` 排除。

## 致谢

本管道的若干设计思路来自下列开源工作者:

- **数字生命卡兹克** — 公众号长文风格与「横纵分析」方法论的早期参照
- **宝玉** — Anthropic / OpenAI 译文体系与 baoyu-* 系列 skill 的开源
- **花叔** — 一人公司视角、shipping velocity 哲学、`huashu-perspective` 灵感
- **赛博禅心** — AI 资讯播报体例参照

## 联系方式

  Email   : 2330304961@qq.com
  WeChat  : FengYunAgent
  公众号  : 研究 Agent 的云
