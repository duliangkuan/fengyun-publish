# Musk 调研 2 — 结构组件机械清单

## 数据源

| # | 篇名 | 发布日期 |
|---|------|----------|
| A | 9项benchmark第一、35小时不停手，Qwen3.7-Max有点东西 | 2026-05-22 |
| B | AI最大的礼物，是让你能廉价地失败100次 | 2026-05-14 |
| C | Claude Code发布Agent View，多任务流的ADHD患者有救了 | 2026-05-12 |
| D | Mavis：让两个Agent"互掐"，比一个聪明Agent靠谱 | 2026-05-15 |
| E | 公司可能是一个300年的临时实验 | 2026-05-23 |
| F | 微信读书出官方skill了，但它还差关键一步 | 2026-05-17 |

---

## 各组件统计

### 1. 标题层级

#### H1（页面大标题，由微信平台 `rich_media_title` 生成，正文外）

| 篇 | H1 内容（标题文字）| 来源 |
|----|-------------------|------|
| A | 9项benchmark第一、35小时不停手，Qwen3.7-Max有点东西 | 平台标题 |
| B | AI最大的礼物，是让你能廉价地失败100次 | 平台标题 |
| C | Claude Code发布Agent View，多任务流的ADHD患者有救了 | 平台标题 |
| D | Mavis：让两个Agent"互掐"，比一个聪明Agent靠谱 | 平台标题 |
| E | 公司可能是一个300年的临时实验 | 平台标题 |
| F | 微信读书出官方skill了，但它还差关键一步 | 平台标题 |

注：上述 H1 是平台生成结构，**正文内容区域**另有章节标题，分两种方案：

#### 正文内 H2（主要章节标题）

**样式特征（A/B/C/D 篇统一方案）：**
```css
font-size: 26px;
font-weight: 600;
color: #C15F3C !important;  /* 赤陶橙，但…*/
background: linear-gradient(135deg, #C15F3C 0%, #9DC88D 100%);  /* 渐变橙→绿 */
-webkit-background-clip: text;  /* 渐变填色文字 */
line-height: 1.25;
margin: 32px 0 16px;
letter-spacing: -0.015em;
```
视觉效果：橙→绿渐变色文字，无背景块，无边框。

**正文内 H1（E 篇「公司」文章使用方案，仅该篇）：**
```css
font-size: 32px;
font-weight: 600;
color: #C15F3C !important;
background: linear-gradient(135deg, #C15F3C 0%, #e97d5b 50%, #CC8B7A 100%);  /* 橙→浅橙→玫瑰 */
-webkit-background-clip: text;
line-height: 1.2;
margin: 36px 0 18px;
letter-spacing: -0.02em;
```

**正文内 H3（C 篇「Agent View」文章使用）：**
```css
font-size: 22px;
font-weight: 600;
color: #2b2b2b !important;  /* 深灰，非橙色 */
line-height: 1.3;
margin: 28px 0 14px;
letter-spacing: -0.01em;
```
注意：H3 是纯深灰色，无渐变，尺寸更小。

#### 各篇正文标题统计

| 篇 | 正文内 H2 数量 | 正文内 H1 数量 | 正文内 H3 数量 | 标题命名风格 |
|----|--------------|--------------|--------------|------------|
| A  | 6 | 0 | 0 | 短句描述行动（「先说说这12项benchmark」「我把Qwen3.7-Max接进了Claude Code」） |
| B  | 5 | 0 | 0 | 单个汉字数字（「一」「二」「三」「四」「五」） |
| C  | 1 | 0 | 4 | H2 = 「参考来源」；H3 = 「一、Agent View是什么」「二、...」「三、...」「四、...」「写在最后」 |
| D  | 3 | 0 | 2 | H2 = 场景描述；H3 = 「第一件：让两个AI心思相反」「第二件：调度靠程序，不靠AI拍板」 |
| E  | 0 | 7 | 0 | 「一、公司制之前的世界」「二、公司制是工业化的产物」…「七、回到那个反直觉的问题」 |
| F  | 0 | 0 | 0 | **全篇无正文标题**；全用 H2 替换为色块 banner 形式（见下注） |

注：F 篇使用独特的「色块 banner」代替标题，style 如下：
```css
font-size: 20px;
font-weight: 600;
color: #fff !important;
background-color: #d32f2f !important;  /* 深红底，白字 */
padding: 12px 20px;
border-radius: 4px;
margin: 32px 0 16px;
```
F 篇主色调为红色 #d32f2f，与其他 5 篇橙色体系完全不同（疑似使用了不同模板）。

**汇总：**

| 组件 | 出现篇数 | 总次数 | 平均每篇 | 是否带 emoji | 是否带数字编号 |
|------|---------|--------|----------|-------------|----------------|
| 正文 H2（渐变橙色） | 4/6 | 15 | 2.5（4篇均值） | 否 | A：否；B：是（一二三四五）；C：1个无编号 |
| 正文 H1（渐变橙色，E 篇） | 1/6 | 7 | 7 | 否 | 是（一~七） |
| 正文 H3（深灰色） | 2/6 | 6 | 3（C、D两篇均值） | 否 | C篇：是；D篇：否 |
| 色块 banner 标题（F 篇） | 1/6 | 6 | 6 | 否 | 否 |

---

### 2. 引用块（blockquote）

| 篇 | 出现次数 | 内容举例（50字内） | 视觉样式 |
|----|---------|-------------------|---------|
| A  | 1 | 「1907年没有AI，没有计算机……成人世界总是急于把他们塑造成某种标准产品」 | 左边框4px #C15F3C，斜体，背景 rgba(0,0,0,0.05)，圆角6px |
| B  | 0 | — | — |
| C  | 0 | — | — |
| D  | 0 | — | — |
| E  | 0 | — | — |
| F  | 0 | — | — |

**blockquote CSS（仅 A 篇出现）：**
```css
margin: 18px 0;
padding: 10px 16px;
border-left: 4px solid #C15F3C;  /* 橙色左边框 */
font-size: 17px;
line-height: 1.6;
font-style: italic;
border-radius: 6px;
background: rgba(0, 0, 0, 0.05) !important;
color: rgba(0, 0, 0, 0.8) !important;
```

引用内容类型：AI 角色扮演结果（蒙台梭利教育家的直接回答），属于文章内部"实验产物"展示，不是引用他人已有著作。

**总结：blockquote 使用率极低，6 篇仅 1 次（1/6）。**

---

### 3. 列表（ul / ol）

#### 无序列表 ul

| 篇 | ul 出现次数 | bullet 字符 | 内容类型 | 每项平均字数 |
|----|-----------|-------------|---------|------------|
| A  | 1 | 默认（CSS list-style 未指定，浏览器默认圆点） | 数字数据清单（35小时/432次/1158次/10倍） | 约15字 |
| B  | 0 | — | — | — |
| C  | 1 | 默认圆点 | 参考来源（URL 列表，6条） | 约50字含 URL |
| D  | 2 | 默认圆点 | 分析要点清单；参考资料链接 | 约60字；约50字 |
| E  | 0 | — | — | — |
| F  | 3 | 明确 `list-style-type: disc` | 「裸weread推的14本里」「huashu-weread推的5本」「直接说大白话」 | 约25字 |

ul CSS（A/C/D 篇）：
```css
margin: 20px 0;
padding-left: 28px;
class="list-paddingleft-1"
/* li: margin:10px 0; line-height:1.8; font-size:17px */
```

ul CSS（F 篇）：
```css
margin: 20px 0;
padding-left: 28px;
list-style-type: disc;
/* li: margin:10px 0; line-height:1.8; color:#1a1a1a */
```

注：参考资料区的 ul 列表项 font-size 降为 15px（区别于正文 17px）。

#### 有序列表 ol

| 篇 | ol 出现次数 | 内容类型 | 格式 |
|----|-----------|---------|------|
| C  | 1 | worktree 隔离处理的三种方式 | `1. 2. 3.`，padding-left:28px，每项约60字 |
| 其余 5 篇 | 0 | — | — |

**总结：**
- ul 出现 4/6 篇，总计 7 次；ol 仅 1/6 篇出现 1 次
- 无序列表主要用于：数据清单、参考链接、操作建议
- 列表前通常有过渡句（如「完整数据：」「打开方式有两种：」）

---

### 4. 分割线

| 篇 | `<hr>` 次数 | 字符分割 | 位置描述 |
|----|-----------|---------|---------|
| A  | 0 | 无 | — |
| B  | 0 | 无 | — |
| C  | 1 | 无 | 正文最后一段「写在最后」后，在「参考来源」H2 之前 |
| D  | 1 | 无 | 正文结尾，在「MiniMax Mavis 下载」纯文字段落之前 |
| E  | 0 | 无 | — |
| F  | 1 | 无 | 正文结尾，在「官方 weread skill 地址」之前 |

`<hr>` 的统一 CSS：
```css
margin: 36px auto;
border: none;
height: 2px;
background: linear-gradient(to right, transparent, rgba(193, 95, 60, 0.3), rgba(157, 200, 141, 0.3), transparent);
/* F 篇略有不同：rgba(193,95,60,0.3) → #d32f2f（红色渐变）*/
```

**总结：**
- `<hr>` 出现 3/6 篇，每篇仅用 1 次
- 位置固定：正文结束与尾部链接/参考之间（相当于「正文结束符」）
- 无任何字符型分割线（· · · / —— / *** 均未出现）
- 3/6 篇完全没有分割线

---

### 5. 加粗 / 高亮

#### `<strong>` 用法（所有篇均有）

**统一 CSS：**
```css
font-weight: 600;
color: #C15F3C !important;  /* 橙色文字 */
background-color: rgba(193, 95, 60, 0.08) !important;  /* 极淡橙色底 */
padding: 2px 6px;
border-radius: 3px;
```

F 篇（红色主题）的 `<strong>`：
```css
font-weight: 700;
color: #d32f2f !important;
background-color: rgba(211, 47, 47, 0.08) !important;
padding: 2px 6px;
border-radius: 3px;
```

#### 各篇 `<strong>` 使用次数统计

| 篇 | `<strong>` 估计次数 | 典型加粗内容举例 |
|----|-------------------|----------------|
| A  | 约10次 | 「IFBench指令遵循79.1分」「Qwen3.7这次的12项评测都是在多框架下完成的」「2088本」「310本笔记书」「5318条笔记」「长链路任务能这样跑下来的国产模型不多」「两个skill并用、自己写4个Python脚本…」|
| B  | 约14次 | 「不是让你更容易成功，是让你更容易失败」「大部分活不过一周」「AI让生产变快了但迭代速度其实没怎么变…」「适应峰」「要去那座山，必须先下山」「敢换方向」「失败的意义从来不是失败本身」「爆款是结果。系统是原因。」「多样性爆发只是开场…」|
| C  | 约10次 | 「131亿token，606个独立会话，38个项目…」「Max 20x档（200美元/月）」「我已经被多agent工作流淹没好几个月了」「每个后台agent都在自己的小房间里干活」「主目录刷新是看不到任何改动的」「如果你之前只用单session的Claude Code」「如果你之前已经在开多个iTerm窗口…」「如果你在用Crystal/claude-squad…」「别因为派活变简单，就一次派8件」「Sherlocking时刻」「subagent」「agent team」「agent view」「人类」|
| D  | 约18次 | 「长程任务该怎么靠谱地交付」「写的不审，审的不写」「别让AI当自己的裁判」「Worker和Verifier的对抗循环」「角色扮演不等于角色分工」「很多框架里的验证环节是可选的附加步骤，在我们这里它是架构的核心」「写作三审三校」「huashu-book-pdf」「darwin-skill」「huashu-data-pro」「我把质量门禁丢给了人，没丢给系统」「每个都做对了一两件事，但全是单点」「多AI协作的核心从来不是「开几个进程」，是结构」「AI协作的下一个阶段，是把AI从「工具」变成「同事」」「比一个无所不能的超级指令更有用」「Team不是默认选项，是策略选项…」|
| E  | 约15次 | 「到底存在多久了」「也不过300年左右」「匠师从来不是「一个人」」「工业化最大的副作用，是让市场交易成本急剧上升」「所以「公司」被发明了——它是一个能在匿名社会里重新制造长期信任的容器」「公司的边界…」「如果哪一天市场交易成本…公司就应该缩小」「AI正在系统性地把市场交易成本砍下来」「长期承诺」「我做的事其实不新，是相当老的…」「我必须诚实一点…」「少数有声誉资本…大多数没有这些资本的人可能反而更脆弱」「比这件事更深一层的，是「员工」这个心智模型也是300年的临时产物」「不是工作消失了，是我们用来理解工作的语言要重写」「等一套新的语言长出来之前，会有一段时间，很多人不知道怎么向陌生人介绍自己」|
| F  | 约15次 | 「查阅书架、书籍搜索、阅读统计、书籍详情、笔记和划线、推荐好书」「全部产生于2020年9月8日一天，跨度10小时」「根本没看我的笔记和书架」「书架和笔记是两个数据源，必须交叉」「裸weread推的14本里」「huashu-weread推的5本」「断崖发生在2023年」「全是2024年开始爆发的」「在那之前我读书是为了「我要怎么把事做正确」……在那之后……」「这件事任何「年度读书报告」都给不了」「官方把最难的事做完了」「关于你这个读者的、可对话的、活的画像」|

**汇总：**

| 指标 | 数据 |
|------|------|
| 所有篇均有 `<strong>` | 6/6 |
| 全样本总次数（估算） | ~82次（A:10, B:14, C:10, D:18, E:15, F:15） |
| 平均每篇 | ~14次 |
| 加粗主要对象 | 核心论断句、关键概念名词、数字/数据、产品/工具名、引用他人原话精髓 |
| 是否有纯 `<b>` 标签 | 无，全为 `<strong>` |
| 是否有其他 span 自定义高亮 | 无，仅 `<strong>` 实现高亮 |

**加粗位置规律：**
- 段中关键名词（一个产品名、一个指标）
- 段末核心结论（「爆款是结果。系统是原因。」）
- 段首强调句（「如果你之前只用单session的Claude Code」）
- 引述他人的核心原话（不超过一句）

---

### 6. emoji

| 篇 | emoji 总数 | 位置分布 | 使用的 emoji |
|----|-----------|---------|------------|
| A  | 0 | — | — |
| B  | 0 | — | — |
| C  | 0 | — | — |
| D  | 0 | — | — |
| E  | 0 | — | — |
| F  | 0 | — | — |

**总结：6 篇正文内容区域 emoji 出现次数为 0。**

注：微信文章平台标题文字（H1 标签内 `js_title_inner`）也均无 emoji。

---

### 7. 链接

#### 外部链接

| 篇 | 正文中可见链接次数 | 链接形式 | 链接对象类型 |
|----|-----------------|---------|------------|
| A  | 0（正文无超链接文字） | — | — |
| B  | 0 | — | — |
| C  | 0（参考来源以纯文字 URL 形式列在 ul 内，非 `<a>` 超链接） | 纯文字 | 官方博客/文档/GitHub |
| D  | 0（同上，参考资料为纯文字 URL） | 纯文字 | 知乎/微信公众号/Anthropic/Google/B站 |
| E  | 0 | — | — |
| F  | 2 处纯文字 URL（非超链接）+ 文末列出 2 个 URL | 纯文字 URL | 微信读书官方/GitHub |

**总结：**
- 全部 6 篇正文均无可点击的 `<a href>` 外链（微信公众号限制外链，符合平台规则）
- 参考链接一律以纯文字 URL 形式出现在文末或列表中
- 无任何链接样式（无下划线、无特殊颜色）可统计

#### 内部特殊链接

C 篇表格中使用 `<code>` 标签展示命令，包含形如 `claude agents`、`claude --bg "task"` 等，不是超链接。

---

### 8. 代码块 / 行内代码

#### 行内代码 `<code>`

| 篇 | `<code>` 出现次数 | 内容类型 |
|----|-----------------|---------|
| A  | 2 | 命令名（`claude`、`claude-qwen`） |
| B  | 0 | — |
| C  | 约12次 | 命令行操作（`claude agents`、`claude --bg "task description"`、`/bg`、`claude respawn --all`、`/loop`、`.claude/worktrees/<会话名>/`、`login.py`、`cp`等） |
| D  | 0 | — |
| E  | 0 | — |
| F  | 0 | — |

行内 `<code>` 无独立样式声明（继承平台默认等宽字体），未见自定义背景色。

#### 代码块 `<pre><code>`

| 篇 | 出现次数 | 内容 | 样式 |
|----|---------|------|------|
| F  | 1 | 微信读书统计数据快照（5行，书架2078本/阅读1671小时等） | 见下 |
| 其余 | 0 | — | — |

F 篇代码块 CSS：
```css
/* pre 外层 */
background: linear-gradient(to bottom, #2a2c33 0%, #383a42 8px, #383a42 100%);
padding: 0;
border-radius: 6px;
overflow: hidden;
margin: 24px 0;
box-shadow: 0 2px 8px rgba(0,0,0,0.15);

/* code 内层 */
color: #abb2bf;  /* 亮灰色文字 */
font-family: "SF Mono", Consolas, Monaco, "Courier New", monospace;
font-size: 14px;
line-height: 1.7;
display: block;
padding: 16px 20px;
```
视觉：深色主题代码块（深灰底 + 亮灰字），类似 One Dark 配色。

**总结：代码块极少见，仅 F 篇出现 1 次，用于展示数据快照（非真正代码）。行内代码仅 C 篇大量使用（命令行教程场景）。**

---

### 9. 表格

| 篇 | 表格数量 | 用途 | 样式特征 |
|----|---------|------|---------|
| A  | 1 | 4 本橙皮书对应关系（3列：橙皮书/主题/现在的含义） | 渐变表头背景（橙绿渐变 rgba），行分隔线 rgba(193,95,60,0.1) |
| B  | 0 | — | — |
| C  | 2 | 1. 打开Agent View的操作方式（2列：动作/命令）；2. 三个概念区分（3列：层/是什么/服务对象） | 同 A 篇样式 |
| D  | 0 | — | — |
| E  | 0 | — | — |
| F  | 1 | huashu-weread 4个workflow（2列：名字/干什么） | 红色表头（#d32f2f），行分隔线 #e0e0e0 |

**表格统一 CSS（A/C 篇）：**
```css
width: 100%;
margin: 24px 0;
border-collapse: collapse;
font-size: 16px;
border-radius: 8px;
overflow: hidden;

/* thead th */
background: linear-gradient(135deg, rgba(193,95,60,0.08) 0%, rgba(157,200,141,0.08) 100%);
padding: 12px 16px;
font-weight: 600;
color: #2b2b2b;
border-bottom: 2px solid rgba(193,95,60,0.2);

/* tbody td */
padding: 12px 16px;
border-bottom: 1px solid rgba(193,95,60,0.1);
color: #2b2b2b;
```

**F 篇表格 CSS（红色主题）：**
```css
/* thead th */
background-color: #d32f2f !important;
color: #fff !important;
padding: 10px 14px;
font-weight: 600;

/* tbody td */
padding: 10px 14px;
border-bottom: 1px solid #e0e0e0;
color: #1a1a1a;
```

**总结：表格出现 3/6 篇，共 4 个。均为 2-3 列的小型对照/说明表，无大型数据表格。**

---

### 10. 图片与图说（Caption）

#### 图片样式（全篇统一，A/B/C/D/E 篇）

```css
max-height: 500px !important;
height: auto;
display: block;
margin: 24px auto;
border-radius: 10px;
box-shadow: 0 6px 24px rgba(193, 95, 60, 0.1);  /* 橙色阴影 */
```

F 篇图片（红色主题）：
```css
max-height: 500px !important;
border-radius: 6px;
border: 2px solid #d32f2f;  /* 红色描边 */
box-shadow: 0 4px 12px rgba(211, 47, 47, 0.12);
```

#### 图说（Alt 文字）

微信公众号图片无可见 caption 标签。所有图片的「图说」通过 `alt` 属性实现，在网页渲染中不显示为可见文字，但 HTML 中存在且极详细：

| 篇 | 有 alt 描述的图片数（估算） | alt 内容风格 |
|----|------------------------|------------|
| A  | 约10张 | 描述图内容（「Artificial Analysis 推文，Qwen3.7-Max 在 Intelligence Index 上拿到 56.6 分」） |
| B  | 约4张 | 插画描述（「红皇后插画：爱丽丝和红皇后手牵手在国际象棋棋盘上拼命奔跑」） |
| C  | 约6张 | UI 截图描述（「Claude Code使用分析dashboard：131亿token…」） |
| D  | 约5张 | 流程图/截图描述（「Mavis的流水线·两个AI互相挑刺,调度程序在中间」） |
| E  | 约5张 | 无 alt（data-src 有但 alt 未填） |
| F  | 约4张 | 截图描述（「微信读书官方 skill 首页」「从「我要怎么把事做对」到「这个世界到底是怎么运转的」：5269 条划线 7 年主题地图」） |

**总结：无可见图注标签（无 figcaption）。图说信息依赖 alt 属性，不在渲染页面显示。**

---

### 11. 全文底色与版面容器

所有 6 篇正文容器统一 CSS（F 篇略有差异）：

**A/B/C/D/E 篇：**
```css
section[data-pm-slice] {
  background-color: #faf9f7 !important;  /* 极浅米白 */
  padding: 20px 24px 40px 24px;
  max-width: 700px;
  margin: 0 auto;
  box-sizing: border-box;
}
```

**F 篇：**
```css
section[data-pm-slice] {
  background-color: #fff !important;  /* 纯白 */
  padding: 16px 12px 36px 12px;  /* padding 更小 */
  max-width: 700px;
  margin: 0 auto;
}
```

**正文段落统一 CSS（5 篇）：**
```css
margin: 20px 0 !important;
line-height: 1.8 !important;
color: #2b2b2b !important;
font-size: 17px;
letter-spacing: -0.005em;
```

**F 篇段落 CSS（略有不同）：**
```css
margin: 18px 0 !important;
line-height: 1.85 !important;
color: #1a1a1a !important;
/* font-size 未指定 */
```

---

### 12. 视频嵌入 iframe

| 篇 | iframe（视频）数量 |
|----|-----------------|
| A  | 2（女娲跑完视频 + 宣传动画视频） |
| C  | 1（Agent View 演示视频） |
| F  | 1（weread skill 安装演示） |
| 其余 | 0 |

均为微信内嵌视频格式 `mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl`。

---

## 关键发现

1. **加粗是最核心的排版手段**：每篇约 14 处 `<strong>`，橙色底+橙色文字组合，用于标记论断句、核心概念、数字。这是花叔排版的最高频操作，6/6 篇全用。

2. **标题体系在篇与篇之间不统一**：B 篇用汉字数字 H2（一/二/三）、E 篇升格用 H1（一~七）、C 篇用 H3（一/二/三/四）、F 篇完全改用红色色块 banner。标题风格随选题调整，无固定模板锁死。

3. **分割线极克制**：6 篇仅 3 篇出现 `<hr>`，且每篇只用 1 次，固定位置在文章正文结束处（作为「正文结束符」，将正文与尾部链接分开）。不用分割线分章节。

4. **emoji 完全缺席**：6 篇正文及标题均无 emoji，与国内大量 AI 公众号依赖 emoji 装饰的风格形成鲜明对比。

5. **引用块（blockquote）几乎不用**：6 篇中仅 A 篇出现 1 次，用于展示 AI 角色扮演的输出片段，其他篇均无引用块。他人话语通过 `<strong>` 高亮或直接嵌入正文段落来呈现。

6. **表格为说明工具，不为数据展示**：4 个表格均为 2-3 列的对照说明表（操作方式、概念区分、功能对比），无数据统计表、无多行数值表。

7. **F 篇（微信读书）是异类**：主色从橙色 #C15F3C 切换为红色 #d32f2f，容器背景从米白 #faf9f7 换为纯白 #fff，标题从渐变文字换为色块 banner，`<strong>` 文字颜色跟随变为深红。推测该篇使用了不同的排版模板。

8. **代码块仅 F 篇出现 1 次**，且是用来展示数据快照（非代码），采用 One Dark 深色配色。行内 `<code>` 仅 C 篇（命令行教程）密集出现（约12次）。

---

## 不确定的地方

- `<strong>` 次数通过目视统计，误差约 ±2 次/篇。
- F 篇是否与其他 5 篇「同一模板体系」存疑：颜色体系完全不同，不排除该篇使用了独立排版主题。
- alt 属性图说的详细程度因篇而异，E 篇部分图片 alt 未填，可能是原始制作时遗漏，无法确认是否有意为之。
- 正文中 `<section>` 包裹图片与段落的层级结构在各篇间略有差异（部分段落用 `<p>`，部分用 `<section>`），本报告以可见语义元素为统计基准，未深入区分 section/p 差异。
