"""
test_round26_fixes.py — Round 26 三件修复的单元测试

覆盖:
  A. critic_vote.vote_all_rounds:human_gate 不能单轮自动放行(B reject 案例)
  B. fix_punctuation:6 个用例(配对引号 / 中文间标点 / 代码块跳过 / frontmatter 跳过)
  C. opening_signal._score_reframe:新增 4 个 reframe 模板命中

Round 26 SPEC: docs/SPEC_ROUND26_HUMAN_GATE_FIX.md
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import critic_vote
import opening_signal
import fix_punctuation


# ============================================================
# A. critic_vote — human_gate 修复
# ============================================================

def test_a1_b_reject_single_round_goes_revise():
    """A=74.2 + B=no-ship + C=ship 单轮 → 应该走 revise(不能 ship)"""
    rounds = [{
        "round": 1,
        "draft_path": "draft_v1.md",
        "a_score": 74.2,
        "b_verdict": "no-ship",
        "c_verdict": "ship",
        "lint_json_path": None,
    }]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "revise", \
        f"B reject 单轮必须 revise,实际 {r['decision']}: {r['reason']}"
    assert "round 2" in r["next_step"], f"应该提示进 round 2,实际 {r['next_step']}"
    print("  ✅ A1: B reject single round → revise")


def test_a2_b_reject_three_rounds_goes_auto_exit():
    """3 轮仍 human_gate → auto_exit(末轮 A=74.2 ≥ 65 → auto_partial_pass = ship)"""
    rounds = [
        {"round": 1, "a_score": 70.0, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d1.md", "lint_json_path": None},
        {"round": 2, "a_score": 72.0, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d2.md", "lint_json_path": None},
        {"round": 3, "a_score": 74.2, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d3.md", "lint_json_path": None},
    ]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship", \
        f"3 轮 + A=74.2 应 auto_partial_pass → ship,实际 {r['decision']}"
    assert r.get("auto_partial_pass") is True
    print("  ✅ A2: B reject 3 rounds + A≥65 → auto_partial_pass ship")


def test_a3_b_reject_three_rounds_low_a_auto_abort():
    """3 轮仍 human_gate + 末轮 A=60.5 < 65 → auto_abort"""
    rounds = [
        {"round": 1, "a_score": 62.0, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d1.md", "lint_json_path": None},
        {"round": 2, "a_score": 61.0, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d2.md", "lint_json_path": None},
        {"round": 3, "a_score": 60.5, "b_verdict": "no-ship", "c_verdict": "ship",
         "draft_path": "d3.md", "lint_json_path": None},
    ]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "abort", \
        f"3 轮 + A<65 应 auto_abort,实际 {r['decision']}"
    assert r.get("auto_abort") is True
    print("  ✅ A3: B reject 3 rounds + A<65 → auto_abort")


def test_a4_a_missing_abort():
    """A 缺 → abort"""
    rounds = [{"round": 1, "a_score": None, "b_verdict": "ship", "c_verdict": "ship",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "abort"
    print("  ✅ A4: A 缺 → abort")


def test_a5_a_below_threshold_revise():
    """A=55 < 60 → revise"""
    rounds = [{"round": 1, "a_score": 55.0, "b_verdict": "ship", "c_verdict": "ship",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "revise"
    print("  ✅ A5: A<60 → revise")


def test_a6_c_reject_revise():
    """C reject 是硬否决 → revise(B ship 也覆盖不了)"""
    rounds = [{"round": 1, "a_score": 80.0, "b_verdict": "ship", "c_verdict": "no-sign",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "revise"
    print("  ✅ A6: C reject → revise(硬否决)")


def test_a7_all_pass_ship():
    """A 过 + B ship + C ship → ship"""
    rounds = [{"round": 1, "a_score": 75.0, "b_verdict": "ship", "c_verdict": "sign",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship"
    print("  ✅ A7: A+B+C 全过 → ship")


def test_a8_b_skip_c_ship_ship():
    """B skip + C ship + A 过 → ship"""
    rounds = [{"round": 1, "a_score": 75.0, "b_verdict": "skip", "c_verdict": "sign",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship"
    print("  ✅ A8: B skip + C ship → ship")


def test_a9_bc_both_skip_ship():
    """B/C 都 skip + A 过 → System A 单轨 ship"""
    rounds = [{"round": 1, "a_score": 75.0, "b_verdict": "skip", "c_verdict": "skip",
               "draft_path": "d1.md", "lint_json_path": None}]
    r = critic_vote.vote_all_rounds(rounds)
    assert r["decision"] == "ship"
    print("  ✅ A9: B/C 都 skip → System A 单轨 ship")


# ============================================================
# B. fix_punctuation
# ============================================================

def test_b1_paired_double_quotes():
    text, n = fix_punctuation.fix_punctuation_text('他说"你好"然后离开了')
    assert text == '他说“你好”然后离开了', f"got: {text}"
    assert n == 2, f"got: {n}"
    print("  ✅ B1: 配对双引号 → 中文 “”")


def test_b2_chinese_comma_period():
    text, n = fix_punctuation.fix_punctuation_text('我说,你听.这是简单的.')
    assert text == '我说，你听。这是简单的。', f"got: {text!r}"
    assert n == 3, f"got: {n}"
    print("  ✅ B2: 中文间 ,. → ，。")


def test_b3_chinese_question_exclaim():
    text, n = fix_punctuation.fix_punctuation_text('真的?不可能!')
    assert text == '真的？不可能！', f"got: {text!r}"
    assert n == 2, f"got: {n}"
    print("  ✅ B3: 中文间 ?! → ?!")


def test_b4_numbers_not_touched():
    """1.5 / 3.14 不应被改"""
    text, n = fix_punctuation.fix_punctuation_text('价格 1.5 万元,数据 3.14')
    # 中文+逗号+空格+数字应该改逗号为, 但1.5和3.14不动
    assert "1.5" in text, f"1.5 被改: {text}"
    assert "3.14" in text, f"3.14 被改: {text}"
    print("  ✅ B4: 1.5 / 3.14 不动")


def test_b5_english_not_touched():
    """English, only. 不应被改"""
    text, _ = fix_punctuation.fix_punctuation_text('English, only.')
    assert text == 'English, only.', f"英文被改: {text}"
    print("  ✅ B5: 纯英文标点不动")


def test_b6_fenced_code_skipped():
    """fenced 代码块不应被改(全文件级测试)"""
    src = '''---
title: test
---

中文正文,带半角逗号.

```python
x = "hello"  # 这里的引号不动
y = 1,2,3    # 逗号不动
```

继续正文,再来一个.'''
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(src)
        path = Path(f.name)
    try:
        total, skipped = fix_punctuation.fix_punctuation_file(path)
        result = path.read_text(encoding="utf-8")
        assert 'x = "hello"' in result, f"代码块引号被改: {result}"
        assert 'y = 1,2,3' in result, f"代码块逗号被改: {result}"
        assert '中文正文，带半角逗号。' in result, f"正文未改: {result!r}"
        assert '继续正文，再来一个。' in result, f"正文未改: {result!r}"
        assert skipped >= 1, f"应跳过至少 1 个代码块,实际 {skipped}"
        print(f"  ✅ B6: fenced code 跳过(total={total}, skipped={skipped})")
    finally:
        path.unlink()


# ============================================================
# C. opening_signal._score_reframe — 新增 reframe 模板
# ============================================================

def test_c1_existing_reframe_still_works():
    """原有 \"以为...才发现\" 仍能命中"""
    score = opening_signal._score_reframe("我以为这是 demo,才发现是真的")
    assert score >= 5, f"原模式失效,score={score}"
    print(f"  ✅ C1: \"以为...才发现\" → {score}")


def test_c2_new_yiwei_zhidao():
    """\"以为...直到\" 应命中(本次 E2E R3 漏判模式)"""
    score = opening_signal._score_reframe("你以为写好一个 agent skill 就完事了,直到上周")
    assert score >= 5, f"\"以为...直到\" 未命中,score={score}"
    print(f"  ✅ C2: \"以为...直到\" → {score}")


def test_c3_new_yiwei_meixiangdao():
    """\"以为...没想到\" 应命中"""
    score = opening_signal._score_reframe("我以为只是普通迭代,没想到是全新架构")
    assert score >= 5, f"\"以为...没想到\" 未命中,score={score}"
    print(f"  ✅ C3: \"以为...没想到\" → {score}")


def test_c4_new_yiwei_jieguo():
    """\"以为...结果\" 应命中"""
    score = opening_signal._score_reframe("以为五分钟搞定,结果搞了一晚上")
    assert score >= 5, f"\"以为...结果\" 未命中,score={score}"
    print(f"  ✅ C4: \"以为...结果\" → {score}")


def test_c5_new_yiwei_houlai():
    """\"以为...后来\" 应命中"""
    score = opening_signal._score_reframe("我以为这条路走不通,后来才发现走得通")
    assert score >= 5, f"\"以为...后来\" 未命中,score={score}"
    print(f"  ✅ C5: \"以为...后来\" → {score}")


def test_c6_combo_hits_higher_score():
    """多个 reframe 命中 → 分更高(测评分曲线)"""
    score_1 = opening_signal._score_reframe("我以为这是 A,直到我发现 B")
    score_2 = opening_signal._score_reframe(
        "我以为这是 A,直到我发现 B。但是真相比这更复杂"
    )
    assert score_2 > score_1, f"多命中应更高:1命中={score_1}, 2命中={score_2}"
    print(f"  ✅ C6: 单命中={score_1}, 双命中={score_2}(曲线正确)")


def test_c7_no_reframe_zero():
    """无任何 reframe → 0 分"""
    score = opening_signal._score_reframe("这是一个普通的开头,没有反差")
    # 注意:可能匹配「这」「是」之类,但 REFRAME_PATTERNS 里没有这类
    # 唯一可能:无命中
    assert score == 0, f"无 reframe 应 0 分,实际 {score}"
    print(f"  ✅ C7: 无 reframe → 0 分")


# ============================================================
# 主入口
# ============================================================

def run_all():
    tests = [
        ("A. critic_vote human_gate 修复", [
            test_a1_b_reject_single_round_goes_revise,
            test_a2_b_reject_three_rounds_goes_auto_exit,
            test_a3_b_reject_three_rounds_low_a_auto_abort,
            test_a4_a_missing_abort,
            test_a5_a_below_threshold_revise,
            test_a6_c_reject_revise,
            test_a7_all_pass_ship,
            test_a8_b_skip_c_ship_ship,
            test_a9_bc_both_skip_ship,
        ]),
        ("B. fix_punctuation 重建", [
            test_b1_paired_double_quotes,
            test_b2_chinese_comma_period,
            test_b3_chinese_question_exclaim,
            test_b4_numbers_not_touched,
            test_b5_english_not_touched,
            test_b6_fenced_code_skipped,
        ]),
        ("C. opening_signal._score_reframe 词典扩充", [
            test_c1_existing_reframe_still_works,
            test_c2_new_yiwei_zhidao,
            test_c3_new_yiwei_meixiangdao,
            test_c4_new_yiwei_jieguo,
            test_c5_new_yiwei_houlai,
            test_c6_combo_hits_higher_score,
            test_c7_no_reframe_zero,
        ]),
    ]

    passed = 0
    failed = 0
    fail_msgs: list[str] = []

    for group_name, group_tests in tests:
        print(f"\n=== {group_name} ===")
        for t in group_tests:
            try:
                t()
                passed += 1
            except AssertionError as e:
                failed += 1
                msg = f"  ❌ {t.__name__}: {e}"
                print(msg)
                fail_msgs.append(msg)
            except Exception as e:
                failed += 1
                msg = f"  💥 {t.__name__} 异常: {type(e).__name__}: {e}"
                print(msg)
                fail_msgs.append(msg)

    print(f"\n{'='*60}")
    print(f"Round 26 fixes test: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    if failed:
        print("\n失败汇总:")
        for m in fail_msgs:
            print(m)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
