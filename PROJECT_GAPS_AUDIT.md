# AI 公众号自动化系统 全面盘点审计

*生成时间:2026-05-21*
*Auditor: Sonnet Agent*
*覆盖范围:Phase 1 + 1.5 + 第一篇文章测试后的状态*

---

## 0. 系统当前状态摘要

系统已完成数据驱动 critic 研究(2730 篇语料 + 80k 评论 + 11 个深挖分析 + SOP v2.1 评分工具),并跑通了第一篇文章的全链路(选题→写稿→出图→草稿推送)。核心痛点集中在三处:一是用户 IP 层缺位(硬编码卡兹克标识、无自己风格画像),二是内容质量控制不闭环(writer↔critic 手动、无自动循环、humanizer-zh 未接入),三是排版与视觉层只有最简陋实现(手写 HTML 渲染器、没有 md2wechat 主题、配图几乎靠手动)。数据飞轮(真实发布→数据回流→critic 再训)完全未搭;发布后无任何监控;Claude Agent SDK harness 框架设计好但未实施。距离一个"可持续自动化 AI 公众号 IP"系统,核心缺失环节约占整体 60%。

---

## 1. 待开发的板块(共 42 项)

### 1.1 数据层

- [ ] **对标号数据持续更新管道** | 状态:部分(一次性抓了 277 篇,无更新机制) | 工程量:1 天 | 依赖:wechat-article-exporter / Cloudflare Worker | 描述:每周自动抓 4 个对标号新文章追加入库,保持 critic 训练数据新鲜度;PLAN.md Phase 4 规划但未实施
- [ ] **自己发布文章的 metrics 回收** | 状态:完全未做 | 工程量:0.5 天(脚本) + 持续积累 | 依赖:微信公众号草稿 API + 飞书 Base | 描述:每篇发布后 1h/6h/24h 多次抓 readNum/shareNum/likeNum/commentNum 回流;数据飞轮的核心前提,无此则 critic 无法校准
- [ ] **真粉丝数追踪** | 状态:完全未做 | 工程量:0.5 天 | 依赖:微信公众平台后台 API | 描述:每次发文后记录粉丝增量,用于 V_score(涨粉变现)后续校准;当前 composite_pct 权重无涨粉维度
- [ ] **时序快照框架(1h/6h/24h)** | 状态:完全未做 | 工程量:1 天 | 依赖:定时任务(cron/飞书) | 描述:PLAN.md P2 决策已定;SMTPD 论文支持多时序快照提升预测准确性;需要调度框架
- [ ] **critic v2 近 12 个月窗口训练** | 状态:部分(critic v1 全数据训,跨期 R²=-1.4;v2 计划中) | 工程量:1 天 | 依赖:features.parquet + targets.parquet | 描述:严谨性验证 v2 证明必须只用近 12 个月数据训;v2 目标 R²>0.4;进行中但未完成
- [ ] **style_match anchor 自动更新** | 状态:部分(anchor 是静态 top10-bot10,不更新) | 工程量:0.5 天 | 依赖:对标号数据持续更新 | 描述:随着对标号发新文,anchor 应每月刷新;style_match_score 是当前最强单信号(ρ=+0.358)

### 1.2 Critic 层

- [ ] **writer↔critic 自动循环 harness** | 状态:完全未做 | 工程量:2-3 天 | 依赖:Claude Agent SDK Python + sop_v2_1.py + critic SKILL.md | 描述:当前手动跑 score_draft.py + 手动 LLM-judge;需要 writer 出稿→critic 打分→反馈→writer 改稿→再评→直到 ≥75 分的自动闭环;最多 3 轮
- [ ] **critic "建议删" 能力** | 状态:完全未做 | 工程量:0.5 天 | 依赖:sop_v2_1.py suggestions 字段 | 描述:当前 suggestions 只会"加 X +Y 分";字数过长时应主动"删冗余段 +Y 分";改动 suggestions 生成逻辑
- [ ] **标题智能压缩** | 状态:完全未做(当前手动) | 工程量:0.5 天 | 依赖:sop_v2_1.py + LLM 调用 | 描述:检测标题 >32 字符时自动生成 ≤32 字候选列表(微信 API 草稿标题限制);当前手动改
- [ ] **字数实时控制** | 状态:完全未做 | 工程量:0.5 天 | 依赖:writer skill / harness | 描述:writer skill 接近 5500 字时主动收尾;当前第一篇写了 7077 字超出甜蜜区
- [ ] **"AI 味"检测维度** | 状态:完全未做 | 工程量:0.5 天 | 依赖:humanizer-zh 的 24 条标准 | 描述:critic 增加 AI_taste_score 子维度;当前 LLM-judge 4 维不含此项;检测 24 条 AI 写作模式
- [ ] **过度模仿卡兹克扣分** | 状态:完全未做 | 工程量:0.5 天 | 依赖:用户确认是否要加 | 描述:检测"鬼使神差/不是哥们/老阴逼"等卡兹克专属词出现频率;超出阈值扣分;可选
- [ ] **deepeval G-Eval 自评框架** | 状态:完全未做 | 工程量:2 天 | 依赖:deepeval 15.5k star | 描述:PLAN.md Phase 3 规划;把 L1-L4 翻译成 metric(hook/金句/AI 味/节奏 4 维);当前 LLM-judge 是手工 prompt 而非 deepeval metric 封装
- [ ] **双 critic 防标题党** | 状态:完全未做(Phase 4 后期) | 工程量:1 周 | 依赖:3 个月以上时序数据 | 描述:Critic1 短期 CTR + Critic2 下一篇阅读代理留存;Nature 论文证明负面词涨 CTR 但微信严打;需要时间序列数据

### 1.3 Writer 层

- [ ] **humanizer-zh 自动接入** | 状态:完全未做 | 工程量:0.5 天 | 依赖:humanizer-zh skill | 描述:writer skill 出稿后自动调 humanizer-zh 跑 24 条 AI 痕迹检测+修复;当前第一篇 AI 味未去
- [ ] **用户写作风格画像 (style anchor)** | 状态:完全未做 | 工程量:1-2 天(含用户访谈) | 依赖:用户提供 2-3 篇自己写过的代表作 | 描述:sop_v2_1.py 里 style_match_score 当前传 0.0(默认中性);需要用户 anchor 才能激活最强信号(ρ=+0.358);待用户提供样稿
- [ ] **khazix-writer 与本 IP 解耦** | 状态:部分(当前默认套 khazix-writer 导致模仿过头) | 工程量:1 天 | 依赖:用户风格画像 | 描述:writer skill 不默认套 khazix-writer;用户有自己 voice 时用自己 anchor;khazix 只作参考而非主风格
- [ ] **BERTopic 选题聚类接入** | 状态:完全未做 | 工程量:2 天 | 依赖:BERTopic 7k star + TrendRadar 输出 | 描述:PLAN.md Phase 3 规划;每天对 TrendRadar 输出做聚类产 5-8 个选题集群;当前选题全靠 aihot API + 人工判断
- [ ] **wewrite extract_exemplar persona YAML** | 状态:完全未做 | 工程量:1 天 | 依赖:用户自己的修改稿 | 描述:PLAN.md Phase 4;从用户自己修改过的稿子中提取写作风格 persona YAML;是构建差异化 IP 的核心
- [ ] **BGE-M3 + Chroma 语料向量库** | 状态:完全未做 | 工程量:2-3 天 | 依赖:FlagEmbedding + 100+ 篇语料 | 描述:PLAN.md Phase 4;按"主题+标题"召回 top-5 卡兹克原文做 few-shot;当前 pick_few_shot.py 是关键词 BM25 召回,精度有限

### 1.4 排版层

- [ ] **md2wechat 主题接入(真实 HTML)** | 状态:部分(有 md2wechat.exe 但用自写的简化 md_to_ocean_html.py) | 工程量:1-2 天 | 依赖:md2wechat API key 或 prompt 模式 | 描述:当前 md_to_ocean_html.py 只硬编码颜色,没有 43 个 layout 模块(hero/verdict/cards/callout/quote);两个方案:省钱=把 prompt.txt 喂给 Claude API;省事=买 md2wechat API key(联系 wzglyay@virxact.com)
- [ ] **手机端段间距修复** | 状态:完全未做(待调研) | 工程量:0.5 天 | 依赖:Phase 3-2 调研结果 | 描述:当前 `<p style="margin:12px 0;">` 在手机上叠加微信默认间距=过大空白;需调研微信手机端 `<p>` 默认 margin 并用 inline style 覆盖
- [ ] **公众号 hero / 引导卡片 / 尾部签名模板** | 状态:完全未做 | 工程量:1 天 | 依赖:用户 IP 信息(笔名/Slogan/Logo) | 描述:头部 hero + 副标引导卡片 + 标准尾部签名(当前硬编码了卡兹克签名)
- [ ] **段落长度 linter** | 状态:完全未做 | 工程量:0.5 天 | 依赖:无 | 描述:PLAN.md §7 点明"段落 ≤150 字 linter 不存在,需要自己写 ~20 行 Python";在 markdown 渲染前检测并警告
- [ ] **自动主题选择** | 状态:完全未做 | 工程量:0.5 天 | 依赖:md2wechat 主题接入完成 | 描述:按文章情绪/主题自动选 minimal-blue/focus-green/apple 等主题;当前手动

### 1.5 发布层

- [ ] **post_to_wechat.py 标准化** | 状态:部分(能跑但未用 md2wechat 标准流程) | 工程量:1 天 | 依赖:md2wechat 主题接入 | 描述:当前手写简单 HTML 直接调微信 API;需改为 md2wechat 标准输出→baoyu-post-to-wechat 推送;同时加草稿成功验证逻辑
- [ ] **Secret 脱离硬编码** | 状态:完全未做(APPID+SECRET 硬编码在 post_to_wechat.py 中) | 工程量:0.5 天 | 依赖:无 | 描述:post_to_wechat.py 里 SECRET=`<REDACTED>` 明文;应移入 .env 并用 python-dotenv 读取;.env 已在 .gitignore 但代码层没隔离
- [ ] **朱雀 AI 检测自动化** | 状态:完全未做 | 工程量:1-2 天 | 依赖:headless 浏览器 | 描述:PLAN.md §7 指出微信 AI 检测无开源 API;需 Playwright headless 自动化朱雀网页版;目标 AI 率 <25%;当前完全靠人工
- [ ] **houbb 敏感词扫描** | 状态:完全未做(工具装了但未接入 pipeline) | 工程量:0.5 天 | 依赖:houbb/sensitive-word 5.8k star | 描述:PLAN.md Phase 3 规划;Stop hook 触发敏感词扫描;当前 pipeline 无此步骤
- [ ] **发布调度(最优时段)** | 状态:完全未做 | 工程量:0.5 天 | 依赖:publish_time_analysis.md 数据 | 描述:已有 publish_time_analysis.md;数据显示时段影响基本可忽略但有方向性;需接入 pipeline 的定时推送

### 1.6 数据飞轮层

- [ ] **飞书 Base 数据回流** | 状态:完全未做 | 工程量:2 天 | 依赖:飞书 API + lark-base skill | 描述:PLAN.md 核心架构;每篇发布文章的 metrics 写入飞书 Base;字段:选题集群/标题模板/首图风格/阅读量/转发率;用户已有飞书栈
- [ ] **每周 critic 数据分析报告** | 状态:完全未做 | 工程量:1 天 | 依赖:飞书 Base 数据积累 | 描述:PLAN.md Phase 4;每周 Claude 跑分析:哪种选题集群×标题模板组合阅读量最高;数据飞轮的分析环节
- [ ] **LLM-judge 80/20 权重校准** | 状态:完全未做(等数据) | 工程量:0.5 天 + 50 篇真实数据 | 依赖:50+ 篇真实发布数据 | 描述:当前 final=0.80 SOP+0.20 LLM 是先验设定;积累 50 篇后用 OLS 拟合最优权重
- [ ] **SOP 定期 retrain(每 3 个月)** | 状态:完全未做(流程未建立) | 工程量:0.5 天设计 + 周期执行 | 依赖:对标号数据持续更新 | 描述:严谨性验证 v2 证明 2023-24 旧数据训出的模型 2026 跨期 R²=-1.4;必须 12 个月滚动窗口;需要自动化触发器

### 1.7 选题 / 主题层

- [ ] **aihot API → topic_hotness 交叉推荐** | 状态:部分(aihot API 能调,run_pipeline.py 已接;但与 topic_hotness.parquet 无交叉) | 工程量:1 天 | 依赖:topic_hotness.parquet + aihot API | 描述:每天拉 aihot 热点→与 topic_hotness_30d 交叉→推荐 Top 3 爆款潜力选题;当前选题是人工+启发式
- [ ] **Twitter/X 信源接入(twscrape)** | 状态:完全未做 | 工程量:2 天 | 依赖:vladkens/twscrape 2.4k | 描述:PLAN.md 规划的 @_akhaliq 等 Twitter 信源;PLAN.md 已标注 dyyz1993/twitter-monitor 弃用;需要 Twitter 账号轮换
- [ ] **the-batch / r/LocalLLaMA RSS 修复** | 状态:部分(TrendRadar 里已注释) | 工程量:1 天 | 依赖:RSSHub 或 Kill the Newsletter | 描述:PLAN.md Phase 1 验证 2 个 URL 有问题;the-batch 无公共 RSS;r/LocalLLaMA Reddit 屏蔽 UA

### 1.8 监控层

- [ ] **pipeline 运行日志 + 告警** | 状态:完全未做 | 工程量:1 天 | 依赖:飞书 IM 或邮件 | 描述:每次 run_pipeline.py 运行结果推送到飞书;封面生成失败/草稿推送失败/评分未过线等异常告警
- [ ] **对标号爆款监控** | 状态:完全未做 | 工程量:1 天 | 依赖:wechat-article-exporter | 描述:每天检测 4 个对标号新文章;标记阅读量 top10% 爆款;自动入 corpus 并触发 few-shot 索引更新
- [ ] **自己文章发布后表现监控** | 状态:完全未做 | 工程量:0.5 天 | 依赖:微信公众号 API | 描述:发布 6h/24h 后自动拉 metrics;与历史均值对比;异常(超低/超高)主动推送通知

### 1.9 用户 IP / Brand 层

- [ ] **用户 IP 基本信息配置** | 状态:完全未做(阻塞级) | 工程量:0.5 天(用户提供信息后) | 依赖:用户必须提供 | 描述:公众号中文名/笔名/Slogan/联系邮箱/Logo 图片;当前文章末尾硬编码卡兹克的"数字生命卡兹克/wzglyay@virxact.com"
- [ ] **IP 视觉风格确定(LoRA 可选)** | 状态:完全未做 | 工程量:1 周(可选) | 依赖:fal.ai / ComfyUI | 描述:PLAN.md Phase 4 可选;Nano Banana 2/Flux.2 出参考图+LoRA 训练做 IP 视觉护城河;先确定配色系统和视觉基调即可
- [ ] **对外开源/IP 曝光动作** | 状态:完全未做 | 工程量:1-2 周 | 依赖:足够数据后 | 描述:PLAN.md §8 提到 4 个开源/PR 动作(md2wechat PR / 30+ 大 V 监控源 / 卡兹克风格池 / 标题阅读量打分器小模型);护城河建设

### 1.10 其他

- [ ] **Claude Agent SDK Python harness 主框架** | 状态:完全未做(决策定了但未实施) | 工程量:3-5 天 | 依赖:所有子模块到位后 | 描述:PLAN.md + harness 决策 memory 已定;plan→researcher→writer→editor→qa→publisher 5 角色串联;当前 run_pipeline.py 只是脚本不是真 harness
- [ ] **Hooks 配置(PostToolUse/Stop)** | 状态:完全未做 | 工程量:0.5 天 | 依赖:Claude Code settings.json | 描述:PostToolUse(Write)→humanizer;Stop→敏感词扫描;SessionStart→注入今日热点 top10;PLAN.md Phase 3 规划
- [ ] **TrendRadar/we-mp-rss 包成 MCP server** | 状态:完全未做 | 工程量:2-3 天 | 依赖:TrendRadar + we-mp-rss 现有代码 | 描述:PLAN.md Phase 3 核心解耦点;当前直接调 API 不通过 MCP

---

## 2. 待解决的问题(共 18 项)

### 2.1 致命阻塞(发不出 / 体验差到不能用)

- [ ] **卡兹克 IP 标识未替换** | 严重程度:致命 | 原因:post_to_wechat.py 和文章模板硬编码卡兹克签名/邮箱 | 影响:发出去的文章末尾是卡兹克的 IP,侵权风险 + 用户 IP 建设为零 | 修复 ETA:用户提供信息后 0.5 天
- [ ] **API Secret 明文硬编码** | 严重程度:致命(安全) | 原因:tools/post_to_wechat.py 第 18 行 `SECRET="65d0fd5..."` 明文 | 影响:如果代码被分享/上传 GitHub,公众号账号被盗 | 修复 ETA:0.5 天(移到 .env)
- [ ] **humanizer-zh 未接入** | 严重程度:致命(质量) | 原因:writer skill 出稿后没有调 humanizer-zh;run_pipeline.py Step 4 只有简单关键词扫描 | 影响:文章 AI 味浓,微信 AI 检测可能拦截,读者体验差 | 修复 ETA:0.5 天
- [ ] **style_match_score 传 0.0** | 严重程度:致命(评分失效) | 原因:sop_v2_1.py 里 style_match 是系统最强信号但需 anchor,用户无 anchor 传 0 | 影响:SOP v2.1 比 v2 强的主要原因失效,等于退回 v2 | 修复 ETA:用户提供风格样稿后 1 天

### 2.2 体验差

- [ ] **手机端段落留白过多** | 严重程度:体验差 | 原因:`<p style="margin:12px 0;">` 叠加微信手机端默认 margin | 影响:手机阅读体验差,像"上下虚浮";公众号主要在手机端读 | 修复 ETA:调研结果后 0.5 天
- [ ] **排版没用 md2wechat 真实主题** | 严重程度:体验差 | 原因:tools/md_to_ocean_html.py 只是简化渲染器;无 hero/verdict/cards 等高级排版 | 影响:视觉呈现与头部大 V 差距悬殊;没有品牌感 | 修复 ETA:1-2 天
- [ ] **文章完全无封面 / 内文图接入** | 严重程度:体验差 | 原因:baoyu-article-illustrator 装了但未接入 pipeline;配图靠手动 | 影响:根据数据分析多图 > 少图;视觉爆款体质接近零 | 修复 ETA:1 天(接入 baoyu-article-illustrator)
- [ ] **过度模仿卡兹克口头禅** | 严重程度:体验差 | 原因:writer 默认套 khazix-writer,无约束条件 | 影响:文章成"模仿秀";用户没有自己的 IP | 修复 ETA:0.5 天(writer skill 加约束 + 用户确认风格方向)
- [ ] **字数过长(7077 字)** | 严重程度:体验差 | 原因:writer 无字数边界控制;SOP 未 enforce | 影响:手机阅读体验差;数据显示 5500+ 字有 ceiling 效应 | 修复 ETA:0.5 天

### 2.3 体验中等差

- [ ] **writer↔critic 手动流程** | 严重程度:体验中等差 | 原因:无 harness 循环;score_draft.py 手动跑 + 手动 LLM-judge | 影响:每篇文章需要大量人工介入,无法规模化;质量一致性低 | 修复 ETA:2-3 天
- [ ] **few-shot 召回精度低** | 严重程度:体验中等差 | 原因:pick_few_shot.py 基于关键词 BM25,不是语义检索 | 影响:召回文章主题相关但风格可能不匹配;影响 few-shot 质量 | 修复 ETA:3 天(BGE-M3 向量库)
- [ ] **选题推荐没数据驱动** | 严重程度:体验中等差 | 原因:run_pipeline.py pick_topic_from_hot() 用启发式分类评分,没对接 topic_hotness.parquet | 影响:选题可能与真实爆款规律脱节 | 修复 ETA:1 天
- [ ] **the-batch / r/LocalLLaMA 信源失效** | 严重程度:体验中等差 | 原因:PLAN.md Phase 1 验证已知;the-batch 无公共 RSS;Reddit 屏蔽 UA | 影响:少 2 个重要信源;护城河信源覆盖不全 | 修复 ETA:1 天

### 2.4 锦上添花

- [ ] **SOP 分箱准确率仅 58.3%** | 严重程度:锦上添花 | 原因:SOP v2.1 ρ=0.393 R²=-0.045;单篇预测 ±15 分误差 | 影响:评分不够精准;50+ 篇数据后可通过 OLS 校准 | 修复 ETA:积累数据后 0.5 天
- [ ] **封面生成依赖 火山方舟 API** | 严重程度:锦上添花 | 原因:无本地备选方案 | 影响:API 不稳定时封面生成失败;无优雅降级 | 修复 ETA:0.5 天(加 fallback 到纯文字封面)
- [ ] **图片上传无批量进度追踪** | 严重程度:锦上添花 | 原因:post_to_wechat.py 上传图片无进度日志 | 影响:多图上传超时无法定位 | 修复 ETA:0.5 天
- [ ] **词汇多样性计算不精确** | 严重程度:锦上添花 | 原因:score_draft.py 用 jieba 分词但未过滤停用词 | 影响:jb_lexical_diversity 计算值偏高 | 修复 ETA:0.5 天
- [ ] **中文可读性仅靠 jieba 词长** | 严重程度:锦上添花 | 原因:未接入 cntext fog_index 或 AlphaReadabilityChinese Lei 三层 | 影响:可读性信号弱;critic_plan.md 已选定工具但未实施 | 修复 ETA:1 天

---

## 3. 待优化的地方(共 15 项)

### 3.1 流程优化

- [ ] **run_pipeline.py Step 3 仍是"人在环路"提示** | 原因:写稿环节打印提示让用户手动说"用 khazix-writer skill" | 影响:自动化程度低;用户体验不连贯 | 建议:改为直接调用 writer skill 并传参;人在环路只保留"最终把关"一步
- [ ] **每篇文章需要手动提供 topic + slug** | 原因:run_pipeline.py 命令行参数仍需人填 | 影响:选题→发布全流程非全自动 | 建议:aihot API 自动选题后直接进 pipeline;人工只做最终确认
- [ ] **每次写稿 few-shot 固定 per_account=5** | 原因:pick_few_shot.py 默认参数;没有按文章类型/长度动态调 | 影响:叙事文可能召回分析文;风格不匹配 | 建议:按选题类型(产品发布/事件分析/教程)分类召回
- [ ] **post_to_wechat.py 图片路径硬编码** | 原因:DRAFT_PATH 和 COVER_PATH 写死在脚本里 | 影响:每次需要手动改代码 | 建议:改为 CLI 参数或从 run_pipeline.py 输出的 manifest.json 读取

### 3.2 工程化优化

- [ ] **评分权重硬编码** | 原因:sop_v2_1.py 里 `DIM_WEIGHTS = {"read":0.40, "share":0.20...}` 硬编码 | 影响:无法在不改代码的情况下快速调整权重实验 | 建议:权重移入 config.yaml 或 .env;支持 CLI 覆盖
- [ ] **Python 脚本无统一 CLI 接口** | 原因:tools/ 下 60+ 个 .py 各自为政,没有统一入口 | 影响:用户或 agent 调用时需要记住每个脚本的参数 | 建议:Makefile 或 typer CLI 统一入口
- [ ] **corpus 全文没版本管理** | 原因:corpus/ 下 .md 文件直接堆放;无 Git LFS 或元数据追踪 | 影响:无法追踪语料变化;对标号新文章加入后无法 diff | 建议:corpus_index.json 加入 last_updated + md5 字段
- [ ] **db.sqlite 437MB 无备份策略** | 原因:唯一数据库,无异地备份 | 影响:硬盘损坏则所有训练数据丢失;整个 Phase 1 成果归零 | 建议:定期(每周)备份到 OneDrive 或 D 盘分区
- [ ] **secrets 管理混乱** | 原因:DeepSeek key 在 TrendRadar config.yaml;微信 Secret 在 post_to_wechat.py;火山方舟 key 位置未统一 | 影响:多处分散难以轮换;任何一个文件泄露都有损失 | 建议:统一到 D:\Dev\ai-wechat-pipeline\.env,python-dotenv 读取

### 3.3 性能 / 成本优化

- [ ] **每篇文章 Claude API Token 成本未追踪** | 原因:没有 token 计量;不知道每篇文章 API 花了多少钱 | 影响:月度成本无法预测;可能超出预算 | 建议:在 run_pipeline.py 接入 Anthropic SDK usage 字段,每次写入 manifest.json
- [ ] **火山方舟配图按张计费无成本上限** | 原因:baoyu-article-illustrator 自动识别位置;可能插入 10+ 张图 | 影响:单篇配图成本可能超出预期 | 建议:配图数量上限参数(默认 max_images=6);超出时优先删低优先级位置
- [ ] **aihot API 请求无缓存** | 原因:每次运行 run_pipeline.py 都重新拉 | 影响:对于同一天多次运行浪费请求 | 建议:24h 内结果缓存到本地 JSON
- [ ] **未利用 Prompt Caching** | 原因:writer/critic skill 调用 Claude API 时没有 cache_control | 影响:few-shot 全文(每篇 3000-5000 字)每次都重新计费;多轮 critic 循环成本倍增 | 建议:接入 claude-api skill 的 prompt caching 最佳实践;few-shot 内容加 cache_control:ephemeral

---

## 4. 用户可能需要关注的盲点(共 22 项)

### 4.1 法律 / 合规

- ⚠️ **卡兹克语料版权风险**:corpus/kazik/ 下 673 篇卡兹克文章是直接抓取的,无授权。用于 few-shot 召回属于内部使用;若将 BGE-M3 向量库开源(PLAN.md §8 提到),则存在版权纠纷风险。建议:向量库不开源或先征得卡兹克同意。
- ⚠️ **文章引用 AI 新闻素材的版权**:写作时引用 smol.ai AINews / HF Daily Papers 等信源;转述没问题,大段复制引用可能侵权。建议:引用时注明来源 + 链接。
- ⚠️ **微信公众号内容审核合规**:houbb 敏感词库是通用词库,不一定覆盖微信最新违禁词。建议:发布前人工检查 + 微信官方"内容安全"API 调用(有免费额度)。

### 4.2 风险管理

- ⚠️ **公众号封号风险**:非认证号只能发草稿(已知);但内容频繁使用 AI 生成、话题敏感(AI 安全/监管)可能触发内容审核。建议:避开"AI 威胁论"等敏感词;文章 AI 率控制在 <25%。
- ⚠️ **连续发文间隔不足被降权**:如果使用定时任务每天发文但内容质量不稳定,可能被微信算法判定为机器号降低推荐。建议:宁可减频(每周 2-3 篇)也要保证质量通过 critic ≥75 分门槛。
- ⚠️ **wechat-article-exporter 风控**:PLAN.md §7 已提醒;建议私有化 Docker 部署+专门小号扫码;当前用 Cloudflare Worker 代理但若 worker 配额耗尽则数据抓取中断。
- ⚠️ **Cloudflare Worker 免费配额限制**:mp-proxy-worker.dufengyun12.workers.dev 是免费 Worker;Cloudflare 免费计划有 100k 请求/天限制。语料批量抓取时可能耗尽配额。建议:监控请求量,必要时升级计划(5美元/月)。

### 4.3 商业模式

- ⚠️ **变现路径尚未规划**:系统目标是"做 AI 公众号 IP",但当前没有变现设计(知识付费/广告/私域/咨询)。建议:早期就在文章末尾测试"加微信"/"扫码进群"转化率;数据反哺内容策略。
- ⚠️ **粉丝增长跟踪缺失**:当前 composite_pct 权重(40%读/20%分享...)无涨粉维度;而商业目标是做 IP。建议:在 targets.parquet 中加入 fan_growth_per_article 字段(需每篇前后各抓粉丝数)。
- ⚠️ **没有 A/B 测试框架**:标题 A/B、风格 A/B 等都是 PLAN.md 里提到的护城河功能,但完全未实施。建议:积累 10 篇后开始同主题不同标题的对照测试。

### 4.4 安全 / 凭证管理

- ⚠️ **微信 AppID + Secret 明文在代码文件**:tools/post_to_wechat.py 第 16-17 行明文硬编码。若文件被分享/误 commit 到 GitHub 则账号风险极大。立即修复:移入 .env。
- ⚠️ **多处 API Key 分散存放**:DeepSeek key 在 TrendRadar config.yaml;火山方舟 key 位置不明;Claude API key 在系统环境变量。建议统一到 D:\Dev\ai-wechat-pipeline\.env 并制作 key 轮换 SOP。
- ⚠️ **db.sqlite 437MB 无异地备份**:所有 Phase 1 训练数据单点存储在 D 盘。建议:每周同步到 OneDrive(自动备份)或外部云存储。

### 4.5 性能 / 成本

- ⚠️ **当前预估每篇文章成本(分项)**:
  - Claude API(writer 4000 字 + critic 2-3 轮 + humanizer):约 $0.15-0.30(Sonnet 4.6 输入 $3/M token 估算)
  - 火山方舟 Seedream 配图(6 张估算):约 $0.10-0.20(取决于 Seedream 定价)
  - 封面生成(1 张):约 $0.02-0.05
  - 其他(aihot API / TrendRadar):基本免费
  - **单篇总成本估算:$0.30-0.60**
  - **月 30 篇:$9-18/月**
  - ⚠️ 未接入 Prompt Caching:few-shot 全文(5篇×4000字)每轮重新计费;接入后可降低 40-60%
  - ⚠️ critic 多轮循环(最多 3 轮)成本会倍增:建议第 1 轮只跑规则评分,分数过 60 才做 LLM-judge

### 4.6 跨平台 / 长期可持续性

- ⚠️ **当前只发公众号**:用户 memory 有小红书 AI 系统(D:\Dev\xhs-ai-system\)但两个系统完全独立;内容可能可以复用(公众号→小红书缩减版);没有跨平台内容复用设计。
- ⚠️ **微信平台政策变化风险**:2025-07 起非认证号只能发草稿(已知);微信可能进一步收紧 API 权限。建议:提前准备备用发布渠道(B 站专栏/知乎);内容资产不只锁在微信。
- ⚠️ **Claude API 涨价风险**:当前成本基于 Sonnet 4.6 定价;Anthropic 可能调整定价。2026-06-15 Agent SDK 单独计费额度开始;建议监控官方公告。
- ⚠️ **依赖卡兹克开源项目风险**:khazix-writer / aihot / hv-analysis 都依赖 KKKKhazix 的 GitHub 仓库和 API(aihot.virxact.com)。若卡兹克关闭 repo 或 API,核心 skill 失效。建议:fork 并私有化部署 aihot API。

### 4.7 数据隐私 / 爬虫合规

- ⚠️ **大量爬取公众号文章的法律灰色地带**:wechat-article-exporter 使用 Cloudflare Worker 绕过微信 UA 检测;规模化爬取可能违反微信服务协议第 7 条。当前 277 篇体量较小,风险低;若规模到 10000 篇则需要重新评估。
- ⚠️ **评论数据 IP 归属地(广东/北京等)属于个人信息**:db.sqlite 中存有 80,397 条评论含 IP 属地。若系统开源或数据集共享,需要脱敏处理。当前只内部使用风险可控。

---

## 5. 推荐执行顺序(给用户)

按依赖关系 + 影响力排序:

### 阶段 1(必须先做,1-2 天):阻断性修复

1. **用户提供 IP 基本信息**(公众号名/笔名/Slogan/邮箱/Logo)并替换文章模板中的卡兹克标识 — 0.5 天
2. **API Secret 移入 .env**(post_to_wechat.py 第 16-17 行) — 0.5 天
3. **humanizer-zh 接入 pipeline**(run_pipeline.py Step 4 从关键词扫描升级为真实 humanizer-zh 调用) — 0.5 天
4. **手机端段间距修复**(微信默认 margin 调研 + inline style 覆盖) — 0.5 天
5. **字数控制(writer SOP 强制 enforce ≤5500 字)** — 0.5 天

### 阶段 2(排版与视觉,2-3 天):体验提升

6. **md2wechat 真实主题接入**(省钱方案:把 prompt.txt 喂给 Claude API 出精排 HTML) — 1-2 天
7. **baoyu-article-illustrator 接入 pipeline**(自动识别配图位置,至少 6 张/篇) — 1 天
8. **用户风格画像建立**(用户提供 2-3 篇样稿,建 style anchor) — 1 天(含用户访谈)

### 阶段 3(质量闭环,3-5 天):全自动化核心

9. **writer↔critic 自动循环 harness**(Claude Agent SDK;最多 3 轮;≥75 分出稿) — 2-3 天
10. **aihot × topic_hotness 交叉选题推荐** — 1 天
11. **Hooks 配置**(PostToolUse→humanizer;Stop→敏感词扫描) — 0.5 天
12. **houbb 敏感词 + 朱雀 AI 检测** — 1-2 天

### 阶段 4(数据飞轮,1-2 周):护城河建设

13. **发布后 metrics 时序回收**(1h/6h/24h 三次抓;写入飞书 Base) — 1-2 天
14. **critic v2 训练**(近 12 个月窗口;目标 R²>0.4) — 1 天(完成现有进行中任务)
15. **对标号语料持续更新(每周)** — 0.5 天设计 + 定期跑
16. **LLM-judge 80/20 权重校准**(积累 50 篇后) — 0.5 天

### 阶段 5(长期护城河,1 个月+):差异化建设

17. BGE-M3 + Chroma 语义召回库
18. wewrite persona YAML 提取用户风格
19. 双 critic 防标题党(3 个月数据后)
20. IP 视觉 LoRA 训练(可选)
21. 标题阅读量打分器小模型(3 个月后)

---

## 6. 强烈建议用户立即确认的事项

(用户必须决定才能往下走的事)

- **公众号 IP 信息**:公众号中文名、笔名/作者名、Slogan、投稿邮箱、Logo 图片 — 这是 P0 阻断项,所有模板都等这个
- **写作风格方向**:像卡兹克(情绪化亲自下场)/ 像宝玉(翻译+短小精悍)/ 自己风格(需提供 2-3 篇样稿) — style_match_score 当前为 0,最强信号失效
- **md2wechat 排版方案选择**:省钱方案(把 prompt.txt 喂给 Claude API)vs 省事方案(买 API key 联系 wzglyay@virxact.com) — 当前排版是最简陋版本,必须升级
- **发文频率目标**:每天 1 篇 / 每周 3 篇 / 每周 1 篇精品 — 影响 harness 自动化优先级和成本预算
- **db.sqlite 备份策略确认**:437MB 所有 Phase 1 数据单点存在 D 盘,建议每周同步到 OneDrive — 需要用户确认是否手动还是自动备份
- **aihot API 依赖风险**:是否需要 fork + 私有部署 aihot — 影响信源层稳定性评估
- **跨平台内容复用**:公众号内容是否要同步发小红书/知乎/B 站 — 影响内容生产 SOP 设计
