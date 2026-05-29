# Musk × Jobs A/B/C 执行监督员手册
*sonnet 自由交流监督 · 2026-05-22*

---

## 自由对话（4 轮）

**Musk**：我先说执行顺序的物理约束。A（替换封面）和 B（headless 试跑）、C（改 config.yaml）的依赖图是这样的——B 和 C 完全独立，A 的封面文件已经存在（`output/images/20260521-anthropic-mythos-fengyun-v4-cover-phase7.png`，Phase 7 Phase F 已出图）。用户给的顺序是 A → C → B，但 B 才是最长的（15-30 分钟，还是 Opus agent），应该最早启动。我的推荐：**C → A → B 并行**，C 纯 YAML 编辑 5 分钟，A 纯文件操作 5 分钟，然后 B 这个 Opus agent 开跑，期间主对话可以干别的。把最长的任务放最后且异步。这是 Idiot Index 最低的顺序。

**Jobs**：顺序我一会儿说。我先盯 B 的主题选择。主对话提了「Claude Skills 设计哲学」这个主题——这个我有意见。从「Real Artists Ship」角度看，headless 试跑的目的不是出一篇好文章，是**验证 9 步流程全通**。用什么主题，对验证来说几乎没区别。但如果必须选一个，「Claude Skills 设计哲学」有一个隐患：这个主题没有时效性新闻锚点，调研（Step 2）可能拿不到 7 天内的新鲜事实，会触发 fengyun-writer 的「凭空写」警报。建议换一个**当下有具体事件**的主题，比如「Anthropic 最近一周发布了什么」——这样调研有真实内容，整条链路都在真实负载下跑，信息比 Skills 哲学这种纯概念题更丰富。

**Musk**：同意 Jobs 的主题判断。「Claude Skills 设计哲学」是个好主题，但 headless 试跑不是为了写出好文，是为了**找到流程里的断点**。你想让 agent 在调研环节就卡住吗？选一个有新闻素材的主题，让 agent 跑到更后面的步骤，才能测试 lint / critic / 封面 / 推草稿这几个真正复杂的节点。推荐主题：「Anthropic 发布 Claude 4.7 / Claude 新功能速览」或者「DeepSeek 最近动态」——两个都有近期事实可抓，且能触发 T4_news 或 T1_agent 模板路由，覆盖面广。

**Jobs**：现在说顺序。Musk 的「C → A → B 异步」对效率是最优的，但我补充一个条件：**A 必须在 B 之前完成，原因是 B 试跑的 headless 流程最终会推草稿到公众号草稿箱，如果 v4 草稿封面没先换好，两件事可能在草稿箱里撞车**——一个旧封面的 v4 草稿和一个新主题的 headless draft 同时在里面，风云会搞混。所以 A 必须是 B 开始之前的 P0 前提。最终顺序：**先 C（5 分钟，并行意义不大），再 A（5 分钟），再 B 开跑（Opus，异步等结果）**。这就是 C → A → B（顺序执行，B 异步）。

---

## 推荐执行顺序

- **第 1 步：C**（改 TrendRadar config.yaml 接入 P0 信源，派 Sonnet agent，30 分钟）
  - 理由：纯配置操作，无任何前置依赖，Sonnet 可以同时开，不占主对话时间太多
  - 但必须先 backup 再改，agent 完成后主对话验证 yaml 语法

- **第 2 步：A**（替换 v4 草稿封面为 phase7 新版，主对话执行，5 分钟）
  - 理由：封面文件已存在，只需重命名/替换 + 可能重推草稿；必须在 B 之前清理干净草稿箱状态

- **第 3 步：B**（试跑 headless 全自动新主题，派 Opus agent，15-30 分钟）
  - 理由：最长任务，主题选「当下有事件」的，跑完等 Opus 返回结果

---

## A 任务监督手册

### 必须验证
- `output/images/20260521-anthropic-mythos-fengyun-v4-cover-phase7.png` 存在且文字 100% 准确（Phase 7 Phase F 已出图，但要人眼确认一次再操作）
- 替换动作：把该文件**重命名为**（或 copy 为）`output/images/YYYYMMDD-anthropic-mythos-fengyun-v4-cover.png`（去掉 `-phase7` 后缀使其成为正式命名）
- 若要重推草稿到公众号：确认 `.env` 里 `WECHAT_APPID` / `WECHAT_SECRET` 有效
- 重推前确认 v4 draft 的 `output/drafts/YYYYMMDD-anthropic-mythos-v4.md` frontmatter 里 title / digest 仍正确

### 不许做的
- **不许直接覆盖**原 v4 草稿文本内容——只换封面图，正文不动
- **不许重跑 generate_cover_by_template.py 生成新图**——Phase 7 已出图，重跑浪费 API 成本且可能出不同风格
- **不许**把 phase7 测试图（`phase7_test_t4.png` / `phase7_test_t6.png`）当 v4 封面——只用 v4 专属的那张（文件名含 `anthropic-mythos-fengyun-v4`）

### 完成判定
- 公众号草稿箱里的 v4 草稿，封面缩略图已更新为 phase7 新版（宝玉风格，Anthropic 字母无 typo）
- 或：若选择不重推（只本地留档），`output/images/` 里 v4 正式封面文件名已去掉 `-phase7` 后缀，且风云确认看过图

---

## B 任务监督手册（派 Opus agent 前必须 brief 它的事）

### agent prompt 必须包含

```
你是 fengyun-publish orchestrator。工作目录：D:\Dev\ai-wechat-pipeline\
任务：用 fengyun-publish skill 走完整 L0→L7 流程，主题是：「[主题]」
注意：
1. Step 2 调研必须找到 7 天内的真实事件/新闻，不许凭空写
2. Step 7 封面优先用 tools/generate_cover_by_template.py，失败才降级
3. Step 8 推草稿：推到公众号草稿箱即可，不要发出
4. 每步完成后在 output/runs/ 下追加日志
5. 如果 lint 3 轮过不了，停止并报告卡在哪里，不要无限循环
```

### 主题推荐（任选一个有时效性的）
- 「Anthropic 本周 AI 新功能速览 —— 作为一人公司我只在意这 3 件」
- 「DeepSeek 最新动态 —— 国内大模型这周又怎么了」
- 「Claude Code 最新更新 —— headless 模式能做什么」

**不推荐**：「Claude Skills 设计哲学」（纯概念，7 天内无新闻锚点，Step 2 调研会空转）

### agent 必须实测
- Step 4 lint 必须跑到 `n_violations == 0`，输出 `*.lint.json`
- Step 6 critic 三轨：A 轨必须跑（`python tools/score_draft.py`），B/C 轨降级记录
- Step 7 封面：`generate_cover_by_template.py` 至少尝试一次，输出 `*-cover.png`
- Step 8：`post_fengyun_publish.py` 推草稿，返回 `draft_media_id`
- 最终 Step 9 报告 print 出来（含 critic 三轨结果 + draft_media_id）

### 完成判定
- `output/runs/YYYYMMDD-<slug>.json` 存在，包含 `draft_media_id`（非 null）
- `output/images/YYYYMMDD-<slug>-cover.png` 存在（封面已出图）
- lint 最终 0 violations
- 公众号草稿箱可见新草稿

---

## C 任务监督手册

### 改 config 前必须 backup
```
cp D:\Dev\TrendRadar\config\config.yaml D:\Dev\TrendRadar\config\config.yaml.backup_20260522
```
backup 路径：`D:\Dev\TrendRadar\config\config.yaml.backup_20260522`（参考 Phase 7 已有 `backup_20260521` 目录的习惯）

### 接入顺序（P0 先，不要一次性全上）

**Day 1 批（agent 本次必须完成的）**：
1. 修改现有 Hacker News URL → `?points=100` 版（1 行改动）
2. 删除 `nvidia-newsroom` 条目（或注释掉）
3. 在 `rss.feeds` 里加入 **8 个国际 T2 newsletter**（Phase 8 Phase 6 YAML 块已给出完整代码，直接抄）：
   - OneUsefulThing / Ahead of AI / Algorithmic Bridge / Ben's Bites / SemiAnalysis / Simon Willison / GitHub Trending Python / Google Research Blog
4. 加入 **3 个国内网页 RSS**：机器之心 / 极客公园 / IT之家
5. 在 `D:\Dev\TrendRadar\config\ai_interests.txt` 末尾追加中文 AI 公司关键词（DeepSeek / Kimi / 通义 / 智谱 / MiniMax / 阶跃 / 百川）

**Day 2 批（本次 agent 不做，标记为 TODO）**：
- we-mp-rss 公众号接入（需要 Docker 在线 + 扫码，agent 无法自动完成）
- ai_analysis_prompt.txt 加 Tier 权重指令（等 Day 1 跑过一次再加，避免未测试的配置叠加）

### 完成判定
- `config.yaml` 语法合法：`python -c "import yaml; yaml.safe_load(open('D:/Dev/TrendRadar/config/config.yaml'))"` 无报错
- 新增的 11 个条目（8 国际 + 3 国内）全部出现在 config.yaml 里，id 无重复
- Hacker News URL 已换为 `?points=100`
- NVIDIA Newsroom 已删除或注释
- ai_interests.txt 末尾有中文 AI 公司关键词
- backup 文件存在

---

## 跨任务红线（任一触发停手）

1. **config.yaml 改坏导致 TrendRadar 启动失败**：改完必须跑 yaml 语法验证，不验证就算未完成
2. **B 的 headless agent 推草稿把 v4 草稿覆盖**：B 的 slug 必须是新主题（非 `anthropic-mythos`），绝不能和 v4 slug 重名
3. **A 任务重跑了封面生成**：耗 API 成本且可能出不同风格，Phase 7 已出图不需要重生成
4. **C 任务接入了 we-mp-rss 公众号条目但 Docker 没在线**：会导致 TrendRadar 抓取报错，公众号部分必须等 Day 2 Docker 确认在线后再加
5. **B 的 agent 用了纯概念主题（无时效新闻）**：Step 2 调研空转，测不到真实负载，算无效试跑
6. **任何任务没有 backup 就做破坏性改动**：config.yaml / 草稿封面 / 草稿文本，改前必须有备份

---

## TrendRadar 路径确认

- **Glob 结果**：`D:\Dev\*` 枚举确认 TrendRadar 目录存在于 `D:\Dev\TrendRadar\`
- **config.yaml 路径**：`D:\Dev\TrendRadar\config\config.yaml`（已验证目录内有 `ai_analysis_prompt.txt` / `ai_interests.txt` / `config.yaml`）
- **注意**：Phase 8 报告里 ai_interests.txt 路径写的是 `D:\Dev\TrendRadar\config\ai_interests.txt`——确认正确，与实际目录结构一致
- **Phase 8 的「11 个 RSS」澄清**：Phase 8 Phase 4.1 共识的 Day 1 批实际是 **11 个新信源**（8 国际 newsletter + 3 国内网页 RSS）+ 2 个改动（HN URL + 删 NVIDIA Newsroom）。不是「11 个全上」，而是 Day 1 批 + Day 2 批分开。C 任务 agent 只做 Day 1 批，we-mp-rss 公众号层（7 个条目）留 Day 2 人工操作。

---

*报告路径：`D:\Dev\ai-wechat-pipeline\reports\phase9_mj_supervisor_handbook.md`*
*生成时间：2026-05-22*
*Musk × Jobs 监督，sonnet orchestrator 执行*
