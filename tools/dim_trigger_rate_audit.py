"""
dim_trigger_rate_audit.py — 18 dim trigger rate audit (2026-05-26)

对 3 个 harness (opening / ending / title) 全部 18 个评分维度,
跑历史 corpus + ship draft 静态扫描,产出每维:
  - 阈值
  - 命中率 (达阈值的比例)
  - 触发率 (< 阈值导致 redo 的比例)
  - verdict (留 / 砍 / 调阈值)

数据源:
  - corpus/.raw/kazik/*.raw.md   (175 篇 卡兹克对标博主)
  - corpus/.raw/baoyu/*.raw.md   (52 篇)
  - corpus/.raw/saiboshanxin/*.raw.md (50 篇)
  - output/drafts/*.md           (~ 30 风云 ship/trial drafts)
"""
from __future__ import annotations
import os
import sys
import re
import glob
import json
from collections import defaultdict, Counter

ROOT = r"D:\Dev\ai-wechat-pipeline"
sys.path.insert(0, ROOT)

from tools.opening_signal import score_opening_signal, DIM_PASS_THRESHOLD as OPEN_TH
from tools.ending_signal import score_ending_signal, DIM_PASS_THRESHOLD as END_TH
from tools.title_signal import score_title


def strip_frontmatter(text: str) -> tuple[str, dict]:
    """Strip YAML frontmatter, return (body, fm_dict)."""
    fm = {}
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end > 0:
            fm_text = text[4:end]
            for line in fm_text.split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    fm[k.strip()] = v.strip().strip('"\'')
            text = text[end + 5 :]
    return text, fm


def extract_title_from_md(text: str, fm: dict) -> str:
    """Get title from frontmatter or first H1."""
    if fm.get("title"):
        return fm["title"]
    m = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return m.group(1).strip() if m else ""


def normalize_setext_headers(text: str) -> str:
    """把 Setext 风格 `XXXX\n=====` / `\n-----` 转成 `# XXXX` / `## XXXX`."""
    # Setext H1: 标题行 + 至少 3 个 =
    text = re.sub(r"^([^\n]+)\n=+\n", r"# \1\n\n", text, flags=re.MULTILINE)
    # Setext H2: 标题行 + 至少 3 个 -
    text = re.sub(r"^([^\n]+)\n-{3,}\n", r"## \1\n\n", text, flags=re.MULTILINE)
    return text


def strip_corpus_chrome(text: str) -> str:
    """去掉 we-mp-rss 抓的微信 HTML/CSS 噪声 + metadata 行."""
    # 去掉首段 CSS 巨长行(如果第一行 > 500 字且含 { 或 :)
    lines = text.split("\n")
    cleaned = []
    skip_until_text = False
    for line in lines:
        # 跳过 CSS 嵌入行
        if len(line) > 500 and ("{" in line or "color:" in line):
            continue
        # 跳过 metadata 行 "原创 XXX YYY 2026-..."
        if re.match(r"^原创\s+\S+", line.strip()):
            continue
        # 跳过 "原文地址" 行
        if line.strip().startswith("> 原文地址:") or line.strip().startswith("原文地址:"):
            continue
        # 跳过单纯的 Setext 下划线
        if re.match(r"^=+$|^-{3,}$", line.strip()):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def extract_opening(text: str, max_chars: int = 400) -> str:
    """文章开头(到 H2 之前 / 前 400 字).

    对 raw corpus(没 H2)用前 400 字模拟 opening — 跟 ship draft 的 intro 长度对齐.
    """
    # 先去 chrome
    text = strip_corpus_chrome(text)
    text = text.lstrip()
    m = re.search(r"\n##\s", text)
    if m and m.start() <= 1200:  # H2 在前 1200 字内才用,否则太远
        return text[: m.start()].strip()
    # 否则取前 400 字(对应风云典型 intro 长度)
    return text[:max_chars].strip()


def load_articles() -> list[dict]:
    """加载所有 corpus + ship drafts."""
    articles = []
    # corpus 3 个作者
    for author in ["kazik", "baoyu", "saiboshanxin"]:
        for fp in glob.glob(os.path.join(ROOT, "corpus", ".raw", author, "*.raw.md")):
            try:
                with open(fp, encoding="utf-8") as f:
                    raw = f.read()
            except Exception:
                continue
            body, fm = strip_frontmatter(raw)
            title = extract_title_from_md(body, fm) or os.path.basename(fp).replace(
                ".raw.md", ""
            ).replace("_", " ")
            articles.append({
                "src": f"corpus/{author}",
                "path": fp,
                "title": title,
                "body": body,
            })
    # ship drafts
    for fp in glob.glob(os.path.join(ROOT, "output", "drafts", "*.md")):
        try:
            with open(fp, encoding="utf-8") as f:
                raw = f.read()
        except Exception:
            continue
        body, fm = strip_frontmatter(raw)
        title = extract_title_from_md(body, fm) or os.path.basename(fp).replace(
            ".md", ""
        )
        articles.append({
            "src": "draft/fengyun",
            "path": fp,
            "title": title,
            "body": body,
        })
    return articles


def audit_opening(articles: list[dict]) -> dict:
    """跑所有 article 的 opening 评分,统计 5 维 + 物理约束的命中率."""
    results = {
        "first_para_chars": [],
        "true_first_para_chars": [],
        "first_person_density": [],
        "concreteness": [],
        "reframe": [],
        "emotion_anchor": [],
        "info_density": [],
        "formula_freshness": [],
        "formula_hit_buckets": [],
    }
    phys_pass = 0
    samples_with_h2 = 0
    n = 0
    n_too_short = 0
    for a in articles:
        opening = extract_opening(a["body"])
        # 过短(< 80 字)视为没有正常 intro
        if len(opening) < 80:
            n_too_short += 1
            continue
        r = score_opening_signal(opening)
        n += 1
        if r["physical_pass"]:
            phys_pass += 1
        # 真实「第一段」字数 — 用 \n\n 切第一段
        first_para = re.split(r"\n\s*\n", opening, maxsplit=1)[0]
        true_chars = len(re.sub(r"\s+", "", first_para))
        results["true_first_para_chars"].append(true_chars)
        results["first_para_chars"].append(r["first_para_chars"])
        results["first_person_density"].append(r["first_person_density"])
        results["concreteness"].append(r["concreteness"])
        results["reframe"].append(r["reframe"])
        results["emotion_anchor"].append(r["emotion_anchor"])
        results["info_density"].append(r["info_density"])
        results["formula_freshness"].append(r["formula_freshness"])
        results["formula_hit_buckets"].append(r["formula_hit_buckets"])

    def stats(arr):
        if not arr:
            return None
        s = sorted(arr)
        n_ = len(s)
        return {
            "n": n_,
            "min": s[0],
            "p25": s[n_ // 4],
            "median": s[n_ // 2],
            "p75": s[(3 * n_) // 4],
            "max": s[-1],
            "mean": round(sum(s) / n_, 2),
        }

    # 命中率 = 该维度 ≥ 阈值的比例
    def hit_rate(arr, threshold, ge=True):
        if not arr:
            return 0.0
        hits = sum(1 for v in arr if (v >= threshold if ge else v < threshold))
        return round(100.0 * hits / len(arr), 1)

    out = {
        "total_articles": n,
        "skipped_no_h2": n_too_short,
        "physical_pass_rate": round(100.0 * phys_pass / n, 1) if n else 0,
        "dims": {},
    }
    out["dims"]["首段字数 ≥ 50 (intro 块)"] = {
        "threshold": 50,
        "stats": stats(results["first_para_chars"]),
        "hit_rate_pct": hit_rate(results["first_para_chars"], 50),
        "trigger_rate_pct": round(100 - hit_rate(results["first_para_chars"], 50), 1),
        "note": "score_opening_signal 把整个 intro 块算字数,raw corpus 取前 400 字 → 必过",
    }
    out["dims"]["真实第一段字数 ≥ 50"] = {
        "threshold": 50,
        "stats": stats(results["true_first_para_chars"]),
        "hit_rate_pct": hit_rate(results["true_first_para_chars"], 50),
        "trigger_rate_pct": round(
            100 - hit_rate(results["true_first_para_chars"], 50), 1
        ),
        "note": "用 \\n\\n 切的第一段,更接近 PHASE1 「首段」原意",
    }
    out["dims"]["第一人称密度 ≥ 5/千字"] = {
        "threshold": 5.0,
        "stats": stats(results["first_person_density"]),
        "hit_rate_pct": hit_rate(results["first_person_density"], 5.0),
        "trigger_rate_pct": round(100 - hit_rate(results["first_person_density"], 5.0), 1),
    }
    for dim_key, label in [
        ("concreteness", "具体性 ≥ 6"),
        ("reframe", "反差感 ≥ 6"),
        ("emotion_anchor", "情绪锚点 ≥ 6"),
        ("info_density", "信息密度 ≥ 6"),
        ("formula_freshness", "公式新鲜度 ≥ 6"),
    ]:
        out["dims"][label] = {
            "threshold": 6,
            "stats": stats(results[dim_key]),
            "hit_rate_pct": hit_rate(results[dim_key], 6),
            "trigger_rate_pct": round(100 - hit_rate(results[dim_key], 6), 1),
        }
    # formula 撞公式分布(2+ bucket = 撞)
    formulaic_hits = sum(1 for v in results["formula_hit_buckets"] if v >= 2)
    out["dims"]["公式新鲜度(原始 bucket 分布)"] = {
        "buckets_0": sum(1 for v in results["formula_hit_buckets"] if v == 0),
        "buckets_1": sum(1 for v in results["formula_hit_buckets"] if v == 1),
        "buckets_2": sum(1 for v in results["formula_hit_buckets"] if v == 2),
        "buckets_3": sum(1 for v in results["formula_hit_buckets"] if v == 3),
        "is_formulaic_rate_pct": round(100.0 * formulaic_hits / n, 1) if n else 0,
    }
    return out


def audit_ending(articles: list[dict]) -> dict:
    results = {
        "last_section_chars": [],
        "aphorism": [],
        "summary": [],
        "imperative": [],
    }
    phys_pass = 0
    n = 0
    skipped = 0
    n_no_h2_fallback = 0
    for a in articles:
        # 只跑足够长的文章
        body = strip_corpus_chrome(a["body"])
        if len(body) < 500:
            skipped += 1
            continue
        # 如果没 H2,用最后 800 字会让所有文章都拿 ~ 800 字 — 注明
        has_h2 = bool(re.search(r"^##\s", body, flags=re.MULTILINE))
        if not has_h2:
            n_no_h2_fallback += 1
        r = score_ending_signal(body)
        n += 1
        if r["physical_pass"]:
            phys_pass += 1
        results["last_section_chars"].append(r["last_section_chars"])
        results["aphorism"].append(r["aphorism"])
        results["summary"].append(r["summary"])
        results["imperative"].append(r["imperative"])

    def stats(arr):
        if not arr:
            return None
        s = sorted(arr)
        n_ = len(s)
        return {
            "n": n_,
            "min": s[0],
            "p25": s[n_ // 4],
            "median": s[n_ // 2],
            "p75": s[(3 * n_) // 4],
            "max": s[-1],
            "mean": round(sum(s) / n_, 2),
        }

    def hit_rate(arr, threshold):
        if not arr:
            return 0.0
        return round(100.0 * sum(1 for v in arr if v >= threshold) / len(arr), 1)

    out = {
        "total_articles": n,
        "skipped_too_short": skipped,
        "fallback_no_h2": n_no_h2_fallback,
        "note": "fallback_no_h2 = 没 ## 的文章用末尾 800 字代替「最后 H2 之后」,这些样本的末段字数恒为 ≤ 800",
    }
    out["physical_pass_rate"] = round(100.0 * phys_pass / n, 1) if n else 0
    out["dims"] = {}
    out["dims"]["末段字数 ≥ 150"] = {
        "threshold": 150,
        "stats": stats(results["last_section_chars"]),
        "hit_rate_pct": hit_rate(results["last_section_chars"], 150),
        "trigger_rate_pct": round(100 - hit_rate(results["last_section_chars"], 150), 1),
    }
    for dim_key, label in [
        ("aphorism", "金句密度 ≥ 6"),
        ("summary", "摘要密度 ≥ 6"),
        ("imperative", "召唤密度 ≥ 6"),
    ]:
        out["dims"][label] = {
            "threshold": 6,
            "stats": stats(results[dim_key]),
            "hit_rate_pct": hit_rate(results[dim_key], 6),
            "trigger_rate_pct": round(100 - hit_rate(results[dim_key], 6), 1),
        }
    return out


def audit_title(articles: list[dict]) -> dict:
    """对所有 corpus 标题跑 10 维评分."""
    n = 0
    char_counts = []
    digit_counts = []
    english_chars = []
    hook_hits = Counter()
    hook_total = 0
    white_brand_hits = 0
    black_brand_hits = 0
    fatal_combo_hits = 0
    score_totals = []
    pass_count = 0
    traits_dist = defaultdict(int)
    traits_count_dist = []

    for a in articles:
        if not a["title"]:
            continue
        # body chars for tb_ratio
        body_chars = len(a["body"])
        r = score_title(a["title"], topic_keywords=None, body_chars=body_chars or 5000)
        n += 1
        char_counts.append(r["char_count"])
        digit_counts.append(r["digit_count"])
        english_chars.append(r["english_chars"])
        if r["hook_type"]:
            hook_hits[r["hook_type"]] += 1
            hook_total += 1
        if r["brand_white_hit"]:
            white_brand_hits += 1
        if r["brand_black_hit"]:
            black_brand_hits += 1
        if r["fatal_combo_risk"]:
            fatal_combo_hits += 1
        score_totals.append(r["score_total"])
        if r["verdict"] == "pass":
            pass_count += 1
        for trait, hit in r["traits_hit"].items():
            if hit:
                traits_dist[trait] += 1
        traits_count_dist.append(r["traits_hit_count"])

    def stats(arr):
        if not arr:
            return None
        s = sorted(arr)
        n_ = len(s)
        return {
            "n": n_,
            "min": s[0],
            "p25": s[n_ // 4],
            "median": s[n_ // 2],
            "p75": s[(3 * n_) // 4],
            "max": s[-1],
            "mean": round(sum(s) / n_, 2),
        }

    in_range_chars = sum(1 for c in char_counts if 20 <= c <= 40)
    out = {
        "total_articles": n,
        "verdict_pass_rate_pct": round(100.0 * pass_count / n, 1) if n else 0,
        "dims": {},
    }
    out["dims"]["字数 ∈ [20,40]"] = {
        "stats": stats(char_counts),
        "hit_rate_pct": round(100.0 * in_range_chars / n, 1) if n else 0,
        "trigger_rate_pct": round(100 - 100.0 * in_range_chars / n, 1) if n else 0,
    }
    out["dims"]["数字组 ≤ 1"] = {
        "stats": stats(digit_counts),
        "hit_rate_pct": round(100.0 * sum(1 for d in digit_counts if d <= 1) / n, 1)
        if n
        else 0,
        "trigger_rate_pct": round(100.0 * sum(1 for d in digit_counts if d > 1) / n, 1)
        if n
        else 0,
    }
    out["dims"]["命中 7 钩子任一"] = {
        "hit_rate_pct": round(100.0 * hook_total / n, 1) if n else 0,
        "trigger_rate_pct": round(100.0 * (n - hook_total) / n, 1) if n else 0,
        "hook_distribution": dict(hook_hits),
    }
    out["dims"]["品牌词白名单命中"] = {
        "hit_rate_pct": round(100.0 * white_brand_hits / n, 1) if n else 0,
        "comment": "白名单 = Anthropic/Claude/Skills/Claude Code/Sonnet/Opus/Haiku",
    }
    out["dims"]["品牌词黑名单不命中"] = {
        "hit_rate_black_pct": round(100.0 * black_brand_hits / n, 1) if n else 0,
        "trigger_rate_pct": round(100.0 * black_brand_hits / n, 1) if n else 0,
        "comment": "黑名单 = OpenAI/GPT-X/Veo/GLM/ChatGPT",
    }
    out["dims"]["致命组合 risk"] = {
        "hit_rate_pct": round(100.0 * fatal_combo_hits / n, 1) if n else 0,
        "trigger_rate_pct": round(100.0 * fatal_combo_hits / n, 1) if n else 0,
    }
    out["dims"]["4 共同特质 ≥ 2"] = {
        "stats": stats(traits_count_dist),
        "hit_rate_pct": round(
            100.0 * sum(1 for c in traits_count_dist if c >= 2) / n, 1
        )
        if n
        else 0,
        "trigger_rate_pct": round(
            100.0 * sum(1 for c in traits_count_dist if c < 2) / n, 1
        )
        if n
        else 0,
        "traits_distribution": dict(traits_dist),
    }
    out["dims"]["总分 ≥ 65"] = {
        "stats": stats(score_totals),
        "hit_rate_pct": round(100.0 * sum(1 for s in score_totals if s >= 65) / n, 1)
        if n
        else 0,
        "trigger_rate_pct": round(100.0 * sum(1 for s in score_totals if s < 65) / n, 1)
        if n
        else 0,
    }
    out["dims"]["英文字符 ≥ 8(致命组合分项)"] = {
        "stats": stats(english_chars),
        "hit_rate_pct": round(100.0 * sum(1 for e in english_chars if e >= 8) / n, 1)
        if n
        else 0,
    }

    # 按 corpus 拆 hook distribution
    out["hook_dist_by_corpus"] = {}
    for src in ["corpus/kazik", "corpus/baoyu", "corpus/saiboshanxin", "draft/fengyun"]:
        subset = [a for a in articles if a["src"] == src and a["title"]]
        if not subset:
            continue
        ch = Counter()
        h_total = 0
        for a in subset:
            r = score_title(a["title"], topic_keywords=None, body_chars=len(a["body"]))
            if r["hook_type"]:
                ch[r["hook_type"]] += 1
                h_total += 1
        out["hook_dist_by_corpus"][src] = {
            "n": len(subset),
            "hook_total": h_total,
            "hook_hit_rate_pct": round(100.0 * h_total / len(subset), 1),
            "dist": dict(ch),
        }

    return out


def main():
    articles = load_articles()
    by_src = Counter(a["src"] for a in articles)
    print(f"加载 {len(articles)} 篇 ({dict(by_src)})")

    opening_out = audit_opening(articles)
    ending_out = audit_ending(articles)
    title_out = audit_title(articles)

    # 风云 ship draft 单独跑(更接近真实 redo 触发场景)
    fengyun_only = [a for a in articles if a["src"] == "draft/fengyun"]
    fengyun_opening = audit_opening(fengyun_only)
    fengyun_ending = audit_ending(fengyun_only)
    fengyun_title = audit_title(fengyun_only)

    full = {
        "total_articles_loaded": len(articles),
        "by_source": dict(by_src),
        "opening_audit_all": opening_out,
        "ending_audit_all": ending_out,
        "title_audit_all": title_out,
        "fengyun_only_opening": fengyun_opening,
        "fengyun_only_ending": fengyun_ending,
        "fengyun_only_title": fengyun_title,
    }
    out_path = os.path.join(ROOT, "reports", "dim_trigger_rate_audit_20260526.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False, indent=2)
    print(f"\nJSON 已写 -> {out_path}")
    print("\n=== OPENING ===")
    print(json.dumps(opening_out, ensure_ascii=False, indent=2))
    print("\n=== ENDING ===")
    print(json.dumps(ending_out, ensure_ascii=False, indent=2))
    print("\n=== TITLE ===")
    print(json.dumps(title_out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
