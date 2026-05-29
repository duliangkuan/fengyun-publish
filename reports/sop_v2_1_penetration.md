# SOP v2.1 穿透测试报告

*生成时间：2026-05-21 12:11:24*

## 测试设计

- **测试集**：2026 H1 hold-out（617 篇）
- **target**：composite_pct = 0.40·read + 0.20·share + 0.15·like + 0.15·old_like + 0.10·comment
- **v2 baseline**：5 维规则（sop_v2.py，不修改）
- **v2.1**：v2 + style_match_score（第六维, 25% 混合权重）+ viral_ending_strength（share 维度内）
- **阈值来源**：所有新规则阈值均在 pre-2026 训练集上确定，不在 hold-out 上调参

## 新增 Feature 说明

### Feature 1: style_match_score（独立第六维, 重磅）
- 来源：style_match_features.parquet
- 验证：hold-out 4/4 账号正向（ρ=0.27-0.37），赛博禅心 ρ=-0.24（保护性 clip）
- 公式：total = 0.75 × 5维加权 + 0.25 × style_match_normalized
- 赛博禅心保护：raw_score → max(0, raw_score) 避免反向负贡献

### Feature 2: viral_ending_strength（share_score 内）
- 来源：viral_design_features.parquet
- 验证：mean_ρ=+0.235，4/4 跨账号一致，与 SOP v2 重叠 0%
- 规则：≥ 0.667（训练集 q75）→ +5；= 1.0（训练集 q97，顶级）→ +8
  *注：viral_ending_strength 为三档离散值(0.333/0.667/1.0)，q75=q90=0.667，*
  *用 1.0 作为顶级档更能区分真正的强结尾*

## v2 vs v2.1 8 指标对比（2026 H1 hold-out）

| 指标 | SOP v2 (baseline) | SOP v2.1 | 胜者 |
|---|---|---|---|
| R² | -0.471 | **-0.045** 🏆 | SOP v2.1 |
| Spearman ρ | +0.336 | **+0.393** 🏆 | SOP v2.1 |
| MAE (越低越好) | 16.7 | **13.7** 🏆 | SOP v2.1 |
| Top 10% 精度 | **24.6%** 🏆 | 24.6% | SOP v2 |
| Top 30% 精度 | 45.9% | **48.6%** 🏆 | SOP v2.1 |
| Bottom 10% 精度 | **32.8%** 🏆 | 32.8% | SOP v2 |
| 分箱准确率 | 47.5% | **58.3%** 🏆 | SOP v2.1 |
| 预测 std | **8.6** 🏆 | 8.0 | SOP v2 |

**Spearman ρ 提升：+0.057**（v2=+0.336 → v2.1=+0.393）

## style_match_score 在 2026 H1 上独立 ρ

| 账号 | n | ρ | p | 方向 |
|---|---|---|---|---|
| **全 hold-out** | 617 | +0.358 | 0.0000 | ✅ 正向 |
| kazik | 106 | +0.382 | 0.0001 | ✅ |
| baoyu | 167 | +0.320 | 0.0000 | ✅ |
| saiboshanxin（clip 后） | 222 | -0.085 | 0.2094 | ❌ |
| huashu | 122 | +0.581 | 0.0000 | ✅ |

## viral_ending_strength 增量贡献

- vs share_pct: ρ=+0.260
- vs composite_pct: ρ=+0.186
- share_score 被提升文章数: 14/617 (2.3%)

## 赛博禅心(saiboshanxin)专项

| 指标 | SOP v2 | SOP v2.1 | 变化 |
|---|---|---|---|
| n | 222 | 222 | — |
| Spearman ρ | +0.189 | +0.188 | -0.001 |
| style_match <0 占比（clip 掉）| — | 81.5% | — |

**赛博禅心结论：⚠️ 变差**（保护性 clip 将负向 style_match 截为 0）

## 5 篇 Hold-out 文章 v2 vs v2.1 反馈对比

（按 v2.1-v2 总分变化幅度排序，展示新维度作用）

### 样本1: [huashu] 年轻人的第一个爱马仕

- **真实 composite_pct**: 96.5
- **SOP v2  总分**: 53.4  (read=41, share=70, like=56, old_like=59, comment=57)
- **SOP v2.1 总分**: 64.4  (share=70, style_match_norm=97.6)  delta=+11.0
- style_match_score(raw)=0.0799,  normalized=97.6

### 样本2: [baoyu] 效率控必看「什么时候该做Skill?」

- **真实 composite_pct**: 95.5
- **SOP v2  总分**: 52.0  (read=51, share=41, like=69, old_like=51, comment=54)
- **SOP v2.1 总分**: 62.2  (share=41, style_match_norm=92.9)  delta=+10.2
- style_match_score(raw)=0.0656,  normalized=92.9

### 样本3: [kazik] AI，正在吞噬所有软件。

- **真实 composite_pct**: 92.1
- **SOP v2  总分**: 55.5  (read=52, share=62, like=56, old_like=57, comment=53)
- **SOP v2.1 总分**: 65.5  (share=62, style_match_norm=95.8)  delta=+10.0
- style_match_score(raw)=0.0745,  normalized=95.8

### 样本4: [huashu] 三本橙皮书分别在微信读书的不同榜单

- **真实 composite_pct**: 65.8
- **SOP v2  总分**: 45.3  (read=37, share=42, like=53, old_like=56, comment=57)
- **SOP v2.1 总分**: 55.3  (share=42, style_match_norm=85.4)  delta=+10.0
- style_match_score(raw)=0.0423,  normalized=85.4

### 样本5: [kazik] 春节6天，我找到了各个领域最强的大模型。

- **真实 composite_pct**: 91.0
- **SOP v2  总分**: 46.1  (read=38, share=31, like=59, old_like=58, comment=71)
- **SOP v2.1 总分**: 55.9  (share=31, style_match_norm=85.3)  delta=+9.8
- style_match_score(raw)=0.0419,  normalized=85.3

## 综合结论

- v2.1 vs v2 Spearman ρ: +0.336 → +0.393 (+0.057)
- ✅ v2.1 在 hold-out 上 ρ 提升
- style_match_score 独立维度（0.25 权重）
- viral_ending_strength 在 share_score 维度内（阈值 0.667/1.0 来自训练集）
- 输出结构兼容 v2（新增 style_match_score / style_match_normalized 字段，critic skill 无需改动）

## 输出结构（v2.1 新增字段）

```python
{
  # v2 原有字段（完全保留）
  'total_score': float,
  'read_score' / 'share_score' / 'like_score' / 'old_like_score' / 'comment_score': float,
  'rules_triggered': [...],
  'suggestions': [...],
  # v2.1 新增
  'style_match_score': float | None,      # 原始余弦相似度差
  'style_match_normalized': float | None,  # 线性映射到 [0,100]
}
```
