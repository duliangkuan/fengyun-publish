"""
gate.py — Round 17 P0:Step 8 推草稿前的物理保安。

由 PreToolUse hook 触发(Claude 想跑 post_fengyun_publish.py 时),
+ post_fengyun_publish.py main() 第一行调用兜底。

行为:
  - 读 draft frontmatter,检查 WRITE_AGENT.md 定义的 11 个必填 pass_flag
  - 检查 cover_path + image_paths 文件物理存在
  - 缺一 → sys.exit(2) + 把 missing 列表打到 stderr
  - 全通过 → exit 0

Escape hatch:--force-skip-gate(只允许风云本人显式传,会留 audit 日志)

宪法依据:D:\\Dev\\ai-wechat-pipeline\\WRITE_AGENT.md
"""
from __future__ import annotations
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\ai-wechat-pipeline")
AUDIT_LOG = ROOT / "output" / "runs" / "gate_audit.jsonl"


# ============================================================
# 必填 pass_flag 清单(WRITE_AGENT.md Step 8 定义)
# ============================================================

# 必填字段(基础 frontmatter,truthy 即可)
REQUIRED_BASE_FIELDS = ["title", "digest", "author", "slug", "date", "north_star"]

# 必填 pass_flag(每个对应一个 step 的产物,必须 == True)
REQUIRED_PASS_FLAGS = [
    ("writer_pass", "Step 3 fengyun-writer 出稿"),
    ("title_pass", "Step 3.3 标题 harness"),
    ("ending_pass", "Step 3.5 ending harness"),
    # lint 允许 partial_pass 兜底
    (["lint_pass", "lint_partial_pass"], "Step 4 fengyun_lint"),
    ("humanizer_pass", "Step 4.5 humanizer-zh"),
    ("wangxiaobo_pass", "Step 5 王小波语感预审"),
    # Round 24:critic 允许 revise_loop_pass / auto_partial_pass / auto_abort 兜底
    # - auto_partial_pass: 3 轮 revise 未过 + A ≥ 65 系统自动 ship 兜底
    # - auto_abort: 3 轮 revise 未过 + A < 65 系统自动终止(gate 仍允许字段存在,
    #   但下游 post_fengyun_publish 看到 auto_abort 应该不该跑到 gate 这一步,
    #   保留是为审计 + 让 gate 出错信息更友好)
    (["critic_vote_pass", "revise_loop_pass",
      "auto_partial_pass", "auto_abort"],
     "Step 6 三轨 critic vote / Step 6.5 改稿循环 / Step 6.5.8 自动出口"),
    ("huashu_decision_pass", "Step 7.2 花叔 Mode 2 配图决策(0 张图也算 pass)"),
    ("cover_pass", "Step 7-cover 封面生成"),
]

# 必填文件路径(string,需检查物理存在)
REQUIRED_FILE_FIELDS = [
    ("cover_path", "Step 7-cover 封面文件"),
]

# ============================================================
# P0-1 (Round 18, 2026-05-25): Fake-pass 防伪审计字段
# ============================================================
# 审计报告 §三 P0-3 发现:主线程可以拍脑袋写 `critic_b_verdict: "ship"` 而不真调 skill。
# gate 必须同时验证:① _real_run: true ② _source 是非空字符串
# 三轨 critic 三个轨道分别审计

REQUIRED_AUDIT_FIELDS = [
    # (real_run flag, source field, step name)
    ("critic_a_real_run", "critic_a_score", "Step 6 Track A sop_v2_1 数字分"),
    ("critic_b_real_run", "critic_b_source", "Step 6 Track B huashu-perspective 真调"),
    # Round 24 改名:fengyun-self → content-judge(独立第三方评委)
    ("critic_c_real_run", "critic_c_source", "Step 6 Track C content-judge 真调"),
]

# Round 21 P0-9: humanizer / 王小波 防伪(独立组,只在对应 pass_flag=True 时检查)
# Round 22 P0-6 扩展:writer + huashu-image-curator(主线程「假装写文章」「假装调花叔配图」)
# 隔壁 e2e 报告 #6:Auto 模式无 fengyun-writer skill,主线程直接扮 writer,gate 无审计字段
REQUIRED_SKILL_AUDIT_FIELDS = [
    # (pass_flag_to_check, real_run_key, source_key, step_name)
    ("writer_pass", "writer_real_run", "writer_source", "Step 3 fengyun-writer skill"),
    ("title_pass", "title_real_run", "title_source", "Step 3.3 标题 harness"),
    ("ending_pass", "ending_real_run", "ending_source", "Step 3.5 ending harness"),
    ("humanizer_pass", "humanizer_real_run", "humanizer_source", "Step 4.5 humanizer-zh skill"),
    ("wangxiaobo_pass", "wangxiaobo_real_run", "wangxiaobo_source", "Step 5 王小波 perspective skill"),
    ("huashu_decision_pass", "huashu_image_curator_real_run", "huashu_image_curator_source",
     "Step 7.2 huashu-image-curator Mode 2 skill"),
]

# ============================================================
# Round 24 P0-7(P0 from e2e #9):Source content 防伪审计升级
# 不只是 non-empty check,还要验证 source 内容模式匹配工具真调用痕迹
# ============================================================

# 各 skill source 字段必须匹配的内容模式(regex)
# 缺模式的 skill → 只做 non-empty check(原来的行为)
REQUIRED_SOURCE_PATTERNS: dict[str, str] = {
    # huashu_image_curator 必须是 Mode 2 调用痕迹
    "huashu_image_curator_source": r"^huashu-image-curator Mode 2,",
    # critic b 必须包含 binary verdict 证据
    "critic_b_source": r"(ship|not.?ship|verdict|灵魂)",
    # critic c 必须包含挂名意愿证据
    "critic_c_source": r"(挂名|verdict|ship|not.?ship)",
    # writer 必须包含 skill 名或 round 证据
    "writer_source": r"(fengyun-writer|mode|round|retry|writer)",
    # Round 25: title/ending harness 防伪(真调 title_signal.py / ending_signal.py 的痕迹)
    "title_source": r"(title_signal|title_dedup|score_title|hook_type)",
    "ending_source": r"(ending_signal|ending_dedup|score_ending)",
}

# 可选的证据字段(vote_pass 时必填或可选)
REQUIRED_EVIDENCE_FIELDS: list[tuple[str, str, str]] = [
    # (pass_flag_to_check, evidence_key, step_name)
    # huashu_decision_pass 时:image_at_h2_indices 必须存在(允许空list)
    ("huashu_decision_pass", "image_at_h2_indices", "Step 7.2 配图决策产物"),
]

# Round 25(2026-05-25 文内图强制必选,Musk × Newton 同意,Jobs 保留意见)
# 用户决策方案 A:image_paths 物理硬约束非空,删 should_illustrate=false 路径
# Newton 补丁:文件 size ≥ 5 KB(防全黑 / 报错图 / 0 字节通过)
# Musk 补丁:placeholder 是合法路径(daily_quota fallback),但 0 图绝对禁止
REQUIRED_IMAGE_PATHS_FIELD = "image_paths"   # 旧名 OPTIONAL_,Round 25 改强制
IMAGE_MIN_SIZE_BYTES = 5 * 1024  # 5 KB,Newton 有效性 floor
# Round 25 placeholder 路径(daily_quota fallback 合法,但 image_paths 仍要包含它)
PLACEHOLDER_IMAGE_PATH = "assets/placeholder-sketch.png"


# ============================================================
# Frontmatter 解析
# ============================================================

def parse_frontmatter(draft_path: Path) -> dict | None:
    """简易 YAML frontmatter 解析(不依赖 PyYAML).

    返回 dict 或 None(没有 frontmatter)。
    """
    if not draft_path.exists():
        return None
    text = draft_path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm_text = parts[1]
    fm: dict = {}
    # Round 21 P0-16:state machine 支持多行 YAML list
    # 当 val 为空且后续行以「  - 」开头时,聚合成 list
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line or line.startswith("#"):
            i += 1
            continue
        # 多行 list item 行(出现在某 key 之后,这里跳过 — 由上一轮处理)
        if line.lstrip().startswith("- "):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        # 简化 bool 解析
        if val.lower() in ("true", "yes"):
            fm[key] = True
        elif val.lower() in ("false", "no"):
            fm[key] = False
        elif val.startswith("[") and val.endswith("]"):
            # 简易 inline JSON list 解析
            inner = val[1:-1].strip()
            if inner:
                items = [x.strip().strip('"').strip("'") for x in inner.split(",")]
                try:
                    fm[key] = [int(x) for x in items]
                except ValueError:
                    fm[key] = items
            else:
                fm[key] = []
        elif val == "":
            # 可能是多行 YAML list 的 header,看后续行
            list_items = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].rstrip()
                if not nxt or nxt.startswith("#"):
                    j += 1
                    continue
                stripped = nxt.lstrip()
                if stripped.startswith("- "):
                    item = stripped[2:].strip().strip('"').strip("'")
                    list_items.append(item)
                    j += 1
                else:
                    break
            if list_items:
                # 尝试转 int(image_at_h2_indices 这种)
                try:
                    fm[key] = [int(x) for x in list_items]
                except ValueError:
                    fm[key] = list_items
                i = j
                continue
            else:
                fm[key] = ""
        else:
            fm[key] = val
        i += 1
    return fm


# ============================================================
# 检查逻辑
# ============================================================

def check_draft(draft_path: Path) -> tuple[bool, list[str]]:
    """检查 draft frontmatter + 文件存在性.

    返回 (passed: bool, missing_reasons: list[str])
    """
    fm = parse_frontmatter(draft_path)
    if fm is None:
        return False, [f"draft 文件无法解析 frontmatter: {draft_path}"]

    missing: list[str] = []

    # 检查基础字段
    for field in REQUIRED_BASE_FIELDS:
        if not fm.get(field):
            missing.append(f"基础字段缺失:{field}(必填)")

    # 检查 pass_flag
    for field, step_name in REQUIRED_PASS_FLAGS:
        if isinstance(field, list):
            # 任一存在即可
            if not any(fm.get(f) is True for f in field):
                opts = " 或 ".join(field)
                missing.append(f"缺 pass_flag:{opts}={step_name}")
        else:
            if fm.get(field) is not True:
                missing.append(f"缺 pass_flag:{field}={step_name}")

    # 检查文件路径字段
    for field, file_desc in REQUIRED_FILE_FIELDS:
        path_str = fm.get(field)
        if not path_str:
            missing.append(f"缺路径字段:{field}={file_desc}")
            continue
        # path_str 可能是相对 ROOT 或绝对
        p = Path(path_str)
        if not p.is_absolute():
            p = ROOT / path_str
        if not p.exists():
            missing.append(f"{file_desc} 文件不存在:{p}")

    # Round 25 P0 文内图强制必选(用户方案 A · Musk × Newton 同意)
    # 物理硬约束:image_paths 必填非空 + 每个文件物理存在 + size ≥ 5 KB
    # 删除「image_at_h2_indices 空 list 也算 pass」的逃逸路径
    if "image_at_h2_indices" not in fm:
        missing.append("缺 image_at_h2_indices(Step 7.2 产物,Round 25 必填)")

    image_paths = fm.get(REQUIRED_IMAGE_PATHS_FIELD)
    if not image_paths:
        missing.append("image_paths 缺失或空 — 任何 ship 必须有 ≥ 1 张内文图")
    elif not isinstance(image_paths, list):
        missing.append(f"image_paths 字段类型应为 list,实际:{type(image_paths).__name__}")
    else:
        for ip in image_paths:
            p = Path(ip) if Path(ip).is_absolute() else ROOT / ip
            if not p.exists():
                missing.append(f"内文图文件不存在:{p}")
                continue
            try:
                size = p.stat().st_size
                if size < IMAGE_MIN_SIZE_BYTES:
                    missing.append(
                        f"内文图 size {size} bytes < {IMAGE_MIN_SIZE_BYTES} bytes 下限:{p}"
                    )
            except Exception as e:
                missing.append(f"内文图 stat 失败 {p}: {e}")

    # image_generation_degraded=true 路径已废弃(Round 25),仍写入会被 BLOCK
    if fm.get("image_generation_degraded") is True:
        missing.append("image_generation_degraded=true 已废弃(Round 25),应走 placeholder fallback")

    # Round 25 P0:配图决策强制检查 — 不论 image_at_h2_indices 是否为空,
    # huashu-image-curator Mode 2 必须真正执行(防止主线程跳过 Step 7.2)
    if fm.get("huashu_decision_pass") is True:
        curator_real_run = fm.get("huashu_image_curator_real_run")
        curator_source = fm.get("huashu_image_curator_source")
        if curator_real_run is not True:
            missing.append(
                "⛔ 配图决策强制:huashu_image_curator_real_run 缺失 — "
                "不论是否出图,花叔 Mode 2 必须真正执行(P0 图片保障)"
            )
        if not curator_source or not re.search(r"huashu-image-curator Mode 2", str(curator_source)):
            missing.append(
                "⛔ 配图决策强制:huashu_image_curator_source 缺失或不匹配 — "
                "必须是花叔 Mode 2 真调痕迹"
            )

    # P0-1 fake-pass 防伪审计(Round 18)
    # 只在 critic_vote_pass=True 时才检查(防止 partial_pass / revise_loop_pass 路径误伤)
    if fm.get("critic_vote_pass") is True:
        for real_run_key, source_key, step_name in REQUIRED_AUDIT_FIELDS:
            real_run = fm.get(real_run_key)
            source_val = fm.get(source_key)
            if real_run is not True:
                missing.append(
                    f"⚠️  Fake-pass 风险:{step_name} 缺 {real_run_key}:true — "
                    f"必须真调 skill,不许主线程拍脑袋写 verdict(P0-1 防伪)"
                )
            if not source_val or (isinstance(source_val, str) and not source_val.strip()):
                missing.append(
                    f"⚠️  Fake-pass 风险:{step_name} 缺 {source_key} 证据字段 — "
                    f"必须填写真实评分/出处(P0-1 防伪)"
                )

    # Round 21 P0-9 fake-pass 防伪扩展:humanizer / wangxiaobo skill 真调审计
    # 只在对应 pass_flag=True 时检查(允许 partial_pass 路径跳过 skill 而不挂)
    for pass_flag, real_run_key, source_key, step_name in REQUIRED_SKILL_AUDIT_FIELDS:
        if fm.get(pass_flag) is not True:
            continue
        real_run = fm.get(real_run_key)
        source_val = fm.get(source_key)
        if real_run is not True:
            missing.append(
                f"⚠️  Fake-pass 风险:{step_name} 缺 {real_run_key}:true — "
                f"必须真调 skill,不许主线程拍脑袋写 verdict(P0-9 防伪扩展)"
            )
        if not source_val or (isinstance(source_val, str) and not source_val.strip()):
            missing.append(
                f"⚠️  Fake-pass 风险:{step_name} 缺 {source_key} 证据字段 — "
                f"必须填写真实出处(P0-9 防伪扩展)"
            )

    # Round 24 P0-7: Source content 防伪审计升级
    # 对所有有内容模式要求的 source field 做 pattern 验证
    for pass_flag, real_run_key, source_key, step_name in REQUIRED_SKILL_AUDIT_FIELDS:
        if fm.get(pass_flag) is not True:
            continue
        source_val = fm.get(source_key)
        if not source_val:
            continue  # 已经在上一轮 non-empty check 处理过了
        pattern = REQUIRED_SOURCE_PATTERNS.get(source_key)
        if pattern and isinstance(source_val, str):
            if not re.search(pattern, source_val, re.IGNORECASE):
                missing.append(
                    f"⚠️  Source 内容防伪:{step_name} 的 {source_key} 值「{source_val[:60]}」"
                    f"不匹配期望模式「{pattern}」— 必须是工具真调用痕迹,"
                    f"不许主线程拍脑袋写占位文字(Round 24 P0-7 防伪升级)"
                )

    # 也检查 critic 三轨的 source(不受 pass_flag 控制,永远检查)
    # critic_a score 是数字分,不做 pattern 检查
    for source_key, pattern in REQUIRED_SOURCE_PATTERNS.items():
        if source_key not in ("critic_b_source", "critic_c_source"):
            continue
        source_val = fm.get(source_key)
        if not source_val:
            continue
        if isinstance(source_val, str) and not re.search(pattern, source_val, re.IGNORECASE):
            # 推断 step_name
            if source_key == "critic_b_source":
                step_name = "Step 6 Track B huashu-perspective source 模式校验"
            else:
                # Round 24:content-judge(原 fengyun-self)
                step_name = "Step 6 Track C content-judge source 模式校验"
            missing.append(
                f"⚠️  Source 内容防伪:{step_name} 的 {source_key} 值「{source_val[:60]}」"
                f"不匹配期望模式「{pattern}」— 必须包含真实 verdict 证据"
            )

    # R18 字段 check(简易)
    if fm.get("aborted_r18") is True:
        missing.append("⛔ R18 P0 已 abort,严禁推草稿 — 必须人工修后重跑全流程")

    passed = len(missing) == 0
    return passed, missing


# ============================================================
# Audit log
# ============================================================

def write_audit_log(draft_path: Path, passed: bool, missing: list[str], force_skip: bool = False) -> None:
    """每次 gate 调用追加一行 audit log."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(),
        "draft": str(draft_path),
        "passed": passed,
        "missing_count": len(missing),
        "missing": missing[:10],  # 最多 10 条避免日志爆炸
        "force_skip": force_skip,
    }
    try:
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # audit log 写失败不阻断 gate
        pass


# ============================================================
# 从 hook 调用解析 draft path
# ============================================================

def extract_draft_path_from_args(argv: list[str]) -> Path | None:
    """从命令行参数里找 .md 文件(支持 hook 传参 + CLI 直接传)."""
    for a in argv:
        if a.endswith(".md") and "drafts" in a.replace("\\", "/"):
            p = Path(a)
            if not p.is_absolute():
                p = ROOT / a
            return p
    return None


def extract_from_stdin_hook_payload() -> tuple[Path | None, bool]:
    """Claude Code hook 通过 stdin 传 JSON payload.

    返回 (draft_path, is_publish_command)
      - is_publish_command=False 时 gate 放行(非 ship 场景)
      - is_publish_command=True 时必须 check
    """
    try:
        if sys.stdin.isatty():
            return None, False
        payload_str = sys.stdin.read()
        if not payload_str.strip():
            return None, False
        payload = json.loads(payload_str)
        cmd = (
            payload.get("tool_input", {}).get("command")
            or payload.get("command")
            or ""
        )
        # 关键 dispatcher:只在命令含 post_fengyun_publish 时才需要 check
        is_publish = "post_fengyun_publish" in cmd
        if not is_publish:
            return None, False
        # 匹配 .md path
        m = re.search(r"([A-Za-z]:[\\/][^\s]+\.md|output[\\/]drafts[\\/][^\s]+\.md)", cmd)
        if m:
            path_str = m.group(1)
            p = Path(path_str)
            if not p.is_absolute():
                p = ROOT / path_str
            return p, True
        return None, True  # 是 publish 命令但没找到 .md → 当作出错,继续走 check 流程
    except Exception:
        return None, False


# ============================================================
# CLI 主入口
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="Round 17 P0 — ship pipeline 物理保安")
    parser.add_argument("draft", nargs="?", help="draft markdown 路径(可选,会尝试从 stdin/argv 推断)")
    parser.add_argument("--force-skip-gate", action="store_true",
                        help="紧急绕过(只允许风云本人显式传,留 audit)")
    parser.add_argument("--check-only", action="store_true",
                        help="不退出,只打印检查结果(测试用)")
    args = parser.parse_args()

    # 推断 draft 路径
    draft_path = None
    is_publish_cmd = bool(args.draft)  # CLI 直接传 = 显式 check
    if args.draft:
        p = Path(args.draft)
        draft_path = p if p.is_absolute() else ROOT / args.draft
    if draft_path is None:
        draft_path, hook_is_publish = extract_from_stdin_hook_payload()
        is_publish_cmd = is_publish_cmd or hook_is_publish
    if draft_path is None:
        draft_path = extract_draft_path_from_args(sys.argv[1:])
        # CLI 含 .md path → 当作显式 check
        if draft_path:
            is_publish_cmd = True

    # 非 publish 命令 → 直接放行(只在 ship 时拦)
    if not is_publish_cmd:
        return 0

    if draft_path is None:
        print("⚠️  gate.py 收到 publish 命令但找不到 draft 路径 — 放行(避免误伤)", file=sys.stderr)
        return 0

    # Force skip 路径(留 audit)
    # Round 24 P1-1(Jobs 视角):强化警报 — audit log Row 38 实测被触发但用户无感知。
    # 现在用 9 行红框 + 收集当前 frontmatter 缺失字段一并记录,让 force_skip 不再静默
    if args.force_skip_gate:
        # 先跑一次 check_draft 拿到「本来会缺什么」— 即使 force-skip,也要记录绕过了哪些检查
        try:
            _passed_real, missing_real = check_draft(draft_path)
        except Exception as e:
            missing_real = [f"check_draft 异常: {e}"]
        write_audit_log(
            draft_path, passed=True,
            missing=["FORCE SKIP"] + [f"[bypassed] {m}" for m in missing_real[:10]],
            force_skip=True,
        )
        # 高亮红框警报 — Jobs 视角:让 force_skip 不再「静默走过去」
        print("", file=sys.stderr)
        print("╔══════════════════════════════════════════════════════════════════╗", file=sys.stderr)
        print("║  🚨 FORCE-SKIP-GATE 触发 — 本次 ship 走兜底通道,非正常 pass     ║", file=sys.stderr)
        print("╠══════════════════════════════════════════════════════════════════╣", file=sys.stderr)
        print(f"║  draft : {draft_path.name[:54]:<54}║", file=sys.stderr)
        print(f"║  绕过项: {len(missing_real)} 个 gate 检查 (详见 audit log)              ║", file=sys.stderr)
        print("║  含义  : 这次 ship 不是「真过」,是「被 --force-skip-gate 绕」    ║", file=sys.stderr)
        print("║  动作  : audit log 已写入 bypassed 字段,事后回查                ║", file=sys.stderr)
        print("╚══════════════════════════════════════════════════════════════════╝", file=sys.stderr)
        print("", file=sys.stderr)
        if missing_real:
            print(f"⚠️  被绕过的具体检查(前 5 条):", file=sys.stderr)
            for i, m in enumerate(missing_real[:5], 1):
                print(f"   [{i}] {m[:100]}", file=sys.stderr)
            print("", file=sys.stderr)
        return 0

    # 主检查
    passed, missing = check_draft(draft_path)
    write_audit_log(draft_path, passed, missing)

    if passed:
        print(f"✅ gate.py PASS:{draft_path.name} 所有 step 产物齐备,允许推草稿", file=sys.stderr)
        return 0

    # 失败 → 详细反馈
    print(f"❌ gate.py BLOCKED:{draft_path.name} 缺 {len(missing)} 个 step 产物", file=sys.stderr)
    print(f"   宪法依据:WRITE_AGENT.md", file=sys.stderr)
    print(f"", file=sys.stderr)
    for i, reason in enumerate(missing, 1):
        print(f"   [{i}] {reason}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"主线程必须回去补完前置 step,再推草稿。", file=sys.stderr)
    print(f"紧急情况风云可显式传 --force-skip-gate(留 audit log)。", file=sys.stderr)

    if args.check_only:
        return 0
    return 2  # exit code 2 = PreToolUse hook 阻断 Claude


if __name__ == "__main__":
    sys.exit(main())
