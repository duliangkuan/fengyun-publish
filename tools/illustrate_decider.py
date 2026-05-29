"""
illustrate_decider.py — 风云 ship pipeline Step 7 配图决策 + 生成入口

设计原则(Round 25 升级 — Musk × Newton 同意,Jobs 保留意见):
- 决策层走 huashu-image-curator skill Mode 2(Claude 主线程 invoke,本脚本不调 LLM API)
- 函数层只做:候选位置预筛 + 调火山 Seedream 出图 + 落地 metadata
- **Round 25 强制必选:0 图 ship 路径已删**(对比 Round 9 允许 0 图的旧策略)
  - 用户决策方案 A(2026-05-25):物理硬约束 — 任何 ship 必须 ≥ 1 张内文图
  - should_illustrate=false 路径:即使 skill 返回 false,本模块强制 fallback 到 placeholder
  - daily_quota / 全失败:placeholder fallback,不再 degraded ship 0 图
- 篇内 style_anchor 一致,篇间自由
- failure mode:任何一层失败 → placeholder fallback,绝不返回空 list

接口(Python 函数,被 fengyun-publish Step 7 import 用):

1. pick_candidates(article_md: str) -> List[Position]
   函数预筛候选位置(H2 + 段落 ≥ 400 字)。无 LLM 调用。

2. read_article_meta(draft_path: Path) -> dict
   读 frontmatter + 提 word_count + h2_sections。

3. generate_from_decision(decision: dict, output_dir: Path, slug: str) -> List[Path]
   接 huashu-image-curator Mode 2 输出的 Decision JSON,并发调火山 Seedream 出图。
   复用 generate_article_images.py 的 _call_seedream 逻辑。

4. write_metadata(draft_path: Path, decision: dict, image_paths: List[Path]) -> None
   把 Decision + image_paths 写入 frontmatter `images:` 字段(数据飞轮被动观察)。

production 用法(在 Claude 主线程,fengyun-publish skill Step 7):
   meta = read_article_meta(draft_path)
   candidates = pick_candidates(meta["article_md"])
   # ↓ 主线程 invoke huashu-image-curator Mode 2 拿 Decision JSON
   decision = <Claude 主线程调 huashu-image-curator skill 出 JSON>
   # Round 25:无论 decision["should_illustrate"] 真假,都调 generate_from_decision
   # 内部强制保证 image_paths 非空(should_illustrate=false 时自动 placeholder fallback)
   image_paths = generate_from_decision(decision, OUT_DIR, slug)
   write_metadata(draft_path, decision, image_paths)
"""

from __future__ import annotations
import json
import os
import re
import shutil
import ssl
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
OUT_DIR = ROOT / "output" / "images"
OUT_DIR.mkdir(exist_ok=True, parents=True)

# Round 25:placeholder image 静态 asset(Seedream fallback 用)
PLACEHOLDER_SRC = ROOT / "assets" / "placeholder-sketch.png"

load_dotenv(ROOT / ".env")


def _copy_placeholder_to_output(slug: str, count: int = 1) -> list[Path]:
    """Round 25 fallback:复制 placeholder 到 output/images/<slug>-NN-placeholder.png

    Seedream daily_quota / 全失败 → placeholder fallback,不返回空 list。
    placeholder 文件 size ≥ 5 KB(通过 gate 有效性 floor)。

    Args:
        slug: 文章 slug
        count: 需要复制的数量(默认 1)

    Returns:
        list[Path]:placeholder 副本路径列表
    """
    if not PLACEHOLDER_SRC.exists():
        # 极端情况:placeholder 也丢了 → hard abort(不允许 0 图)
        raise RuntimeError(
            f"placeholder asset 不存在: {PLACEHOLDER_SRC}\n"
            f"修复:跑 `python assets/generate_placeholder.py` 重新生成"
        )
    paths = []
    for i in range(1, count + 1):
        dst = OUT_DIR / f"{slug}-{i:02d}-placeholder.png"
        shutil.copy2(PLACEHOLDER_SRC, dst)
        paths.append(dst)
        print(f"  [{slug}-{i:02d}] placeholder fallback → {dst.name}", flush=True)
    return paths


# ============================================================
# Step 1: 候选位置预筛(纯函数,无 LLM 调用)
# ============================================================

@dataclass
class Position:
    """文章里一个候选配图位置"""
    h2_idx: int               # 第几个 H2(0-based)
    h2_title: str             # H2 标题
    position_idx: int         # 全文段落索引(0-based,frontmatter 后开始)
    paragraph_preview: str    # 段落前 200 字预览
    word_count: int           # 段落总字数


def pick_candidates(article_md: str, min_para_chars: int = 80) -> list[Position]:
    """函数预筛候选配图位置(无 LLM 调用)。

    规则(Round 9 修正,基于风云实际段落分布):
    - 风云文章 H2 首段经常是 8-30 字过渡短句,不能用「H2 紧跟首段」作候选
    - 改为:每个 H2 章节里**第一段达到 ≥ min_para_chars 字的段**作候选
    - 同时:任何 ≥ 200 字的长段也作候选(可能是核心论证段)
    - intro 章节(第一个 H2 之前的开场)也算一个虚拟 chapter,取第一段 ≥ min_para_chars
    - 跳过 frontmatter / H1-H6 / 引用 / 列表

    Args:
        article_md: 文章 markdown(可带 frontmatter)
        min_para_chars: H2 章节首个 substantive 段的最小字数,默认 80

    Return: List[Position],按 position_idx 升序
    """
    # 剥 frontmatter
    body = article_md
    if body.lstrip().startswith("---"):
        parts = body.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]

    paragraphs = re.split(r"\n\s*\n", body.strip())

    candidates: list[Position] = []
    h2_idx = -1
    current_h2_title = "(intro)"   # 虚拟 intro 章节
    h2_first_substantive_found: dict[int, bool] = {}  # 每个 h2_idx 是否已找到 substantive 首段
    seen_positions: set[int] = set()

    for idx, p in enumerate(paragraphs):
        p_stripped = p.strip()
        if not p_stripped:
            continue

        # H2 章节标题 → 切换章节
        if p_stripped.startswith("## "):
            h2_idx += 1
            current_h2_title = p_stripped[3:].strip()
            h2_first_substantive_found[h2_idx] = False
            continue

        # H1 / H3 / H4 / 引用 / 列表 跳过
        if p_stripped.startswith("#"):
            continue
        if p_stripped.startswith(">") or p_stripped.startswith("- ") or p_stripped.startswith("* "):
            continue

        # 计算「字数」(中文按字数,去掉 markdown 标记)
        plain = re.sub(r"[*`\[\]()!\-]", "", p_stripped)
        word_count = len(plain)

        # 候选条件 1: 本 H2 章节的第一个 substantive 段(≥ min_para_chars)
        is_first_substantive = (
            h2_first_substantive_found.get(h2_idx, True) is False
            and word_count >= min_para_chars
        )
        if is_first_substantive and idx not in seen_positions:
            candidates.append(Position(
                h2_idx=h2_idx,
                h2_title=current_h2_title,
                position_idx=idx,
                paragraph_preview=p_stripped[:200],
                word_count=word_count,
            ))
            seen_positions.add(idx)
            h2_first_substantive_found[h2_idx] = True
            continue

        # 候选条件 2: 任何 ≥ 200 字的长段(核心论证段,可能不是 H2 首段)
        if word_count >= 200 and idx not in seen_positions:
            candidates.append(Position(
                h2_idx=h2_idx,
                h2_title=current_h2_title,
                position_idx=idx,
                paragraph_preview=p_stripped[:200],
                word_count=word_count,
            ))
            seen_positions.add(idx)

    return candidates


# ============================================================
# Step 2: 读 article meta(frontmatter + word_count + h2)
# ============================================================

def read_article_meta(draft_path: Path) -> dict:
    """读 markdown,返回 meta dict + 全文."""
    text = draft_path.read_text(encoding="utf-8")
    body = text

    frontmatter: dict = {}
    if text.lstrip().startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2]
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip()

    # H2 chapters
    h2_titles = re.findall(r"^## (.+)$", body, flags=re.MULTILINE)

    # word_count(中文按字数,粗略剔除 markdown 标记)
    plain = re.sub(r"[#*`>\-\[\]()!]", "", body)
    plain = re.sub(r"\s+", "", plain)
    word_count = len(plain)

    return {
        "draft_path": str(draft_path),
        "slug": frontmatter.get("slug", draft_path.stem),
        "title": frontmatter.get("title", ""),
        "frontmatter": frontmatter,
        "article_md": text,    # 完整含 frontmatter,给 huashu-image-curator skill
        "body": body,           # 剥 frontmatter 后正文,给 pick_candidates
        "h2_titles": h2_titles,
        "h2_count": len(h2_titles),
        "word_count": word_count,
    }


# ============================================================
# Step 3: 调火山 Seedream 出图(复用 generate_article_images.py 逻辑)
# ============================================================

ARK_KEY = os.environ.get("VOLCENGINE_IMAGE_KEY")
ARK_URL = (
    os.environ.get("VOLCENGINE_IMAGE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    + "/images/generations"
)
ARK_MODEL = os.environ.get("VOLCENGINE_IMAGE_MODEL", "doubao-seedream-5-0-260128")


# ============================================================
# P0-3 (Round 18, 2026-05-25): 限流错误分类
# ============================================================
# 审计报告 §三 P0-1 发现:宪法只写了 60/120/240s backoff,对日额度等于没兜底。
# 实测今天 TrapDoor 文就是因 daily quota exceeded 直接 0 图 degraded。
#
# 错误分类(根据错误字符串内容):
#   - "rps_limit" / "rate limit" + retry 后立刻又 429 → 短期限流(可 retry)
#   - "daily" / "quota" / "quota_exceeded" → 日额度(24h 无解,直接 abort)
#   - 第 1 张就 429 + 重试 ≥ 2 次仍 429 → 推定日额度(经验法则)

QUOTA_EXCEEDED_KEYWORDS = (
    "daily", "quota", "quota_exceeded", "rate_limit_exceeded",
    "exceeded the limit", "limit_exceeded", "RPM_LIMIT", "RPD_LIMIT",
    # Round 21 P0-14: 火山 Safe Experience Mode(隔壁 e2e 抓的新错误码)
    "SetLimitExceeded", "safe experience mode", "safe_experience",
    "SafeExperienceMode", "TPM_LIMIT", "TPD_LIMIT",
)


def _classify_seedream_error(error_msg: str) -> str:
    """分类:'daily_quota' / 'rps_limit' / 'transient' / 'other'."""
    if not error_msg:
        return "other"
    msg_lower = error_msg.lower()
    if any(k.lower() in msg_lower for k in QUOTA_EXCEEDED_KEYWORDS):
        return "daily_quota"
    if "429" in error_msg or "too many requests" in msg_lower:
        return "rps_limit"
    if "timeout" in msg_lower or "ssl" in msg_lower or "connection" in msg_lower:
        return "transient"
    return "other"


def _call_seedream(prompt: str, output_path: Path, slug_for_log: str = "img") -> dict:
    """直调火山方舟 Seedream API 生成一张图并下载到本地。

    Return: {slug, path, ok, error?, error_type?, duration_s}
        error_type: 'daily_quota' / 'rps_limit' / 'transient' / 'other'(失败时)
    """
    if not ARK_KEY:
        return {"slug": slug_for_log, "ok": False, "error": "VOLCENGINE_IMAGE_KEY 未配置",
                "error_type": "other"}

    payload = {
        "model": ARK_MODEL,
        "prompt": prompt,
        "size": "2K",
        "response_format": "url",
        "watermark": False,
    }
    headers = {
        "Authorization": f"Bearer {ARK_KEY}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        ARK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    print(f"  [{slug_for_log}] 调用 Seedream API ...", flush=True)
    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=180) as resp:
            body = resp.read().decode("utf-8")
        data = json.loads(body)
        img_url = data["data"][0]["url"]
        dt = time.time() - t0
        print(f"  [{slug_for_log}] API 返回(耗时 {dt:.1f}s),下载 ...", flush=True)

        urllib.request.urlretrieve(img_url, str(output_path))
        size_kb = output_path.stat().st_size / 1024
        print(f"  [{slug_for_log}] OK {output_path.name} ({size_kb:.0f} KB)", flush=True)
        return {"slug": slug_for_log, "path": str(output_path), "ok": True, "duration_s": dt}
    except Exception as e:
        dt = time.time() - t0
        err_str = str(e)
        err_type = _classify_seedream_error(err_str)
        print(f"  [{slug_for_log}] FAIL ({dt:.1f}s, type={err_type}): {e}", flush=True)
        return {"slug": slug_for_log, "ok": False, "error": err_str,
                "error_type": err_type, "duration_s": dt}


def derive_image_at_h2_indices(decision: dict) -> list[int]:
    """Bug 2 修复 2026-05-24:从 decision 派生 image_at_h2_indices.

    优先从 decision['image_at_h2_indices'] 字段直接读,
    否则从 decision['positions'][i]['h2_slot'] 字段派生,
    否则 fallback 用 positions 顺序对应 1, 2, 3...(老行为).

    Returns:
        list[int]: slot 编号(0=intro hero, 1=H2[0], 2=H2[1]...)
    """
    if "image_at_h2_indices" in decision and isinstance(decision["image_at_h2_indices"], list):
        return list(decision["image_at_h2_indices"])
    positions = decision.get("positions", [])
    if positions and all(isinstance(p, dict) and "h2_slot" in p for p in positions):
        return [p["h2_slot"] for p in positions]
    # fallback:1-based 顺序对应 H2(没花叔指定 → layout_rules 用 None 走老行为)
    return None


def generate_from_decision(
    decision: dict,
    output_dir: Path,
    slug: str,
    max_workers: int = 3,
    retry_failed: bool = True,
) -> list[Path]:
    """接 huashu-image-curator Mode 2 输出的 Decision JSON,并发出图。

    Args:
        decision: Mode 2 JSON {should_illustrate, count, prompts, image_at_h2_indices, ...}
        output_dir: 输出目录(默认 D:/Dev/ai-wechat-pipeline/output/images/)
        slug: 文章 slug,用于命名 <slug>-NN-img.png
        max_workers: 并发数,默认 3
        retry_failed: 是否对失败的图 retry 一次

    Return: 成功出图的 Path list(可能少于 decision["count"])

    注:image_at_h2_indices 通过 write_metadata 写到 frontmatter,
    然后 post_fengyun_publish 从 frontmatter 读取透传给 layout_rules(Bug 2 闭环).
    """
    if not decision.get("should_illustrate", False):
        # skill 返回 false → placeholder fallback(应永远走不到这,SKILL.md 已删此返回路径)
        print(f"[fallback] reason=skill_returned_false slug={slug}", flush=True)
        decision["fallback_reason"] = "skill_returned_false"
        # Bug 3 修复:placeholder 路径必须写 image_at_h2_indices,
        # 否则 derive 函数返回 None,write_metadata 不写字段,gate.py 会拦
        decision["image_at_h2_indices"] = [0]  # 单张 placeholder 默认放 intro slot
        return _copy_placeholder_to_output(slug, count=1)

    prompts: list[str] = decision.get("prompts", [])
    count = len(prompts)
    if count == 0:
        # prompts 解析失败 → placeholder fallback
        print(f"[fallback] reason=prompt_parse_fail slug={slug}", flush=True)
        decision["fallback_reason"] = "prompt_parse_fail"
        # Bug 3 修复:同上,placeholder 路径必须写 image_at_h2_indices
        decision["image_at_h2_indices"] = [0]
        return _copy_placeholder_to_output(slug, count=1)

    style_anchor = decision.get("style_anchor", "")

    # 准备 task list
    tasks = []
    for i, prompt in enumerate(prompts, start=1):
        # 把 style_anchor append 进 prompt(篇内一致)
        full_prompt = prompt
        if style_anchor:
            full_prompt = f"{prompt}, overall style: {style_anchor}"
        # 加 universal 约束:无文字 / 无英文专名 / 不要符号化
        full_prompt += (
            ", NO text labels, NO English words, NO Chinese characters, "
            "NO logos, NO realistic photo, NOT 3D render, "
            "purely visual storytelling through composition and gesture."
        )

        slug_full = f"{slug}-{i:02d}"
        out_path = output_dir / f"{slug_full}.png"
        tasks.append({"prompt": full_prompt, "output_path": out_path, "slug": slug_full})

    print(f"\n=== 并发出图 {count} 张(火山 Seedream,workers={max_workers})===", flush=True)
    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(_call_seedream, t["prompt"], t["output_path"], t["slug"]): t
            for t in tasks
        }
        for f in as_completed(futures):
            results.append(f.result())

    # P0-3 Round 18: 日额度兜底 — 第 1 轮全部 429 且检测到 daily_quota → 立即 abort,不无效 retry
    failed = [r for r in results if not r.get("ok")]
    if failed and len(failed) == len(results):  # 全部失败
        daily_quota_hits = sum(1 for r in failed if r.get("error_type") == "daily_quota")
        rps_hits = sum(1 for r in failed if r.get("error_type") == "rps_limit")
        # 显式 daily_quota → 立即 abort
        # 或 ≥ 2 张 rps_limit 但即时重试也 429 → 推定日额度
        if daily_quota_hits >= 1 or (rps_hits >= 2 and count >= 2):
            # daily_quota 触发 → placeholder fallback
            elapsed = time.time() - t0
            print(f"[fallback] reason=seedream_daily_quota slug={slug} "
                  f"failed={len(failed)}/{count} daily={daily_quota_hits} rps={rps_hits} "
                  f"elapsed={elapsed:.0f}s", flush=True)
            decision["fallback_reason"] = "seedream_daily_quota"
            # Bug 3 修复:placeholder 路径写 image_at_h2_indices(沿用原 decision 或 fallback)
            if not decision.get("image_at_h2_indices"):
                decision["image_at_h2_indices"] = list(range(count))
            return _copy_placeholder_to_output(slug, count=count)

    # retry 失败的图(仅 transient / 单张 rps 才走 retry),指数退避(G5 Newton 修复)
    if retry_failed and failed:
        # G5:exponential backoff 1s / 2s / 4s,真实现 SPEC §2 承诺
        for attempt, backoff_s in enumerate([1, 2, 4], start=1):
            still_failed = [r for r in results if not r.get("ok")]
            if not still_failed:
                break
            print(f"\n=== Retry attempt {attempt}/3 ({len(still_failed)} 张),"
                  f"backoff {backoff_s}s ===", flush=True)
            time.sleep(backoff_s)
            retry_tasks = [next(t for t in tasks if t["slug"] == r["slug"])
                           for r in still_failed]
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {
                    ex.submit(_call_seedream, t["prompt"], t["output_path"], t["slug"]): t
                    for t in retry_tasks
                }
                for f in as_completed(futures):
                    rr = f.result()
                    for idx, r in enumerate(results):
                        if r["slug"] == rr["slug"]:
                            results[idx] = rr
                            break

    dt = time.time() - t0
    ok = sum(1 for r in results if r.get("ok"))
    print(f"\n=== 完成 {ok}/{count} 张,总耗时 {dt:.0f}s ===", flush=True)

    # partial failure → 失败位置补 placeholder(确保 image_paths 长度 = count)
    sorted_results = sorted(results, key=lambda x: x.get("slug", ""))
    image_paths: list[Path] = []
    failed_indices: list[int] = []
    for idx, r in enumerate(sorted_results, start=1):
        if r.get("ok"):
            image_paths.append(Path(r["path"]))
        else:
            failed_indices.append(idx)

    # 失败位置统一用 _copy_placeholder_to_output 补(Musk 删除清单 2:统一一个实现路径)
    if failed_indices:
        for idx in failed_indices:
            dst = OUT_DIR / f"{slug}-{idx:02d}-placeholder.png"
            try:
                shutil.copy2(PLACEHOLDER_SRC, dst)
                image_paths.insert(idx - 1, dst)
                print(f"  [{slug}-{idx:02d}] partial fail → placeholder", flush=True)
            except Exception as e:
                # 极端兜底:即使 copy 失败也指向源文件本身,保证 image_paths 非空
                print(f"  [{slug}-{idx:02d}] placeholder copy fail: {e}, "
                      f"using src", flush=True)
                image_paths.insert(idx - 1, PLACEHOLDER_SRC)
        decision["fallback_reason"] = decision.get(
            "fallback_reason", f"partial_fail_{len(failed_indices)}/{count}"
        )
        print(f"   partial placeholder fill: {len(failed_indices)}/{count}", flush=True)

    # invariant:image_paths 永远不为空(出口保证)
    if not image_paths:
        print(f"[fallback] reason=invariant_violation_emergency slug={slug}", flush=True)
        decision["fallback_reason"] = "invariant_violation_emergency"
        decision["image_at_h2_indices"] = [0]
        image_paths = _copy_placeholder_to_output(slug, count=1)

    return image_paths


# ============================================================
# Step 4: 写 metadata 到 frontmatter(数据飞轮被动观察)
# ============================================================

def write_metadata(
    draft_path: Path,
    decision: dict,
    image_paths: list[Path],
) -> None:
    """把配图决策结果写入 draft frontmatter(数据飞轮被动观察 + audit trail)。

    新增字段:
      illustrate_anchor: <style_anchor>
      illustrate_count: <count>
      illustrate_should: <bool>
      fallback_reason: <string>  (Round 25 audit:placeholder 触发原因,非 placeholder 则不写)
      image_at_h2_indices: [...]
      images:
        - path: ...
          alt: ...
          h2: ...

    注:这里只在 frontmatter 末尾追加(yaml block),不覆盖原有字段。
    Round 25 invariant:image_paths 永远非空(B2 fail-fast)
    """
    # Bug B2 修复(Newton):invariant 入口检查,Round 25 严禁接收空 image_paths
    assert image_paths, (
        "Round 25 invariant 违反:write_metadata 接收到空 image_paths。"
        "generate_from_decision 应在所有路径上保证 image_paths 非空,"
        "如出现请检查调用方是否绕过了 generate_from_decision"
    )

    text = draft_path.read_text(encoding="utf-8")
    if not text.lstrip().startswith("---"):
        # 没 frontmatter,跳过(理论上不应该发生)
        return

    parts = text.split("---", 2)
    if len(parts) < 3:
        return

    fm_lines = parts[1].strip().splitlines()
    body = parts[2]

    # 移除已有的 illustrate_* + fallback_reason 字段(覆盖式重写)
    fm_lines = [
        ln for ln in fm_lines
        if not ln.startswith("illustrate_")
           and not ln.startswith("fallback_reason")
           and not ln.startswith("images:")
           and not (ln.startswith("  -") or ln.startswith("    ")
                    and any(prev.startswith("images:") for prev in fm_lines[:fm_lines.index(ln)]))
    ]

    # 重建 frontmatter
    new_fm_lines = list(fm_lines)
    new_fm_lines.append(f"illustrate_anchor: {decision.get('style_anchor') or 'null'}")
    new_fm_lines.append(f"illustrate_count: {len(image_paths)}")
    new_fm_lines.append(f"illustrate_should: {str(decision.get('should_illustrate', False)).lower()}")
    # Bug B4 修复(Newton):placeholder 触发时写 fallback_reason 到 frontmatter(audit trail)
    # 字段重命名:_zero_reason → fallback_reason(去 Round 25 版本号前缀)
    fallback_reason = decision.get("fallback_reason")
    if fallback_reason:
        new_fm_lines.append(f'fallback_reason: "{fallback_reason}"')
    # Bug 2 闭环 2026-05-24:写 image_at_h2_indices 到 frontmatter,
    # post_fengyun_publish 读取后透传给 layout_rules
    derived_indices = derive_image_at_h2_indices(decision)
    if derived_indices is not None:
        # YAML inline list 格式:[1, 3, 5]
        indices_str = "[" + ", ".join(str(i) for i in derived_indices) + "]"
        new_fm_lines.append(f"image_at_h2_indices: {indices_str}")

    if image_paths:
        new_fm_lines.append("images:")
        positions = decision.get("positions", [])
        alts = decision.get("alts", [])
        for i, img_path in enumerate(image_paths):
            # 用相对路径(相对 ai-wechat-pipeline/)
            try:
                rel_path = img_path.relative_to(ROOT)
            except ValueError:
                rel_path = img_path
            alt = alts[i] if i < len(alts) else ""
            h2 = positions[i].get("h2_title", "") if i < len(positions) else ""
            new_fm_lines.append(f"  - path: {rel_path}")
            new_fm_lines.append(f"    alt: \"{alt}\"")
            new_fm_lines.append(f"    h2: \"{h2}\"")

    new_text = "---\n" + "\n".join(new_fm_lines) + "\n---" + body
    draft_path.write_text(new_text, encoding="utf-8")
    print(f"   metadata 写入 frontmatter:{len(image_paths)} 张图 + anchor='{decision.get('style_anchor')}'",
          flush=True)


# ============================================================
# CLI 入口(测试用,production 走 fengyun-publish 主线程)
# ============================================================

def cli_dry_run(draft_path: Path):
    """干跑:只跑 read_article_meta + pick_candidates,不调 LLM 不出图。"""
    meta = read_article_meta(draft_path)
    print(f"=== Article meta ===")
    print(f"  slug: {meta['slug']}")
    print(f"  title: {meta['title']}")
    print(f"  word_count: {meta['word_count']}")
    print(f"  h2_count: {meta['h2_count']}")
    print(f"  h2_titles: {meta['h2_titles']}")

    candidates = pick_candidates(meta["body"])
    print(f"\n=== 候选位置({len(candidates)} 处)===")
    for c in candidates:
        print(f"  H2[{c.h2_idx}] '{c.h2_title}' / 段 {c.position_idx} / {c.word_count} 字")
        print(f"    preview: {c.paragraph_preview[:80]}...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python illustrate_decider.py <draft_path.md> [--dry-run]")
        sys.exit(1)
    draft = Path(sys.argv[1])
    if not draft.exists():
        print(f"ERROR: {draft} 不存在")
        sys.exit(1)
    if "--dry-run" in sys.argv:
        cli_dry_run(draft)
    else:
        # 默认就是 dry-run(production 走主线程)
        cli_dry_run(draft)
