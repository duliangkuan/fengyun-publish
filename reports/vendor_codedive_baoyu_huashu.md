# 深读报告:baoyu-skills + huashu-md-html

> 生成时间:2026-05-24  
> 深读 agent:claude-sonnet-4-6  
> 覆盖文件:baoyu-skills 17 个关键文件 + huashu-md-html 12 个关键文件

---

## 1. 架构概览

### baoyu-skills

| 维度 | 详情 |
|---|---|
| 项目入口 | Claude Skill 触发(`baoyu-markdown-to-html`/`baoyu-post-to-wechat`/`baoyu-format-markdown`),每个 SKILL.md 定义工作流 |
| 主题定义 | 主题名写在 SKILL.md 表格里(default/grace/simple/modern),颜色(13个预设)通过 `--color` 参数传入 `baoyu-md` npm 包 |
| 主题切换 | 三层优先级:CLI `--theme` → EXTEND.md `default_theme` → 交互问询;跨 skill 共享:post-to-wechat 会读 markdown-to-html 的 EXTEND.md 作为 fallback(SKILL.md L81-83) |
| 渲染主体 | TypeScript + Bun,实际渲染由内部 `baoyu-md` npm 包承担(未开源),main.ts 是 thin wrapper |
| 配置系统 | EXTEND.md 三优先级路径:项目级 → XDG → 用户 Home,YAML 格式(解析在 wechat-extend-config.ts) |
| 发布模式 | 3 种:browser(Chrome CDP)/ API(直连)/ remote-api(SSH SOCKS5 隧道绕过微信 IP 白名单) |

核心亮点:

- **SSH SOCKS5 隧道**:wechat-remote-publish.ts 动态找空闲端口 → spawn SSH → 等待 SOCKS 就绪 → 路由所有微信 API 请求 → 结束后 kill 进程。完整的 TCP 端口探活 + 超时机制(L120-153)
- **--cite 底部引用**:外链 → 上标数字 + 底部引用链接列表,微信公众号友好。mp.weixin.qq.com 域名不转换(SKILL.md L93-98)
- **多账号 accounts: 块**:EXTEND.md 支持数组,per-account credentials + Chrome profile 隔离(wechat-extend-config.ts L8-44)
- **--dry-run**:渲染 + 元数据解析但不推送,输出 JSON 供调试(wechat-api.ts L703-714)
- **图片去重上传**:uploadedBySource Map 缓存 imagePath → UploadResponse,同一图片只上传一次(wechat-api.ts L217-228)
- **baoyu-format-markdown**:两阶段格式化:Claude 负责内容分析+结构优化(Step 1-5),TypeScript 脚本负责机械 typography(Step 6:CJK 标点/间距/引号)

### huashu-md-html

| 维度 | 详情 |
|---|---|
| 项目入口 | Python CLI 脚本 4 个:`any_to_md.py` / `md_to_html.py` / `html_to_md.py` / `md_to_docx.py` |
| 主题定义 | 每个主题是独立目录:`templates/<name>/theme.css` + 可选 `template.html5`,自包含单 CSS 文件不依赖 CDN |
| 主题切换 | CLI `--theme article|report|reading|interactive|wechat`,默认 article |
| 渲染主体 | Pandoc 二进制(外部工具),Python 负责前处理+后处理+图片内联 |
| wechat 主题 | templates/wechat/ 是唯一为公众号设计的主题,template.html5 内嵌 JS 做 inline style 复制 |
| 反 AI slop | references/anti-ai-slop.md 12 条强检查单:禁紫渐变/emoji 图标/圆角卡片+左border/霓虹色/#0D1117 深蓝底/SVG 人物 |

核心亮点:

- **wechat 主题的 JS inline 化**:template.html5 里的 JS 在点击「复制到公众号」时:①给 h2 注入真实 `<span class="h2-num">` 数字(不用 CSS ::before 避免微信过滤);②给 ul 的 li 注入 `<span class="bullet">—</span>`;③`getComputedStyle` 遍历所有元素把 CSS 变量解析后写入 inline style(template.html5 L51-125)
- **两模式架构**:兜底模式(Pandoc 一条命令,5 秒,不耗 token)+ 视觉设计师模式(AI 读懂内容推荐 3 个方向)
- **图片三选一策略**:`--inline-images`(base64 自包含)/ `--copy-images`(拷贝到输出目录)/ 默认(相对路径不动)(md_to_html.py L62-72)
- **reading 主题的设计哲学**:19px 大字 + 1.85 行高 + 680px 窄体 + 暖米色底 + `·   ·   ·` 三点分割符(reading/theme.css L9-31,L269-275)
- **反 slop 体系化**:design-tokens.md 定义黑名单 10 条,anti-ai-slop.md 7 条硬禁令 + 5 条软原则 + 输出前检查表

---

## 2. 关键文件深读

### baoyu-markdown-to-html

#### SKILL.md 要点

**文件**:`vendor/baoyu-skills/skills/baoyu-markdown-to-html/SKILL.md`

- Step 0 中文检测:检测 CJK 字符 → 询问是否先跑 `baoyu-format-markdown`(L52-69)
- 主题解析四级优先链:CLI → 本 skill EXTEND.md → post-to-wechat EXTEND.md → 问询(L74-87)
- 13 个颜色预设含 Hex:orange `#D97757`(modern 默认),red `#A93226`,vermilion `#FA5151`(L130-146)
- frontmatter 支持:`title`/`author`/`description`,自动 fallback 到第一个 H1/H2/文件名(L226-237)

#### 主题切换机制

**文件**:`vendor/baoyu-skills/skills/baoyu-markdown-to-html/scripts/main.ts`

核心流程(L43-134):
1. `parseFrontmatter(content)` 分离 frontmatter + body
2. `replaceMarkdownImagesWithPlaceholders(body, "MDTOHTMLIMGPH_")` 图片占位符化
3. `renderMarkdownDocument(rewrittenMarkdown, options)` — 实际调用 baoyu-md 包渲染(L83-96)
4. 输出 JSON 包含 `htmlPath`/`title`/`summary`/`contentImages`(图片信息数组)(L126-133)

**与我们的差异**:baoyu 渲染完后图片仍是 placeholder,由 post-to-wechat 二次上传替换 URL;我们 layout_rules.py 直接内联 img src。

#### EXTEND.md 三层优先级链

路径优先级(SKILL.md L38-47):
1. `.baoyu-skills/baoyu-markdown-to-html/EXTEND.md` — 项目级
2. `$XDG_CONFIG_HOME/baoyu-skills/baoyu-markdown-to-html/EXTEND.md` — XDG
3. `$HOME/.baoyu-skills/baoyu-markdown-to-html/EXTEND.md` — 用户 Home

跨 skill fallback(SKILL.md L81-83):本 skill 没设 default_theme 时读 post-to-wechat 的 EXTEND.md。

---

### baoyu-post-to-wechat

#### SKILL.md 关键字段

**文件**:`vendor/baoyu-skills/skills/baoyu-post-to-wechat/SKILL.md`

- `need_open_comment`/`only_fans_can_comment` 控制评论权限,通过 EXTEND.md 持久化(L54-61)
- 封面图 fallback 链:CLI `--cover` → frontmatter(coverImage/featureImage/cover/image) → `imgs/cover.png` → 内容首图(SKILL.md Step 3 L186)
- markdown 输入默认开 `--cite`(外链转底部引用),HTML 输入不转(SKILL.md L191-193)

#### SSH SOCKS5 隧道实现

**文件**:`vendor/baoyu-skills/skills/baoyu-post-to-wechat/scripts/wechat-remote-publish.ts`

```
findFreePort() → buildSshArgs() → spawn("ssh", [..., "-N", "-D", port]) → waitForSocksReady() → createSocksClient()
```

- 动态端口:TCP bind 0 找空闲端口(L120-138)
- SSH 参数:`-N -T -D 127.0.0.1:PORT -o ExitOnForwardFailure=yes -o ServerAliveInterval=30`(L90-117)
- SOCKS 就绪探活:150ms 轮询 TCP connect,超时抛 Error(L140-153)
- 优雅关闭:SIGINT/SIGTERM/SIGHUP 全部接管 → kill SSH 子进程(L224-232)

**对我们的意义**:我们现在直接调微信 API 需要本机 IP 在白名单。如果上云后 IP 变,这个方案直接复用。

#### 微信 API 图片上传去重

**文件**:`vendor/baoyu-skills/skills/baoyu-post-to-wechat/scripts/wechat-api.ts`

```typescript
const uploadedBySource = new Map<string, UploadResponse>();  // L196
// 同一 imagePath 只上传一次
let resp = uploadedBySource.get(imagePath);
if (!resp) {
  resp = await uploadImage(imagePath, accessToken, baseDir, "body", client);
  uploadedBySource.set(imagePath, resp);  // L217-219
}
```

封面图 fallback 到首张内文图(L759-761):如果没有 `--cover` 也没 frontmatter 封面,用内文第一张图的 `material` media_id 作封面。

---

### huashu-md-html

#### SKILL.md 要点

**文件**:`vendor/huashu-md-html/SKILL.md`

- 4 能力决策树 + URL 双路分流(L12-43)
- 核心审美底线表(L45-53):6 类 必须/禁止对照
- 两模式说明:兜底(不耗 token)vs 设计师模式(AI 介入,L143-154)
- 异常处理表 8 条,所有依赖缺失明确提示安装命令(L341-352)

#### wechat 主题 CSS

**文件**:`vendor/huashu-md-html/templates/wechat/theme.css`

关键设计决策(行号对应):

| 决策 | 位置 | 内容 |
|------|------|------|
| 字体 | L19 | `"Songti SC"` 宋体系列,无 web font 依赖 |
| 纸底 | L16 | `#f8f3e7` 暖米色(比我们的 #FAF9F5 更黄暖) |
| H2 编号 | L157-167 | `.h2-num` 真 span,terracotta 色 |
| strong 背景 | L196-200 | `linear-gradient(to bottom, transparent 62%, #f3deb6 62%)` 下划线高亮效果 |
| ul bullet | L249-255 | `.bullet` 真 span,值为「—」,terracotta 色 |
| hr 分割 | L349-354 | 30% 宽,高度 1px,不是 `::after` 内容 |
| 纯黑背景代码块 | L283-288 | `#2a2622` 暖黑,不是 #0D1117 |

#### wechat 主题 template.html5 JS 部分

**文件**:`vendor/huashu-md-html/templates/wechat/template.html5`

这是整个项目最值得学的工程:

1. **DOM 后处理(L57-80)**:渲染后 JS 遍历 h2/li,注入真实 span(非 CSS 伪元素)确保微信粘贴存活
2. **inline style 白名单(L84-98)**:28 个精选 CSS 属性,避免完整 `getComputedStyle` 污染
3. **剪贴板写入三级 fallback(L181-224)**:现代 `ClipboardItem` → `navigator.clipboard.writeText` → 旧式 `execCommand('copy')`
4. **隐藏 DOM 复制技巧(L127-136)**:克隆 article 到 `left:-99999px` 的隐藏节点再 `getComputedStyle`,避免修改可见页面

#### reading 主题设计

**文件**:`vendor/huashu-md-html/templates/reading/theme.css`

签名细节(L269-275):
```css
hr::after {
  content: "·   ·   ·";
  color: var(--color-ink-mute);
  letter-spacing: 0.6em;
  font-size: 1.2em;
}
```

我们的分割符是 `· · ·`(layout_rules.py L91),几乎相同但 CSS 实现方式不同(我们用 Python 生成 `<p>`,他们用 `::after`)。

#### 反 AI slop 体系

**文件**:`vendor/huashu-md-html/references/anti-ai-slop.md`

7 条硬禁令详细展开(带 CSS 反例):
1. 紫渐变 `linear-gradient(135deg, #667eea, #764ba2)` — AI 默认"科技感"
2. Emoji 作系统图标
3. 圆角卡片+左 border 组合(带 CSS 反例)
4. `#0D1117` 深蓝底
5. 赛博霓虹
6. Inter/Roboto 打天下(标题正文同字族)
7. SVG 手画人物

检查表 12 项(L202-213)每次输出 HTML 前必过。

---

## 3. 跟我们 fengyun-publish 的设计对比

| 维度 | 我们(fengyun-publish) | baoyu-skills | huashu-md-html | 谁更好 + 为啥 |
|------|------|------|------|------|
| **主题数** | 2(默认风云 + huashu 逆向) | 4 主题 × 13 色 = 52 种组合 | 5 主题(article/report/reading/interactive/wechat) | baoyu 灵活性最高;我们专一精准 |
| **配置持久化** | frontmatter 每次手填 `style: huashu` | EXTEND.md 三级优先链,跨 skill 共享 | CLI `--theme` 无持久化 | baoyu 最优;我们缺 "一次设好下次不问" 机制 |
| **主题切换粒度** | frontmatter `style`/`theme` 字段 | CLI `--theme` + `--color` 独立控制 | CLI `--theme` | 我们的 frontmatter 方式跟 baoyu CLI 等效 |
| **渲染引擎** | 自写 Python 逐行解析 | baoyu-md npm 包(TypeScript,闭源) | Pandoc 二进制 | huashu 最稳(Pandoc 工业级);我们最灵活可控 |
| **图片处理** | 内联 img src 直接写入 HTML | placeholder → 上传微信 → 替换 URL | base64 内联 / 复制 / 相对路径三选一 | baoyu 对微信最正确(URL 必须是微信 CDN) |
| **微信发布** | Python urllib + 直连 API | TypeScript + 3 模式(API/Browser/SSH) | 无发布(只生成 HTML) | baoyu 最完整;SSH 隧道我们尚未有 |
| **微信粘贴友好** | 无(直接 API 推草稿) | API 模式无需粘贴;Browser 模式用剪贴板 | wechat 主题有完整 inline style JS | huashu wechat 主题可作「本地预览+手动粘贴」补充方案 |
| **lint 体系** | fengyun_lint.py(R1-R25)+ huashu yaml | 无专门 lint | references/anti-ai-slop.md(12 条 checklist) | 我们最系统;huashu 的哲学可补充我们的黑名单 |
| **frontmatter 字段** | `style`/`theme`/`article_type`/`cover`/`title`/`author` | `title`/`author`/`description`;CLI 参数控制样式 | `title`/`author`/`date`/`eyebrow`/`subtitle` | 字段名略有出入,`eyebrow`(眉标)我们没有 |
| **--cite 底部引用** | 无 | baoyu-markdown-to-html/post-to-wechat 都支持 | 无 | baoyu 独有,微信友好 |
| **多账号** | 单账号 .env | EXTEND.md accounts: 块,per-account credentials | 无 | baoyu 多账号方案成熟 |
| **CJK spacing 修正** | 无 | baoyu-format-markdown scripts/autocorrect.ts | 无 | baoyu 有;我们缺 |
| **反 slop 哲学** | fengyun_lint.py 部分覆盖 | 无 | anti-ai-slop.md 12 条系统化 | huashu 最系统;我们应该对标 |
| **图片 dry-run** | 无 | `--dry-run` 只渲染不发布(wechat-api.ts L703) | 无 | baoyu 有;调试用途高 |

---

## 4. 可复用清单(精筛 9 个)

| # | 项 | 来源文件 + 行号 | 目标(我们的文件+接入点) | 改动量 | 价值 |
|---|---|---|---|---|---|
| 1 | **SSH SOCKS5 隧道绕 IP 白名单** | `scripts/wechat-remote-publish.ts` L48-274 | `tools/post_fengyun_publish.py` — 在 `fetch_access_token()` 前加 `withSshTunnel()` | 大(Python 重写) | 高——上云后必需;阿里云轻量 IP 固定正好配 |
| 2 | **EXTEND.md 三级优先配置链** | `skills/baoyu-post-to-wechat/SKILL.md` L38-53;`wechat-extend-config.ts` L103-225 | 新建 `tools/fengyun_config.py`:EXTEND.md → `.env` → CLI 的优先链 | 中 | 高——解决「每次手填 frontmatter style」问题 |
| 3 | **huashu wechat JS inline-style 复制** | `templates/wechat/template.html5` L51-226 | `tools/layout_rules_huashu.yaml` + 新 `tools/render_wechat_preview.py`:生成带 copy-bar 的 HTML | 中 | 高——提供「预览+粘贴」通道,补充 API 推送不够时的备用 |
| 4 | **图片上传去重 Map** | `scripts/wechat-api.ts` L196-228 | `tools/post_fengyun_publish.py` `upload_image()` 附近 | 小(加 dict cache) | 中——当前同一图片可能多次上传,加 10 行 dict 去重 |
| 5 | **封面 fallback 到首张内文图** | `scripts/wechat-api.ts` L731-761 | `tools/post_fengyun_publish.py` 封面逻辑段 | 小 | 中——省去每次 `--cover` 参数 |
| 6 | **--dry-run 模式** | `scripts/wechat-api.ts` L703-714 | `tools/post_fengyun_publish.py` argparse 增加 `--dry-run` | 小(10 行) | 中——本地调试大幅提速 |
| 7 | **huashu strong 下划线高亮** | `templates/wechat/theme.css` L196-200 | `tools/layout_rules_huashu.yaml` template_A strong 配置段 | 小(改 strong CSS) | 中——比纯色背景更精致;需测试微信渲染兼容性 |
| 8 | **anti-ai-slop 12 条检查表移植到 lint** | `references/anti-ai-slop.md` L202-213 | `tools/fengyun_lint.py` 新增 R26-R37 规则段 | 中 | 中——把哲学转化为可执行规则,防止 AI 输出的 slop 漏过 |
| 9 | **`--cite` 外链转底部引用** | `skills/baoyu-markdown-to-html/SKILL.md` L89-98 | `tools/layout_rules.py` `render_to_wechat_html()` 新增 `cite=True` 模式 | 中 | 中——微信不渲染 http 外链,底部引用更友好;仅对 thought_essay 型文章有价值 |

---

## 5. 不建议引入(理由)

| 项 | 来源 | 不引入原因 |
|---|---|---|
| **Pandoc 作为主渲染引擎** | huashu-md-html md_to_html.py | Pandoc 是外部二进制依赖,Windows 安装麻烦;且我们的 layout_rules.py 已经是自写 Python,迁移成本远超收益。Pandoc 输出的 HTML 结构跟微信内联样式需求不完全吻合 |
| **baoyu-md npm 包** | baoyu-markdown-to-html scripts/main.ts | 未开源的 npm 包,TypeScript 生态 vs 我们的 Python 生态;bun 在 Windows 支持有限。且 baoyu-md 内部样式与我们的品牌色体系可能冲突 |
| **Browser 模式(Chrome CDP)** | baoyu-post-to-wechat wechat-browser.ts | 需要本机 Chrome + Accessibility 权限 + 剪贴板权限;我们已有 API 模式工作正常,引入 CDP 增加复杂度和维护负担 |
| **baoyu-format-markdown 全套** | skills/baoyu-format-markdown SKILL.md | 6 步骤工作流里 Step 2-5 是 AI 内容重写(改结构/bold/heading),跟我们「迭代机制不改单篇」的 P0 原则冲突;Step 6 的 autocorrect.ts 是 TypeScript,Python 有等效的 `autocorrect` 库可替代 |
| **huashu docx 能力** | scripts/md_to_docx.py | 我们的终点是公众号 HTML,docx 出版能力对我们没有应用场景 |

---

## 6. 整体洞察

**baoyu 最大的架构启发是「placeholder 两段式流水线」**。baoyu-markdown-to-html 渲染时把图片替换成 `MDTOHTMLIMGPH_N` 占位符,JSON 输出携带图片元信息;post-to-wechat 消费这份 JSON,把每张图上传到微信 CDN 后再替换 URL。这个解耦设计让渲染层完全不需要知道发布目标是什么——同一份 HTML 可以走 API、Browser 或任何第三方。我们现在 layout_rules.py 把渲染和样式耦合在一起,未来如果要支持「同一篇文章发多个平台」就会很痛。

**huashu 最大的工程亮点是 wechat theme 的 JS inline 化**。微信编辑器粘贴 HTML 时会过滤 CSS class 和 CSS 变量,只保留 style attribute 里的具体值。huashu 的解决方案是在点击「复制」时动态调用 `getComputedStyle` 把所有计算后的 CSS 值写入 inline style,然后把这份 HTML 写入剪贴板。这是目前见过的最干净的解决方案——不依赖任何第三方服务,纯浏览器端。我们的 API 推草稿路线不需要这个,但如果未来要提供「离线预览+手动粘贴」的 fallback,直接抄 template.html5 L51-226 即可。

**两个项目共同验证了「反 AI slop」的可执行化**。huashu 的 anti-ai-slop.md 把审美底线变成 12 条可 checklist 的规则(禁 #0D1117/紫渐变/emoji 图标/圆角卡片+左border);baoyu 的 format-markdown 则把 CJK 标点/间距问题变成可运行的 TypeScript 脚本。这两个项目都在做的事情就是:把人的审美直觉转化成机器可执行的代码。我们的 fengyun_lint.py(R1-R25)走的是同一条路,但缺少 huashu 的视觉维度(颜色/字体/容器)覆盖。**建议把 huashu anti-ai-slop.md 的 12 条检查表映射到 R26-R37**,让 lint 覆盖从「内容语言」扩展到「视觉呈现」。
