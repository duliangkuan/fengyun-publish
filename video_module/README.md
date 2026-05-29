# video_module · AI 证书广告数字人流水线

> 文案 → TTS → 数字人口播视频 → mp4,云端推理,本地零 GPU 要求。
> 接 fal.ai 的 HunyuanVideo-Avatar 端点(腾讯混元开源数字人,SOTA 级)。

---

## 这是什么

一段 Python 胶水脚本,把"30 秒口播文案 + 一张讲师照片"自动跑成 mp4 数字人广告。

```
text(yaml)
  → edge-tts(免费) → audio.mp3
    → fal.ai HunyuanVideo-Avatar(云端) → talking_head.mp4
```

适用场景:批量生产 AI 证书 / 知识付费类**投流广告短视频**(20–60 秒)。

---

## 目录

```
video_module/
├── pipeline.py            # CLI 入口
├── providers/
│   ├── base.py            # AvatarProvider 抽象基类
│   └── falai.py           # fal.ai 实现(主)
├── tts.py                 # edge-tts 中文 TTS 封装
├── scripts/
│   ├── jianying_ad_template.md   # 剪映用的脚本模板(25 个钩子)
│   └── example_input.yaml        # 流水线输入示例
├── assets/portraits/      # 你的讲师头像(自己放,已 gitignore)
├── output/                # 成片输出
├── tmp/                   # TTS 中间产物
├── requirements.txt
└── .env.example
```

---

## 环境准备

### 1. Python 依赖

```powershell
cd D:\Dev\ai-wechat-pipeline\video_module
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. fal.ai API Key

注册 https://fal.ai → Dashboard → API Keys → 复制 key。

**注意:fal.ai 收费需要海外信用卡**(Visa/Master)。国内用户可以:
- 用 Wildcard / Depay / OneKey Card 等虚拟卡充值
- 充 $5 起步,够跑 ~50 条 30 秒视频

把 `.env.example` 复制成 `.env`,填入:
```
FAL_KEY=你的key
```

### 3. 讲师头像准备

放 1–N 张人像图到 `assets/portraits/`,要求:
- 正脸或半侧脸,面部清晰
- 商务装(西装/职业装),跟"AI 讲师"调性匹配
- 分辨率 ≥ 768x768,JPG/PNG
- 来源:Midjourney / 即梦 / 通义万相 生成的虚拟讲师(规避肖像权)

---

## 使用

### 单条出片

1. 复制 `scripts/example_input.yaml` 改成 `scripts/my_ad_001.yaml`
2. 填:`avatar_image`(头像路径) + `text`(文案)
3. 跑:

```powershell
python pipeline.py scripts/my_ad_001.yaml
```

成片在 `output/ad_001.mp4`。

### 批量出片(20 条)

写一个简单 shell:

```powershell
foreach ($f in Get-ChildItem scripts\batch\*.yaml) {
    python pipeline.py $f.FullName
}
```

把 25 个钩子(见 `scripts/jianying_ad_template.md`)各做一个 yaml,丢进 `scripts/batch/` 一晚跑完。

---

## 成本估算

| 项 | 单价 | 说明 |
|---|---|---|
| edge-tts | **0 元** | 微软免费 TTS,中文质量够投流用 |
| fal.ai HunyuanVideo-Avatar | **~$0.3–0.6 / 条** | 30 秒 720P,turbo 模式,约 1–2 分钟生成 |
| **单条综合** | **~¥2.5–5** | 含失败重跑 buffer |
| **一晚 20 条投流弹药** | **~¥60–100** | 比任何 SaaS 月费便宜 |

---

## TTS 音色选择

`voice` 字段填以下任一别名,或填 edge-tts 完整 voice 名:

| 别名 | 真实 voice | 调性 |
|---|---|---|
| `male_calm` | zh-CN-YunjianNeural | 沉稳男声(默认,适合知识付费) |
| `male_news` | zh-CN-YunyangNeural | 新闻男声(权威感) |
| `male_warm` | zh-CN-YunxiNeural | 温暖男声(35 岁讲师感) |
| `female_warm` | zh-CN-XiaoxiaoNeural | 知性女声 |
| `female_smart` | zh-CN-XiaoyiNeural | 干练女声 |

**避坑**:不要选可爱卡通音色,跟"考证"调性冲突。

如果想用克隆自己的声音 → 后面接 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 替换 `tts.py`。

---

## 跑通后下一步

1. **跑前 20 条投流测试**:用 25 个钩子的前 20 个,每个出一条,推到视频号/小红书
2. **看 3 天数据**:CTR、3秒/完播率、评论区"想考"扣字数量
3. **赢家迭代**:跑赢的钩子,换 3 个不同讲师头像各出 5 条变体
4. **接入主流水线**:把 video_module 当 ai-wechat-pipeline 的 L7 视觉层延伸,跟 baoyu-post-to-wechat 串起来,做"公众号文章 + 配套口播广告"双发

---

## 可扩展的 provider

`providers/base.py` 是抽象基类,未来想换:

- **WaveSpeedAI** — fal.ai 的备份,价格略低,海外卡
- **腾讯云混元 Avatar** — 国内人民币付费,微信支付,需企业认证
- **火山引擎即梦** — 字节家,个人实名可调
- **本地 ComfyUI + HunyuanVideo-Avatar** — 租 AutoDL 4090 自建,长期最便宜

新增 provider 只需在 `providers/` 加一个文件实现 `AvatarProvider.generate()`,再注册到 `providers/__init__.py:PROVIDERS`。

---

## 已知坑

1. **首次调用 fal.ai 冷启动可能 90s+**,后续热实例 30–60s/条
2. **音频超过 1 分钟成本翻倍**,广告控制在 30s 内最划算
3. **头像必须是正脸,侧脸 > 30° 会爆**(模型对侧脸支持差)
4. **fal.ai 偶发 429**,加重试或换 webhook 模式
5. **配音如果用 edge-tts,情感表达单一** — 跑通后建议升级 GPT-SoVITS 克隆真人声

---

## 跟 ai-wechat-pipeline 主项目的关系

- 本模块**独立运行**,不依赖 PLAN.md 里 L0–L7 任何层
- 但**共享 corpus/**:讲师文案可以从 corpus/ 选题数据库直接生成
- 后期可以包成 MCP server 接入 Claude Agent SDK,跟 L7 排发反馈层并列做"投流广告"分支
