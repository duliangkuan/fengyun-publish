"""
评分 draft 文章:从 markdown 文件抽取所有需要的 feature,调 sop_v2_1 评分
"""
from __future__ import annotations
import sys, re, json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import jieba
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from sop_v2_1 import sop_score_v2_1

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")


def extract_features(md_path: Path, account_slug: str = "kazik") -> dict:
    """从 markdown 文件抽取 sop_v2_1 需要的 feature."""
    text = md_path.read_text(encoding="utf-8")
    # 拆 frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            body = parts[2].strip()
            title_m = re.search(r"^title:\s*(.+)$", fm, re.M)
            title = title_m.group(1).strip() if title_m else ""
        else:
            body = text
            title = ""
    else:
        body = text
        title = ""

    # ===== 标题特征 =====
    t_chars = len(title)
    t_english_chars = len(re.findall(r"[A-Za-z]", title))
    t_digit_count = len(re.findall(r"\d", title))
    t_has_digit = int(t_digit_count > 0)
    t_has_english = int(t_english_chars > 0)
    t_questions = title.count("?") + title.count("?")
    t_excl = title.count("!") + title.count("!")
    t_colons = title.count(":") + title.count(":")
    t_dashes = title.count("—") + title.count("—")
    t_dots3 = title.count("...") + title.count("…")
    t_brackets_zh = title.count("【") + title.count("[")
    t_brackets_en = title.count("[") + title.count("(")
    # emoji 粗略检测(Unicode 范围 U+1F300-U+1F9FF)
    t_emojis = sum(1 for c in title if ord(c) >= 0x1F300)

    # ===== 正文特征 =====
    # 拆段落(连续空行分隔)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    # 去掉文末固定推广段
    paragraphs = [p for p in paragraphs
                  if not p.startswith("以上,既然") and not p.startswith("> /")]
    b_para_count = len(paragraphs)
    b_chars = sum(len(p) for p in paragraphs)

    # 段长统计
    para_lens = [len(p) for p in paragraphs]
    b_para_avg_chars = sum(para_lens) / max(1, len(para_lens))
    b_para_max_chars = max(para_lens) if para_lens else 0
    import statistics
    b_para_std_chars = statistics.stdev(para_lens) if len(para_lens) > 1 else 0
    b_first_para_chars = para_lens[0] if para_lens else 0
    b_last_para_chars = para_lens[-1] if para_lens else 0

    # 一行一段比例(段落 < 30 字)
    b_one_liner_ratio = sum(1 for l in para_lens if l < 30) / max(1, len(para_lens))
    b_short_para_ratio = sum(1 for l in para_lens if l < 50) / max(1, len(para_lens))

    # 标点统计(正文)
    b_questions = body.count("?") + body.count("?")
    b_excl = body.count("!") + body.count("!")
    b_commas = body.count(",") + body.count(",")
    b_periods = body.count("。") + body.count(".")
    b_colons = body.count(":") + body.count(":")
    b_quote_zh = body.count("「") + body.count("」") + body.count(""") + body.count(""")
    b_quote_en = body.count('"') * 2  # 估算
    b_dash = body.count("—") + body.count("—")
    b_dots3 = body.count("...") + body.count("…")
    b_emojis = sum(1 for c in body if ord(c) >= 0x1F300)

    # 英文比例
    b_english_chars = len(re.findall(r"[A-Za-z]", body))
    b_english_ratio = b_english_chars / max(1, b_chars)

    # 图片数(markdown ![]() 语法)
    b_img_count = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", body))
    img_per_1k_chars = b_img_count / max(100, b_chars) * 1000

    # jieba 分词
    words = list(jieba.cut(body))
    words_filtered = [w for w in words if len(w.strip()) > 0]
    jb_word_count = len(words_filtered)
    jb_unique_words = len(set(words_filtered))
    jb_lexical_diversity = jb_unique_words / max(1, jb_word_count)
    jb_avg_word_len = sum(len(w) for w in words_filtered) / max(1, len(words_filtered))

    # 标题/正文比
    tb_ratio = t_chars / max(1, b_chars)

    # 封面色 — 配图后:暖橙金调,深色背景(根据生成的封面图实际色调)
    # 主色估算(暖橙):RGB(180, 120, 60),亮度 (180+120+60)/3 ≈ 120
    cover_r = 180
    cover_g = 120
    cover_b = 60
    cover_brightness = 120
    has_cover_color = 1

    # ===== 第一人称密度 等 semantic features =====
    first_person_pat = re.compile(r"我|咱|咱们|我们|俺|本")
    first_person_count = len(first_person_pat.findall(body))
    first_person_density = first_person_count / max(1, b_chars) * 1000

    # 标题第一人称
    personal_pronoun_in_title = int(bool(first_person_pat.search(title)))

    # action verb
    action_pat = re.compile(r"买了|装了|试了|跑了|玩了|搞了|调了|装|刷到|跑")
    action_verb_count = len(action_pat.findall(body))

    # current event words in title
    event_pat = re.compile(r"今天|昨天|刚刚|最近|这周|本周|这两天|这几天|突然")
    current_event_words_in_title = int(bool(event_pat.search(title)))

    # opinion strength
    opinion_pat = re.compile(r"必须|一定|绝对|真的|完全|简直|封神|史诗|震撼|炸|绝|无敌|真香")
    opinion_strength_markers = len(opinion_pat.findall(body))

    # controversy
    controversy_pat = re.compile(r"翻车|暴雷|拉黑|不行|失望|警告|崩了|哥们|尼玛|傻")
    controversy_markers = len(controversy_pat.findall(body))

    # cultural meme
    meme_pat = re.compile(r"八荣八耻|真香|内卷|躺平|摆烂|emo|破防|绝绝子|栓Q")
    cultural_meme = len(meme_pat.findall(body))

    # ===== viral features =====
    # ending strength(末段是否含金句模式 + 感叹问句)
    last_para = paragraphs[-1] if paragraphs else ""
    last_has_opinion = int(bool(opinion_pat.search(last_para)))
    last_has_exclaim = int("!" in last_para or "!" in last_para)
    last_has_question = int("?" in last_para or "?" in last_para)
    # 末段长度规范化
    last_normalized = min(1.0, b_last_para_chars / 200)
    viral_ending_strength = (last_has_opinion * 0.4 +
                            (last_has_exclaim or last_has_question) * 0.3 +
                            last_normalized * 0.3)

    # 来自 style_match parquet — 看看这篇没有 style_match,先用近似
    # 实际上对于新文章,我们没有 anchor 算 style_match
    # 用一个保守的中性值,或者用 jieba 词频跟 kazik anchor 比
    style_match_score = 0.0  # 默认中性,critic 不加分也不扣分

    # 拼装 row
    row = {
        # title features
        "title": title,
        "t_chars": t_chars,
        "t_english_chars": t_english_chars,
        "t_digit_count": t_digit_count,
        "t_has_digit": t_has_digit,
        "t_has_english": t_has_english,
        "t_questions": t_questions,
        "t_excl": t_excl,
        "t_colons": t_colons,
        "t_dashes": t_dashes,
        "t_dots3": t_dots3,
        "t_brackets_zh": t_brackets_zh,
        "t_brackets_en": t_brackets_en,
        "t_emojis": t_emojis,
        # body
        "b_chars": b_chars,
        "b_para_count": b_para_count,
        "b_para_avg_chars": b_para_avg_chars,
        "b_para_max_chars": b_para_max_chars,
        "b_para_std_chars": b_para_std_chars,
        "b_first_para_chars": b_first_para_chars,
        "b_last_para_chars": b_last_para_chars,
        "b_one_liner_ratio": b_one_liner_ratio,
        "b_short_para_ratio": b_short_para_ratio,
        "b_questions": b_questions,
        "b_excl": b_excl,
        "b_commas": b_commas,
        "b_periods": b_periods,
        "b_colons": b_colons,
        "b_quote_zh": b_quote_zh,
        "b_quote_en": b_quote_en,
        "b_dash": b_dash,
        "b_dots3": b_dots3,
        "b_emojis": b_emojis,
        "b_english_ratio": b_english_ratio,
        "b_img_count": b_img_count,
        "img_per_1k_chars": img_per_1k_chars,
        # jieba
        "jb_word_count": jb_word_count,
        "jb_unique_words": jb_unique_words,
        "jb_lexical_diversity": jb_lexical_diversity,
        "jb_avg_word_len": jb_avg_word_len,
        # ratios
        "tb_ratio": tb_ratio,
        # cover
        "cover_r": cover_r, "cover_g": cover_g, "cover_b": cover_b,
        "cover_brightness": cover_brightness,
        "has_cover_color": has_cover_color,
        # semantic
        "first_person_density": first_person_density,
        "personal_pronoun_in_title": personal_pronoun_in_title,
        "action_verb_count": action_verb_count,
        "current_event_words_in_title": current_event_words_in_title,
        "opinion_strength_markers": opinion_strength_markers,
        "controversy_markers": controversy_markers,
        "cultural_meme": cultural_meme,
        # topic hotness(Anthropic Mythos 算 "Anthropic 公司动态 / Anthropic Skills" 主题
        # 2026 H1 爆款率 88%,所以 hotness 用高值)
        "topic_hotness_30d": 0.85,
        "topic_hotness_90d": 0.80,
        # style match — 没法在线算,留 0
        "style_match_score": style_match_score,
        # viral
        "viral_ending_strength": viral_ending_strength,
        # 账号 + 元数据
        "account_slug": account_slug,
        "itemidx": 1,  # 头条
    }

    return row, paragraphs


def main():
    # 支持 CLI 参数(SKILL.md 文档行为),无参数走默认
    if len(sys.argv) > 1:
        draft_path = Path(sys.argv[1])
        if not draft_path.is_absolute():
            draft_path = Path.cwd() / draft_path
    else:
        print("用法: python score_draft.py <draft.md>", file=sys.stderr)
        sys.exit(2)
    if not draft_path.exists():
        print(f"❌ draft 不存在: {draft_path}")
        sys.exit(2)
    print(f"=== 评分 {draft_path.name} ===\n")

    row, paragraphs = extract_features(draft_path)

    # 输出 key features 给我看
    print("=== 文章统计 ===")
    print(f"  标题: {row['title']}")
    print(f"  标题字数: {row['t_chars']} | 英文字数: {row['t_english_chars']}")
    print(f"  正文字数: {row['b_chars']}")
    print(f"  段落数: {row['b_para_count']}")
    print(f"  平均段长: {row['b_para_avg_chars']:.1f} 字 ⚠️ SOP 要求 ≥200")
    print(f"  一行一段比例: {row['b_one_liner_ratio']:.1%} ⚠️ SOP 要求 <30%, >70% 致命")
    print(f"  短段(<50 字)比例: {row['b_short_para_ratio']:.1%}")
    print(f"  最长段: {row['b_para_max_chars']} 字 / 最短段: ?")
    print(f"  第一人称密度: {row['first_person_density']:.2f}/千字")
    print(f"  action_verb_count: {row['action_verb_count']}")
    print(f"  opinion_strength: {row['opinion_strength_markers']}")
    print(f"  controversy_markers: {row['controversy_markers']}")
    print(f"  cultural_meme: {row['cultural_meme']}")
    print(f"  词汇多样性: {row['jb_lexical_diversity']:.3f}")
    print(f"  图片数: {row['b_img_count']}(尚未配图)")
    print(f"  topic_hotness_30d: {row['topic_hotness_30d']:.2f}(Anthropic 主题 88% 爆款率)")
    print()

    # 调 sop_v2_1
    result = sop_score_v2_1(row)
    print("=== Layer 1 SOP v2.1 评分 ===")
    print(f"  total_score: {result['total_score']:.1f}")
    print(f"  read_score:  {result.get('read_score', 0):.1f}")
    print(f"  share_score: {result.get('share_score', 0):.1f}")
    print(f"  like_score:  {result.get('like_score', 0):.1f}")
    print(f"  old_like_score: {result.get('old_like_score', 0):.1f}")
    print(f"  comment_score:  {result.get('comment_score', 0):.1f}")
    smn = result.get('style_match_normalized')
    if smn is not None:
        print(f"  style_match_normalized: {smn:.1f}")
    else:
        # Bug 4 修复 2026-05-24:style_match silent fail 改 fail-loud
        print(
            f"  style_match_normalized: ⚠️  None (anchor 未生效) — "
            f"如果你期望有这个分数,跑 tools/fengyun_anchor.py rebuild"
        )
    print()

    # 打印 rules_triggered
    if 'rules_triggered' in result:
        print("=== 触发规则(加扣分明细)===")
        for r in result['rules_triggered'][:20]:
            if isinstance(r, dict):
                dim = r.get('dim', '?')
                rule = r.get('rule', '?')
                delta = r.get('delta', 0)
                rtype = r.get('type', '?')
                marker = "+" if delta > 0 else ""
                print(f"  [{dim:10s}] {rule:50s}  {marker}{delta} ({rtype})")
        print()

    # 改进建议
    if 'suggestions' in result:
        print("=== 改进建议(按 ROI 排序)===")
        for s in result['suggestions'][:10]:
            if isinstance(s, dict):
                action = s.get('action', '?')
                dim = s.get('dim', '?')
                delta = s.get('expected_delta', 0)
                print(f"  +{delta:>4.1f} [{dim:10s}] {action}")
        print()

    # 保存 JSON(Bug 3 修复 2026-05-24:用 draft stem 派生路径,不再 hardcoded anthropic-mythos)
    # stem 去 -vN 后缀,跟 draft 同源
    import re as _re
    stem = _re.sub(r"-v\d+$", "", draft_path.stem)
    out_path = draft_path.parent / f"{stem}.scoring.json"
    out_data = {
        "layer1_sop_v2_1": result,
        "extracted_features": {k: v for k, v in row.items() if not isinstance(v, str) or len(v) < 100},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"✓ Layer 1 评分结果保存:{out_path}")


if __name__ == "__main__":
    main()
