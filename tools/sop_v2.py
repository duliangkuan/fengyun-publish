"""
SOP v2 多维度评分系统(可被其他脚本 import)

核心思路:
  composite_pct = 0.40*read + 0.20*share + 0.15*like + 0.15*old_like + 0.10*comment
  ↓ 每个 sub-target 单独建一个维度规则,各维度内规则的 feature 选择基于
  pre-2026 训练集上 ρ(feat, sub_target) 的真实大小,而不是猜测。

  每维度评分 0-100(基线 50),total_score 按 composite_pct 同权重加权。

输出结构(sop_score_v2 返回 dict):
  total_score / read_score / share_score / like_score / old_like_score / comment_score
  rules_triggered: 每条触发的规则,标明 dim、加减分、类型(bonus/penalty)
  suggestions:按预期收益排序的改进建议(只针对扣分项 + 未拿到的 bonus)

# 数据来源 (ρ 自 tools/_sop_v2_corr_probe.py 在 pre-2026 训练集 n=2106 上计算)
# 详见 reports/_sop_v2_feature_rho.csv,规则不在 2026 H1 hold-out 上调参。
"""
from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

# ============================================================
# 品牌词(来自 deep dive 6 brand_words.md,跨期稳定)
# ============================================================
BRAND_HOT = {
    "skills": re.compile(r"\b[Ss]kills?\b"),
    "claude_code": re.compile(r"[Cc]laude\s*[Cc]ode|claude-code"),
    "claude": re.compile(r"\b[Cc]laude\b"),
    "anthropic": re.compile(r"\b[Aa]nthropic\b"),
    "karpathy": re.compile(r"[Kk]arpathy"),
    "vibe_coding": re.compile(r"[Vv]ibe\s*[Cc]oding"),
    "agent": re.compile(r"[Aa]gent|智能体"),
}
BRAND_COLD = {
    "openai_gpt": re.compile(r"\bGPT\b|[Oo]pen[Aa][Ii]"),
    "veo": re.compile(r"\b[Vv]eo\d?\b"),
    "glm": re.compile(r"\bGLM\b|智谱"),
}


def cover_family(r, g, b):
    """RGB → 色族;对齐 deep dive 7 cover_color_deep.md"""
    if pd.isna(r) or pd.isna(g) or pd.isna(b):
        return "missing"
    r, g, b = int(r), int(g), int(b)
    if r > 220 and g > 220 and b > 220:
        return "white"
    if r < 60 and g < 60 and b < 60:
        return "dark"
    if abs(r - g) < 20 and abs(g - b) < 20 and abs(r - b) < 20:
        return "gray"
    if r > 180 and 80 < g < 200 and b < 130 and r > b + 50 and r >= g:
        return "orange"
    if b > r + 20 and b > g + 20 and b > 100:
        return "blue"
    if r > 180 and r > g + 40 and r > b + 30:
        return "red"
    if g > r + 30 and g > b + 20:
        return "green"
    return "other"


def _g(row, key, default=0):
    """安全取值;NaN/None 都视为 default"""
    v = row.get(key, default) if hasattr(row, "get") else default
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return default
    return v


# ============================================================
# 各维度评分(每维度返回 score, triggered_rules, missed_bonuses)
# ============================================================

def score_read(row) -> tuple[float, list, list]:
    """read_score:预测打开率
    feature 选择依据(ρ vs read_pct,n=2106 train):
      - 标题/英文/字数 (deep dive 9: t_english 跨期稳定 Top 5)
      - 品牌词 (Skills/Claude 系热点 ρ via brand_words)
      - 封面色家族 (cover_r/g/b ρ=0.32 vs share, ρ=0.21 vs read,有效)
      - topic_hotness_30d/90d (ρ vs read=0.32-0.35,主题热点强信号)
      - current_event_words_in_title (时事词增强打开)
    """
    score = 50.0
    triggered, missed = [], []
    title = str(_g(row, "title", "") or "")

    # 1. 标题长度
    t_chars = _g(row, "t_chars", 0)
    if 20 <= t_chars <= 40:
        score += 3
        triggered.append({"dim":"read","rule":f"标题字数 {t_chars} 在 20-40 区间","delta":+3,"type":"bonus"})
    elif t_chars < 10:
        score -= 3
        triggered.append({"dim":"read","rule":f"标题过短({t_chars}字)","delta":-3,"type":"penalty"})
        missed.append({"action":"标题扩到 20-30 字,加修饰语","dim":"read","expected_delta":+6})

    # 2. 标题英文字数 (deep dive 8/9 唯一真规律)
    t_english = _g(row, "t_english_chars", 0)
    if t_english >= 8:
        score += 8
        triggered.append({"dim":"read","rule":f"标题英文字数 {t_english} (≥8)","delta":+8,"type":"bonus"})
    elif t_english >= 3:
        score += 3
        triggered.append({"dim":"read","rule":f"标题英文字数 {t_english} (≥3)","delta":+3,"type":"bonus"})
    else:
        score -= 3
        triggered.append({"dim":"read","rule":f"标题英文字数仅 {t_english}","delta":-3,"type":"penalty"})
        missed.append({"action":"标题加 1 个英文产品名/品牌(如 Claude Code/Skills)","dim":"read","expected_delta":+11})

    # 3. 品牌词
    brand_hits = []
    if BRAND_HOT["skills"].search(title):
        score += 15; brand_hits.append("Skills(+15)")
        triggered.append({"dim":"read","rule":"标题含 Skills(88.9%爆款率)","delta":+15,"type":"bonus"})
    if BRAND_HOT["claude_code"].search(title):
        score += 12; brand_hits.append("Claude Code(+12)")
        triggered.append({"dim":"read","rule":"标题含 Claude Code","delta":+12,"type":"bonus"})
    if BRAND_HOT["claude"].search(title) or BRAND_HOT["anthropic"].search(title):
        score += 10; brand_hits.append("Claude/Anthropic(+10)")
        triggered.append({"dim":"read","rule":"标题含 Claude/Anthropic","delta":+10,"type":"bonus"})
    if BRAND_HOT["vibe_coding"].search(title):
        score += 10; brand_hits.append("Vibe Coding(+10)")
        triggered.append({"dim":"read","rule":"标题含 Vibe Coding","delta":+10,"type":"bonus"})
    if BRAND_HOT["karpathy"].search(title):
        score += 6
        triggered.append({"dim":"read","rule":"标题含 Karpathy","delta":+6,"type":"bonus"})
    if BRAND_HOT["agent"].search(title):
        score += 3
        triggered.append({"dim":"read","rule":"标题含 Agent/智能体","delta":+3,"type":"bonus"})
    if BRAND_COLD["openai_gpt"].search(title):
        score -= 5
        triggered.append({"dim":"read","rule":"标题含 OpenAI/GPT(冷标签)","delta":-5,"type":"penalty"})
        missed.append({"action":"主品牌词换成 Claude/Anthropic","dim":"read","expected_delta":+15})
    if BRAND_COLD["veo"].search(title):
        score -= 6
        triggered.append({"dim":"read","rule":"标题含 Veo(冷标签)","delta":-6,"type":"penalty"})
    if BRAND_COLD["glm"].search(title):
        score -= 5
        triggered.append({"dim":"read","rule":"标题含 GLM/智谱(冷标签)","delta":-5,"type":"penalty"})
    if not brand_hits:
        missed.append({"action":"标题加 1 个热门品牌词(Skills/Claude/Anthropic)","dim":"read","expected_delta":+10})

    # 4. 封面
    has_cover = _g(row, "has_cover_color", 0)
    if has_cover == 0:
        score -= 10
        triggered.append({"dim":"read","rule":"无封面","delta":-10,"type":"penalty"})
        missed.append({"action":"补一张暖橙/白底封面图","dim":"read","expected_delta":+16})
    else:
        fam = cover_family(_g(row,"cover_r"), _g(row,"cover_g"), _g(row,"cover_b"))
        delta_map = {"white":+6,"orange":+8,"dark":+5,"blue":-6,"red":-6,"green":-3,"gray":+2,"other":0}
        d = delta_map.get(fam, 0)
        if d != 0:
            score += d
            ttype = "bonus" if d > 0 else "penalty"
            triggered.append({"dim":"read","rule":f"封面色家族={fam}","delta":d,"type":ttype})
            if d < 0:
                missed.append({"action":f"封面色换成暖橙(+8)或白底(+6),当前 {fam}({d:+d})","dim":"read","expected_delta":(8 - d)})

    # 5. topic_hotness_30d (主题热点)  阈值依据训练集分位: q75=0.56, q90=0.79
    hot30 = _g(row, "topic_hotness_30d", None)
    if hot30 is not None and not (isinstance(hot30, float) and np.isnan(hot30)):
        if hot30 >= 0.75:
            score += 8
            triggered.append({"dim":"read","rule":f"主题 30d 热度 {hot30:.2f} 前 10%","delta":+8,"type":"bonus"})
        elif hot30 >= 0.50:
            score += 4
            triggered.append({"dim":"read","rule":f"主题 30d 热度 {hot30:.2f} 中等偏热","delta":+4,"type":"bonus"})
        elif hot30 < 0.10:
            score -= 5
            triggered.append({"dim":"read","rule":f"主题 30d 热度 {hot30:.2f} 太冷","delta":-5,"type":"penalty"})
            missed.append({"action":"换个近 30d 内有人讨论的主题(Skills/Agent/Claude Code)","dim":"read","expected_delta":+13})

    # 6. 时事词 (current_event_words_in_title)  q90=0,有 1 个就是稀缺信号
    ce = _g(row, "current_event_words_in_title", 0)
    if ce >= 2:
        score += 5
        triggered.append({"dim":"read","rule":f"标题含时事词 {int(ce)} 个(稀缺)","delta":+5,"type":"bonus"})
    elif ce >= 1:
        score += 3
        triggered.append({"dim":"read","rule":f"标题含时事词","delta":+3,"type":"bonus"})

    return max(0, min(100, score)), triggered, missed


def score_share(row) -> tuple[float, list, list]:
    """share_score:预测转发率(20% 权重)
    feature 选择依据(ρ vs share_pct):
      - cover_brightness/r/g/b ρ≈0.32(share 最强信号,封面亮 → 转发)
      - b_para_avg_chars ρ=0.30 (段落写厚 → 转发)
      - b_chars/jb_word_count ρ≈0.29 (字数,长文转发)
      - jb_lexical_diversity ρ=-0.26 (词汇密度低 → 长文 → 转发)
      - tb_ratio ρ=-0.24 (标题/正文比小 → 转发)
      - b_periods ρ=0.25 (句号多 → 长文)
      - topic_hotness_90d ρ=0.38 (90d 主题热度对 share 也很强)
      - comment_long_ratio (深度评论 → 内容值得分享)
    """
    score = 50.0
    triggered, missed = [], []

    # 1. 字数(deep dive 10 calibration)
    b_chars = _g(row, "b_chars", 0)
    if 3500 <= b_chars <= 5500:
        score += 12
        triggered.append({"dim":"share","rule":f"正文 {b_chars}字 在 3500-5500 黄金区","delta":+12,"type":"bonus"})
    elif 5500 < b_chars <= 8000:
        score += 10
        triggered.append({"dim":"share","rule":f"正文 {b_chars}字 (5500-8000)","delta":+10,"type":"bonus"})
    elif 2500 <= b_chars < 3500:
        score += 5
        triggered.append({"dim":"share","rule":f"正文 {b_chars}字 (2500-3500)","delta":+5,"type":"bonus"})
        missed.append({"action":f"再加 1000-2000 字案例/数据,推到 3500-5500","dim":"share","expected_delta":+7})
    elif 1500 <= b_chars < 2500:
        score += 2
        triggered.append({"dim":"share","rule":f"正文 {b_chars}字 (1500-2500 略短)","delta":+2,"type":"bonus"})
        missed.append({"action":f"加 1500+ 字案例,推到 3500-5500 黄金区","dim":"share","expected_delta":+10})
    elif b_chars < 500:
        score -= 8
        triggered.append({"dim":"share","rule":f"正文仅 {b_chars}字 太短","delta":-8,"type":"penalty"})
        missed.append({"action":"扩到 3000+ 字,加完整案例/数据","dim":"share","expected_delta":+20})
    elif b_chars > 20000:
        score -= 10
        triggered.append({"dim":"share","rule":f"正文 {b_chars}字 过长","delta":-10,"type":"penalty"})

    # 2. 平均段长
    para_avg = _g(row, "b_para_avg_chars", 0)
    if para_avg >= 200:
        score += 8
        triggered.append({"dim":"share","rule":f"平均段长 {para_avg:.0f} ≥200","delta":+8,"type":"bonus"})
    elif para_avg >= 100:
        score += 4
        triggered.append({"dim":"share","rule":f"平均段长 {para_avg:.0f} ≥100","delta":+4,"type":"bonus"})
    elif 0 < para_avg < 50:
        score -= 4
        triggered.append({"dim":"share","rule":f"平均段长 {para_avg:.0f} <50 太碎","delta":-4,"type":"penalty"})
        missed.append({"action":"段落合并/扩写到平均 100+ 字","dim":"share","expected_delta":+8})

    # 3. 一行一段比例
    one_liner = _g(row, "b_one_liner_ratio", 0)
    if one_liner < 0.1:
        score += 6
        triggered.append({"dim":"share","rule":f"一行一段比 {one_liner:.0%} <10%","delta":+6,"type":"bonus"})
    elif one_liner > 0.7:
        score -= 12
        triggered.append({"dim":"share","rule":f"一行一段比 {one_liner:.0%} >70%","delta":-12,"type":"penalty"})
        missed.append({"action":"把碎句合并段落,降到 <30%","dim":"share","expected_delta":+15})
    elif one_liner > 0.5:
        score -= 6
        triggered.append({"dim":"share","rule":f"一行一段比 {one_liner:.0%} >50%","delta":-6,"type":"penalty"})
        missed.append({"action":"把碎句合并段落,降到 <30%","dim":"share","expected_delta":+9})

    # 4. 词汇多样性(负向,长文标志)
    lex_div = _g(row, "jb_lexical_diversity", 0.5)
    if lex_div < 0.42:
        score += 4
        triggered.append({"dim":"share","rule":f"词汇多样性 {lex_div:.2f} <0.42(长文)","delta":+4,"type":"bonus"})
    elif lex_div > 0.5:
        score -= 3
        triggered.append({"dim":"share","rule":f"词汇多样性 {lex_div:.2f} >0.5(短文)","delta":-3,"type":"penalty"})

    # 5. tb_ratio
    tb_r = _g(row, "tb_ratio", 0)
    if tb_r < 0.05:
        score += 3
        triggered.append({"dim":"share","rule":f"tb_ratio {tb_r:.3f} <0.05","delta":+3,"type":"bonus"})
    elif tb_r > 0.15:
        score -= 5
        triggered.append({"dim":"share","rule":f"tb_ratio {tb_r:.3f} >0.15 标题占比过大","delta":-5,"type":"penalty"})

    # 6. 图片密度
    img_density = _g(row, "img_per_1k_chars", 0)
    if 2 <= img_density <= 6:
        score += 6
        triggered.append({"dim":"share","rule":f"图片密度 {img_density:.1f}/千字 在 2-6","delta":+6,"type":"bonus"})
    elif 1 <= img_density < 2:
        score += 3
        triggered.append({"dim":"share","rule":f"图片密度 {img_density:.1f}/千字","delta":+3,"type":"bonus"})
    elif img_density > 12:
        score -= 5
        triggered.append({"dim":"share","rule":f"图片密度 {img_density:.1f}/千字 过高","delta":-5,"type":"penalty"})
    elif img_density == 0:
        score -= 3
        triggered.append({"dim":"share","rule":"无配图","delta":-3,"type":"penalty"})
        missed.append({"action":"加 3-6 张说明图(密度 2-6/千字)","dim":"share","expected_delta":+9})

    # 7. 封面亮度(share 最强信号 ρ=0.32)
    bright = _g(row, "cover_brightness", None)
    if bright is not None and not (isinstance(bright, float) and np.isnan(bright)):
        if bright >= 200:
            score += 5
            triggered.append({"dim":"share","rule":f"封面亮度 {bright:.0f} ≥200(明亮)","delta":+5,"type":"bonus"})
        elif bright < 80:
            score -= 3
            triggered.append({"dim":"share","rule":f"封面亮度 {bright:.0f} <80(暗)","delta":-3,"type":"penalty"})
            missed.append({"action":"封面换更亮的图(亮度≥200)","dim":"share","expected_delta":+8})

    # 8. topic_hotness_90d(ρ=0.38 in share)  阈值依据训练集分位: q75=0.40, q90=0.71
    hot90 = _g(row, "topic_hotness_90d", None)
    if hot90 is not None and not (isinstance(hot90, float) and np.isnan(hot90)):
        if hot90 >= 0.65:
            score += 6
            triggered.append({"dim":"share","rule":f"主题 90d 热度 {hot90:.2f} 前 10%","delta":+6,"type":"bonus"})
        elif hot90 >= 0.35:
            score += 3
            triggered.append({"dim":"share","rule":f"主题 90d 热度 {hot90:.2f} 中偏热","delta":+3,"type":"bonus"})
        elif hot90 < 0.10:
            score -= 4
            triggered.append({"dim":"share","rule":f"主题 90d 热度 {hot90:.2f} 太冷","delta":-4,"type":"penalty"})

    # 9. comment_long_ratio (评论深度 → 文章值得分享)  q75=0.44
    clr = _g(row, "comment_long_ratio", None)
    if clr is not None and not (isinstance(clr, float) and np.isnan(clr)):
        if clr >= 0.44:
            score += 3
            triggered.append({"dim":"share","rule":f"长评论比 {clr:.0%} 深度评论多","delta":+3,"type":"bonus"})

    # 致命组合
    one_liner = _g(row, "b_one_liner_ratio", 0)
    t_english = _g(row, "t_english_chars", 0)
    avg_word = _g(row, "jb_avg_word_len", 1.5)
    if t_english < 7 and one_liner > 0.5 and avg_word > 1.8:
        score -= 15
        triggered.append({"dim":"share","rule":"致命组合(短英文+一行一段>0.5+短词)","delta":-15,"type":"penalty"})
        missed.append({"action":"合并段落+加英文品牌词,打破致命组合","dim":"share","expected_delta":+20})

    return max(0, min(100, score)), triggered, missed


def score_like(row) -> tuple[float, list, list]:
    """like_score:预测点赞率(15% 权重)
    feature 依据(ρ vs like_pct):
      - topic_hotness_90d ρ=0.42 / topic_hotness_30d ρ=0.40(like 最强信号)
      - comment_at_ratio ρ=0.23(@别人 → 互动赞)
      - comment_avg_length ρ=0.19(评论长 → 文章引发深度反应)
      - action_verb_count ρ=0.21(动作动词 → 实用感)
      - cultural_meme(段子 → 点赞)
      - opinion_strength_markers(强观点)
    """
    score = 50.0
    triggered, missed = [], []

    # topic_hotness_90d  q75=0.40, q90=0.71
    hot90 = _g(row, "topic_hotness_90d", None)
    if hot90 is not None and not (isinstance(hot90, float) and np.isnan(hot90)):
        if hot90 >= 0.65:
            score += 10
            triggered.append({"dim":"like","rule":f"主题 90d 热度 {hot90:.2f} 前 10%(like 最强信号)","delta":+10,"type":"bonus"})
        elif hot90 >= 0.35:
            score += 5
            triggered.append({"dim":"like","rule":f"主题 90d 热度 {hot90:.2f} 中偏热","delta":+5,"type":"bonus"})
        elif hot90 < 0.10:
            score -= 6
            triggered.append({"dim":"like","rule":f"主题 90d 热度 {hot90:.2f} 太冷","delta":-6,"type":"penalty"})
            missed.append({"action":"选近 90d 内有讨论度的主题","dim":"like","expected_delta":+16})

    # topic_hotness_30d  q75=0.56, q90=0.79
    hot30 = _g(row, "topic_hotness_30d", None)
    if hot30 is not None and not (isinstance(hot30, float) and np.isnan(hot30)):
        if hot30 >= 0.75:
            score += 6
            triggered.append({"dim":"like","rule":f"主题 30d 热度 {hot30:.2f} 前 10%","delta":+6,"type":"bonus"})
        elif hot30 < 0.10:
            score -= 3
            triggered.append({"dim":"like","rule":f"主题 30d 热度 {hot30:.2f} 太冷","delta":-3,"type":"penalty"})

    # action_verb_count  q75=1.54, q90=2.66 (per-1k-chars density)
    av = _g(row, "action_verb_count", 0)
    if av >= 2.5:
        score += 6
        triggered.append({"dim":"like","rule":f"动作动词密度 {av:.2f} (高,实用感)","delta":+6,"type":"bonus"})
    elif av >= 1.0:
        score += 3
        triggered.append({"dim":"like","rule":f"动作动词密度 {av:.2f} (中)","delta":+3,"type":"bonus"})
    else:
        missed.append({"action":"加 3-5 个动作动词(做了/试了/写了/拆了),提升 av 密度到 1.5+","dim":"like","expected_delta":+6})

    # opinion_strength_markers  q75=3.05, q90=4.64 (per-1k-chars density)
    ops = _g(row, "opinion_strength_markers", 0)
    if ops >= 4.5:
        score += 4
        triggered.append({"dim":"like","rule":f"强观点密度 {ops:.2f}(高)","delta":+4,"type":"bonus"})
    elif ops >= 1.7:
        score += 2
        triggered.append({"dim":"like","rule":f"强观点密度 {ops:.2f}(中)","delta":+2,"type":"bonus"})
    else:
        missed.append({"action":"加 2-3 处强观点表态(我认为/必须/绝对)","dim":"like","expected_delta":+4})

    # cultural_meme (0 or 1)
    cm = _g(row, "cultural_meme", 0)
    if cm >= 1:
        score += 3
        triggered.append({"dim":"like","rule":"含梗/段子","delta":+3,"type":"bonus"})

    # comment_ip_diversity  q75=0.79
    ipd = _g(row, "comment_ip_diversity", None)
    if ipd is not None and not (isinstance(ipd, float) and np.isnan(ipd)):
        if ipd >= 0.79:
            score += 4
            triggered.append({"dim":"like","rule":f"评论 IP 多样性 {ipd:.2f} 高","delta":+4,"type":"bonus"})

    # comment_avg_length  q75=38
    cal = _g(row, "comment_avg_length", None)
    if cal is not None and not (isinstance(cal, float) and np.isnan(cal)):
        if cal >= 38:
            score += 3
            triggered.append({"dim":"like","rule":f"评论平均长度 {cal:.0f} ≥38","delta":+3,"type":"bonus"})

    return max(0, min(100, score)), triggered, missed


def score_old_like(row) -> tuple[float, list, list]:
    """old_like_score:预测「在看」率(15% 权重)
    feature 依据(ρ vs old_like_pct):
      - controversy_markers ρ=0.13(争议 → 表态在看)
      - first_person_density ρ=0.17(第一人称 → 共鸣)
      - jb_avg_word_len ρ=-0.20(短词 → 口语化 → 共鸣)
      - comment_long_ratio ρ=0.20(深度评论)
    """
    score = 50.0
    triggered, missed = [], []

    # controversy_markers  q75=0.26, q90=0.70 (per-1k-chars density)
    cv = _g(row, "controversy_markers", 0)
    if cv >= 0.70:
        score += 8
        triggered.append({"dim":"old_like","rule":f"争议密度 {cv:.2f}(高,立场鲜明)","delta":+8,"type":"bonus"})
    elif cv >= 0.26:
        score += 4
        triggered.append({"dim":"old_like","rule":f"争议密度 {cv:.2f}(中)","delta":+4,"type":"bonus"})
    else:
        missed.append({"action":"加 2-3 处明确立场/反共识观点","dim":"old_like","expected_delta":+8})

    # first_person_density  q25=0.95, q75=9.79, q90=15.23 (per-1k-chars density)
    fpd = _g(row, "first_person_density", 0)
    if fpd >= 10.0:
        score += 6
        triggered.append({"dim":"old_like","rule":f"第一人称密度 {fpd:.2f}(高)","delta":+6,"type":"bonus"})
    elif fpd >= 4.0:
        score += 3
        triggered.append({"dim":"old_like","rule":f"第一人称密度 {fpd:.2f}(中)","delta":+3,"type":"bonus"})
    elif fpd < 1.0:
        score -= 3
        triggered.append({"dim":"old_like","rule":f"第一人称密度 {fpd:.2f}(低,缺共鸣)","delta":-3,"type":"penalty"})
        missed.append({"action":"加 5-10 处第一人称体验(我试了/我发现)","dim":"old_like","expected_delta":+9})

    # 短词倾向 (jb_avg_word_len 小 → 口语化)
    awl = _g(row, "jb_avg_word_len", 1.5)
    if awl < 1.5:
        score += 5
        triggered.append({"dim":"old_like","rule":f"平均词长 {awl:.2f} 口语化","delta":+5,"type":"bonus"})
    elif awl > 2.0:
        score -= 4
        triggered.append({"dim":"old_like","rule":f"平均词长 {awl:.2f} 偏书面","delta":-4,"type":"penalty"})
        missed.append({"action":"把长术语换成日常说法,降低词长","dim":"old_like","expected_delta":+9})

    # comment_long_ratio  q75=0.44
    clr = _g(row, "comment_long_ratio", None)
    if clr is not None and not (isinstance(clr, float) and np.isnan(clr)):
        if clr >= 0.44:
            score += 4
            triggered.append({"dim":"old_like","rule":f"长评论比 {clr:.0%}","delta":+4,"type":"bonus"})
        elif clr >= 0.20:
            score += 2
            triggered.append({"dim":"old_like","rule":f"长评论比 {clr:.0%}","delta":+2,"type":"bonus"})

    # cultural_meme (0/1)
    cm = _g(row, "cultural_meme", 0)
    if cm >= 1:
        score += 2
        triggered.append({"dim":"old_like","rule":"含梗/段子","delta":+2,"type":"bonus"})

    return max(0, min(100, score)), triggered, missed


def score_comment(row) -> tuple[float, list, list]:
    """comment_score:预测评论率(10% 权重)
    feature 依据(ρ vs comment_pct):
      - comment_count_real ρ=0.35(post-hoc 但用户表示可用)
      - comment_question_ratio ρ=0.24
      - comment_ip_diversity ρ=0.23
      - first_person_density ρ=0.09
      - personal_pronoun_in_title
      - interaction_call_in_title
    """
    score = 50.0
    triggered, missed = [], []

    # comment_question_ratio  q75=0.19, q90=0.33
    cqr = _g(row, "comment_question_ratio", None)
    if cqr is not None and not (isinstance(cqr, float) and np.isnan(cqr)):
        if cqr >= 0.30:
            score += 8
            triggered.append({"dim":"comment","rule":f"评论问句比 {cqr:.0%} ≥30%","delta":+8,"type":"bonus"})
        elif cqr >= 0.15:
            score += 4
            triggered.append({"dim":"comment","rule":f"评论问句比 {cqr:.0%}","delta":+4,"type":"bonus"})

    # comment_ip_diversity  q75=0.79, q90=0.82
    ipd = _g(row, "comment_ip_diversity", None)
    if ipd is not None and not (isinstance(ipd, float) and np.isnan(ipd)):
        if ipd >= 0.79:
            score += 6
            triggered.append({"dim":"comment","rule":f"评论 IP 多样性 {ipd:.2f} 高","delta":+6,"type":"bonus"})
        elif ipd >= 0.60:
            score += 3
            triggered.append({"dim":"comment","rule":f"评论 IP 多样性 {ipd:.2f}","delta":+3,"type":"bonus"})

    # comment_sentiment_neg_ratio  q90=0.09
    csn = _g(row, "comment_sentiment_neg_ratio", None)
    if csn is not None and not (isinstance(csn, float) and np.isnan(csn)):
        if csn >= 0.09:
            score += 4
            triggered.append({"dim":"comment","rule":f"负面评论比 {csn:.0%}(有争议)","delta":+4,"type":"bonus"})

    # personal_pronoun_in_title (0/1)
    ppt = _g(row, "personal_pronoun_in_title", 0)
    if ppt >= 1:
        score += 4
        triggered.append({"dim":"comment","rule":"标题含人称代词(你/我)","delta":+4,"type":"bonus"})
    else:
        missed.append({"action":"标题加「你」或「我」唤起对话","dim":"comment","expected_delta":+4})

    # interaction_call_in_title (rare, mostly 0)
    ict = _g(row, "interaction_call_in_title", 0)
    if ict >= 1:
        score += 5
        triggered.append({"dim":"comment","rule":"标题含互动召唤(评论/告诉我等)","delta":+5,"type":"bonus"})
    else:
        missed.append({"action":"标题末尾加问句或互动召唤","dim":"comment","expected_delta":+5})

    # first_person_density  q75=9.79
    fpd = _g(row, "first_person_density", 0)
    if fpd >= 10.0:
        score += 4
        triggered.append({"dim":"comment","rule":f"第一人称密度 {fpd:.2f}(高)","delta":+4,"type":"bonus"})

    # opinion_strength_markers  q75=3.05, q90=4.64
    ops = _g(row, "opinion_strength_markers", 0)
    if ops >= 3.0:
        score += 3
        triggered.append({"dim":"comment","rule":f"强观点密度 {ops:.2f}(引争论)","delta":+3,"type":"bonus"})
    elif ops < 0.5:
        missed.append({"action":"加 2-3 处明确立场观点","dim":"comment","expected_delta":+3})

    return max(0, min(100, score)), triggered, missed


# ============================================================
# 顶层接口
# ============================================================

# 权重对齐 composite_pct
DIM_WEIGHTS = {"read": 0.40, "share": 0.20, "like": 0.15, "old_like": 0.15, "comment": 0.10}


def sop_score_v2(row) -> dict[str, Any]:
    """SOP v2 多维度评分 + 反馈结构
    输入:一行(dict 或 pandas Series),包含 features.parquet + comment_features.parquet
          + topic_hotness.parquet + semantic_features.parquet 合并后的字段 + title。
    输出:{ total_score, read_score, share_score, like_score, old_like_score, comment_score,
           rules_triggered: [{dim,rule,delta,type}, ...],
           suggestions: [{action,dim,expected_delta}, ...] 按 expected_delta 降序 }
    """
    r_s, r_tr, r_ms = score_read(row)
    s_s, s_tr, s_ms = score_share(row)
    l_s, l_tr, l_ms = score_like(row)
    o_s, o_tr, o_ms = score_old_like(row)
    c_s, c_tr, c_ms = score_comment(row)

    total = (DIM_WEIGHTS["read"]*r_s + DIM_WEIGHTS["share"]*s_s + DIM_WEIGHTS["like"]*l_s
             + DIM_WEIGHTS["old_like"]*o_s + DIM_WEIGHTS["comment"]*c_s)

    all_triggered = r_tr + s_tr + l_tr + o_tr + c_tr
    all_missed = r_ms + s_ms + l_ms + o_ms + c_ms
    all_missed.sort(key=lambda x: -x.get("expected_delta", 0))

    return {
        "total_score": round(total, 1),
        "read_score": round(r_s, 1),
        "share_score": round(s_s, 1),
        "like_score": round(l_s, 1),
        "old_like_score": round(o_s, 1),
        "comment_score": round(c_s, 1),
        "rules_triggered": all_triggered,
        "suggestions": all_missed,
    }


def sop_score_v2_total(row) -> float:
    """便捷:只取 total_score(用于 df.apply 求总分向量)"""
    return sop_score_v2(row)["total_score"]


if __name__ == "__main__":
    # 自检
    dummy = {
        "title": "Claude Code Skills 完全指南:我用 vibe coding 做了 3 个 agent",
        "t_chars": 32, "t_english_chars": 15,
        "b_chars": 4200, "b_para_avg_chars": 220, "b_one_liner_ratio": 0.05,
        "jb_lexical_diversity": 0.40, "jb_avg_word_len": 1.6, "tb_ratio": 0.03,
        "has_cover_color": 1, "cover_r": 250, "cover_g": 200, "cover_b": 110,
        "cover_brightness": 210, "img_per_1k_chars": 3.5,
        "topic_hotness_30d": 0.85, "topic_hotness_90d": 0.82,
        "current_event_words_in_title": 1, "action_verb_count": 4,
        "opinion_strength_markers": 3, "cultural_meme": 1,
        "controversy_markers": 2, "first_person_density": 0.025,
        "personal_pronoun_in_title": 1, "interaction_call_in_title": 0,
        "comment_question_ratio": 0.25, "comment_ip_diversity": 0.72,
        "comment_avg_length": 35, "comment_long_ratio": 0.42,
        "comment_sentiment_neg_ratio": 0.10,
    }
    out = sop_score_v2(pd.Series(dummy))
    print(f"total={out['total_score']}, read={out['read_score']}, share={out['share_score']},"
          f" like={out['like_score']}, old_like={out['old_like_score']}, comment={out['comment_score']}")
    print(f"triggered={len(out['rules_triggered'])} rules, suggestions={len(out['suggestions'])}")
    for s in out["suggestions"][:5]:
        print(f"  → [{s['dim']}] {s['action']} ({s['expected_delta']:+d})")
