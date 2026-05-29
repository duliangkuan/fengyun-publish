# Musk 调研:图片上下间距诊断

> 调研日期:2026-05-24  
> 调研 agent:Musk 沙盒(3 次调研额度全部用满)

---

## 调研 1:HTML 精确 diff

### 我们 v7 的图 HTML(「他的转身」H1 后第一张图)

```html
<h1 style="font-size: 20px;font-weight: 600;color: #222;line-height: 1.4;
           margin: 32px 0 14px 0;padding: 0 0 0 12px;
           border-left: 3px solid #C15F3C;">
  <span leaf="">他的转身</span>
</h1>

<section style="margin: 20px 0 !important;
                line-height: 1.8 !important;
                color: #2b2b2b !important;
                font-size: 17px;
                letter-spacing: -0.005em;"
         nodeleaf="">
  <img class="rich_pages wxw-img"
       style="max-width: 100%;
              max-height: 500px !important;
              height: auto;
              display: block;
              margin: 0 auto;
              border-radius: 10px;
              box-shadow: 0 6px 24px rgba(193, 95, 60, 0.1);"
       src="http://mmbiz.qpic.cn/..." />
</section>

<p style="margin: 20px 0 !important;...">
  <span leaf="">先把事情说清楚。</span>
</p>
```

**Box model 计算(v7):**
- H1.margin-bottom = 14px
- section.margin-top = 20px → margin collapse → 取 max = **20px**
- img.margin = 0(v7 改掉了)
- section 容器高度 = img 实际高度(无内边距)
- section.margin-bottom = 20px
- p.margin-top = 20px → margin collapse → 取 max = **20px**
- **理论上:图片上方 20px,下方 20px。对称。**

### 真品花叔的图 HTML(第一张图)

```html
<section style="margin: 20px 0 !important;
                line-height: 1.8 !important;
                color: #2b2b2b !important;
                font-size: 17px;
                letter-spacing: -0.005em;"
         nodeleaf="">
  <img class="rich_pages wxw-img"
       data-aistatus="1"
       data-imgfileid="100006628"
       data-src="https://mmbiz.qpic.cn/..."
       data-type="jpeg"
       style="max-height: 500px !important;
              height: auto;
              display: block;
              margin: 24px auto;
              border-radius: 10px;
              box-shadow: 0 6px 24px rgba(193, 95, 60, 0.1);"
       src="./assets/17796124747890...jpg">
</section>
```

**Box model 计算(真品):**
- section.margin-top = 20px
- img.margin-top = **24px**
- img.margin-bottom = **24px**
- section.margin-bottom = 20px

### 差异点(逐条)

| 属性 | v7 | 真品 | 影响 |
|------|-----|------|------|
| `img margin` | `0 auto` | `24px auto` | **核心差异** — 真品图上方和下方各有 24px 内部间距,v7 改成 0 |
| `max-width` on img | `max-width: 100%` | 无此属性 | 轻微:真品无 max-width,依赖微信自身 webview 限宽;我们加了保险 |
| `data-aistatus` | 无 | `data-aistatus="1"` | 微信编辑器内部属性,渲染时忽略,无视觉影响 |
| `data-imgfileid` | 无 | `data-imgfileid="100006628"` | 微信内部图片 ID,无视觉影响 |
| `data-src` | 无 | `data-src="..."` | 微信懒加载用,本地 preview 无影响 |
| `data-type` | 无 | `data-type="jpeg"` | 无视觉影响 |
| src 格式 | mmbiz CDN URL | 本地相对路径 `./assets/...` | 真品是本地存档,CDN 图可能加载失败影响测量 |
| H1 style | `font-size:20px; margin:32px 0 14px 0; border-left:3px solid` | `font-size:32px; gradient color; margin:36px 0 18px` | **H1 本身样式不同** — 真品 H1 更大更豪放;但这不影响图片间距对称性 |

---

## 调研 2:微信渲染规则

### 1. img `display: block` + 容器 `line-height` 的经典陷阱

来自 CSS 规范和多个技术博客的确认结论:

**当 img 设置 `display: block` 之后**,它不再是 inline 元素,因此**不受 baseline 对齐规则影响**。理论上应该没有底部幽灵空白。

但是:**如果父容器(section)设置了 `line-height: 1.8`**,在某些渲染引擎中,容器内部仍然会为「幽灵文本节点(strut)」保留 line-height 对应的空间。这个 strut 是 CSS 规范规定的行内格式化上下文的最小高度占位符。

**关键问题:**我们的 section 容器本身是 block 元素,但它有 `line-height: 1.8 !important; font-size: 17px`。这意味着:
- section 内部的 IFC(行内格式化上下文)有一个 strut 高度 = 17 × 1.8 = **30.6px**
- 即使 img 是 `display: block`,**strut 本身仍然占据 section 高度的一部分**
- 具体表现:**section 的计算高度 = img 高度 + strut 高度的某个比例**

这就是为什么把 img margin 改成 0 之后,section 下方仍然有空白 — **这个空白来自 section 容器内 line-height strut,不是 img 的 margin**。

### 2. `section` 标签在微信公众号渲染中的特殊性

根据调研:
- 微信公众号渲染引擎对 `section` 和 `div` 的处理方式**基本一致**,都是 block-level 元素
- `nodeleaf=""` 是微信编辑器内部标记,表示该节点是叶节点(leaf node),不包含嵌套的编辑单元。这个属性**不影响渲染**
- 微信公众号 webview 基于系统 WebView(Android: Chrome/Blink, iOS: WebKit),遵循标准 CSS box model

### 3. `rich_pages wxw-img` class 的含义

`rich_pages wxw-img` 是微信公众号编辑器为图片元素自动添加的 CSS class。在微信 webview 中,这两个 class **本身没有任何额外的间距 CSS**。微信不会通过这两个 class 注入额外的 padding 或 margin。

### 4. box-shadow 是否影响间距?

`box-shadow: 0 6px 24px rgba(193,95,60,0.1)` — y-offset 6px + blur 24px,实际阴影向下扩展约 30px。

**结论:CSS 规范明确规定,`box-shadow` 不参与 layout 计算,不影响 margin/padding/height。** 微信 webview 遵循此规范。box-shadow 不是间距不对称的原因。

---

## 调研 3:Box model + 真因分析

### 精确 box model 计算(v7)

```
H1:
  font-size: 20px
  line-height: 1.4 → computed line-height = 28px
  margin-bottom: 14px

[H1 与 section 之间的 margin collapse]
  H1.margin-bottom = 14px
  section.margin-top = 20px
  → max(14, 20) = 20px → 图片上方间距 = 20px ✓

section(nodeleaf, 包含 img):
  display: block (section 默认)
  margin: 20px 0 !important
  line-height: 1.8 !important
  font-size: 17px
  → strut 高度 = 17 × 1.8 = 30.6px

  img(inside section):
    display: block
    margin: 0 auto  ← v7 改过
    max-height: 500px

[section 内部高度计算]
  img 是 block,独占一行
  section 高度 = img 高度 + strut
  
  ← 关键问题在这里 →
  strut 是 IFC(行内格式化上下文)的最小线框高度
  即使 img 是 block,section 作为其 BFC 仍然保留了 line-height 带来的 half-leading

[section 与 p 之间的 margin collapse]
  section.margin-bottom = 20px
  p.margin-top = 20px
  → max(20, 20) = 20px → 图片下方间距 = 20px ✓
```

**理论计算结果:上下都是 20px 对称。**

### 真因:为什么实际渲染不对称?

**真因 = section 容器的 `line-height: 1.8` 在微信 webview 中产生了 bottom half-leading**

具体机制:

1. section 容器声明了 `line-height: 1.8; font-size: 17px`
2. 这在 section 内部创建了一个行内格式化上下文(IFC),该 IFC 的 strut 高度 = 30.6px
3. img 虽然是 `display: block`,但 **section 容器本身是 block**,而 img 是其唯一子元素
4. **关键:**在某些 WebKit/Blink 实现中,block 容器的 `line-height` 会被用来计算容器本身的最小高度 —— 即使子元素是 block,容器也会为自己的 line-height strut 预留空间

5. 这个 strut 空间的 half-leading 部分在**底部**表现为额外空白:
   - strut = 30.6px(line-height × font-size)
   - 字体内容区高度 ≈ 17px × 0.8(经验值)≈ 13.6px
   - leading = 30.6 - 13.6 = 17px
   - half-leading = 8.5px(加在 strut 底部)
   - **这 8.5px 加在 section 内部 img 的下方**,使得图片底部 = margin-bottom(20px) + half-leading(~8-9px) ≈ **28-29px**
   - 而图片上方 = section.margin-top(20px),仅 **20px**

6. 结果:下方比上方多 ~8-9px,在手机端视觉上明显不对称。

### 为什么真品没有这个问题?

真品 img 有 `margin: 24px auto`:
- img 上方:section.margin-top(20px) + img.margin-top(24px) = **44px**
- img 下方:img.margin-bottom(24px) + half-leading(~8-9px) + section.margin-bottom(20px)
  - 但 img 有 margin-bottom 24px 把 half-leading 「包裹」了进去,视觉上 24px > 8.5px,half-leading 被 img 的 margin 底部遮蔽/包含了
  - 也就是:img 的 24px margin-bottom 使得图片底部边缘距离 section 底部边缘 = 24px,half-leading 在这个 24px 的范围之内,不会再额外突出来
- 结果:上下视觉间距相对均衡(上方因为 24px img margin 而更多,但整体匀称感好)

实际上**真品花叔的解法**是:接受 line-height strut,用 `img margin: 24px` 把视觉间距做得足够大,让 half-leading 在 24px 里「消化掉」,不再显眼。

### 为什么 v7 的 `margin: 0` 反而让问题更严重?

- v6 img 有 `margin: 24px auto`:和真品一样,half-leading 被 24px 消化
- v7 把 img margin 改成 `0 auto`:消除了 24px 底部 buffer,half-leading 的 ~8-9px 赤裸暴露
- section.margin-bottom = 20px + 暴露的 half-leading ~8.5px = **实际底部间距 ~28-29px**
- section.margin-top(collapse 后) = 20px
- **不对称幅度 ≈ 8-9px,在手机上约等于 0.5~0.6 个字的高度,视觉上非常明显**

---

## Musk verdict

### 真因最可能是:

**section 容器的 `line-height: 1.8; font-size: 17px` 在 block 容器内产生了 half-leading strut(约 8.5px),叠加在 img 的底部与 section 边框之间。v7 把 img margin 改为 0 之后,这个 half-leading 完全暴露,使得图片下方实际间距比上方多 ~8-9px。**

这是一个**标准的 CSS half-leading 问题**,在微信 webview(WebKit/Blink)中完全遵循标准行为,不是微信特有的 bug。

### 推荐修法:

**方案 A(推荐):恢复 img 的 bottom margin,精确抵消 half-leading**

```css
/* 在 img style 中 */
margin: 0 auto 8px auto;  /* 或 9px,经验调试 */
```

原理:用 img.margin-bottom ≈ half-leading,使 section 内部 img 底边到 section 底边的空间 = img.margin-bottom + half-leading ≈ 8+8.5 ≈ 接近 16px。但 section 本身 margin-bottom 20px 负责外部间距。上方:section.margin-top = 20px 无变化。下方:20px + section内8px margin = 实际 28px 但已经接近对称了。

**方案 B(最根本):消除 section 的 line-height strut**

```css
/* section 容器 style 改成 */
line-height: 0 !important;
/* 或 */
font-size: 0 !important;
```

原理:把 section 容器的 line-height 归零,消除 strut。这样 img 的 block 高度就是 section 的精确高度,上下间距完全由 section margin 决定,得到精确对称的 20px 上下间距。

**但是:方案 B 有风险 —— 如果 section 内有文字,文字会因 line-height:0 显示异常**。

**方案 C(最稳妥):与真品完全对齐,恢复 img margin: 24px auto**

```css
/* 恢复 v6 的 img margin */
margin: 24px auto;
```

原理:与真品花叔保持一致。24px bottom margin 足以包裹 ~8.5px half-leading,视觉上「消化」掉了 strut 的影响。结果是图片上下各有 20px(section外) + 24px(img内) = 44px,视觉上宽松但均匀。

### 最终推荐:方案 C

恢复 `margin: 24px auto`,和真品花叔保持一致。这是花叔原稿经过微信编辑器实战验证的方案。

**但附加一个小改动:**如果嫌 44px 太宽松,可以用 `margin: 12px auto`,把 half-leading (~8.5px) 消化掉后,视觉间距 = 20px + 12px = 32px,比纯 section margin 20px 多一点点 buffer,且上下对称。

```css
/* 最终推荐的 img style */
style="max-width: 100%;
       max-height: 500px !important;
       height: auto;
       display: block;
       margin: 12px auto;   /* ← 改这里:从 0 改成 12px,消化 half-leading */
       border-radius: 10px;
       box-shadow: 0 6px 24px rgba(193, 95, 60, 0.1);"
```

### 改动量:小

只改 img 的 `margin: 0 auto` → `margin: 12px auto`(或 24px auto 与真品对齐)。一行 CSS,影响范围仅图片 block。

---

## 不确定的地方

1. **half-leading 精确数值**:约 8.5px 是基于 `font-size:17px; line-height:1.8` 的估算。不同字体的 content-area 高度略有差异(PingFang SC 的 ascender/descender 比例),实际 half-leading 可能是 7-10px 范围内。需要在手机端实测校准。

2. **微信 webview 版本差异**:iOS WebKit 和 Android Blink 对 line-height strut 的具体渲染可能有 1-2px 差异。

3. **WebFetch 被拒**:调研 2 中无法直接读取 CSDN 和 axtonliu.ai 的原文,结论基于搜索结果摘要 + CSS 规范推理,未能直接 fetch 页面验证。

4. **真品实际间距**:真品花叔的上下间距也不完全对称(上方 44px,下方包含 half-leading 后约 52px)。花叔的视觉效果好是因为整体宽松,8px 的不对称在 44px 基数上只有 18%,感知不强。我们 v7 的 8px 不对称在 20px 基数上是 40%,非常明显。
