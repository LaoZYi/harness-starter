"""Interactive and non-interactive init flows, extracted from cli.py."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import questionary

from .cli_utils import LANGUAGE_DEFAULTS, console, print_detected

SCAFFOLD_SKIP = {".git", "node_modules", ".venv", "__pycache__", ".DS_Store", ".agent-harness"}

PROJECT_TYPE_CHOICES = [
    "backend-service", "web-app", "cli-tool", "library",
    "worker", "mobile-app", "monorepo", "data-pipeline",
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


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-") or "project"


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


def interactive_init(target: Path, profile: object, config: dict[str, object]) -> dict[str, object]:
    console.print("\n[bold]项目初始化[/bold]\n")
    name = questionary.text("项目名称", validate=lambda v: bool(v.strip()) or "不能为空").ask()
    if name is None:
        raise SystemExit(1)
    slug = _slugify(name)
    summary = questionary.text("一句话目标", validate=lambda v: bool(v.strip()) or "不能为空").ask()
    if summary is None:
        raise SystemExit(1)
    default_type = profile.project_type if profile.project_type in PROJECT_TYPE_CHOICES else "backend-service"
    project_type = questionary.select("项目类型", choices=PROJECT_TYPE_CHOICES, default=default_type).ask()
    if project_type is None:
        raise SystemExit(1)
    sensitivity = questionary.select("敏感级别", choices=SENSITIVITY_CHOICES, default="standard").ask()
    if sensitivity is None:
        raise SystemExit(1)
    has_prod_answer = questionary.select("是否已有生产环境", choices=["否", "是"], default="否").ask()
    if has_prod_answer is None:
        raise SystemExit(1)
    has_production = has_prod_answer == "是"

    lang = profile.language or "unknown"
    lang_defs = LANGUAGE_DEFAULTS.get(lang, {})

    answers: dict[str, object] = {
        "project_name": name,
        "project_slug": slug,
        "summary": summary,
        "project_type": project_type,
        "sensitivity": sensitivity,
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

    print_detected(answers)
    return answers


def non_interactive_init(
    args: argparse.Namespace,
    profile: object,
    config: dict[str, object],
    resolve_answers_fn: object,
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
    return answers
