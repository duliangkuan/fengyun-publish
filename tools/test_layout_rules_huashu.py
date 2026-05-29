"""
Smoke test for huashu render branch in layout_rules.py.

测试目标:
1. default 路径不传 style 行为不变
2. huashu T-A 路径走花叔规则(17px / #C15F3C)
3. huashu T-B 路径走深红色块(#d32f2f)
4. 现有 4 参数调用(按位置)未受影响
"""
from __future__ import annotations

import sys
from pathlib import Path

# 让 sibling import 找得到
sys.path.insert(0, str(Path(__file__).parent))

from layout_rules import render_to_wechat_html, lint  # noqa: E402


MD_SAMPLE = """# 标题

这是第一段,**关键词**在这里。

## 第一章

第二段的内容。

## 第二章

第三段的内容。
"""


def test_no_style_arg_defaults_to_huashu() -> None:
    """2026-05-24 排版主力切 huashu:不传 style 默认走 huashu T-A."""
    html = render_to_wechat_html(MD_SAMPLE)
    assert "17px" in html, "新默认 huashu 字号应是 17px"
    assert "#C15F3C" in html, "新默认 huashu 应有橙强调 #C15F3C"
    assert "#faf9f7" in html, "新默认 huashu 应有暖米黄底"
    print("[PASS] no style arg defaults to huashu T-A (17px / #C15F3C / #faf9f7)")


def test_legacy_style_arg_redirects_to_huashu() -> None:
    """Round 21 决策 1.2:style='default' 已废弃,强制走 huashu(向后兼容旧 caller)."""
    html = render_to_wechat_html(MD_SAMPLE, style="default")
    # 不再有 default 路径,所有 style 都走 huashu(17px / #C15F3C / 暖米黄)
    assert "17px" in html, "style='default' 应被 Round 21 redirect 到 huashu(17px)"
    assert "#C15F3C" in html, "redirect 后应该有 huashu T-A 主色 #C15F3C"
    print("[PASS] style='default' redirects to huashu (Round 21 砍 default 分支)")


def test_default_positional_args_redirect() -> None:
    """按位置传 4 个原始参数 + style='default' kwarg — Round 21 后 redirect 到 huashu."""
    html = render_to_wechat_html(MD_SAMPLE, None, None, True, style="default")
    assert "17px" in html  # huashu 字号
    print("[PASS] default positional 4-arg + style='default' kwarg → redirected to huashu")


def test_huashu_template_A() -> None:
    html = render_to_wechat_html(MD_SAMPLE, style="huashu")
    assert "17px" in html, "huashu 字号应是 17px"
    assert "#C15F3C" in html, "huashu T-A 主色应是 #C15F3C"
    # 2026-05-24 用户偏好:T-A H1 改 left-border 风格,不用渐变
    assert "border-left: 3px solid #C15F3C" in html, "huashu T-A H1 应有橙左竖边"
    assert "linear-gradient" not in html, "huashu T-A H1 不应再有渐变(2026-05-24 调整)"
    # 真品 strong 背景用 rgba(193, 95, 60, 0.08) — 含空格,1:1 复刻
    assert "rgba(193, 95, 60" in html, "huashu T-A strong 应有橙底高亮(真品空格写法)"
    # 真品外层 section 暖米黄底
    assert "#faf9f7" in html, "huashu T-A 外层 section 应有 #faf9f7 暖米黄底"
    # 真品用 <h1> 不是 <h2>(tag 保留,只是样式从渐变改成左竖边)
    assert "<h1 " in html, "huashu T-A 章节标题用 <h1>"
    # 真品微信编辑器签名:<span leaf="">
    assert '<span leaf="">' in html, "huashu T-A 文字应包 <span leaf=\"\">(微信编辑器产物)"
    print("[PASS] huashu T-A (17px / #C15F3C / <h1> left-border / #faf9f7 bg / span leaf)")


def test_huashu_template_B() -> None:
    html = render_to_wechat_html(MD_SAMPLE, style="huashu", theme="B")
    assert "#d32f2f" in html, "huashu T-B 主色应是 #d32f2f"
    assert "17px" in html, "huashu T-B 字号也是 17px"
    # T-B H2 用色块,真品用 background-color(不是 background)
    assert "background-color: #d32f2f" in html, \
        "huashu T-B H2 应有红色块背景(真品 background-color 写法)"
    # T-B 用 <h2> 不是 <h1>(真品做法)
    assert "<h2 " in html, "huashu T-B 章节标题用 <h2>(真品做法)"
    print("[PASS] huashu T-B (17px / #d32f2f / <h2> color block)")


def test_huashu_no_emoji_in_render() -> None:
    """渲染层不产 emoji 字符."""
    html = render_to_wechat_html(MD_SAMPLE, style="huashu")
    # 简单检查没有典型 emoji range
    import re
    emoji_pat = re.compile(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]")
    matches = emoji_pat.findall(html)
    assert not matches, f"huashu render 不应注入 emoji,发现 {matches}"
    print("[PASS] huashu render contains no emoji chars")


def test_huashu_signature_present() -> None:
    html = render_to_wechat_html(MD_SAMPLE, style="huashu")
    assert "研究Agent的云" in html, "huashu 应包含风云签名"
    print("[PASS] huashu signature present")


def test_zero_regression_diff() -> None:
    """零回归 diff:一篇较丰富的 md,新签名下不传 style 时 byte-for-byte 等同."""
    rich_md = """---
title: Test
style: not-huashu-still-default
---

# 大标题

第一段,带 **加粗** 和 *斜体* 和 `code` 还有 [链接](https://x.com)。

![alt](https://mmbiz.qpic.cn/foo.jpg)

第二段较长,做长段拆分测试。" + "测" * 200 + ""

## 第一章

> 这是一句引用,不长。

章节正文。

---

## 第二章

再一段。
"""
    # Round 21 决策 1.2 后:default 分支已砍,任何 style 都走 huashu
    # 零回归测试现在 anchor 改为「两次等价调用走 huashu 字节一致」
    h1 = render_to_wechat_html(rich_md, ["https://mmbiz.qpic.cn/a.jpg"], style="huashu")
    h2 = render_to_wechat_html(rich_md, ["https://mmbiz.qpic.cn/a.jpg"], None, True, style="huashu")
    assert h1 == h2, "等价调用应字节一致(huashu 唯一路径)"
    # Round 21 后任何 style 都走 huashu,所以应该包含 huashu 主色
    assert "#C15F3C" in h1, "Round 21 锁定 huashu 唯一路径,应有 huashu 主色"
    print("[PASS] zero regression: huashu 唯一路径下等价调用字节一致")


def test_huashu_image_uses_figure_wrapper() -> None:
    """2026-05-24 Musk × Jobs 沙盒裁决(Jobs 方案胜):
    huashu 图片用 <figure> 包(不是 <section>),避免 line-height 创建 strut 导致下方留白多.
    """
    md_with_img = """# 标题

第一段。

![alt 文本](https://mmbiz.qpic.cn/foo.jpg)

第二段。
"""
    html = render_to_wechat_html(md_with_img, style="huashu")
    assert "<figure" in html, "huashu 图片应用 <figure> wrapper(2026-05-24 sandbox 裁决)"
    # 同时确保 img 仍带微信前端 class
    assert 'class="rich_pages wxw-img"' in html, "img 应保留 rich_pages wxw-img class"
    print("[PASS] huashu image wrapper is <figure> (not <section>) — Jobs verdict 2026-05-24")


def test_lint_works_on_both() -> None:
    issues_default = lint(render_to_wechat_html(MD_SAMPLE))
    issues_huashu = lint(render_to_wechat_html(MD_SAMPLE, style="huashu"))
    # 两边都应通过 lint(或至少不因 huashu 特殊改动崩)
    print(f"[INFO] lint default issues: {issues_default}")
    print(f"[INFO] lint huashu  issues: {issues_huashu}")
    print("[PASS] lint() runs on both branches without crashing")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    tests = [
        test_no_style_arg_defaults_to_huashu,
        test_legacy_style_arg_redirects_to_huashu,
        test_default_positional_args_redirect,
        test_huashu_template_A,
        test_huashu_template_B,
        test_huashu_no_emoji_in_render,
        test_huashu_signature_present,
        test_zero_regression_diff,
        test_huashu_image_uses_figure_wrapper,
        test_lint_works_on_both,
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
