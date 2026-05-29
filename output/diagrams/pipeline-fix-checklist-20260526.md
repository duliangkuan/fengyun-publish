# fengyun-publish Pipeline 修复清单

*基于 2026-05-26「从笑话到武器」全流程实测*
*生成时间: 2026-05-26*

---

## 概览

| 优先级 | 数量 | 说明 |
|--------|------|------|
| P0 必修 | 3 | 阻塞下次 ship 的硬伤 |
| P1 强烈建议 | 4 | 下次 ship 大概率会踩的坑 |
| P2 可选优化 | 3 | 提升自动化率但不阻塞 |

---

## P0 · 必修 (下次 ship 前必须修)

### P0-1 · gate.py 字段预写模板

**问题**: 本次 gate.py 阻断 3 次，分别缺 slug/north_star、image_paths、Track B/C 字段。每次阻断都需要手动 Edit 补字段再重跑。

**根因**: 各 Step 写 frontmatter 时没有统一的"gate 需要什么"清单，字段分散在 9 个 Step 里，容易漏。

**修复方案**:
1. 在 Step 1 完成后，一次性写入 gate.py 需要的全部基础字段 (slug, north_star, cover_path 占位)
2. 在 `gate.py` 或 `ship.py` 里加一个 `preflight_fields_check()` 函数，在 publish 前扫描 frontmatter 缺失字段并打印修复建议，而不是只报 "缺 N 个 step 产物"
3. 把 gate.py 的错误信息从 "image_paths 缺失或空" 改为 "image_paths 缺失 — 请在 frontmatter 加:\nimage_paths:\n  - output/images/<slug>-01.png"

**影响**: 消除 3 次阻断中的 2 次
**工作量**: 小 (改 gate.py 的报错逻辑 + ship.py 加预写)

---

### P0-2 · WebSearch 环境修复

**问题**: 本次 WebSearch 工具完全不可用（返回训练数据而非实时搜索结果），导致 Step 2 深搜仅靠 aihot 单源，信源覆盖不足。

**根因**: Claude Code 的 WebSearch 工具在当前环境未正确配置（可能是代理/网络/权限问题）。

**修复方案**:
1. 确认 WebSearch 在 Claude Code 中是否可用：运行 `WebSearch("test query")` 检查返回
2. 如果不可用，检查 Claude Code 设置中的网络配置
3. 备选：在 `iti_explore.py` 里接入备用搜索 API（如 SerpAPI / Bing API），不依赖 Claude Code 内置 WebSearch

**影响**: 调研信源从 1 个 (aihot) 恢复到 5+ 个
**工作量**: 小 (配置检查) ~ 中 (备用 API 接入)

---

### P0-3 · WebFetch 反爬绕过

**问题**: 本次 4 次 WebFetch 全部失败 (X 403, IT之家 403, 9to5Mac 404, Bloomberg 403)，核心事件源无法获取详情。

**根因**: WebFetch 工具的 UA / headers 被主流网站反爬检测拦截。

**修复方案**:
1. 在 `iti_explore.py` 里用 requests + 自定义 UA + proxy 实现 `safe_webfetch()`，不依赖 Claude Code 内置 WebFetch
2. 对 X/Twitter 源走 TikHub MCP (已有 xiaohongshu 工具，但 Twitter 需要单独接入)
3. 对中文科技媒体 (IT之家/36氪/机器之心) 接 RSS 源 (we-mp-rss 已有基础设施)

**影响**: 调研事实从 13 条 (仅 aihot) 恢复到 20+ 条
**工作量**: 中 (safe_webfetch 封装 + RSS 接入)

---

## P1 · 强烈建议 (下次 ship 大概率踩坑)

### P1-1 · fengyun-writer 内部流程封装

**问题**: 本次 invoke 了 fengyun-writer skill，但实际是主线程手写初稿（读了 voice-dna + corpus 后直接写），skill 内部的 Step 0-3 工作流未自动执行。

**根因**: fengyun-writer 是一个 skill 定义（SKILL.md），不是一个可执行脚本。Claude 在长上下文中容易"跳过"skill 内部流程直接写。

**修复方案**:
1. 把 fengyun-writer 的 Step 0 (读 voice-dna + corpus) 封装为 `tools/fengyun_prepare.py`，自动输出 context 文件
2. 在 `ship.py` 的 Step 3 里先跑 `fengyun_prepare.py`，再 invoke writer skill
3. 或者：在 SKILL.md 里加一个 `CHECKLIST` 字段，gate.py 检查 writer 是否真跑了每个子步骤

**影响**: 确保初稿质量稳定在 fengyun-writer 标准
**工作量**: 中

---

### P1-2 · 三轨 Critic 并行调度

**问题**: 本次 Track A 先跑完，然后才补跑 Track B 和 Track C。非并行导致:
- B/C 延迟填写 → gate.py 阻断
- 上下文长度限制 → B/C 被迫在后续对话中补跑

**根因**: Claude Code 的 Skill tool 不能真正并行 invoke 多个 skill。每次 invoke 都是串行的。

**修复方案**:
1. 在 `ship.py` 里用 `subprocess.Popen` 并行启动 3 个 Python 进程:
   - `score_draft.py` (Track A)
   - `critic_vote.py --track B --draft <path>` (Track B wrapper)
   - `critic_vote.py --track C --draft <path>` (Track C wrapper)
2. 3 个进程全部完成后，`critic_vote.py --merge` 合并结果
3. Track B/C 的 wrapper 脚本调用 LLM API (而非 skill invoke)

**影响**: 三轨并行 → 单次 gate 通过
**工作量**: 大 (需要把 huashu-perspective 和 content-judge 封装为可脚本调用的 API)

---

### P1-3 · R13 焦虑检测算法修复

**问题**: 本次 lint R13 报 "前 60% 只建立 0 个焦虑点"，但文章实际有 3 个明确焦虑点（隐私风险、窗口缩短、创业公司淘汰）。检测算法漏判。

**根因**: `fengyun_lint.py` 的 R13 检测器使用关键词匹配，但文章的焦虑点用的是自然语言表达而非预设关键词。

**修复方案**:
1. 扩展 R13 关键词词典: 加入 "不安""缩小""淘汰""崩""等不起了""活不下来""不得不面对""紧张" 等
2. 或改用 LLM 判断: 在 R13 检测器里加一个 `llm_check_anxiety_points()` 函数，用小模型扫描前 60% 是否有 ≥3 个焦虑点
3. 最简方案: 把 R13 从 high 降为 medium (info-only)，不阻断 ship

**影响**: 消除 partial_pass → lint_pass
**工作量**: 小 (关键词扩展) ~ 中 (LLM 判断)

---

### P1-4 · huashu-image-curator 真调保障

**问题**: 本次 huashu-image-curator skill 未真调（context length 限制），直接手动生成了 1 张图。gate.py 初始阻断就是因为 `huashu_image_curator_real_run: false`。

**根因**: skill invoke 在长上下文中容易被跳过。

**修复方案**:
1. 把 huashu-image-curator 的核心逻辑封装为 `tools/huashu_image_decision.py`，接受 draft path + candidates，输出 JSON decision
2. 在 `ship.py` Step 7.2 里调用这个脚本而非 invoke skill
3. 脚本输出直接写入 frontmatter，确保 gate.py 能读到

**影响**: Step 7.2 从 "手动" 变 "自动"
**工作量**: 中

---

## P2 · 可选优化 (提升自动化率)

### P2-1 · iti_collect.py 接入

**问题**: 本次 Step 1 选题靠手动 curl aihot API + 人工排序。`iti_collect.py` 脚本存在但未跑。

**修复**: 在 `ship.py` Step 1 里自动跑 `python tools/iti_collect.py --hours 24`，输出候选池。
**影响**: 选题从手动变自动
**工作量**: 小 (脚本已存在，只需接入)

---

### P2-2 · opening_signal.py 集成到 writer 流程

**问题**: 本次 dogfood gate 的 3 关评分是手动调用 `opening_signal.py` 的 Python API。预期是 fengyun-writer skill 内部自动跑。

**修复**: 在 fengyun-writer SKILL.md 的 Step 1.5 里明确写 "必须调用 `tools/opening_signal.py score_opening_signal(text)` 并检查 verdict=pass"。
**影响**: dogfood gate 从手动变自动
**工作量**: 小 (SKILL.md 文档更新)

---

### P2-3 · 前端 HTML preview 自动打开

**问题**: 本次 `post_fengyun_publish.py` 输出了 HTML preview 路径但没有自动打开。

**修复**: 在脚本末尾加 `os.startfile(html_path)` (Windows) 或 `open html_path` (Mac)。
**影响**: 风云审阅更方便
**工作量**: 极小

---

## 修复后的预期效果

| 指标 | 本次实测 | 修复后预期 |
|------|----------|------------|
| gate.py 阻断 | 3 次 | 0 次 |
| WebSearch 可用 | ❌ | ✅ |
| WebFetch 成功率 | 0% | 60-80% |
| 三轨并行 | ❌ | ✅ |
| Lint violations | 3 (partial) | 0 (pass) |
| 自动化率 | 46% (6/13) | 85% (11/13) |
| 总耗时 | ~45 min | ~30 min |

---

## 修复优先级排序

```
本次修 (P0):
  P0-1 gate.py 字段预写     → 消除阻断     → 1h
  P0-2 WebSearch 环境检查    → 恢复信源     → 30min
  P0-3 WebFetch 反爬绕过     → 恢复深搜     → 2h

下次修 (P1):
  P1-1 writer 流程封装       → 稳定初稿质量  → 3h
  P1-2 三轨并行调度          → 单次 gate 通过 → 4h
  P1-3 R13 算法修复          → lint 清零     → 1h
  P1-4 image-curator 封装    → 自动配图      → 2h

有空修 (P2):
  P2-1 iti_collect 接入      → 自动选题      → 30min
  P2-2 opening_signal 集成   → 自动 dogfood  → 30min
  P2-3 HTML preview 自动打开 → 审阅体验      → 10min
```

---

*此清单基于单次实测数据，修复后建议用不同主题再跑 1-2 次验证。*
