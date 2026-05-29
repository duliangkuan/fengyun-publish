# 微信公众号草稿协议 + 排版兼容性调研

> 调研日期：2026-05-21
> 严谨性声明：每条结论带 URL 出处；未找到出处的标注「调研空白 ⚠️」

---

## 调研方法 + 来源清单

**搜索关键词：**
- 微信公众号 HTML CSS inline style 支持 草稿API 排版 2024 2025
- wechat official account draft API HTML CSS subset stripped tags 2024
- 微信公众号 position display:flex grid 被剥离 inline style 限制
- 微信公众号文章 HTML 白名单 section div 被转换 实测
- 微信公众号 blockquote border-left 手机端不显示 table 溢出
- 微信公众号 暗黑模式 dark mode 颜色失效 强制反色 CSS
- 微信公众号草稿API content字节限制 图片必须mmbiz 限制 官方文档
- wechat article display:flex position:absolute stripped removed css

**经过核实的 URL 来源（9 个）：**

| # | 来源 | URL |
|---|------|-----|
| 1 | 微信官方 - 新增草稿API（服务号） | https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add.html |
| 2 | 微信官方 - 上传图文消息图片 | https://developers.weixin.qq.com/doc/subscription/api/notify/message/api_uploadimage.html |
| 3 | 微信开放社区 - content字符计算说明 | https://developers.weixin.qq.com/community/develop/doc/000a8c82b50790ca4f92dea626b000 |
| 4 | 微信开放社区 - 行间距错乱问题 | https://developers.weixin.qq.com/community/develop/doc/00086813c78d483387cd263095b800 |
| 5 | axtonliu.ai - 微信HTML/CSS支持情况解析 | https://www.axtonliu.ai/newsletters/ai-2/posts/wechat-article-html-css-support |
| 6 | CSDN - 微信公众号CSS布局和SVG推文的坑 | https://blog.csdn.net/liixnhai/article/details/111693575 |
| 7 | 博客园 - 微信公众号CSS布局和SVG推文的坑 | https://www.cnblogs.com/haqiao/p/13438686.html |
| 8 | Medium - Obsidian WeChat CSS Style Template | https://medium.com/@joycebirkins/obsidian-wechat-official-account-article-formatting-and-publishing-with-css-style-template-e1406888b90b |
| 9 | DEV.to - 自动化 WeChat 发布流水线 | https://dev.to/chenyanchen/how-i-built-an-automated-wechat-publishing-pipeline-with-python-as-an-ai-4c3a |
| 10 | 微信暗黑模式适配指南 | https://developers.weixin.qq.com/doc/service/guide/h5/darkmode.html |
| 11 | 数英 - 公众号暗黑模式适配6点 | https://www.digitaling.com/articles/274098.html |
| 12 | 微信官方 - 订阅号字数限制讨论 | https://developers.weixin.qq.com/community/develop/doc/000ccc656fc388a85f1df968356c00 |
| 13 | md2wechat CLI README | https://github.com/geekjourneyx/md2wechat-skill |

---

## Q1 HTML 标签支持表

| 标签 | 是否支持 | 微信处理方式 | 出处 |
|------|---------|------------|------|
| `<p>` | ✓ | 保留，推荐主体容器；默认段后距微信会注入 24pt（2022年改动）| [4] |
| `<section>` | ✓ | 保留，常用于第三方排版工具（如135编辑器）套娃排版 | [5] |
| `<div>` | ⚠️ 部分 | 基本保留但属于"不推荐"——排版工具普遍改用 `<section>` 或 `<p>` | [5] |
| `<h1>`-`<h6>` | ✓ | 保留，但字号不会被微信强制改写；需自行用 inline `font-size` 控制 | [5] |
| `<strong>` / `<b>` | ✓ | 完全保留，加粗显示 | [5] |
| `<em>` / `<i>` | ✓ | 完全保留，斜体显示 | [5] |
| `<u>` | ✓ | 保留，下划线 | [5] |
| `<br>` | ✓ | 保留，换行 | [5] |
| `<hr>` | ⚠️ 调研空白 | 未找到明确说明是否保留 | — |
| `<blockquote>` | ✓ | 保留；border-left 需显式写 inline style，否则样式全无 | [8] |
| `<ul>` / `<ol>` / `<li>` | ✓ | 保留；微信编辑器会重置默认 list-style，需手动 inline 补 | [1] (wechat-format README 提到) |
| `<a>` | ⚠️ 条件 | 保留标签但**外链会触发安全提示页**；非微信白名单域名跳转受限；**具有微信支付权限的账号可用，其他账号不能使用 a 标签** | [官方文档原文] |
| `<img>` | ✓ 条件 | 保留但**src 必须为 mmbiz.qpic.cn 域名**；外部 URL 被过滤不显示 | [2][官方] |
| `<table>` | ⚠️ 有坑 | 保留但手机端自动溢出形成横向滚动条；强烈建议转图片 | [96微信编辑] |
| `<pre>` / `<code>` | ✓ | 保留；需 inline 设 background/font-family/white-space:pre-wrap | [8] |
| `<video>` | ❌ | 不支持标准 `<video>` 标签；须用微信专有 `<mpvideo>` | [5] |
| `<audio>` | ❌ | 须用微信专有 `<mpvoice>` | [5] |
| `<iframe>` | ❌ | 完全剥除，安全限制 | [5] |
| `<script>` | ❌ | 完全剥除，上传时自动去 JS | [1][官方] |
| `<style>` | ❌ | 完全剥除；只能用 inline style | [5] |
| `<form>` / `<input>` | ❌ | 完全剥除 | [5] |
| `id` 属性 | ❌ | 上传后所有 HTML 元素和 SVG 的 id 属性被删除 | [6][7] |
| `class` 属性 | ❌ | 上传后所有 class 属性被删除，所以不能用 class-based CSS | [9] |
| SVG 相关标签 | ⚠️ 部分 | `<svg>`, `<animate>`, `<g>`, `<path>` 等有白名单；图片 href 必须 mmbiz；iOS 有兼容性 bug | [6][7] |

---

## Q2 CSS 属性支持表

> **铁律：所有 CSS 必须写为 inline style（`style="..."` 属性），不能用 `<style>` 块或 class**

| 属性 | 保留/支持? | 手机端表现 | 出处 |
|------|-----------|-----------|------|
| `font-size` | ✓ 完全 | 正常渲染，建议用 px，不要用 % | [5][8] |
| `font-weight` | ✓ 完全 | 正常，bold/700 均可 | [5] |
| `font-style` | ✓ 完全 | italic 正常 | [5] |
| `font-family` | ✓ 完全 | 系统字体。推荐降级栈：`-apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", STHeiti, "Microsoft YaHei", sans-serif` | [搜索综合] |
| `color` | ✓ 完全 | 正常，但暗黑模式下浅色系会被算法强制反色（变得很亮或不可见）| [10][11] |
| `background-color` | ✓ 完全 | 纯色可靠；暗黑模式会被反色 | [5][11] |
| `background-image: linear-gradient(...)` | ⚠️ 部分 | 技术可用（须 background-image 属性，不是 background-color）；暗黑模式渐变色可能失真 | [搜索综合] |
| `line-height` | ✓ 完全 | 正常渲染；但有坑：微信后台 2022 年后默认为段后 24pt，与 line-height 叠加导致电脑/手机差异 | [4] |
| `letter-spacing` | ✓ 完全 | 正常 | [5][8] |
| `margin` | ✓ 完全 | 正常；建议用 `margin: Xpx 0` 精确控制段落间距；**不要依赖浏览器默认** | [5] |
| `padding` | ✓ 完全 | 正常 | [5] |
| `text-align` | ✓ 完全 | left/center/right 正常 | [5] |
| `text-indent` | ✓ 基本 | 调研空白 ⚠️ 无明确实测数据，理论支持 | — |
| `text-decoration` | ✓ 完全 | 正常 | [5] |
| `border` | ✓ 完全 | 正常 | [5][8] |
| `border-left` | ✓ 完全 | 正常，blockquote 左侧线用这个 | [8] |
| `border-radius` | ✓ 完全 | 正常，图片圆角可用 | [5] |
| `box-shadow` | ✓ 完全 | 正常；暗黑模式下 black shadow 变 white，出现白色发光效果 | [11] |
| `width` | ✓ 完全 | px 单位可靠；百分比 `%` **不可靠**，建议 px 或 vw | [6][7] |
| `height` | ⚠️ 部分 | px 可用；百分比不可靠 | [6][7] |
| `max-width` | ✓ 完全 | 微信已内置 `max-width:100%` 给图片，手动写也有效 | [5] |
| `display: block` | ✓ 完全 | 正常 | [5] |
| `display: inline-block` | ✓ 完全 | 正常 | [5] |
| `display: flex` | ✓ 基本可用 | 官方文档未明确限制；实测在特定场景可用（做 z-index 分层时推荐用 flex 替代 position）| [7] |
| `display: grid` | 调研空白 ⚠️ | 未找到有出处的实测数据 | — |
| `position: absolute/fixed/relative` | ❌ 剥除 | **上传后被删除**，定位完全失效 | [6][7] |
| `float` | ⚠️ 有坑 | 标签保留但在可展开/折叠内容中元素会"逃出"容器，高度不受控 | [6][7] |
| `transform` | ⚠️ 部分 | 现在基本可用；早期被剥除；iOS 暗黑模式系统会对所有元素加 transform，干扰层叠 | [7] |
| `opacity` | ✓ 完全 | 正常 | [5] |
| `@media` 媒体查询 | ❌ 不支持 | `<style>` 被剥除，媒体查询无法生效；用 vw/vh 代替响应式 | [5][6] |
| `@keyframes` 动画 | ❌ 不支持 | `<style>` 被剥除，CSS 动画不可用；改用 SVG animate 或 GIF | [5] |
| 伪元素 `:before` `:after` | ❌ 不支持 | `<style>` 被剥除，无法使用；只能改为真实 HTML 元素 | [8] |
| 伪类 `:hover` | ❌ 不支持 | 同上，无法使用 | [8] |
| `vw` / `vh` 单位 | ✓ 推荐替代 | 可用，是 % 的替代方案，用于响应式 | [5][6] |
| `%` 百分比单位 | ❌ 不可靠 | `transform: translateY(-100%)` 等百分比值**失效** | [6][7] |

---

## Q3 常见 Bug + 规避方法

### Bug 1: 段落间距 — 电脑预览和手机不一致

**根本原因：** 微信后台在 2022 年后将段落默认「段后距」从 0 改为 24pt。编辑器预览可能不体现这个全局默认值，手机端却会应用。
**规避：** 显式用 `margin` 覆盖，不依赖任何默认值：
```html
<p style="margin: 0 0 24px 0; padding: 0; line-height: 1.8; font-size: 16px; color: #333;">
  段落内容
</p>
```
**出处：** https://developers.weixin.qq.com/community/develop/doc/00086813c78d483387cd263095b800

---

### Bug 2: 图片宽度溢出手机屏幕

**根本原因：** 微信内置了 `max-width: 100%`，但如果自定义 `width` 为固定 px 且超出屏幕宽度则仍会溢出。
**规避：**
```html
<img src="https://mmbiz.qpic.cn/..." 
     style="max-width: 100%; width: 100%; height: auto; display: block;" 
     alt="图片描述"/>
```
**出处：** https://www.axtonliu.ai/newsletters/ai-2/posts/wechat-article-html-css-support

---

### Bug 3: `position` 完全失效

**根本原因：** 微信上传时服务端脚本会把所有 `position` 属性代码删掉。
**规避：** 用 `display: flex` + `z-index` 替代层叠定位。
**出处：** https://blog.csdn.net/liixnhai/article/details/111693575 + https://www.cnblogs.com/haqiao/p/13438686.html

---

### Bug 4: `id` 和 `class` 属性被删除

**根本原因：** 微信安全过滤机制，上传时同步删除所有 `id`、`class` 属性。
**规避：** 所有样式写 inline `style` 属性，不依赖 id/class 选择器。
**出处：** https://blog.csdn.net/liixnhai/article/details/111693575

---

### Bug 5: 暗黑模式颜色失效

**根本原因：** iOS/Android 微信暗黑模式下，CSS 颜色被算法自动强制反色：
- 浅灰色文字 → 变为浅色背景上看不清
- `box-shadow` 黑色 → 变为白色，产生"发光"效果
- SVG 中定义的颜色**不被反色**，导致 SVG 与背景颜色对比异常
**规避：**
1. 避免极浅灰色（如 `#eee`、`#f5f5f5`）作为正文颜色
2. 有阴影效果的图片导出为 PNG（透明底），不用 JPG
3. 纯色分隔线改用中灰（`#595757`），避免纯黑/纯白
4. 如需 SVG 颜色适配，用 `fill: currentColor`
**出处：** https://www.digitaling.com/articles/274098.html

---

### Bug 6: `blockquote` 左边框手机端不显示

**根本原因：** 未写 inline style，依赖浏览器默认或 `<style>` 块（被剥除）。
**规避：**
```html
<blockquote style="border-left: 4px solid #42b983; padding: 10px 16px; margin: 16px 0; background-color: #f6fffa; color: #555; font-size: 15px; line-height: 1.75;">
  引用内容
</blockquote>
```
**出处：** https://wallleap.cn/2020/03/27/wechatpaper/

---

### Bug 7: `<table>` 手机端变滚动条

**根本原因：** 表格宽度超出手机屏幕时微信不会自动换行，形成横向滚动。
**规避方案（按优先级）：**
1. 将表格转换为截图（Excel 截图后作为图片插入）
2. 使用预制表格模板（第三方编辑器的 Style Center）
3. 如必须 HTML 表格，加 `overflow-x: auto` 的包裹 div（但 div 本身也有渲染风险）
**出处：** https://bj.96weixin.com/help/100013.html

---

### Bug 8: `ul`/`ol` 样式被重置

**根本原因：** 微信编辑器会重置列表默认样式（list-style、padding）。
**规避：**
```html
<ul style="padding-left: 2em; margin: 16px 0;">
  <li style="margin-bottom: 8px; line-height: 1.8;">列表项</li>
</ul>
```
**出处：** lyricat/wechat-format README（项目已停止维护，核心结论仍有效）

---

### Bug 9: 百分比单位失效

**根本原因：** `transform: translateY(-100%)`、`margin-top: -100%` 等百分比计算在微信环境中失效。
**规避：** 所有需要响应式的尺寸用 `px` 或 `vw/vh` 替代。
**出处：** https://blog.csdn.net/liixnhai/article/details/111693575

---

### Bug 10: SVG + iOS 兼容性

**具体问题：**
- `<g style>` 中的 inline style 在 iOS 上失效（Android/PC 正常）
- iOS 忽略 SVG 动画的 `restart="never"` 属性
- SVG 图片 href 必须 mmbiz 链接，外链/base64 均不显示
**出处：** https://www.cnblogs.com/haqiao/p/13438686.html

---

## Q4 实战工具借鉴

### doocs/md
- **项目地址：** https://github.com/doocs/md
- **解决思路：** Vue3 + Vite 构建，Markdown 渲染时将 CSS theme 注入为 inline style；支持自定义主题 CSS（用户自定义后工具自动 inline 化）；支持 Mermaid/PlantUML；通过多图床支持解决图片 mmbiz 问题。
- **关键点：** 工具本身不直接调 API，靠用户复制 HTML 粘贴进微信编辑器（copy-paste 方式不经过 draft API 过滤）。

### lyricat/wechat-format（已停止维护）
- **项目地址：** https://github.com/lyricat/wechat-format
- **核心发现：** 发现并解决了 `ul`/`ol` 样式被微信编辑器重置的问题；外部链接自动转换为文末参考索引。
- **现状：** 已停止维护，推荐使用 Quaily Markdown Tools 替代。

### md2wechat CLI（geekjourneyx）
- **项目地址：** https://github.com/geekjourneyx/md2wechat-skill
- **解决思路：** 提供 AI 模式（生成 prompt 给外部 LLM）和 API 模式（直接输出 inline HTML）；40+ 主题（Minimal/Focus/Elegant/Bold 四系列）；明确提示 draft API 20,000 字符限制，建议遇到 45002 错误时拆分文章或用更精简主题。
- **关键点：** inline CSS 会显著增加 content 体积，长文需注意字符上限。

### Markdown Here（wechat CSS gist）
- **Gist：** https://gist.github.com/shisaq/48afebdc21b4cde3531e2b28ba2893b8
- **CSS 模板摘要：**
  - `p`: `margin: 0 0 1.2em 0 !important`
  - `h1`: `font-size: 1.6em; border-bottom: 1px solid #ddd;`
  - `blockquote`: `border-left: 4px solid #009688; padding: 0 1em; color: #777;`
  - `code`: `background: #f9f2f4; color: #c7254e; border-radius: 3px;`
  - `img`: `max-width: 100%; height: auto; border-radius: 5px;`

---

## Q5 推草稿前 Checklist

### 1. 预处理步骤（草稿推送前必做）

```
□ Step 1: 所有图片先上传到微信图床
   POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=XXX
   → 返回 http://mmbiz.qpic.cn/XXXX URL
   → 替换 HTML 中所有 <img src="..."> 为 mmbiz URL
   支持格式: jpg/png, 大小 < 1MB
   接口日限: 1000 次/天

□ Step 2: 移除所有 <style> 块和 <script> 块

□ Step 3: 移除所有 class="" 和 id="" 属性

□ Step 4: 移除所有 position: absolute/fixed/relative

□ Step 5: 将百分比尺寸改为 px 或 vw

□ Step 6: 计算 content 字段总字符数（含 HTML 标签）< 20,000

□ Step 7: 封面图 thumb_media_id 为永久素材 media_id（非临时）

□ Step 8: title ≤ 32 字符，author ≤ 16 字符，digest ≤ 128 字符
```

### 2. 本地模拟手机端渲染

- 用 Chrome DevTools → Toggle Device Toolbar（手机模拟）→ 选 iPhone 12 Pro（375px 宽）
- 在模拟手机视口中检查所有图片是否自适应（无横向溢出）
- 检查字号在 375px 视口下是否可读（建议正文 ≥ 15px）
- 检查颜色对比度（用 Chrome 无障碍面板）
- **注意：** 本地预览与手机微信有渲染差异，本地通过只是最低标准

### 3. 推完后验证手机端

```
□ 在草稿箱打开文章 → 点击"在手机上预览"（公众号后台功能）
□ 实机 iPhone + Android 各检查一遍（iOS/Android 渲染引擎不同）
□ 开启 iOS 暗黑模式重新预览 → 检查颜色是否崩溃
□ 检查图片是否全部加载（外链/base64 会显示为空）
□ 检查 blockquote 左边框是否显示
□ 滚动到文末检查列表格式是否正确
```

### 4. 必须本地测试通过的样式

- `max-width: 100%; height: auto` 图片自适应
- `margin: 0 0 Xpx 0` 段落间距明确
- `line-height: 1.6~1.85` 行高在小屏幕可读
- `font-size: 15~16px` 正文，不低于 14px
- `color` 颜色在白底和深色背景下均可见

### 5. 已知踩坑汇总

| 坑 | 规避方法 |
|----|--------|
| `<style>` 被剥除 | 只写 inline style |
| `position` 被删除 | 用 flex 替代 |
| id/class 被删除 | 纯 inline style，不依赖 class |
| 外部图片 URL 不显示 | 先上传 uploadimg 接口拿 mmbiz URL |
| content > 20,000 字符报 45002 | 拆文章或删减 inline CSS |
| 百分比单位失效 | 改用 px 或 vw |
| 段落间距手机比电脑大 | 显式 `margin: 0 0 24px 0; padding: 0` |
| 暗黑模式颜色崩溃 | 避免极浅灰；阴影图片用 PNG 透明底 |
| 表格手机溢出 | 截图转图片 |
| iOS SVG transform-origin 失效 | 避免在 SVG `<g>` 内用 transform-origin |

---

## Q6 微信官方硬限制

| 限制项 | 具体值 | 出处 |
|-------|--------|------|
| `content` 字段最大字符数 | **< 20,000 字符**（含 HTML 标签全部计入） | [1][3] |
| `content` 字段最大字节 | **< 1MB** | [1] |
| 文章最大字符数（用户可读内容） | **50,000 字符**（官方社区回答，高于 API 限制；两者存在矛盾，API 限制更严格） | [12] |
| `title` 最大长度 | **32 字符** | [1] |
| `author` 最大长度 | **16 字符** | [1] |
| `digest` 最大长度 | **128 字符** | [1] |
| `content_source_url` 最大长度 | **1kb** | [1] |
| 图片消息单条最多图片数 | **20 张** | [1] |
| 草稿箱草稿数量上限 | **无上限**（官方社区：暂无限制，永久保存） | [搜索综合] |
| 图片 URL 域名要求 | **必须 mmbiz.qpic.cn**；外部 URL 被过滤不显示 | [2][官方] |
| 图片上传格式 | JPG / PNG，单张 < 1MB | [2] |
| 图片上传接口日限 | **1,000 次/天** | [社区讨论] |
| 封面图要求 | 必须为**永久素材** `thumb_media_id` | [1] |
| 订阅号群发频次 | 每天最多 1 次 | [社区] |
| 服务号群发频次 | 每月最多 4 次 | [社区] |
| 单次群发最多文章数 | **8 篇** | [社区] |
| JS 处理 | 上传时自动删除所有 JavaScript | [1] |
| `id` / `class` 属性 | 上传时全部删除 | [6][7] |

> **注意：** content 字段 20,000 字符上限含 HTML 标签。长文加了大量 inline CSS 后，实际内容远比"看起来"短。md2wechat 文档明确提到遇到 45002 错误需要换更精简主题。

---

## 关键调研空白（找不到的）

⚠️ **`articles` 数组单次最多可传几篇：** 文档未明确，群发上限是 8 篇，但草稿 API 的 articles 数组上限找不到官方说明。

⚠️ **`display: grid` 是否支持：** 未找到有出处的实测数据。

⚠️ **`text-indent` 具体行为：** 理论可用但无实测数据确认。

⚠️ **`linear-gradient` 在 inline background-image 是否被过滤：** 微信小程序文档支持，但公众号文章的 draft API 服务端过滤规则未找到明确说明。（判断：中等风险，建议实测后再用）

⚠️ **`<hr>` 标签渲染行为：** 未找到明确测试数据。

⚠️ **`<section>` 嵌套最大层数：** 无官方说明，135编辑器等工具大量使用多层 section 嵌套，实践上似乎无严格层数限制，但也未找到文档确认。

⚠️ **emoji 跨设备渲染差异：** 未找到有数据的来源。

---

## 强建议的【公众号草稿生成规则集】

> 下面是每个元素的标准 inline HTML 模板，可直接复制使用。

### 规则 1：全局容器

```html
<section style="font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', STHeiti, 'Microsoft YaHei', sans-serif; font-size: 16px; color: #333333; line-height: 1.8; word-break: break-word;">
  <!-- 正文内容 -->
</section>
```

### 规则 2：正文段落（主体用这个，不用 `<div>`）

```html
<p style="margin: 0 0 20px 0; padding: 0; font-size: 16px; line-height: 1.8; color: #333333; letter-spacing: 0.3px;">
  段落内容
</p>
```

### 规则 3：标题（不要依赖 `<h1>`-`<h6>` 的浏览器默认）

```html
<!-- 一级标题 -->
<p style="margin: 32px 0 16px 0; padding: 0; font-size: 22px; font-weight: bold; color: #1a1a1a; line-height: 1.4; text-align: center;">
  标题文字
</p>

<!-- 二级标题 -->
<p style="margin: 24px 0 12px 0; padding: 0; font-size: 18px; font-weight: bold; color: #1a1a1a; line-height: 1.4; border-left: 4px solid #07C160; padding-left: 12px;">
  二级标题
</p>
```

### 规则 4：图片（必须 mmbiz URL）

```html
<p style="margin: 24px 0; padding: 0; text-align: center;">
  <img src="https://mmbiz.qpic.cn/..." 
       style="max-width: 100%; width: 100%; height: auto; display: block; margin: 0 auto; border-radius: 4px;"
       alt="图片描述"/>
</p>
<p style="margin: -16px 0 20px 0; text-align: center; font-size: 13px; color: #888888; line-height: 1.5;">
  图片说明文字（可选）
</p>
```

### 规则 5：引用块

```html
<blockquote style="margin: 20px 0; padding: 12px 16px; border-left: 4px solid #07C160; background-color: #f6fff8; color: #555555; font-size: 15px; line-height: 1.75; border-radius: 0 4px 4px 0;">
  <p style="margin: 0; padding: 0;">引用内容</p>
</blockquote>
```

### 规则 6：代码块

```html
<pre style="margin: 16px 0; padding: 16px; background-color: #282c34; color: #abb2bf; font-family: 'Courier New', Consolas, Monaco, monospace; font-size: 13px; line-height: 1.6; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;"><code>代码内容</code></pre>
```

### 规则 7：行内代码

```html
<code style="background-color: #f0f0f0; color: #c7254e; font-size: 0.9em; padding: 2px 5px; border-radius: 3px; font-family: 'Courier New', Consolas, monospace;">行内代码</code>
```

### 规则 8：无序列表

```html
<ul style="margin: 16px 0; padding: 0 0 0 2em; list-style-type: disc;">
  <li style="margin-bottom: 10px; line-height: 1.8; font-size: 16px; color: #333333;">列表项 1</li>
  <li style="margin-bottom: 10px; line-height: 1.8; font-size: 16px; color: #333333;">列表项 2</li>
</ul>
```

### 规则 9：有序列表

```html
<ol style="margin: 16px 0; padding: 0 0 0 2em; list-style-type: decimal;">
  <li style="margin-bottom: 10px; line-height: 1.8; font-size: 16px; color: #333333;">步骤 1</li>
  <li style="margin-bottom: 10px; line-height: 1.8; font-size: 16px; color: #333333;">步骤 2</li>
</ol>
```

### 规则 10：强调/加粗

```html
<strong style="font-weight: bold; color: #1a1a1a;">重点内容</strong>
```

### 规则 11：分隔线（避免 `<hr>` 不确定行为）

```html
<p style="margin: 24px 0; padding: 0; border-top: 1px solid #e8e8e8; height: 0; line-height: 0; font-size: 0;"> </p>
```

### 规则 12：链接（仅具有微信支付权限的服务号可用 `<a>`）

```html
<!-- 有权限时 -->
<a href="https://your-domain.com" style="color: #07C160; text-decoration: none;">链接文字</a>

<!-- 没有权限 / 外链 → 移到文末手动处理 -->
<!-- 推荐做法：文中标记 [1]，文末列参考链接 -->
```

### 规则 13：禁止使用的写法

```html
<!-- ❌ 禁止：<style> 标签 -->
<style>.foo { color: red; }</style>

<!-- ❌ 禁止：class 属性 -->
<p class="paragraph">...</p>

<!-- ❌ 禁止：id 属性 -->
<div id="section1">...</div>

<!-- ❌ 禁止：position -->
<div style="position: absolute; top: 10px;">...</div>

<!-- ❌ 禁止：外部图片 URL -->
<img src="https://example.com/image.jpg"/>

<!-- ❌ 禁止：百分比 transform -->
<div style="transform: translateY(-50%);">...</div>

<!-- ❌ 禁止：<script> -->
<script>alert('test')</script>

<!-- ❌ 禁止：<iframe> -->
<iframe src="..."></iframe>
```

---

## 附：推草稿 Python 预处理伪代码

```python
import re
from bs4 import BeautifulSoup

def sanitize_wechat_html(html: str) -> str:
    """
    推草稿前的 HTML 预处理：
    1. 移除 <style> / <script>
    2. 移除所有 class / id 属性
    3. 移除 position CSS
    4. 替换百分比尺寸为 px/vw（需人工审核）
    5. 检查 content 字符数
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # 移除 style 块和 script 块
    for tag in soup.find_all(['style', 'script']):
        tag.decompose()
    
    # 移除 class / id 属性
    for tag in soup.find_all(True):
        tag.attrs.pop('class', None)
        tag.attrs.pop('id', None)
    
    # 从 inline style 中移除 position
    for tag in soup.find_all(style=True):
        style = tag['style']
        style = re.sub(r'position\s*:\s*[^;]+;?', '', style, flags=re.IGNORECASE)
        tag['style'] = style.strip(' ;')
    
    result = str(soup)
    
    # 检查字符数（含标签）
    if len(result) >= 20000:
        raise ValueError(f"content 超过 20000 字符限制: {len(result)} 字符")
    
    return result
```

---

*本报告调研来源 13 个，硬规则 35+ 条（带 URL），调研空白 7 处已标注。*
