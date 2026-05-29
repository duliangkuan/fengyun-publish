"""
test_iti_explore.py — ITI I-2 深搜单测

重点测 Round 27 新增的 fetch_trendradar_topic():
- 主题命中过滤
- 空 entities 降级
- 完全无匹配
"""
from __future__ import annotations
import sys
from pathlib import Path

# 让 import 找到 tools/
ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from iti_explore import fetch_trendradar_topic  # noqa: E402


# ============================================================
# fetch_trendradar_topic
# ============================================================

def test_fetch_trendradar_topic_with_entities():
    """主题命中过滤 — 用常见的 AI 实体词,应该至少匹配若干条."""
    items = fetch_trendradar_topic(
        ["Anthropic", "Claude", "AI", "OpenAI", "Google"],
        top_k=20,
    )
    # 当 TrendRadar 数据活的时候,这些 AI 大词应该至少命中 1 条
    # 如果 TrendRadar 文件过期或不存在,返回 [] 也是合法行为(降级)
    assert isinstance(items, list)
    if items:
        # 命中条目必须有 title/url 字段
        for it in items:
            assert "title" in it
            assert "url" in it
            assert it.get("_origin") == "trendradar"


def test_fetch_trendradar_topic_empty_entities():
    """传 [] 应该走降级返回前 top_k 条."""
    items = fetch_trendradar_topic([], top_k=5)
    assert isinstance(items, list)
    # 文件活的话至少有几条;过期则 []
    assert len(items) <= 5


def test_fetch_trendradar_topic_no_match():
    """传不可能命中的随机词,应该返回 []."""
    items = fetch_trendradar_topic(
        ["zzzzzz_no_such_entity_should_match_xyz_12345"],
        top_k=10,
    )
    assert items == []


def test_fetch_trendradar_topic_top_k_cap():
    """top_k 截断生效."""
    items = fetch_trendradar_topic(["AI", "模型"], top_k=3)
    assert isinstance(items, list)
    assert len(items) <= 3


def test_fetch_trendradar_topic_case_insensitive():
    """大小写不敏感 — 全小写 entity 应该匹配大小写混合的 title."""
    upper_items = fetch_trendradar_topic(["ANTHROPIC"], top_k=20)
    lower_items = fetch_trendradar_topic(["anthropic"], top_k=20)
    # 大小写不敏感,两次结果应该一致
    assert len(upper_items) == len(lower_items)


def test_fetch_trendradar_topic_filters_empty_entity_strings():
    """entities 里混入空字符串不应该影响过滤."""
    items = fetch_trendradar_topic(["AI", "", None], top_k=10)  # type: ignore
    assert isinstance(items, list)


# ============================================================
# explore_topic 接入(快速 smoke,trendradar 在 sources 列表里)
# ============================================================

def test_explore_topic_includes_trendradar_in_stats():
    """explore_topic 的 stats 里必须有 trendradar key."""
    from iti_explore import explore_topic
    result = explore_topic(
        slug="test-trendradar-smoke",
        title="测试 TrendRadar 接入",
        entities=["zzzz_impossible_entity_xyz"],  # 故意不命中,跑得快
        main_source_urls=None,
        verbose=False,
    )
    assert "stats" in result
    assert "trendradar" in result["stats"], (
        f"explore_topic.stats 必须含 trendradar key,实际: {list(result['stats'].keys())}"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
