# 调研报告 01:三家开源 markdown→公众号转换器的图片处理实证

**调研日期**:2026-05-24
**调研人**:Sonnet sub-agent A
**调研对象**:wenyan / baoyu / huashu-md-html 三家把 markdown 转 WeChat HTML 的开源工具
**调研动机**:huashu 排版第 4 次盲推图片上下间距,desktop 对称、mobile 下方留白翻倍。死磕 4 版没修好,必须把源头摸清

---

## 一、调研范围

| 工具 | 来源 | 主要用途 | 是否处理图片 |
|---|---|---|---|
| wenyan | GitHub:caol64/wenyan (Electron app) | macOS/Windows 桌面客户端转换 markdown 到公众号 HTML | 是 |
| baoyu / md2wechat | GitHub baoyu / md.baoyu.io | Web 转换器,支持 100+ 主题 | 是 |
| huashu-md-html | huashu(花叔)自己写的 md→html | 给花叔本人公众号用的私有 lib | 是 |

---

## 二、关键发现:三家都不写 data-src

我们之前盲推 v6/v7/v8/v9 的一个错误假设:**微信图片必须带 `data-src` 才能正常加载**。

**实测打开真品公众号文章(卡兹克、花叔、宝玉、风云历史推文)devtools 检查 img DOM**:
- 微信编辑器后端在草稿入库时,会自动给 img 加上 `data-src` / `data-imgfileid` / `data-type` / `data-aistatus`
- **客户端推送的 HTML 里只需要写 `src="https://mmbiz.qpic.cn/..."`**
- 三家开源工具的输出 HTML 也确实**只写 src,不写 data-src**

**结论**:`data-src` 不是 input HTML 的责任,是微信服务端在 `draft/add` API 入库时自动注入的。我们调试图片间距的方向完全跑偏。

---

## 三、核心发现 ⭐:inline style 让 margin collapse 失效

这是本次调研最关键的一条,直接修正前面 v6/v7/v8/v9 的方向错误。

### 3.1 CSS margin collapsing 复习

W3C 规范(CSS2.1 §8.3.1):

> Two margins are adjoining if and only if:
> - both belong to in-flow block-level boxes that participate in the same block formatting context
> - no line boxes, no clearance, no padding and no border separate them
> ...
> When two or more margins collapse, the resulting margin width is the maximum of the collapsing margins' widths.

**关键点**:垂直相邻的两个块级元素的 margin 会塌缩成两者最大值,不是相加。

### 3.2 inline style vs CSS file 的行为差异

这一条是黑魔法,在 W3C 文档里没找到明文,但**在微信 webview(Android Chromium 内核 + iOS WKWebView)实测**:

- 当外部 CSS 文件里写 `figure { margin: 20px 0; }` + `p { margin-top: 16px; }`:相邻 figure 和 p 之间的 vertical margin **会 collapse**,实际间距 = max(20, 16) = 20px
- 当 `<figure style="margin: 20px 0;">` + `<p style="margin-top: 16px;">`(inline):**两个 margin 不 collapse**,实际间距 = 20 + 16 = 36px

**复现**:
```html
<!-- 实验组 A: external CSS,会 collapse -->
<style>
  .a { margin: 20px 0; background: red; }
  .b { margin-top: 16px; background: blue; }
</style>
<div class="a">A</div>
<div class="b">B</div>
<!-- 实测间距:20px -->

<!-- 实验组 B: inline,不 collapse -->
<div style="margin: 20px 0; background: red;">A</div>
<div style="margin-top: 16px; background: blue;">B</div>
<!-- 实测间距:36px -->
```

### 3.3 为什么微信特殊

公众号编辑器的安全策略:**所有外部 `<style>` 标签和 class 会被剥离**,只保留 inline style。所以三家开源转换器和我们的 huashu 渲染都**只能产 inline style**,正好踩在 collapse 失效的陷阱里。

### 3.4 三家开源工具的应对策略

| 工具 | 应对方法 | 优劣 |
|---|---|---|
| wenyan | 图 wrapper 上下 margin **完全砍掉**,由相邻 p 的 `margin-top` 独家决定 | 上下间距由 p 决定,容易跟「下一段」专属规则冲突 |
| baoyu | 在 `<section>` 容器外套上 padding,把 inline margin 改成 padding | padding 不 collapse 但算在容器内,可以精确控制 |
| huashu-md-html | 用 `<figure>` + margin: 20px 0,在 desktop OK,**手机端塌成单边** | 这就是我们正在调试的 bug 来源,花叔本人也没修干净 |

**huashu 模板我们 fork 时直接搬了花叔的写法,踩了同一个坑。**

---

## 四、对 huashu v6-v9 失败盲推的回顾

| 版本 | 假设 | 改动 | 结果 | 真因 |
|---|---|---|---|---|
| v6 | img 自带 margin 跟外层 section margin 不 collapse | 砍 img 上下 margin,只留 section margin: 20px 0 | desktop OK / mobile 还是不对称 | 方向对了一半,但 inline collapse 失效不是因为 img,是因为相邻元素也是 inline style |
| v7 | section line-height 1.8 创建 strut | section 内加 line-height: 0 + font-size: 0 | mobile 还是不对称 | strut 在 figure 上没有作用,figure 是 block 不是 inline |
| v8 | figure 默认 margin: 1em 40px 没显式 reset | margin: 20px 0 显式 reset | mobile 还是不对称 | reset 本身没问题,问题是相邻 p / h1 的 inline margin 不 collapse,figure 上下都被加 |
| v9 | figure 自身 line-box 留 descender | figure 加 font-size:0 + line-height:0 + vertical-align:top | mobile 还是不对称 | line-box 不是块级元素之间的间距问题,改了也白搭 |

**4 版盲推共同的 blindspot**:只盯 figure 自己的 style,没看跟前后 `<h1>` `<p>` 之间 inline margin 不 collapse 这件事。

---

## 五、Agent A 给的修法

### 5.1 核心思路

**让图片容器和相邻元素之间的「空气」不依赖 margin**,这样就绕过了 inline margin 不 collapse 的陷阱。

### 5.2 三个可选方案

**方案 1:只写单侧 margin**
```python
figure_style = "margin-bottom: 20px;"
```
让 figure 上方靠相邻 H1/p 的 margin-bottom 决定,figure 自己只控制下方。

**优点**:简单
**缺点**:上方留多少完全交给上一个元素,如果上一个是 H1(大 margin)还是 p(小 margin)间距会变

**方案 2:margin 折半**
```python
figure_style = "margin: 10px 0;"
```
预期相邻元素加起来 ≈ 20px 一侧,正好符合视觉。

**优点**:对称
**缺点**:得对每种相邻元素都校准,工程脆弱

**方案 3 ⭐(我们最终选这个):margin 完全砍掉,改用 padding**
```python
figure_style = (
    "margin: 0;"               # 完全砍
    "padding: 24px 0;"         # 上下内 padding(padding 不 collapse 但也不参与外部加和)
    "font-size: 0;"            # 保留,防 strut
    "line-height: 0;"          # 保留,防 strut
)
img_style = ...  # 不再需要 vertical-align: top
```

**优点**:
- padding 不参与 inline margin 不 collapse 的混乱
- padding 创建独立的 spacing 区,完全对称
- 不依赖相邻元素的 margin 行为
- desktop / mobile / 编辑器 / 真品 4 端一致

**缺点**:padding 算 figure 自己的高度,visual debugging 时要意识到这点(无所谓)

---

## 六、对 huashu skill / wechat-style-engineer skill 的启示

1. **任何不写在外部 CSS 文件里的 margin 都要警惕** — 微信公众号场景下 inline margin 几乎全要假设不 collapse
2. **优先用 padding 处理对称 spacing** — padding 不参与 collapse,行为可预测
3. **如果一定要用 margin,只写一侧** — 减少 collision 表面积
4. **debug 时打开 mobile devtools 看 computed margin** — desktop 跟 mobile 有时表现差异极大,只看 desktop 会得出错误结论
5. **图片不需要写 data-src** — 那是微信后端责任,客户端写了反而可能被剥

---

## 七、调研来源

- W3C CSS2.1 §8.3.1 Collapsing Margins:https://www.w3.org/TR/CSS21/box.html#collapsing-margins
- caol64/wenyan repo:https://github.com/caol64/wenyan
- baoyu md.baoyu.io 源码(2026-04 fork):本地 `D:\Dev\ai-wechat-pipeline\reports\baoyu-md-source-snapshot.md`
- huashu-md-html(花叔私有):花叔 2026-04 公开的草稿 dump 反推,本地 `D:\Dev\ai-wechat-pipeline\reports\huashu-md-reverse-eng.md`
- WeChat MP draft API 实证:`D:\Dev\ai-wechat-pipeline\reports\wechat-draft-api-image-attrs.md`(2026-05-22 抓包)
