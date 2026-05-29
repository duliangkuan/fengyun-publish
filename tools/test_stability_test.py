"""
test_stability_test.py — stability_test.py 单元测试

pytest tools/test_stability_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保 tools/ 在 sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from stability_test import (
    verdict_consistency,
    reasoning_avg_jaccard,
    grade,
)
from opening_dedup import tokenize, jaccard


# ─────────────────────────────────────────────────────────────
# Case 1: tokenize 一致性 — 同文本两次 tokenize 结果相同
# ─────────────────────────────────────────────────────────────

def test_tokenize_deterministic():
    text = "这篇文章的 AI 写作分析,让我看到了 LLM 的真实局限"
    result1 = tokenize(text)
    result2 = tokenize(text)
    assert result1 == result2, "tokenize 应是纯函数,同输入同输出"
    assert isinstance(result1, set), "tokenize 应返回 set"


def test_tokenize_returns_tokens():
    text = "AI research frontier model"
    tokens = tokenize(text)
    # 至少包含长度≥3 的英文词
    assert len(tokens) > 0


# ─────────────────────────────────────────────────────────────
# Case 2: jaccard 边界值
# ─────────────────────────────────────────────────────────────

def test_jaccard_identical():
    a = {"apple", "banana", "cherry"}
    assert jaccard(a, a) == 1.0, "完全相同集合 Jaccard=1.0"


def test_jaccard_disjoint():
    a = {"apple", "banana"}
    b = {"cherry", "durian"}
    assert jaccard(a, b) == 0.0, "完全不重叠 Jaccard=0.0"


def test_jaccard_empty():
    assert jaccard(set(), {"a"}) == 0.0, "空集 Jaccard=0.0"
    assert jaccard(set(), set()) == 0.0, "双空集 Jaccard=0.0"


def test_jaccard_partial():
    a = {"a", "b", "c"}
    b = {"b", "c", "d"}
    # intersection=2, union=4 → 0.5
    assert abs(jaccard(a, b) - 0.5) < 1e-9


# ─────────────────────────────────────────────────────────────
# Case 3: 一致率分档判定 (95/80 阈值)
# ─────────────────────────────────────────────────────────────

def test_verdict_consistency_all_same():
    verdicts = ["ship", "ship", "ship"]
    assert verdict_consistency(verdicts) == 1.0


def test_verdict_consistency_split():
    verdicts = ["ship", "ship", "不ship"]
    # majority=2/3 ≈ 0.667
    result = verdict_consistency(verdicts)
    assert abs(result - 2 / 3) < 1e-9


def test_verdict_consistency_empty_ignored():
    verdicts = ["ship", "", "ship"]
    # 空字符串不计 → filled=["ship","ship"] → 1.0
    assert verdict_consistency(verdicts) == 1.0


def test_grade_pass():
    assert grade(0.95) == "PASS"
    assert grade(1.0)  == "PASS"


def test_grade_warn():
    assert grade(0.80) == "WARN"
    assert grade(0.90) == "WARN"


def test_grade_fail():
    assert grade(0.79) == "FAIL"
    assert grade(0.0)  == "FAIL"


# ─────────────────────────────────────────────────────────────
# Case 4: reasoning_avg_jaccard 边界
# ─────────────────────────────────────────────────────────────

def test_reasoning_jaccard_identical():
    r = "这篇文章选题很好 AI 工具使用自然"
    score = reasoning_avg_jaccard([r, r, r])
    assert score == 1.0, "完全相同理由 Jaccard=1.0"


def test_reasoning_jaccard_empty_runs():
    # 少于 2 条有效数据 → 不扣分,返回 1.0
    score = reasoning_avg_jaccard(["", "", ""])
    assert score == 1.0


def test_reasoning_jaccard_range():
    r1 = "选题犀利 数据真实"
    r2 = "情感共鸣 传播潜力"
    score = reasoning_avg_jaccard([r1, r2, r1])
    assert 0.0 <= score <= 1.0, f"Jaccard 应在 [0,1],实际={score}"
