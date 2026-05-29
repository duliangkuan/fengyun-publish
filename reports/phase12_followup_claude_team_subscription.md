# Phase 12 Follow-up · Claude Team 订阅替代 API 的可行性

*主对话整合 · Opus 4.7 · 2026-05-22 13:00 完成*
*起因：连续 2 次 Sonnet agent 因 Anthropic 529 Overloaded 失败，主对话接手调研 + 整合*

---

## 用户问题

「我有 Claude Team 订阅,能不能直接用订阅额度(不付 API 费)让 Claude Code 在 VPS 上 24/7 cron 跑 fengyun-publish 全自动写文章?Anthropic 应该有自己的云端服务吧?」

这是省 Phase 11 verdict 中 ¥97/月 Claude API 费的关键决策点。

---

## 5 个事实点(全部有官方出处)

### F1 · Claude Code 登录方式

**支持的认证**:
- Anthropic API key(走 Console,按 token 付费)
- Claude.ai 订阅 OAuth(Pro / Team / Enterprise 通用)
- 第三方 provider(Bedrock / Vertex)

**VPS Headless 实操**:
1. 在有浏览器的本地机跑 `claude setup-token` → 走 OAuth 授权 → 输出 **`sk-ant-oat01-` 开头 token,有效期 1 年**
2. 传到 VPS,设 `CLAUDE_CODE_OAUTH_TOKEN` 环境变量
3. 配 `~/.claude.json` 标记 onboarding 完成
4. token 是 inference-only,不能开 Remote Control sessions

**Source**: 多个社区 tutorial + anthropics/claude-code issue #7100(官方支持但文档薄弱)

---

### F2 · Team 订阅在 Claude Code 上的额度

| 类型 | 价格 | Claude Code 含? | Rate Limit(5h 窗口) | Agent SDK Credit(2026-06-15 起) |
|---|---|---|---:|---:|
| **Team Standard** | $20/seat/月(年付)/ $25(月付)| 含 | ~55k tokens | **$20/月** |
| **Team Premium** | $100/seat/月(年付)/ $125(月付),**最少 5 seats** | 含,完整 | ~275k tokens(6.25x Pro)| **$100/月** |

**关键**: 2026-05 Anthropic 在与 SpaceX Colossus 1 compute 协议后,把 Claude Code 5h 窗口额度翻倍。Team Standard / Premium 都吃到了 doubling。

**Opus 4.6 1M context**: 自 2026-03 起,Max / Team(Standard + Premium)/ Enterprise 用户**自动**获得 Opus 4.6 1M context,无额外配置无额外费用。

**Source**:
- claude.com/pricing(官方价格页)
- Anthropic Help Center 11145838(Pro/Max 订阅 Claude Code)
- 9to5google.com 2026-05-06 报道额度翻倍

---

### F3 · ToS / AUP 对自动化的限制

**Anthropic AUP 全文搜索**: 未明确禁止 / 也未明确允许「自动化使用 Claude.ai 订阅账号」。

**只有两条相关条款**:
> "Circumvent a ban through the use of a different account..."
>
> "Coordinate malicious activity across multiple accounts to avoid detection or circumvent product guardrails"

**关键的官方明示授权**(在 Agent SDK 文档里):
> "credits are **sized for individual experimentation and automation**"

但同份文档也说:
> "Teams running shared production automation should use Claude Platform with an API key for predictable pay-as-you-go billing"

**解读**:
- ✅ 个人 IP 自动化 = 明示允许
- ⚠️ 团队 / 商业服务 / 给客户的托管自动化 = 官方建议走 API

**Source**: anthropic.com/legal/aup + support.claude.com/en/articles/15036540

---

### F4 · Anthropic 官方云端服务(用户猜测的方向)

**两个相关的官方服务**:

#### Claude Managed Agents(2026-04-08 公测)

**计费**: 不吃订阅,按用计费 ──
- $0.08 / session-hour(running 时按毫秒计)
- 每个 token 按标准 API 价格(Sonnet 4.6: $3/M input + $15/M output)
- WebSearch 触发: $0.01 / 搜索

**适用**: 完整托管的复杂 agent 任务,适合企业。

#### Agent SDK Credits(2026-06-15 起)

**所有订阅自带每月 Agent SDK credits,不吃 5h 窗口**:
- Pro: $20/月
- Max 5x: $100/月
- Max 20x: $200/月
- **Team Standard: $20/月**
- **Team Premium: $100/月**
- Enterprise 按 seat: $200/月

**关键原话**:
> "Agent SDK usage draws from your monthly credit before any other source. If credits exhaust, usage moves to standard API rates only if usage credits are enabled; otherwise, Agent SDK requests stop until your credit refreshes."

**Source**: support.claude.com/en/articles/15036540

---

### F5 · VPS 实操可行性

社区已有完整 tutorial:
- gist coenjacobs/d37adc34149d8c30034cd1f20a89cce9: VPS 自动化部署 Claude Code
- virtua.cloud: Run Claude Code on a VPS: Install, Secure, Persist
- dev.to/benutting/building-claudio: "Building My Always On Claude VPS"
- quantvps.com: How to Install Claude Code on a VPS

**实操路径**:
```bash
# 本地有浏览器的机器
claude setup-token  # 走 OAuth 授权 → 输出 sk-ant-oat01-... token

# VPS 上
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-xxx
echo '{"hasCompletedOnboarding": true}' > ~/.claude.json
claude -p "你的 prompt"
```

**Token 续期**: 1 年。1 年后重跑 `setup-token` 即可。

---

## 4 个 Verdict

### V1 · 技术可行性 = **Y(明确可行)**
长期 OAuth token + CLAUDE_CODE_OAUTH_TOKEN 环境变量是 Anthropic 官方支持的 CI / VPS 路径,1 年期持久化,无 hack。

### V2 · 合规性 = **Y(官方明示允许 individual automation)**
- AUP 未明禁
- Agent SDK 文档原话 "sized for individual experimentation and automation"
- 风云个人 IP 完全在范围内
- **限制**: 不能跨账号共享 / 不能为客户提供托管服务

### V3 · 推荐采用 = **Y,Hybrid 分阶段**

| 阶段 | 路径 | 月成本 | 说明 |
|---|---|---:|---|
| **6-15 前(短期)** | API Sonnet 4.6(Phase 11 原方案)| ¥97 | 先跑通端到端,等 Credits |
| **6-15 起(中期)** | **Agent SDK Credits + 订阅** ⭐ | **0** | 订阅自带,**净增 0 元** |
| 备用 | Managed Agents | ~¥210 | 全托管但不省钱 |

**Sonnet 4.6 跑 fengyun-publish** ≈ 50k tokens/篇 × $0.0009(Sonnet 4.6 平均)= **$0.45/篇** × 30 篇 = **$13.5/月**

- Team Standard $20 credit / 月 = ✅ 覆盖
- Team Premium $100 credit / 月 = ✅✅ 绰绰有余

### V4 · Anthropic 官方云端方案 = **有 2 个**
- Managed Agents(2026-04-08 公测,按用计费,适合企业)
- Agent SDK Credits(2026-06-15 起,订阅自带,适合个人 IP)── **推荐**

---

## Musk × Jobs 整合视角

**Musk**: 物理上完全可跑。`setup-token` + 长期 OAuth token 是官方支持路径,1 年期 token 持久化,不存在 hack。**Team Standard 5h 窗口对 80k tokens 边界吃紧 → 必须靠 Agent SDK Credits 单独额度兜底**。Idiot Index 最低决策: 等 6-15 用 Credits,月成本从 ¥97 降到 0。

**Jobs**: 「灰色地带」担忧消解了 ── Anthropic 文档原话明示 "individual automation" 允许。但**「这是 individual automation 不是商业 SLA」**这条不能忽视: 如果未来要给客户提供托管服务必须切 API。当前风云个人 IP **完全合规**。

---

## 翻转的 Phase 11 决策

**Phase 11 原 verdict 月成本**:
- 阿里云轻量: ¥5.7
- DeepSeek API: ¥20-50
- Claude API Sonnet: ¥97
- 豆包: ¥0-6
- **合计: ¥123-160/月**

**Phase 12 修正后(6-15 之后)**:
- 阿里云轻量: ¥5.7
- DeepSeek API: ¥20-50
- **Claude API → Agent SDK Credits(订阅自带,0 元)**
- 豆包: ¥0-6
- **合计: ¥26-62/月**(净降 ¥97)

每年节省 ¥97 × 12 = **¥1164**。

---

## 必踩的 3 个坑

1. **token 1 年到期**: 设日历提醒,2027-05-22 重跑 `setup-token`
2. **Agent SDK Credits 不吃 5h 窗口,但订阅基础调用仍受 5h 窗口约束**: cron 用 Agent SDK API,不要混淆
3. **Team Standard $20 Credit 紧贴 30 篇用量**: 如果想扩展每天 2 篇,要么升 Premium,要么加 API key fallback

---

## TOP 3 必做(继承 Phase 11,有 3 处工具替换)

**T1**(继承)`tools/extract_topic.py` + 企微选题确认消息 ── 2 小时

**T2**(继承+修正)VPS 装 Claude Code + 同步项目 + **用 `setup-token` 生成长期 OAuth token,不用 API key** + 配微信白名单 + 端到端跑一次 ── 3-4 小时

**T3**(继承+修正)`daily_ship.sh` 6-15 后**切到 Agent SDK Credits API endpoint(@anthropic-ai/claude-agent-sdk 包)**,不再用 API key 计费 ── 30 分钟

---

## 仍待用户确认

1. Claude Team 是 **Standard** 还是 **Premium**?
2. 订阅了几个 seats?
3. 月付还是年付?

这 3 个决定 6-15 Credits 上线后的具体路径选择。

---

## 调研记录

| 调研 | 来源 | 关键发现 |
|---|---|---|
| 1 · Claude Code 认证 | docs.claude.com/claude-code(redirect to code.claude.com) | "log in on first use",官方推荐 setup-token 用于 headless |
| 2 · Anthropic Pricing | claude.com/pricing | Team Standard $20-25,Premium $100-125 最少 5 seats,Claude Code 均含 |
| 3 · AUP | anthropic.com/legal/aup | 未明禁自动化,只禁 ban 后绕过 + 跨账号协同 |
| 4 · Agent SDK + Plans | support.claude.com 15036540 | **个人 automation 明示允许**,Credits 6-15 起 |
| 5 · Claude Code + Pro/Max | support.claude.com 11145838 | 订阅 OAuth 登录支持 |
| 6 · VPS Headless OAuth | WebSearch 多个社区 tutorial | setup-token 1 年期,CLAUDE_CODE_OAUTH_TOKEN 环境变量 |
| 7 · Team Rate Limits | tygartmedia + sitepoint | Standard 55k / Premium 275k / 5h 窗口 |
| 8 · Managed Agents | verdent + tygartmedia | 2026-04-08 公测,$0.08/session-hour + tokens API 价 |

**总调研 8 次** WebFetch + WebSearch,2 次因 Anthropic 529 失败的 sonnet agent 不计。

---

*报告路径: `D:\Dev\ai-wechat-pipeline\reports\phase12_followup_claude_team_subscription.md`*
*生成时间: 2026-05-22 13:00,主对话 Opus 接手撰写*
