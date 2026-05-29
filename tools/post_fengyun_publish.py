"""
post_fengyun_publish.py — 通用化版 post_fengyun_v3.py

用法:
    python tools/post_fengyun_publish.py <draft.md> [--cover <cover.png>]
                                                    [--no-thumb]
                                                    [--insert TRIGGER=PATH=ALT ...]
                                                    [--html-out <html.html>]

跟 v3 的区别:
- DRAFT_PATH / COVER_PATH 从命令行参数取(v3 写死)
- 找 cover 的默认规则:跟 draft 同名替换后缀为 -cover.{png,jpg}
- 内文图 IMAGE_INSERTIONS 默认空 list(可用 --insert 追加)
- 抽 title / digest / author 自 frontmatter(同 v3)
- 推送成功后打印 draft media_id(同 v3)
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import ssl
import sys
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
DOTENV = ROOT / ".env"


def _load_env():
    if DOTENV.exists():
        for line in DOTENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# ===== Style =====
# Round 21 决策 1.1:legacy 渲染器 + 6 个硬编 style 常量 + FOOTER 已砍
# 排版统一走 layout_rules.py(huashu 模板),不再有 legacy fallback


# ===== WeChat API =====
def _get_token(appid: str, secret: str) -> str:
    url = (f"https://api.weixin.qq.com/cgi-bin/token"
           f"?grant_type=client_credential&appid={appid}&secret={secret}")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, context=ctx, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if "access_token" not in data:
            raise RuntimeError(f"WeChat token error: {data}")
        return data["access_token"]


# 模块级图片上传缓存 — 同一 (abs_path, kind) 上传只走一次,避免重复消耗素材库配额
# 灵感:vendor/baoyu-skills/skills/baoyu-post-to-wechat/scripts/wechat-api.ts:194-232
# 的 uploadedBySource Map<string, UploadResponse>. 这里改成模块级 dict + main() 入口 clear.
_IMAGE_UPLOAD_CACHE: dict[tuple[str, str], dict] = {}


def _upload(token: str, path: Path, kind: str = "img") -> dict:
    # 缓存命中:同一绝对路径 + 同一 kind 直接复用之前 WeChat 返回的 url/media_id
    cache_key = (str(path.resolve()), kind)
    if cache_key in _IMAGE_UPLOAD_CACHE:
        return _IMAGE_UPLOAD_CACHE[cache_key]

    if kind == "thumb":
        url = (f"https://api.weixin.qq.com/cgi-bin/material/add_material"
               f"?access_token={token}&type=thumb")
    else:
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8") + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))

    _IMAGE_UPLOAD_CACHE[cache_key] = resp_data
    return resp_data


def _create_draft(token: str, html: str, title: str, digest: str, author: str,
                  thumb_id: str) -> str:
    """新建草稿(cgi-bin/draft/add),返回 media_id."""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    article = {
        "title": title, "author": author, "digest": digest, "content": html,
        "thumb_media_id": thumb_id,
        "need_open_comment": 1, "only_fans_can_comment": 0, "show_cover_pic": 1,
    }
    body = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if "media_id" not in data:
            raise RuntimeError(f"WeChat draft error: {data}")
        return data["media_id"]


def _update_draft(token: str, existing_media_id: str, html: str,
                  title: str, digest: str, author: str, thumb_id: str,
                  index: int = 0) -> str:
    """Round 19 P0-2 (2026-05-25):更新已有草稿(cgi-bin/draft/update),不产生新 media_id.

    依据微信公众平台官方 API,POST 到 cgi-bin/draft/update,带:
      - media_id: 已存在的草稿
      - index: 要更新的文章索引(单篇 ship 通常 0)
      - articles: 单篇 article dict(注意是 articles 不是 article)

    成功返回 errcode=0,**保持原 media_id**(不变)。
    """
    url = f"https://api.weixin.qq.com/cgi-bin/draft/update?access_token={token}"
    article = {
        "title": title, "author": author, "digest": digest, "content": html,
        "thumb_media_id": thumb_id,
        "need_open_comment": 1, "only_fans_can_comment": 0, "show_cover_pic": 1,
    }
    payload = {
        "media_id": existing_media_id,
        "index": index,
        "articles": article,  # 单篇 — 注意 API 这里是单 dict 不是 list
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"WeChat draft/update error: {data}")
        return existing_media_id  # 更新成功,沿用原 media_id


# ===== draft parsing / rendering =====
def _parse_fm(text: str):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    lines = parts[1].strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v:
                # 单行值(含 inline JSON list 如 [1,2,3])
                meta[k] = v
            else:
                # 空值 → 检查下一行是否 YAML 多行 list(- item)
                collected: list[str] = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith("- "):
                    item = lines[i].strip()[2:].strip()
                    # 去掉 YAML 引号("..." / '...')
                    if len(item) >= 2 and item[0] in ('"', "'") and item[-1] == item[0]:
                        item = item[1:-1]
                    collected.append(item)
                    i += 1
                if collected:
                    import json as _json
                    meta[k] = _json.dumps(collected, ensure_ascii=False)
                else:
                    meta[k] = ""
                continue  # i 已在 while 里推进,跳过底部 i+=1
        i += 1
    return meta, parts[2].strip()


def _render_html_layout_rules(body: str, section_image_urls: list,
                              style: str | None = None,
                              theme: str = "A",
                              article_type: str = "thought_essay",
                              image_at_h2_indices: list[int] | None = None) -> str:
    """Musk × Jobs 沙盒辩论 2026-05-23 共识渲染器(默认 huashu,2026-05-24 Round 10).

    9 维度自动化排版:字号 / 行高 / H2 边 / 引用块 / 分割线 / 段长拆分 /
    首段 banned 词剥除 / 结尾签名 / lint 自检.

    Args:
        style: None / "huashu" → huashu T-A 暖米黄(2026-05-24 起的新默认);
               "default" / "classic" → 原蓝灰 default(opt-out 路径)
        theme: huashu 模板 A/B
        article_type: tech_demo | thought_essay
        image_at_h2_indices: Bug 2 修复 2026-05-24,花叔指定 slot 列表
            None → 老行为(hero + 连续 H2)
            list[int] → 严格按 slot 插(0=intro hero,1=H2[0],2=H2[1]...)
    """
    sys.path.insert(0, str(Path(__file__).parent))  # 确保能 import 同目录 layout_rules
    from layout_rules import render_to_wechat_html, lint

    # 2026-05-24 Round 10:layout_rules 默认 style=huashu,这里透传所有参数
    kwargs = dict(
        section_image_urls=section_image_urls,
        strip_frontmatter=False,  # body 已被 _parse_fm 剥过 frontmatter
    )
    if style is not None:
        kwargs["style"] = style
        kwargs["theme"] = theme
        kwargs["article_type"] = article_type
    if image_at_h2_indices is not None:
        kwargs["image_at_h2_indices"] = image_at_h2_indices
    html = render_to_wechat_html(body, **kwargs)
    issues = lint(html)
    if issues:
        # Bug 7 修复(2026-05-25 Round 17):致命级 issue 阻断 ship
        # FATAL 关键词来自 layout_rules.lint 的 docstring 严重度分类
        fatal_keywords = ["上限", "禁用标签", "<hr>", "position:absolute", "position:fixed"]
        fatal_issues = [i for i in issues
                        if any(k in i for k in fatal_keywords)]
        warn_issues = [i for i in issues if i not in fatal_issues]

        if fatal_issues:
            print(f"❌ layout_rules lint {len(fatal_issues)} FATAL issues — 阻断 ship:")
            for i in fatal_issues:
                print(f"   ✗ {i}")
        if warn_issues:
            print(f"⚠️  layout_rules lint {len(warn_issues)} warn issues(只提示不阻断):")
            for i in warn_issues:
                print(f"   - {i}")

        if fatal_issues:
            raise RuntimeError(
                f"layout_rules.lint 致命级 issue × {len(fatal_issues)}:"
                f"{fatal_issues[0]}(... 其他见上)。修完 html 再 ship。"
            )
    else:
        print(f"   layout_rules lint: 0 issues ✓")
    return html


def _render_html(body: str, insertions: list, image_url_map: dict,
                 style: str | None = None,
                 theme: str = "A",
                 article_type: str = "thought_essay",
                 image_at_h2_indices: list[int] | None = None) -> str:
    """渲染入口 — Round 21 决策 1.1:legacy 分支已砍,只走 layout_rules(huashu).

    Bug 2 修复 2026-05-24:image_at_h2_indices 透传 layout_rules,
    实现花叔指定 H2 slot ↔ 渲染层闭环.
    """
    # layout_rules 模式:把 insertions 的 url 按顺序抽出来作 section_image_urls
    section_urls = []
    for _trigger, img_path, _alt in insertions:
        url = image_url_map.get(Path(img_path).name)
        if url:
            section_urls.append(url)
    return _render_html_layout_rules(
        body, section_urls,
        style=style, theme=theme, article_type=article_type,
        image_at_h2_indices=image_at_h2_indices,
    )


def _find_cover(draft: Path) -> Path | None:
    # YYYYMMDD-<slug>-vN.md -> YYYYMMDD-<slug>-cover.{png,jpg,jpeg}
    stem = draft.stem
    stem = re.sub(r"-v\d+$", "", stem)
    images_dir = ROOT / "output" / "images"
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        cand = images_dir / f"{stem}-cover{ext}"
        if cand.exists():
            return cand
    # 兜底:任何包含 stem + 'cover' 的图
    for f in images_dir.glob(f"{stem}*cover*"):
        return f
    return None


def _parse_insertions(specs: list[str]) -> list[tuple[str, Path, str]]:
    """specs 形如 '## 二、=path/to/img.png=alt 文字' 列表."""
    out = []
    for s in specs:
        bits = s.split("=", 2)
        if len(bits) != 3:
            print(f"WARN: --insert 解析失败({s}),期望 TRIGGER=PATH=ALT")
            continue
        out.append((bits[0], Path(bits[1]), bits[2]))
    return out


def main():
    # 每次 main() 入口 reset 模块级图片上传缓存,避免跨次调用串扰
    _IMAGE_UPLOAD_CACHE.clear()

    ap = argparse.ArgumentParser(description="推送 markdown draft 到微信公众号草稿箱")
    ap.add_argument("draft", help="markdown draft 路径")
    ap.add_argument("--cover", default=None, help="封面图路径(不给则按 slug 自动找)")
    ap.add_argument("--no-thumb", action="store_true", help="不传 thumb(测试用)")
    ap.add_argument("--insert", action="append", default=[],
                    help="内文图,格式 'TRIGGER=PATH=ALT' 可多次")
    ap.add_argument("--html-out", default=None, help="本地 preview HTML 路径")
    # Round 21 决策 1.1:--render-mode 已砍,排版统一走 layout_rules huashu 模板
    ap.add_argument("--style", default="huashu",
                    help="layout_rules style:huashu(默认/唯一活跃路径)")
    ap.add_argument("--theme", default="A", help="huashu 模板 A/B")
    ap.add_argument("--article-type", default="thought_essay",
                    help="tech_demo | thought_essay")
    ap.add_argument("--force-skip-gate", action="store_true",
                    help="紧急绕过 gate.py 物理保安(留 audit log)")
    ap.add_argument("--update-media-id", default=None,
                    help="Round 19 P0-2:已有 media_id,走 draft/update 不产生新草稿。"
                         "不传则走 draft/add(默认行为)。也可从 frontmatter `media_id` 自动读取。")
    args = ap.parse_args()

    draft = Path(args.draft).resolve()
    if not draft.exists():
        print(f"[FATAL] draft 不存在: {draft}")
        sys.exit(2)

    # === Round 17 P0 兜底:gate.py preflight assertion (C 方案) ===
    # 即使 PreToolUse hook 失效 / 没装 / 路径解析挂,也在这里兜住
    # 宪法依据:D:\Dev\ai-wechat-pipeline\WRITE_AGENT.md Step 8
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from gate import check_draft, write_audit_log
        if args.force_skip_gate:
            write_audit_log(draft, passed=True, missing=["FORCE SKIP (C 兜底层)"], force_skip=True)
            print("⚠️  post_fengyun_publish FORCE-SKIP gate(已记 audit)")
        else:
            passed, missing = check_draft(draft)
            write_audit_log(draft, passed, missing)
            if not passed:
                print(f"\n❌ gate preflight BLOCKED:{draft.name} 缺 {len(missing)} 个 step 产物")
                print(f"   宪法依据:WRITE_AGENT.md")
                print()
                for i, reason in enumerate(missing, 1):
                    print(f"   [{i}] {reason}")
                print()
                print("主线程必须回去补完前置 step。紧急情况用 --force-skip-gate(留 audit)")
                sys.exit(2)
            print(f"✅ gate preflight PASS")
    except ImportError as e:
        print(f"⚠️  gate.py import 失败 ({e}),跳过 preflight(主线程自检)")

    _load_env()
    appid = os.environ.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_SECRET")
    if not (appid and secret):
        print("[FATAL] .env 缺 WECHAT_APPID / WECHAT_SECRET")
        sys.exit(2)

    print(f"=== post_fengyun_publish ===")
    print(f"draft: {draft}")

    text = draft.read_text(encoding="utf-8")
    meta, body = _parse_fm(text)
    title = meta.get("title", draft.stem).strip()
    digest = meta.get("digest", "").strip()
    author = meta.get("author", "研究Agent的云").strip()
    print(f"title:  {title}  ({len(title)} chars)")
    print(f"author: {author}")
    print(f"digest: {digest[:60]}{'...' if len(digest) > 60 else ''}")

    # frontmatter 优先 > 命令行(作者意图优先于命令行覆盖)
    style = (meta.get("style") or args.style) or None
    if isinstance(style, str):
        style = style.strip() or None
    theme = (meta.get("theme") or args.theme or "A").strip()
    article_type = (meta.get("article_type") or args.article_type
                    or "thought_essay").strip()
    if style:
        print(f"style:  {style}  (theme={theme}, article_type={article_type})")

    # Bug 2 闭环 2026-05-24:从 frontmatter 读 image_at_h2_indices
    # illustrate_decider.write_metadata() 把花叔决策的 slot 列表写到这里
    image_at_h2_indices: list[int] | None = None
    iah_raw = meta.get("image_at_h2_indices", "").strip()
    if iah_raw:
        try:
            # YAML inline list 形如 [1, 3, 5]
            import json as _json
            image_at_h2_indices = _json.loads(iah_raw)
            if isinstance(image_at_h2_indices, list) and all(isinstance(i, int) for i in image_at_h2_indices):
                print(f"image_at_h2_indices: {image_at_h2_indices}  (花叔决策位置,Bug 2 闭环)")
            else:
                print(f"⚠️  image_at_h2_indices 格式错(非 int list),忽略:{iah_raw}")
                image_at_h2_indices = None
        except Exception as e:
            print(f"⚠️  image_at_h2_indices 解析失败({e}),忽略:{iah_raw}")
            image_at_h2_indices = None

    cover = Path(args.cover).resolve() if args.cover else _find_cover(draft)
    if not args.no_thumb:
        if not cover or not cover.exists():
            print(f"[FATAL] 找不到封面图(默认按 slug 找,或用 --cover 指定)")
            sys.exit(2)
        print(f"cover:  {cover}")

    insertions = _parse_insertions(args.insert)

    # Bug B 修复 2026-05-25:CLI 没传 --insert 时,自动从 frontmatter image_paths 读
    # illustrate_decider 把 Seedream 生成的图写到 image_paths(inline JSON list)
    # Round 25 修:多行 YAML array 已由 _parse_fm 序列化为 JSON list;
    #   同时过滤掉 cover(封面已由 thumb 通道上传,不重复作 inline image)
    if not insertions:
        ip_raw = meta.get("image_paths", "").strip()
        if ip_raw.startswith("[") and ip_raw.endswith("]"):
            try:
                import json as _json
                ip_list = _json.loads(ip_raw)
                if isinstance(ip_list, list):
                    cover_name = cover.name if cover else None
                    for i, p in enumerate(ip_list):
                        ipath = Path(p)
                        if not ipath.is_absolute():
                            ipath = ROOT / ipath
                        # 跳过封面(已由 thumb 通道处理)
                        if cover_name and ipath.name == cover_name:
                            continue
                        if ipath.exists():
                            insertions.append((f"[auto-{i}]", ipath, ipath.stem))
                    if insertions:
                        print(f"image_paths: 从 frontmatter 自动接入 {len(insertions)} 张内文图(已排除封面)")
            except Exception as e:
                print(f"⚠️  image_paths 解析失败({e})")

    token = _get_token(appid, secret)
    print(f"[1/4] token OK")

    thumb_id = None
    if not args.no_thumb:
        thumb_data = _upload(token, cover, "thumb")
        thumb_id = thumb_data.get("media_id")
        if not thumb_id:
            print(f"[FATAL] 上传封面失败: {thumb_data}")
            sys.exit(2)
        print(f"[2/4] cover uploaded -> {thumb_id[:30]}...")
    else:
        print(f"[2/4] skip thumb (--no-thumb)")

    image_url_map = {}
    for trigger, img_path, alt in insertions:
        data = _upload(token, img_path, "img")
        image_url_map[img_path.name] = data.get("url", "")
    if insertions:
        print(f"[3/4] {len(insertions)} 内文图 uploaded")
    else:
        print(f"[3/4] no inline images")

    print(f"[4/4] render: layout_rules huashu (Round 21 锁定唯一路径)")
    html = _render_html(
        body, insertions, image_url_map,
        style=style, theme=theme, article_type=article_type,
        image_at_h2_indices=image_at_h2_indices,
    )
    print(f"       HTML: {len(html):,} chars")

    # 本地 preview
    html_out = Path(args.html_out) if args.html_out else (
        ROOT / "output" / "html" / f"{draft.stem}.html")
    html_out.parent.mkdir(parents=True, exist_ok=True)
    preview = (
        f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>'
        f'</head><body style="max-width:677px; margin:20px auto; padding:20px; '
        f"background:#fff; font-family:'PingFang SC',sans-serif;\">"
        f'<p style="margin:0 0 22px 0; padding:0; font-size:22px; font-weight:600; '
        f'color:#222; line-height:1.4; text-align:center;">{title}</p>'
        f'<p style="margin:0 0 28px 0; padding:0; font-size:12px; color:#666; '
        f'text-align:center;">{author}</p>{html}</body></html>'
    )
    html_out.write_text(preview, encoding="utf-8")
    print(f"preview: {html_out}")

    if args.no_thumb:
        print("\n--no-thumb 模式,跳过 create_draft")
        return

    # Round 19 P0-2 (2026-05-25): draft/update 路径 — 避免重推产生重复草稿
    # 优先级:CLI --update-media-id > frontmatter media_id > draft/add 新建
    update_target = args.update_media_id
    if not update_target:
        # fallback:从 frontmatter 读 media_id(上次 ship 时持久化)
        fm_media_id = (meta.get("media_id") or "").strip().strip('"').strip("'")
        if fm_media_id:
            update_target = fm_media_id
            print(f"[draft/update] 从 frontmatter media_id 读到 {update_target[:30]}...,走 update 路径")

    if update_target:
        try:
            draft_id = _update_draft(
                token, update_target, html, title, digest, author, thumb_id
            )
            print(f"\nOK 草稿 UPDATED media_id: {draft_id}(沿用原 ID,不产生新草稿)")
        except Exception as e:
            # update 失败(media_id 可能已经被微信清掉)→ 兜底 draft/add
            print(f"\n⚠️  draft/update 失败({e}),兜底走 draft/add")
            draft_id = _create_draft(token, html, title, digest, author, thumb_id)
            print(f"OK 草稿 NEW media_id: {draft_id}")
    else:
        draft_id = _create_draft(token, html, title, digest, author, thumb_id)
        print(f"\nOK 草稿 NEW media_id: {draft_id}")

    print("公众号后台 -> 草稿箱 -> 审阅 -> 发出")

    # 把 media_id 持久化:① cover.media_id.txt ② draft frontmatter `media_id` 字段
    Path(str(cover) + ".media_id.txt").write_text(thumb_id, encoding="utf-8")

    # Round 19 P0-2:把 draft media_id 写回 frontmatter,下次重推自动走 update
    try:
        draft_text = draft.read_text(encoding="utf-8")
        if draft_text.startswith("---"):
            parts = draft_text.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                body = parts[2]
                # 替换或追加 media_id 字段
                if re.search(r"^media_id:", fm, flags=re.MULTILINE):
                    new_fm = re.sub(
                        r'^media_id:.*$',
                        f'media_id: "{draft_id}"',
                        fm, flags=re.MULTILINE,
                    )
                else:
                    new_fm = fm.rstrip() + f'\nmedia_id: "{draft_id}"\n'
                new_text = "---" + new_fm + "---" + body
                draft.write_text(new_text, encoding="utf-8")
                print(f"[draft/update] media_id 已持久化到 frontmatter,下次重推自动走 update")
    except Exception as e:
        # 写入失败不阻断流程
        print(f"⚠️  media_id 写回 frontmatter 失败(不影响 ship): {e}")


if __name__ == "__main__":
    main()
