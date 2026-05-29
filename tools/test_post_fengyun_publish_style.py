"""
test_post_fengyun_publish_style.py — 测试 style/theme/article_type 抽取与透传.

只测纯函数 + render mock,不触发微信 API.

跑法:
    python tools/test_post_fengyun_publish_style.py
"""
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS))

import post_fengyun_publish as mod  # noqa: E402


class ParseFrontmatterTests(unittest.TestCase):
    """_parse_fm 抽 style/theme/article_type 的能力."""

    def test_frontmatter_with_style_fields(self):
        fm_text = (
            "---\n"
            "title: 测试\n"
            "style: huashu\n"
            "theme: A\n"
            "article_type: thought_essay\n"
            "---\n"
            "\n"
            "正文..."
        )
        meta, body = mod._parse_fm(fm_text)
        self.assertEqual(meta.get("style"), "huashu")
        self.assertEqual(meta.get("theme"), "A")
        self.assertEqual(meta.get("article_type"), "thought_essay")
        self.assertEqual(meta.get("title"), "测试")
        self.assertEqual(body, "正文...")

    def test_frontmatter_without_style_fields(self):
        fm_text = (
            "---\n"
            "title: 测试\n"
            "---\n"
            "\n"
            "正文..."
        )
        meta, body = mod._parse_fm(fm_text)
        self.assertIsNone(meta.get("style"))
        self.assertIsNone(meta.get("theme"))
        self.assertIsNone(meta.get("article_type"))
        self.assertEqual(body, "正文...")


class RenderDispatchTests(unittest.TestCase):
    """_render_html_layout_rules 是否按 style 条件透传给 render_to_wechat_html."""

    def _fake_layout_rules(self, captured: dict):
        """造一个假的 layout_rules 模块,塞进 sys.modules."""
        fake = types.ModuleType("layout_rules")

        def fake_render(markdown, **kwargs):
            captured["markdown"] = markdown
            captured["kwargs"] = kwargs
            return "<p>FAKE-HTML</p>"

        def fake_lint(html):
            return []

        fake.render_to_wechat_html = fake_render
        fake.lint = fake_lint
        return fake

    def test_style_none_does_not_pass_style_kwargs(self):
        """style=None → kwargs 不含 style/theme/article_type(零回归)."""
        captured: dict = {}
        fake = self._fake_layout_rules(captured)
        with patch.dict(sys.modules, {"layout_rules": fake}):
            html = mod._render_html_layout_rules(
                "正文", section_image_urls=[], style=None)
        self.assertIn("FAKE-HTML", html)
        kwargs = captured["kwargs"]
        self.assertNotIn("style", kwargs)
        self.assertNotIn("theme", kwargs)
        self.assertNotIn("article_type", kwargs)
        # 旧行为参数仍透传
        self.assertEqual(kwargs.get("section_image_urls"), [])
        self.assertEqual(kwargs.get("strip_frontmatter"), False)

    def test_style_huashu_passes_style_theme_article_type(self):
        """style=huashu → kwargs 含 style+theme+article_type."""
        captured: dict = {}
        fake = self._fake_layout_rules(captured)
        with patch.dict(sys.modules, {"layout_rules": fake}):
            mod._render_html_layout_rules(
                "正文", section_image_urls=["http://x/1.png"],
                style="huashu", theme="A", article_type="thought_essay",
            )
        kwargs = captured["kwargs"]
        self.assertEqual(kwargs.get("style"), "huashu")
        self.assertEqual(kwargs.get("theme"), "A")
        self.assertEqual(kwargs.get("article_type"), "thought_essay")

    def test_render_html_no_legacy_mode_round_21(self):
        """Round 21 决策 1.1:legacy 模式已砍,_render_html 签名不再接受 mode 参数."""
        captured: dict = {}
        fake = self._fake_layout_rules(captured)
        with patch.dict(sys.modules, {"layout_rules": fake}):
            # 不传 mode,只传 style — 必须能正常跑
            mod._render_html(
                "## H\n\n段落", insertions=[], image_url_map={},
                style="huashu",
            )
        # layout_rules 应该被调到(走 huashu 路径)
        self.assertIn("kwargs", captured)

    def test_render_html_layout_rules_no_style_zero_regression(self):
        """style=None 时 _render_html 仍正常跑(layout_rules 内部 redirect 到 huashu)."""
        captured: dict = {}
        fake = self._fake_layout_rules(captured)
        with patch.dict(sys.modules, {"layout_rules": fake}):
            mod._render_html(
                "正文", insertions=[], image_url_map={},
                style=None,
            )
        kwargs = captured["kwargs"]
        # Round 21:style=None 时 _render_html 也不会传 style/theme/article_type
        # (layout_rules.render_to_wechat_html 默认 huashu)
        self.assertNotIn("style", kwargs)
        self.assertNotIn("theme", kwargs)
        self.assertNotIn("article_type", kwargs)


class FrontmatterPriorityTests(unittest.TestCase):
    """模拟 main() 里的 frontmatter > CLI 合并逻辑."""

    @staticmethod
    def _resolve(meta: dict, cli_style=None, cli_theme="A",
                 cli_article_type="thought_essay"):
        """复刻 main() 里的合并逻辑."""
        style = (meta.get("style") or cli_style) or None
        if isinstance(style, str):
            style = style.strip() or None
        theme = (meta.get("theme") or cli_theme or "A").strip()
        article_type = (meta.get("article_type") or cli_article_type
                        or "thought_essay").strip()
        return style, theme, article_type

    def test_frontmatter_style_huashu_wins_over_cli_none(self):
        meta = {"style": "huashu", "theme": "A",
                "article_type": "thought_essay"}
        s, t, a = self._resolve(meta, cli_style=None)
        self.assertEqual(s, "huashu")
        self.assertEqual(t, "A")
        self.assertEqual(a, "thought_essay")

    def test_no_frontmatter_falls_back_to_cli(self):
        meta = {}
        s, t, a = self._resolve(meta, cli_style="huashu", cli_theme="B",
                                cli_article_type="tech_demo")
        self.assertEqual(s, "huashu")
        self.assertEqual(t, "B")
        self.assertEqual(a, "tech_demo")

    def test_no_frontmatter_no_cli_returns_none_style(self):
        meta = {}
        s, t, a = self._resolve(meta)
        self.assertIsNone(s)
        # theme / article_type 即便没 style 也仍给 default
        self.assertEqual(t, "A")
        self.assertEqual(a, "thought_essay")

    def test_frontmatter_overrides_cli_when_both_set(self):
        meta = {"style": "huashu", "theme": "A"}
        s, t, _ = self._resolve(meta, cli_style="other", cli_theme="B")
        self.assertEqual(s, "huashu")  # frontmatter wins
        self.assertEqual(t, "A")        # frontmatter wins


if __name__ == "__main__":
    unittest.main(verbosity=2)
