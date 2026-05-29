"""
风云写作 lint — harness 内循环的自动 critic 层

检测 voice-dna.md anti-patterns + Vision 违规
每次 Claude 写完 / 改完文章后必须跑这个 lint
输出: violations 清单 + 修改建议

⚠️ Bug 7 分工注释(2026-05-25 Round 17 · WRITE_AGENT.md v1.0):
    本 lint 只检查 **markdown 内容** 维度(R0-R25 二十多条规则),
    跟 layout_rules.lint 分工清晰、不重叠:
    - fengyun_lint.lint_article(md) → Step 4 内容 gate(本文件)
    - layout_rules.lint(html)       → Step 8 HTML gate(渲染后微信兼容性)
    两者都跑、各管一段,不要合并。Gate.py 只看本文件结果决定 Step 4 lint_pass。
"""
from __future__ import annotations
import sys, re, json
from pathlib import Path
from dataclasses import dataclass, asdict, field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Violation:
    rule_id: str
    severity: str  # "high" | "medium" | "low"
    category: str
    issue: str
    matches: list = field(default_factory=list)  # 具体匹配位置
    fix: str = ""


# ===== Anti-pattern 词典(从 voice-dna.md Part 3 + 5 + 6) =====

AI_BUZZWORDS = ["降维打击", "信息茧房", "赛道", "破圈", "顶流",
                "爆款逻辑", "流量密码", "硬核", "干货", "大佬",
                "整活", "底层逻辑", "卷王"]

KAZIK_HABITS = ["鬼使神差", "不是哥们", "老阴逼", "属实", "抽象",
                "整活", "尼玛"]

AI_WRITING_MARKERS = ["此外", "与此同时", "与.{0,5}保持一致", "至关重要",
                      "深入探讨", "持久的", "增强", "凸显", "强调",
                      "格局", "织锦", "证明", "宝贵的", "充满活力的"]

# 焦虑贩卖词
# Bug 6 修复(2026-05-25 Round 17 · WRITE_AGENT.md v1.0):
#   原版「替代」「落后」是纯字面字符串,跟 R13 anxiety_signals 词典冲突
#   (R13 要求深度文前 60% 出现「替代/失业/落后」等焦虑建立词;R8 要求全文不出现)。
#   改成「指着读者吓」的精确语境 regex 后,中性焦虑建立(「被替代风险」「技术落后」)
#   归 R13 计数,R8 只抓标题党式恐吓。
#
#   关键区分:
#     R13 中性建立(放过):被 AI 替代的风险 / 替代风险存在 / 技术落后的代价
#     R8 焦虑贩卖(抓):AI 会替代你 / 马上替代所有人 / 落后于时代你就输了
#   区分点 = 是否有「你/我们/所有人/大家/每个人」直指读者
ANXIETY_TRIGGERS = [
    "你还没", "再不", "就完了", "就晚了", "就输了",
    "淘汰", "倒计时", "9.\\d?%",
    "燃烧着活",  # 风云特别加入
    # 「替代」必须直指读者(替代你 / 替代我们 / 替代所有人)才算焦虑贩卖
    r"替代.{0,4}(你|我们|所有人|大家|每个人)",
    # 「落后」必须带主体指向(再不学就落后 / 落后于时代 + 你的)
    r"再不.{0,8}(落后|输了|完了|晚了)",
    r"落后.{0,4}(于|了).{0,4}(时代|别人|世界|同行).{0,8}(你|我们)",
]

# 古人典故关键词(出现时要审查上下文)
ALLUSION_KEYWORDS = ["韩信", "孙膑", "司马迁", "孔明", "诸葛亮",
                     "庄子", "老子", "孟子", "孔子", "李白",
                     "杜甫", "苏轼", "陶渊明", "屈原", "项羽"]

# 英式中文(翻译腔)词典 v0 — 2026-05-21 用户截图实指 + 王小波 perspective 诊断
# 规则:每条带「翻译腔表达 → 母语替代」对照
# 严格条件(Musk × Jobs 共识):必须从真实诊断里来,不凭空列举
ENGLISH_LIKE_CHINESE = {
    "沉默了一会儿": "愣了一下 / 放下书发了一会儿呆 / 心里突然堵了一下",
    "沉默了片刻": "愣了一下 / 想了想",
    "有点沉": "心里堵了一下 / 心里沉了下去",
    "有些沉": "心里堵了一下 / 心里沉了下去",
    "那束光": "那点东西 / 那点亮 / 那点星火",
    "那道光": "那点东西 / 那点亮 / 那点星火",
    "看看天上的云": "看看云 / 看看天",
    "感到": "(直接说感觉,删掉「感到」)",
    "感受到": "(直接描述感觉,「我读完心里堵了一下」而不是「我感受到心里堵了一下」)",
}


# ===== R18:商业机密 / 自暴 AI 生成 三级分级 + 白名单 =====
# 2026-05-23 Musk × Jobs Round 2 元辩论共识:
#   废弃一刀切 high severity,改为 P0/P1/P2 三级:
#     P0(明确自指 AI 身份)→ critic_vote aborted_r18(阻断所有兜底,强制人工)
#     P1(架构 / skill / 工具栈暴露)→ revise(不阻断,让 writer 改)
#     P2(自动化流程暴露)→ revise + 计入触发率统计(给 r18_dashboard.py)
#   加白名单豁免讨论 AI 行业的正常表述(「AI 公司」「AI 辅助」等中性词)

# R18-P0:明确自指 AI 身份(读者感知致命,Musk Round 1 指出威胁面)
R18_P0_PATTERNS = [
    (r'本文.{0,5}(由|经|用).{0,5}(AI|人工智能|语言模型|大模型|Claude|GPT|Gemini|Sonnet|Opus)',
     "本文由 AI 生成自指"),
    (r'(作为)(一个|个)?(AI|人工智能|语言模型|大模型|机器人|助手)',
     "作为 AI 自指"),
    (r'(AI|大模型|Claude).{0,5}(帮我|代我|替我|为我).{0,5}(写|生成|创作|输出)',
     "AI 代写自指"),
]

# R18-P1:架构 / skill 名 / 工具栈暴露
R18_P1_PATTERNS = [
    (r'我的.{0,5}(harness|writer|critic|pipeline|工作流|自动化流程|发布系统|三轨)',
     "架构自暴"),
    (r'(经过|跑了).{0,5}(N 轮|多轮)?(critic|lint)(评审|修复)?',
     "评审流程自暴"),
    (r'(fengyun-writer|fengyun-publish|fengyun_lint|huashu-perspective|wangxiaobo-perspective)',
     "skill 名暴露"),
    (r'(豆包 Seedream|DeepSeek API|Anthropic API).{0,15}(我|本号)(的)?.{0,5}(选|工具|栈)',
     "工具栈自暴"),
]

# R18-P2:自动化流程暴露
R18_P2_PATTERNS = [
    (r'(自动 ship|cron 发布|Task Scheduler|headless)',
     "自动化流程自暴"),
]

# 白名单上下文(±30 字窗口检测,命中后豁免)
# 防止讨论 Anthropic / Claude 行业动态时正常表述被误判
R18_WHITELIST_CONTEXTS = [
    r'AI 公司',
    r'AI 行业',
    r'AI 时代',
    r'AI 辅助',
    r'(Claude|GPT|AI).{0,10}(帮助|赋能).{0,10}(用户|开发者|创作者|读者)',
]


def _r18_whitelisted(body: str, m) -> bool:
    """检查命中是否落在白名单上下文里(±30 字窗口)"""
    win_start = max(0, m.start() - 30)
    win_end = min(len(body), m.end() + 30)
    window = body[win_start:win_end]
    for wp in R18_WHITELIST_CONTEXTS:
        if re.search(wp, window):
            return True
    return False


def _scan_r18(body: str, patterns: list) -> list:
    """扫描一组 R18 patterns,带白名单过滤"""
    hits = []
    for pat, label in patterns:
        for m in re.finditer(pat, body):
            if _r18_whitelisted(body, m):
                continue
            prev = max(0, m.start() - 10)
            nxt = min(len(body), m.end() + 10)
            ctx = body[prev:nxt].replace("\n", "↵")
            hits.append(f"[{label}] 「{ctx}」")
    return hits


def strip_fm(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text


def parse_fm_meta(text: str) -> dict:
    """从 markdown 文件头部 frontmatter 提取 key: value 元数据。

    只解析顶层 key: value(不支持嵌套 / 列表)。返回 dict。
    无 frontmatter 时返回 {}。
    """
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_block = parts[1]
    meta = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            meta[k] = v
    return meta


# ===== R19-R25: huashu 风格专属规则(仅在 frontmatter style: huashu 时触发) =====
# 花叔(huashu)风格特征(来自 huashu-perspective skill 校准):
#   - 平均段长 50-80 字(短促,有节奏感)
#   - 独段成行 4-9 处(关键句单独成段)
#   - H2 标题用 3 种模式:概念陈述句 / 口语动词句 / 汉字数字
#   - 零 emoji(花叔不在正文用 emoji 装饰)
#   - 零 CTA(花叔结尾不求关注转发)
#   - 长段 <= 8%(>200 字段落极少)
#   - 省略号 <= 1 处(避免文艺腔)

# 关键约束:emoji 范围必须避开 CJK 统一表意区(U+4E00-U+9FFF)
# 这些 block 都不与 CJK 重叠,可以安全使用
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002600-\U000026FF"  # misc symbols
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols & pictographs
    "\U0001FA70-\U0001FAFF"  # symbols & pictographs extended-A
    "\U0001F004"             # mahjong
    "\U0001F0CF"             # playing cards
    "]",
    flags=re.UNICODE,
)

HUASHU_CTA_PATTERNS = ["点赞", "转发", "关注", "求三连", "扫码", "二维码",
                       "觉得有用", "点个在看", "右下角", "公众号矩阵"]

HUASHU_CHINESE_NUMERALS = {"一", "二", "三", "四", "五", "六", "七", "八", "九", "十"}


def _huashu_body_paras(body: str) -> list:
    """切分正文段(排除 H1/H2/H3 / 图片 / 引用)"""
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return [p for p in paras
            if not p.startswith("#")
            and not p.startswith("!")
            and not p.startswith(">")]


def _r19_huashu_avg_para_length(body: str):
    """R19:平均段长 50-80 字(中文字数)"""
    body_paras = _huashu_body_paras(body)
    chinese_counts = [len(re.findall(r"[一-鿿]", p)) for p in body_paras]
    if not chinese_counts:
        return None
    avg = sum(chinese_counts) / len(chinese_counts)
    if 50 <= avg <= 80:
        return None
    return Violation(
        rule_id="R19_huashu_avg_para_length",
        severity="medium",
        category="huashu_style",
        issue=f"平均段长 {avg:.1f} 不在花叔风格区间 50-80",
        fix="花叔段落短促有节奏:目标平均段长 50-80 字;过长拆分,过短合并"
    )


def _r20_huashu_solo_lines(body: str):
    """R20:<20 字独段成行 >= 4 处(花叔特征不足时告警)"""
    body_paras = _huashu_body_paras(body)
    solo_count = sum(1 for p in body_paras
                     if len(re.findall(r"[一-鿿]", p)) < 20)
    if solo_count >= 4:
        return None
    return Violation(
        rule_id="R20_huashu_solo_lines",
        severity="medium",
        category="huashu_style",
        issue=f"独段成行 {solo_count} 处 < 花叔目标 4-9",
        fix="花叔风格要把关键句单独成段(<20 字),目标 4-9 处;增加几个独立短句段"
    )


def _r21_huashu_h2_pattern(body: str):
    """R21:每个 H2 命中 3 种模式之一(概念陈述句 / 口语动词句 / 汉字数字)"""
    h2_lines = re.findall(r"^## (.+)$", body, re.MULTILINE)
    violations = []
    for h2 in h2_lines:
        h2 = h2.strip()
        # 模式 3:汉字数字(可加空格)
        h2_compact = h2.replace(" ", "")
        if h2_compact in HUASHU_CHINESE_NUMERALS:
            continue
        # 模式 1:概念陈述句(含 是/不是/就是,无问号,长度 5-25)
        if (any(w in h2 for w in ["是", "不是", "就是"])
                and "?" not in h2 and "?" not in h2
                and 5 <= len(h2) <= 25):
            continue
        # 模式 2:口语动词句(以「我」/「我们」开头,长度 5-25)
        if (h2.startswith("我") or h2.startswith("我们")) and 5 <= len(h2) <= 25:
            continue
        violations.append(Violation(
            rule_id="R21_huashu_h2_pattern",
            severity="medium",
            category="huashu_style",
            issue=f"H2 '{h2}' 不命中花叔 3 种模式",
            fix="花叔 H2 三种模式:① 概念陈述句(含 是/不是/就是) "
                "② 口语动词句(我/我们开头) ③ 汉字数字(一/二/三...)"
        ))
    return violations


def _r22_huashu_emoji_zero(body: str):
    """R22:emoji 数 == 0(命中即 error,必改)"""
    matches = EMOJI_PATTERN.findall(body)
    if not matches:
        return None
    return Violation(
        rule_id="R22_huashu_emoji_zero",
        severity="high",
        category="huashu_style",
        issue=f"花叔风格 emoji 必须为 0,检测到 {len(matches)} 处",
        matches=[str(m) for m in matches[:5]],
        fix="花叔正文不用 emoji 装饰 — 全部删除"
    )


def _r23_huashu_cta_zero(body: str):
    """R23:不含 CTA 模式(命中即 error,必改)"""
    matches = [w for w in HUASHU_CTA_PATTERNS if w in body]
    if not matches:
        return None
    return Violation(
        rule_id="R23_huashu_cta_zero",
        severity="high",
        category="huashu_style",
        issue=f"花叔风格结尾零 CTA,检测到: {matches}",
        matches=matches,
        fix="花叔不在结尾做 CTA(点赞/关注/扫码等),全部删除"
    )


def _r24_huashu_long_para_ratio(body: str):
    """R24:>200 字段落 / 总段数 <= 8%"""
    body_paras = _huashu_body_paras(body)
    if not body_paras:
        return None
    long_count = sum(1 for p in body_paras
                     if len(re.findall(r"[一-鿿]", p)) > 200)
    ratio = long_count / len(body_paras)
    if ratio <= 0.08:
        return None
    return Violation(
        rule_id="R24_huashu_long_para_ratio",
        severity="medium",
        category="huashu_style",
        issue=f"长段(>200字)占比 {ratio:.1%} 超过花叔目标 8%",
        fix="花叔避免长段堆叠,目标 >200 字段落占比 <= 8%;拆分长段为多个短段"
    )


def _r25_huashu_ellipsis(body: str):
    """R25:省略号 …/... 出现 <= 1 处"""
    count = body.count("……") + body.count("...") + body.count("…")
    # 注意:"……" 是 2 个 "…",所以单独计 "……" 后还要避免重复计 "…"
    # 简化:直接按 "……" 和 "..." 这两种分隔符计,再加单独的 "…"
    # 但 "……".count("…") = 2,会双倍计。改用更精确的统计
    count_ellip_cn = len(re.findall(r"…+", body))   # 中文省略号连续(……/…计 1)
    count_ellip_en = len(re.findall(r"\.{3,}", body))  # 英文省略号 ...
    total = count_ellip_cn + count_ellip_en
    if total <= 1:
        return None
    return Violation(
        rule_id="R25_huashu_ellipsis",
        severity="medium",
        category="huashu_style",
        issue=f"省略号 {total} 处超过花叔目标 ≤1",
        fix="花叔避免省略号文艺腔,目标全文 <= 1 处;改用句号或具体表达"
    )


def _r26_huashu_bold_per_para(body: str):
    """R26(Round 23 新增,2026-05-25):每段 bold ≤ 1 处。

    Musk × Jobs 共识:单段注意力 spotlight 只能制造 1 个有效异常 chunk。
    用户原话:「严禁一段落上去一大堆无用的标注突出」「找最好的几句话分开进行标注突出」
    花叔 corpus 抽查:单段从不堆 2 处 bold,与此约束一致。
    """
    body_paras = _huashu_body_paras(body)
    offending = []
    for i, para in enumerate(body_paras):
        bolds = re.findall(r"\*\*([^*\n]+)\*\*", para)
        if len(bolds) >= 2:
            preview = para[:40].replace("\n", " ")
            offending.append(f"段{i+1}({len(bolds)}处):「{preview}…」")
    if not offending:
        return None
    return Violation(
        rule_id="R26_huashu_bold_per_para",
        severity="medium",
        category="huashu_style",
        issue=f"{len(offending)} 段 bold ≥ 2 处(花叔每段最多 1 处金句)",
        matches=offending[:5],
        fix="花叔风格每段只允许 1 处 bold 金句;删段内次要高亮,保留最值得带走的那句"
    )


def _r27_huashu_bold_total(body: str):
    """R27(Round 23 新增,2026-05-25):全文 bold ≤ 5 处(working memory 4±1 chunk 上限)。

    短文(< 1000 字)按比例缩放,允许 3 处。
    Musk 第一性原理:高亮的物理功能是「让扫读者带走核心」— 超过 5 处变装饰噪音。
    Jobs:「Innovation is saying no to 1000 things」— 高亮的本质是稀缺性。
    """
    bolds = re.findall(r"\*\*([^*\n]+)\*\*", body)
    n = len(bolds)
    n_chars = len(re.sub(r"\s", "", body))
    cap = 3 if n_chars < 1000 else 5
    if n <= cap:
        return None
    return Violation(
        rule_id="R27_huashu_bold_total",
        severity="medium",
        category="huashu_style",
        issue=f"全文 bold {n} 处 > {cap} 处上限({n_chars} 字)",
        matches=[f"前 5 处: {bolds[:5]}"],
        fix=f"花叔风格全文 bold ≤ {cap} 处金句;删除装饰高亮,保留最值得带走的几句"
    )


def _r28_huashu_bold_minimum(body: str):
    """R28(Round 24 新增,2026-05-25):B 类长文 bold ≥ 3 处(最低金句数量)。

    跟 R27(全文 ≤ 5 上限)互补:
      - R27 设 upper bound(防堆砌)
      - R28 设 lower bound(防裸文)

    B 类长文判定:全文 ≥ 3000 字(总字符数,非纯 CJK — 技术文含大量英文术语)。
    短线(如试稿/短文 < 3000)不触发 — R26 段密度兜底即可。

    e2e 实测发现:主线程有时跳过 Step 7.3 内文图后,连带跳过写 bold 的意愿。
    此规则确保长文至少有 3 处读者可以「带走」的核心金句。

    Round 25 修:阈值从 3500 CJK 降为 3000 总字数(技术文 CJK 占比低,
    如 TrapDoor 文 4358 总字但仅 2810 CJK,原阈值漏检)。
    """
    # 用总字符数(去空白)而非纯 CJK,与 R12 字数规则一致
    n_chars = len(re.sub(r"\s+", "", body))
    if n_chars < 3000:
        return None
    bolds = re.findall(r"\*\*([^*\n]+)\*\*", body)
    n = len(bolds)
    if n >= 3:
        return None
    return Violation(
        rule_id="R28_huashu_bold_minimum",
        severity="medium",
        category="huashu_style",
        issue=f"B 类长文({n_chars} 字)全文 bold 仅 {n} 处 < 3 处最低金句下限",
        matches=bolds[:3] if bolds else ["(全文无粗体)"],
        fix="B 类长文需要至少 3 处核心金句加粗(读者可以「带走」的句子);"
            "检查文章最有冲击力的 3-5 句话,确保至少 3 处有 **金句** 加粗"
    )


def _scan_huashu_rules(body: str) -> list:
    """整合 R19-R28 十条 huashu 专属规则。

    Round 23 新增 R26 + R27 段落 / 全文 bold 密度规则。
    Round 24 新增 R28 B 类长文 bold 最低下限规则。
    """
    violations = []
    for fn in [_r19_huashu_avg_para_length,
               _r20_huashu_solo_lines,
               _r22_huashu_emoji_zero,
               _r23_huashu_cta_zero,
               _r24_huashu_long_para_ratio,
               _r25_huashu_ellipsis,
               _r26_huashu_bold_per_para,   # Round 23 段密度
               _r27_huashu_bold_total,       # Round 23 全文密度上限
               _r28_huashu_bold_minimum]:    # Round 24 全文密度下限
        v = fn(body)
        if v:
            violations.append(v)
    violations.extend(_r21_huashu_h2_pattern(body))
    return violations


def lint_article(md_path: Path) -> dict:
    raw = md_path.read_text(encoding="utf-8")
    body = strip_fm(raw)
    fm_meta = parse_fm_meta(raw)
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    n_paras = len(paras)
    n_chars = sum(1 for c in body if c.strip())

    violations: list[Violation] = []

    # === Rule 0: 全角标点检测(P0 — 2026-05-21 风云铁律) ===
    # 中文上下文里的英文半角标点必须替换为全角
    # 例外:数字/英文之间(如 2026-05-21 / Mythos v3)、URL、代码块
    halfwidth_punct_violations = []
    # 中文字符 + 英文标点(后跟中文或空白/句末)
    # 标点集合:, . ; : ! ? " ' ( )
    cn = r"[一-鿿]"
    halfwidth_pat = re.compile(
        rf"({cn})([,;:!?])(?={cn}|\s|$)"
    )
    for m in halfwidth_pat.finditer(body):
        prev = max(0, m.start() - 5)
        nxt = min(len(body), m.end() + 5)
        ctx = body[prev:nxt].replace("\n", "↵")
        halfwidth_punct_violations.append(f"「{ctx}」(半角{m.group(2)})")

    # 句号特殊处理:中文 + . + (空格|换行|句末|中文)
    # Bug 5 修复(2026-05-25 Round 17):排除技术标识符
    #   .env / .md / .py / .yaml / .cursorrules 等扩展名 — 点后紧跟字母不是句号
    #   v1.0 / v3.0 / 2.35:1 等版本号 — 点前后都是数字
    # (?![a-zA-Z]) 排除扩展名;(?<!\d) 起手已由 cn 类约束(必中文)
    period_pat = re.compile(rf"({cn})(\.)(?![a-zA-Z0-9])(?=\s|$|{cn})")
    for m in period_pat.finditer(body):
        prev = max(0, m.start() - 5)
        nxt = min(len(body), m.end() + 5)
        ctx = body[prev:nxt].replace("\n", "↵")
        halfwidth_punct_violations.append(f"「{ctx}」(半角.)")

    # 英文双引号 " 和单引号 '(在中文上下文里)
    dquote_pat = re.compile(rf'({cn})(")')
    for m in dquote_pat.finditer(body):
        prev = max(0, m.start() - 5)
        nxt = min(len(body), m.end() + 5)
        ctx = body[prev:nxt].replace("\n", "↵")
        halfwidth_punct_violations.append(f"「{ctx}」(半角双引号)")

    squote_pat = re.compile(rf"({cn})(')")
    for m in squote_pat.finditer(body):
        prev = max(0, m.start() - 5)
        nxt = min(len(body), m.end() + 5)
        ctx = body[prev:nxt].replace("\n", "↵")
        halfwidth_punct_violations.append(f"「{ctx}」(半角单引号)")

    # 英文圆括号
    paren_pat = re.compile(rf"({cn})([()])|([()]){cn}")
    for m in paren_pat.finditer(body):
        prev = max(0, m.start() - 5)
        nxt = min(len(body), m.end() + 5)
        ctx = body[prev:nxt].replace("\n", "↵")
        halfwidth_punct_violations.append(f"「{ctx}」(半角括号)")

    if halfwidth_punct_violations:
        violations.append(Violation(
            rule_id="R0_halfwidth_punctuation",
            severity="high",
            category="punctuation",
            issue=f"中文上下文出现 {len(halfwidth_punct_violations)} 处英文半角标点",
            matches=halfwidth_punct_violations[:8],
            fix=", ; : ! ?  → , ; : ! ? / . → 。 / \" → \"\" / ' → '' / () → ()(全角)"
                "  数字/英文之间标点不动(如 2026-05-21 / Mythos v3)"
        ))

    # === Rule 1: 中文方括号「」 ===
    bracket_pat = re.compile(r"[「『][^」』]+[」』]")
    bracket_matches = bracket_pat.findall(body)
    if bracket_matches:
        violations.append(Violation(
            rule_id="R1_brackets",
            severity="high",
            category="symbol",
            issue=f"使用了禁用的 「」/『』 共 {len(bracket_matches)} 次",
            matches=bracket_matches[:5],
            fix='全部 「...」 改为 中文双引号 "..."(voice-dna anti-pattern 3.4)'
        ))

    # === Rule 2: 「笔者」频次过载 ===
    bizhe_count = body.count("笔者")
    bizhe_limit = max(1, int(n_paras * 0.15))
    if bizhe_count > bizhe_limit:
        violations.append(Violation(
            rule_id="R2_bizhe_overload",
            severity="medium",
            category="voice",
            issue=f"「笔者」用了 {bizhe_count} 次,超过限额 {bizhe_limit}(段落数 × 15%)",
            fix='哲思段保留「笔者」/普通叙事用「我」/抒情段省略主语,混用'
        ))

    # === Rule 3: 感叹号连排 ===
    excl_pat = re.compile(r"[!!]{2,}")
    excl_matches = excl_pat.findall(body)
    if excl_matches:
        violations.append(Violation(
            rule_id="R3_exclam_stack",
            severity="low",
            category="symbol",
            issue=f"连续感叹号 {len(excl_matches)} 处",
            matches=excl_matches[:3],
            fix="最多 1 个感叹号,改用句号或感叹词"
        ))

    # === Rule 4: 破折号堆叠 ===
    dash_stack_pat = re.compile(r"——.{2,30}——")
    dash_matches = dash_stack_pat.findall(body)
    if dash_matches:
        violations.append(Violation(
            rule_id="R4_dash_stack",
            severity="low",
            category="symbol",
            issue=f"破折号堆叠 {len(dash_matches)} 处",
            matches=dash_matches[:3],
            fix="不用破折号做补充,改逗号 + 新句子"
        ))

    # === Rule 5: AI 圈套话 ===
    ai_buzzword_hits = []
    for w in AI_BUZZWORDS:
        if w in body:
            ai_buzzword_hits.append(w)
    if ai_buzzword_hits:
        violations.append(Violation(
            rule_id="R5_ai_buzzwords",
            severity="high",
            category="vocabulary",
            issue=f"出现 AI 圈套话: {', '.join(ai_buzzword_hits)}",
            fix="替换成风云式表达(温和、具体、不抽象)"
        ))

    # === Rule 6: 卡兹克口头禅 ===
    kazik_hits = [w for w in KAZIK_HABITS if w in body]
    if kazik_hits:
        violations.append(Violation(
            rule_id="R6_kazik_habits",
            severity="high",
            category="style",
            issue=f"出现卡兹克口头禅: {', '.join(kazik_hits)}",
            fix="System B 不模仿卡兹克 — 全部删掉"
        ))

    # === Rule 7: AI 写作味 ===
    ai_marker_hits = []
    for pat in AI_WRITING_MARKERS:
        if re.search(pat, body):
            ai_marker_hits.append(pat)
    if ai_marker_hits:
        violations.append(Violation(
            rule_id="R7_ai_writing_markers",
            severity="medium",
            category="vocabulary",
            issue=f"AI 写作标记词: {', '.join(ai_marker_hits[:5])}",
            fix="用 humanizer-zh 24 条标准清理"
        ))

    # === Rule 8: 焦虑贩卖词(Vision 5.1) === ⭐ 最重要
    # Bug 7 修复 2026-05-24:加 ±15 字白名单上下文检测,
    # 避免「不可替代」「无可替代」「难以替代」这种正面短语被误判
    ANXIETY_WHITELIST_PHRASES = [
        "不可替代", "无可替代", "难以替代", "独一无二",
        "不可或缺", "不会被替代", "无法被替代", "不会取代",
        "不被取代", "不可被取代",
    ]
    anxiety_hits = []
    for pat in ANXIETY_TRIGGERS:
        # 不用 findall,用 finditer 以拿到位置 + 检查白名单
        for m in re.finditer(pat, body):
            win_start = max(0, m.start() - 8)
            win_end = min(len(body), m.end() + 8)
            window = body[win_start:win_end]
            # 白名单命中则豁免
            if any(wp in window for wp in ANXIETY_WHITELIST_PHRASES):
                continue
            anxiety_hits.append(m.group(0))
            if len(anxiety_hits) >= 6:  # 同一规则最多 6 个 sample
                break
    if anxiety_hits:
        violations.append(Violation(
            rule_id="R8_anxiety_triggers",
            severity="high",
            category="vision",
            issue=f"违反 Vision 5.1「不制造焦虑」: {', '.join(anxiety_hits)}",
            fix='风云目标是「让读者拥抱 AI 而不是焦虑」 — 删除或改写为温和句'
        ))

    # === Rule 9 已删除 ===
    # 「典故突兀检测」 — Musk 评审:「前段 30 字」阈值无出处,假约束包装成真约束
    # 典故的自然程度交给 founder verdict(灵魂判断,不交给机械 lint)

    # === Rule 10: 章节标题缺失(AI 主题文章) ===
    h2_count = len(re.findall(r"^##\s", body, flags=re.M))
    h3_count = len(re.findall(r"^###\s", body, flags=re.M))
    if h2_count == 0 and h3_count == 0 and n_chars > 1500:
        violations.append(Violation(
            rule_id="R10_no_chapters",
            severity="high",
            category="structure",
            issue=f"AI 主题文章 {n_chars} 字,但没有 ## / ### 章节标题",
            fix="加 3-5 个章节,每章节有突出小标题(voice-dna 铁律 6.4)"
        ))

    # === Rule 11: 段落数过多(碎片化) — 仅对深度文 ===
    is_deep_article = n_chars >= 2000  # AI 深度文判定
    if is_deep_article and n_paras > 0 and n_chars / n_paras < 50:
        violations.append(Violation(
            rule_id="R11_too_fragmented",
            severity="medium",
            category="structure",
            issue=f"AI 深度文平均段长 {n_chars // n_paras} 字(< 50),太碎",
            fix="深度文段落 100-200 字,只有需要重点突出的才单独成段"
        ))

    # === Rule 12: 字数硬约束(AI 深度文 4000-5000) ===
    # 检测是否 AI 深度文(看标题 + 主题关键词)
    title_match = re.search(r"title:\s*(.+)$", raw, re.M)
    title_str = title_match.group(1) if title_match else ""
    ai_keywords = ["AI", "Anthropic", "Claude", "GPT", "Mythos", "Skills",
                   "Karpathy", "Cursor", "Sora", "AGI", "LLM", "OpenAI", "Agent"]
    is_ai_topic = any(kw in title_str or kw in raw[:500] for kw in ai_keywords)

    # R12 字数硬约束 — Musk 2026-05-21 反馈:对齐风云原话 4000-5000
    if is_ai_topic:
        if n_chars < 4000:
            gap = 4000 - n_chars
            violations.append(Violation(
                rule_id="R12_word_count_too_short",
                severity="high",
                category="depth",
                issue=f"AI 深度文 {n_chars} 字 < 4000 下限(距目标差 {gap} 字)",
                fix=f"字数硬约束 4000-5000 字 — PHASE1_FACTS 数据归纳的爆款区间。还需写 {gap} 字"
            ))
        elif n_chars > 5000:
            over = n_chars - 5000
            violations.append(Violation(
                rule_id="R12_word_count_too_long",
                severity="medium",
                category="depth",
                issue=f"AI 深度文 {n_chars} 字 > 5000 上限(超 {over} 字)",
                fix=f"字数硬约束 4000-5000 字,需精简 {over} 字"
            ))

        # Round 21 P0-17:HTML 上限预警(huashu 模板渲染膨胀 ~5x,60000 上限)
        # 估算 HTML 字节 = markdown 字符 × 5(huashu inline style 膨胀系数)
        # 60000 ÷ 5 = 12000 字 markdown 是 HTML 安全水位
        est_html_bytes = n_chars * 5
        if est_html_bytes > 50000:  # warn at 50k(留 10k 缓冲到 60k 硬上限)
            violations.append(Violation(
                rule_id="R12b_html_size_warn",
                severity="low",
                category="layout",
                issue=f"markdown {n_chars} 字 × 5 ≈ {est_html_bytes} HTML chars,接近微信 60000 上限",
                fix="huashu 模板渲染会膨胀 ~5x,若超 60000 layout_rules.lint 会拦。考虑精简或拆篇"
            ))

    # === Rule 13: 焦虑建立检测(深度文必须先建立焦虑再安抚) ===
    if is_ai_topic and n_chars > 2000:
        # Round 19 P0-5 (2026-05-25):R8 R13「替代」矛盾分开词典
        # 之前:R8 抓「替代」做焦虑贩卖、R13 也用「替代」做焦虑建立 → 同词双重判定矛盾。
        # 现修:R13 删单字「替代」,改用「被替代」「替代风险」精确短语(中性焦虑建立)
        #       R8 保留 `替代.{0,4}(你|我们|所有人|...)` 精确正则(焦虑贩卖)
        # 不再冲突。R8 和 R13 词典物理隔离。
        anxiety_signals = ["攻破", "击穿", "拆开", "焦虑", "失控", "警告", "威胁",
                          "Schneier", "贝利", "FSB", "拒绝", "封禁", "断", "落后",
                          "被替代", "替代风险", "失业", "不确定", "未知", "速度", "无人理解"]
        consolation_signals = ["不慌", "不怕", "泡杯茶", "看看云", "我们也一直都在",
                              "亲爱的朋友", "(*∩_∩*)", "(^(エ)^)", "ᵔᴥᵔ", "祝你"]

        # 切分前 60% 和后 40%(用于焦虑建立检测)
        threshold_60 = int(n_chars * 0.6)
        char_count = 0
        first_60 = ""
        for p in paras:
            char_count += sum(1 for c in p if c.strip())
            if char_count <= threshold_60:
                first_60 += p + "\n"

        anxiety_in_first60 = sum(1 for s in anxiety_signals if s in first_60)

        # R13:深度文前 60% 必须建立至少 3 个焦虑点
        if anxiety_in_first60 < 3:
            violations.append(Violation(
                rule_id="R13_insufficient_anxiety_buildup",
                severity="high",
                category="craft",
                issue=f"AI 深度文前 60% 只建立 {anxiety_in_first60} 个焦虑点(<3)",
                fix="前 60% 必须呈现 ≥3 个具体焦虑点(攻防不对称/监管警告/失控/替代等)"
                    "才让读者进入信息密集区,后段安抚才有着陆点"
            ))

        # R14:前 40% 严禁安抚词(Musk+Jobs 共识比之前 70% 更严格)
        threshold_40 = int(n_chars * 0.4)
        char_count = 0
        first_40 = ""
        for p in paras:
            char_count += sum(1 for c in p if c.strip())
            if char_count <= threshold_40:
                first_40 += p + "\n"

        consolation_in_first40 = [s for s in consolation_signals if s in first_40]
        if consolation_in_first40:
            violations.append(Violation(
                rule_id="R14_premature_consolation",
                severity="high",
                category="craft",
                issue=f"文章前 40% 出现安抚词: {', '.join(consolation_in_first40[:3])}",
                fix="安抚词只能在后 60% 出现,且前 60% 须先建立 ≥3 焦虑点"
            ))

    # === Rule 16: 段尾悬空(Musk+Jobs 议题 1 共识 — 禁段尾悬空) ===
    if is_ai_topic:
        # 全文最后一个非颜文字非签名段
        actual_paras = [p for p in paras if not any(em in p for em in
                       ["(*∩_∩*)", "(^(エ)^)", "ᵔᴥᵔ", "邮箱", "微信", "@"])]
        if actual_paras:
            last_para = actual_paras[-1]
            last_para_len = sum(1 for c in last_para if c.strip())
            if last_para_len < 15:
                violations.append(Violation(
                    rule_id="R16_dangling_ending",
                    severity="medium",
                    category="structure",
                    issue=f"末段悬空: 末段只 {last_para_len} 字('{last_para[:50]}')",
                    fix="深度文末段不能 < 15 字独立短句 — 必须有收尾论点 / 末句收束"
                ))

    # === Rule 15 已删除 ===
    # 「列举 vs 论证 / 思想深度」 — 风云 2026-05-21 反馈:
    # "思想深度根本难以量化,我不认可"
    # critic 只查机械可执行规则,思想深度交给作者(风云本人)和读者反馈
    # 不让 critic 做 LLM 主观判断

    # === Rule 17: 英式中文(翻译腔)词典 v0 ===
    # 2026-05-21 Musk × Jobs 元辩论 + 风云截图实指
    # 严格条件:词典只收录已被 founder verdict 标记的翻译腔词,不凭空列举
    # 严格条件 2:同时配王小波 perspective skill 做长尾覆盖(Step 0.5,SKILL.md)
    english_like_hits = []
    for phrase, native_alt in ENGLISH_LIKE_CHINESE.items():
        if phrase in body:
            english_like_hits.append((phrase, native_alt))
    if english_like_hits:
        matches_display = [f"{p} → {alt}" for p, alt in english_like_hits[:5]]
        violations.append(Violation(
            rule_id="R17_english_like_chinese",
            severity="high",
            category="native_voice",
            issue=f"翻译腔词典命中 {len(english_like_hits)} 处英式中文表述",
            matches=matches_display,
            fix="用王小波 perspective skill 做语感预审 + 替换为母语表达"
                "(Claude 写中文不要先想英文再翻译 — 直接从中文神经回路生成)"
        ))

    # === Rule 18: 商业机密 / 自暴 AI 生成 三级分级 + 白名单 ===
    # 2026-05-23 Musk × Jobs Round 2 共识:
    #   P0 → critic_vote aborted_r18(强制人工,跳过所有兜底)
    #   P1 → revise(让 writer 改,不阻断)
    #   P2 → revise + 触发率统计(r18_dashboard.py 监控,> 阈值时修 L1)
    r18_p0_hits = _scan_r18(body, R18_P0_PATTERNS)
    r18_p1_hits = _scan_r18(body, R18_P1_PATTERNS)
    r18_p2_hits = _scan_r18(body, R18_P2_PATTERNS)

    if r18_p0_hits:
        violations.append(Violation(
            rule_id="R18_P0_self_as_ai",
            severity="high",
            category="business_secret",
            issue=f"⛔ R18-P0(明确自指 AI 身份)→ aborted_r18:命中 {len(r18_p0_hits)} 处",
            matches=r18_p0_hits[:8],
            fix="必须删除或重写命中段。critic_vote 多轮模式遇到此规则会跳过所有兜底,"
                "强制人工介入。详见 fengyun-writer SKILL.md「⛔ 商业机密 / 自暴绝对禁令」"
        ))
    if r18_p1_hits:
        violations.append(Violation(
            rule_id="R18_P1_architecture_leak",
            severity="medium",
            category="business_secret",
            issue=f"⚠️ R18-P1(架构 / skill / 工具栈暴露)→ revise:命中 {len(r18_p1_hits)} 处",
            matches=r18_p1_hits[:8],
            fix="改稿删除内部架构词 / skill 名 / 工具栈自指。不阻断 ship,但 writer 必须改。"
                "r18_dashboard.py 会统计:P1 周触发 > 2 → 修 L1 writer SKILL.md"
        ))
    if r18_p2_hits:
        violations.append(Violation(
            rule_id="R18_P2_automation_leak",
            severity="low",
            category="business_secret",
            issue=f"💭 R18-P2(自动化流程暴露)→ revise + 统计:命中 {len(r18_p2_hits)} 处",
            matches=r18_p2_hits[:8],
            fix="改稿删除自动化流程提及。r18_dashboard.py 统计:"
                "P2 周触发 > 3 → 评估升级为 P1"
        ))

    # === Rule 19: PHASE1 致命组合(2026-05-24 Round 7 P0)===
    # PHASE1_FACTS §扑街致命组合 — 实测扑街率 36-46%(4× 基线)
    # 组合 A 扑街率 45.7%(4.56× 基线):标题英文 < 7 + 一行一段 > 50% + 平均词长 > 1.8
    # 组合 B 扑街率 41.7%:标题英文 < 7 + 一行一段 > 50% + 正文英文占比 > 0.2
    # 组合 C 扑街率 36.1%:标题/正文比 > 0 + 标题英文 < 7 + 一行一段 > 50%
    if is_ai_topic and n_chars > 1500:
        # 1. title 英文字符数
        t_en_chars = len(re.findall(r"[a-zA-Z]", title_str))
        # 2. 短段比例(<50 字)≈「一行一段」近似
        body_paras = [p for p in paras if not p.startswith("##")]
        short_paras = sum(1 for p in body_paras
                          if sum(1 for c in p if c.strip()) < 50)
        oneline_ratio = short_paras / max(1, len(body_paras))
        # 3. 平均词长:中文 1.0/词,英文 word 长度
        n_zh = sum(1 for c in body if "一" <= c <= "鿿")
        en_words = re.findall(r"[a-zA-Z]+", body)
        n_en_words = len(en_words)
        en_total_chars = sum(len(w) for w in en_words)
        total_words = n_zh + n_en_words
        avg_word_len = ((n_zh + en_total_chars) / total_words) if total_words > 0 else 1.0
        # 4. 正文英文占比
        n_text_chars = sum(1 for c in body if c.strip())
        body_en_ratio = en_total_chars / max(1, n_text_chars)
        # 5. title/body 比
        n_title_chars = sum(1 for c in title_str if c.strip())
        title_body_ratio = n_title_chars / max(1, n_text_chars)

        # 三个致命组合检测
        # Round 7 监督修复:combo_c 原条件 title_body_ratio > 0 永远为真,
        # 退化为两变量,跟 PHASE1 三变量定义不符。
        # 找不到精确分位切点 → 暂只保留 combo A/B,combo C 注释掉等 PHASE1 出处确认
        combo_a = (t_en_chars < 7 and oneline_ratio > 0.5
                   and avg_word_len > 1.8)
        combo_b = (t_en_chars < 7 and oneline_ratio > 0.5
                   and body_en_ratio > 0.2)
        # combo_c TODO: 等从 PHASE1_FACTS 查 title_body_ratio 真实分位切点(应为 ~0.05+)
        # 当前规则 > 0 是 bug,删掉避免假报。规则待精确分位后再启用

        combos_hit = []
        if combo_a:
            combos_hit.append(
                f"组合 A(扑街 4.56× 基线): 标题英文 {t_en_chars}<7 + "
                f"短段比 {oneline_ratio:.0%}>50% + 平均词长 {avg_word_len:.2f}>1.8"
            )
        if combo_b:
            combos_hit.append(
                f"组合 B(扑街 4.17× 基线): 标题英文 {t_en_chars}<7 + "
                f"短段比 {oneline_ratio:.0%}>50% + 正文英文占比 {body_en_ratio:.0%}>20%"
            )

        if combos_hit:
            violations.append(Violation(
                rule_id="R19_lethal_combo",
                severity="high",
                category="phase1_lethal",
                issue=f"⛔ PHASE1 致命组合命中 {len(combos_hit)} 个(扑街率 36-46%)",
                matches=combos_hit,
                fix="改稿避开命中维度:① 加标题英文产品名(Anthropic/Claude/Skills 等 ≥7 字符) "
                    "② 增加平均段长减少短段比(目标 80-150 字/段) "
                    "③ 降低正文英文占比 < 20%"
            ))

    # === Rule 20: 图密度(被动观察,2026-05-24 Round 9 改 info-only)===
    # 用户原话「图密度那个不要拦截,没图片的文章不一定不是好文章」(2026-05-24)
    # 配图决策已移交 huashu-image-curator skill + tools/illustrate_decider.py
    # R20 仅作为数据飞轮被动观察值,severity=info,不计 violations 不阻断 ship
    if is_ai_topic and n_chars > 1500:
        n_inline_imgs = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", body))
        img_per_1k = n_inline_imgs / (n_chars / 1000.0) if n_chars else 0

        if img_per_1k < 1.0:
            violations.append(Violation(
                rule_id="R20_image_density_low",
                severity="info",
                category="phase1_image_density",
                issue=(f"💭 内文图密度 {img_per_1k:.2f} 张/千字 < 1.0 "
                       f"(可接受 — 没图片的文章不一定不是好文章)"),
                fix=(f"当前 {n_inline_imgs} 张 / {n_chars} 字。Step 7 huashu-image-curator "
                     f"已自行判断不出图。如需出图请检查 illustrate_decider 日志")
            ))
        elif img_per_1k > 3.0:
            violations.append(Violation(
                rule_id="R20_image_density_high",
                severity="info",
                category="phase1_image_density",
                issue=(f"💭 内文图密度 {img_per_1k:.2f} 张/千字 > 3.0 "
                       f"(可接受 — 数据飞轮被动观察用)"),
                fix=f"如需减少,在 huashu-image-curator Mode 2 决策时调整"
            ))

    # === Huashu R19-R25(仅在 frontmatter style: huashu 时触发)===
    # 2026-05-24 加入:花叔(huashu)风格专属 7 条规则
    # 零回归保证:其他风格文章完全不触发
    if fm_meta.get("style") == "huashu":
        violations.extend(_scan_huashu_rules(body))

    # === Rule 21: 粗体意识检测(2026-05-24 修正 humanizer-zh #14 over-correction)===
    # 风云铁律:不抓粗体数量,只抓「无意义粗体」
    #   - 粗体数量 > 8 + 平均粗体内容长度 < 10 字 → 警告(AI 假装强调可能性高)
    #   - 否则不触发(深度长文 3-5 处金句粗体是健康的,不要 over-correct)
    # 跨域错配修复:voice-dna「哲思文几乎无粗体」是 corpus/growth/ 短文统计观察,
    # 不适用于 AI 深度长文(4000-5000 字)。后者需要视觉锚点扫读,是物理约束。
    bold_matches = re.findall(r'\*\*([^\*\n]+)\*\*', body)
    n_bold = len(bold_matches)
    if n_bold > 8:
        avg_len = sum(len(b) for b in bold_matches) / max(1, n_bold)
        if avg_len < 10:
            violations.append(Violation(
                rule_id="R21_bold_ai_padding",
                severity="medium",
                category="bold_meaning",
                issue=f"⚠️ 粗体 {n_bold} 处 + 平均长度 {avg_len:.1f} 字 < 10(AI 假装强调可能性)",
                matches=[f"「{b}」" for b in bold_matches[:5]],
                fix="检查每处粗体后的句子能否独立成「金句」(读者带走的那一句);"
                    "无意义的粗体 → 删;深度长文 3-5 处金句粗体是健康的,不要 over-correct"
            ))

    return {
        "article": str(md_path),
        "stats": {
            "n_paragraphs": n_paras,
            "n_chars_non_space": n_chars,
            "avg_para_len": n_chars // max(1, n_paras),
            "h2_count": h2_count,
            "h3_count": h3_count,
        },
        "style": fm_meta.get("style", ""),
        "violations": [asdict(v) for v in violations],
        "n_violations": len(violations),
        "severity_counts": {
            "high": sum(1 for v in violations if v.severity == "high"),
            "medium": sum(1 for v in violations if v.severity == "medium"),
            "low": sum(1 for v in violations if v.severity == "low"),
        }
    }


def pretty(result: dict):
    print(f"=== Lint: {Path(result['article']).name} ===\n")
    s = result["stats"]
    print(f"统计: {s['n_chars_non_space']} 字 / {s['n_paragraphs']} 段 / "
          f"平均段长 {s['avg_para_len']} 字 / H2={s['h2_count']} H3={s['h3_count']}\n")

    sc = result["severity_counts"]
    print(f"违规总数: {result['n_violations']}  "
          f"(🚨{sc['high']} high  ⚠️{sc['medium']} medium  💭{sc['low']} low)\n")

    if result["n_violations"] == 0:
        print("✅ 全部通过 anti-patterns + Vision 检查\n")
        return

    sev_icon = {"high": "🚨", "medium": "⚠️", "low": "💭"}
    for v in result["violations"]:
        print(f"{sev_icon.get(v['severity'], '?')} [{v['rule_id']}] {v['category']}/{v['severity']}")
        print(f"   问题: {v['issue']}")
        if v["matches"]:
            for m in v["matches"][:3]:
                print(f"   样本: {m}")
        print(f"   修复: {v['fix']}\n")


def main():
    if len(sys.argv) < 2:
        # 默认 lint 风云版第一篇
        target = Path(r"D:\Dev\ai-wechat-pipeline\output\drafts\20260521-anthropic-mythos-fengyun.md")
    else:
        target = Path(sys.argv[1])

    if not target.exists():
        print(f"❌ 文件不存在: {target}")
        sys.exit(1)

    result = lint_article(target)
    pretty(result)

    # 保存 JSON
    out_path = target.with_suffix(".lint.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON 报告: {out_path}")


if __name__ == "__main__":
    main()
