# Round 26 · human_gate 漏洞修复 + 工具补完 SPEC

**日期**: 2026-05-26
**触发**: 2026-05-26 18:05-18:22 E2E 测试(`E2E_TEST_20260526-180544.log`)发现 1/14 FAIL + 5/14 SKIPPED + critic 门控被绕
**主导**: 主线程 / 风云 review
**关联**: [Round 25 image mandatory](SPEC_ROUND25_IMAGE_MANDATORY.md) · [Round 2 critic 门控树共识](../reports/round2_critic_gate_tree.md)

---

## 一、本轮范围(只修 3 件能闭环的事)

| # | 文件 | 问题 | 修法 |
|---|---|---|---|
| **A** | `tools/critic_vote.py` | single-round human_gate 错走 auto_partial_pass 绕过 B reject(L342-346) | human_gate 等同 revise:N<3 → revise;N≥3 → auto_exit |
| **B** | `tools/fix_punctuation.py` | 文件缺失,SKILL.md L49 / L535 仍引用 | 重建为通用 half→full 工具(CLI + import 双入口) |
| **C** | `tools/opening_signal.py` | `_score_reframe` 漏匹配「以为 X,直到 Y」「以为 X,没想到 Y」 | 扩 `REFRAME_PATTERNS` 加 4 个常见模板 |

**不在本轮范围**(下一轮 Round 27 处理):
- gate.py `*_source` 字段防伪升级到独立 receipt 文件协议(改动涉及 6 个 skill 接口,需独立 SPEC)
- ITI Step 1/2 降级 abort 阈值
- 微信 API IP 白名单(用户在公众号后台操作)

---

## 二、漏洞 A 详解:human_gate 被自动放行

### 当前(错):`critic_vote.py:342-346`

```python
if decision == "human_gate":
    # Round 24 新架构:human_gate 不再等真人,直接走自动出口
    return _auto_exit_result(round_info, r18_p1_warnings,
                             r18_p2_warnings,
                             reason + " | gate_tree 判 human_gate → 自动出口")
```

**问题**:`_auto_exit_result` 看到末轮 A ≥ 65 直接 ship。本次 E2E:

```
A=74.2 + B=no-ship + C=ship
→ gate_tree 正确判 human_gate
→ _auto_exit_result(A=74.2 >= 65) → ship ❌
```

B 的 3 个具体改稿点(L23-27 hearsay / L37-47 PR 稿语气 / L95 伪权威)**完全没进 revise loop**。

### 修后(对)

```python
if decision == "human_gate":
    # Round 26:human_gate 必须先 revise,不能跳过改稿循环
    # N<3 → revise(给 writer 1 次以上的修复机会)
    # N>=3 → _auto_exit_result(末轮 A 决定 ship vs abort)
    if last["round"] >= 3:
        return _auto_exit_result(
            round_info, r18_p1_warnings, r18_p2_warnings,
            reason + " | 3 轮仍 human_gate → 自动出口",
        )
    return {
        "decision": "revise",
        "reason": reason + " | human_gate 必须先 revise 至少 1 轮(Round 26)",
        "next_step": f"回 Step 6.5 改稿(round {last['round']+1})",
        "r18_p1_warnings": r18_p1_warnings,
        "r18_p2_warnings": r18_p2_warnings,
        "round_info": round_info,
    }
```

### 设计依据

- **Round 2 锁定的本意**:human_gate = 「B reject 但 A+C 都过线」的灰色地带,需要人工或 revise 解决
- **Round 24 改动的本意**:废除 partial_pass(原本是 A≥60 强行 ship 的兜底),但**只针对「3 轮 revise 仍 revise」**的死循环兜底
- **错误**:Round 24 把 N=1 的 human_gate 也接到 auto_partial_pass,等于把 B reject 的硬否决能力变成「打个折扣的 A 分」
- **修正**:让 human_gate 至少经过 1 轮 revise(用 B 的 brief 改稿)再判 — 与 「revise → N<3」逻辑统一

---

## 三、漏洞 B 详解:`fix_punctuation.py` 缺失

### 当前

- 文件不存在
- 唯一替代 `_fix_quotes.py` 是个**硬编码 path** 的一次性脚本(`D:\Dev\ai-wechat-pipeline\output\drafts\20260525-trapdoor-ai-supply-chain.md`),完全不通用
- `~/.claude/skills/fengyun-publish/SKILL.md:49` 和 `:535` 仍引用 `tools/fix_punctuation.py`
- E2E 测试时只能手动 Python 修复

### 修后

新建 `tools/fix_punctuation.py`:
- 接受 `<draft.md>` 路径,扫描正文(跳过 frontmatter),写回原文件
- 修复规则(R0 半角标点):
  - ASCII `"` 配对 → 中文 `"` `"`
  - ASCII `'` 配对 → 中文 `'` `'`
  - 中文之间的半角 `, . ? ! : ;` → 全角 `,。?!:;`
  - 中文之间的半角 `()` → 全角 `()`
  - 中文之间的半角破折号 `--` / `—` → 全角破折号 `——`
- 提供 `fix_punctuation_text(text: str) -> tuple[str, int]` 函数供 import
- CLI 输出:`Fixed N punctuation marks in <file>`

### 设计依据

- SKILL.md L535 描述:「直接跑 `python tools/fix_punctuation.py <draft>`,会半角→全角并写回原文件」
- [feedback_chinese_native_voice](../../.claude/projects/C--Users-23303/memory/feedback_chinese_native_voice.md) — 中文母语化 P0,全角标点是底线

---

## 四、漏洞 C 详解:`_score_reframe` 漏匹配

### 当前 `tools/opening_signal.py:52-66`

REFRAME_PATTERNS 已覆盖:
- `不是X,是Y` / `原以为X` / `以为X才发现` / `看似X实际` / `表面上X事实` 等

**漏匹配**(本次 R3 开头「你以为...直到」):
- `以为 X,直到 Y` ← 经典 reframe
- `以为 X,没想到 Y` ← 同样高频
- `以为 X,结果 Y` ← 口语化 reframe
- `以为 X,后来才 Y` ← 时间线 reframe

### 修后

`REFRAME_PATTERNS` 加 4 个模式:

```python
r"以为[^。\n]{1,15}直到",
r"以为[^。\n]{1,15}没想到",
r"以为[^。\n]{1,15}结果",
r"以为[^。\n]{1,15}后来",
```

### 设计依据

- [feedback_data_first_design_loop](../../.claude/projects/C--Users-23303/memory/feedback_data_first_design_loop.md):列模式池要验证;**本次只在已有模式池中补漏,不引入新分类**
- 4 个新模式都是经典反差句式,跟现有 `以为X才发现` 同类(已经验证有效)
- 不动 0/1/2/3+ 命中 → 0/5/7/9+ 的评分曲线

---

## 五、测试覆盖

新增 `tools/test_round26_fixes.py`:

1. **critic_vote**:9 个分支(A 缺 / A<60 / C reject / B+C ship / B reject single round 走 revise / B reject 3轮走 auto_exit / A<65 走 auto_abort / B/C skip / aborted_r18)
2. **fix_punctuation**:6 个用例(纯中文不动 / 引号配对 / 中文间逗号 / 中文间句号 / 含代码块跳过 / 含 frontmatter 跳过)
3. **opening_signal reframe**:5 个用例(原有 4 模式回归 + 新增 4 模式命中 + 复合命中加分)

**目标**:全套 74/74(Round 25)+ 新增 20 用例 = 94/94 PASS

---

## 六、不变项(向后兼容)

- gate.py 不动 — 已有的 8 项物理硬约束 + Round 25 image mandatory 全部保留
- WRITE_AGENT.md 不动 — 19 个 BLOCKING step 标记不变
- 其他 skill 不动 — humanizer / 王小波 / huashu-image-curator 接口不动
- 单轮模式 `vote()` 不动 — 只有多轮 `vote_all_rounds()` 在 human_gate 分支改

---

## 七、Round 27 议程(下次开干)

- Receipt 文件协议:humanizer / 王小波 / title harness / ending harness / 三轨 critic / huashu-image-curator 6 个 skill 完成后落 `output/receipts/<slug>/<step>.receipt.json`,gate.py 改读 receipt 验证 `draft_hash` 一致
- ITI Step 1/2 降级 abort 阈值:广搜 < 6 条或 WebSearch + arxiv 都挂 → abort 而非 degraded 跑下去
