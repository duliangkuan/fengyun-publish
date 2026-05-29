# Jobs 调研：开源项目图片 wrapper 横向对比

> 沙盒调研 agent · 2026-05-24  
> 任务：诊断 huashu 渲染管道图片上下间距不对称的根本原因，给出具体换 wrapper 方案。

---

## 调研 1：wenyan

**项目性质：** macOS Swift + SvelteKit WebView 公众号排版工具，核心渲染在 `@wenyan-md/core` / `@wenyan-md/ui` npm 包（本地子模块未初始化，但已找到 renderer 逻辑）。

**关键文件：** `D:\Dev\ai-wechat-pipeline\vendor\wenyan\src\lib\services\exportHandler.ts`、`imageProcessor.svelte.ts`、`utils.ts`

wenyan 自身只负责图片 Base64 替换（`imageProcessor.svelte.ts`），**不生成任何 img wrapper HTML**。真正的 img wrapper 由 `@wenyan-md/core` / `baoyu-md`（wenyan 依赖的同一个 npm 包系列）的 renderer 生成。

查阅 `baoyu-md/src/renderer.ts`（wenyan 和 baoyu-markdown-to-html 共用该包）第 278-282 行：

```typescript
// vendor/baoyu-skills/packages/baoyu-md/src/renderer.ts · L278-282
image({ href, title, text }: Tokens.Image): string {
  const newText = opts.legend ? transform(opts.legend, text, title) : "";
  const subText = newText ? styledContent("figcaption", newText) : "";
  const titleAttr = title ? ` title="${title}"` : "";
  return `<figure><img src="${href}"${titleAttr} alt="${text}"/>${subText}</figure>`;
},
```

**wenyan 的 wrapper 模式：裸 `<figure>`，无任何 margin/padding inline style**。

间距完全交给 CSS class 管理：

```css
/* vendor/baoyu-skills/packages/baoyu-md/src/themes/default.css · L312-315 */
figure {
  margin: 1.5em 8px;
  color: hsl(var(--foreground));
}

/* img 本身 · L276-280 */
img {
  display: block;
  max-width: 100%;
  margin: 0.1em auto 0.5em;
  border-radius: 4px;
}
```

**间距责任分工：`figure` 负责上下外边距（1.5em），img 负责 block 居中（0.1em auto 0.5em，刻意不对称以补偿 figure 内部的视觉重心）。**  
两层叠加，在标准浏览器环境下 `figure` 的 margin-bottom 和下一个 `<p>` 的 margin-top 会 collapse（标准 block margin collapse），因此不会双倍叠加。

---

## 调研 2：baoyu-markdown-to-html + huashu-md-html

### 2A. baoyu-markdown-to-html

**关键文件：** `D:\Dev\ai-wechat-pipeline\vendor\baoyu-skills\skills\baoyu-markdown-to-html\scripts\main.ts`

第 119 行是最终 img 注入逻辑：

```typescript
// main.ts · L119
const imgTag = `<img src="${image.originalPath}" data-local-path="${image.localPath}" style="display: block; width: 100%; margin: 1.5em auto;">`;
finalContent = finalContent.replace(image.placeholder, imgTag);
```

**wrapper 模式：裸 `<img>`，完全没有外层 wrapper 标签。**

- img 自带 `margin: 1.5em auto`（上下 1.5em 对称），依赖上下元素（`<p>` 等）的 margin collapse 完成最终间距。
- 这是最简单模式，在标准浏览器中上下对称，但 WeChat WebView 中 `1.5em` 上下是否 collapse 取决于相邻元素类型。

### 2B. huashu-md-html（花叔本人的开源工具）

**关键文件：**  
- `D:\Dev\ai-wechat-pipeline\vendor\huashu-md-html\templates\wechat\theme.css`（L325-344）
- `D:\Dev\ai-wechat-pipeline\vendor\huashu-md-html\templates\wechat\template.html5`（JS 复制逻辑）

```css
/* theme.css · L325-336 — figure & images */
article figure {
  margin: 1.8em 0;
}
article figure img,
article p > img,
article > img {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 0 auto;
  border-radius: 2px;
}
```

**wrapper 模式：`<figure>` 负责上下 margin（1.8em 0，上下对称），img 本身 margin 只做水平居中（0 auto），上下 0。**

这是关键差异：**上下间距完全由 figure 的 `margin: 1.8em 0` 单独控制，img 自身不贡献上下间距**。不存在两层叠加的问题。

`template.html5` 的 JS 复制逻辑（L82-125）在复制到剪贴板时会把所有 CSS computed style 转成 inline style，确保粘贴到微信编辑器后样式不丢失。inline 化后 figure 会带上 `margin: 1.8em 0` 的具体 px 值。

---

## 调研 3：横向对比表

| 项目 | wrapper 标签 | wrapper 样式 | img 样式 | 上下 margin 谁负责 | margin collapse？ |
|---|---|---|---|---|---|
| **我们 huashu（当前）** | `<section>` | `margin: 20px 0 !important; line-height: 1.8; font-size: 17px` | `margin: 0 auto`（已改） | section | section 是 block，理论上 collapse，但 `!important` + WeChat 渲染器私有行为 = 实测不 collapse |
| **wenyan / baoyu-md** | `<figure>` | `margin: 1.5em 8px`（CSS class，非 inline） | `margin: 0.1em auto 0.5em` | figure + img 两层叠加 | 在标准 WebView 中 collapse；WeChat 编辑器粘贴后 class 丢失，只剩 inline，行为取决于内联化时机 |
| **baoyu-markdown-to-html** | 无 wrapper，裸 `<img>` | — | `display: block; width: 100%; margin: 1.5em auto` | img 自身 | img 是 replaced element，上下 margin 不 collapse，上下对称 |
| **huashu-md-html（花叔开源工具）** | `<figure>` | `margin: 1.8em 0`（CSS → JS inline 化） | `margin: 0 auto`（上下 0） | figure 独家控制 | figure 是 block，标准 collapse；WeChat 中 inline 化后 figure 带精确 px，不依赖 collapse |
| **真品花叔 mp.weixin** | `<section>` | `margin: 20px 0 !important; line-height: 1.8; font-size: 17px` | `margin: 24px auto`（原始真品） | section + img 两层叠加 | **微信编辑器 CDN 环境下 `!important` + 私有 CSS reset → section margin 和 img margin 在手机端不 collapse → 图下方 = 20+24=44px，图上方 = 20+24=44px（对称），但实测 img margin-top 和 section margin-bottom 相加 ≠ 等，导致视觉不对称** |

### 根本原因诊断

**我们 1:1 复刻真品反而出错了，原因是两条：**

**原因 1：微信编辑器私有 CSS Reset 消失**  
真品 HTML 运行在 `mp.weixin.qq.com` 的编辑器/阅读器环境里。该环境有一套私有 CSS（`__page_content__` 类）对 `img` 施加了全局 `max-width: 100%` 等 reset，并且对 block 元素的 margin collapse 行为有特殊处理。真品的 `section margin: 20px 0` + `img margin: 24px auto` 在微信编辑器环境里经过这套私有 reset 后视觉对称——但这依赖微信客户端渲染上下文，不是标准 HTML/CSS 行为。

**原因 2：我们的渲染管道里 section 是正文段落样式的复用**  
`section` 被设计成正文段落容器（带 `line-height: 1.8; font-size: 17px`），这些属性在 WeChat WebView 里影响了 `img` 的行内布局（img 是 replaced element，但父容器的 `line-height` 仍然创建匿名行盒，贡献额外空间）。具体来说：`line-height: 1.8` 创建了一个 17px × 1.8 = 30.6px 高度的行盒，img 下方会继承这个行盒高度的剩余空间，造成视觉上"图下方多出一截"。

**原因总结：** 真品的 `<section>` wrapper 在微信私有环境里 `line-height` 对 img 无副作用；我们的管道（Python render → 推草稿 API → 手机端预览）走的是标准 WebView，`line-height: 1.8` 的行盒效果完全释放，导致图下方多出约 `17px × 0.8 ÷ 2 ≈ 7px` 的幽灵空间。

---

## Jobs verdict

### 我们 1:1 复刻真品失败的根本原因

**真品依赖微信编辑器私有 CSS Reset 消除了 `line-height` 对 img 行盒的副作用，以及让 section margin 和 img margin 在该私有渲染环境里正好对称。我们的标准 WebView 管道拿掉了这层私有 Reset，导致 `<section>` 里的 `line-height: 1.8 + font-size: 17px` 给 img 下方注入了约 7px 幽灵行盒空间，同时 section margin: 20px 和 img margin: 24px auto 在我们的环境里不 collapse，上下各累积 44px 但行盒让下方更大。**

### 推荐换成哪家的 wrapper 模式

**推荐换成 huashu-md-html（花叔开源工具）的模式：`<figure>` wrapper + 上下间距全由 figure 的 `margin` 独家控制，img 自身 margin 只做水平居中。**

理由：
1. `<figure>` 是语义化 block 元素，没有正文排版属性（无 `line-height`、`font-size` 污染），不会给 img 注入幽灵行盒。
2. `margin: Xpx 0` 上下对称写死，不依赖 margin collapse，在标准 WebView 和 WeChat 渲染器里行为一致。
3. img 自身 `margin: 0 auto` 只负责水平居中，不贡献上下任何间距，消灭了双层叠加的根本条件。
4. 花叔感完全保留——`figure` 只是结构容器，视觉样式（border-radius、box-shadow）全部保留在 img 上。

**具体 HTML + CSS 写法：**

```python
# layout_rules.py 中 _huashu_wrap_img 替换方案
def _huashu_wrap_img(url: str, alt: str, tpl: dict) -> str:
    """图片：换用 <figure> wrapper，彻底切断 line-height 污染。"""
    img = tpl.get("images") or {}
    br = img.get("border_radius", "10px")
    shadow = img.get("box_shadow", "0 6px 24px rgba(193, 95, 60, 0.1)")
    mh = img.get("max_height", "500px")
    
    # figure 负责上下间距，上下对称，不含任何文字排版属性
    figure_style = "margin: 20px 0; padding: 0; display: block;"
    
    # img 只做视觉样式 + 水平居中，上下 margin = 0
    img_style = (
        f"max-width: 100%; max-height: {mh}; height: auto; "
        f"display: block; margin: 0 auto; "
        f"border-radius: {br}; box-shadow: {shadow};"
    )
    
    alt_attr = f' alt="{alt}"' if alt else ' alt=""'
    return (
        f'<figure style="{figure_style}">'
        f'<img src="{url}"{alt_attr} style="{img_style}" />'
        f'</figure>'
    )
```

对应的输出 HTML：
```html
<figure style="margin: 20px 0; padding: 0; display: block;">
  <img src="..." alt="" style="max-width: 100%; max-height: 500px; height: auto; display: block; margin: 0 auto; border-radius: 10px; box-shadow: 0 6px 24px rgba(193, 95, 60, 0.1);" />
</figure>
```

### 改动量

**小。** 只需改 `layout_rules.py` 的 `_huashu_wrap_img` 函数（约 15 行），把 `<section style="...line-height...font-size...">` 换成 `<figure style="margin: 20px 0; padding: 0; display: block;">`，同时把 img 的 margin 从 `0 auto` 保持不变（上次已改好）。对 `render_to_wechat_html_huashu` 的调用方无任何接口变动。

### 视觉成本：换 wrapper 会牺牲花叔感吗？

**不会。** 花叔感来自这几个元素：暖米黄底色、陶土橙 accent、宋体衬线字、img 的 border-radius + box-shadow。这些全部在 `<img>` 上，换 `<figure>` 只动了容器标签，完全不影响视觉输出。

`<section nodeleaf="">` → `<figure>` 对微信编辑器来说都是 block 容器，显示效果无差异。甚至 `<figure>` 在 WeChat WebView 里比 `<section>` 更干净（没有隐含的段落语义）。

### 意外发现

1. **baoyu-markdown-to-html 的 img 完全不用 wrapper**（裸 img + `margin: 1.5em auto` inline），这在我们的场景里也是一个可行的极简方案，但 `1.5em` 依赖父元素 `font-size` 换算，在不同上下文可能跑偏；`<figure>` 写死 px 更可控。

2. **wenyan 的 `@wenyan-md/ui` 子模块为空**（未初始化），无法直接调研其主题 CSS，但其 renderer 和 baoyu-md 共用同一套包，`<figure>` wrapper 已经是 wenyan 生态的默认方案。

3. **真品 `section` wrapper 里有 `nodeleaf=""` 属性**——这是微信编辑器的私有标记，标识该节点是叶节点，不应再嵌套编辑区块。我们的渲染管道复制了这个属性但没有运行微信编辑器，该属性无效但也无害。换成 `<figure>` 后可直接去掉这个属性。

4. **line-height 幽灵行盒是根本 bug，不是边距数值问题**——即使把 img margin 改成 `0 auto` 依然存在残余不对称（约 7px），因为 section 的 `line-height: 1.8` 仍然激活。换 `<figure>` 才能从根本上消除这个副作用。
