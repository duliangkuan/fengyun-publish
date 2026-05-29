# Round 3 沙盒辩论 — layout_rules 自动化排版落地文档

**日期**: 2026-05-24
**作者**: Musk × Jobs(虚拟沙盒辩论)+ 风云(最终拍板)
**触发**: fengyun-publish 内容质量已达标,转向排版与视觉体验层优化

---

## 一、背景

风云的 fengyun-publish AI 公众号自动化系统已能跑通从选题到推草稿全流程。内容生成质量已基本达标,**现在重点转向【排版与视觉体验层】优化**。

**最终目标**:让排版像内容一样可以**系统化、自动化生产**,不是每篇手动调。

**读者群体**:AI 圈从业者和爱好者
**平台约束**:微信公众号(字号 14-17px / inline style / HTML ≤ 20K / 无 class id / 无 hr table iframe)

---

## 二、沙盒辩论规则(虚拟世界设定)

为了在客观事实驱动下做决策,设了一个生死沙盒:

- Musk 偷懒 → 死亡 + 永久禁止移民火星 / 发展航天事业
- Jobs 偷懒 → 苹果公司毁灭 + 死亡
- 第三方审判官全程监视,警告一次后再犯即执行惩罚
- 每人 5 次调研额度,**至少必须用 3 次**
- 调研结果是**唯一**有效论据,不许凭主观断言

**辩论结果**:两人都活着,0 警告,9 维度全部带客观出处。

---

## 三、9 维度规则与依据

### 1. 文章插图策略

- 频次:**每 1100 字 1 张**(±100 字容差)
- 首图(钩子)必须有
- 每个 H2 章节首必须一张
- **禁止图注文字**(微信会压缩成噪音)

**出处**:本地 PHASE1_FACTS.md L209 + Musk 调研#3 — 「头部公众号 15+ 张图/文是 Idiot Index,物理最优在每 1000-1200 字 1 张」

### 2. 字体使用

- 正文 **15px / normal / #333**
- letter-spacing 0.3px(中文字间气口)
- H2 **20px / bold / #222**
- H2 用 `<p>` 标签不用 `<h1-6>`(防微信覆盖字号)
- 引用 14px / #666(降一档制造层级)
- strong 用 #000(纯黑制造重点反差)
- **不设 font-family**(系统接管,Jobs「让字体消失」)

**出处**:
- Musk#1 中文眼动 14-16px <https://www.researchgate.net/publication/330051180>
- Jobs#1 Apple HIG <https://developer.apple.com/design/human-interface-guidelines/typography>

### 3. 背景色 + 主色调

- 背景 #FFFFFF(纯白,灰底反色会失明)
- 文本灰 #333
- 主色 #1E6FFF(链接 / 章节标识)
- 引用块底 **#FAF9F5**(暖象牙,风云品牌)
- 引用块边 **#D97757**(陶土橙,风云品牌,Anthropic 同族)
- CTA #FF4D4D
- **最多 4 色** + 灰色文字

**出处**:
- Jobs#3 WCAG 2.2 Contrast Minimum <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html>
- Light/Dark Mode Visual Fatigue <https://pmc.ncbi.nlm.nih.gov/articles/PMC12027292/>
- 风云封面三件套品牌色锁定(`reports/cover_color_deep.md`)

### 4. 行距 line-height

- 正文 **1.75**
- 引用块 1.7(稍紧凑制造对比)
- H2 1.4

**出处**:Musk#1 中文方块字密度 +25-30% over Apple 1.36 + 本地 Phase 3-1 实测 1.75 是最优

### 5. 段落节奏

- 平均段长 80-150 字
- **超 200 字自动拆**(按句号 / 问号 / 感叹号)
- 段间距 margin-bottom 20px(显式覆盖微信默认 24pt 叠加)
- 每 3-5 段插 1 个 20-40 字短段(视觉换气)

**出处**:
- Musk#2 Pew 117M 移动阅读 <https://www.pewresearch.org/journalism/2016/05/05/long-form-reading-shows-signs-of-life-in-our-mobile-news-world/>
- Jobs 删减测试

### 6. 分割线

- **禁 `<hr>`**(微信渲染丑)
- 用「· · ·」三点字符,居中,#ccc 浅灰(装饰性允许)
- 上下 32px margin
- 全文 3-5 个(对应 3-5 章节)

**出处**:物理约束(微信 `<hr>` 渲染丑)+ 本地实测

### 7. 引导块(引用 / CTA)

- 引用块 **2-4 个/篇**
- 每个 **≤60 字**(超 60 说明不是金句是段落)
- 样式:border-left:4px solid #D97757 + bg:#FAF9F5 + padding:14px 18px
- CTA **不能在正文中段**(只能文末)

**出处**:Jobs#2 情感锚点 — sans-serif 正文中性,情感放在引用块色彩里

### 8. 开头处理

- 第一段 ≤80 字(易入口)
- 100 字内出现价值承诺
- 200 字内插入首图
- **banned 短语**:「大家好」「今天聊聊」「话说」「朋友们」「各位朋友」「今天我们来」「今天来聊」
- 禁正文重复 title(微信卡片已显示)

**出处**:本地 SOP + Jobs#1 Apple 首句 ≤12 词原则

### 9. 结尾处理

- 总结段 80-120 字
- **1 个具体问题 CTA**(不是「关注我」,而是「你怎么看 X?」)
- 自动加风云签名(#FAF9F5 底 + 邮箱微信)
- **banned 短语**:「感谢阅读」「点赞收藏」「往期回顾」「感谢支持」「求点赞」「求转发」「求关注」

**出处**:Jobs 删减测试 + Apple 风格 CTA(具体下一步,不是抽象号召)

---

## 四、模块接口

### Python API

```python
from tools.layout_rules import render_to_wechat_html, lint, LAYOUT_RULES

# 渲染
html = render_to_wechat_html(
    markdown_text,
    section_image_urls=[url_hero, url_section1, url_section2, ...],  # 必须 mmbiz.qpic.cn
    signature_html=None,    # None 用默认风云签名
    strip_frontmatter=True,
)

# 自检(空 list = 全通过)
issues = lint(html)

# 看规则常量(每条带 source)
print(LAYOUT_RULES["font"]["body_px"])  # → 15
print(LAYOUT_RULES["font"]["source"])   # → 调研出处
```

### CLI

```bash
# 基础渲染
python tools/layout_rules.py output/drafts/<slug>.md

# 加章节图(URL 顺序对应 hero + 每个 H2)
python tools/layout_rules.py <draft.md> --image https://mmbiz.qpic.cn/... --image ...

# 只跑 lint 不输出 HTML
python tools/layout_rules.py <draft.md> --lint-only

# 生成本地浏览器可打开的 preview(带 <html><body> 包装)
python tools/layout_rules.py <draft.md> output/html/preview.html --preview
```

### 集成到 fengyun-publish Step 8

**Round 21 决策 1(2026-05-25)更新** — 排版统一花叔,legacy 已物理砍掉:

```bash
# 唯一渲染路径(huashu 默认,任何 style 输入都被 redirect 到 huashu)
python tools/post_fengyun_publish.py output/drafts/<slug>.md
```

**已砍**:
- `--render-mode legacy`(argparse 选项已删 + `_render_html_legacy` 函数已删)
- `style=default / classic`(layout_rules.py 78 行 default 分支 + 13 个 default-only helper 已删)
- 任何 `style` 输入(包括 `default` / `classic`)都被 `render_to_wechat_html` redirect 到 huashu(向后兼容)

---

## 五、Lint 自检项

跑 `lint(html)` 返回违规清单(空 list = 全过):

1. **HTML 长度 ≤ 60,000**(Round 21 P0-17 升级,2026-05-25)— 原 20,000 是 layout_rules 内部历史值,无外部出处。微信草稿真实物理上限 ~65,000,留 5,000 缓冲到 60,000。huashu 模板 inline style 膨胀 ~5x,4000 字 markdown 渲染后稳定在 20,000-25,000 字节,远低于新上限
2. 禁用标签 `<style>` / `<iframe>` / `<script>` / `<form>` / `<video>` / `<table>` / `<hr>`
3. class / id 属性(微信会剥)
4. 浅灰文字 #9XX / #aXX / #bXX(暗黑模式不可见)
5. position absolute / fixed(微信剥除,布局崩)
6. 百分比 margin / transform(微信端失效)

**fengyun_lint R12b warn**(配套,Round 21 P0-17):
- markdown × 5 倍膨胀估算 > 50,000 → low severity warn(留 10k 缓冲到 60k 硬上限)
- 不阻断 ship,但提示作者文章接近上限

**Round 23 huashu 高亮 2 bug 修(2026-05-25)**:
- **Bug 1 punct 错位**:`_fix_cjk_bold_punctuation` 拆分两套字符集 — 末尾踢出激进(全套 ASCII + 全角),开头踢出保守(只全角 + ASCII 引号 `"` `'` + 冒号 `:`)+ lookbehind `(?<!\*)`。修法根因:开头加 ASCII 半角逗号会让 `**A**,**B**` 连续 bold 被误判成「,开头 bold」
- **Bug 2 高亮过密**:fengyun_lint 新增 R26 + R27 双密度规则,LLM 改稿循环收敛到「每段 ≤ 1 + 全文 ≤ 5」。这是「比花叔本人更克制」的设计(花叔 corpus 20% 篇单段 ≥ 2 处,Round 23 主动选更严)

---

## 六、测试结果

### v4 草稿端到端

- 输入:5,382 字 markdown
- 输出:14,704 字 HTML
- lint:**0 issues**

### 渲染元素清点(历史对比,仅作参考)

> **Round 21 决策 1 后**:legacy 已砍,以下对比仅作历史参考。当前所有 ship 都走 layout_rules huashu T-A。

| 元素 | layout_rules(huashu T-A,唯一活跃)| legacy(已砍)|
|---|---|---|
| `<p>` 段数 | 90 | ~~85~~ |
| `<blockquote>` | 0(v4 无引用)| ~~0~~ |
| `· · ·` 分割线 | 4(章节间)| ~~0~~ |
| `<hr>` | 0 | ~~0~~ |
| 字号 | 17px 正文 + 20px H2 + 22px 标题(huashu T-A)| ~~15/18/22~~ |
| 行高 | 1.75 正文 + 1.4 H2 + 1.7 引用 | ~~1.85/1.4/1.8~~ |
| 主色 | #C15F3C(huashu T-A 陶土橙)+ #faf9f7 暖米黄底 | ~~#D97757~~ |

---

## 七、Jobs 保留意见(非阻塞,但要正视)

> R18 三层防御的存在本身是 writer persona 设计不足的补丁信号。如果 fengyun-writer SKILL.md 足够强,L2/L3 应是稀有路径,而不是常规检查。建议系统稳定后,**优先加固 L1(writer 层)**,而非不断细化 L2/L3 规则。

> L2 lint 是烟雾报警器,不是灭火器。

---

## 八、关联文件

- `tools/layout_rules.py` — 本文档对应主模块
- `tools/post_fengyun_publish.py` — 集成入口(默认 layout_rules)
- `tools/fengyun_lint.py` — R18 分级(Round 2)
- `tools/critic_vote.py` — 门控树(Round 2)
- `tools/r18_dashboard.py` — 触发率监控(Round 2)
- `WRITING_SOP_PRIORITIES.md` — 历史 SOP(Phase 1+3)
- `~/.claude/skills/fengyun-publish/SKILL.md` — orchestrator skill(已对齐)

---

## 九、下次扩展方向

1. **加固 L1 fengyun-writer SKILL.md**(Jobs 保留意见的执行)
2. 自动判定章节图位置(目前按 H2 顺序对应,可加更智能判定)
3. 短段子弹自动插入(每 3-5 段插 1 个 20-40 字短段 — 当前未实现自动插入)
4. 真推一篇试跑 + 手机端查看微信渲染效果
5. 45 天后跑 `r18_dashboard.py` 看 P1/P2 触发率分布
6. Musk 要求的「3 轮 revise → human_gate」实际比例分析,决定是否回退 2 轮
