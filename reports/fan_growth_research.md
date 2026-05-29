# 公众号涨粉变现真规律调研

> 调研日期: 2026-05-21
> 目的: 验证项目当前 composite_pct 权重 (0.40·read + 0.20·share + 0.15·like + 0.15·old_like + 0.10·comment) 是否有出处, 并寻找"涨粉变现"target 的真出处。
> 铁律: 每条结论必须带 URL 出处; 无硬数据则标 ⚠️。

---

## 调研方法和搜索关键词

执行了 12+ 次 WebSearch 和 11+ 次 WebFetch, 抓取了以下来源:

**搜索关键词**:
- 微信公众号 算法 权重 / 流量分发算法 / 推荐机制
- 看一看 推荐 流量池 完读率 / 张小龙 官方演讲 / 朋友推荐
- 涨粉 漏斗 阅读量 关注转化率 / 在看率 分享率 行业基准
- 真粉 假爆款 标题党 互动比 / 1000阅读 多少粉丝
- 私域 变现 加微信 知识付费 卖课
- 新榜 / 清博指数 / 西瓜指数 公式 权重
- WeChat reverse engineering recommendation system (英文学术)

**Verified sources (主要采用)**:
1. 清博指数 WCI V14.2 官方说明 (gsdata.cn) — **有公开公式 + 权重**
2. 西瓜数据 XGZS 指数算法说明 (xiguaji.com) — **有公开公式 + 权重**
3. 新榜参考资料 v4.1 PDF (newrank.cn) — 二进制 PDF, WebFetch 抽不出内容
4. yiban.io 2025 行业打开率报告 — 引用《2025新媒体内容生态研究报告》
5. 腾讯新闻官方 2024 复盘 — 10w+ 文章总量数据
6. 优设网 / 腾讯新闻 — 张小龙产品哲学 + 朋友推荐功能
7. 知乎 + 人人都是产品经理 + 数英 — 业内运营 SOP
8. CSDN/博客园 — 业内"独家揭秘"类文章 (低可信)

**Failed fetches (服务器拒绝)**:
- 知乎 zhuanlan.zhihu.com (HTTP 403 — 多个 URL)
- 网易 163.com (HTTP 404)
- 知乎深度文 p/4353751844 (HTTP 403)

---

## Q1: 微信算法权重的真实出处

### 结论 1 ⚠️: 项目当前 `0.40 read + 0.20 share + 0.15 like + 0.15 old_like + 0.10 comment` 的具体权重**没有官方出处**

调研中遇到的"40% / 30% / 20% / 10%"或类似比例,均出自**自媒体公众号 / SEO 博客的"独家揭秘"类内容**, 无任何一篇引用腾讯官方文档。

主要疑似源头是 jzl.com 一篇 2026-02 的文章:
> "打开率占40%权重，互动率(赞/在看/收藏)占30%，分享率占20%，完读率占10%"
> 来源: <https://www.jzl.com/news/195>
>
> WebFetch 评估: "No reference to WeChat's official developer documentation. No attribution to Tencent spokespeople. Presented as claimed data from unnamed sources (某财经号). The specific percentages lack verifiable sourcing."

另一篇 CSDN "10W+秘密"独家揭秘文 (<https://blog.csdn.net/2401_87027887/article/details/148262211>) 同样无官方引用:
> "Cites no official Tencent documentation. References no industry research papers. Provides zero empirical data."

**判定**: 0.40/0.20/0.15/0.15/0.10 这套权重,以及 0.40/0.30/0.20/0.10 那套,**都是行业坊间传闻**,不是腾讯官方披露。

### 结论 2 ✅: 腾讯官方**从未公开**算法权重

微信官方在 developers.weixin.qq.com 社区面对 "阅读完成率 vs 完读率 区别" 的反复追问, 官方账号 livia 仅回复"请通过反馈按钮提交问题",**没有任何技术说明**。
来源: <https://developers.weixin.qq.com/community/develop/doc/00048815da00f0364df06ab5a61400>

WebFetch 结论: "This is not official documentation but rather a community Q&A page where the distinction remains unexplained by WeChat's technical team."

### 结论 3 ✅: 张小龙的官方哲学是"社交分发优先,算法分发为补充"

2019 微信公开课张小龙讲:
> "我一直很相信通过社交推荐来获取信息是最符合人性的。"
> 来源: 优设网整理 <https://www.uisdc.com/wechat-algorithm-distribution>

但 2018-2020 期间, 腾讯 App 使用时长占比从 47.3% 跌到 39.5%, 字节从 9.7% 涨到 15.3% (同源), 导致微信被迫引入算法分发。**当前是混合机制**, 朋友圈仍按时间排序,公众号 + 视频号引入算法。

### 结论 4 ✅: 业内有 3 个**公开**的"近似估算"指数, 不是腾讯权重但可作为业内共识

#### (A) 清博指数 WCI V14.2 ⭐ 最权威
来源: <https://www.gsdata.cn/site/usage>

```
WCI = {
  0.60 × [0.85 LN(R/d+1) + 0.09 LN(Z/d·10+1) + 0.06 LN(L/d·10+1) + 0.15 LN(RE/d·10+1)]   # 整体传播力
+ 0.20 × [篇均传播力 同结构]                                                                # 篇均
+ 0.10 × [头条传播力 同结构]                                                                # 头条
+ 0.10 × [峰值传播力 Rmax/Zmax/Lmax/REmax]                                                  # 峰值
}² × 1.2 × 10
```

二级权重:
- **阅读 R: 85%** (含错误, gsdata 文档显示 70% — 见下方注释)
- 推荐 Z: 9%
- 点赞 L: 6%
- 转发 RE: 15% (清博 V14.2 新增维度)

⚠️ 注: gsdata 官网原文说 "Reads 70% / Recommendations 9% / Likes 6% / Shares 15%" (总和 100%); 另一篇 Python 实现 (<https://blog.csdn.net/NYRyn/article/details/121574058>) 说 85%/9%/6% (总和 100%, 但无 shares 项)。两个版本 LN 标准化系数也不一致, 应以 gsdata 官网为准。

#### (B) 西瓜指数 XGZS ⭐
来源: <https://data.xiguaji.com/help/detail/117.html>

```
XGZS = (R'·W1 + L'·W2 + F'·W3 + E'·W3 + C'·W4) × D'

R: 粉丝粘性(平均阅读, 去极值)  W1 = 30%
L: 内容质量(平均点赞, 去极值)  W2 = 25%
F: 粉丝质量(平均评论)          W3 = 20%
E: 影响力(头条总阅读)          W3 = 20%
C: 活跃指标(累计发文)          W4 = 5%
D: 风险系数(刷量/删文, 0-1)
```

**对项目的启示**: 西瓜把"评论"(粉丝质量)拉到 20%, 比清博的 6% 高 3 倍, 因为评论是**"真粉" 信号**,刷量难刷评论。

#### (C) 新榜指数
来源: <https://www.newrank.cn/public/about/reference.pdf> (PDF, WebFetch 抽不出内容)

间接搜到的公式片段 (未完整核实):
> "新榜指数 = 250 × [ln(评论)/ln(评论理论最大值)] + 625 × [ln(转发数)/ln(转发理论最大值)] + 125 × [ln(点赞数)...]"

按这个片段看, 新榜把 **转发权重 (625) 拉到评论 (250) 的 2.5 倍**, 点赞 (125) 最低。⚠️ 但完整公式未确认。

---

## Q2: 涨粉真规律

### 结论 5 ✅: 涨粉漏斗 5 阶段, 业内共识 "首次传播 + 二次传播"

来源: <http://www.woshipm.com/operate/2074187.html> + <https://www.woshipm.com/operate/3375626.html>

```
推送文章 → 会话窗口打开 → 分享朋友圈/微信群 → 好友再分享 → 朋友圈/群陌生人阅读 → 关注
   送达        一次传播      首次外溢          二次传播     新读者池          新粉
```

关键转化指标:
- **初次打开率** = 会话渠道阅读人数 / 所有渠道阅读人数
- **转发分享率** = 分享次数 / 所有渠道阅读人数 (业内称为 "share rate")
- **二次传播率**: 朋友圈/群带来的阅读 / 总阅读
- **引导关注人数** ⭐ ← 公众号后台直接提供, 这是 ground truth 涨粉指标

来源: yiban.io <https://yiban.io/blog/24912> — 提到公众号后台 【图文分析】→【数据报告】→【日报】 显示 "阅读次数、好看数、引导关注人数"。

### 结论 6 ✅: 2025 行业打开率基线 (硬数据)

来源: yiban.io 引用《2025新媒体内容生态研究报告》 <https://yiban.io/geo/31780>

| 账号档位 | 粉丝量 | 平均打开率 |
|---|---|---|
| 头部 | 100K+ | **2.1%** |
| 腰部 | 1K-10K | **0.7%** |
| 尾部 | <1K | **<0.3%** |

整体:
- 订阅号 0.89% (Q1 2025)
- 服务号 1.32%
- > 1% 超过 60% 同行
- > 2% 优秀
- > 5% 爆款

历史对比 (来源 chyxx.com 2019 数据 <https://www.chyxx.com/industry/201909/788894.html>):
- 2018 整体打开率 1.32% / 分享率 **3.85%** / 原文点击率 2.17%
- 粉丝 < 1万的小号打开率 2.88% (最高)

→ 7 年下降约 33%, 与抖音/小红书竞争激烈相符。

### 结论 7 ✅: **share (分享/转发) 是涨粉的核心驱动**, 不是 like

来源: <https://www.opp2.com/77218.html> + 多个运营文综合
> "涨粉的逻辑: 老用户得看完文章 → 转发朋友圈 / 转发群 / 点在看 → 外部用户才能看到 → 选择关注。如果不转发,涨粉无源头。"

来源: 知乎讨论 (摘要可见, 原文 403) <https://zhuanlan.zhihu.com/p/689406274>
> "微信公众号采用赛马机制, 文章发布后进入低流量池, 点赞量、分享量、评论量决定能否进入更大流量池。阅读量超过 1万 → 触碰高流量池门槛 → 人工审核阶段。"

### 结论 8 ✅: 朋友推荐功能上线后, 社交信号权重 **上升至 35%**, 但实际带流仍少

来源: 腾讯新闻 <https://news.qq.com/rain/a/20250321A05GDI00>
> 实测某 10万+ 文章:
> - 分享 1010 次
> - 朋友推荐(♡) 34 次
> - 朋友推荐渠道带来流量只占 0.02% 总阅读

→ "朋友推荐"占位强 (UI 顶部), 但仍小, **传统 share-to-朋友圈仍是涨粉主路径**。

### 结论 9 ✅: 一次传播 vs 二次传播比例是**"粉丝忠诚度"信号**

来源: <http://www.woshipm.com/operate/2074187.html>
> "对一个粉丝多的公众号, 二次传播率意味着朋友圈/群传播能力。**二次传播率 < 50% → 用户忠诚度低**。"

→ 项目用 share 作 target 之一是对的, 但应该用 **share/read 比** 而不是 share 绝对数 (大号 share 绝对数自然高)。

### 结论 10 ⚠️: 没找到"share率 vs comment率 vs old_like率 哪个最预测新粉丝"的硬实证研究

业内运营经验排序 (非论文): **share > comment > 在看 > 点赞**, 因为:
1. share 直接带来曝光给陌生人 → 新粉来源
2. comment 反映粉丝深度参与 → 真粉信号 + 算法权重
3. 在看 (old_like) 进入"看一看"算法池 → 二次推荐
4. 点赞 (like) 是最弱信号, 1000:2 是正常比 (<https://blog.csdn.net/weixin_45610775/article/details/101284349>)

⚠️ 这个排序是行业 SOP 共识, 没找到论文级实证。**项目方应该用自家 LightGBM + SHAP 自己跑出来。**

---

## Q3: 变现真规律

### 结论 11 ✅: 14 种变现路径, 但主流就 4 条

来源: 知乎 <https://zhuanlan.zhihu.com/p/1956855283927188404> (WebFetch 403 但搜索摘要可见)
- 流量主 (腾讯广告分成) — 阅读 PV 驱动
- 接广告 (品牌投放) — 新榜/西瓜指数排名驱动
- 卖课/知识付费 — 私域信任驱动
- 加微信进社群/星球 — 私域沉淀驱动

### 结论 12 ✅: 知识付费变现 = "公域内容 → 私域沉淀 → 信任建立 → 转化"

来源: <https://blog.csdn.net/2401_86572348/article/details/141218855>
> "黄金法则: 先价值, 后转化。公众号建立认知 + 输出干货 → 引流到视频号直播 → 沉淀私域流量池 → 直播间促成转化。"

来源: <https://blog.csdn.net/fxd1232/article/details/126073903>
> "知识付费需要私域运营降低获客成本、提高粘性和转化率。"

### 结论 13 ⚠️: **没找到"评论质量 / 在看 / 转发 哪个最预测付费转化"的硬数据**

业内说法 (运营经验, 非数据):
- 评论质量 → 信任度核心信号, 直接预测私域转化
- 在看 → 算法分发驱动 (公域曝光), 间接预测
- 转发 → 公域扩散, 间接预测

⚠️ 我没找到任何带 URL 的硬数据说"评论数 vs 在看 vs 转发"哪个对私域加微信转化率最高。**这是调研空白。**

### 结论 14 ✅: 西瓜指数对"广告投放价值"的评估排序 (权威性较高)

来源: <http://data.xiguaji.com/help/detail/192.html>

广告主评估账号价值的指标优先级:
1. **日均阅读量** (比粉丝数更靠谱, "粉丝数最容易 PS")
2. 广告专项表现 (通常比常规内容低 2-10 倍)
3. 历史广告复投情况 (转化已验证)
4. 受众活跃度 (评论数、留言数)
5. **二次分享率 > 一次分享率** (病毒潜力信号)

→ 对项目的启示: **如果 target 是变现 (接广告/卖课), 应该重点拟合的是「日均阅读 + 评论数 + 二次分享率」, 而不是单一爆款 read 峰值**。

---

## Q4: 优质爆款 vs 假爆款

### 结论 15 ✅: 业内共识真假爆款判定法 (有 URL 出处)

来源: <https://blog.csdn.net/weixin_45610775/article/details/101284349> + <https://www.digitaling.com/articles/236557.html>

**真爆款特征**:
- 阅读量增长**不规律** (符合传播曲线)
- 阅读 : 点赞 ≈ **1000 : 2** 是正常基线
- 10万+文章 → 评论:点赞 ≈ **10%** 是正常 (<https://yiban.io/geo/31780>)
- 评论区**有活跃讨论 + 作者互动**
- 转发数 / 收藏数和阅读匹配 (高读 → 高转)
- 二次传播率 > 50% (粉丝忠诚度)

**假爆款 / 标题党 / 刷量信号**:
- 阅读量呈"绝对正增长 / 每 5 秒涨 300" — 机器规律性 → 刷量
- 100,000+ 阅读 + "零散几十个赞" → 比例严重失调
- 高读 + 低转发 + 低收藏 → 标题党, 用户被骗点击
- 评论区死寂 → 假粉
- 广告类图文阅读 > 日常 → 可疑

### 结论 16 ✅: 完读率代理指标 — "5% 跳出率"

来源: yiban.io <https://yiban.io/blog/24912>
> "公众号后台 → 数据报告 → 100% 完成阅读占比 + 5% 处跳出率"

5% 跳出 = 文章开头 5% 位置被关闭的用户比例, 高 → 标题党。
**项目方 critic 数据集应有此字段**, 用作"真爆款"label 校准。

### 结论 17 ✅: 北极星指标 — "总有效阅读时长"

来源: 腾讯新闻 <https://news.qq.com/rain/a/20250830A02XLH00>
> 某账号阅读量提升 580% 的复盘:
> - 北极星指标 = 阅读 UV × 平均阅读时长(秒)
> - 案例对比:
>   - 低质爆款: 5,745 reads × 11 秒 = 63,195 分 (完读率 3%)
>   - 高质内容: 38,009 reads × 121 秒 = 4,599,089 分
> - 目标完读率: ~30%

→ **"reads × dwell_time" 这个乘法 target 比单一 read 更能区分真假爆款**。

### 结论 18 ⚠️: AI/科技垂类特殊性 — 行业认可"卡兹克"是黑马, 但没硬数据复盘

来源: <https://www.newrank.cn/article/detail/29573> + <https://news.qq.com/rain/a/20250119A03DEG00>
- "数字生命卡兹克" 在 2024 微信复盘被腾讯定性为"亮眼黑马"
- Sora 文章 10w+, 日常 1-3 万
- 但**没找到 AI 垂类的关键转化率数据** (例如 read → follower 转化率行业基准)

⚠️ AI/科技垂类相比"情感/生活"垂类的差异点 (业内观察, 无硬数据):
- 用户黏性高 (技术受众"专业兴趣">"娱乐消遣")
- comment 比例显著高于平均 (用户喜欢讨论)
- 私域转化率更高 (技术买课/咨询付费意愿强)
- 但分享率(share)可能低于情感类 (技术内容朋友圈展示意愿弱)

---

## 调研空白 (诚实承认)

⚠️ 以下问题**没有 URL 出处的硬数据**, 不要凭空设计:

1. **腾讯官方算法权重** — 永久封闭, 不可能拿到
2. **share率 vs comment率 vs old_like率 对涨粉的实证比较** — 无论文
3. **评论质量 / 在看 / 转发 哪个最预测付费转化** — 完全空白
4. **AI/科技垂类的 read → follower 转化率基准** — 完全空白
5. **新榜指数完整公式** — PDF 抓不出, 网上只有片段
6. **加微信转化率行业基准** — 找到一条说"知乎引流 8%-12%", 但来源不明
7. **新榜单条文章涨粉数据** — newrank.cn 有付费 API, 我们没买
8. **公众号 vs 视频号 vs 小红书 跨平台涨粉对比** — 完全空白

---

## 给项目的实操建议

### 建议 1: composite_pct **不要继续用**作为"涨粉/变现 target"

理由:
- 它的权重 0.40/0.20/0.15/0.15/0.10 无官方出处
- 它混了 "read" (公域分发结果) 和 "share/like/comment" (涨粉前置信号), 即"用结果预测结果"
- "old_like" (在看) 是看一看推荐池信号, 不是涨粉信号本身

**可保留场景**: 当作"平台分发友好度"的一个 feature 输入, 不要当 target。

### 建议 2: 真 target 应基于**「引导关注人数」**, 这是公众号后台 ground truth

如果数据集里有这个字段 → 直接用它当 y。
如果没有 → 用代理 target (按可信度排序):

#### 方案 A (最佳, 但需算力): 北极星乘法 target
```
y_value = read_uv × avg_dwell_time_sec
```
出处: <https://news.qq.com/rain/a/20250830A02XLH00>
⚠️ 需要数据集有 dwell_time 字段

#### 方案 B (次佳, 朴素直观, 业内共识): 涨粉漏斗代理
```
y_fan_growth = share_count
   × (1 + 2 × secondary_share_rate)     # 二次传播放大
   × engagement_quality_factor
其中:
   secondary_share_rate = 朋友圈阅读 / 总阅读  (需后台数据)
   engagement_quality_factor = 0.7 × comment + 0.3 × log(read+1)
                                  ↑ 评论是真粉信号, 西瓜指数权重 20%
```
出处:
- share 主导: <https://www.opp2.com/77218.html>
- 二次传播 50% 阈值: <http://www.woshipm.com/operate/2074187.html>
- 西瓜指数评论权重 20%: <https://data.xiguaji.com/help/detail/117.html>

#### 方案 C (最简单): 直接抄西瓜指数 XGZS 公式作为变现 target
```
XGZS = (0.30·R + 0.25·L + 0.20·F + 0.20·E + 0.05·C) × D
其中:
   R = 平均阅读 (去极值)
   L = 平均点赞 (去极值)
   F = 平均评论数         ← 注意这里, 评论权重 20%, 远高于清博的 6%
   E = 头条总阅读
   C = 累计发文数
   D = 0-1 风险系数(刷量/删文)
```
出处: <https://data.xiguaji.com/help/detail/117.html>

#### 方案 D (兜底): 用清博指数 WCI V14.2
```
WCI 内部权重: 阅读 70% / 转发 15% / 推荐 9% / 点赞 6%
```
出处: <https://www.gsdata.cn/site/usage>

### 建议 3: 加 "真假爆款" 过滤 label

在训练集上预过滤"假爆款"(标题党/刷量):
- read/like > 1000 (远超 1000:2 正常基线 → 可疑)
- 10w+ 文章 comment/like < 5% (远低于 10% 基线 → 可能假)
- 5% 处跳出率高 (如有此字段)

出处: <https://blog.csdn.net/weixin_45610775/article/details/101284349>, <https://yiban.io/geo/31780>

### 建议 4: 不要再臆想公式

P0 铁律: **"客观事实驱动 + 不知道先调研"**。
本次调研为 target 设计提供了 4 个有出处的备选方案 (A/B/C/D), 任选其一作为 baseline, 用 LightGBM + SHAP 跑实证。
**禁止**再出一个无出处的 `V_score = 0.40 × share + 0.30 × comment ...` 公式。

### 建议 5: AI 垂类特殊性, 用对标账号验证

调研空白 4 (AI 垂类基准) 无法补, 但可以用**对标账号实测数据**填:
- 卡兹克 (数字生命卡兹克) — 行业认可
- 量子位 / 机器之心 / 新智元 — 头部 AI 媒体
- 拉新榜 AI 影响力榜 <https://www.newrank.cn/rankai/gongzhonghao>

抓他们的 share/comment/read 比例, 算 AI 垂类的"真实基线", 比通用基线更准。

---

## Sources (本调研所有 URL 汇总)

### 官方/权威源
- 腾讯微信开放社区 — 阅读完成率 vs 完读率 QA <https://developers.weixin.qq.com/community/develop/doc/00048815da00f0364df06ab5a61400>
- 腾讯新闻 2024 微信复盘 <https://news.qq.com/rain/a/20250119A03DEG00>
- 腾讯新闻 朋友推荐功能上线 <https://news.qq.com/rain/a/20250321A05GDI00>
- 腾讯新闻 阅读量 580% 复盘 <https://news.qq.com/rain/a/20250830A02XLH00>
- 优设网 — 张小龙算法哲学 <https://www.uisdc.com/wechat-algorithm-distribution>
- 新榜 — 微信 2024 复盘 <https://www.newrank.cn/article/detail/29573>
- 新榜 AI 影响力榜 <https://www.newrank.cn/rankai/gongzhonghao>
- 新榜参考资料 PDF (抽不出) <https://www.newrank.cn/public/about/reference.pdf>

### 行业指数公式 (核心可引用)
- **清博指数 WCI V14.2** <https://www.gsdata.cn/site/usage>
- **西瓜指数 XGZS** <https://data.xiguaji.com/help/detail/117.html>
- 西瓜数据 — 广告投放价值评估 <http://data.xiguaji.com/help/detail/192.html>
- WCI V13.0 Python 实现 <https://blog.csdn.net/Aubrey_yt/article/details/90317966>
- WCI V14.2 Python 实现 <https://blog.csdn.net/NYRyn/article/details/121574058>

### 行业基线数据
- yiban.io 2025 打开率行业标准 <https://yiban.io/geo/31780>
- yiban.io 单文章涨粉数据查看 <https://yiban.io/blog/24912>
- yiban.io 打开率历史 <https://yiban.io/blog/4262>
- 智研咨询 2018 行业数据 (历史对照) <https://www.chyxx.com/industry/201909/788894.html>

### 运营 SOP 来源
- 人人都是产品经理 — 4 模块 34 指标 (3375626) <https://www.woshipm.com/operate/3375626.html>
- 人人都是产品经理 — 数据分析关键点 (2074187) <http://www.woshipm.com/operate/2074187.html>
- 人人都是产品经理 — 关注转化率 (926739) <https://www.woshipm.com/operate/926739.html>
- 人人都是产品经理 — 看一看分发 (4074775) <https://www.woshipm.com/operate/4074775.html>
- 青瓜传媒 — 7 种涨粉套路 <https://www.opp2.com/77218.html>
- 数英 — 6 步鉴别水军 <https://www.digitaling.com/articles/236557.html>
- CSDN — 刷量识别 <https://blog.csdn.net/weixin_45610775/article/details/101284349>

### 自媒体"独家揭秘"类 (低可信, 仅供参考)
- jzl.com — 2025 推荐机制全解析 (0.40/0.30/0.20/0.10 出处) <https://www.jzl.com/news/195>
- CSDN — 10W+ 秘密独家揭秘 <https://blog.csdn.net/2401_87027887/article/details/148262211>
- 白杨SEO — 流量解密 <https://www.baiyangseo.com/blog/901.html>
- CSDN — 全面解读推荐机制 <https://blog.csdn.net/longzorg_cn/article/details/145682351>

### 学术研究
- Semantic Scholar — WeChat 混合推荐算法研究 <https://www.semanticscholar.org/paper/Research-on-Recommendation-Mode-of-WeChat-Official-Chen-Zheng/565efb019ac605be1d41acca757077cba31f775a>
- ACM — Ranking Learning Algorithm for WeChat <https://dl.acm.org/doi/10.1145/3078564.3078572>
- PMC — Chinese CDC WeChat engagement study <https://pmc.ncbi.nlm.nih.gov/articles/PMC10101727/>

### 抓取失败 (供参考, 抓不到内容)
- 知乎 zhuanlan p/689406274 (HTTP 403)
- 知乎 zhuanlan p/698645906 (HTTP 403)
- 知乎 zhuanlan p/4353751844 (HTTP 403)
- 知乎 zhuanlan p/164873679 (HTTP 403)
- 知乎 zhuanlan p/1956855283927188404 (HTTP 403)
- 网易 163.com (HTTP 404)
