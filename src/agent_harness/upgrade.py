from __future__ import annotations

import fnmatch
import json
from datetime import UTC, datetime
from difflib import unified_diff
from pathlib import Path

from ._merge3 import json_merge, merge3
from ._shared import PKG_DIR, PLACEHOLDER_RE, SUPERPOWERS_ROOT, TEMPLATE_ROOT
from .initializer import _load_preset, prepare_initialization
from .models import UpgradeExecutionResult, UpgradePlanResult
from .templating import render_templates

BASE_DIR = ".agent-harness/.base"

# File category manifest. overwrite=pure template, skip=user data,
# json_merge=structured merge, default=three_way line-based merge.
FILE_CATEGORIES: dict[str, str] = {
    ".claude/commands/*": "overwrite",
    ".claude/rules/*": "overwrite",
    ".claude/hooks/*": "overwrite",
    ".claude/settings.json": "overwrite",
    ".github/*": "overwrite",
    "CLAUDE.md": "overwrite",
    "CLAUDE.local.md.example": "overwrite",
    "docs/decisions/.gitkeep": "overwrite",
    "docs/superpowers/specs/.gitkeep": "overwrite",
    "notes/.gitkeep": "overwrite",
    ".agent-harness/current-task.md": "skip",
    ".agent-harness/task-log.md": "skip",
    ".agent-harness/lessons.md": "skip",
    ".agent-harness/memory-index.md": "skip",
    ".agent-harness/init-summary.md": "skip",
    ".agent-harness/project.json": "json_merge",
}

PROJECT_JSON_FW_KEYS = {"harness_version"}


def get_category(rel_path: str) -> str:
    for pattern, category in FILE_CATEGORIES.items():
        if fnmatch.fnmatch(rel_path, pattern):
            return category
    return "three_way"

def _filter_rendered(rendered: dict[str, str], only_files: list[str] | None) -> dict[str, str]:
    if not only_files:
        return rendered
    allowed = set(only_files)
    return {path: content for path, content in rendered.items() if path in allowed}


def _build_diff(rp: str, cur: str, exp: str) -> str:
    return "".join(unified_diff(cur.splitlines(keepends=True), exp.splitlines(keepends=True), fromfile=f"a/{rp}", tofile=f"b/{rp}"))


def _render_all(root: Path, answers: dict[str, object]) -> dict[str, str]:
    _, _, ctx = prepare_initialization(root, answers)
    project_type = str(answers.get("project_type") or "backend-service")
    preset = _load_preset(project_type)
    exclude = [f".claude/rules/{r}" for r in preset.get("exclude_rules", [])]
    rendered = render_templates(TEMPLATE_ROOT, ctx, exclude=exclude)
    if answers.get("superpowers", True) and SUPERPOWERS_ROOT.is_dir():
        rendered.update(render_templates(SUPERPOWERS_ROOT, ctx))
    type_root = PKG_DIR / "templates" / project_type
    if type_root.is_dir():
        rendered.update(render_templates(type_root, ctx))
    return rendered


def _generate_changelog(plan: UpgradePlanResult) -> str:
    lines = [f"# 升级变更摘要\n\n时间：{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"]
    for label, files in [("新增", plan.create_files), ("更新", plan.update_files), ("未变化", plan.unchanged_files)]:
        if files:
            lines.append(f"\n## {label}文件（{len(files)} 个）\n")
            lines.extend(f"- `{f}`" for f in files)
    return "\n".join(lines) + "\n"


def save_base(target_root: Path, rendered: dict[str, str]) -> None:
    base_root = target_root / BASE_DIR
    for rp, content in rendered.items():
        bp = base_root / rp
        bp.parent.mkdir(parents=True, exist_ok=True)
        bp.write_text(content, encoding="utf-8")

def _build_checklist(create, update, rendered, root):
    cl = []
    if create: cl.append("新增文件可以直接接入。")
    nm = sum(1 for f in update if get_category(f) in ("three_way", "json_merge"))
    no = sum(1 for f in update if get_category(f) == "overwrite")
    ns = sum(1 for r in rendered if get_category(r) == "skip" and (root / r).exists())
    nb = sum(1 for f in update if get_category(f) == "three_way" and not (root / BASE_DIR / f).exists())
    if nm: cl.append(f"{nm} 个文件将三方合并（保留用户内容）。")
    if no: cl.append(f"{no} 个模板文件直接覆盖。")
    if ns: cl.append(f"{ns} 个用户数据文件已保护。")
    if nb: cl.append(f"⚠️ {nb} 个文件无基准版本，将备份后覆盖。")
    return cl or ["文件已是最新。"]


def plan_upgrade(
    target_root: Path,
    answers: dict[str, object],
    *,
    only_files: list[str] | None = None,
    _rendered: dict[str, str] | None = None,
) -> UpgradePlanResult:
    target_root = target_root.resolve()
    rendered = _rendered or _filter_rendered(_render_all(target_root, answers), only_files)

    create_files: list[str] = []
    update_files: list[str] = []
    unchanged_files: list[str] = []
    diffs: dict[str, str] = {}

    for relative_path, expected_content in rendered.items():
        cat = get_category(relative_path)
        path = target_root / relative_path

        if cat == "skip" and path.exists():
            unchanged_files.append(relative_path)
            continue

        if not path.exists():
            create_files.append(relative_path)
            continue

        current_content = path.read_text(encoding="utf-8")
        if current_content == expected_content:
            unchanged_files.append(relative_path)
        else:
            update_files.append(relative_path)
            diffs[relative_path] = _build_diff(relative_path, current_content, expected_content)

    checklist = _build_checklist(create_files, update_files, rendered, target_root)

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
    rendered = _filter_rendered(_render_all(target_root, answers), only_files)
    plan = plan_upgrade(target_root, answers, only_files=only_files, _rendered=rendered)
    changelog = _generate_changelog(plan)
    if dry_run:
        return UpgradeExecutionResult(target_root=str(target_root), created_files=plan.create_files, updated_files=plan.update_files, unchanged_files=plan.unchanged_files, selected_files=sorted(rendered.keys()), dry_run=True, changelog=changelog)
    progress_marker = target_root / ".agent-harness" / ".upgrade-in-progress"
    progress_marker.parent.mkdir(parents=True, exist_ok=True)
    progress_marker.touch()
    base_root = target_root / BASE_DIR
    backup_root: Path | None = None
    if plan.update_files:
        backup_root = target_root / ".agent-harness" / "backups" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    for rp in plan.update_files:
        src = target_root / rp
        if backup_root and src.exists():
            bp = backup_root / rp
            bp.parent.mkdir(parents=True, exist_ok=True)
            bp.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    # Process files by category
    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    merged: list[str] = []
    conflicts: dict[str, list[str]] = {}

    for rp in plan.create_files:
        output_path = target_root / rp
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered[rp], encoding="utf-8")
        created.append(rp)

    for rp in plan.update_files:
        cat = get_category(rp)
        output_path = target_root / rp
        new_content = rendered[rp]
        current = output_path.read_text(encoding="utf-8")
        base_path = base_root / rp
        try:
            base_content = base_path.read_text(encoding="utf-8") if base_path.exists() else ""
        except (UnicodeDecodeError, OSError):
            base_content = ""

        if cat == "overwrite":
            output_path.write_text(new_content, encoding="utf-8")
            updated.append(rp)
        elif cat == "three_way":
            if not base_path.exists():
                # No base dir at all: first upgrade after migration
                output_path.write_text(new_content, encoding="utf-8")
                updated.append(rp)
                conflicts[rp] = ["无基准版本，已用框架版本覆盖（备份至 backups/）"]
            elif not base_content:
                # Base exists but empty/corrupted: warn and overwrite
                output_path.write_text(new_content, encoding="utf-8")
                updated.append(rp)
                conflicts[rp] = ["基准文件损坏或为空，已用框架版本覆盖（备份至 backups/）"]
            else:
                result_text, conflict_list = merge3(base_content, current, new_content)
                output_path.write_text(result_text, encoding="utf-8")
                if conflict_list:
                    conflicts[rp] = conflict_list
                merged.append(rp)
        elif cat == "json_merge":
            result_text, warnings = json_merge(
                base_content, current, new_content,
                framework_keys=PROJECT_JSON_FW_KEYS,
            )
            output_path.write_text(result_text, encoding="utf-8")
            if warnings:
                conflicts[rp] = warnings
            merged.append(rp)

    for rp in rendered:
        if get_category(rp) == "skip" and (target_root / rp).exists() and rp not in plan.create_files:
            skipped.append(rp)

    save_base(target_root, rendered)
    progress_marker.unlink(missing_ok=True)
    cl_path = target_root / ".agent-harness" / "upgrade-changelog.md"
    cl_path.parent.mkdir(parents=True, exist_ok=True)
    cl_path.write_text(changelog, encoding="utf-8")
    return UpgradeExecutionResult(target_root=str(target_root), created_files=created,
        updated_files=updated, unchanged_files=plan.unchanged_files, skipped_files=skipped,
        merged_files=merged, conflicts=conflicts,
        backup_root=str(backup_root) if backup_root else None,
        selected_files=sorted(rendered.keys()), dry_run=False, changelog=changelog)


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
            unfilled = PLACEHOLDER_RE.findall(text)
            if unfilled:
                warnings.append(f"{md.name} 中存在未填充的占位符：{', '.join(unfilled[:3])}")
    # Check for unresolved merge conflict markers in all mergeable files
    marker = "<<<<<<< "
    for md in sorted(p for pat in ("**/*.md", "**/*.yml", "**/*.yaml", "**/*.py", "**/*.toml") for p in target_root.glob(pat)):
        rel = str(md.relative_to(target_root))
        if get_category(rel) in ("overwrite", "skip"):
            continue
        try:
            if marker in md.read_text(encoding="utf-8"):
                warnings.append(f"{rel} 中存在未解决的合并冲突标记")
        except (UnicodeDecodeError, OSError):
            pass
    return warnings
