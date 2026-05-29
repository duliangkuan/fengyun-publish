# critic v0 训练报告 — Phase 1 Step 5

*生成时间:2026-05-20 20:59:58*

## 1. 5 个 critic v0 模型表现

| target | 含义 | 微信权重 | 线性 R² | **LightGBM R²** | 内容空间(Step 2)|
|---|---|---|---|---|---|
| `read_residual` | 阅读 | 40% | 0.048±0.160 | **0.248±0.020** | 44% |
| `share_residual` | 转发 | 20% | 0.107±0.149 | **0.323±0.022** | 59% |
| `like_residual` | 点赞 | 15% | 0.110±0.126 | **0.302±0.022** | 48% |
| `old_like_residual` | 在看 | 15% | 0.097±0.173 | **0.294±0.025** | 45% |
| `comment_residual` | 评论 | 10% | 0.053±0.009 | **0.214±0.027** | 45% |

**解读**:
- R² = 「48 个 X 特征能解释残差的多少 variance」
- 残差已经去混淆,所以这是「纯内容贡献」的预测力
- LGB > Linear 说明特征之间有非线性或交互
- 内容预测 R² 0.2-0.4 在社科领域已经算很可观了

## 2.阅读(read_residual)— Top 15 关键特征

### LightGBM gain(看哪些特征模型最依赖)
| 排名 | 特征 | gain |
|---|---|---|
| 1 | `b_english_ratio` | 460 |
| 2 | `jb_avg_word_len` | 437 |
| 3 | `jb_lexical_diversity` | 424 |
| 4 | `b_periods` | 313 |
| 5 | `tb_ratio` | 306 |
| 6 | `t_chars` | 305 |
| 7 | `jb_unique_words` | 281 |
| 8 | `t_english_chars` | 262 |
| 9 | `b_quote_zh` | 207 |
| 10 | `cover_b` | 205 |
| 11 | `b_para_avg_chars` | 190 |
| 12 | `cover_r` | 176 |
| 13 | `b_colons` | 172 |
| 14 | `jb_word_count` | 160 |
| 15 | `cover_g` | 158 |

### 线性标准化系数(看方向 + 强度)
| 排名 | 特征 | 系数 | 方向 |
|---|---|---|---|
| 1 | `jb_unique_words` | +0.450 | ↑ 正相关 |
| 2 | `b_last_para_chars` | -0.441 | ↓ 负相关 |
| 3 | `b_chars` | -0.432 | ↓ 负相关 |
| 4 | `b_english_ratio` | +0.354 | ↑ 正相关 |
| 5 | `jb_avg_word_len` | -0.342 | ↓ 负相关 |
| 6 | `b_para_max_chars` | +0.262 | ↑ 正相关 |
| 7 | `jb_word_count` | -0.236 | ↓ 负相关 |
| 8 | `b_para_avg_chars` | +0.236 | ↑ 正相关 |
| 9 | `tb_ratio` | -0.173 | ↓ 负相关 |
| 10 | `b_short_para_ratio` | +0.160 | ↑ 正相关 |
| 11 | `b_para_count` | +0.153 | ↑ 正相关 |
| 12 | `b_quote_zh` | +0.149 | ↑ 正相关 |
| 13 | `has_cover_color` | +0.143 | ↑ 正相关 |
| 14 | `cover_g` | -0.138 | ↓ 负相关 |
| 15 | `b_emojis` | -0.134 | ↓ 负相关 |

## 2.转发(share_residual)— Top 15 关键特征

### LightGBM gain(看哪些特征模型最依赖)
| 排名 | 特征 | gain |
|---|---|---|
| 1 | `jb_avg_word_len` | 447 |
| 2 | `b_english_ratio` | 434 |
| 3 | `tb_ratio` | 397 |
| 4 | `jb_lexical_diversity` | 385 |
| 5 | `b_periods` | 308 |
| 6 | `t_chars` | 275 |
| 7 | `jb_unique_words` | 262 |
| 8 | `t_english_chars` | 241 |
| 9 | `cover_r` | 207 |
| 10 | `b_quote_zh` | 196 |
| 11 | `b_para_avg_chars` | 192 |
| 12 | `cover_b` | 189 |
| 13 | `cover_brightness` | 164 |
| 14 | `b_colons` | 149 |
| 15 | `b_dash` | 140 |

### 线性标准化系数(看方向 + 强度)
| 排名 | 特征 | 系数 | 方向 |
|---|---|---|---|
| 1 | `b_chars` | -0.707 | ↓ 负相关 |
| 2 | `b_last_para_chars` | -0.633 | ↓ 负相关 |
| 3 | `jb_unique_words` | +0.554 | ↑ 正相关 |
| 4 | `b_para_avg_chars` | +0.534 | ↑ 正相关 |
| 5 | `b_para_max_chars` | +0.432 | ↑ 正相关 |
| 6 | `has_cover_color` | +0.391 | ↑ 正相关 |
| 7 | `b_english_ratio` | +0.388 | ↑ 正相关 |
| 8 | `jb_avg_word_len` | -0.384 | ↓ 负相关 |
| 9 | `b_short_para_ratio` | +0.227 | ↑ 正相关 |
| 10 | `b_para_count` | +0.222 | ↑ 正相关 |
| 11 | `b_emojis` | -0.210 | ↓ 负相关 |
| 12 | `jb_lexical_diversity` | -0.207 | ↓ 负相关 |
| 13 | `b_quote_zh` | +0.169 | ↑ 正相关 |
| 14 | `cover_r` | +0.153 | ↑ 正相关 |
| 15 | `cover_g` | -0.143 | ↓ 负相关 |

## 2.点赞(like_residual)— Top 15 关键特征

### LightGBM gain(看哪些特征模型最依赖)
| 排名 | 特征 | gain |
|---|---|---|
| 1 | `jb_avg_word_len` | 373 |
| 2 | `jb_lexical_diversity` | 370 |
| 3 | `b_periods` | 368 |
| 4 | `b_english_ratio` | 361 |
| 5 | `tb_ratio` | 347 |
| 6 | `t_english_chars` | 286 |
| 7 | `jb_unique_words` | 258 |
| 8 | `cover_b` | 257 |
| 9 | `b_quote_zh` | 253 |
| 10 | `t_chars` | 251 |
| 11 | `b_colons` | 193 |
| 12 | `jb_word_count` | 157 |
| 13 | `cover_r` | 151 |
| 14 | `cover_g` | 148 |
| 15 | `cover_brightness` | 143 |

### 线性标准化系数(看方向 + 强度)
| 排名 | 特征 | 系数 | 方向 |
|---|---|---|---|
| 1 | `jb_unique_words` | +0.598 | ↑ 正相关 |
| 2 | `b_last_para_chars` | -0.555 | ↓ 负相关 |
| 3 | `b_chars` | -0.474 | ↓ 负相关 |
| 4 | `b_para_avg_chars` | +0.445 | ↑ 正相关 |
| 5 | `b_para_std_chars` | +0.430 | ↑ 正相关 |
| 6 | `jb_avg_word_len` | -0.362 | ↓ 负相关 |
| 7 | `b_english_ratio` | +0.353 | ↑ 正相关 |
| 8 | `jb_word_count` | -0.232 | ↓ 负相关 |
| 9 | `jb_lexical_diversity` | -0.212 | ↓ 负相关 |
| 10 | `b_quote_zh` | +0.202 | ↑ 正相关 |
| 11 | `has_cover_color` | +0.196 | ↑ 正相关 |
| 12 | `b_para_count` | +0.193 | ↑ 正相关 |
| 13 | `b_link_count` | +0.166 | ↑ 正相关 |
| 14 | `b_short_para_ratio` | +0.155 | ↑ 正相关 |
| 15 | `b_emojis` | -0.137 | ↓ 负相关 |

## 2.在看(old_like_residual)— Top 15 关键特征

### LightGBM gain(看哪些特征模型最依赖)
| 排名 | 特征 | gain |
|---|---|---|
| 1 | `b_english_ratio` | 440 |
| 2 | `jb_lexical_diversity` | 407 |
| 3 | `jb_avg_word_len` | 407 |
| 4 | `b_periods` | 399 |
| 5 | `tb_ratio` | 322 |
| 6 | `t_english_chars` | 281 |
| 7 | `t_chars` | 243 |
| 8 | `cover_b` | 240 |
| 9 | `b_quote_zh` | 239 |
| 10 | `jb_unique_words` | 224 |
| 11 | `cover_r` | 207 |
| 12 | `b_colons` | 171 |
| 13 | `cover_brightness` | 167 |
| 14 | `jb_word_count` | 149 |
| 15 | `b_dash` | 141 |

### 线性标准化系数(看方向 + 强度)
| 排名 | 特征 | 系数 | 方向 |
|---|---|---|---|
| 1 | `jb_unique_words` | +0.574 | ↑ 正相关 |
| 2 | `b_chars` | -0.562 | ↓ 负相关 |
| 3 | `jb_avg_word_len` | -0.434 | ↓ 负相关 |
| 4 | `b_english_ratio` | +0.403 | ↑ 正相关 |
| 5 | `b_last_para_chars` | -0.387 | ↓ 负相关 |
| 6 | `b_para_avg_chars` | +0.295 | ↑ 正相关 |
| 7 | `b_para_std_chars` | +0.279 | ↑ 正相关 |
| 8 | `jb_word_count` | -0.230 | ↓ 负相关 |
| 9 | `b_para_count` | +0.189 | ↑ 正相关 |
| 10 | `has_cover_color` | +0.183 | ↑ 正相关 |
| 11 | `b_short_para_ratio` | +0.181 | ↑ 正相关 |
| 12 | `b_quote_zh` | +0.181 | ↑ 正相关 |
| 13 | `jb_lexical_diversity` | -0.138 | ↓ 负相关 |
| 14 | `b_first_para_chars` | -0.130 | ↓ 负相关 |
| 15 | `t_chars` | +0.123 | ↑ 正相关 |

## 2.评论(comment_residual)— Top 15 关键特征

### LightGBM gain(看哪些特征模型最依赖)
| 排名 | 特征 | gain |
|---|---|---|
| 1 | `b_english_ratio` | 446 |
| 2 | `jb_avg_word_len` | 428 |
| 3 | `jb_lexical_diversity` | 385 |
| 4 | `b_periods` | 359 |
| 5 | `tb_ratio` | 301 |
| 6 | `t_chars` | 267 |
| 7 | `t_english_chars` | 262 |
| 8 | `cover_b` | 251 |
| 9 | `jb_unique_words` | 228 |
| 10 | `b_quote_zh` | 203 |
| 11 | `cover_r` | 198 |
| 12 | `jb_word_count` | 178 |
| 13 | `b_colons` | 169 |
| 14 | `b_dash` | 153 |
| 15 | `b_first_para_chars` | 141 |

### 线性标准化系数(看方向 + 强度)
| 排名 | 特征 | 系数 | 方向 |
|---|---|---|---|
| 1 | `b_para_std_chars` | +0.813 | ↑ 正相关 |
| 2 | `b_chars` | -0.509 | ↓ 负相关 |
| 3 | `jb_avg_word_len` | -0.378 | ↓ 负相关 |
| 4 | `b_english_ratio` | +0.333 | ↑ 正相关 |
| 5 | `jb_unique_words` | +0.249 | ↑ 正相关 |
| 6 | `b_para_max_chars` | -0.242 | ↓ 负相关 |
| 7 | `b_last_para_chars` | -0.209 | ↓ 负相关 |
| 8 | `b_short_para_ratio` | +0.202 | ↑ 正相关 |
| 9 | `b_para_avg_chars` | -0.183 | ↓ 负相关 |
| 10 | `b_para_count` | +0.172 | ↑ 正相关 |
| 11 | `b_quote_zh` | +0.169 | ↑ 正相关 |
| 12 | `tb_ratio` | -0.150 | ↓ 负相关 |
| 13 | `t_chars` | +0.137 | ↑ 正相关 |
| 14 | `has_cover_color` | +0.126 | ↑ 正相关 |
| 15 | `b_periods` | +0.109 | ↑ 正相关 |

## 3. 综合分公式(critic 对外接口)

```
综合分 = 
     0.40 × predict_阅读 +
     0.20 × predict_转发 +
     0.15 × predict_点赞 +
     0.15 × predict_在看 +
     0.10 × predict_评论 +
```

基于微信官方算法权重:打开率 40% + 互动率 30%(拆 like + old_like 各 15%)+ 分享 20% + 完读 10%(用 commentNum 代理,因为完读率拿不到)

## 4. critic v0 怎么用(写稿评分)

```python
# 加载所有子模型
import pickle
interface = pickle.load(open('models/critic_v0_interface.pkl', 'rb'))
models = {t: pickle.load(open(f'models/{p}', 'rb')) for t, p in interface['subscores'].items()}

# 对新文章评分(extract_features 抽 48 维 X)
def score_article(features_48d):  # dict
    X = pd.DataFrame([features_48d])[interface['X_cols']]
    subs = {}
    for target, m in models.items():
        subs[target] = float(m['lgb'].predict(X)[0])
    total = sum(subs[t] * w for t, w in interface['weights'].items())
    return {'total': total, **subs}
```

## 5. 给你确认

- [ ] R² 数字接受吗?(0.2-0.4 是内容预测的常规水平)
- [ ] LGB Top 15 跟 Step 4 单变量真规律对得上吗?
- [ ] 综合分公式权重对吗?还是想调?
- [ ] 是否要训 4 号专属 critic?(saiboshanxin 那组特征跟其他号相反)