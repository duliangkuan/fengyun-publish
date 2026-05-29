# Vendor Code Deep-Dive 报告

**分析日期**: 2026-05-24  
**分析对象**: wenyan / xiaohu-wechat-format / html-anything  
**目标**: 排版/格式相关代码的可借鉴点 + 可复用代码精确定位

---

## Phase 1: 架构梳理

### 1. caol64/wenyan

| 维度 | 情况 |
|------|------|
| 入口 | macOS 桌面 App（Swift + SvelteKit WebView） |
| 主题定义 | CSS 字符串，通过 `ThemeStorageAdapter` 存取，`CustomTheme = {id, name, css}` |
| 主题切换 | UI 面板选择，调用 `wenyanCopier.copy(element)` |
| Render | `@wenyan-md/core`（npm 包，未开源进 clone 目录），`wenyanCopier` 封装具体逻辑 |
| 公众号直推 | 有，通过 Swift bridge `publishArticleToDraft` → `/cgi-bin/draft/add`，接口见 `action.ts:110` |

**关键发现**:  
wenyan 主仓是 macOS App，核心渲染逻辑在外部 npm 包 `@wenyan-md/core`（该包未随 clone），本地 clone 目录只有 bridge 层。因此主题 CSS 结构和渲染引擎**无法从本地 clone 直接读取**。唯一可参考的是 Swift→JS 的 WKWebView bridge 架构，以及 `themeStorageAdapter`（`src/lib/adapters/themeStorageAdapter.ts:1`）展示的主题 CRUD 接口设计。

**可运行命令**: `pnpm install && pnpm web:build`（需 macOS + Xcode，Windows 不适用）

---

### 2. xiaohuailabs/xiaohu-wechat-format

| 维度 | 情况 |
|------|------|
| 入口 | CLI（`python3 scripts/format.py --input article.md --theme newspaper`）+ SKILL.md Claude Code 技能 |
| 主题定义 | JSON 文件（`themes/*.json`），每文件一个主题，含 `colors` + `styles` + `dark_mode` 三段 |
| 主题切换 | `--theme <name>` CLI 参数；矩阵主题用 `layout-palette` 命名（如 `minimal-gold`）自动合并 |
| Render | 纯 Python：`scripts/format.py` 自实现 Markdown→HTML + 内联样式注入，约 1800 行 |
| 公众号直推 | 有（`scripts/publish.py`），调用 `/cgi-bin/draft/add`，含封面图上传和正文图片批量替换 CDN |

**30 套主题分类**:  
- 独立风格 9 套（flat JSON，每个独立文件）  
- 精选风格 7 套（同上）  
- 模板系列 14 套 = 4 种布局 × 多色板（`themes/layouts/*.json` + `themes/palettes/*.json`，通过 `merge_layout_palette()` 合并）  
- 布局 JSON 内用 `{{accent}}` 占位符，合并时被色板值替换（`format.py:146-195`）

**可运行命令**:  
```bash
pip3 install markdown requests
cp config.example.json config.json  # 填写路径
python3 scripts/format.py --input article.md --theme newspaper
python3 scripts/format.py --input article.md --gallery --recommend newspaper ink
```

---

### 3. nexu-io/html-anything

| 维度 | 情况 |
|------|------|
| 入口 | Next.js Web App（`pnpm -F @html-anything/next dev`） |
| 主题定义 | `SKILL.md` frontmatter（yaml头）+ prompt body，每个 Skill 一个文件夹，无 CSS 文件 |
| 主题切换 | UI 技能选择器，`/api/templates` 返回注册表，frontmatter `scenario/category/featured` 排序 |
| Render | AI（Claude/GPT）生成完整 HTML；juice 库仅用于微信导出路径（`export/wechat.ts:41`） |
| 公众号直推 | **仅复制粘贴**（`toWechatHtml()` + `copyHtml()`），无 API 直推 |

**juice 接入**（`export/wechat.ts:11-51`）：
```
juice.inlineContent(tagged, css, {
  inlinePseudoElements: true,
  preserveImportant: true,
})
```
juice 处理的是从 `<style>` 标签收集的 CSS 字符串，不处理 Tailwind CDN（Tailwind 在客户端 DOM 里运行，juice 在字符串层面无法触达 Tailwind 生成的类）。因此 juice 对 Tailwind 驱动的模板效果有限，只对手写 `<style>` 块有效。

---

## Phase 2: 深读关键文件

### wenyan — 关键文件

| 文件 | 行号 | 要点 |
|------|------|------|
| `src/lib/adapters/themeStorageAdapter.ts` | 1-23 | 主题三字段设计：`{id, name, css}`；load/save/remove 三接口抽象，与存储无关 |
| `src/lib/action.ts` | 110-112 | `publishArticleToDraft(publishOption: WechatPublishOptions)` → Swift bridge，是唯一推文入口 |
| `src/lib/services/exportHandler.ts` | 1-72 | 截图导出：克隆 DOM → 等待图片加载 → `domToPng(scale:2)` → base64，`width:420px` 固定 |
| `src/lib/services/copyHandler.ts` | 1-17 | 掘金平台走文本路径（`wenyanRenderer.postHandlerContent`）；其余走 HTML clipboard |

---

### xiaohu-wechat-format — 关键文件

| 文件 | 行号 | 要点 |
|------|------|------|
| `scripts/format.py` | 115-143 | `load_theme()` 三步退化：flat JSON → layouts+palettes 合并 → 报错列出可用选项 |
| `scripts/format.py` | 146-195 | `merge_layout_palette()`：JSON dump 为字符串 → str.replace `{{占位符}}` → JSON load 回来；派生色（10%/30% 透明度）用 hex→rgba 计算 |
| `scripts/format.py` | 720-729 | `build_style_string()`：JSON key 下划线→CSS 连字符，5 行纯 Python |
| `scripts/format.py` | 732-767 | `_auto_dark_mode()`：对未显式声明 dark_mode 的标签（p/strong/em/h3~h6/td 等）自动生成深色覆盖值 |
| `scripts/format.py` | 770-794 | `inject_dark_mode_attrs()`：通过 `data-darkmode-bgcolor` / `data-darkmode-color` 属性实现微信深色模式，精准匹配 style 字符串注入 |
| `scripts/format.py` | 1158-1330 | `inject_inline_styles()`：核心注入函数，处理顺序：列表→callout→blockquote→pre/code→简单标签；微信 pre 换行必须转 `<br>`，空格必须转 `&nbsp;` |
| `scripts/format.py` | 232-268 | `fix_cjk_spacing()`：中英文间自动加空格，保护行内代码/URL/图片链接不被修改 |
| `scripts/format.py` | 271-282 | `fix_cjk_bold_punctuation()`：把中文标点从 `**xxx，**` 移到 `**xxx**，` |
| `scripts/format.py` | 469-549 | `process_fenced_containers()`：`:::dialogue/gallery/stat/timeline/steps/compare/quote` 容器语法，支持嵌套 |
| `scripts/format.py` | 1527-1584 | `generate_gallery()`：5 大分组按钮 + 并行渲染所有主题（`ThreadPoolExecutor`）+ 单预览区 JS 切换 |
| `scripts/format.py` | 1472-1487 | `convert_image_captions()`：图片后紧跟斜体段落 → 图说样式（`</section>` / `</p>` 后匹配） |
| `scripts/publish.py` | 98-131 | `upload_content_image()`：上传正文图片含 3 次自动重试 |
| `scripts/publish.py` | 213-243 | `push_draft()`：`json.dumps(ensure_ascii=False)` 防中文转义导致标题长度计算错误 |

---

### html-anything — 关键文件

| 文件 | 行号 | 要点 |
|------|------|------|
| `next/src/lib/export/wechat.ts` | 11-51 | `toWechatHtml()`：DOMParser 解析 → 收集 `<style>` 内容 → `juice.inlineContent()` → 顶层元素加 `data-tool="html-anything"` → `<section>` 包裹 |
| `next/src/lib/export/wechat.ts` | 41-46 | juice 选项：`inlinePseudoElements:true, preserveImportant:true`；try/catch 失败降级返回未内联版本 |
| `next/src/lib/export/clipboard.ts` | 1-72 | `copyHtml()`：现代 ClipboardItem API → 失败降级 `execCommand copy`（Safari 兼容） |
| `next/src/lib/extract-html.ts` | 5-63 | `extractHtml()`：5 级降级：fence → DOCTYPE → `<html>` → `<` → 降级 scaffold；处理 AI 输出的 chatty 前置文字 |
| `next/src/lib/templates/loader.ts` | 94-150 | `parseFrontmatter()`：无外部依赖的 YAML 子集解析器，支持 string/int/array 三种类型 |
| `next/src/lib/templates/loader.ts` | 196-207 | `metaCache`：生产环境缓存 SkillMeta 列表，dev 环境跳过，支持 `invalidateSkillsCache()` 主动失效 |
| `next/src/lib/templates/shared.ts` | 6-38 | `SHARED_DESIGN_DIRECTIVES`：全局硬约束（8px 基线、65ch 段宽、对比度≥4.5、CJK 字体栈、Noto Sans SC/Inter），每次 AI 调用前置注入 |
| `next/src/lib/templates/shared.ts` | 46-58 | `assemblePrompt()`：`SHARED_DIRECTIVES + skill body + 用户内容`，统一 prompt 拼接 |
| `next/src/lib/skills/registry.ts` | 123-143 | `listUserSkills()`：扫描 `~/.html-anything/skills/<pkg-id>/skills/<original-id>/SKILL.md`，缺 SKILL.md 则静默跳过（健壮） |
| `next/src/lib/export/zhihu.ts` | 10-26 | `toZhihuHtml()`：复用 `toWechatHtml()` + 替换 MathJax 为 `data-eeimg` img 标签，展示 pipe 复用模式 |
| `next/src/lib/templates/skills/article-magazine/SKILL.md` | 全文 | 最接近公众号长文 skill；frontmatter 有 `example_id`，浏览器中内嵌 example.html 预览 |

---

## Phase 3: 与 fengyun-publish 对比

### 比较基准

我们现有：
- `tools/layout_rules.py`（~979 行）：硬编码 9 维度规则字典 + 渲染函数
- `tools/layout_rules_huashu.yaml`：huashu 风格配置（YAML）
- `tools/fengyun_lint.py`（~915 行）：机械规则 lint
- `tools/post_fengyun_publish.py`：发布入口（含 `_render_html_layout_rules()`）

---

### 亮点 A：JSON 主题 + `build_style_string` 机制（xiaohu）

**来源**: `scripts/format.py:720-729`  
**内容**: JSON key 用下划线（`font_size`），转 CSS 时 `.replace("_", "-")`，5 行代码  

| 指标 | 情况 |
|------|------|
| 我们有吗? | 部分有。`layout_rules_huashu.yaml` 用 YAML 定义，但渲染时是 Python f-string 硬拼，**没有统一的 `build_style_string` 转换层** |
| 可以直接抄? | **可以**。新增 `tools/theme_utils.py`，5 行，改动量极小 |
| 冲突? | 无冲突，属于纯新增工具函数 |

---

### 亮点 B：Layout × Palette 矩阵组合（xiaohu）

**来源**: `scripts/format.py:146-195` + `themes/layouts/` + `themes/palettes/`  
**内容**: 布局 JSON 内含 `{{accent}}` 占位符，色板 JSON 提供 16 进制值 + 派生色（10%/30% 透明度自动计算），`merge_layout_palette()` 用字符串替换合并

| 指标 | 情况 |
|------|------|
| 我们有吗? | **没有**。目前只有默认风格和 huashu 风格，两个完全独立的配置文件，无法矩阵组合 |
| 可以直接抄? | **可以**。将 `layout_rules_huashu.yaml` 拆分为 layout（结构规则）+ palette（色板），在 `layout_rules.py` 内实现 `merge_layout_palette()` 约 30 行 |
| 冲突? | 字段命名暂无冲突；YAML vs JSON 格式需统一（建议全改 YAML） |

---

### 亮点 C：微信深色模式 `data-darkmode-*` 属性（xiaohu）

**来源**: `scripts/format.py:770-794` + `_auto_dark_mode():732-767`  
**内容**: 在内联 style 属性旁加 `data-darkmode-bgcolor="..." data-darkmode-color="..."`，微信 App 黑暗模式时自动覆盖；未声明 dark_mode 的标签通过 `_auto_dark_mode()` 自动补全

| 指标 | 情况 |
|------|------|
| 我们有吗? | **完全没有**，目前只有亮色模式 |
| 可以直接抄? | **可以**。把 `inject_dark_mode_attrs()` 函数（约 25 行）+ `_auto_dark_mode()`（约 35 行）整体搬入 `layout_rules.py`，在 `render_to_wechat_html()` 末尾调用 |
| 冲突? | 无；纯增量 |

---

### 亮点 D：CJK spacing + bold punctuation 自动修复（xiaohu）

**来源**: `scripts/format.py:232-282`  
**内容**: `fix_cjk_spacing()`（中英间加空格，保护代码块/URL/链接不被改） + `fix_cjk_bold_punctuation()`（`**文字，**` → `**文字**，`）

| 指标 | 情况 |
|------|------|
| 我们有吗? | **没有**。目前 `layout_rules.py` 无预处理步骤，直接渲染原始 Markdown |
| 可以直接抄? | **直接复制**这两个函数（约 50 行），在 `render_to_wechat_html()` 的 Markdown 预处理阶段调用 |
| 冲突? | 无 |

---

### 亮点 E：juice 的接入模式（html-anything）

**来源**: `next/src/lib/export/wechat.ts:41-46`  
**内容**: `juice.inlineContent(html, css, {inlinePseudoElements:true, preserveImportant:true})`；收集页面所有 `<style>` 内容拼接成 css 字符串传入

| 指标 | 情况 |
|------|------|
| 我们有吗? | **不需要**。我们是 Python 实现，直接输出内联 style，跳过了 juice 这一层。juice 是 JS 生态的解决方案 |
| 可以直接抄? | **不建议**引入 juice 到 Python 侧；Python 等价是直接在生成 HTML 时就写 inline style（我们已经这样做了）。juice 对我们无增量价值 |
| 冲突? | 无冲突但无必要 |

---

### 亮点 F：SHARED_DESIGN_DIRECTIVES 全局硬约束前置注入（html-anything）

**来源**: `next/src/lib/templates/shared.ts:6-38`  
**内容**: 所有 Skill 的 prompt 前都拼接统一的设计约束：8px 基线、65ch 段宽、CJK 字体栈、对比度要求、颜色数量限制等

| 指标 | 情况 |
|------|------|
| 我们有吗? | **有类似机制**，但分散在 `fengyun_lint.py` 的 lint 规则里，不是写作 prompt 前置注入 |
| 可以直接抄? | **可以**。将 `LAYOUT_RULES`（`layout_rules.py:39-124`）的核心要点浓缩成一个 `WRITING_SYSTEM_PROMPT` 字符串，在 writer prompt 里前置注入，让 AI 生成阶段就符合规则，减少 lint 修复量 |
| 冲突? | 无 |

---

### 亮点 G：图说自动检测（xiaohu）

**来源**: `scripts/format.py:1472-1487`，`convert_image_captions()`  
**内容**: 图片（`</section>` 或 `</p>`）后紧跟 `<p><em>xxx</em></p>` 的段落 → 自动转为图注样式

| 指标 | 情况 |
|------|------|
| 我们有吗? | **没有**，`layout_rules.py` 中明确禁用 `caption_allowed: False` |
| 可以直接抄? | 暂不需要，我们策略是禁图注 |
| 冲突? | 不冲突，仅策略不同 |

---

### 亮点 H：`ensure_ascii=False` 防中文转义（xiaohu）

**来源**: `scripts/publish.py:232`  
**内容**: `json.dumps(data, ensure_ascii=False).encode("utf-8")`，防止中文标题被转为 `\uXXXX` 导致微信计算标题字节长度错误

| 指标 | 情况 |
|------|------|
| 我们有吗? | 需要确认 `post_fengyun_publish.py` 中的 `json.dumps` 调用是否有此参数 |
| 可以直接抄? | 一行修改，极低成本 |
| 冲突? | 无 |

---

### 亮点 I：`extractHtml()` 5 级降级解析（html-anything）

**来源**: `next/src/lib/extract-html.ts:5-45`  
**内容**: 处理 AI 输出时解析 HTML 的健壮策略：fence → DOCTYPE → `<html>` → `<` → 降级 scaffold

| 指标 | 情况 |
|------|------|
| 我们有吗? | **有部分**。`post_fengyun_publish.py` 中处理 writer 输出时有基础的 frontmatter 解析，但没有对 AI 输出中 HTML 块的健壮提取 |
| 可以直接抄? | 可以翻译成 Python（约 20 行），用于处理 writer AI 回复中可能的 Markdown fence 包裹 |
| 冲突? | 无 |

---

## Phase 4: 可复用清单（精筛 Top 8）

| 项 | 来源 | 我们的接入点 | 改动量 | 价值 |
|----|------|-------------|--------|------|
| 1 | `build_style_string()` (`format.py:720-729`) | `tools/theme_utils.py` 新增，供 `layout_rules.py` + 未来主题 JSON 用 | 5 行新增 | 消除样式拼接散落 |
| 2 | `fix_cjk_spacing()` (`format.py:232-268`) | `render_to_wechat_html()` 预处理阶段 | 直接复制 40 行 | 解决中英混排间距，提升专业度 |
| 3 | `fix_cjk_bold_punctuation()` (`format.py:271-282`) | 同上，接在 `fix_cjk_spacing()` 后 | 直接复制 12 行 | 杜绝加粗末尾标点挂在 `**` 内 |
| 4 | `inject_dark_mode_attrs()` + `_auto_dark_mode()` (`format.py:732-794`) | `render_to_wechat_html()` 末尾追加 | 约 60 行 | 微信黑暗模式支持，白嫖功能 |
| 5 | Layout × Palette 矩阵设计（`format.py:146-195`） | 新增 `tools/themes/layouts/` + `palettes/`，重构主题加载 | 中量（约 50 行 + YAML 拆分） | 用 4 布局 × 色板 = N 套主题，而不是写 N 个完整文件 |
| 6 | `SHARED_DESIGN_DIRECTIVES` 前置注入模式（`shared.ts:6-38`） | 将 `LAYOUT_RULES` 核心浓缩为 writer prompt 系统提示词前缀 | 约 20 行字符串 | 减少 lint 修复量（规则从出口转到入口） |
| 7 | `ensure_ascii=False` 防转义（`publish.py:232`） | `post_fengyun_publish.py` 的 `json.dumps` 调用 | 1 行 | 防止中文标题字节长度计算错误 |
| 8 | Gallery 分组按钮 + 并行渲染（`format.py:1505-1584`） | 可参考实现我们自己的主题预览 CLI（目前没有） | 中量，可选做 | 选题前直观对比多主题效果 |

---

## 整体洞察

### 最大架构启发：JSON/YAML 驱动 vs Python 硬编码

**xiaohu 的核心洞察**：主题定义（颜色+尺寸+间距）全部放 JSON/YAML，用极薄的 `build_style_string()` 转换层（5 行）粘合。新增主题 = 新增一个 JSON 文件，**零代码改动**。

我们目前的 `layout_rules.py` 是混合态：规则数据用 Python 字典（`LAYOUT_RULES`），渲染函数是硬编码 f-string。huashu 风格用 YAML 定义，但读取 YAML→渲染 HTML 之间的桥梁不清晰。

**建议路线**：
1. 保留 `LAYOUT_RULES` 字典（作为风云默认风格的规则），但增加 `build_style_string()` 工具
2. 为"风云默认"也生成一个 `themes/fengyun.json`，让主题切换机制统一（现在 huashu 是 YAML，默认是 Python 字典，不对称）
3. 未来新主题只加 JSON/YAML，不改 Python 代码

---

### 反例：juice 在 Python 管线中无用

html-anything 使用 `juice` 库的原因是：Next.js 用 Tailwind CDN 在浏览器 runtime 生成内联样式，AI 生成的 HTML 里没有 CSS 字符串可供服务器端处理；juice 是在"能拿到 `<style>` 块"时的补救手段。

**我们的 Python 管线不需要 juice**：`layout_rules.py` 直接生成带 `style=` 属性的 HTML，天然已是内联样式。引入 juice（Node.js 库）反而增加跨语言依赖，无增量价值，**不建议引入**。

---

### 主题适合 AI 圈的推荐

从 xiaohu 30 套主题中，最适合"研究Agent的云"AI 技术公众号的：

1. **newspaper**（报纸风 `#326891` 蓝灰）— 严肃深度长文，AI 行业分析
2. **sspai**（少数派红 `#D71A1B`）— 科技评测风，产品测评类
3. **github**（开发者风，浅色代码块）— 技术教程类，有大量代码
4. **ink**（纯黑水墨，极简留白）— 思考类文章，高密度文字
5. **bytedance**（蓝青渐变，科技现代）— 产品发布/行业动态类

---

## 附：本地可运行命令

### xiaohu-wechat-format

```bash
cd D:\Dev\ai-wechat-pipeline\vendor\xiaohu-wechat-format
cp config.example.json config.json  # 编辑填写路径
pip3 install markdown requests

# 单主题排版
python3 scripts/format.py --input <article.md> --theme newspaper

# 主题画廊（浏览器对比）
python3 scripts/format.py --input <article.md> --gallery --recommend newspaper ink sspai

# 推送草稿箱（需填写 config.json wechat 段）
python3 scripts/publish.py --dir /tmp/wechat-format/<article>/ --cover cover.jpg
```

### html-anything

```bash
cd D:\Dev\ai-wechat-pipeline\vendor\html-anything
pnpm install --frozen-lockfile
pnpm -F @html-anything/next dev
# 访问 http://localhost:3000
```

### wenyan

仅支持 macOS，Windows 下只能读代码，不可运行。

---

*报告生成于 2026-05-24 | 分析员: Claude Sonnet 4.6 代码深读 Agent*
