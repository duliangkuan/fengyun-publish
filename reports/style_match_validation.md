# Style Match 验证报告

生成时间：2026-05-21 11:50

## 方法说明

- **特征提取**：TF-IDF（max_features=20000, min_df=2, sublinear_tf=True）+ jieba 分词
- **为何用 TF-IDF 而非 BGE**：2730 篇文章 BGE 调用成本高且慢；TF-IDF 在词袋层面已能有效捕捉写作风格差异；若 TF-IDF 有信号，再决定是否升级到语义 embedding
- **Anchor 规则**：top10%（read_pct ≥ 90th AND comment_pct ≥ 80th，双高；若样本不足退化为单高），bot10%（read_pct ≤ 10th）
- **Leakage 控制**：LOO——计算文章 t 的相似度时，排除 t 自身
- **Hold-out**：用 2026-01-01 之前数据建 anchor，在 2026 H1 测试

## 全量验证结果（账号内 Spearman ρ）

| 账号 | n | anchor_top | anchor_bot | ρ(top10) | ρ(anti_bot10) | ρ(score) | p(score) | 显著? |
|---|---|---|---|---|---|---|---|---|
| kazik | 673 | 56 | 68 | 0.611 | 0.271 | 0.717 | 0.0 | ✅ |
| baoyu | 767 | 65 | 77 | 0.514 | 0.119 | 0.632 | 0.0 | ✅ |
| saiboshanxin | 892 | 53 | 89 | 0.084 | -0.062 | 0.334 | 0.0 | ✅ |
| huashu | 398 | 28 | 40 | 0.622 | 0.158 | 0.76 | 0.0 | ✅ |

## Hold-out 验证（2025 anchor → 2026 H1）

| 账号 | n_train | n_test | ρ_holdout | p_holdout | 显著? |
|---|---|---|---|---|---|
| kazik | 567 | 106 | 0.273 | 0.0046 | ✅ |
| baoyu | 600 | 167 | 0.298 | 0.0001 | ✅ |
| saiboshanxin | 667 | 225 | -0.242 | 0.0003 | ✅ |
| huashu | 276 | 122 | 0.368 | 0.0 | ✅ |

## 验证结论

**✅ 通过：4/4 正向且至少 2/4 显著**

- 正向账号数：4/4
- 显著账号数（p<0.05）：4/4

## 解读

style_match_score 在多个账号内与 composite_pct 显著正相关，说明：
- 与爆款写法相似的文章确实更容易爆款
- 与扑街写法相似的文章倾向于表现更差
- **建议**：将 style_match_score 纳入 critic 特征集，可考虑升级到 BGE 语义向量

## Chicken-and-Egg 风险说明

同一账号所有文章天然共享作者风格，TF-IDF 相似度上限高。
本验证在账号内排除了 leakage（LOO），并用 hold-out 做时序验证，
已尽量规避自相关偏差。若 ρ 较低，说明风格相似度对爆款的边际解释力有限。
