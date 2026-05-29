"""
critic_vote.py — 三轨 critic 投票决议工具(Musk × Jobs Round 2 共识版)

【门控树(2026-05-23 共识,废弃 A + 10×B + 10×C 数值公式)】
  A 缺                       → abort(工具链断)
  A 没过线                    → revise
  C reject                   → revise(C 硬否决,founder verdict 优先)
  C ship/skip + B ship       → pass
  C ship/skip + B reject     → human_gate(人工裁决)
  B skip + C skip            → pass(System A 单轨,A 过线即过)

【3 轮 revise 后】
  最后一轮仍判 revise → human_gate(系统停止,日志推荐 A 分最高版本)
  不建通知系统。不自动跑 Step 7/8。

【R18 分级处理】
  R18-P0(明确自指 AI 身份)→ aborted_r18(跳过所有兜底,强制人工)
  R18-P1(架构 / skill / 工具栈暴露)→ 不阻断,走 gate tree(让 writer 改)
  R18-P2(自动化流程暴露)→ 不阻断,但计入触发率统计(给 r18_dashboard.py)

【两种调用模式】
  单轮:--a-score / --b-verdict / --c-verdict   (向后兼容)
  多轮:--all-rounds <rounds.json>               (Round 2 共识)

规则参考 fengyun-publish SKILL.md Step 6 / 6.5.7 / 6.5.8 + Musk × Jobs Round 2 共同决策。
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class VoteResult:
    decision: str            # ship | revise | abort | human_gate
    reason: str
    next_step: str
    a_passed: bool | None
    b_passed: bool | None    # None 表示 skip / 缺席
    c_passed: bool | None
    a_score: float | None
    threshold_a: float
    degraded: dict


def _norm_binary(verdict: str | None, true_label: str) -> bool | None:
    """归一化 binary verdict 字符串"""
    if verdict is None:
        return None
    v = verdict.strip().lower()
    if v in ("", "skip", "none", "n/a", "na"):
        return None
    if v in ("yes", "y", "1", "true", "t", "pass", true_label.lower(), true_label):
        return True
    if v.startswith("no") or v in ("0", "false", "f", "fail"):
        return False
    if true_label.lower() in v:
        return True
    if "no" in v:
        return False
    return None


def gate_tree(a_score: float | None,
              b_verdict: str | None,
              c_verdict: str | None,
              threshold_a: float = 60.0) -> tuple[str, str]:
    """
    Musk × Jobs Round 2 共识门控树(替代废弃的数值公式)

    返回:(decision, reason)
      decision ∈ {'pass', 'revise', 'human_gate', 'abort'}
    """
    a_passed = (a_score is not None) and (a_score >= threshold_a)
    b_passed = _norm_binary(b_verdict, "ship")
    c_passed = _norm_binary(c_verdict, "sign")

    # A 缺 → abort(工具链断,人工修)
    if a_score is None:
        return ("abort", "Track A 无分数,工具链断,先修 sop_v2_1 工具")

    # A 没过线 → revise(底线)
    if not a_passed:
        return ("revise", f"A 没过线(底线):total={a_score:.1f} < {threshold_a}")

    # C reject = 硬否决(founder verdict 优先于 A 数字分 + B 外部 critic)
    if c_passed is False:
        return ("revise",
                f"C(founder) reject → 硬否决,founder verdict 优先,A={a_score:.1f}")

    # B ship + C ship/skip → 自动过
    if b_passed is True:
        c_str = "ship" if c_passed else "skip"
        return ("pass", f"A 过线 + B ship + C {c_str},A={a_score:.1f}")

    # B reject + C ship/skip → 人工裁决
    if b_passed is False:
        c_str = "ship" if c_passed else "skip"
        return ("human_gate",
                f"A 过线 + B reject + C {c_str} → 人工裁决,A={a_score:.1f}")

    # B skip + C ship → 不严格,A 过线就过
    if c_passed is True:
        return ("pass", f"A 过线 + C ship + B 缺席,A={a_score:.1f}")

    # B skip + C skip → System A 单轨
    return ("pass", f"A 单轨过线(B/C 都缺席),A={a_score:.1f}")


def vote(a_score, b_verdict, c_verdict, threshold_a=60.0) -> VoteResult:
    """单轮投票(向后兼容旧调用)"""
    a_passed = (a_score is not None) and (a_score >= threshold_a)
    b_passed = _norm_binary(b_verdict, "ship")
    c_passed = _norm_binary(c_verdict, "sign")

    degraded = {}
    if a_score is None:
        degraded["A"] = "score missing"
    if b_passed is None:
        degraded["B"] = "skip / skill missing"
    if c_passed is None:
        degraded["C"] = "skip / critic_mode missing"

    decision, reason = gate_tree(a_score, b_verdict, c_verdict, threshold_a)

    next_step_map = {
        "pass": "进 Step 7(封面)",
        "revise": "回 Step 6.5 改稿(看 score_draft 三维拆解,定向修)",
        "human_gate": "⛔ 系统停止,风云人工裁决:挑版本/改/弃稿",
        "abort": "跑 `python tools/score_draft.py <draft>` 看报错",
    }

    # 单轮模式:pass 统一叫 ship(兼容旧 caller)
    decision_external = "ship" if decision == "pass" else decision

    return VoteResult(
        decision=decision_external,
        reason=reason,
        next_step=next_step_map[decision],
        a_passed=a_passed if a_score is not None else None,
        b_passed=b_passed,
        c_passed=c_passed,
        a_score=a_score,
        threshold_a=threshold_a,
        degraded=degraded,
    )


# ===== R18 分级检测 =====

def check_r18_priority(lint_json_path: str | None) -> tuple[bool, list, list]:
    """
    读 lint JSON,返回 (has_p0, p1_hits, p2_hits)

    has_p0 = True 即触发 aborted_r18(阻断所有兜底)
    p1_hits / p2_hits 仅用于统计/报告,不阻断 gate tree
    """
    if not lint_json_path:
        return False, [], []
    p = Path(lint_json_path)
    if not p.exists():
        return False, [], []
    try:
        lint = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return False, [], []

    has_p0 = False
    p1_hits = []
    p2_hits = []
    for v in lint.get("violations", []):
        rid = v.get("rule_id", "")
        if rid.startswith("R18_P0"):
            has_p0 = True
        elif rid.startswith("R18_P1"):
            p1_hits.append({
                "rule_id": rid,
                "issue": v.get("issue", ""),
                "matches": v.get("matches", [])[:3],
            })
        elif rid.startswith("R18_P2"):
            p2_hits.append({
                "rule_id": rid,
                "issue": v.get("issue", ""),
                "matches": v.get("matches", [])[:3],
            })
    return has_p0, p1_hits, p2_hits


# ===== 多轮模式(Round 2 共识)=====

def _summarize_round(r: dict) -> dict:
    """单轮信息摘要(用于报告)"""
    return {
        "round": r["round"],
        "draft_path": r.get("draft_path"),
        "a_score": r.get("a_score"),
        "b_verdict": r.get("b_verdict"),
        "c_verdict": r.get("c_verdict"),
        "b_passed": _norm_binary(r.get("b_verdict"), "ship"),
        "c_passed": _norm_binary(r.get("c_verdict"), "sign"),
    }


def _auto_exit_result(round_info, r18_p1_warnings, r18_p2_warnings, reason,
                      threshold_partial: float = 65.0):
    """
    Round 24 自动出口(原 human_gate 已废除真人介入):
      - 3 轮 revise 未过 + A ≥ threshold_partial(默认 65)→ auto_partial_pass(ship)
      - 3 轮 revise 未过 + A <  threshold_partial      → auto_abort(终止 pipeline)

    取末轮 A 分作为决策依据(末轮通常是改稿基于反馈最精的版本)。
    """
    last = round_info[-1]
    last_a = last.get("a_score")

    # A 缺 → 无法自动判,降级 auto_abort
    if last_a is None:
        return {
            "decision": "abort",
            "auto_abort": True,
            "reason": reason + " | 末轮 A 缺,无法自动判 partial_pass 兜底",
            "next_step": "终止 pipeline,工具链断,先修 sop_v2_1 工具",
            "r18_p1_warnings": r18_p1_warnings,
            "r18_p2_warnings": r18_p2_warnings,
            "round_info": round_info,
        }

    if last_a >= threshold_partial:
        return {
            "decision": "ship",
            "auto_partial_pass": True,
            "reason": (f"auto_partial_pass(3 轮 revise 未过 + A={last_a:.1f}"
                       f" >= {threshold_partial}):{reason}"),
            "next_step": "进 Step 7(封面)— 自动 partial_pass 兜底通道",
            "chosen_version": last["round"],
            "chosen_draft_path": last.get("draft_path"),
            "r18_p1_warnings": r18_p1_warnings,
            "r18_p2_warnings": r18_p2_warnings,
            "round_info": round_info,
        }

    return {
        "decision": "abort",
        "auto_abort": True,
        "reason": (f"auto_abort(3 轮 revise 未过 + A={last_a:.1f}"
                   f" < {threshold_partial}):{reason}"),
        "next_step": "终止 pipeline — 自动 partial_pass 兜底不达 A 分阈值",
        "r18_p1_warnings": r18_p1_warnings,
        "r18_p2_warnings": r18_p2_warnings,
        "round_info": round_info,
    }


# 向后兼容别名 — 老调用方仍能 import _human_gate_result;新代码用 _auto_exit_result
_human_gate_result = _auto_exit_result


def vote_all_rounds(rounds: list[dict], threshold_a: float = 60.0) -> dict:
    """
    多轮决议(Round 24 自动出口版):
      1. 任一轮 lint R18-P0 → aborted_r18(跳过所有兜底)
      2. 最后一轮跑 gate tree:
           pass → ship
           revise + N < 3 → revise(继续改)
           revise + N >= 3 → 自动出口:A ≥ 65 → auto_partial_pass(ship)
                                            A <  65 → auto_abort
           human_gate(末轮 gate_tree 直接判)→ 同上自动出口
           abort → abort
    """
    if not rounds:
        return {
            "decision": "abort",
            "reason": "rounds 为空",
            "next_step": "至少给一轮数据",
            "round_info": [],
        }

    # 1. R18-P0 红线检查
    r18_p0_rounds = []
    r18_p1_warnings = []
    r18_p2_warnings = []
    for r in rounds:
        has_p0, p1, p2 = check_r18_priority(r.get("lint_json_path"))
        if has_p0:
            r18_p0_rounds.append(r["round"])
        if p1:
            r18_p1_warnings.append({"round": r["round"], "hits": p1})
        if p2:
            r18_p2_warnings.append({"round": r["round"], "hits": p2})

    round_info = [_summarize_round(r) for r in rounds]

    if r18_p0_rounds:
        return {
            "decision": "aborted_r18",
            "reason": (f"R18-P0(明确自指 AI 身份)命中 轮次 {r18_p0_rounds}。"
                       f"P0 阻断所有兜底,强制人工介入。"),
            "next_step": ("把全部轮 draft + lint 报告打包给风云人工 review,"
                          "定位 P0 命中段并改稿。"),
            "r18_p0_rounds": r18_p0_rounds,
            "r18_p1_warnings": r18_p1_warnings,
            "r18_p2_warnings": r18_p2_warnings,
            "round_info": round_info,
        }

    # 2. 最后一轮跑门控树
    last = rounds[-1]
    decision, reason = gate_tree(
        last.get("a_score"),
        last.get("b_verdict"),
        last.get("c_verdict"),
        threshold_a,
    )

    if decision == "pass":
        return {
            "decision": "ship",
            "reason": reason,
            "next_step": "进 Step 7(封面)",
            "chosen_version": last["round"],
            "chosen_draft_path": last.get("draft_path"),
            "r18_p1_warnings": r18_p1_warnings,
            "r18_p2_warnings": r18_p2_warnings,
            "round_info": round_info,
        }

    if decision == "abort":
        return {
            "decision": "abort",
            "reason": reason,
            "next_step": "跑 score_draft.py 看报错,修工具链",
            "round_info": round_info,
        }

    # Round 26 修正(2026-05-26):human_gate / revise 走同一条循环路径
    # 漏洞:Round 24 把 single-round human_gate 直接接 auto_partial_pass,
    #       导致 B reject 单轮就 ship 通过(A=74.2 案例真实复现)
    # 修法:human_gate 等同 revise — N<3 → revise(给 writer 用 B brief 改稿一次);
    #       N>=3 → auto_exit(末轮 A 决定 ship vs abort)
    if decision in ("human_gate", "revise"):
        if last["round"] >= 3:
            tag = "3 轮 human_gate 未过" if decision == "human_gate" else "3 轮 revise 未过"
            return _auto_exit_result(
                round_info, r18_p1_warnings, r18_p2_warnings,
                reason + f" | {tag} → 自动出口",
            )
        next_reason = reason
        if decision == "human_gate":
            next_reason += " | human_gate 必须先 revise 至少 1 轮(Round 26 修正)"
        return {
            "decision": "revise",
            "reason": next_reason,
            "next_step": f"回 Step 6.5 改稿(round {last['round']+1})",
            "r18_p1_warnings": r18_p1_warnings,
            "r18_p2_warnings": r18_p2_warnings,
            "round_info": round_info,
        }

    # 兜底:未识别 decision(理论上不会到这,gate_tree 只返回 4 种 + pass)
    return {
        "decision": "abort",
        "reason": f"未识别的 gate_tree decision={decision}: {reason}",
        "next_step": "检查 critic_vote.gate_tree 返回值",
        "round_info": round_info,
    }


def main():
    ap = argparse.ArgumentParser(
        description="critic 三轨投票决议(Musk × Jobs Round 2 门控树版)")
    ap.add_argument("--a-score", type=float, default=None,
                    help="(单轮)Track A 综合分")
    ap.add_argument("--b-verdict", default=None,
                    help="(单轮)ship / no-ship / skip")
    ap.add_argument("--c-verdict", default=None,
                    help="(单轮)sign / no-sign / skip")
    ap.add_argument("--all-rounds", default=None,
                    help="(多轮)JSON 文件路径,含 rounds + threshold_a")
    ap.add_argument("--threshold-a", type=float, default=60.0)
    ap.add_argument("--out", default=None, help="JSON 输出路径")
    args = ap.parse_args()

    if args.all_rounds:
        rounds_data = json.loads(Path(args.all_rounds).read_text(encoding="utf-8"))
        rounds = rounds_data["rounds"]
        threshold = rounds_data.get("threshold_a", args.threshold_a)
        result = vote_all_rounds(rounds, threshold)

        print(f"=== critic vote · multi-round ({len(rounds)} rounds) ===")
        print(f"decision: {result['decision'].upper()}")
        if result.get("auto_partial_pass"):
            print(f"          ↳ auto_partial_pass (Round 24 自动兜底)")
        if result.get("auto_abort"):
            print(f"          ↳ auto_abort (Round 24 自动终止)")
        print(f"reason:   {result['reason']}")
        print(f"next:     {result['next_step']}")
        if "chosen_version" in result:
            print(f"chosen:   round {result['chosen_version']} → "
                  f"{result.get('chosen_draft_path')}")
        print(f"\nround info:")
        for s in result["round_info"]:
            print(f"  round {s['round']}: A={s['a_score']} "
                  f"B={s['b_verdict']} C={s['c_verdict']}")
        if result.get("r18_p1_warnings"):
            total = sum(len(w["hits"]) for w in result["r18_p1_warnings"])
            print(f"\n⚠️  R18-P1(架构暴露,已计入 revise):"
                  f" {total} hits across {len(result['r18_p1_warnings'])} rounds")
        if result.get("r18_p2_warnings"):
            total = sum(len(w["hits"]) for w in result["r18_p2_warnings"])
            print(f"💭 R18-P2(自动化暴露,计入统计):"
                  f" {total} hits across {len(result['r18_p2_warnings'])} rounds")

        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\nJSON: {args.out}")

        # Round 24:human_gate 已废,自动出口走 ship(auto_partial_pass)或 abort(auto_abort)
        exit_map = {"ship": 0, "revise": 1, "abort": 2,
                    "human_gate": 3, "aborted_r18": 4}
        sys.exit(exit_map.get(result["decision"], 2))

    # 单轮模式
    r = vote(args.a_score, args.b_verdict, args.c_verdict, args.threshold_a)
    print(f"=== critic vote · single round ===")
    print(f"A score:  {args.a_score}  (threshold {args.threshold_a})")
    print(f"B:        {args.b_verdict}  -> {r.b_passed}")
    print(f"C:        {args.c_verdict}  -> {r.c_passed}")
    print(f"decision: {r.decision.upper()}")
    print(f"reason:   {r.reason}")
    print(f"next:     {r.next_step}")
    if r.degraded:
        print(f"degraded: {r.degraded}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(asdict(r), ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"\nJSON: {args.out}")

    exit_map = {"ship": 0, "revise": 1, "abort": 2, "human_gate": 3}
    sys.exit(exit_map.get(r.decision, 2))


if __name__ == "__main__":
    main()
