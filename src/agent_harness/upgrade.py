from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from difflib import unified_diff
from pathlib import Path

from .initializer import SUPERPOWERS_ROOT, TEMPLATE_ROOT, prepare_initialization
from .models import UpgradeExecutionResult, UpgradePlanResult
from .templating import render_templates


def _filter_rendered(rendered: dict[str, str], only_files: list[str] | None) -> dict[str, str]:
    if not only_files:
        return rendered

    allowed = set(only_files)
    return {path: content for path, content in rendered.items() if path in allowed}


def _build_diff(relative_path: str, current_content: str, expected_content: str) -> str:
    return "".join(
        unified_diff(
            current_content.splitlines(keepends=True),
            expected_content.splitlines(keepends=True),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
        )
    )


def _generate_changelog(plan: UpgradePlanResult) -> str:
    lines = ["# 升级变更摘要\n"]
    lines.append(f"时间：{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    if plan.create_files:
        lines.append(f"\n## 新增文件（{len(plan.create_files)} 个）\n")
        for f in plan.create_files:
            lines.append(f"- `{f}`")
    if plan.update_files:
        lines.append(f"\n## 更新文件（{len(plan.update_files)} 个）\n")
        for f in plan.update_files:
            lines.append(f"- `{f}`")
    if plan.unchanged_files:
        lines.append(f"\n## 未变化文件（{len(plan.unchanged_files)} 个）\n")
        for f in plan.unchanged_files:
            lines.append(f"- `{f}`")
    return "\n".join(lines) + "\n"


def plan_upgrade(
    target_root: Path,
    answers: dict[str, object],
    *,
    only_files: list[str] | None = None,
) -> UpgradePlanResult:
    target_root = target_root.resolve()
    _, _, context = prepare_initialization(target_root, answers)
    rendered = render_templates(TEMPLATE_ROOT, context)
    if answers.get("superpowers", True) and SUPERPOWERS_ROOT.is_dir():
        rendered.update(render_templates(SUPERPOWERS_ROOT, context))
    rendered = _filter_rendered(rendered, only_files)

    create_files: list[str] = []
    update_files: list[str] = []
    unchanged_files: list[str] = []
    diffs: dict[str, str] = {}

    for relative_path, expected_content in rendered.items():
        path = target_root / relative_path
        if not path.exists():
            create_files.append(relative_path)
            continue

        current_content = path.read_text(encoding="utf-8")
        if current_content == expected_content:
            unchanged_files.append(relative_path)
        else:
            update_files.append(relative_path)
            diffs[relative_path] = _build_diff(relative_path, current_content, expected_content)

    checklist: list[str] = []
    if create_files:
        checklist.append("新增文件可以直接接入，优先检查 docs/ 和 .agent-harness/ 下的新入口。")
    if update_files:
        checklist.append("存在会变化的文件，升级前请先 review 差异并保留本地自定义内容。")
    if ".agent-harness/project.json" in update_files or ".agent-harness/project.json" in create_files:
        checklist.append("升级后请确认 .agent-harness/project.json 里的命令和目录仍准确。")
    if "AGENTS.md" in update_files or "AGENTS.md" in create_files:
        checklist.append("升级后请确认 AGENTS.md 仍符合团队当前协作习惯。")
    if not checklist:
        checklist.append("当前生成结果与仓库内 harness 文件一致，可以按需跳过升级。")

    return UpgradePlanResult(
        target_root=str(target_root),
        create_files=create_files,
        update_files=update_files,
        unchanged_files=unchanged_files,
        checklist=checklist,
        diffs=diffs,
    )


def execute_upgrade(
    target_root: Path,
    answers: dict[str, object],
    *,
    only_files: list[str] | None = None,
    dry_run: bool = False,
) -> UpgradeExecutionResult:
    target_root = target_root.resolve()
    plan = plan_upgrade(target_root, answers, only_files=only_files)
    changelog = _generate_changelog(plan)

    if dry_run:
        return UpgradeExecutionResult(
            target_root=str(target_root),
            created_files=plan.create_files,
            updated_files=plan.update_files,
            unchanged_files=plan.unchanged_files,
            selected_files=sorted(plan.create_files + plan.update_files + plan.unchanged_files),
            dry_run=True,
            changelog=changelog,
        )

    _, _, context = prepare_initialization(target_root, answers)
    rendered = render_templates(TEMPLATE_ROOT, context)
    if answers.get("superpowers", True) and SUPERPOWERS_ROOT.is_dir():
        rendered.update(render_templates(SUPERPOWERS_ROOT, context))
    rendered = _filter_rendered(rendered, only_files)

    backup_root: Path | None = None
    if plan.update_files:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        backup_root = target_root / ".agent-harness" / "backups" / timestamp

    for relative_path in plan.update_files:
        source_path = target_root / relative_path
        backup_path = backup_root / relative_path if backup_root else None
        if backup_path is not None:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")

    for relative_path in plan.create_files + plan.update_files:
        output_path = target_root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered[relative_path], encoding="utf-8")

    changelog_path = target_root / ".agent-harness" / "upgrade-changelog.md"
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    changelog_path.write_text(changelog, encoding="utf-8")

    return UpgradeExecutionResult(
        target_root=str(target_root),
        created_files=plan.create_files,
        updated_files=plan.update_files,
        unchanged_files=plan.unchanged_files,
        backup_root=str(backup_root) if backup_root is not None else None,
        selected_files=sorted(rendered.keys()),
        dry_run=False,
        changelog=changelog,
    )


_PLACEHOLDER_RE = re.compile(r"\{\{\s*[a-z0-9_]+\s*\}\}")


def verify_upgrade(target_root: Path) -> list[str]:
    """Post-upgrade verification. Returns list of warnings (empty = PASS)."""
    target_root = target_root.resolve()
    warnings: list[str] = []
    agents = target_root / "AGENTS.md"
    if agents.exists():
        line_count = len(agents.read_text(encoding="utf-8").splitlines())
        if line_count > 80:
            warnings.append(f"AGENTS.md 超过 80 行（当前 {line_count} 行），建议拆分到 docs/。")
    pj = target_root / ".agent-harness" / "project.json"
    if pj.exists():
        try:
            json.loads(pj.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            warnings.append(f"project.json 格式错误：{e}")
    for md in (target_root / "AGENTS.md", target_root / "CLAUDE.md"):
        if md.exists():
            text = md.read_text(encoding="utf-8")
            unfilled = _PLACEHOLDER_RE.findall(text)
            if unfilled:
                warnings.append(f"{md.name} 中存在未填充的占位符：{', '.join(unfilled[:3])}")
    return warnings
