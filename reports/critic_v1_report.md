# critic v1 报告 — 双高潜力综合分模型

*生成时间:2026-05-21 00:49:46*

## 1. 核心:微信算法权重对齐的综合潜力分

**公式**(账号内分位):

```
composite_pct = 
   0.40 * read_pct       (阅读 — 微信权重 40%)
 + 0.15 * like_pct       (点赞 — 互动 30% 的一半)
 + 0.15 * old_like_pct   (在看 — 互动 30% 的一半)
 + 0.20 * share_pct      (分享 — 微信权重 20%)
 + 0.10 * comment_pct    (评论 — 完读 10% 代理)
```

**意义**:这是「涨粉变现潜力」的算法对齐分,微信推荐 / 涨粉效率本来就按这个权重

## 2. 模型表现

| 模型 | 5-fold CV R² | 训练集 R² |
|---|---|---|
| Linear Ridge | 0.105 ± 0.112 | 0.228 |
| **LightGBM** | **0.326 ± 0.036** | 0.751 |

**对比 critic v0 各 sub R²(Step 5)**:
- read_residual:  0.248
- share_residual: 0.323
- like_residual:  0.302
- old_like_residual: 0.294
- comment_residual: 0.214
- **critic v1 综合: 0.326** ← 更强

## 3. critic v1 LGB 特征重要性 Top 15

| 排名 | 特征 | gain |
|---|---|---|
| 1 | `jb_avg_word_len` | 398 |
| 2 | `jb_lexical_diversity` | 366 |
| 3 | `b_english_ratio` | 355 |
| 4 | `b_periods` | 337 |
| 5 | `tb_ratio` | 302 |
| 6 | `cover_b` | 256 |
| 7 | `t_chars` | 255 |
| 8 | `t_english_chars` | 246 |
| 9 | `b_quote_zh` | 223 |
| 10 | `cover_r` | 218 |
| 11 | `jb_unique_words` | 215 |
| 12 | `jb_word_count` | 190 |
| 13 | `cover_brightness` | 169 |
| 14 | `b_colons` | 167 |
| 15 | `cover_g` | 166 |

## 4. Linear 标准化系数 Top 15(方向 + 强度)

| 排名 | 特征 | 系数 | 方向 |
|---|---|---|---|
| 1 | `b_last_para_chars` | -19.633 | ↓ 负 |
| 2 | `b_chars` | -15.369 | ↓ 负 |
| 3 | `b_para_avg_chars` | +13.562 | ↑ 正 |
| 4 | `jb_unique_words` | +11.738 | ↑ 正 |
| 5 | `b_para_std_chars` | +10.589 | ↑ 正 |
| 6 | `b_english_ratio` | +8.171 | ↑ 正 |
| 7 | `jb_avg_word_len` | -8.105 | ↓ 负 |
| 8 | `b_para_count` | +4.740 | ↑ 正 |
| 9 | `b_short_para_ratio` | +3.726 | ↑ 正 |
| 10 | `has_cover_color` | +3.355 | ↑ 正 |
| 11 | `b_quote_zh` | +3.320 | ↑ 正 |
| 12 | `cover_r` | +2.867 | ↑ 正 |
| 13 | `jb_lexical_diversity` | -2.823 | ↓ 负 |
| 14 | `b_emojis` | -2.789 | ↓ 负 |
| 15 | `b_colons` | -2.670 | ↓ 负 |

## 5. 综合分阈值(各号内)

| 账号 | 中位 | 75% | 90% | 95% | 99% |
|---|---|---|---|---|---|
| 卡兹克 | 52.2 | 72.9 | 88.5 | 92.7 | 96.8 |
| 宝玉 | 49.4 | 73.9 | 88.4 | 94.2 | 98.2 |
| 赛博 | 50.4 | 72.0 | 86.2 | 92.1 | 97.7 |
| 花叔 | 50.2 | 73.7 | 87.9 | 93.4 | 98.1 |

## 6. critic v1 使用方法

```python
import pickle
import pandas as pd

# 加载
model = pickle.load(open('models/critic_v1_composite.pkl', 'rb'))

# 评分(features_48d 是 dict)
def score(features_48d):
    X = pd.DataFrame([features_48d])[model['X_cols']]
    score = float(model['lgb'].predict(X)[0])
    # score 是综合分位(0-100),越高越接近双高潜力
    return score
```

## 7. 给你确认

- [ ] LGB R² = 0.326,接受吗?
- [ ] 综合分公式权重(40/15/15/20/10)跟微信算法对齐,可调吗?
- [ ] critic v1 比 v0 sub-models 更适合做主 critic 吗?