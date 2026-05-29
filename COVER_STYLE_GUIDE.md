# 风云公众号封面 + 插图 风格规范

*基于 Phase 5 + Phase 6 沙盒辩论*
*2026-05-22 v2 锁定(翻转为 baoyu sketch-notes 风格)*

---

## ⚠️ v2 vs v1 重大变更(读懂这条再看下面)

**v1 旧方案**:flat-vector + 70% 留白 + no text + 单彩色家族 → ❌ 全错方向
**v2 新方案**:hand-drawn sketchnote + 卡通人物 + 标题嵌入图 + 暖色多色饱满 → ✅ 对标宝玉

风云 2026-05-22 反馈"图案太简单",Musk × Jobs Phase 6 沙盒辩论完整翻转。
实测豆包 Seedream 复现宝玉风相似度 85-95%。

---

## 一、核心识别度三件套(每张封面必含)

| 元素 | 值 | 实现 |
|---|---|---|
| **底色** | 暖米黄/暖象牙 `#F8F0E0` / `#FAF9F5` | paper grain 纸质纹理 |
| **主强调色** | 陶土橙 `#D97757`(Anthropic 同族)+ 黄高亮 `#F6AD55` | 标题底色/线条 |
| **云朵签名** | 左上角 small floating cloud labeled「云」 | 风云专属(融入场景,非孤立 logo)|

**风云 vs 对标账号的区分**:
- 宝玉 = sketch-notes + 标题中文嵌入 + 卡通人物
- 赛博禅心 = 禅意极简(无陶土橙强调)
- **风云 = sketch-notes 同款 + 「云」字签名** ← 跟宝玉一个量级,但有自己签名

---

## 二、辅助色板(取自 Refero Design System Claude/Anthropic)

| 角色 | 名称 | Hex |
|---|---|---|
| 主强调 | Clay | `#D97757` |
| 悬停强调 | Accent Ember | `#C6613F` |
| 底色 | Ivory Light | `#FAF9F5` |
| 次级底 | Ivory Medium | `#F0EEE6` |
| 三级底 | Ivory Dark | `#E8E6DC` |
| 燕麦卡片 | Oat | `#E3DACC` |
| 弱化分割线 | Cloud Light | `#D1CFC5` |
| 弱化文字 | Cloud Medium | `#B0AEA5` |
| 主文字 | Slate Dark | `#141413` |
| 橄榄绿(辅) | Olive | `#788C5D` |

**铁律**:整张封面只允许出现 1 个彩色家族(陶土橙)。其他全是暖中性色 + 黑。不许蓝/红/绿/紫。

---

## 三、5 个分类模板(分类路由 + 各自 seed)

### 路由规则
扫描 `output/research/YYYYMMDD-<slug>.md` 前 200 字 → 关键词命中 → fallback 标题 → fallback T5

```python
CATEGORY_RULES = {
    "T1_agent":    ["agent", "智能体", "多智能体", "协作", "workflow", "mcp", "orchestrat", "harness"],
    "T2_research": ["调研", "评测", "深度", "解析", "拆解", "报告", "论文", "分析", "实测"],
    "T3_compare":  ["vs", "对比", "横评", "测评", "哪个好", "选择", "选型"],
    "T4_news":     ["发布", "上线", "宣布", "更新", "新版", "新功能", "重磅", "开源"],
    "T5_method":   ["方法", "框架", "系统", "思考", "哲学", "反思", "本质", "理解", "是什么", "为什么"],
}
DEFAULT_TEMPLATE = "T5_method"
```

---

### T1 · Agent 网络 / 多智能体协作

**Prompt**:
```
A flat-vector editorial illustration on a warm cream paper background (#FAF9F5).
Abstract minimalist scene: several glowing soft-orange circular nodes connected by clean
geometric lines, suggesting a multi-agent network. The nodes pulse with warm terracotta
light (#D97757) against an ivory field. Above the network, a soft abstract cloud silhouette
formed by the arrangement of the outermost nodes — the cloud shape emerges naturally from
the geometry, rendered in terracotta outline, suggesting "the cloud that studies agents".
Style: clean flat design, subtle hand-drawn texture on node edges, generous white space (65%+),
no text, no humans, no photorealism. Mood: intellectual warmth, calm emergence. Aspect 2.35:1.
```

**Seed**:`待 Day 1 跑 10 张选最佳后填入`

---

### T2 · 深度研究 / 思考分析

**Prompt**:
```
A minimal editorial cover illustration in warm editorial style. Background: aged parchment
texture (#F5F0E8). Central motif: a single open book rendered in clean flat linework with
terracotta orange (#D97757) spine. Floating above the book, a soft abstract cloud silhouette
drawn with a single continuous terracotta line (stroke 1.5px), like a thought bubble
transforming into a cloud — evoking "research clouds". A soft glowing magnifying glass
overlaps the top corner. Generous negative space surrounds the central element. Style:
hand-drawn sketchnote with slight paper grain, no gradient fills, flat color only.
Mood: deep thinking, research, slow reading. 16:9 aspect ratio.
```

**Seed**:`待 Day 1 跑 10 张选最佳后填入`

---

### T3 · 工具测评 / 产品对比

**Prompt**:
```
A clean flat editorial cover in warm Anthropic aesthetic. Scene: two or three simplified
geometric UI windows or cards arranged asymmetrically on a warm ivory background (#F0EEE6).
One card is highlighted with a soft terracotta border (#C6613F). In the upper-right corner,
a small geometric cloud icon (abstract, 3-4 rounded bumps, terracotta outline only, no fill,
approximately 80x50px equivalent) marks the "researcher's perspective" viewpoint.
Thin olive-green (#788C5D) horizontal rule divides the composition. No text. No photorealistic
elements. Style: flat-vector design, zero gradients, clean outline stroke 1.5px, very generous
padding. Mood: balanced comparison, objective analysis, calm precision. 16:9 widescreen.
```

**Seed**:`待 Day 1 跑 10 张选最佳后填入`

---

### T4 · AI 前沿动态 / 新模型发布

**Prompt**:
```
An editorial conceptual illustration with a warm cream base (#F5F0E8). A large abstract
cloud formation — soft rounded cumulus shape rendered entirely in flat terracotta (#D97757)
with fine radiating dotted lines emerging from its edges, suggesting emergence and release —
sits centered as the primary visual. The cloud is stylized: geometric, not naturalistic,
built from overlapping circles and smooth curves at 2.35:1 cinematic proportions.
Fine dotted lines radiate outward from the cloud's edges in cloud-gray (#B0AEA5).
Background has a subtle paper grain texture. Style: editorial flat illustration,
minimal hand-drawn details, no text, no photorealism. Mood: anticipation, emergence,
intelligent expansion. Aspect ratio 2.35:1.
```

**Seed**:`待 Day 1 跑 10 张选最佳后填入`

---

### T5 · 方法论 / 系统思维 (旗舰主力,默认 fallback)

**Prompt**:
```
A minimalist editorial illustration blending warm Anthropic aesthetic with subtle East Asian
ink wash sensibility. Background: warm ivory (#FAF9F5) with very light paper texture.
Central composition: a single abstract cloud form drawn with one continuous terracotta
brushstroke (#D97757, stroke weight 2px), occupying 30-40% of the image area, centered
slightly above middle. The cloud is abstract and flowing — not a cartoon cloud, but an
elegant calligraphic gesture suggesting lightness and inquiry. Below the cloud, three thin
horizontal geometric lines in cloud gray (#B0AEA5) suggest structure, ground, and flow.
Extremely generous white space (70%+). No text, no gradients, no photorealism.
Style: minimal flat with ink wash texture on the cloud stroke.
Mood: clarity, systems thinking, calm intelligence, researcher's spirit. 16:9 widescreen.
```

**Seed**:`待 Day 1 跑 10 张选最佳后填入`

---

## 四、禁用元素清单(v2 翻转后)

每张封面**严格禁用**:

- ❌ 渐变紫 / 渐变蓝背景
- ❌ 科幻感深色底
- ❌ 写实人像 / 摄影素材(**卡通简化人物 ✅ 允许**)
- ❌ 荧光 / 高饱和彩色
- ❌ 机械感写实机器人头(**卡通工程师 / 简化角色 ✅ 允许**)
- ❌ 抽象 flat-vector 极简(**这是 v1 错误方向,已废**)
- ❌ 70%+ 大留白(**v2 要饱满构图**)

**允许并鼓励**:
- ✅ 卡通人物(简单脸 / hoodie / 思考姿态)
- ✅ 中文标题嵌入图中(右侧大字 + 黄高亮 + 「」括号)
- ✅ 副标在虚线框
- ✅ 装饰元素(星星 / 绿叶 / 云朵 / 小图标)
- ✅ 暖色家族多色(陶土橙主 + 黄高亮 + 橄榄绿点缀)
- ✅ 大脑 / 笔记本 / 工具图标(场景叙事用)

---

## 五、工具调用优先级链(Phase 5 follow-up 翻转后)

| 层级 | 工具 | 价格 | 触发条件 |
|---|---|---|---|
| **主力** | 豆包 Seedream 5.0(火山引擎方舟)`doubao-seedream-5-0-260128` | 测试期免费 / 商用极低 | 默认 |
| **降级 1** | 阿里云万相 `wan2.6-image` | 90 天免费额度 | 主力超时/报错 |
| **兜底** | `baoyu-cover-image` skill(baoyu-imagine 后端) | 取决于 runtime | 国内 API 全挂 |
| **应急** | fal.ai Seedream Lite | $0.035/张 | 国内/国外全挂(极少触发) |

**为什么主力是豆包 Seedream(火山引擎)而不是 fal.ai**:
- 用户 `.env` 已配 `VOLCENGINE_IMAGE_KEY`,直接可用
- 完全国内 + 测试期免费,符合"国内 + 免费/极低成本"硬约束
- Seedream 5.0 模型本身在火山引擎和 fal.ai 上是同一个,fal.ai 只是 proxy
- Musk × Jobs follow-up 已承认原方案漏判,翻转

---

## 六、Step 7 自动化接入

`tools/generate_cover_by_template.py` 提供:
- 接受 `<draft.md>` + `<research.md>`(可选)
- 自动分类路由
- 调豆包 Seedream API(火山引擎方舟)
- 保存到 `output/images/YYYYMMDD-<slug>-cover.png`
- 失败降级到 baoyu-imagine

`fengyun-publish` SKILL.md Step 7 已更新指向该脚本。

---

## 七、seed 配置表(Day 1 跑完填入)

| 模板 | 最佳 Seed | 备选 Seed | 更新日期 |
|---|---|---|---|
| T1_agent | — | — | — |
| T2_research | — | — | — |
| T3_compare | — | — | — |
| T4_news | — | — | — |
| T5_method | — | — | — |

**月度更新**:每月初 5 分钟跑 10 次 × 5 模板,选最佳 seed 更新此表。

---

## 八、变更日志

| 日期 | 变更 |
|---|---|
| 2026-05-22 | 初版 — Phase 5 follow-up 翻转方案锁定。主力翻转为豆包 Seedream(火山引擎)|
