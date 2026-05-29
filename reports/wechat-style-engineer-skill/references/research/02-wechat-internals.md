# 调研报告 02:微信公众号 inline HTML 标准 + 真品 img attribute 实证

**调研日期**:2026-05-24
**调研人**:Sonnet sub-agent B
**调研对象**:微信公众号 webview 渲染管线 / img attribute / line-height 行为
**调研动机**:huashu 图片间距 bug,Agent A 从 margin collapse 角度切入,Agent B 从微信 webview 内核角度切入互验

---

## 一、调研边界

Agent A 在 markdown-to-html 转换层调研,本报告从**微信 webview 渲染层**切入:
- 微信 iOS WKWebView / Android Chromium 内核版本
- 公众号编辑器对 input HTML 的 sanitize 策略
- 图片 lazy load / placeholder 机制
- inline style 在不同设备的渲染差异

---

## 二、微信 webview 内核版本

| 平台 | 内核 | 关键差异 |
|---|---|---|
| iOS 微信 | WKWebView(Safari 内核) | 严格遵守 W3C,但 inline style 有自己的优化 |
| Android 微信 | XWalk → 现在已切换 Chromium(基于 X5,2025 已升 Chrome 110+) | margin collapse 行为跟桌面 Chrome 接近,但有「字号自动 16px floor」 |
| 公众号编辑器(PC) | Chrome embedded | 几乎跟桌面 Chrome 一致,**所以 desktop 看着对称** |
| 公众号编辑器(预览模式手机) | 模拟器,但不完全等同于真机 | 这是 v6-v9 调试时一直在用的环境,误导性大 |

**核心 takeaway**:**只看 PC 编辑器预览** 等于在 Chrome 模式,看不到 Android/iOS 真机的差异。bug 在真机才出现。

---

## 三、关键发现 ❌:data-src lazy load 假设是错的

### 3.1 原假设

我们之前假设:
- 微信图片必须带 `data-src`,真正的 `src` 是 placeholder
- 当图片入视口时,微信前端 JS 把 `data-src` 拷贝到 `src`,触发加载
- 推测如果不写 `data-src`,图片会卡在 placeholder,产生额外占位高度

### 3.2 实际验证

打开真品文章 devtools 看 img DOM:

```html
<img class="rich_pages wxw-img"
     data-src="https://mmbiz.qpic.cn/mmbiz_jpg/.../640"
     data-imgfileid="100000123"
     data-type="jpeg"
     data-aistatus="0"
     src="https://mmbiz.qpic.cn/mmbiz_jpg/.../640?wx_fmt=jpeg" />
```

**关键观察**:
- `src` 和 `data-src` **同时存在**且指向同一资源
- 图片在 DOM 渲染时**直接用 src 加载**,不依赖 data-src
- data-src 是微信前端 lazy load 机制的备份字段,但**src 存在时优先用 src**

### 3.3 微信 draft/add API 行为

抓包 `cgi-bin/draftadd`:
- POST 时 content 字段就是我们传的 HTML
- 微信服务端入库时给所有 img **自动加** `data-src` / `data-imgfileid` / `data-type` / `data-aistatus`
- 我们传 `<img src="..." />` 完全够用,**多写 data-src 也只会被 overwrite**

**结论**:lazy load 假设不成立,data-src 不是图片间距 bug 的因。

---

## 四、微信图片必有 5 个 attribute 清单(实证)

虽然不是间距 bug 的因,但**对其它问题有用**(例如图片在公众号 App 内无法点开看大图、图片不能复制等),记录在此:

| attribute | 必填 | 服务端是否自动加 | 含义 |
|---|---|---|---|
| `src` | ✅ 客户端必填 | 否(我们提供) | 实际加载 URL |
| `class="rich_pages wxw-img"` | ✅ 客户端建议加 | 否 | 微信公众号前端 hook 这个 class 做点击放大、长按保存等 |
| `data-src` | ❌ 服务端补 | ✅ | lazy load 备份 |
| `data-imgfileid` | ❌ 服务端补 | ✅ | 微信图床内部 ID |
| `data-type` | ❌ 服务端补 | ✅ | 图片格式(jpeg/png/gif) |
| `data-aistatus` | ❌ 服务端补 | ✅ | AI 生成图标记(0=非 AI, 1=AI) |
| `alt` | ⚪ 可选 | 否 | 无障碍 / SEO |

**huashu 当前已经正确写了** `class="rich_pages wxw-img"`,这块没问题。

---

## 五、Agent B 对图片间距 bug 的诊断(跟 Agent A 不同)

### 5.1 Agent B 真因假设

`<section style="line-height: 1.8;">` 父容器,line-height 通过 inheritance 传给 figure 内部的 anonymous line-box,**figure 内 img 之外的 strut(行框 baseline 偏移)** 占了 ~7-9px 留白,在 mobile 由于字号自动放大到 16px 看起来更明显。

### 5.2 Agent B 修法

```python
figure_style = (
    "line-height: 0;"
    "font-size: 0;"
)
```

强制 figure 内 line-box 高度为 0,消除 strut。

### 5.3 v9 实测否定 Agent B 假设

**v9 已经做过 Agent B 这个方案**,在 figure 上加 `font-size: 0; line-height: 0; margin: 20px 0; padding: 0;`,**手机端依旧不对称**。

证明 Agent B 真因不成立,strut 不是主因。

### 5.4 Agent B 真因为什么不对

回头看 W3C 规范:

> A line box is the box that holds a line of inline-level content within a block container.

Figure 是 **block** 元素,figure 内只有一个 img(也是 inline 但只有一行),不存在 anonymous line-box 高度叠加问题。Agent B 把 line-box 现象套错地方了。

但 Agent B 的修法**作为防御性 hardening 仍然有价值**(保留 font-size: 0 / line-height: 0,即使不是主因,无害)。

---

## 六、桌面 vs 手机为什么差异这么大

### 6.1 字号 floor

Android Chromium 公众号 webview **会强制把 `<p>` 等正文字号 floor 到 16px**,即使 inline style 写 14px / 17px。但 line-height 不 floor,所以 line-height 算出来的实际行高跟桌面不一样。

**对图片间距的影响**:line-height 1.8 在桌面 17px 字号 = 30.6px;在手机被 floor 到 16px(但 line-height 仍按 17 算) ≈ 30.6px;但相邻 p 的 margin-top 在手机算 0.65em × 16 = 10.4px,桌面 17 × 0.65 = 11px。**小差异但叠加多次会被放大**。

### 6.2 高 DPI

iOS Retina 3x,Android 一般 2.5-3x。1px 边界差异在 3x 设备上被放大 3 倍。

### 6.3 viewport meta

微信 webview 强制 `viewport content="width=375"`(iOS)或 `width=360`(Android)。所以 desktop 编辑器宽 800 看图比 actual 渲染缩小,小间距差异看不出来。

**这是 desktop 编辑器永远不能完全代表 mobile 的根本原因。**

---

## 七、跟 Agent A 的 cross-check 结论

| 维度 | Agent A | Agent B | 我们的判断 |
|---|---|---|---|
| 真因 | inline margin 不 collapse | line-height 1.8 创 strut | **A 更对**,v9 已经否定 B |
| data-src 假设 | 错误,不写 OK | 错误,不写 OK | **一致**,删掉这个方向 |
| 5 attribute | 没特别提 | 详细列出 | **B 的实证有用**,但跟 bug 无关 |
| 修法 | margin 改 padding / 单侧 | font-size:0 + line-height:0 | **采纳 A**,B 的 hardening 保留 |
| 桌面 vs 手机原理 | 没展开 | 字号 floor + DPI + viewport | **B 这部分有 deep insight**,补充到 skill |

---

## 八、对 wechat-style-engineer skill 的输入(B 角度)

1. **不要只看桌面编辑器** — 字号 floor / DPI / viewport 三件事让 mobile 真机跟 desktop 永远有差异
2. **img 必有 class="rich_pages wxw-img"** — 不影响间距,但影响点击放大 / 长按保存等 UX
3. **data-src 不要主动写** — 服务端会 overwrite,写了等于白写
4. **line-height: 0 + font-size: 0 作为 hardening 保留** — 即使不是主因,作为防御性手段无害
5. **debug 必上真机** — 编辑器预览不算数

---

## 九、调研来源

- 微信公众号编辑器 sanitize 规则反推:`D:\Dev\ai-wechat-pipeline\reports\wechat-editor-sanitize-rules.md`
- 微信 webview UA / 内核版本:抓 Android / iOS 真机 User-Agent,详见 `wechat-webview-ua.md`
- W3C CSS2.1 Visual formatting model:https://www.w3.org/TR/CSS21/visuren.html
- W3C CSS Inline Layout Module Level 3(strut / leading 现代化):https://drafts.csswg.org/css-inline/
- 抓包真品 img DOM:devtools 截图保存在 `D:\Dev\ai-wechat-pipeline\reports\wechat-img-dom-screenshots\`
- 卡兹克、花叔、宝玉 3 家公众号真品 article 实证:`D:\Dev\ai-wechat-pipeline\corpus\benchmark-articles\`
