"""10-dimension /lfg audit checks.

Each check takes (lfg_text, repo_root) → DimensionScore.
See `lfg_audit.py` for the data model and `audit()` orchestrator.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from .lfg_audit import (
    COMMON_REL,
    SUPERPOWERS_REL,
    DimensionScore,
    collect_opt_in_rules,
)
from .skills_registry import expected_in_lfg, load_registry


def check_rules_coverage(lfg_text: str, repo_root: Path) -> DimensionScore:
    """Dim 1: always-on rules in templates/common/.claude/rules/ all referenced."""
    opt_in = collect_opt_in_rules(repo_root)
    common_rules_dir = repo_root / COMMON_REL / ".claude" / "rules"
    checks: list[tuple[str, bool]] = []
    notes: list[str] = []

    if not common_rules_dir.exists():
        return DimensionScore(
            1, "Rules 覆盖", 0.0, [],
            [f"规则目录缺失：{common_rules_dir}"],
        )

    always_on: list[str] = []
    for tmpl in sorted(common_rules_dir.glob("*.md.tmpl")):
        name = tmpl.name[: -len(".tmpl")]  # context-budget.md
        if name in opt_in:
            continue
        always_on.append(name)

    for rule_name in always_on:
        basename = rule_name[: -len(".md")]
        path_pattern = re.compile(rf"\.claude/rules/{re.escape(rule_name)}")
        keyword_pattern = re.compile(rf"\b{re.escape(basename)}\b")
        ok = bool(path_pattern.search(lfg_text) or keyword_pattern.search(lfg_text))
        checks.append((f"{rule_name} 被引用", ok))

    if opt_in:
        notes.append(f"opt-in 规则（不计入基线）：{', '.join(sorted(opt_in))}")

    score = sum(1 for _, ok in checks if ok) / len(checks) if checks else 0.0
    return DimensionScore(1, "Rules 覆盖", score, checks, notes)


def check_skills_orchestration(lfg_text: str, repo_root: Path) -> DimensionScore:
    """Dim 2: every expected_in_lfg=true skill referenced in lfg.md.tmpl."""
    sp_tmpl = repo_root / SUPERPOWERS_REL
    try:
        registry = load_registry(sp_tmpl)
    except (FileNotFoundError, ValueError) as exc:
        return DimensionScore(
            2, "Skills 编排", 0.0, [], [f"registry 加载失败：{exc}"]
        )
    expected = sorted(expected_in_lfg(registry))
    checks: list[tuple[str, bool]] = []
    for skill in expected:
        pattern = re.compile(rf"{re.escape(skill)}\b")
        checks.append((f"{skill} 被编排", bool(pattern.search(lfg_text))))
    score = sum(1 for _, ok in checks if ok) / len(checks) if checks else 0.0
    return DimensionScore(2, "Skills 编排", score, checks)


def check_memory_layering(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 3: 分层记忆 4 要素都要显式出现。"""
    checks = [
        ("读 memory-index.md", "memory-index.md" in lfg_text),
        ("/recall 技能被调用", "/recall" in lfg_text),
        ("memory rebuild 收尾", "memory rebuild" in lfg_text),
        (
            "L0/L1/L2/L3 或分层概念",
            bool(re.search(r"L[0-3]/L[0-3]|分层记忆|分层加载", lfg_text)),
        ),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(3, "Memory 分层加载", score, checks)


def check_anti_laziness(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 4: anti-laziness rule + 4 gates。"""
    checks = [
        ("anti-laziness.md 路径引用", "anti-laziness.md" in lfg_text),
        ("数量门禁", "数量门禁" in lfg_text),
        ("上下文隔离", "上下文隔离" in lfg_text),
        ("反合理化", "反合理化" in lfg_text),
        ("下游消费者", "下游消费者" in lfg_text),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(4, "反偷懒门禁", score, checks)


def check_stuck_detector(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 5: 3 次硬停机制。"""
    fail_context = bool(
        re.search(r"连续 3 (步|次|轮)", lfg_text)
        or re.search(r"3 轮.{0,20}(未收敛|失败|修复)", lfg_text)
    )
    checks = [
        ("连续 3 步/次/轮 失败判定", fail_context),
        ("卡点记录 / 停下", bool(re.search(r"🔴 停下来|停下|卡点", lfg_text))),
        (
            "候选方向 / 选项给用户",
            bool(re.search(r"候选方向|3 个候选|三个选项|选项[:：]", lfg_text)),
        ),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(5, "StuckDetector", score, checks)


def check_agent_design(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 6: F3/F5/F8/F10 + /agent-design-check。"""
    has_f_factor = bool(
        re.search(r"\bF(3|5|8|10)\b", lfg_text)
        or re.search(
            r"Context Ownership|Control Flow|State Unification|Small Focused",
            lfg_text,
        )
    )
    checks = [
        ("/agent-design-check 被串接", "/agent-design-check" in lfg_text),
        ("F3/F5/F8/F10 因子标识", has_f_factor),
        (
            "子 agent 隔离（bin/agent init 或 diary）",
            bool(re.search(r"bin/agent (init|diary|aggregate)", lfg_text)),
        ),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(6, "Agent 设计（12-factor）", score, checks)


def check_audit_wal(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 7: audit append 覆盖 3 个关键文件。"""

    def appends_for(fname: str) -> bool:
        pattern = re.compile(
            rf"audit append[^`]*--file {re.escape(fname)}", re.DOTALL
        )
        return bool(pattern.search(lfg_text))

    checks = [
        ("audit append current-task.md", appends_for("current-task.md")),
        ("audit append lessons.md", appends_for("lessons.md")),
        ("audit append task-log.md", appends_for("task-log.md")),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(7, "Audit WAL", score, checks)


def check_doc_sync(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 8: 文档同步规则 + /doc-release + 关键文档名。"""
    checks = [
        ("documentation-sync 规则引用", "documentation-sync" in lfg_text),
        ("/doc-release 技能被串接", "/doc-release" in lfg_text),
        (
            "docs/product.md 或 docs/architecture.md 在同步语境",
            bool(
                re.search(
                    r"docs/(product|architecture)\.md.{0,40}(更新|同步|更改)",
                    lfg_text,
                )
                or "README、docs/product.md" in lfg_text
            ),
        ),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(8, "文档同步", score, checks)


def check_knowledge_compound(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 9: /compound + memory rebuild + audit lessons."""
    has_rebuild_after_compound = bool(
        re.search(
            r"/compound[\s\S]{0,500}memory rebuild|memory rebuild[\s\S]{0,100}"
            r"compound|compound 完成后[\s\S]{0,500}memory rebuild",
            lfg_text,
        )
    )
    checks = [
        ("/compound 被串接", "/compound" in lfg_text),
        ("compound 后刷新 memory-index", has_rebuild_after_compound),
        (
            "lessons.md 写入有 WAL 审计",
            bool(
                re.search(
                    r"audit append[^`]*--file lessons\.md", lfg_text, re.DOTALL
                )
            ),
        ),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(9, "知识复利", score, checks)


def check_context_budget(lfg_text: str, _repo_root: Path) -> DimensionScore:
    """Dim 10: context-budget 规则 + /compact + Think in Code / 2k 预算。"""
    checks = [
        ("context-budget.md 路径引用", "context-budget.md" in lfg_text),
        ("/compact 被调用", "/compact" in lfg_text),
        (
            "2k tokens 预算或 Think in Code",
            bool(re.search(r"2k tokens|Think in Code|> 2k", lfg_text)),
        ),
    ]
    score = sum(1 for _, ok in checks if ok) / len(checks)
    return DimensionScore(10, "Context Budget", score, checks)


# 维度 11-15 抽到 lfg_audit_quality.py(实际威力暗角检测,2026-04-26)
from .lfg_audit_quality import QUALITY_CHECKS  # noqa: E402


DIMENSION_CHECKS: list[Callable[[str, Path], DimensionScore]] = [
    check_rules_coverage,
    check_skills_orchestration,
    check_memory_layering,
    check_anti_laziness,
    check_stuck_detector,
    check_agent_design,
    check_audit_wal,
    check_doc_sync,
    check_knowledge_compound,
    check_context_budget,
    *QUALITY_CHECKS,
]
