from __future__ import annotations

from pathlib import Path

from .initializer import TEMPLATE_ROOT, prepare_initialization
from .models import UpgradePlanResult
from .templating import render_templates


def plan_upgrade(target_root: Path, answers: dict[str, object]) -> UpgradePlanResult:
    target_root = target_root.resolve()
    _, _, context = prepare_initialization(target_root, answers)
    rendered = render_templates(TEMPLATE_ROOT, context)

    create_files: list[str] = []
    update_files: list[str] = []
    unchanged_files: list[str] = []

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
    )
