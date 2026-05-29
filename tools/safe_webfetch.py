"""
safe_webfetch.py — WebFetch 反爬 retry wrapper(Bug 6 修复,2026-05-24)

设计原则:
- Claude 内置的 WebFetch 工具不能直接修改,本脚本提供 Python 层包装
- 用 urllib + 浏览器 UA 直接抓页面,403 时 retry 一次另一个 UA
- 仍 fail → 返回 None,调用者降级到 WebSearch 摘要

接口:
    from tools.safe_webfetch import safe_fetch
    result = safe_fetch(url, fallback_to_websearch=True)
    # 返回 dict {ok: bool, html: str | None, error: str | None, attempts: int}

不替代 Claude WebFetch(它有 markdown 转换 + LLM 摘要功能):
- 用法 1:在 Claude 主线程发现 WebFetch 403 → 调本脚本拿 raw HTML
- 用法 2:在自动化脚本里需要可靠抓页面 → 直接调本脚本
"""
from __future__ import annotations
import sys
import ssl
import urllib.request
from typing import Optional, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# 3 个浏览器 UA(轮换用,反爬升级时换备用)
UA_POOL = [
    # macOS Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # macOS Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0",
]


def safe_fetch(
    url: str,
    *,
    timeout: int = 30,
    max_retries: int = 2,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """带 UA 轮换 + retry 的 GET 抓取。

    Args:
        url: 目标 URL
        timeout: 单次请求超时(秒)
        max_retries: 失败重试次数(每次换 UA)
        extra_headers: 额外 header dict(如 Cookie / Referer)

    Return:
        {
            "ok": bool,
            "html": str | None,           # 抓到的 raw HTML(decoded utf-8)
            "status": int | None,         # HTTP 状态码
            "error": str | None,          # 失败原因
            "attempts": int,              # 实际尝试次数
            "ua_used": str | None,        # 成功时用的 UA
        }
    """
    result = {
        "ok": False,
        "html": None,
        "status": None,
        "error": None,
        "attempts": 0,
        "ua_used": None,
    }

    headers_base = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    }
    if extra_headers:
        headers_base.update(extra_headers)

    last_error = None
    for attempt in range(max_retries + 1):
        ua = UA_POOL[attempt % len(UA_POOL)]
        headers = dict(headers_base)
        headers["User-Agent"] = ua

        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                raw = resp.read()
                # 处理 gzip
                if resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                # decode
                try:
                    html = raw.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        html = raw.decode("gbk")
                    except UnicodeDecodeError:
                        html = raw.decode("utf-8", errors="replace")

                result.update({
                    "ok": True,
                    "html": html,
                    "status": resp.status,
                    "attempts": attempt + 1,
                    "ua_used": ua,
                })
                return result
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}: {e.reason}"
            result["status"] = e.code
            # 403 / 429 才 retry,500-class 不 retry
            if e.code in (403, 429) and attempt < max_retries:
                continue
            else:
                break
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                continue
            else:
                break

    result.update({
        "ok": False,
        "error": last_error,
        "attempts": max_retries + 1,
    })
    return result


def cli():
    """CLI 入口:python safe_webfetch.py <url>"""
    if len(sys.argv) < 2:
        print("用法: python safe_webfetch.py <url> [timeout=30]", file=sys.stderr)
        sys.exit(2)
    url = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    r = safe_fetch(url, timeout=timeout)
    if r["ok"]:
        print(f"OK status={r['status']} attempts={r['attempts']} ua_used={r['ua_used']}",
              file=sys.stderr)
        print(f"--- HTML ({len(r['html'])} chars) ---", file=sys.stderr)
        # 前 5000 字符够给 caller 看了
        sys.stdout.write(r["html"][:5000])
    else:
        print(f"FAIL status={r['status']} error={r['error']} attempts={r['attempts']}",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli()
