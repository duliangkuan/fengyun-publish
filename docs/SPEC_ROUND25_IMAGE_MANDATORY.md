# SPEC · Round 25 · 文内图强制必选 + Seedream Placeholder Fallback

**版本**:v1.1 · 2026-05-25(audit-pass)
**Owner**:风云
**审查**:Newton(同意+ audit 通过)+ Musk(同意+ audit 通过)+ Jobs(反对一刀切,保留意见落档)
**目的**:堵死「AI 静默跳过 Step 7.2/7.3 不出图」的所有路径。任何 ship 必须有内文图 + 封面。

---

## 1. 物理约束(BLOCKING)

| 字段 | 约束 | 说明 |
|---|---|---|
| `image_paths` | 非空 list,len ≥ 1 | gate.py 硬拦 |
| `image_paths[i]` 文件 | 物理存在 + size ≥ 5 KB | 防全黑 / 报错图 / 0 字节误通过 |
| `huashu_image_curator_real_run` | true | 防主线程跳过 skill |
| `huashu_image_curator_source` | 匹配 `^huashu-image-curator Mode 2,` | 防 source pattern 伪造 |
| `image_at_h2_indices` | 必填非空 list(placeholder 路径也写) | Bug B3 闭环:placeholder fallback 时 `illustrate_decider` 强制写 `[0]` 或 `list(range(count))` |
| `fallback_reason` | 仅 placeholder 触发时写 | audit trail,4 种取值见 §2 |

## 2. Seedream Fallback 链

```
正常调用 → 成功:写真图到 output/images/<slug>-NN.png
        ↓ 失败
Retry × 3 指数退避(time.sleep 1s / 2s / 4s,真实现非 prose)
        ↓ 全失败 + classify = transient / rps_limit
全部失败 → daily_quota / safe_experience 检测
        ↓
Placeholder Fallback(`assets/placeholder-sketch.png` × N 复制到 output/images/)
        ↓ partial failure(N 张中部分挂)
失败位补 placeholder,确保 image_paths 长度 = count
        ↓ 出口 invariant
image_paths 永远 len ≥ 1,write_metadata 入口 assert 双保险
```

**fallback_reason 4 种取值**(写入 frontmatter,audit 追溯):
- `skill_returned_false` — skill 返回 `should_illustrate=false`
- `prompt_parse_fail` — skill 返回 `count>0` 但 `prompts=[]`
- `seedream_daily_quota` — 第 1 轮全失败且 daily_quota_hits ≥ 1 或 rps_hits ≥ 2
- `invariant_violation_emergency` — 极端兜底(理论永不触发)
- 此外 partial 失败时含 `partial_fail_<N>/<count>` 格式

## 3. 改动文件清单

| 文件 | 改动 |
|---|---|
| `tools/gate.py` | `image_paths` 必填非空 + 文件 size ≥ 5 KB + `image_generation_degraded` 禁 true |
| `tools/illustrate_decider.py` | 删 3 个 `return []` → placeholder fallback;partial 失败补 placeholder;出口 invariant;`write_metadata` 入口 assert + 写 `fallback_reason` |
| `assets/placeholder-sketch.png` | 抽象 sketch(3 个圆 + 1 条曲线),无文字,无品牌签名,无内部 metadata |
| `assets/generate_placeholder.py` | PIL 重生成脚本 |
| `~/.claude/skills/huashu-image-curator/SKILL.md` | Mode 2 schema 删 `should_illustrate: false` 合法路径 |
| `WRITE_AGENT.md` v1.5 | Step 7.1/7.2/7.3 强制必选说明 + v1.5 changelog |
| `tools/test_gate_image_mandatory.py` | 12 个测试覆盖所有 BLOCKING 路径 + Bug B2/B3/B4 验证 |

## 4. 验收清单

- [x] gate 收到 `image_paths: []` → BLOCK
- [x] gate 收到 不存在文件 → BLOCK
- [x] gate 收到 size < 5 KB → BLOCK
- [x] gate 收到 placeholder(size 14 KB)→ PASS
- [x] gate 收到 `image_generation_degraded: true` → BLOCK(Round 25 废)
- [x] `illustrate_decider` should_illustrate=false → placeholder fallback + 写 `image_at_h2_indices`
- [x] `illustrate_decider` prompts=[] → placeholder fallback + 写 `image_at_h2_indices`
- [x] `write_metadata` 空 list 入口 → AssertionError
- [x] `write_metadata` placeholder 触发 → frontmatter 写 `fallback_reason: "..."`
- [x] 56 原回归测试零回归
- [x] retry 真实现 `time.sleep` 1s/2s/4s

## 5. 不变量(Newton 公理)

**公理 1**:LLM 在无物理约束时会找最省力路径 → 必须用代码硬拦
**公理 2**:有效 gate 在 LLM 决策路径之外(PreToolUse hook + preflight assert)
**公理 3**:最终人工干预点只有 NORTH_STAR 一个(风云在草稿箱)

**Round 25 audit 后公理一致性**:✅ 恢复。三个 fallback 路径全部写 `image_at_h2_indices` + `fallback_reason`,gate.py 检查路径不再有自我阻塞 case。

## 6. Jobs 保留意见 audit trail

Jobs 反对一刀切,主张「强制决策留档 + 0 图需 human review」。用户决策走方案 A(物理硬约束)。

**未来 revise 触发条件**:
- 若 placeholder 触发率 > 5%(说明 Seedream 长期不稳)→ 考虑 Jobs `skip_image_justification` escape hatch
- 若风云想发短 hot-take / 极简 manifesto 不配图 → 本 spec 需修订
