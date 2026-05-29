# Changelog

本文档记录 AI 公众号 Ship Pipeline 的版本变更历史。完整 round-by-round 历史见 [`WRITE_AGENT.md`](WRITE_AGENT.md)「版本变更日志」一节。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/);版本号策略:`Round N` 对应一次重要机制改动,通常对应一次 commit 范围。

---

## [Round 26] — 2026-05-26 · RSSHub 信源层硬化 + 首次纳入 git

### Changed
- **RSSHub 从 HF Spaces 迁移到本机 Docker** — Hugging Face Spaces 在中国大陆 IP 实测返回 HTTP 418(地区屏蔽,2026-05-26)
- `preflight.ps1` 第 5 项探活从 HF Spaces 改为 `localhost:1200` 容器 + cookie 双测
- `docs/rsshub_hf_spaces_setup.md` 标记 DEPRECATED

### Added
- `docs/rsshub_cookie_setup.md` — B 站 / 知乎 cookie 抓取 + 注入 RSSHub 容器的 5 步教程
- `README.md` · 项目入门 + 5 层架构表 + 19 Step + 三轨 critic
- `docs/architecture.svg` + `docs/architecture@2x.png` — 系统架构图(暗色 + 5 层 + 三轨 critic)
- `.env.example` — 凭证模板(微信 / Seedream / Claude / DeepSeek / Lark / TikHub)
- `.gitattributes` — 跨平台行尾统一
- `LICENSE` · All Rights Reserved
- `requirements.txt` · Python 依赖清单
- `CHANGELOG.md`(本文件)
- `SECURITY.md` — 凭证管理 + 旋转周期 + 泄漏应急
- `.pre-commit-config.yaml` — gitleaks 凭证扫描 + 大文件拦截

### Security
- 仓库首次 `git init` + push 到私有 GitHub(`duliangkuan/ai-wechat-pipeline`)
- `.gitignore` 拦截 9 类敏感文件(`.env` / `tools/.wechat_token.json` / `corpus/_credentials_backup/` / `db.sqlite` / `*.parquet` / `vendor/` / `corpus/raw/` / `*.exe` / 中间态)

---

## [Round 25] — 2026-05-25 · 文内图强制必选 + placeholder fallback

### Added
- `assets/placeholder-sketch.png`(14 KB)兜底图,Seedream 全失败时复制 N 张保证 `image_paths` 非空
- `gate.py` 硬规则:`image_paths` 非空 + 每文件 ≥ 5 KB + `image_at_h2_indices` 必填

### Changed
- `illustrate_decider.py` 三个 `return []` 出口全部改为 placeholder fallback
- 0 图 ship 路径删除(旧 Round 9 `should_illustrate: false` 已废)

### Removed
- `image_generation_degraded: true` 状态(出现即被 gate 拦)

---

## [Round 24] — 2026-05-25 · 全自动化升级

### Added
- `auto_partial_pass`(末轮 A≥65)/ `auto_abort`(A<65)自动出口,3 轮 revise 后不再等真人
- `gate.py` source pattern 正则匹配(防 source 字段拍脑袋写占位)

### Changed
- `fengyun-self` skill 重命名为 `content-judge`(从「作者本人 perspective」改为「独立第三方评委」)
- `human_gate` 路径废弃(改为自动 partial_pass / abort)

---

## [Round 23] — 2026-05-25 · huashu 高亮 2 bug 修复

### Fixed
- **Bug 1 标点错位**:`**xxx**` 高亮框前的 ASCII 引号 / 半角冒号被吸进框(`_fix_cjk_bold_punctuation` 拆分集合修复)
- **Bug 2 高亮过密**:新增 R26(每段 bold ≤ 1)+ R27(全文 ≤ 5,短文 ≤ 3),Musk × Jobs 物理约束

---

## [Round 22] — 2026-05-25 · gate 防伪扩面 + ITI 工具链小升级

### Added
- gate 防伪扩面到 **8 项**(critic 三轨 + Round 21 humanizer/wangxiaobo + Round 22 新增 writer / huashu_image_curator)
- `iti_collect.py` 默认写 `output/candidates/YYYYMMDD.json`
- `event_dedup` 扫两个 source(drafts + runs/*.json 含 media_id),解决「已发还推荐」
- `iti_explore.py` CLI 新增 `--main-source-urls` 显式注入 WebSearch URL

---

## [Round 21] — 2026-05-25 · huashu 唯一活跃路径 + 封面 / 内文图风格一致

### Removed
- `--render-mode legacy` 砍(78 行 + 13 个 helper)
- `style=default/classic` 分支砍

### Added
- 封面输出 `<slug>-cover.style_anchor.txt` sidecar,Step 7.2 huashu-image-curator 必须读
- gate 防伪加 humanizer / wangxiaobo
- `gate.py parse_frontmatter` 支持多行 YAML list
- `fengyun_lint` R12b `html_size_warn`(markdown × 5 估算超 50000 → warn)

### Changed
- HTML 上限 20000 → **60000 bytes**(对齐微信真实 65000 物理上限,留 5000 缓冲)

---

## [Round 17-20] — 2026-05-25 之前 · 反馈机制 + lint 重构

要点(从 WRITE_AGENT.md 摘录):
- **Round 17** · BLOCKING + 跨 Round 持续 validation 制度建立
- **Round 18** · 三轨 critic 防伪字段 P0-1 引入(`*_real_run` + `*_source`)
- **Round 19** · R8 / R13「替代」规则自相矛盾修复(P0-5)
- **Round 20** · 一些 lint 细节

---

## [Phase 1-9] — 2026-05 之前 · 项目奠基

完整 Phase 报告见 `reports/` 目录(80+ 篇沙盒辩论结果)。关键里程碑:
- **Phase 1** · 抓 277 篇 KOL 语料,清洗入库,建 4 个 tools/ 脚本
- **Phase 2** · 端到端手工验证打通,Cloudflare Worker 反代上线
- **Phase 3** · TrendRadar 接入 + 浏览器 UA 侵入修改
- **Phase 4** · Musk × Jobs critic 方案沙盒辩论,数据驱动设计路线锁定
- **Phase 5-6** · 封面 + 配图 + 排版深度优化(baoyu-skills 逆向)
- **Phase 7** · 封面模板 5→7,3 张图 100% 成功率验证
- **Phase 8** · 信源 22→52 升级方案
- **Phase 9** · critic-revise loop 修复,全自动 revise 打通

---

## 未来规划

### [Phase 10-16] — 上云决策(⏸ 暂停)
等本地完善后重启。已有 12 份 phase 调研报告,锁定方案:阿里云轻量 2C4G ¥199/年 + 中转 API,月 ¥52-97 全报销。

### [Layer E 数据飞轮] — v0 规划中
- 飞书 Base `fengyun_metrics` 表(13 字段)— 表未建
- 每天 30 秒手抄 5 个数字(微信不开放 read API)
- 第 30 天 `weekly_metrics_report.py` 上线(规划)
- 第 60 天 / ≥50 篇 `critic_retrain.py` 重训 critic v3(规划)
