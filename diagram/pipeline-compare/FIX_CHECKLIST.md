# fengyun-publish Pipeline 修复清单

*基于 2026-05-26 首次完整跑通的实际执行日志*
*生成时间: 2026-05-26*

---

## P0 · 必修（阻塞下次运行质量）

### FIX-1: Preflight 红线强制执行

**问题**: we-mp-rss Docker 未启动，pipeline 静默 degraded 而非 abort。WRITE_AGENT.md 要求 "P0 全绿才允许进入任何 Step"，但实际绕过了。

**修复方案**:
- [ ] 在 `tools/iti_collect.py` 返回结果中加 `preflight_ok` 布尔字段
- [ ] 信源全空（we-mp-rss=0 且 Docker 检测失败）时，`degraded` 字段设为 `True` 并附原因
- [ ] 在 SKILL.md Step 1.0 前加 3 行 Preflight 检查提示（Claude 主线程执行）:
  ```
  1. 检查 Docker Desktop 是否运行（`docker ps`）
  2. 检查 we-mp-rss 容器是否 healthy
  3. 任一 P0 不绿 → 提示用户启动后再跑，或显式确认 degraded 继续
  ```
- [ ] **不自动 abort**（用户可能选择 degraded 继续），但必须**显式告知**

**影响**: 信源从 3/6 恢复到 5/6，选题质量提升
**工时**: 30 min
**风险**: 低

---

### FIX-2: Writer 初稿字数自驱循环

**问题**: fengyun-writer 首稿 3344 字，差 4000 下限 16%。3 轮手动扩写浪费 API 调用。

**修复方案**:
- [ ] 在 `fengyun-writer` SKILL.md Step 2（写作）末尾加自检循环:
  ```
  Step 2.8: 字数自检
  - 写完后统计中文字数
  - < 4000 → 自动扩写（优先补 lived stake 段落 + 数据分析段）
  - > 5500 → 自动精简（优先砍重复论证 + 段尾悬空句）
  - 上限 2 次自检循环
  ```
- [ ] 在 writer prompt 中加硬约束: 「**目标 4500 字，宁可写多再删，不要写少再扩**」
- [ ] 在 voice-dna.md 6.4 B 类长文规则中加: 「初稿目标 4800 字（给 lint 精简留 300 字余量）」

**影响**: 消除 Step 3→Step 4 的字数返工
**工时**: 20 min
**风险**: 低（纯 prompt 层修改）

---

### FIX-3: Frontmatter 渐进写入规范

**问题**: gate.py 首次拦截缺 7 个字段（slug/date/north_star/cover_pass/cover_path/huashu_decision_pass/image_paths），全部在 Step 7 之后才补。

**修复方案**:
- [ ] 在 SKILL.md 每个 Step 末尾的「→ 立即写入 frontmatter」块中，确认列出**该 Step 产出的所有字段**
- [ ] 补充 Step 1.1 必写: `slug` / `date` / `north_star`
- [ ] 补充 Step 7-cover 必写: `cover_pass` / `cover_path`
- [ ] 补充 Step 7.2 必写: `huashu_decision_pass` / `huashu_image_curator_real_run` / `huashu_image_curator_source` / `image_at_h2_indices`
- [ ] 补充 Step 7.3 必写: `image_paths`（list）
- [ ] 在 `gate.py` 的拦截输出中加**「该回哪个 Step 补」的建议**（当前只报缺什么字段，不报去哪补）

**影响**: 消除 Step 8 的 gate 拦截重试
**工时**: 40 min
**风险**: 低（文档 + 轻量代码改动）

---

## P1 · 应修（提升效率和质量）

### FIX-4: opening_signal reframe 维度调优

**问题**: 反差感（reframe）维度 3 次 retry 始终 0/10。regex 模式过于严格，200 字短试稿很难自然命中。

**修复方案**:
- [ ] 在 `tools/opening_signal.py` 的 `REFRAME_PATTERNS` 中扩展匹配:
  ```
  现有: "不是 X, 是 Y" 句式
  新增: "但 + 让/使 + 停/愣/想"（转折+情绪动词）
  新增: "如果你以为...那"（假设否定）
  新增: "不是...本身"（焦点转移）
  ```
- [ ] 降低 reframe 阈值: 从 4 维全部 ≥ 6 改为「**3 维 ≥ 6 + 1 维 ≥ 4**」（即允许 1 个维度较弱）
- [ ] 或: 把 reframe 从 blocker 改为 **warning**（不阻塞 dogfood gate，只记 run log）

**影响**: opening loop 从 3/3 失败降到 1/3 以下
**工时**: 30 min
**风险**: 中（需要验证新 regex 不会引入 false positive）

---

### FIX-5: fengyun_lint R0 标点自动修复前置

**问题**: 初稿 65 处半角标点（R0），全部在 Step 4 才修复。这是 writer 应该在 Step 3 做对的事。

**修复方案**:
- [ ] 在 fengyun-writer SKILL.md Step 2（写作）末尾加:
  ```
  Step 2.9: 标点自检
  - 写完后检查全文半角标点（, ; : ! ? " '）
  - 中文上下文中一律用全角（，；：！？""''）
  - 数字/英文之间的标点不动
  ```
- [ ] 或: 在 `post_fengyun_publish.py` 渲染前自动跑一次 `fix_punctuation.py`（已存在工具，只需串进去）

**影响**: 消除 60%+ 的 R0 lint violations，减少 lint 修复轮次
**工时**: 15 min
**风险**: 低

---

### FIX-6: H2 命名模板注入 writer prompt

**问题**: 初稿 6 个 H2 全部不符合花叔 3 种模式（概念陈述句/口语动词句/汉字数字），Step 4 全部重写。

**修复方案**:
- [ ] 在 fengyun-writer SKILL.md `style: huashu` 时，Step 0.1 已要求读 `references/h2_patterns.md`
- [ ] 强化: 在 Step 2（写作）中加硬约束:
  ```
  H2 标题必须命中以下 3 种模式之一:
  ① 概念陈述句（含 是/不是/就是）— 如「上下文窗口就是 AI 的记忆」
  ② 口语动词句（我/我们开头）— 如「我们来算一笔账」
  ③ 汉字数字开头（一/二/三...）— 如「一、数字背后是一场巧合」
  全篇统一选一种，不混用。
  ```
- [ ] 在 `fengyun_lint.py` R21 规则的修复建议中加**具体示例**（当前只说"不命中"，不给示例）

**影响**: 消除 R21 lint violations，减少 2-3 轮 lint 修复
**工时**: 15 min
**风险**: 低

---

### FIX-7: WebSearch 降级检测 + 替代方案

**问题**: WebSearch 在当前环境不可用，Step 1.0 和 Step 2 均无替代方案。

**修复方案**:
- [ ] 在 `iti_collect.py` 中加 WebSearch 可用性检测:
  ```python
  def check_websearch_available():
      """在主线程中调用，检测 WebSearch 工具是否可用"""
      # 返回 True/False，写入 pool_result["websearch_available"]
  ```
- [ ] WebSearch 不可用时，自动降级到 **WebFetch URL 列表**（预置 10-15 个高质量 AI 新闻 URL 模板）
- [ ] 在 SKILL.md Step 2 中加降级路径:
  ```
  如果 WebSearch 不可用:
  → 用 WebFetch 拉以下 URL（按主题关键词拼接）:
    - https://www.36kr.com/search/articles/{keyword}
    - https://www.jiqizhixin.com/search?keyword={keyword}
    - https://techcrunch.com/?s={keyword_en}
  ```

**影响**: Step 2 调研从事实 10 条提升到 15+ 条
**工时**: 45 min
**风险**: 中（WebFetch 对搜索页可能也 403）

---

## P2 · 可修（长期优化）

### FIX-8: R13 焦虑点检测算法修复

**问题**: `fengyun_lint.py` R13 规则检测到 2 个焦虑点，但实际文章有 3 个（隐私、就业、安全）。算法少检。

**修复方案**:
- [ ] 审查 `fengyun_lint.py` 中 R13 的焦虑关键词词典
- [ ] 补充关键词: 「泄露」「安全」「隐私的边界」「靠经验吃饭」「保证」
- [ ] 或: 改用 LLM 辅助判断焦虑点数量（但增加 API 调用成本）

**影响**: R13 不再误报
**工时**: 30 min
**风险**: 低

---

### FIX-9: 配图密度引导

**问题**: huashu-image-curator 决定 2 张/4900 字（0.41/千字），低于 PHASE1 爆款甜蜜区 1.5-3 张/千字。

**修复方案**:
- [ ] 在 huashu-image-curator SKILL.md Mode 2 Step 4 中加软约束:
  ```
  B 类 AI 深度长文（4000-5000 字）建议配图:
  - 最少: H2 章节数 × 0.5（即 6 个 H2 → 至少 3 张）
  - 甜蜜区: 1.5-3 张/千字
  - 花叔仍有最终决定权（允许低于建议），但 self_check.notes 必须注明原因
  ```
- [ ] 在 `fengyun_lint.py` R20 中，把 info-only 升级为 **warn**（不阻断但提醒）

**影响**: 配图密度从 0.41 提升到 ~1.0 张/千字
**工时**: 20 min
**风险**: 低

---

### FIX-10: smol.ai SSL 超时处理

**问题**: smol.ai RSS feed SSL handshake timeout，贡献 0 条。

**修复方案**:
- [ ] 在 `iti_collect.py` 中给 smol.ai 请求加 `timeout=15` 参数（当前可能用默认 timeout）
- [ ] 加 `ssl.create_default_context()` 或 `verify=False` 降级（权衡安全性）
- [ ] 如果连续 3 天 SSL 失败，自动从信源列表中临时移除并告警

**影响**: smol.ai 信源恢复可用
**工时**: 15 min
**风险**: 低

---

## 修复优先级排序

| 序号 | FIX | 优先级 | 工时 | 影响面 |
|---|---|---|---|---|
| 1 | FIX-2 Writer 字数自驱 | P0 | 20 min | 消除最大返工源 |
| 2 | FIX-3 Frontmatter 渐进写入 | P0 | 40 min | 消除 gate 拦截 |
| 3 | FIX-1 Preflight 强制 | P0 | 30 min | 信源覆盖 +2 |
| 4 | FIX-5 标点自检前置 | P1 | 15 min | 减少 60% lint 轮次 |
| 5 | FIX-6 H2 模板注入 | P1 | 15 min | 减少 R21 violations |
| 6 | FIX-4 reframe 调优 | P1 | 30 min | opening loop 通过率 |
| 7 | FIX-7 WebSearch 降级 | P1 | 45 min | 调研深度 |
| 8 | FIX-8 R13 算法修复 | P2 | 30 min | lint 准确性 |
| 9 | FIX-9 配图密度引导 | P2 | 20 min | 完读率 |
| 10 | FIX-10 smol.ai SSL | P2 | 15 min | 信源覆盖 +1 |

**总工时: ~4 小时（全部修完）**
**P0 只修: ~1.5 小时**

---

## 验收标准

修完后重跑一次完整 pipeline，验收以下指标:

| 指标 | 本次实际 | 修后期望 |
|---|---|---|
| 有效信源数 | 3/6 | ≥5/6 |
| 初稿字数达标率 | 首稿不达标，3 轮扩写 | 首稿 ≥4000 字 |
| Lint 修复轮次 | 6 轮 | ≤3 轮 |
| Opening loop 通过率 | 0/3 | ≥1/3 |
| Gate 拦截次数 | 1 次 | 0 次 |
| 配图密度 | 0.41/千字 | ≥1.0/千字 |
| 端到端耗时 | ~45 min | ≤35 min |
