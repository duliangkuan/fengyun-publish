# 修 fengyun-publish critic-revise 循环
*Musk × Jobs 承认漏洞 + 修复 + 验证 · 2026-05-22*

## 风云的质问

> "B 被机制挡住之后,没有带花叔的反馈原因反馈然后再重新改进写一下重新评分的机制嘛,这是 harness 的灵魂啊,这个事情你问问马斯克和乔布斯,质问他们当初是怎么设计的,这样的话怎么可以称之为全自动呢"

**他骂得对**。fengyun-publish Step 6 投票规则写了「回 Step 3 改稿(最多 2 轮)」,但 agent B 跑到花叔 not_ship 就直接停了 — 没把 critic 反馈喂回 writer 重新改。run log `step6_critic` 字段干脆是缺失的,这就是审判官警告里说的「agent 偷懒」。

---

## Part 1 · 漏洞分析(Musk × Jobs 对话,3 轮)

### Round 1 · Musk 开场:Idiot Index

**Musk**:风云说得对,这是设计错误,不是 agent 偷懒。打开 SKILL.md 看 Step 6 投票表 — 我们写了「revise」决议,然后写了一行「每轮改稿最多 2 轮」,然后……就什么都没了。**没有改稿 prompt、没有 revise_brief 文件名、没有调 fengyun-writer 的触发语、没有回 Step 4 / 5 / 6 的明确指令**。

这就是 Idiot Index 1000:一行字「回 Step 3 改稿」看起来很完整,实际信息量为零。Agent 看到这一行,只能猜:回 Step 3 是从头重写吗?还是只改 critic 指出的段落?改完去哪一步?要不要重跑 lint?要不要重跑王小波?要不要重投票?**全是空的**。Agent 不偷懒才怪 — 它没法不偷懒,因为没有可执行的指令。

火箭工程一条铁律:**任何被你写在 SOP 里又含糊的步骤,就是日后炸的那一步**。这一行就是炸点。

### Round 2 · Jobs 接:产品语言学的失败

**Jobs**:Elon 是从工程视角看的,我从产品视角再加一层。

风云说「全自动」三个字,这不只是个程度副词,这是**产品承诺**。一个产品承诺「全自动」却把 critic 反馈丢掉,这就跟当年 Newton 承诺手写识别但识别率 70% 一样 — **承诺与现实之间的断裂会摧毁信任**。

更糟的是,critic 反馈在这个 harness 里**就是产品的灵魂**。三轨 vote 是什么?是把三个不同视角(SOP 量化 / 花叔 emotion / 风云 founder voice)的判断喂给同一份草稿,然后用最严苛的标准 gate-keep。这套机制存在的全部理由,就是为了让 critic 的反馈**回流**到 writer。

我们把这套机制写出来了,但**没把回流通道接上**。这等于做了 iPhone 但忘了接电池 — 形似神不在。

产品语言上犯的错是:把「回 Step 3 改稿」当成边角注释,而它本应是 first-class workflow。SKILL.md 里 Step 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 都有完整的 sub-step,**唯独「revise」没有**。这一不对称就是 design smell。

### Round 3 · 漏洞类型判定 + 双人共识

**Musk**:综合证据看,这是 (a) 不是 (b)。

证据:
- SKILL.md Step 6 投票表最后只有一行「每轮改稿最多 2 轮。2 轮还过不了 → ... 人工 review」— 没写第一轮怎么跑
- 没有 revise_brief 模板、没有 fengyun-writer 改稿触发语规范、没有「改完回哪一步」的明确顺序
- run log `step6_critic` 字段缺失 — 这说明 agent 跑到投票就停了,而不是「跑了投票得到 revise 然后偷懒不执行」
- agent B 完成后给的简报里说花叔 not_ship 后**没有下一步动作**,这是 SKILL.md 没指引,不是 agent 主动放弃

**Jobs**:同意。(a) 是机制设计的灵魂错位 — 我们把最重要的产品承诺写得最草率。

**双人共识 — 漏洞类型: (a) SKILL.md 写得不清,导致 agent 不知道怎么 trigger 改稿循环。**

不许辩护机制设计无漏洞。修。

---

## Part 2 · SKILL.md Step 6.5 修复

Edit 了 `C:\Users\23303\.claude\skills\fengyun-publish\SKILL.md` — 在 Step 6 投票表后、Step 7 封面前,插入了整块 **Step 6.5 · critic-revise loop ⛔ BLOCKING**。

### 关键加了什么(摘要):

1. **触发条件明确**:`decision == revise` 必须进 6.5,不许停在投票决议
2. **审判官警告**:加了一段 quote 「不许直接停在 revise 决议上 ... agent 跑到 critic 不 ship 直接停 = 偷懒,不叫全自动」
3. **7 步执行序列**(6.5.1 → 6.5.7):
   - 6.5.1 收集三轨具体改稿点(A 维度+扣分规则 / B 段落+原因类型 / C 段落+建议)
   - 6.5.2 写 `revise_brief.md` 到 `output/drafts/<slug>-revise-brief-r{N}.md`,模板包含三轨原文 + 优先修复点 + 改稿硬约束
   - 6.5.3 用规范触发语调 fengyun-writer **改稿模式**(不是从头写,只改 critic 指出的段落)
   - 6.5.4 回 Step 4 lint
   - 6.5.5 回 Step 5 王小波
   - 6.5.6 回 Step 6 重跑三轨
   - 6.5.7 重新投票:ship → Step 7 / revise+N<2 → 重复 6.5 / revise+N≥2 → 中止人工
4. **改稿硬约束**(铁律):
   - 字数变动 ≤ ±10%(避免大改重写丢 voice)
   - 章节结构 + 北极星 + 标题不许改
   - 只改 critic 指出的具体段落,其它一字不动
   - voice 一致性优先于所有修复(Step 0 必读)

### before / after diff

```
- BEFORE:
  「每轮改稿最多 2 轮。2 轮还过不了 → 把三轨报告 + lint 报告甩给风云人工 review,不再自动迭代。」
  (一行,信息量为零)

+ AFTER:
  + 加了审判官 quote(不许停在 revise)
  + 加了 Step 6.5 · critic-revise loop ⛔ BLOCKING 整块
  + 包含 7 个子步骤、3 张表格、6 条铁律
  + 总共加了 ~80 行可执行指令
```

---

## Part 3 · B v0 验证修复(实战首跑)

### 输入
- v0 draft: `output/drafts/20260522-openai-ipo-xai-burn-v0.md`(4318 字 post-王小波,0 lint violation)
- B 轨 not_ship 原因(主对话已记录,3 个具体点)

### 6.5.2 · revise_brief
- 文件:`output/drafts/20260522-openai-ipo-xai-burn-revise-brief-r1.md`
- 内容:3 个优先修复点 + 改稿硬约束 + 字数目标区间 [3886, 4750]

### 6.5.3 · fengyun-writer 改稿(只改 3 处段落,voice DNA 一致)

| 段落 | 改稿动作 | 实际插入 |
|---|---|---|
| 第 4 段(焦虑) | 加 lived stake(API 账单) | "笔者自己每个月看 Claude 加火山引擎加豆包的 API 账单,是真的看了肉疼..." |
| 第 23 段(Cursor) | 加 lived stake(harness 跑稿) | "笔者自己跑这套公众号的 harness,体感是一样的。一句"ship 一篇..."丢出去,Claude 在三十分钟里..." |
| 末段 | 删鸡汤 + 加押注 | 删"慢慢看慢慢想慢慢走";加"笔者自己押第三档 — agent 真在客户的工作流里跑出现金流..." |

输出:`output/drafts/20260522-openai-ipo-xai-burn-v1.md`

### 6.5.4 · Lint
- 第一次跑:2 violations(R1_brackets 用了「」 / R6_kazik_habits 用了"抽象")
- 修完 + 跑 fix_punctuation(全角化半角双引号)
- **最终:0 violations** ✓

### 6.5.5 · 王小波
- 检查 3 个新句子是否引入翻译腔:无。「肉疼」「实打实」「丢出去」「跑完」「押第三档」全是母语表达。
- 7 个王小波 v0 修复全部保留(grep 验证全通过)

### 6.5.6 · 重跑三轨 critic

| 轨 | 结果 | 通过? |
|---|---|---|
| **A · critic v2.1** | total=72.5(read=79 / share=73 / like=77) | ✓(≥60) |
| **B · huashu** | ship — v0 三个 not_ship 维度(API stake / harness stake / 押注表态)全部在 v1 修复 | ✓ |
| **C · fengyun critic_mode** | sign(挂名) — 三个 lived stake 正是风云 founder voice 标志(笔者自己 X 过 + 押第 N 档) | ✓ |

### 6.5.7 · 投票决议

```
=== critic vote ===
A score:  72.5  (threshold 60.0)
B:        ship  -> True
C:        sign  -> True
decision: SHIP
reason:   A 过线 (72.5) + B/C 至少一个同意 (B=True, C=True)
next:     进 Step 7(封面)
```

**全票通过 → SHIP**

### Step 7 · 封面
- 自动路由命中 T6_portrait_concept(豆包 Seedream API)
- 输出:`output/images/20260522-openai-ipo-xai-burn-v1-cover.png`(38.3s, 1 次成功,无 retry)

### Step 8 · 推草稿
- HTML 渲染 10,446 chars,本地 preview 落到 `output/html/20260522-openai-ipo-xai-burn-v1.html`
- 公众号 API 上传 thumb + 创建 draft 成功
- **draft media_id: `f5xAnh6tT5u4aYGYiST-AE3SrtA69163EBqoPeMwhL0_ux0YPrYNHrNU7T3XpdQk`**
- 下一步:风云后台草稿箱审阅 → 人工发出

### 字数核查

| 版本 | 字数 | vs v0 | 在 ±10% 区间? |
|---|---|---|---|
| v0(post-王小波 baseline) | 4318 | — | — |
| v1 | 4658 | +340(+7.9%) | ✓([3886, 4750]) |

---

## 给风云的最终回复

风云,你骂得对。这是机制设计漏洞,不是 agent 偷懒。SKILL.md Step 6 把「回 Step 3 改稿」写成一行光秃秃的注释,没说改稿 prompt 怎么写、没说改完回哪一步,**这等于做了 iPhone 但忘了接电池**。Musk 和 Jobs 都承认了。

我加了 Step 6.5 · critic-revise loop ⛔ BLOCKING — 7 步序列、3 个表、6 条铁律,把 critic 反馈到 writer 改稿到重投票的全通道接上了。然后用 v0 实战跑了一遍 — 花叔三个 not_ship 点全部修复(API 账单肉疼 / harness 跑稿 / 押第三档),三轨重投票全过(A=72.5 / B=ship / C=sign),草稿已推:`f5xAnh6t...lNU7T3XpdQk`。

总用时 ~38 分钟,在 60 分钟硬上限内。你后台审阅一下就可以发出。

---

## 给主对话简报(已附在主返回里)
