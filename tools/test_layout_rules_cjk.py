"""
test_layout_rules_cjk.py — 2026-05-24
CJK 中英文混排自动加空格 + `**xxx,**` 标点位置修正(_preprocess_cjk)。

测试目标:
1. 中 + 英 + 中 → 自动补空格
2. **关键词,** → **关键词**,(标点踢出加粗)
3. 纯中文 / 纯英文 / 已有空格 → 不改
4. 代码块 / 行内代码 / URL / 链接 / 图片不动
5. 接入 render_to_wechat_html 后,渲染前确实跑过预处理
"""
from __future__ import annotations

import sys
from pathlib import Path

# 让 sibling import 找得到
sys.path.insert(0, str(Path(__file__).parent))

from layout_rules import (  # noqa: E402
    _fix_cjk_bold_punctuation,
    _fix_cjk_spacing,
    _preprocess_cjk,
    render_to_wechat_html,
)


# ============================================================
# _fix_cjk_spacing
# ============================================================

def test_cjk_latin_cjk_gets_spaced() -> None:
    """我用 Cursor 写代码 — 中 + 英 + 中应补两个空格."""
    src = "我用Cursor写代码"
    out = _fix_cjk_spacing(src)
    assert out == "我用 Cursor 写代码", f"got: {out!r}"
    print("[PASS] cjk-latin-cjk gets spaced both sides")


def test_pure_chinese_untouched() -> None:
    src = "今天天气很好,我们去散步。"
    out = _fix_cjk_spacing(src)
    assert out == src, f"got: {out!r}"
    print("[PASS] pure chinese untouched")


def test_pure_english_untouched() -> None:
    src = "The quick brown fox jumps over the lazy dog."
    out = _fix_cjk_spacing(src)
    assert out == src, f"got: {out!r}"
    print("[PASS] pure english untouched")


def test_existing_space_not_duplicated() -> None:
    """已经有空格的不应再加(避免双空格)."""
    src = "我用 Cursor 写代码"
    out = _fix_cjk_spacing(src)
    assert out == src, f"got: {out!r}"
    assert "  " not in out, "不应出现连续两个空格"
    print("[PASS] existing space not duplicated")


def test_digit_cjk_gets_spaced() -> None:
    """数字也算 latin 类,与中文之间应补空格."""
    src = "我有3个苹果"
    out = _fix_cjk_spacing(src)
    assert out == "我有 3 个苹果", f"got: {out!r}"
    print("[PASS] digit-cjk gets spaced")


def test_inline_code_not_touched() -> None:
    """行内代码内部即便有中文也不动."""
    src = "调用 `print(中文)` 输出"
    out = _fix_cjk_spacing(src)
    # backtick 内容应原样保留
    assert "`print(中文)`" in out, f"行内代码被改了: {out!r}"
    print("[PASS] inline code preserved")


def test_url_not_touched() -> None:
    src = "看这个 https://example.com/中文路径 链接"
    out = _fix_cjk_spacing(src)
    assert "https://example.com/中文路径" in out, f"URL 被改了: {out!r}"
    print("[PASS] URL preserved")


def test_code_block_not_touched() -> None:
    src = "前文\n```python\nx=1  # 中文comment\n```\n后文"
    out = _fix_cjk_spacing(src)
    # 代码块内的 `中文comment` 不应被加空格
    assert "中文comment" in out, f"代码块内容被改: {out!r}"
    print("[PASS] code block preserved")


def test_link_not_touched() -> None:
    src = "看[这篇文章](https://x.com/post/中文)"
    out = _fix_cjk_spacing(src)
    # link 内部应原样,但 link 后若紧跟中文也不会被 _fix_cjk_spacing 加(因为 link 被保护)
    assert "[这篇文章](https://x.com/post/中文)" in out, f"链接被改: {out!r}"
    print("[PASS] link preserved")


# ============================================================
# _fix_cjk_bold_punctuation
# ============================================================

# 全角标点常量(避免编辑器/harness 把全角自动转半角导致测试不准)
COMMA = "，"   # 全角逗号 ，
PERIOD = "。"  # 全角句号 。
BANG = "！"    # 全角感叹号 ！
QMARK = "？"   # 全角问号 ？
COLON = "："   # 全角冒号 ：


def test_bold_punctuation_moved_out() -> None:
    """**关键词，**接下来 → **关键词**，接下来(全角逗号)."""
    src = f"**关键词{COMMA}**接下来"
    out = _fix_cjk_bold_punctuation(src)
    expected = f"**关键词**{COMMA}接下来"
    assert out == expected, f"got: {out!r}, expected: {expected!r}"
    print("[PASS] bold punctuation moved out (full-width comma)")


def test_bold_full_punct_set() -> None:
    """各种全角标点都应踢出加粗."""
    cases = [
        (f"**重点{PERIOD}**", f"**重点**{PERIOD}"),
        (f"**注意{BANG}**", f"**注意**{BANG}"),
        (f"**问题{QMARK}**", f"**问题**{QMARK}"),
        (f"**说明{COLON}**", f"**说明**{COLON}"),
    ]
    for src, expected in cases:
        out = _fix_cjk_bold_punctuation(src)
        assert out == expected, f"{src!r} -> {out!r}, expected {expected!r}"
    print("[PASS] bold full-width punct moved out (multiple chars)")


def test_bold_no_punct_untouched() -> None:
    src = "**关键词**后面"
    out = _fix_cjk_bold_punctuation(src)
    assert out == src
    print("[PASS] bold without trailing punct untouched")


def test_italic_punct_moved_out() -> None:
    """单星号斜体也应踢标点."""
    src = f"*强调{COMMA}*下文"
    out = _fix_cjk_bold_punctuation(src)
    expected = f"*强调*{COMMA}下文"
    assert out == expected, f"got: {out!r}, expected: {expected!r}"
    print("[PASS] italic punctuation moved out")


def test_halfwidth_end_punct_kicked_out() -> None:
    """Round 23(2026-05-25)更新:末尾踢出激进集合现在覆盖半角标点。

    原 xiaohu-format 行为只动全角,Round 23 因 LLM 中英文混排经常用 ASCII 标点,
    末尾踢出扩到全套(末尾踢出不会跨 bold 误判,开头踢出仍保守只含 ASCII 引号/冒号)。
    """
    src = "**word,**next"  # 半角逗号末尾
    out = _fix_cjk_bold_punctuation(src)
    assert out == "**word**,next", f"末尾半角逗号应踢出,got: {out!r}"
    print("[PASS] Round 23: half-width end punct kicked out")


def test_round23_bug1_ascii_quote_kicked_out() -> None:
    """Round 23 Bug 1: 弯引号 / ASCII 直引号在 ** 开头都应被踢出。

    用户报告:LLM 输出 `**\"Opus**` 或 `**“想清楚**` 时,引号被吸进高亮框。
    根因:cjk_punct 漏了 ASCII 直引号 + 半角标点。Round 23 修。
    """
    # ASCII 双引号开头
    assert _fix_cjk_bold_punctuation('**"Opus**') == '"**Opus**'
    # ASCII 冒号末尾
    assert _fix_cjk_bold_punctuation('**Sonnet:**') == '**Sonnet**:'
    # Unicode 弯引号开头(双保险冗余)
    assert _fix_cjk_bold_punctuation('**“想清楚**') == '“**想清楚**'
    # ASCII 冒号开头(LLM 中英文混排常见)
    assert _fix_cjk_bold_punctuation('**:启动**') == ':**启动**'
    print("[PASS] Round 23 Bug 1: ASCII/CJK quote + colon kicked out at boundaries")


def test_round23_no_regression_consecutive_bolds() -> None:
    """Round 23 关键 regression case:连续 bold 中间 ASCII 标点不应被误判成「,开头 bold」。

    `**A**,**B**` 必须保持原样,不能被改成 `**A,**`...
    根因:开头踢出用激进集合会误把上个 bold 闭合后的 `,**` 当作下个 bold 开头标点。
    Round 23 修法:开头踢出用保守集合(只 ASCII 引号 + 冒号 + 全角)+ lookbehind。
    """
    # 关键 case:连续 bold 中间 ASCII 半角逗号
    assert _fix_cjk_bold_punctuation('**预测**,不是**理解**') == '**预测**,不是**理解**'
    # 全角逗号同理
    assert _fix_cjk_bold_punctuation('**A**,**B**') == '**A**,**B**'
    # 中间隔句号
    assert _fix_cjk_bold_punctuation('**A**。**B**') == '**A**。**B**'
    # 中间隔感叹号 + 空格
    assert _fix_cjk_bold_punctuation('**A**! **B**') == '**A**! **B**'
    print("[PASS] Round 23: consecutive bolds with punctuation between not误判")


# ============================================================
# _preprocess_cjk(组合)
# ============================================================

def test_preprocess_combined() -> None:
    """组合两个修复:中英空格 + 加粗标点踢出."""
    src = f"我用Cursor写代码{COMMA}**关键词{COMMA}**接下来"
    out = _preprocess_cjk(src)
    assert "我用 Cursor 写代码" in out, f"空格没补: {out!r}"
    assert f"**关键词**{COMMA}" in out, f"标点没踢出: {out!r}"
    print("[PASS] _preprocess_cjk combined two fixes")


def test_preprocess_idempotent() -> None:
    """跑两遍结果应一致(幂等性)."""
    src = f"我用Cursor写代码{COMMA}**关键词{COMMA}**接下来"
    once = _preprocess_cjk(src)
    twice = _preprocess_cjk(once)
    assert once == twice, "应幂等"
    print("[PASS] _preprocess_cjk idempotent")


# ============================================================
# 接入 render_to_wechat_html 验证
# ============================================================

def test_render_applies_preprocess_default() -> None:
    """default style 渲染前应跑过 _preprocess_cjk."""
    md = f"# 标题\n\n我用Cursor写代码{COMMA}**关键词{COMMA}**接下来{PERIOD}"
    html = render_to_wechat_html(md)
    # 渲染后的 HTML 里应包含已加空格的 'Cursor' 两边
    assert "我用 Cursor 写代码" in html, f"default 渲染未跑预处理: {html[:300]}"
    # 标点踢出后,strong 内不应再带全角逗号
    assert f"关键词{COMMA}</strong>" not in html, "strong 内还带标点"
    print("[PASS] render_to_wechat_html (default) applies CJK preprocess")


def test_render_applies_preprocess_huashu() -> None:
    """huashu style 渲染前也应跑过 _preprocess_cjk."""
    md = f"# 标题\n\n我用Cursor写代码{COMMA}**关键词{COMMA}**接下来{PERIOD}"
    html = render_to_wechat_html(md, style="huashu")
    assert "我用 Cursor 写代码" in html, f"huashu 渲染未跑预处理: {html[:300]}"
    # huashu strong 里多了 span leaf,简单断言全角标点不在 strong 闭合前
    assert f"关键词{COMMA}</span></strong>" not in html, "huashu strong 内还带标点"
    print("[PASS] render_to_wechat_html (huashu) applies CJK preprocess")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    tests = [
        # _fix_cjk_spacing
        test_cjk_latin_cjk_gets_spaced,
        test_pure_chinese_untouched,
        test_pure_english_untouched,
        test_existing_space_not_duplicated,
        test_digit_cjk_gets_spaced,
        test_inline_code_not_touched,
        test_url_not_touched,
        test_code_block_not_touched,
        test_link_not_touched,
        # _fix_cjk_bold_punctuation
        test_bold_punctuation_moved_out,
        test_bold_full_punct_set,
        test_bold_no_punct_untouched,
        test_italic_punct_moved_out,
        test_halfwidth_end_punct_kicked_out,           # Round 23 改名+断言反转
        test_round23_bug1_ascii_quote_kicked_out,      # Round 23 新增
        test_round23_no_regression_consecutive_bolds,  # Round 23 新增 regression
        # combined + integration
        test_preprocess_combined,
        test_preprocess_idempotent,
        test_render_applies_preprocess_default,
        test_render_applies_preprocess_huashu,
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

    print()
    print(f"Result: {len(tests) - failed}/{len(tests)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
