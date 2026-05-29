# 评论挖掘报告 v3 — SiliconFlow API 版(最终版)

*生成时间:2026-05-20 23:48:22*

**方法**:BGE-large-zh embedding + UMAP/HDBSCAN 自动聚类 + Qwen2.5 LLM 起名 + Qwen2.5 LLM 情感打分。

## 1. 数据总览

- 评论数:74,175
- 主题数:116(HDBSCAN 自动决定)
- 离群:30,848 (41.6%)
- 情感分布:正面 25,252 (34%)/ 中性 30,676 (41%) / 负面 18,247 (25%)

## 2. 4 号读者画像

| 账号 | 评论数 | 平均字数 | 正面率 | 负面率 | 平均点赞 |
|---|---|---|---|---|---|
| **数字生命卡兹克** | 54,454 | 38 | 35.0% | 24.8% | 6.4 |
| **宝玉AI** | 2,704 | 42 | 33.8% | 19.8% | 1.6 |
| **赛博禅心** | 13,114 | 27 | 30.2% | 26.0% | 3.9 |
| **花叔** | 3,903 | 33 | 33.5% | 20.8% | 2.8 |

## 3. 全部 116 个主题(按评论数)

| ID | 评论数 | LLM 起名 | 代表词 | 平均点赞 | 正面率 | 主导账号 |
|---|---|---|---|---|---|---|
| #0 | 27,105 | **AI平权与认知博弈** | `deepseek ai agent aiai token` | 5.8 | 32% | 数字生命卡兹克 (73%) |
| #1 | 2,947 | **卡神粉丝技术崇拜圈** | `666 2024 nb tim 2026` | 4.4 | 71% | 数字生命卡兹克 (99%) |
| #2 | 1,214 | **Claude Code使用讨论** | `claude code claudecode claudeclaude codexclaude` | 3.6 | 21% | 数字生命卡兹克 (67%) |
| #3 | 1,017 | **getseed产品与网络黑话** | `cos geo ntr kiss first` | 5.6 | 33% | 数字生命卡兹克 (69%) |
| #4 | 742 | **飞书多维表格AI工作流** | `aily wps cli notion claw` | 3.6 | 29% | 数字生命卡兹克 (87%) |
| #5 | 574 | **卡兹克AI实操分享** | `bai all skill do 3ai` | 9.1 | 60% | 数字生命卡兹克 (98%) |
| #6 | 479 | **Gemini与GPT对比实测** | `gemini gemini3 25 flash pro` | 5.3 | 31% | 数字生命卡兹克 (75%) |
| #7 | 445 | **龙虾AI使用与吐槽集** | `apiapi aily maxclaw skillskill linux` | 4.9 | 20% | 数字生命卡兹克 (79%) |
| #8 | 428 | **大聪明酒吧整活集锦** | `bar call svg colab 169` | 2.0 | 56% | 赛博禅心 (93%) |
| #9 | 309 | **提示词优化与使用心得** | `cosplay you are above ii` | 4.5 | 26% | 数字生命卡兹克 (58%) |
| #10 | 280 | **社群入群与交流讨论** | `200 21 612 1226 qq` | 1.3 | 19% | 数字生命卡兹克 (52%) |
| #11 | 249 | **智谱GLM用户评论热议** | `autoglm tog glm glmpc minimaxkimi` | 5.1 | 39% | 数字生命卡兹克 (60%) |
| #12 | 241 | **宝玉老师技能分享** | `baoyuskill skills gem kol example` | 1.5 | 68% | 宝玉AI (93%) |
| #13 | 228 | **Kimi AI使用与功能讨论** | `kimi kimikimi k2 k26 kimikimikimi` | 6.6 | 41% | 数字生命卡兹克 (65%) |
| #14 | 227 | **读者盛赞花叔强大技能** | `aiskill skill powerful promax kind` | 1.8 | 68% | 花叔 (96%) |
| #15 | 210 | **即梦AI版本更新热议** | `40 30 ai30 seedance banana` | 4.7 | 33% | 数字生命卡兹克 (94%) |
| #16 | 198 | **腾讯元宝与微信AI生态热议** | `ima wechat 255 dm agentprompt` | 10.1 | 30% | 数字生命卡兹克 (92%) |
| #17 | 185 | **可灵Runway视频生成对决** | `runway away luma yyds 30` | 4.9 | 39% | 数字生命卡兹克 (97%) |
| #18 | 166 | **鲜虾包评论区蹲守** | `nice 130 ola istj kimideepseek` | 6.7 | 28% | 数字生命卡兹克 (93%) |
| #19 | 155 | **Prompt使用经验与技巧** | `prompt promptprompt promptai injection promptaiai` | 3.2 | 30% | 数字生命卡兹克 (75%) |
| #20 | 148 | **真实而强烈的点赞热潮** | `bold real update anything no` | 0.5 | 98% | 数字生命卡兹克 (64%) |
| #21 | 146 | **AI幻觉的多元探讨** | `whisper mbti aiai70 box llm` | 7.2 | 10% | 数字生命卡兹克 (84%) |
| #22 | 141 | **AI视频生成模型热议** | `sora sora2 seedance20 sota case` | 10.1 | 22% | 数字生命卡兹克 (87%) |
| #23 | 128 | **Vibe Coding实战与AI编程体验** | `vibe coding vibecoding codingai vide` | 7.4 | 30% | 数字生命卡兹克 (63%) |
| #24 | 128 | **Anthropic：AI安全与竞争漩涡** | `anthropic anthropicai anthropicclaude dario anthropicceo` | 16.5 | 32% | 数字生命卡兹克 (39%) |
| #25 | 127 | **秘塔AI工具使用心得** | `miromind grokx notebooklmapp gptapi 65` | 6.2 | 38% | 数字生命卡兹克 (94%) |
| #26 | 125 | **数字生命与记忆永恒** | `id remember live 365 2077` | 12.5 | 40% | 数字生命卡兹克 (97%) |
| #27 | 118 | **AI翻译工具与实时翻译讨论** | `arxiv deepl vpn improving does` | 3.9 | 36% | 数字生命卡兹克 (73%) |
| #28 | 117 | **Cursor AI编程工具使用讨论** | `cursor cursorcursor codevs directory rvc` | 4.4 | 15% | 数字生命卡兹克 (51%) |
| #29 | 109 | **赛博禅心读者梗合集** | `bro 2077 no1 mini sd` | 6.5 | 51% | 数字生命卡兹克 (57%) |
| #30 | 108 | **Trae使用体验与排队** | `trae solo trea traecursor traesolo` | 3.6 | 22% | 数字生命卡兹克 (82%) |
| #31 | 94 | **MCP技术生态与争议** | `mcp client mcn host mcpai` | 2.1 | 12% | 数字生命卡兹克 (51%) |
| #32 | 93 | **读者热议作者爆肝行为** | `mj666 tag discord 12 emm` | 5.1 | 47% | 数字生命卡兹克 (88%) |
| #33 | 91 | **GLM-5能力与价格引热议** | `glm5 glm glm51 glm47 plan` | 3.2 | 12% | 数字生命卡兹克 (51%) |
| #34 | 88 | **技术圈内卷进行时** | `run tts 15 up emm` | 6.2 | 25% | 数字生命卡兹克 (61%) |
| #35 | 84 | **国内AI第一SOTA霸主** | `zhipu china sota no1 3000` | 1.8 | 42% | 数字生命卡兹克 (74%) |
| #36 | 82 | **杭州场报名咨询热** | `2050 base 50 ai ` | 1.7 | 45% | 数字生命卡兹克 (78%) |
| #37 | 82 | **扣子AI平台体验与讨论** | `space copliot codingskill nanobanana minimax` | 1.5 | 24% | 数字生命卡兹克 (63%) |
| #38 | 78 | **读者点赞感谢集锦** | `ruma luma nice star 99` | 1.0 | 85% | 数字生命卡兹克 (63%) |
| #39 | 76 | **OpenAI模型版本对比与困惑** | `o3 o1 o3mini 4o o4` | 2.3 | 11% | 数字生命卡兹克 (64%) |
| #40 | 76 | **AI默认五指与六指困境** | `ai6 ai5 4o6 gpt6 65` | 7.0 | 9% | 数字生命卡兹克 (100%) |
| #41 | 75 | **Harness工程：约束与自动驾驶** | `harness engineering context engine session` | 7.9 | 20% | 数字生命卡兹克 (55%) |
| #42 | 75 | **AI配图生成工具问答** | `notebooklm 2k remix doge svg` | 1.5 | 16% | 赛博禅心 (35%) |
| #43 | 74 | **主题43** | `qwenqwen kimiminimax app aq qwen` | 9.1 | 23% | 数字生命卡兹克 (66%) |
| #44 | 72 | **主题44** | `kiss kpi deep 17 ip` | 3.1 | 74% | 数字生命卡兹克 (67%) |
| #45 | 72 | **主题45** | `qwen qwen3 qwen35 36 max` | 1.5 | 17% | 数字生命卡兹克 (62%) |
| #46 | 71 | **主题46** | `3500    ` | 1.2 | 28% | 数字生命卡兹克 (72%) |
| #47 | 70 | **主题47** | `cherry codebuddy 2027 2028 tt` | 1.5 | 27% | 数字生命卡兹克 (69%) |
| #48 | 70 | **主题48** | `codeagent cuda seed20 gemma m3` | 9.0 | 24% | 赛博禅心 (49%) |
| #49 | 69 | **主题49** | `invalid 410 59 22 vivo50` | 0.1 | 3% | 赛博禅心 (90%) |
| #50 | 68 | **主题50** | `34 14 3232 2727 611` | 2.2 | 18% | 数字生命卡兹克 (69%) |
| #51 | 68 | **主题51** | `sft onpolicy sonnetsonnet qwen35397ba17b feedback` | 6.7 | 24% | 花叔 (46%) |
| #52 | 67 | **主题52** | `minimax minmax mini max minimaxm27` | 2.3 | 30% | 数字生命卡兹克 (58%) |
| #53 | 67 | **主题53** | `markdown html md mdhtml huashu` | 3.9 | 16% | 花叔 (40%) |
| #54 | 64 | **主题54** | `er skillgithub learn vpn fellou` | 1.8 | 9% | 数字生命卡兹克 (88%) |
| #55 | 63 | **主题55** | `45 911 91199 09 99` | 4.0 | 13% | 数字生命卡兹克 (57%) |
| #56 | 63 | **主题56** | `2223ai 115 23ai 2019 safari` | 8.0 | 52% | 数字生命卡兹克 (90%) |
| #57 | 62 | **主题57** | `manus openmanus mens at meta` | 2.6 | 18% | 数字生命卡兹克 (50%) |
| #58 | 61 | **主题58** | `lovart figma lovartai safari 05` | 11.3 | 23% | 数字生命卡兹克 (74%) |
| #59 | 60 | **主题59** | `agi most aiagi people agiagi` | 5.8 | 38% | 数字生命卡兹克 (52%) |
| #60 | 60 | **主题60** | `ar vr pico vivo vrar` | 3.1 | 43% | 数字生命卡兹克 (92%) |
| #61 | 59 | **主题61** | `t0 xhs tools 403 windows` | 2.2 | 8% | 数字生命卡兹克 (83%) |
| #62 | 59 | **主题62** | `grok grok3 grok4 groq xgrok` | 3.3 | 27% | 数字生命卡兹克 (76%) |
| #63 | 59 | **主题63** | `85 bing new gpu ` | 7.6 | 17% | 数字生命卡兹克 (71%) |
| #64 | 56 | **主题64** | `2026 2025 2024 2023 20200` | 5.6 | 45% | 数字生命卡兹克 (70%) |
| #65 | 55 | **主题65** | `aihot hot aifut aihotai app` | 4.9 | 53% | 数字生命卡兹克 (98%) |
| #66 | 55 | **主题66** | `svip 23ai 16g boss bgm` | 10.6 | 56% | 数字生命卡兹克 (91%) |
| #67 | 54 | **主题67** | `    ` | 0.5 | 0% | 数字生命卡兹克 (83%) |
| #68 | 54 | **主题68** | `as we absolutely sure thats` | 5.2 | 15% | 数字生命卡兹克 (63%) |
| #69 | 54 | **主题69** | `emmm mod oppo eve ios` | 0.4 | 6% | 数字生命卡兹克 (67%) |
| #70 | 51 | **主题70** | `qq robot qqqq npx tm` | 2.1 | 2% | 数字生命卡兹克 (71%) |
| #71 | 50 | **主题71** | `bup call   ` | 1.5 | 86% | 数字生命卡兹克 (52%) |
| #72 | 50 | **主题72** | `eve 2000 midjourney seedance20 adobe` | 3.5 | 0% | 数字生命卡兹克 (74%) |
| #73 | 50 | **主题73** | `ollama getseed luma hot 2023` | 1.5 | 16% | 数字生命卡兹克 (68%) |
| #74 | 50 | **主题74** | `vb kun 21 qwen ai` | 4.8 | 44% | 数字生命卡兹克 (62%) |
| #75 | 49 | **主题75** | `genspark 45 trae claude ` | 2.0 | 61% | 数字生命卡兹克 (76%) |
| #76 | 49 | **主题76** | `bar agi agibar barai 3w` | 5.7 | 45% | 赛博禅心 (96%) |
| #77 | 48 | **主题77** | `v4 dsv4 ds4 v3 v4pro` | 2.2 | 21% | 数字生命卡兹克 (60%) |
| #78 | 47 | **主题78** | `ikun 25   ` | 4.7 | 21% | 数字生命卡兹克 (68%) |
| #79 | 46 | **主题79** | `    ` | 1.3 | 2% | 数字生命卡兹克 (100%) |
| #80 | 45 | **主题80** | `100ai top1 bushi aiaiai aiai` | 29.1 | 31% | 数字生命卡兹克 (98%) |
| #81 | 45 | **主题81** | `turing lecun 2028 xp xai` | 5.0 | 27% | 数字生命卡兹克 (64%) |
| #82 | 44 | **主题82** | `ai3000 530 7000 ipad 800` | 7.2 | 23% | 数字生命卡兹克 (100%) |
| #83 | 43 | **主题83** | `lv10 lv1 lv 678 78` | 0.4 | 28% | 数字生命卡兹克 (98%) |
| #84 | 42 | **主题84** | `plan coding codingplan glmcoding planglm` | 4.1 | 12% | 数字生命卡兹克 (48%) |
| #85 | 42 | **主题85** | `clawdbot clawbot doctor plusgemini fix` | 2.7 | 14% | 数字生命卡兹克 (88%) |
| #86 | 41 | **主题86** | `uxai hc uiai vr appapp` | 6.6 | 24% | 数字生命卡兹克 (85%) |
| #87 | 41 | **主题87** | `tt 54 24 11 15` | 3.6 | 22% | 数字生命卡兹克 (100%) |
| #88 | 40 | **主题88** | `ka21 ka21ka21   ` | 7.6 | 60% | 数字生命卡兹克 (98%) |
| #89 | 40 | **主题89** | `150 qq 3000 yyds app` | 20.2 | 35% | 数字生命卡兹克 (92%) |
| #90 | 40 | **主题90** | `28 gamma agi gpt5 666` | 4.8 | 88% | 数字生命卡兹克 (92%) |
| #91 | 40 | **主题91** | `salute fomo ta emm ` | 3.2 | 25% | 数字生命卡兹克 (100%) |
| #92 | 40 | **主题92** | `    ` | 3.8 | 80% | 赛博禅心 (92%) |
| #93 | 40 | **主题93** | `vai gptds 33 aiai ai` | 1.9 | 18% | 数字生命卡兹克 (92%) |
| #94 | 39 | **主题94** | `02 level tts case 666666666` | 4.6 | 31% | 数字生命卡兹克 (97%) |
| #95 | 39 | **主题95** | `emm windows   ` | 0.0 | 21% | 赛博禅心 (79%) |
| #96 | 37 | **主题96** | `moss googleai alignment 54 llm` | 16.0 | 8% | 数字生命卡兹克 (89%) |
| #97 | 37 | **主题97** | `glmai 12 ps glm 666` | 5.6 | 41% | 数字生命卡兹克 (95%) |
| #98 | 37 | **主题98** | `rpa airpa xpath automate 2w` | 7.2 | 41% | 数字生命卡兹克 (92%) |
| #99 | 36 | **主题99** | `see gay eve id hhh` | 15.9 | 33% | 数字生命卡兹克 (50%) |
| #100 | 36 | **主题100** | `coze cozeskill cozeapi md skills` | 2.2 | 25% | 数字生命卡兹克 (64%) |
| #101 | 36 | **主题101** | `lol gif cc openai ` | 5.0 | 67% | 数字生命卡兹克 (92%) |
| #102 | 35 | **主题102** | `666 66666 666666 996 6666` | 1.2 | 89% | 数字生命卡兹克 (60%) |
| #103 | 35 | **主题103** | `deepseekgpu gpu 45 10 chatgpt` | 7.2 | 11% | 数字生命卡兹克 (49%) |
| #104 | 35 | **主题104** | `veo3 veo medeo veo2 veo31` | 2.0 | 31% | 数字生命卡兹克 (94%) |
| #105 | 34 | **主题105** | `workbuddy free control remote work` | 1.0 | 18% | 数字生命卡兹克 (79%) |
| #106 | 34 | **主题106** | `ing python xx it ` | 2.9 | 15% | 数字生命卡兹克 (85%) |
| #107 | 34 | **主题107** | `switch ccswitch cc cask apiopencode` | 1.5 | 41% | 数字生命卡兹克 (94%) |
| #108 | 34 | **主题108** | `ascii intuitive   ` | 2.6 | 18% | 数字生命卡兹克 (50%) |
| #109 | 33 | **主题109** | `1m clawdbot ai  ` | 0.8 | 9% | 数字生命卡兹克 (55%) |
| #110 | 33 | **主题110** | `2000 aiaiai ai  ` | 19.1 | 76% | 数字生命卡兹克 (100%) |
| #111 | 33 | **主题111** | `sql cli agent  ` | 1.2 | 15% | 数字生命卡兹克 (76%) |
| #112 | 32 | **主题112** | `hermes hermesskill switch engineering agent` | 0.8 | 16% | 数字生命卡兹克 (69%) |
| #113 | 31 | **主题113** | `mj wow respect up 666` | 6.3 | 100% | 数字生命卡兹克 (87%) |
| #114 | 30 | **主题114** | `tapnow blender handoff aws tapnowskills` | 1.4 | 7% | 数字生命卡兹克 (90%) |
| #115 | 30 | **主题115** | `broken right 19 ai ` | 15.1 | 10% | 数字生命卡兹克 (97%) |

## 4. 高赞主题 Top 15(读者最认可)

| 排名 | LLM 起名 | 评论数 | 平均点赞 | 代表词 |
|---|---|---|---|---|
| 1 | **主题80** | 45 | 29.1 | `100ai top1 bushi aiaiai aiai ai` |
| 2 | **主题89** | 40 | 20.2 | `150 qq 3000 yyds app ` |
| 3 | **主题110** | 33 | 19.1 | `2000 aiaiai ai   ` |
| 4 | **Anthropic：AI安全与竞争漩涡** | 128 | 16.5 | `anthropic anthropicai anthropicclaude dario anthropicceo able` |
| 5 | **主题96** | 37 | 16.0 | `moss googleai alignment 54 llm 4o` |
| 6 | **主题99** | 36 | 15.9 | `see gay eve id hhh you` |
| 7 | **主题115** | 30 | 15.1 | `broken right 19 ai  ` |
| 8 | **数字生命与记忆永恒** | 125 | 12.5 | `id remember live 365 2077 now` |
| 9 | **主题58** | 61 | 11.3 | `lovart figma lovartai safari 05 tapnow` |
| 10 | **主题66** | 55 | 10.6 | `svip 23ai 16g boss bgm pr` |
| 11 | **AI视频生成模型热议** | 141 | 10.1 | `sora sora2 seedance20 sota case seedance` |
| 12 | **腾讯元宝与微信AI生态热议** | 198 | 10.1 | `ima wechat 255 dm agentprompt r1api` |
| 13 | **卡兹克AI实操分享** | 574 | 9.1 | `bai all skill do 3ai doge` |
| 14 | **主题43** | 74 | 9.1 | `qwenqwen kimiminimax app aq qwen 2023` |
| 15 | **主题48** | 70 | 9.0 | `codeagent cuda seed20 gemma m3 emo` |

## 5. 负面率高的主题 Top 10(读者不满方向)

| 排名 | LLM 起名 | 评论数 | 负面率 | 代表词 |
|---|---|---|---|---|
| 1 | **主题79** | 46 | 89% | `     ` |
| 2 | **主题106** | 34 | 68% | `ing python xx it  ` |
| 3 | **主题91** | 40 | 65% | `salute fomo ta emm  ` |
| 4 | **主题87** | 41 | 63% | `tt 54 24 11 15 llm` |
| 5 | **主题63** | 59 | 59% | `85 bing new gpu  ` |
| 6 | **主题68** | 54 | 56% | `as we absolutely sure thats important` |
| 7 | **主题49** | 69 | 48% | `invalid 410 59 22 vivo50 this` |
| 8 | **主题70** | 51 | 47% | `qq robot qqqq npx tm doge` |
| 9 | **AI视频生成模型热议** | 141 | 45% | `sora sora2 seedance20 sota case seedance` |
| 10 | **AI幻觉的多元探讨** | 146 | 42% | `whisper mbti aiai70 box llm aillm` |

## 6. 各号读者 Top 5 主题

### 数字生命卡兹克

| 主题 | 评论数 | 代表词 |
|---|---|---|
| **AI平权与认知博弈** | 19876 | `deepseek ai agent aiai token` |
| **卡神粉丝技术崇拜圈** | 2919 | `666 2024 nb tim 2026` |
| **Claude Code使用讨论** | 817 | `claude code claudecode claudeclaude codexclaude` |
| **getseed产品与网络黑话** | 702 | `cos geo ntr kiss first` |
| **飞书多维表格AI工作流** | 642 | `aily wps cli notion claw` |

### 宝玉AI

| 主题 | 评论数 | 代表词 |
|---|---|---|
| **AI平权与认知博弈** | 897 | `deepseek ai agent aiai token` |
| **宝玉老师技能分享** | 223 | `baoyuskill skills gem kol example` |
| **Claude Code使用讨论** | 71 | `claude code claudecode claudeclaude codexclaude` |
| **提示词优化与使用心得** | 62 | `cosplay you are above ii` |
| **Vibe Coding实战与AI编程体验** | 29 | `vibe coding vibecoding codingai vide` |

### 赛博禅心

| 主题 | 评论数 | 代表词 |
|---|---|---|
| **AI平权与认知博弈** | 5049 | `deepseek ai agent aiai token` |
| **大聪明酒吧整活集锦** | 397 | `bar call svg colab 169` |
| **getseed产品与网络黑话** | 269 | `cos geo ntr kiss first` |
| **Claude Code使用讨论** | 180 | `claude code claudecode claudeclaude codexclaude` |
| **社群入群与交流讨论** | 125 | `200 21 612 1226 qq` |

### 花叔

| 主题 | 评论数 | 代表词 |
|---|---|---|
| **AI平权与认知博弈** | 1283 | `deepseek ai agent aiai token` |
| **读者盛赞花叔强大技能** | 219 | `aiskill skill powerful promax kind` |
| **Claude Code使用讨论** | 146 | `claude code claudecode claudeclaude codexclaude` |
| **Cursor AI编程工具使用讨论** | 41 | `cursor cursorcursor codevs directory rvc` |
| **getseed产品与网络黑话** | 32 | `cos geo ntr kiss first` |

## 7. 主要省份 Top 3 关注主题

### 广东(14,951 条)
- 5497 条:**AI平权与认知博弈**
- 550 条:**卡神粉丝技术崇拜圈**
- 273 条:**Claude Code使用讨论**

### 北京(11,840 条)
- 4242 条:**AI平权与认知博弈**
- 494 条:**卡神粉丝技术崇拜圈**
- 185 条:**getseed产品与网络黑话**

### 上海(7,832 条)
- 2827 条:**AI平权与认知博弈**
- 289 条:**卡神粉丝技术崇拜圈**
- 136 条:**getseed产品与网络黑话**

### 浙江(6,433 条)
- 2339 条:**AI平权与认知博弈**
- 244 条:**卡神粉丝技术崇拜圈**
- 135 条:**Claude Code使用讨论**

### 江苏(3,986 条)
- 1469 条:**AI平权与认知博弈**
- 151 条:**卡神粉丝技术崇拜圈**
- 58 条:**Claude Code使用讨论**

### 四川(2,816 条)
- 1052 条:**AI平权与认知博弈**
- 126 条:**卡神粉丝技术崇拜圈**
- 48 条:**Claude Code使用讨论**

### 山东(2,503 条)
- 901 条:**AI平权与认知博弈**
- 122 条:**卡神粉丝技术崇拜圈**
- 34 条:**getseed产品与网络黑话**

## 8. 反推选题清单(planner 输入)

**综合排序**:`平均点赞 × log(评论数) × 正面率`

| 排名 | 主题 | 评论数 | 平均点赞 | 正面率 | 代表词 |
|---|---|---|---|---|---|
| 1 | **主题80** | 45 | 29.1 | 31% | `100ai / top1 / bushi / aiaiai / aiai` |
| 2 | **主题110** | 33 | 19.1 | 76% | `2000 / aiaiai / ai /  / ` |
| 3 | **Anthropic：AI安全与竞争漩涡** | 128 | 16.5 | 32% | `anthropic / anthropicai / anthropicclaude / dario / anthropicceo` |
| 4 | **卡兹克AI实操分享** | 574 | 9.1 | 60% | `bai / all / skill / do / 3ai` |
| 5 | **主题89** | 40 | 20.2 | 35% | `150 / qq / 3000 / yyds / app` |
| 6 | **数字生命与记忆永恒** | 125 | 12.5 | 40% | `id / remember / live / 365 / 2077` |
| 7 | **AI平权与认知博弈** | 27,105 | 5.8 | 32% | `deepseek / ai / agent / aiai / token` |
| 8 | **主题99** | 36 | 15.9 | 33% | `see / gay / eve / id / hhh` |
| 9 | **主题66** | 55 | 10.6 | 56% | `svip / 23ai / 16g / boss / bgm` |
| 10 | **卡神粉丝技术崇拜圈** | 2,947 | 4.4 | 71% | `666 / 2024 / nb / tim / 2026` |
| 11 | **腾讯元宝与微信AI生态热议** | 198 | 10.1 | 30% | `ima / wechat / 255 / dm / agentprompt` |
| 12 | **AI视频生成模型热议** | 141 | 10.1 | 22% | `sora / sora2 / seedance20 / sota / case` |
| 13 | **主题56** | 63 | 8.0 | 52% | `2223ai / 115 / 23ai / 2019 / safari` |
| 14 | **主题58** | 61 | 11.3 | 23% | `lovart / figma / lovartai / safari / 05` |
| 15 | **主题96** | 37 | 16.0 | 8% | `moss / googleai / alignment / 54 / llm` |
| 16 | **Kimi AI使用与功能讨论** | 228 | 6.6 | 41% | `kimi / kimikimi / k2 / k26 / kimikimikimi` |
| 17 | **主题113** | 31 | 6.3 | 100% | `mj / wow / respect / up / 666` |
| 18 | **getseed产品与网络黑话** | 1,017 | 5.6 | 33% | `cos / geo / ntr / kiss / first` |
| 19 | **主题115** | 30 | 15.1 | 10% | `broken / right / 19 / ai / ` |
| 20 | **主题88** | 40 | 7.6 | 60% | `ka21 / ka21ka21 /  /  / ` |