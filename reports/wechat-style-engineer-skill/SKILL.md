---
name: wechat-style-engineer
description: 微信公众号渲染细节 debug 主题 skill。当用户 debug 公众号样式(图片上下间距不对称 / 桌面与手机表现差异 / inline style 陷阱 / 字号被强制 floor / 元素 margin 翻倍)时使用。也适用于:用户在改 markdown-to-html 渲染器、修 huashu/khazix 等排版模板里的 layout bug、定位「编辑器里看正常但真机不正常」的诡异现象。**这不是 writer skill,是 reviewer + debugger**。触发词:「微信公众号 debug 样式」「图片间距问题」「公众号渲染异常」「图上下不对称」「inline style 不 collapse」「桌面与手机不一致」「margin 翻倍」。
---

# wechat-style-engineer

微信公众号样式细节工程化排查 skill。

## 触发场景

- 修微信公众号 HTML 渲染器(layout_rules.py / md2wechat / wenyan / baoyu / huashu-md-html 类)的 layout bug
- 排查「桌面编辑器看正常但手机真机不正常」的诡异现象
- 图片、blockquote、code block 上下间距不对称
- 字号在手机被强制放大或缩小
- inline style 行为反直觉(改了一个 margin 整体布局塌掉)
- 长按图片点不开、复制失败等 img attribute 相关 UX 问题

## 不触发

- 写文章(用 khazix-writer / fengyun-writer)
- 评判文章灵魂(用 huashu-perspective)
- 生成封面图(用 baoyu-cover-image)
- 普通 CSS 调试(本 skill 专攻微信 webview 特殊性)

---

## 一、核心方法论:5 个微信公众号样式 debug 铁律

### 铁律 1 ⭐⭐⭐:inline style 让 margin collapse 失效

**这是公众号样式 debug 的第一坑。**

W3C 规范说垂直相邻的块级元素的 margin 会 collapse 取最大值,但**仅当 margin 是从外部 CSS 文件来时**。当 margin 写在 inline `style=""` 上,**两个相邻元素的 margin 会相加,不 collapse**。

微信公众号编辑器把所有外部 `<style>` 标签和 class 剥光,**只允许 inline style 通过**,所以我们写的 markdown-to-html 输出全踩在这个坑里。

**症状**:H1.margin-bottom = 20px + figure.margin-top = 20px,期待 20px,实际 40px。下方同理 → 「上 20 下 40」感觉就是图下方多一倍。

**修法**:
- 优先用 padding(不参与 collapse 但也不参与外部加和)
- 实在要 margin,只写一侧(`margin-bottom` 或 `margin-top` 二选一)
- 避免 `margin: X 0` 这种上下双开口

详见 `references/research/01-opensource-image-handling.md` §3。

---

### 铁律 2 ⭐⭐:桌面 vs 手机必须分离调试

公众号编辑器 PC 预览 ≠ 真机。三件事让两个环境永远不一样:

1. **字号 floor**:Android 微信 webview 强制把正文 `<p>` 字号 floor 到 16px,desktop 不 floor
2. **viewport**:微信真机强制 `viewport content="width=375"`(iOS)/ `width=360`(Android),desktop 编辑器 800+
3. **DPI**:iOS Retina 3x / Android 2.5-3x,1px 边界在 3x 上放大 3 倍

**症状**:同一份 HTML 在公众号编辑器 PC 看完美对称,微信 App 真机看图下方多 10-15px。

**修法**:
- debug 时必须**真机推草稿看**,不要只信编辑器预览
- desktop 编辑器只用来跑 lint / 字节级 diff,不当视觉权威
- 测试 cycle:推草稿 → 微信扫码看草稿 → 截图对比

详见 `references/research/02-wechat-internals.md` §六。

---

### 铁律 3 ⭐:真品对照法(byte-level diff)

任何「我以为微信图片应该……」的假设都要先打开真品文章 devtools 检查。本项目 `D:\Dev\ai-wechat-pipeline\corpus\benchmark-articles\` 存了卡兹克、花叔、宝玉、风云历史推文的真品 HTML dump。

**操作流程**:
1. 在草稿状态打开真品文章,菜单「复制链接」获得 mp.weixin.qq.com URL
2. desktop Chrome 打开 → F12 → Elements → 找到 img / figure / blockquote DOM
3. **盯着真品 inline style 一个字符一个字符抄**,不要相信「应该是这样」的归纳

**反例(v6-v9 的 4 次盲推)**:都基于「我猜 figure 应该 ...」,没看真品。结果绕了 4 圈才搞清楚是 inline margin collapse 问题。

---

### 铁律 4:微信 img 必有 5 个 attribute

```html
<img class="rich_pages wxw-img"      <!-- 客户端必填,微信前端 hook 点击放大 -->
     src="https://mmbiz.qpic.cn/..."  <!-- 客户端必填 -->
     data-src="..."                   <!-- 服务端补 -->
     data-imgfileid="..."             <!-- 服务端补 -->
     data-type="jpeg"                 <!-- 服务端补 -->
     data-aistatus="0" />             <!-- 服务端补 -->
```

**客户端只要写 `class="rich_pages wxw-img"` 和 `src`**,其余 4 个微信 `draft/add` API 服务端会自动注入。

**反例**:v6-v9 中有版本添加 `data-src=""`,以为是 lazy load 必须 — 其实白写,服务端会 overwrite。

详见 `references/research/02-wechat-internals.md` §四。

---

### 铁律 5:5 步 debug checklist

遇到图片 / 块元素间距 bug,按顺序排查:

1. **查 img 的 `display`**:微信 webview 里 img 默认 `display: inline`,会有 baseline 留白。改成 `display: block` 消除
2. **查父容器 `line-height` 是否被 figure/p 覆盖**:父 `<section>` 的 line-height 1.8 会通过 inheritance 影响子元素 inline content,figure 内最好显式 `line-height: 0`(防御性)
3. **查 inline margin 是否双侧**:`margin: X 0` 一侧跟相邻 H1 的 margin-bottom 不 collapse 翻倍,另一侧跟相邻 p 的 margin-top 不 collapse 翻倍 → 改 padding 或单侧 margin
4. **查微信必有 attribute 是否齐全**:img 必有 `class="rich_pages wxw-img"`,否则点击放大功能失效
5. **真品 byte-level diff**:出 HTML → 跟 corpus 真品 inline style 字符级对比,任何差异都先怀疑自己

---

## 二、本 skill 调研来源

完整调研报告:

- `references/research/01-opensource-image-handling.md` — Agent A:深读 wenyan / baoyu / huashu-md-html 三家开源工具,挖出 inline margin collapse 失效的核心机制
- `references/research/02-wechat-internals.md` — Agent B:从微信 webview 内核切入,实证 img attribute / 字号 floor / DPI / viewport,反向证否 Agent B 自己的 strut 假设,确认 Agent A 的 inline-margin 假设是真因

---

## 三、本 skill 的反 over-engineer 提醒

- 不要堆 attribute(`data-src` `data-imgfileid` 都是服务端补,客户端写了白写)
- 不要堆 CSS reset(每加一条 inline 都增加 collapse 表面积)
- 不要在桌面编辑器调对称就 ship(必须真机看)
- 不要凭直觉改 figure / section / div / p 五选一,先看真品

---

## 四、本项目内的应用案例

- huashu 排版图片间距 bug(v6→v10,2026-05-24)
- 修改对象:`D:\Dev\ai-wechat-pipeline\tools\layout_rules.py` `_huashu_wrap_img`(line 882+)
- 最终修法:`figure margin: 0 + padding: 24px 0` + `img margin: 0 auto`(铁律 1 方案 3)
- v10 即采用本 skill 蒸馏完成后的方案
