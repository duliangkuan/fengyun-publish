# Hook Power 钩子力 验证报告

生成时间: 2026-05-21
训练集: 2025-05-21 → 2025-12-31 (674 条)
Hold-out: 2026-01-01 → 2026-06-30 (617 条)

## A. Feature 重要性表 (训练集单变量 Spearman ρ)

| Feature | kazik | baoyu | saiboshanxin | huashu | mean_ρ | overall_ρ | p-value | 4/4一致? |
|---------|-------|-------|-------------|--------|--------|-----------|---------|---------|
| first_para_first_person_open | +0.202 | +0.126 | +0.071 | +0.032 | +0.108 | +0.147 | 0.0001 | ✅ |
| first_para_emotional_open | +0.045 | +0.018 | -0.051 | +0.166 | +0.045 | +0.008 | 0.8411 | ❌ |
| title_hook_anti_consensus | +0.012 | -0.029 | +0.057 | +0.102 | +0.035 | +0.014 | 0.7249 | ❌ |
| title_hook_emotion | +0.032 | +0.000 | -0.076 | +0.077 | +0.008 | +0.015 | 0.6921 | ❌ |
| title_hook_number_shock | -0.144 | +0.030 | -0.050 | +0.158 | -0.001 | -0.001 | 0.9803 | ❌ |
| title_hook_identity | +0.068 | -0.040 | +0.046 | -0.105 | -0.008 | -0.022 | 0.5763 | ❌ |
| first_para_event_intro | -0.029 | +0.064 | -0.049 | -0.056 | -0.017 | +0.034 | 0.3721 | ❌ |
| title_hook_question | -0.110 | -0.168 | +0.000 | -0.041 | -0.080 | -0.089 | 0.0202 | ❌ |
| first_para_question | -0.140 | -0.115 | -0.106 | -0.096 | -0.114 | -0.104 | 0.0071 | ✅ |
| first_para_chars_normalized | -0.183 | -0.086 | -0.169 | -0.379 | -0.204 | -0.229 | 0.0000 | ✅ |

## B. hook_power_composite 合成分

### 公式 (权重由训练集 |ρ| 标定,不一致特征权重减半)

```
hook_power_composite = 100 × (
    0.3904 × norm(first_para_chars_normalized)
    0.2185 × norm(first_para_question)
    0.2056 × norm(first_para_first_person_open)
    0.0764 × norm(title_hook_question)
    0.0426 × norm(first_para_emotional_open)
    0.0338 × norm(title_hook_anti_consensus)
    0.0167 × norm(first_para_event_intro)
    0.0077 × norm(title_hook_emotion)
    0.0072 × norm(title_hook_identity)
    0.0012 × norm(title_hook_number_shock)
)
```

- **训练集 ρ** = -0.1285 (p = 0.0008)
- **Hold-out ρ** = -0.0280 (p = 0.4868)

### Hold-out 跨账号 ρ

| 账号 | ρ |
|------|---|
| kazik | +0.0484 |
| baoyu | -0.0519 |
| saiboshanxin | -0.1818 |
| huashu | -0.0813 |

### LightGBM partial R² (增量贡献)

| 模型 | hold-out R² |
|------|-------------|
| SOP v2 only | -1.1587 |
| SOP v2 + hook features | -1.1460 |
| **增量 partial R²** | **+0.0127** |

> 注意: 两个模型的 R² 均为负值, 原因是训练集(均值 56.1)和 hold-out(均值 76.9)之间存在显著的分布漂移 — 这是数据本身的特性, 不影响 partial R² 的相对比较结论。partial R²=+0.0127 表示 hook features 对 SOP v2 基线有微弱增量贡献。

### Hook Features 在联合模型中的 Feature Importance

| Feature | Importance |
|---------|-----------|
| first_para_chars_normalized | 49 |
| first_para_question | 29 |
| first_para_first_person_open | 27 |
| first_para_event_intro | 7 |
| first_para_emotional_open | 4 |
| title_hook_number_shock | 3 |
| title_hook_question | 1 |
| title_hook_identity | 1 |
| title_hook_anti_consensus | 0 |
| title_hook_emotion | 0 |

## C. 与 SOP v2 重叠检查

| Hook Feature | 最大相关 (vs SOP v2 代理) |
|-------------|--------------------------|
| title_hook_anti_consensus | +0.207 |
| title_hook_number_shock | +0.994 |
| title_hook_emotion | +0.189 |
| title_hook_identity | -0.059 |
| title_hook_question | -0.087 |
| first_para_event_intro | +0.053 |
| first_para_first_person_open | -0.091 |
| first_para_question | -0.091 |
| first_para_emotional_open | +0.082 |
| first_para_chars_normalized | -0.283 |

**平均重叠度** (|r| 均值) = 0.214
**重叠 < 50%?** ✅ 是

## D. Hold-out 3 个稳健 Feature 验证

对 3 个跨账号 4/4 一致的 feature 单独在 hold-out 验证:

| Feature | hold-out ρ (全局) | kazik | baoyu | saiboshanxin | huashu | 方向一致? |
|---------|------------------|-------|-------|-------------|--------|---------|
| first_para_first_person_open | +0.1204 (p=0.003) | +0.221 | +0.023 | +0.133 | +0.071 | ✅ 4/4 正向 |
| first_para_chars_normalized | -0.1995 (p<0.001) | -0.087 | -0.077 | -0.263 | -0.318 | ✅ 4/4 负向 |
| first_para_question | +0.0507 (p=0.209) | +0.018 | +0.087 | +0.012 | -0.054 | ❌ 3/4 (训练集负向→hold-out 反转) |

**关键发现**: `first_para_question` 在训练集 4/4 负向, 在 hold-out 方向反转为 3/4 正向, 说明该信号不稳定。

## E. 验证结论

**🟡 部分通过**

- 跨账号 4/4 一致 feature: 3/10 个
  - `first_para_first_person_open` (ρ=+0.108 训练 / +0.120 hold-out, **稳健**)
  - `first_para_chars_normalized` (ρ=-0.204 训练 / -0.200 hold-out, **最强信号, 越短越好**)
  - `first_para_question` (ρ=-0.114 训练 / +0.051 hold-out, **方向反转, 不稳定**)
- hook_power_composite hold-out ρ = -0.0280 (近 0, 因合成方向问题被内耗)
- partial R² (vs SOP v2) = +0.0127 (微弱增量)
- 与 SOP v2 平均重叠度 = 0.214 (< 50%)

**结论细节**: hook_power 作为"标题钩子词"的假设基本**不成立** — 标题的反共识词、数字冲击、情绪词、身份认同词、问句等均无跨账号稳健信号。有效信号来自**首段结构层面**:首段越短(相对全文)、首段有第一人称开场, 与爆款正相关; 这两个维度与 SOP v2 现有的 `b_first_para_chars` 部分重叠但方向补充有效, 可作为独立 feature 纳入。

**建议**: 不应整体引入 hook_power_composite; 可单独加入 `first_para_chars_normalized` 和 `first_para_first_person_open` 两个 feature。

## F. 输出文件

- `hook_power_features.parquet`: 2723 行, 13 列

---
*由 hook_power_validation.py 自动生成*