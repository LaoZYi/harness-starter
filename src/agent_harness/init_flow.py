"""Interactive and non-interactive init flows, extracted from cli.py."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Callable

import questionary

from ._shared import slugify
from .cli_utils import LANGUAGE_DEFAULTS, console, print_detected
from .models import ProjectProfile
from rich.panel import Panel
from rich.table import Table

SCAFFOLD_SKIP = {".git", "node_modules", ".venv", "__pycache__", ".DS_Store", ".agent-harness"}

PROJECT_TYPE_CHOICES = [
    "backend-service", "web-app", "cli-tool", "library",
    "worker", "mobile-app", "monorepo", "data-pipeline", "meta",
]
SENSITIVITY_CHOICES = ["standard", "internal", "high"]


def copy_scaffold(scaffold: Path, target: Path) -> int:
    """Copy scaffold directory to target, skipping common non-essential dirs. Returns file count."""
    scaffold = scaffold.resolve()
    if not scaffold.is_dir():
        raise SystemExit(f"错误：框架路径不存在或不是目录：{scaffold}")
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for src in sorted(scaffold.rglob("*")):
        if src.is_symlink():
            continue
        rel = src.relative_to(scaffold)
        if any(part in SCAFFOLD_SKIP for part in rel.parts):
            continue
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            count += 1
    return count



def _lang_default(lang_defs: dict[str, str], key: str, profile_val: str, slug: str) -> str:
    if profile_val and profile_val not in ("TODO", "unknown", "未定"):
        return profile_val
    tmpl = lang_defs.get(key, profile_val)
    return tmpl.replace("{slug}", slug) if tmpl else profile_val


def ask_scaffold(target: Path) -> bool:
    """Ask user if they want to scaffold from an existing framework. Returns True if scaffold was applied."""
    answer = questionary.select("是否基于现有技术框架创建", choices=["否，空项目", "是，指定框架路径"], default="否，空项目").ask()
    if answer is None:
        raise SystemExit(1)
    if answer.startswith("否"):
        return False
    scaffold_path = questionary.path("框架路径", only_directories=True, validate=lambda v: Path(v).expanduser().is_dir() or "路径不存在").ask()
    if scaffold_path is None:
        raise SystemExit(1)
    scaffold = Path(scaffold_path).expanduser().resolve()
    count = copy_scaffold(scaffold, target)
    console.print(f"  [green]已复制框架代码[/green]：{count} 个文件来自 {scaffold.name}")
    return True


_BACK = "↩ 返回上一步"

_STEP_LABELS = ["项目名称", "一句话目标", "项目类型", "敏感级别", "生产环境"]


def _ask_with_back(message: str, choices: list[str], default: str, *, allow_back: bool = True) -> str | None:
    """Ask a select question, optionally with a back option. Returns None on Ctrl-C, _BACK on back."""
    opts = list(choices) + ([_BACK] if allow_back else [])
    return questionary.select(message, choices=opts, default=default).ask()


def interactive_init(target: Path, profile: ProjectProfile, config: dict[str, object]) -> dict[str, object]:
    console.print("\n[bold]项目初始化[/bold]\n")

    default_type = profile.project_type if profile.project_type in PROJECT_TYPE_CHOICES else "backend-service"
    collected: dict[str, str] = {}
    step = 0

    max_step = 4
    while step <= max_step:
        match step:
            case 0:
                val = questionary.text(
                    "项目名称",
                    default=collected.get("project_name", ""),
                    validate=lambda v: bool(v.strip()) or "不能为空",
                ).ask()
                if val is None:
                    raise SystemExit(1)
                collected["project_name"] = val.strip()
                step += 1

            case 1:
                val = questionary.text(
                    "一句话目标",
                    default=collected.get("summary", ""),
                    validate=lambda v: bool(v.strip()) or "不能为空",
                ).ask()
                if val is None:
                    raise SystemExit(1)
                collected["summary"] = val.strip()
                step += 1

            case 2:
                val = _ask_with_back(
                    "项目类型",
                    PROJECT_TYPE_CHOICES,
                    default=collected.get("project_type", default_type),
                )
                if val is None:
                    raise SystemExit(1)
                if val == _BACK:
                    step -= 1
                    continue
                collected["project_type"] = val
                if val == "meta":
                    # Meta repo 没有生产环境，跳过敏感级别和生产环境问题
                    collected["sensitivity"] = "standard"
                    collected["has_production_raw"] = "否"
                    max_step = 2  # 到此结束
                else:
                    max_step = 4
                step += 1

            case 3:
                val = _ask_with_back(
                    "敏感级别",
                    SENSITIVITY_CHOICES,
                    default=collected.get("sensitivity", "standard"),
                )
                if val is None:
                    raise SystemExit(1)
                if val == _BACK:
                    step -= 1
                    continue
                collected["sensitivity"] = val
                step += 1

            case 4:
                val = _ask_with_back(
                    "是否已有生产环境",
                    ["否", "是"],
                    default=collected.get("has_production_raw", "否"),
                )
                if val is None:
                    raise SystemExit(1)
                if val == _BACK:
                    step -= 1
                    continue
                collected["has_production_raw"] = val
                step += 1

    # -- 确认环节 --
    visible_steps = _STEP_LABELS[:3] if collected.get("project_type") == "meta" else _STEP_LABELS
    while True:
        console.print()
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim")
        table.add_column(style="cyan")
        for i, label in enumerate(visible_steps):
            if label == "生产环境":
                table.add_row(f"[{i}] {label}", collected.get("has_production_raw", "否"))
            else:
                key = ["project_name", "summary", "project_type", "sensitivity"][i]
                table.add_row(f"[{i}] {label}", str(collected.get(key, "")))
        console.print(Panel(table, title="[bold]初始化配置[/bold]", border_style="blue"))

        confirm_choices = ["✓ 确认继续"] + [f"修改 [{i}] {label}" for i, label in enumerate(visible_steps)]
        choice = questionary.select("确认或修改", choices=confirm_choices).ask()
        if choice is None:
            raise SystemExit(1)
        if choice.startswith("✓"):
            break
        # 跳回对应步骤
        for i in range(len(visible_steps)):
            if f"[{i}]" in choice:
                step = i
                break
        # 只执行一步后回到确认
        match step:
            case 0:
                val = questionary.text("项目名称", default=collected.get("project_name", ""), validate=lambda v: bool(v.strip()) or "不能为空").ask()
                if val is not None:
                    collected["project_name"] = val.strip()
            case 1:
                val = questionary.text("一句话目标", default=collected.get("summary", ""), validate=lambda v: bool(v.strip()) or "不能为空").ask()
                if val is not None:
                    collected["summary"] = val.strip()
            case 2:
                val = questionary.select("项目类型", choices=PROJECT_TYPE_CHOICES, default=collected.get("project_type", default_type)).ask()
                if val is not None:
                    collected["project_type"] = val
                    if val == "meta":
                        collected["sensitivity"] = "standard"
                        collected["has_production_raw"] = "否"
                    visible_steps = _STEP_LABELS[:3] if collected.get("project_type") == "meta" else _STEP_LABELS
            case 3:
                val = questionary.select("敏感级别", choices=SENSITIVITY_CHOICES, default=collected.get("sensitivity", "standard")).ask()
                if val is not None:
                    collected["sensitivity"] = val
            case 4:
                val = questionary.select("是否已有生产环境", choices=["否", "是"], default=collected.get("has_production_raw", "否")).ask()
                if val is not None:
                    collected["has_production_raw"] = val

    # -- 组装 answers --
    name = collected["project_name"]
    slug = slugify(name)
    has_production = collected.get("has_production_raw") == "是"
    lang = profile.language or "unknown"
    lang_defs = LANGUAGE_DEFAULTS.get(lang, {})

    answers: dict[str, object] = {
        "project_name": name,
        "project_slug": slug,
        "summary": collected["summary"],
        "project_type": collected["project_type"],
        "sensitivity": collected["sensitivity"],
        "has_production": has_production,
        "language": lang,
        "package_manager": _lang_default(lang_defs, "package_manager", profile.package_manager, slug),
        "run_command": _lang_default(lang_defs, "run_command", profile.run_command, slug),
        "test_command": _lang_default(lang_defs, "test_command", profile.test_command, slug),
        "check_command": _lang_default(lang_defs, "check_command", profile.check_command, slug),
        "ci_command": _lang_default(lang_defs, "ci_command", profile.ci_command, slug),
        "deploy_target": profile.deploy_target,
    }
    for ek in ("description", "features", "constraints", "done_criteria"):
        if ek in config:
            answers[ek] = config[ek]
    answers["superpowers"] = config.get("superpowers", True)

    print_detected(answers)
    return answers


def non_interactive_init(
    args: argparse.Namespace,
    profile: ProjectProfile,
    config: dict[str, object],
    resolve_answers_fn: Callable[[argparse.Namespace, ProjectProfile, dict[str, object]], dict[str, object]],
) -> dict[str, object]:
    answers = resolve_answers_fn(args, profile, config)
    lang = str(answers.get("language", "unknown"))
    lang_defs = LANGUAGE_DEFAULTS.get(lang, {})
    slug = str(answers.get("project_slug", "project"))
    for key in ("package_manager", "run_command", "test_command", "check_command", "ci_command"):
        if answers.get(key) in (None, "TODO", "unknown"):
            answers[key] = _lang_default(lang_defs, key, str(answers.get(key, "TODO")), slug)
    for ek in ("description", "features", "constraints", "done_criteria"):
        cv = getattr(args, ek, None)
        if cv is not None:
            answers[ek] = cv
        elif ek in config:
            answers[ek] = config[ek]
    answers["superpowers"] = config.get("superpowers", True)
    return answers
