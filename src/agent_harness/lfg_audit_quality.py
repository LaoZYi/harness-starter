"""LFG audit — quality dimensions 11-15(实际威力暗角检测).

2026-04-26 抽离自 lfg_audit_checks.py:形式集成 ≠ 实际深度,这 5 维度
检测形式满分但实际威力可能不到位的暗角。

- Dim 11 引用深度 — 每个 skill 至少 2 次引用,防"提到一次就忘"
- Dim 12 主模板长度门禁 — 防主模板炸 context
- Dim 13 用户确认点密度 — 防 🔴 太多用户疲劳
- Dim 14 关键守卫多点 — source-verify / careful / context-budget 各 ≥ 2 次
- Dim 15 通道层级化 — 长段抽到 references/,主模板留指针
"""
from __future__ import annotations

import re
from pathlib import Path

from .lfg_audit import SUPERPOWERS_REL, DimensionScore
from .skills_registry import expected_in_lfg, load_registry


def check_reference_depth(lfg_text: str, repo_root: Path) -> DimensionScore:
    """Dim 11: 引用深度 — 每个 expected_in_lfg=true 的 skill 至少 2 次引用。

    形式集成(grep 命中)≠ 实际深度——只引用 1 次的 skill AI 容易遗忘。
    """
    sp_tmpl = repo_root / SUPERPOWERS_REL
    try:
        registry = load_registry(sp_tmpl)
    except (FileNotFoundError, ValueError):
        return DimensionScore(11, "引用深度", 0.0, [], ["registry 损坏"])
    expected = expected_in_lfg(registry)  # 返回已带 / 前缀的 skill id
    checks = []
    notes = []
    shallow = []
    for skill_id in sorted(expected):
        count = lfg_text.count(skill_id)
        ok = count >= 2
        if not ok:
            shallow.append(f"{skill_id}({count}次)")
        checks.append((f"{skill_id} 至少 2 次", ok))
    score = sum(1 for _, ok in checks if ok) / len(checks) if checks else 0.0
    if shallow:
        head = ", ".join(shallow[:5])
        suffix = "..." if len(shallow) > 5 else ""
        notes.append(f"浅集成:{head}{suffix}")
    return DimensionScore(11, "引用深度", score, checks, notes)


def check_template_length(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 12: 主模板长度门禁 — 超长会让每次 /lfg 启动都炸 context。"""
    line_count = lfg_text.count("\n") + 1
    if line_count <= 600:
        score, status = 1.0, f"{line_count} 行(优秀,<= 600)"
    elif line_count <= 800:
        score, status = 0.85, f"{line_count} 行(良好,600-800)"
    elif line_count <= 1000:
        score, status = 0.5, f"{line_count} 行(警告,800-1000 — 抽长段到 references/)"
    else:
        score, status = 0.0, f"{line_count} 行(超限,> 1000 — 必须立即抽离)"
    return DimensionScore(12, "主模板长度", score, [(status, score >= 0.85)])


def check_intervention_density(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 13: 用户确认点密度 — 太多 🔴 会让用户疲劳。"""
    line_count = lfg_text.count("\n") + 1
    rocket_count = lfg_text.count("🔴")
    if line_count == 0:
        return DimensionScore(13, "确认点密度", 0.0, [("空模板", False)])
    density = rocket_count / (line_count / 50)
    if density <= 1.0:
        score, label = 1.0, "优秀"
    elif density <= 1.5:
        score, label = 0.7, "警告"
    elif density <= 2.0:
        score, label = 0.4, "疲劳"
    else:
        score, label = 0.0, "超载"
    status = f"{rocket_count} 个 🔴 / {line_count} 行 = {density:.2f}/50 行({label})"
    return DimensionScore(13, "确认点密度", score, [(status, score >= 0.7)])


def check_critical_guards(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 14: 关键守卫多点引用 — 防 API 幻觉/不可逆/上下文爆炸的守卫不能只提一次。"""
    guards = {
        "/source-verify": "防 API 幻觉",
        "/careful": "防不可逆操作",
        "context-budget": "防上下文爆炸",
    }
    checks = []
    for keyword, purpose in guards.items():
        count = lfg_text.count(keyword)
        ok = count >= 2
        checks.append((f"{keyword} 至少 2 次({purpose}) — 实际 {count} 次", ok))
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(14, "关键守卫多点", score, checks)


def check_channel_layering(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 15: 通道层级化 — 长段通过 references/ 抽离机制,主模板留指针。"""
    checks = [
        (
            ".agent-harness/references/ 路径引用",
            ".agent-harness/references/" in lfg_text,
        ),
        (
            "具体 references/<file>.md 引用",
            bool(re.search(r"references/[\w-]+\.md", lfg_text)),
        ),
        (
            "/recall --refs 加载机制",
            "/recall --refs" in lfg_text or "recall --refs" in lfg_text,
        ),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(15, "通道层级化", score, checks)


QUALITY_CHECKS = [
    check_reference_depth,
    check_template_length,
    check_intervention_density,
    check_critical_guards,
    check_channel_layering,
]
