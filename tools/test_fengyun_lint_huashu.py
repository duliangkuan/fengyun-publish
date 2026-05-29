"""
测试 fengyun_lint.py 的 huashu R19-R25 规则。

零回归测试 + 7 条规则的触发/不触发验证。
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

# 让脚本能从 tools/ 直接跑
sys.path.insert(0, str(Path(__file__).parent))

from fengyun_lint import lint_article, parse_fm_meta  # noqa: E402


# ---------- 工具 ----------

def _run(md_text: str) -> dict:
    """把字符串写到临时文件后跑 lint。"""
    with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".md", delete=False) as f:
        f.write(md_text)
        path = f.name
    try:
        return lint_article(Path(path))
    finally:
        try:
            Path(path).unlink()
        except OSError:
            pass


def _rule_ids(result: dict) -> set:
    return {v["rule_id"] for v in result["violations"]}


# ---------- frontmatter 解析 ----------

def test_parse_fm_meta_basic():
    txt = """---
style: huashu
title: 测试
---

正文。
"""
    meta = parse_fm_meta(txt)
    assert meta.get("style") == "huashu", meta
    assert meta.get("title") == "测试", meta
    print("[PASS] test_parse_fm_meta_basic")


def test_parse_fm_meta_no_frontmatter():
    txt = "没有 frontmatter\n"
    meta = parse_fm_meta(txt)
    assert meta == {}, meta
    print("[PASS] test_parse_fm_meta_no_frontmatter")


# ---------- 零回归:无 frontmatter / 不是 huashu 不触发 ----------

def test_default_style_skips_huashu_rules():
    """没有 style: huashu 的文章不该触发任何 R19_huashu_* / R22_huashu_*"""
    md = """---
title: 普通文章
---

# 标题

正文 🚀 不是 huashu 风格,带 emoji 不该触发 R22。

点赞转发关注扫码,这些 CTA 词也不该触发 R23。

省略号……省略号……省略号……省略号也不该触发 R25。
"""
    res = _run(md)
    ids = _rule_ids(res)
    for rid in ids:
        assert not rid.startswith("R19_huashu") and not rid.startswith("R20_huashu"), ids
        assert not rid.startswith("R21_huashu") and not rid.startswith("R22_huashu"), ids
        assert not rid.startswith("R23_huashu") and not rid.startswith("R24_huashu"), ids
        assert not rid.startswith("R25_huashu"), ids
    print("[PASS] test_default_style_skips_huashu_rules")


def test_no_frontmatter_skips_huashu_rules():
    md = """# 标题

正文 🚀 emoji,扫码关注。
"""
    res = _run(md)
    ids = _rule_ids(res)
    for rid in ids:
        assert "_huashu_" not in rid, ids
    print("[PASS] test_no_frontmatter_skips_huashu_rules")


# ---------- R22 emoji 必须为 0 ----------

def test_huashu_emoji_fails_r22():
    md = """---
style: huashu
---

# 标题

正文带 emoji 🚀 一个。

继续写一段。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R22_huashu_emoji_zero" in ids, ids
    # severity high
    v22 = [v for v in res["violations"]
           if v["rule_id"] == "R22_huashu_emoji_zero"][0]
    assert v22["severity"] == "high", v22
    print("[PASS] test_huashu_emoji_fails_r22")


# ---------- R23 CTA 必须为 0 ----------

def test_huashu_cta_fails_r23():
    md = """---
style: huashu
---

正文最后求关注转发点赞。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R23_huashu_cta_zero" in ids, ids
    v23 = [v for v in res["violations"]
           if v["rule_id"] == "R23_huashu_cta_zero"][0]
    assert v23["severity"] == "high", v23
    print("[PASS] test_huashu_cta_fails_r23")


# ---------- R25 省略号 ----------

def test_huashu_ellipsis_fails_r25():
    md = """---
style: huashu
---

第一段……有省略号。

第二段也有……省略号。

第三段还有……省略号。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R25_huashu_ellipsis" in ids, ids
    print("[PASS] test_huashu_ellipsis_fails_r25")


def test_huashu_ellipsis_ok_when_one():
    md = """---
style: huashu
---

只有一处省略号……其他段都没有。

段二。

段三。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R25_huashu_ellipsis" not in ids, ids
    print("[PASS] test_huashu_ellipsis_ok_when_one")


# ---------- R21 H2 模式 ----------

def test_huashu_h2_pattern_ok():
    """H2 命中三种模式之一都该通过"""
    md = """---
style: huashu
---

# 标题

## 这就是对抗采样的本质

正文。

## 我把它接进来了

正文。

## 一

正文。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R21_huashu_h2_pattern" not in ids, ids
    print("[PASS] test_huashu_h2_pattern_ok")


def test_huashu_h2_pattern_fails():
    """H2 不命中三种模式时报错"""
    md = """---
style: huashu
---

# 标题

## 关于产品设计的若干思考方法论体系建设细则

正文。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R21_huashu_h2_pattern" in ids, ids
    print("[PASS] test_huashu_h2_pattern_fails")


# ---------- R19 平均段长 ----------

def test_huashu_para_too_short_fails_r19():
    md = """---
style: huashu
---

很短。

也短。

依然短。

继续短。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R19_huashu_avg_para_length" in ids, ids
    print("[PASS] test_huashu_para_too_short_fails_r19")


# ---------- 综合:干净的 huashu 文章不触发 R22/R23 ----------

def test_huashu_clean_article_no_emoji_no_cta():
    md = """---
style: huashu
---

# 标题

昨晚我把 Mavis 接进来了。

它做的事很简单。两个 Agent 互掐。这种"互掐"在博弈论里叫对抗采样,实际效果远超单个聪明 Agent。

因为对抗是真理的产婆。

## 一

我跑了一晚上,发现一个很有意思的现象:当两个 Agent 立场相反地辩论同一个问题时,真相会自己浮出来。这不需要任何额外的标注。

这种自发的对齐机制,让我想起 GAN 的工作原理。生成器和判别器互相博弈,最后生成器学会了真实数据的分布。

只不过这次,博弈的不是图像,而是观点。

## 我把它接到了主流程里

接进来之后,整个 pipeline 的输出质量肉眼可见地提升了。

但代价是 token 翻倍。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R22_huashu_emoji_zero" not in ids, f"clean article should not trigger R22: {ids}"
    assert "R23_huashu_cta_zero" not in ids, f"clean article should not trigger R23: {ids}"
    print("[PASS] test_huashu_clean_article_no_emoji_no_cta")


# ---------- 零回归:huashu 不影响现有 R0-R18 行为 ----------

def test_huashu_does_not_break_r1_brackets():
    """无 huashu frontmatter 时 R1 该照常触发"""
    md = """# 标题

文中使用了「中文方括号」这种禁用符号。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R1_brackets" in ids, ids
    print("[PASS] test_huashu_does_not_break_r1_brackets")


# ---------- Round 23 R26 + R27 双密度规则 ----------

def test_huashu_r26_bold_per_para_fails():
    """R26:某段 bold ≥ 2 处 → 触发 medium."""
    md = """---
style: huashu
title: 测试
---

# 标题

## 一、起点

正常引子。

AI 的本质是**预测**,不是**理解**,这两件事完全不同。

下一段内容正常,只**一处加粗**。

## 二、继续

第三段不带 bold,只走通文字。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R26_huashu_bold_per_para" in ids, ids
    # R27 不该触发(全文 bold 数 3 < 5)
    assert "R27_huashu_bold_total" not in ids, ids
    print("[PASS] test_huashu_r26_bold_per_para_fails")


def test_huashu_r26_pass_when_each_para_has_one():
    """每段 ≤ 1 处 bold → R26 不触发."""
    md = """---
style: huashu
title: 测试
---

# 标题

## 一、起点

引子,带一处**预测**金句。

## 二、转折

第二段,**理解**需要意识。

## 三、收尾

第三段没有 bold,只是普通文字。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R26_huashu_bold_per_para" not in ids, ids
    print("[PASS] test_huashu_r26_pass_when_each_para_has_one")


def test_huashu_r27_bold_total_fails():
    """全文 bold > 5 处(长文)→ R27 触发."""
    md = """---
style: huashu
title: 测试
---

# 标题

## 一

""" + ("正文" * 1000) + """

## 二

**a** 然后 **b** 然后 **c** 然后 **d** 然后 **e** 然后 **f**
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R27_huashu_bold_total" in ids, ids
    print("[PASS] test_huashu_r27_bold_total_fails")


def test_huashu_r27_short_article_cap_3():
    """短文(< 1000 字)上限 3 处 → 4 处触发 R27."""
    md = """---
style: huashu
title: 短文
---

# 标题

## 一

短文 **a** **b** **c** **d** 四处加粗。
"""
    res = _run(md)
    ids = _rule_ids(res)
    assert "R27_huashu_bold_total" in ids, ids
    print("[PASS] test_huashu_r27_short_article_cap_3")


# ---------- main ----------

def run_all():
    tests = [
        test_parse_fm_meta_basic,
        test_parse_fm_meta_no_frontmatter,
        test_default_style_skips_huashu_rules,
        test_no_frontmatter_skips_huashu_rules,
        test_huashu_emoji_fails_r22,
        test_huashu_cta_fails_r23,
        test_huashu_ellipsis_fails_r25,
        test_huashu_ellipsis_ok_when_one,
        test_huashu_h2_pattern_ok,
        test_huashu_h2_pattern_fails,
        test_huashu_para_too_short_fails_r19,
        test_huashu_clean_article_no_emoji_no_cta,
        test_huashu_does_not_break_r1_brackets,
        # Round 23 R26 + R27 双密度规则
        test_huashu_r26_bold_per_para_fails,
        test_huashu_r26_pass_when_each_para_has_one,
        test_huashu_r27_bold_total_fails,
        test_huashu_r27_short_article_cap_3,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n=== {len(tests) - failed}/{len(tests)} passed ===")
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
