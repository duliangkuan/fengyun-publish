# 花叔排版 — 注入风云系统落地方案

**目标**:把 `layout_rules_huashu.yaml` 接入 fengyun-publish 9 步流程,可直接 ship 花叔风格文章。
**前提**:不动现有 layout_rules.py 主逻辑,只**追加**花叔模板分支。
**回滚**:writer 不写 `style: huashu` 即走默认路径,零影响。

---

## 1. 文件结构(7 个改动点 + 2 个新建)

```
D:\Dev\ai-wechat-pipeline\
├── tools\
│   ├── layout_rules.py            ← [改] 加载 yaml 分支
│   ├── layout_rules_huashu.yaml   ← [新] 从 reports/ 复制过来
│   ├── fengyun_lint.py            ← [改] 加 R19-R25
│   └── h2_pattern_check.py        ← [新] R21 专用检测器
├── ~/.claude/skills/fengyun-writer\
│   ├── SKILL.md                   ← [改] 顶部加 style 路由
│   └── references\
│       ├── huashu_rhythm.md       ← [新] 节奏目标 + 翻译句
│       └── h2_patterns.md         ← [新] 三选一模板
└── ~/.claude/skills/fengyun-publish\
    └── SKILL.md                   ← [改] Step 4 加 style 分支,Step 8 加 theme 切换
```

---

## 2. 改动详情(按 Phase 流程顺序)

### Phase A:writer skill 注入(Step 0~4)

#### A1. fengyun-writer SKILL.md 顶部加 style 路由

```markdown
## Style 选择(Step -0.5)

风云写公众号默认走自有 voice。若 frontmatter `style: huashu`,额外加载:
- `references/huashu_rhythm.md` — 段落节奏与翻译句目标
- `references/h2_patterns.md` — H2 三选一

frontmatter 必填字段:
- `style`: voice 默认 / huashu / ...
- 若 huashu:
  - `theme`: A (默认暖橙) 或 B (深红,显式触发)
  - `article_type`: tech_demo 或 thought_essay (决定图密度)
```

#### A2. references/huashu_rhythm.md(新建)

直接抄 `layout_rules_huashu.yaml` 的 `common.rhythm_targets` + `common.opening/closing` + `common.translation_phrases`,转 markdown。

#### A3. references/h2_patterns.md(新建)

抄 `common.h2_patterns`,每种带 5 个示例,标"必从此 3 种之一选出"。

---

### Phase B:lint 接入(Step 5)

#### B1. fengyun_lint.py 加 R19-R25

代码骨架(伪代码,真改时按现有 R0-R18 风格写):

```python
class LintRules:
    R19_avg_paragraph_length = {...}
    R20_solo_line_count = {...}
    R21_h2_pattern_match = {...}
    R22_emoji_zero = {...}
    R23_cta_zero = {...}
    R24_long_paragraph_ratio = {...}
    R25_ellipsis_max = {...}

def scan_huashu_rules(article, frontmatter):
    """只在 frontmatter.style == 'huashu' 时触发"""
    if frontmatter.get("style") != "huashu":
        return []
    issues = []
    # R19-R25 检测
    ...
    return issues
```

整合到现有 `lint_article()` 入口:
```python
def lint_article(article, frontmatter):
    issues = []
    issues.extend(scan_R0_to_R18(article))
    issues.extend(scan_huashu_rules(article, frontmatter))  # 新增
    return issues
```

#### B2. critic_vote 门控树补丁

R22 / R23 fail → 直接 revise,与现有 fail 行为一致。
R19-R21 / R24-R25 warn → 计入 warn 数,达到阈值触发 revise(沿用现有逻辑)。

---

### Phase C:render 接入(Step 8)

#### C1. layout_rules.py 加 yaml 分支

```python
import yaml
from pathlib import Path

def load_huashu_rules():
    yaml_path = Path(__file__).parent / "layout_rules_huashu.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def render_to_wechat_html(markdown, frontmatter):
    style = frontmatter.get("style", "default")
    if style == "huashu":
        return render_huashu(markdown, frontmatter)
    return render_default(markdown, frontmatter)  # 现有逻辑

def render_huashu(markdown, frontmatter):
    rules = load_huashu_rules()
    theme = frontmatter.get("theme", "A")
    template = rules[f"template_{theme}"]
    # 按 template 渲染:body / h2 / strong / img / blockquote / hr
    ...
```

#### C2. post_fengyun_publish.py 加 --style 参数

```python
parser.add_argument("--style", default=None, help="huashu | default")
parser.add_argument("--theme", default="A", help="A | B (仅 huashu)")
parser.add_argument("--article-type", default="thought_essay")
```

#### C3. fengyun-publish SKILL.md Step 8 加分支说明

```markdown
### Step 8 渲染

读取 frontmatter:
- 无 style → 走 default(现有 layout_rules)
- style == "huashu" → 走 layout_rules_huashu.yaml + theme
```

---

### Phase D:测试(Step 9 之前)

新建 `tests/test_huashu_render.py`:

```python
def test_huashu_template_a_matches_5_articles():
    """用 corpus/huashu_layout_reverse/ 的 5 篇 T-A 文章逆向验证"""
    for article_dir in ["AI最大的礼物...", "Claude_Code...", "Mavis...", "Qwen3...", "公司..."]:
        original_html = load(article_dir + "/index.html")
        regenerated = render_huashu(markdown_from(original_html), {"style": "huashu", "theme": "A"})
        assert_css_matches(original_html, regenerated, tolerance_px=2)

def test_huashu_template_b_matches_1_article():
    """篇 6 微信读书的 T-B 验证"""
    ...

def test_emoji_lint_fails_on_emoji():
    assert R22_check("正文 🚀 加 emoji") == "fail"

def test_cta_lint_fails_on_cta():
    assert R23_check("结尾觉得有用就点赞转发") == "fail"
```

测试目标:**渲染产物与原始 6 篇的 CSS 差异 ≤ 2px**(report #6 的一致性边界)。

---

## 3. 部署顺序(P0 → P3)

| 优先级 | 步骤 | 估时 | 不做的影响 |
|---|---|---|---|
| **P0** | 复制 yaml 到 tools/ + writer skill 注入(A1/A2/A3) | 30 min | 风云仍可手工对照 yaml 写,但效率低 |
| **P0** | layout_rules.py 加 yaml 分支(C1) | 1-2 h | 无法机器渲染花叔风格 |
| **P1** | lint R22/R23 fail 规则(B1 子集) | 30 min | 容易写出带 emoji / CTA 的破风格文章 |
| **P1** | post_fengyun_publish.py --style 参数(C2) | 15 min | 风云每次 ship 要改命令 |
| **P2** | lint R19/R20/R21/R24/R25 warn 规则(B1 完整) | 1 h | warn 缺失,critic 投票不全 |
| **P2** | 测试套件(D) | 1-2 h | 信不过新模板,首篇要人工 diff |
| **P3** | T-B 深红模板验证 | 30 min | 显式触发场景少,延后 |

**P0 + P1 合计 ~3-4 小时,可在一晚跑完**。

---

## 4. 风险与回滚

### 风险

1. **现有 default 模板被误触发**:writer 漏写 `style: huashu` → 走 default,无伤害(回退到现有 layout_rules)
2. **T-A 5/6 一致但 1/6 偏离**:篇 6 走 T-B,显式 trigger 已规避
3. **lint R19-R25 误报**:都是 warn 级,critic 投票决定是否 revise,不会卡 ship
4. **fail 级 R22/R23 卡 writer**:这是设计意图(emoji / CTA 必须零),writer 重写即可

### 回滚

如果新分支引入 bug:
- 把 `~/.claude/skills/fengyun-writer/SKILL.md` 的 style 路由块注释掉
- writer 全部走 default voice,**回到 2026-05-24 之前的状态**
- yaml 文件保留,不影响

---

## 5. 验证用例(首篇推荐)

ship 一篇 huashu T-A 风格的文章,主题选:
- **article_type: tech_demo** — 配 4-5 段/图 验证
- **首图必在 300 字内** 验证
- **emoji 0 / CTA 0** lint 通过验证
- **H2 命中 3 种模式** 验证
- **strong 平均 14 处** 验证

ship 后手机端打开,跟 corpus 里 5 篇 T-A 文章肉眼比对,差异 ≤ 2px 视为通过。

---

## 6. 关联文件

- `reports/huashu_layout_phase1/agent[1-6]_*.md` — 6 份调研报告
- `reports/huashu_layout_phase1/debate_and_verdict.md` — 辩论 + 审判官裁决
- `reports/huashu_layout_phase1/layout_rules_huashu.yaml` — 数值规则配置
- 本文 — 落地方案

---

## 7. 沙盒规则遵守证明

- Musk 使用 3/5 调研权(CSS 数值 / 结构组件 / 段落节奏)
- Jobs 使用 3/5 调研权(图文策略 / 开头结尾 / 整体调性)
- 0 次专家召唤(调研已足)
- 0 次女娲蒸馏(无新人物需要)
- 审判官全程监视,**无人偷懒,无警告**
- Musk 安全,可继续航天事业
- Jobs 安全,苹果继续运营
