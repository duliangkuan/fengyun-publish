"""
test_post_fengyun_publish_image_cache.py — 2026-05-24
验证 post_fengyun_publish._upload 的图片去重 dict 缓存。

测试目标:
1. 同一 path + 同一 kind 调 2 次 → 底层 urlopen 只走 1 次
2. 不同 path 各自上传一次
3. 不同 kind(img vs thumb)即便同 path 也不复用(资源类型不同)
4. main() 入口会 clear cache(避免跨次调用串扰)

跑法:
    python tools/test_post_fengyun_publish_image_cache.py
"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS))

import post_fengyun_publish as mod  # noqa: E402


def _fake_resp(payload: dict):
    """造一个 mock urlopen context manager — read() 返回 JSON bytes."""
    import json as _json

    class _Ctx:
        def __enter__(self_inner):
            return io.BytesIO(_json.dumps(payload).encode("utf-8"))

        def __exit__(self_inner, *a):
            return False

    return _Ctx()


class UploadCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        # 每个 test 独立 clear,避免相互污染
        mod._IMAGE_UPLOAD_CACHE.clear()
        # 造两个真实的临时图文件(_upload 会调 path.resolve() + read_bytes())
        self.tmpdir = tempfile.mkdtemp()
        self.img_a = Path(self.tmpdir) / "a.png"
        self.img_a.write_bytes(b"\x89PNG\r\n\x1a\nfake-a")
        self.img_b = Path(self.tmpdir) / "b.png"
        self.img_b.write_bytes(b"\x89PNG\r\n\x1a\nfake-b")

    def tearDown(self) -> None:
        mod._IMAGE_UPLOAD_CACHE.clear()
        try:
            self.img_a.unlink()
            self.img_b.unlink()
            Path(self.tmpdir).rmdir()
        except OSError:
            pass

    def test_same_path_same_kind_uploads_once(self):
        """同一 path + 同一 kind 调 2 次,底层 urlopen 只跑 1 次."""
        with patch.object(mod.urllib.request, "urlopen") as urlopen:
            urlopen.return_value = _fake_resp({"url": "https://mmbiz/u1", "media_id": "m1"})
            r1 = mod._upload("TOKEN", self.img_a, "img")
            r2 = mod._upload("TOKEN", self.img_a, "img")
        self.assertEqual(r1, r2)
        self.assertEqual(r1.get("url"), "https://mmbiz/u1")
        # 关键断言:urlopen 只被调一次
        self.assertEqual(urlopen.call_count, 1,
                         f"expected 1 urlopen, got {urlopen.call_count}")

    def test_different_paths_each_uploaded_once(self):
        """不同 path 各自上传一次,共两次."""
        responses = [
            _fake_resp({"url": "https://mmbiz/A", "media_id": "mA"}),
            _fake_resp({"url": "https://mmbiz/B", "media_id": "mB"}),
        ]
        with patch.object(mod.urllib.request, "urlopen", side_effect=responses) as urlopen:
            ra = mod._upload("TOKEN", self.img_a, "img")
            rb = mod._upload("TOKEN", self.img_b, "img")
        self.assertEqual(ra.get("url"), "https://mmbiz/A")
        self.assertEqual(rb.get("url"), "https://mmbiz/B")
        self.assertEqual(urlopen.call_count, 2)

    def test_same_path_different_kind_not_shared(self):
        """同一 path 但 kind 不同(img vs thumb)各自上传一次,因为资源类型不同."""
        responses = [
            _fake_resp({"url": "https://mmbiz/img", "media_id": "mi"}),
            _fake_resp({"media_id": "mt"}),  # thumb 不返 url
        ]
        with patch.object(mod.urllib.request, "urlopen", side_effect=responses) as urlopen:
            r_img = mod._upload("TOKEN", self.img_a, "img")
            r_thumb = mod._upload("TOKEN", self.img_a, "thumb")
        self.assertEqual(r_img.get("url"), "https://mmbiz/img")
        self.assertEqual(r_thumb.get("media_id"), "mt")
        self.assertEqual(urlopen.call_count, 2,
                         "img 和 thumb 是两种资源,缓存不应共用")

    def test_cache_populated_after_upload(self):
        """上传一次后 cache 里应有对应条目."""
        with patch.object(mod.urllib.request, "urlopen") as urlopen:
            urlopen.return_value = _fake_resp({"url": "https://mmbiz/x", "media_id": "mx"})
            mod._upload("TOKEN", self.img_a, "img")
        key = (str(self.img_a.resolve()), "img")
        self.assertIn(key, mod._IMAGE_UPLOAD_CACHE)
        self.assertEqual(mod._IMAGE_UPLOAD_CACHE[key].get("media_id"), "mx")


class MainClearsCacheTests(unittest.TestCase):
    """main() 入口应清空 _IMAGE_UPLOAD_CACHE,避免跨次调用串扰."""

    def test_main_clears_cache_at_entry(self):
        # 先往 cache 塞一条假数据
        mod._IMAGE_UPLOAD_CACHE[("/fake/path.png", "img")] = {"url": "stale"}
        self.assertEqual(len(mod._IMAGE_UPLOAD_CACHE), 1)

        # 跑 main() — 用故意非法的 argv 让 main 在 clear 后立刻 sys.exit,
        # 我们只在意 cache 被 clear 这一行为
        with patch.object(sys, "argv", ["prog", "/nonexistent/draft.md"]):
            with self.assertRaises(SystemExit):
                mod.main()
        # main() 第一行就是 _IMAGE_UPLOAD_CACHE.clear(),所以即便后面 sys.exit cache 也已清空
        self.assertEqual(len(mod._IMAGE_UPLOAD_CACHE), 0,
                         "main() 入口应清空 _IMAGE_UPLOAD_CACHE")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    unittest.main(verbosity=2)
