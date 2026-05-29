# AI 公众号系统未完成 / 待修复 / 待优化清单

*Last update: 2026-05-21 第一篇文章后用户全面反馈*
*用户决策:先全部修复完再测试,不急着写下一篇*

---

## 🔴 P0 用户明确反馈的问题(本次第一篇暴露)

### 1. 卡兹克 Logo / 标识没改 ❌
**问题**:
- 文章末尾硬编码了「数字生命卡兹克 / 投稿:wzglyay@virxact.com」
- 这是卡兹克的 IP,我们不能直接用
- 用户自己的:公众号名 / 笔名 / Logo / 邮箱 / Slogan 都没设置

**需要用户提供**:
- 用户公众号 NAME(已知:wx3b564039c7a4560e,但中文名?)
- 笔名 / 作者名
- 个人简介(尾部用)
- 投稿邮箱 / 联系方式
- Logo 图片(尾图)
- Tagline / Slogan

### 2. 手机上段落留白过多 ❌
**问题**:
- 当前 `<p style="margin:12px 0;">` 在手机上叠加微信默认间距 = 过大空白
- 段间距矛盾:SOP 要求段落写长(数据规律),但每段中间又留白多
- 视觉上像是「上下虚浮」,不像紧凑文章

**待 Phase 3-2 调研后修复**:
- 微信公众号在手机上的 `<p>` 默认 margin 多大?
- 怎么写 inline style 让手机端段间距正常?
- 是否应该把多个短段合并成长段(降低 visible 段间距)?

### 3. 排版根本没做好(电脑 vs 手机不一致)❌
**问题**:
- 我们用简单 markdown → inline HTML,没用 md2wechat 的 43 个 layout 模块
- 没用主题(minimal-blue / focus-green / apple 等)
- 公众号头部 hero / 副标 / 引导卡片都没有

**待 Phase 3-2 调研后**:
- 决定用哪个主题作 baseline
- 写 layout 模板(hero + verdict + cards + cta)
- 重写 post_to_wechat.py 接 md2wechat 标准流程

### 4. AI 味没去 ❌
**问题**:
- 没调用 humanizer-zh skill
- 文章里可能有大量 AI 套话
- 检测的 24 条标准没跑

**待补**:
- writer skill 内置 humanizer-zh 调用
- critic loop 必须经过 humanizer-zh
- 添加"AI 味检测"评分维度

### 5. 生硬模仿卡兹克 ❌
**问题**:
- 堆砌"鬼使神差/不是哥们/老阴逼"等卡兹克口头禅
- 变成"模仿秀"而不是"用户本人"
- memory feedback_content_priority:"卡兹克是参考不是必须模仿"

**待补**:
- 用户写作风格画像(更技术 / 更感性 / 更文学 / 自定义)
- writer skill 不默认套 khazix-writer,只在用户要求时套
- critic 加「过度模仿」扣分维度(可选)

---

## 🟡 P1 工程系统未完成

### 6. Writer ↔ Critic 自动循环没真正实现
**现状**:
- writer skill 装好了
- critic skill 装好了
- 但我**手动**跑 Python 脚本 score_draft.py + 手动 LLM-judge
- writer 没真正接收 critic 反馈自动改稿

**需要**:
- writer skill 内置 critic 调用 + 反馈接收 + 自动改写循环
- 最多 3 轮,达 75 分自动出稿

### 7. 微信草稿推送没标准化
**现状**:
- 我手写了 post_to_wechat.py(直调微信 API)
- 没用 md2wechat / baoyu-post-to-wechat 等标准 skill
- HTML 排版是我手写的简单版本,不专业

**需要**:
- 用 md2wechat 的标准流程(after Phase 3-2)
- 标题缩短(>32 字时自动智能压缩)
- 自动选合适主题
- 自动验证草稿成功推送

### 8. 配图位置选择 + 数量手动
**现状**:
- 我手动选了 5 个位置
- 配图数量按 SOP 应该 10+ 张(2-6 张/千字)
- 风格统一靠 prompt 约束,不可控

**需要**:
- baoyu-article-illustrator skill 自动识别位置
- 配图密度自动按 SOP 计算
- 用户 brand-specific 风格 reference(reference image)

### 9. 主题选择自动化没做
**现状**:
- 我让用户给主题或自己 brainstorm
- topic_hotness_30d 数据已有,但没用作"主题推荐"

**需要**:
- 自动接 aihot.virxact.com API 拉今天热点
- 跟 topic_hotness 交叉,推荐 Top 3 选题
- 用户钦定后开始写

### 10. 字数动态控制
**现状**:
- 我写了 7077 字,超出手机舒适区
- SOP 说 3500-5500 但没强制 enforce

**需要**:
- writer skill 实时计字数
- 接近 5500 时主动收尾
- critic 检测超长自动建议删

---

## 🔵 P2 调研空白 / 未来工作

### 11. 用户本人写作风格画像
**调研空白**:
- 我不知道用户的写作风格倾向
- 卡兹克 / 宝玉 / 赛博 / 花叔 哪个最近?
- 还是有用户自己的独特风格?

**建议**:做一次用户访谈或让用户提供 2-3 篇自己写过的代表作,作 style anchor

### 12. V_score(涨粉变现真公式)
**调研空白**:
- 当前 composite_pct 权重无官方出处
- 调研找到 4 个备选(清博 / 西瓜 / 北极星 / 合成)
- 没选用 — 还在用「类清博」的 composite_pct

**等数据**:用户自己发布几篇后回收真粉丝数据 → 校准

### 13. LLM-judge 80/20 权重校准
**待积累**:
- 当前 final = 0.80 SOP + 0.20 LLM 是先验
- 50+ 篇真实发布后用 OLS 拟合

### 14. 数据飞轮自动化
**未做**:
- 每周抓 4 对标号新文章
- 真实 metrics 回收(自己发的)
- SOP 定期 retrain
- 真粉丝数追踪

---

## 🛠️ P3 SOP / Critic 系统增强

### 15. critic 没有"段落数 / 段间距 / 单段最长字数"硬规则
- 等 Phase 3-2 调研结果后加

### 16. critic 不会建议「删」
- 当前 suggestions 只会"加 X +Y 分"
- 应该也能"删冗余段 +Y 分"
- 字数过长时主动建议精简

### 17. critic 标题智能压缩
- 当前我手动改了标题(>32 → 27 字)
- 应自动检测 + 给出 ≤32 字候选

### 18. style_match 完整实现
- 当前 sop_v2_1.py 里 style_match_score 我传了 0.0(默认中性)
- 应该实时计算 vs 用户 anchor 的相似度
- 用户没自己的 anchor,要先建立(P2-11 的输出)

---

## 📋 修复优先级建议

```
立即做(P0):
  1. ✅ 写本 TODO_GAPS.md(已做)
  2. ⏳ 等 Phase 3-1 / 3-2 Agent 调研完成
  3. 用户提供:公众号名 / 笔名 / 邮箱 / Slogan / Logo
  4. 重写 post_to_wechat.py(用 md2wechat 标准 + 主题)
  5. 用 humanizer-zh 跑当前文章试效果

调研出结果后(P1):
  6. 根据 Phase 3-1 调研改字号 / 行高 / 段距规则
  7. 根据 Phase 3-2 调研改 HTML / CSS 模板
  8. writer ↔ critic 自动循环
  9. 配图自动化(baoyu-article-illustrator)

数据积累后(P2):
  10. 真粉丝数据回收
  11. V_score 校准
  12. LLM-judge 80/20 校准
  13. 数据飞轮自动化

下个 milestone:
  ✅ 一切修好 → 写第 2 篇文章测试 → 真实发布 → 数据回收
```

---

## 必须用户输入的项目

为了往下推进,你必须告诉我:

```
1. 公众号中文名:_______
2. 笔名 / 作者名:_______
3. 公众号 Slogan:_______
4. 投稿 / 联系邮箱:_______
5. 写作风格倾向:
   □ 像卡兹克(亲自下场 + 情绪化)
   □ 像宝玉(翻译 + 短小精悍)
   □ 像赛博禅心(学术 + 深度)
   □ 像花叔(技术深度)
   □ 我有自己风格,我提供 1-2 篇样稿
   □ 还没定,先用通用风格写第一篇,迭代调

6. 已写过的代表作(可选):_______
   (作 style_match anchor 的初始数据)

7. 公众号 Logo 图片(可选):
   尾部插入用,贴文件路径或上传
```
