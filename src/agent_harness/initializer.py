from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from .assessment import assess_project
from .discovery import discover_project
from .models import InitializationResult
from .templating import materialize_templates

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "templates" / "common"
PRESET_ROOT = REPO_ROOT / "presets"
FRAMEWORK_VERSION = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def _load_preset(project_type: str) -> dict[str, object]:
    path = PRESET_ROOT / f"{project_type}.json"
    if not path.exists():
        path = PRESET_ROOT / "backend-service.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-") or "project"


def _bullet_list(items: list[str], *, fallback: str) -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- `{item}`" for item in items)


def _inline_list(items: list[str], *, fallback: str) -> str:
    if not items:
        return fallback
    return ", ".join(f"`{item}`" for item in items)


def _json_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _auto_done_criteria(features_raw: str, preset: dict[str, object]) -> str:
    items: list[str] = []
    if features_raw:
        for f in features_raw.replace(",", "\n").splitlines():
            f = f.strip()
            if f:
                items.append(f"功能「{f}」已实现并可正常工作")
    preset_criteria = preset.get("default_done_criteria")
    if isinstance(preset_criteria, list):
        items.extend(str(c) for c in preset_criteria)
    if not items:
        return "（初始化时未提供功能列表和完成标准，agent 应在实现功能后自行生成验收清单）"
    return "\n".join(f"- [ ] {item}" for item in items)


def prepare_initialization(target_root: Path, answers: dict[str, object]) -> tuple[object, object, dict[str, str]]:
    target_root = target_root.resolve()
    profile = discover_project(target_root)
    project_name = str(answers.get("project_name") or profile.project_name or target_root.name)
    project_slug = str(answers.get("project_slug") or profile.project_slug or _slugify(project_name))
    project_type = str(answers.get("project_type") or profile.project_type)
    preset = _load_preset(project_type)

    summary = str(answers.get("summary") or profile.summary or "待补充项目目标")
    language = str(answers.get("language") or profile.language or "unknown")
    package_manager = str(answers.get("package_manager") or profile.package_manager or "unknown")
    run_command = str(answers.get("run_command") or profile.run_command or "TODO")
    test_command = str(answers.get("test_command") or profile.test_command or "TODO")
    check_command = str(answers.get("check_command") or profile.check_command or "TODO")
    ci_command = str(answers.get("ci_command") or profile.ci_command or "TODO")
    deploy_target = str(answers.get("deploy_target") or profile.deploy_target or "未定")
    has_production = bool(answers.get("has_production") if "has_production" in answers else profile.has_production)
    sensitivity = str(answers.get("sensitivity") or profile.sensitivity or "standard")
    effective_profile = replace(
        profile,
        project_name=project_name,
        project_slug=project_slug,
        summary=summary,
        project_type=project_type,
        language=language,
        package_manager=package_manager,
        run_command=run_command,
        test_command=test_command,
        check_command=check_command,
        ci_command=ci_command,
        deploy_target=deploy_target,
        has_production=has_production,
        sensitivity=sensitivity,
    )
    assessment = assess_project(effective_profile, root=target_root)

    description = str(answers.get("description") or "")
    features_raw = str(answers.get("features") or "").replace("\\n", "\n")
    constraints_raw = str(answers.get("constraints") or "").replace("\\n", "\n")

    if features_raw:
        items = [f.strip() for f in features_raw.replace(",", "\n").splitlines() if f.strip()]
        features_bullets = "\n".join(f"- {item}" for item in items)
    else:
        features_bullets = "（agent 在实现功能后自动填充此节，每条功能用一行描述）"

    if constraints_raw:
        items = [c.strip() for c in constraints_raw.replace(",", "\n").splitlines() if c.strip()]
        constraints_bullets = "\n".join(f"- {item}" for item in items)
    else:
        constraints_bullets = ""

    done_raw = str(answers.get("done_criteria") or "").replace("\\n", "\n")
    if done_raw:
        items = [d.strip() for d in done_raw.replace(",", "\n").splitlines() if d.strip()]
        done_criteria_bullets = "\n".join(f"- [ ] {item}" for item in items)
    else:
        done_criteria_bullets = _auto_done_criteria(features_raw, preset)

    context = {
        "project_name": project_name,
        "project_slug": project_slug,
        "project_summary": summary,
        "project_type": project_type,
        "language": language,
        "package_manager": package_manager,
        "run_command": run_command,
        "test_command": test_command,
        "check_command": check_command,
        "ci_command": ci_command,
        "deploy_target": deploy_target,
        "has_production": "true" if has_production else "false",
        "production_status": "已有生产环境" if has_production else "暂未接入生产环境",
        "sensitivity": sensitivity,
        "source_paths_bullets": _bullet_list(profile.source_paths, fallback="待补充源码目录"),
        "test_paths_bullets": _bullet_list(profile.test_paths, fallback="待补充测试目录"),
        "docs_paths_bullets": _bullet_list(profile.docs_paths, fallback="待补充文档目录"),
        "ci_paths_bullets": _bullet_list(profile.ci_paths, fallback="待补充 CI 入口"),
        "external_systems_bullets": _bullet_list(profile.external_systems, fallback="当前未探测到显式外部系统"),
        "notes_bullets": _bullet_list(profile.notes, fallback="当前探测结果可直接作为第一版初始化信息"),
        "assessment_score": str(assessment.score),
        "assessment_readiness": assessment.readiness,
        "assessment_strengths_bullets": _bullet_list(assessment.strengths, fallback="当前没有额外优势项"),
        "assessment_gaps_bullets": _bullet_list(assessment.gaps, fallback="当前没有明显缺口"),
        "assessment_recommendations_bullets": _bullet_list(
            assessment.recommendations,
            fallback="初始化完成后可以直接开始补充项目细节。",
        ),
        "assessment_confidence": assessment.confidence,
        "project_description": description,
        "features_bullets": features_bullets,
        "constraints_bullets": constraints_bullets,
        "done_criteria_bullets": done_criteria_bullets,
        "harness_version": FRAMEWORK_VERSION,
        "source_paths_inline": _inline_list(profile.source_paths, fallback="待补充"),
        "test_paths_inline": _inline_list(profile.test_paths, fallback="待补充"),
        "docs_paths_inline": _inline_list(profile.docs_paths, fallback="待补充"),
        "ci_paths_inline": _inline_list(profile.ci_paths, fallback="待补充"),
        "behavior_change_definition": str(preset["behavior_change_definition"]),
        "architecture_focus": str(preset["architecture_focus"]),
        "release_checks_bullets": _bullet_list(list(preset["release_checks"]), fallback="待补充发布检查项"),
        "workflow_notes": str(preset["workflow_notes"]),
        "project_name_json": _json_value(project_name),
        "project_slug_json": _json_value(project_slug),
        "project_summary_json": _json_value(summary),
        "project_type_json": _json_value(project_type),
        "language_json": _json_value(language),
        "package_manager_json": _json_value(package_manager),
        "run_command_json": _json_value(run_command),
        "test_command_json": _json_value(test_command),
        "check_command_json": _json_value(check_command),
        "ci_command_json": _json_value(ci_command),
        "deploy_target_json": _json_value(deploy_target),
        "has_production_json": _json_value(has_production),
        "sensitivity_json": _json_value(sensitivity),
        "source_paths_json": _json_value(profile.source_paths),
        "test_paths_json": _json_value(profile.test_paths),
        "docs_paths_json": _json_value(profile.docs_paths),
        "ci_paths_json": _json_value(profile.ci_paths),
        "external_systems_json": _json_value(profile.external_systems),
        "notes_json": _json_value(profile.notes),
    }
    return profile, assessment, context


def initialize_project(
    target_root: Path,
    answers: dict[str, object],
    *,
    force: bool = False,
    dry_run: bool = False,
) -> InitializationResult:
    target_root = target_root.resolve()
    if not dry_run:
        target_root.mkdir(parents=True, exist_ok=True)
    _, _, context = prepare_initialization(target_root, answers)

    written, skipped = materialize_templates(
        TEMPLATE_ROOT,
        target_root,
        context,
        force=force,
        dry_run=dry_run,
    )

    plugin_root = target_root / ".harness-plugins"
    if plugin_root.is_dir():
        pw, ps = _materialize_plugins(plugin_root, target_root, context, force=force, dry_run=dry_run)
        written.extend(pw)
        skipped.extend(ps)

    return InitializationResult(
        target_root=str(target_root),
        context=context,
        written_files=written,
        skipped_files=skipped,
        dry_run=dry_run,
        summary_path=".agent-harness/init-summary.md",
    )


def _materialize_plugins(
    plugin_root: Path,
    target_root: Path,
    context: dict[str, str],
    *,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[list[str], list[str]]:
    from .templating import render_template

    written: list[str] = []
    skipped: list[str] = []

    # rules/ → .claude/rules/
    rules_dir = plugin_root / "rules"
    if rules_dir.is_dir():
        for f in sorted(rules_dir.glob("*.md")):
            output_rel = f".claude/rules/{f.name}"
            output_path = target_root / output_rel
            content = render_template(f.read_text(encoding="utf-8"), context)
            if output_path.exists() and not force:
                skipped.append(output_rel)
            else:
                if not dry_run:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(content, encoding="utf-8")
                written.append(output_rel)

    # templates/ → project root (preserving subdirectory structure)
    tmpl_dir = plugin_root / "templates"
    if tmpl_dir.is_dir():
        for f in sorted(tmpl_dir.rglob("*")):
            if f.is_dir():
                continue
            output_rel = str(f.relative_to(tmpl_dir))
            output_path = target_root / output_rel
            content = render_template(f.read_text(encoding="utf-8"), context)
            if output_path.exists() and not force:
                skipped.append(output_rel)
            else:
                if not dry_run:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(content, encoding="utf-8")
                written.append(output_rel)

    return written, skipped
