# viral_design 维度验证报告
生成时间: 2026-05-21
训练集: 678 条 (2025-05-21 → 2025-12-31)
Hold-out: 620 条 (2026-01-01 → 2026-06-30)

## A. Feature 重要性表

| Feature | mean_ρ | kazik | baoyu | saiboshanxin | huashu | 4/4? |
|---------|--------|-------|-------|--------------|--------|------|
| viral_ending_strength | +0.235 | +0.141 | +0.269 | +0.135 | +0.393 | ✅ |
| viral_sharing_addr | +0.184 | +0.003 | +0.308 | +0.147 | +0.277 | ✅ |
| viral_call_action | +0.142 | +0.114 | +0.222 | +0.052 | +0.181 | ✅ |
| viral_summary_density | +0.125 | -0.082 | +0.195 | +0.113 | +0.275 | ❌ |
| viral_aphorism_pattern | +0.117 | -0.143 | +0.266 | +0.106 | +0.238 | ❌ |
| viral_transitions | +0.110 | -0.004 | +0.201 | +0.109 | +0.136 | ❌ |
| viral_unexpected_words | +0.085 | +0.073 | -0.001 | +0.112 | +0.156 | ❌ |
| viral_imperative | +0.074 | -0.122 | +0.065 | +0.206 | +0.148 | ❌ |
| viral_quote_punchline | +0.055 | -0.044 | +0.213 | -0.080 | +0.129 | ❌ |
| viral_callback | +0.016 | +0.008 | -0.049 | +0.102 | +0.003 | ❌ |
| viral_quote_density | +0.011 | -0.040 | +0.039 | +0.103 | -0.058 | ❌ |

## B. viral_design_composite 合成分

### 权重公式

```
viral_design_composite = 100 × Σ(weight_i × norm_i)
其中 norm_i = (x_i - train_min_i) / (train_max_i - train_min_i)

  viral_ending_strength: weight = 0.2737
  viral_sharing_addr: weight = 0.2143
  viral_call_action: weight = 0.1660
  viral_summary_density: weight = 0.0732
  viral_aphorism_pattern: weight = 0.0682
  viral_transitions: weight = 0.0644
  viral_unexpected_words: weight = 0.0495
  viral_imperative: weight = 0.0433
  viral_quote_punchline: weight = 0.0318
  viral_callback: weight = 0.0093
  viral_quote_density: weight = 0.0064
```

### Hold-out 性能

- 训练集 ρ = +0.3271 (p=0.0000)
- Hold-out 整体 ρ = +0.2826 (p=0.0000)

| 账号 | hold-out ρ |
|------|------------|
| kazik | +0.226 |
| baoyu | +0.217 |
| saiboshanxin | +0.148 |
| huashu | +0.219 |

### partial R² (SOP v2 增量)

- SOP v2 only R² = -1.1239
- SOP v2 + viral_design R² = -1.1221
- 增量 partial R² = **+0.0018**

## C. 验证结论

| 条件 | 结果 | 达标? |
|------|------|-------|
| 跨账号4/4一致特征数 | 3/11 | ✅ |
| partial R² > 0.005 | +0.0018 | ❌ |
| SOP v2重叠 < 50% | 0.0% | ✅ |

**最终结论: 🟡 部分通过**

### 跨账号4/4一致的特征 (Top)

- `viral_ending_strength`: mean_ρ=+0.235
- `viral_sharing_addr`: mean_ρ=+0.184
- `viral_call_action`: mean_ρ=+0.142

## D. 与 SOP v2 重叠分析

高重叠特征对 (|ρ| > 0.5): 0 对

