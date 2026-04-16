"""Skills registry — single source of truth for 34 skill metadata.

Loaded from `templates/superpowers/skills-registry.json` and rendered into:
- `which-skill.md.tmpl`  (decision tree + index by phase)
- `lfg.md.tmpl`              (coverage table)
- `tests/test_lfg_coverage.py` (EXPECTED_IN/NOT_IN_LFG)

Placeholders use `<<SKILL_xxx>>` (double-angle, distinct from harness
`{{var}}` jinja-style placeholders) to avoid double-substitution conflicts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SKILLS_REGISTRY_FILENAME = "skills-registry.json"
PLACEHOLDER_DECISION_TREE = "<<SKILL_DECISION_TREE>>"
PLACEHOLDER_INDEX_BY_PHASE = "<<SKILL_INDEX_BY_PHASE>>"
PLACEHOLDER_COVERAGE_TABLE = "<<SKILL_COVERAGE_TABLE>>"

CATEGORY_PHASE_ORDER = ["process", "implementation", "review"]
PHASE_LABEL = {
    "process": "流程类（影响怎么思考和规划）",
    "implementation": "实现类（影响怎么执行）",
    "review": "收尾类（影响怎么完成）",
}


def load_registry(template_root: Path) -> dict[str, Any]:
    """Load and validate skills-registry.json from a superpowers template root.

    Args:
        template_root: Path to `templates/superpowers/` directory containing
            `skills-registry.json`.

    Returns:
        Parsed registry dict with `registry_version`, `categories`, `skills` keys.

    Raises:
        FileNotFoundError: registry file missing.
        ValueError: schema validation failure.
    """
    registry_path = Path(template_root) / SKILLS_REGISTRY_FILENAME
    data = json.loads(registry_path.read_text(encoding="utf-8"))

    if data.get("registry_version") != 1:
        raise ValueError(
            f"unsupported registry_version: {data.get('registry_version')}"
        )
    skills = data.get("skills")
    if not isinstance(skills, list) or not skills:
        raise ValueError("registry.skills must be a non-empty list")

    seen_ids: set[str] = set()
    for skill in skills:
        for required in ("id", "name", "category", "expected_in_lfg"):
            if required not in skill:
                raise ValueError(f"skill missing field {required}: {skill}")
        if skill["id"] in seen_ids:
            raise ValueError(f"duplicate skill id: {skill['id']}")
        seen_ids.add(skill["id"])
        if not skill["expected_in_lfg"] and not skill.get("exclusion_reason"):
            raise ValueError(
                f"excluded skill {skill['id']} must have exclusion_reason"
            )
    return data


def expected_in_lfg(registry: dict) -> set[str]:
    """Return set of slash-prefixed skill ids that MUST appear in lfg.md.tmpl."""
    return {f"/{s['id']}" for s in registry["skills"] if s["expected_in_lfg"]}


def expected_not_in_lfg(registry: dict) -> dict[str, str]:
    """Return id -> exclusion_reason for skills intentionally NOT in lfg."""
    return {
        f"/{s['id']}": s["exclusion_reason"]
        for s in registry["skills"]
        if not s["expected_in_lfg"]
    }


def render_decision_tree(registry: dict) -> str:
    """Render the which-skill decision tree text block."""
    lines = ["```", "开始任务", "  |"]
    for skill in registry["skills"]:
        label = skill.get("decision_tree_label")
        if not label:
            continue
        slash = f"/{skill['id']}"
        # 28-char left column for the question, then arrow + skill
        question = f"  +-- {label}"
        padded = question.ljust(34, "-")
        lines.append(f"{padded}> {slash}")
        lines.append("  |")
    if lines[-1] == "  |":
        lines.pop()
    lines.append("```")
    return "\n".join(lines)


def render_skill_index_by_phase(registry: dict) -> str:
    """Render the three-section index used in which-skill.md.tmpl."""
    sections: list[str] = []
    for cat in CATEGORY_PHASE_ORDER:
        cat_skills = [s for s in registry["skills"] if s["category"] == cat]
        if not cat_skills:
            continue
        sections.append(f"### {PHASE_LABEL[cat]}\n")
        for s in cat_skills:
            sections.append(f"- `/{s['id']}` —— {s['one_line']}")
        sections.append("")
    return "\n".join(sections).rstrip()


def render_lfg_coverage_table(registry: dict) -> str:
    """Render the lfg.md.tmpl skill coverage table grouped by lfg_stage."""
    by_stage: dict[str, list[str]] = {}
    for s in registry["skills"]:
        if not s["expected_in_lfg"]:
            continue
        for stage in s.get("lfg_stage") or []:
            by_stage.setdefault(stage, []).append(f"`/{s['id']}`")

    lines = ["| 阶段 | 调用的技能 |", "|---|---|"]
    for stage in sorted(by_stage.keys(), key=_stage_sort_key):
        skills_str = "、".join(by_stage[stage])
        lines.append(f"| {stage} | {skills_str} |")

    excluded = [s for s in registry["skills"] if not s["expected_in_lfg"]]
    if excluded:
        excluded_str = "、".join(
            f"`/{s['id']}`（{s['exclusion_reason']}）" for s in excluded
        )
        lines.append(f"| 元任务（非单任务流，不由 /lfg 驱动） | {excluded_str} |")

    return "\n".join(lines)


def render_all(template_text: str, registry: dict) -> str:
    """Replace all <<SKILL_*>> placeholders in a template body."""
    text = template_text
    text = text.replace(PLACEHOLDER_DECISION_TREE, render_decision_tree(registry))
    text = text.replace(
        PLACEHOLDER_INDEX_BY_PHASE, render_skill_index_by_phase(registry)
    )
    text = text.replace(
        PLACEHOLDER_COVERAGE_TABLE, render_lfg_coverage_table(registry)
    )
    return text


def apply_to_rendered_dict(
    template_root: Path, rendered: dict[str, str]
) -> None:
    """In-place substitute <<SKILL_*>> in rendered dict's two skill files (Issue #27)."""
    try:
        registry = load_registry(template_root)
    except (FileNotFoundError, ValueError):
        return
    for path in (".claude/commands/which-skill.md", ".claude/commands/lfg.md"):
        if path in rendered:
            rendered[path] = render_all(rendered[path], registry)


def apply_to_target(
    template_root: Path, target_root: Path, *, dry_run: bool = False
) -> list[str]:
    """Post-process materialized templates: replace <<SKILL_*>> placeholders.

    Called from initializer / upgrade after materialize_templates so the
    rendered .claude/commands/which-skill.md and lfg.md get their
    skill blocks substituted from skills-registry.json.

    Returns list of files actually rewritten (empty in dry_run).
    """
    try:
        registry = load_registry(template_root)
    except FileNotFoundError:
        return []

    targets = [
        target_root / ".claude" / "commands" / "which-skill.md",
        target_root / ".claude" / "commands" / "lfg.md",
    ]
    rewritten: list[str] = []
    for path in targets:
        if not path.is_file():
            continue
        original = path.read_text(encoding="utf-8")
        rendered = render_all(original, registry)
        if rendered == original:
            continue
        if not dry_run:
            path.write_text(rendered, encoding="utf-8")
        rewritten.append(str(path.relative_to(target_root)))
    return rewritten


def _stage_sort_key(stage: str) -> tuple:
    """Sort stages like '0.2 历史加载' < '1 环境准备' < '10 收尾'."""
    head = stage.split(" ", 1)[0]
    try:
        parts = [int(x) for x in head.split(".")]
        return (0, parts)
    except ValueError:
        return (1, [head])
