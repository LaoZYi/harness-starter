from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "agent_harness"

REQUIRED_FILES = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "CLAUDE.md",
    ROOT / "scripts" / "plan_upgrade.py",
    ROOT / "scripts" / "apply_upgrade.py",
    ROOT / "scripts" / "init_project.py",
    ROOT / "examples" / "init-config.example.json",
    ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml",
    ROOT / "docs" / "product.md",
    ROOT / "docs" / "architecture.md",
    ROOT / "docs" / "workflow.md",
    ROOT / "docs" / "release.md",
    ROOT / "docs" / "runbook.md",
    ROOT / "src" / "agent_harness" / "cli.py",
    ROOT / "src" / "agent_harness" / "init_flow.py",
    ROOT / "src" / "agent_harness" / "doctor.py",
    ROOT / "src" / "agent_harness" / "export.py",
    ROOT / "src" / "agent_harness" / "stats.py",
    ROOT / "src" / "agent_harness" / "__main__.py",
    ROOT / "src" / "agent_harness" / "__init__.py",
    ROOT / "src" / "agent_harness" / "models.py",
    ROOT / "src" / "agent_harness" / "cli_utils.py",
    ROOT / "src" / "agent_harness" / "lang_detect.py",
    ROOT / "src" / "agent_harness" / "discovery.py",
    ROOT / "src" / "agent_harness" / "assessment.py",
    ROOT / "src" / "agent_harness" / "upgrade.py",
    ROOT / "src" / "agent_harness" / "templating.py",
    ROOT / "src" / "agent_harness" / "initializer.py",
    ROOT / "src" / "agent_harness" / "sync_render.py",
    ROOT / "src" / "agent_harness" / "audit.py",
    ROOT / "src" / "agent_harness" / "audit_cli.py",
    ROOT / "src" / "agent_harness" / "agent.py",
    ROOT / "src" / "agent_harness" / "agent_cli.py",
    PKG / "templates" / "common" / ".agent-harness" / "agents" / ".gitkeep.tmpl",
    ROOT / "tests" / "test_discovery.py",
    ROOT / "tests" / "test_assessment.py",
    ROOT / "tests" / "test_apply_upgrade.py",
    ROOT / "tests" / "test_upgrade.py",
    ROOT / "tests" / "test_initializer.py",
    ROOT / "tests" / "test_init_script.py",
    ROOT / "tests" / "test_cli.py",
    ROOT / "tests" / "test_lang_detect.py",
    ROOT / "tests" / "test_project_types.py",
    PKG / "templates" / "common" / "AGENTS.md.tmpl",
    PKG / "templates" / "common" / "CLAUDE.md.tmpl",
    PKG / "templates" / "common" / "CONTRIBUTING.md.tmpl",
    PKG / "templates" / "common" / ".github" / "PULL_REQUEST_TEMPLATE.md.tmpl",
    PKG / "templates" / "common" / ".github" / "ISSUE_TEMPLATE" / "bug_report.md.tmpl",
    PKG / "templates" / "common" / ".github" / "ISSUE_TEMPLATE" / "feature_request.md.tmpl",
    PKG / "templates" / "common" / ".github" / "ISSUE_TEMPLATE" / "config.yml.tmpl",
    PKG / "templates" / "common" / "docs" / "product.md.tmpl",
    PKG / "templates" / "common" / "docs" / "architecture.md.tmpl",
    PKG / "templates" / "common" / "docs" / "workflow.md.tmpl",
    PKG / "templates" / "common" / "docs" / "release.md.tmpl",
    PKG / "templates" / "common" / "docs" / "runbook.md.tmpl",
    PKG / "templates" / "common" / ".claude" / "rules" / "safety.md.tmpl",
    PKG / "templates" / "common" / ".claude" / "rules" / "database.md.tmpl",
    PKG / "templates" / "common" / ".claude" / "rules" / "api.md.tmpl",
    PKG / "templates" / "common" / ".claude" / "rules" / "testing.md.tmpl",
    PKG / "templates" / "common" / ".claude" / "rules" / "autonomy.md.tmpl",
    PKG / "templates" / "common" / "CLAUDE.local.md.example.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "current-task.md.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "lessons.md.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "task-log.md.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "init-summary.md.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "project.json.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "memory-index.md.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "references" / "accessibility-checklist.md.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "references" / "performance-checklist.md.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "references" / "security-checklist.md.tmpl",
    PKG / "templates" / "common" / ".agent-harness" / "references" / "testing-patterns.md.tmpl",
    PKG / "templates" / "common" / ".claude" / "hooks" / "session-start.sh.tmpl",
    PKG / "templates" / "common" / ".claude" / "hooks" / "stop.sh.tmpl",
    PKG / "templates" / "common" / ".claude" / "hooks" / "pre-compact.sh.tmpl",
    PKG / "templates" / "common" / ".claude" / "commands" / "recall.md.tmpl",
    PKG / "templates" / "common" / ".claude" / "commands" / "source-verify.md.tmpl",
    PKG / "templates" / "superpowers" / ".claude" / "commands" / "adr.md.tmpl",
    PKG / "templates" / "superpowers" / "docs" / "decisions" / ".gitkeep.tmpl",
    PKG / "presets" / "backend-service.json",
    PKG / "presets" / "web-app.json",
    PKG / "presets" / "cli-tool.json",
    PKG / "presets" / "library.json",
    PKG / "presets" / "worker.json",
    PKG / "presets" / "mobile-app.json",
    PKG / "presets" / "monorepo.json",
    PKG / "presets" / "data-pipeline.json",
    PKG / "presets" / "meta.json",
    ROOT / "VERSION",
]

MARKDOWN_LINK_PATTERN = re.compile(r"`([^`]+\.md)`")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def check_required_files() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    assert_true(not missing, f"缺少关键文件: {', '.join(missing)}")


def check_agents_length() -> None:
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    line_count = len(agents_text.splitlines())
    assert_true(line_count <= 120, f"AGENTS.md 过长: {line_count} 行")


def check_adapter_files_point_to_agents() -> None:
    claude_text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert_true("AGENTS.md" in claude_text, "CLAUDE.md 必须引用 AGENTS.md")


def check_markdown_references() -> None:
    skip_prefixes = (".agent-harness/", ".claude/", ".github/", ".harness-plugins/")
    for path in [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "CLAUDE.md", ROOT / "CONTRIBUTING.md"]:
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_PATTERN.findall(text):
            if any(match.startswith(p) for p in skip_prefixes):
                continue
            target = ROOT / match
            assert_true(target.exists(), f"{path.name} 引用了不存在的文档: {match}")


def check_command_surface() -> None:
    makefile_text = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("check:", "test:", "ci:", "assess:", "upgrade-plan:", "upgrade-apply:", "init:"):
        assert_true(target in makefile_text, f"Makefile 缺少目标: {target[:-1]}")


def check_module_sizes() -> None:
    """Enforce the 280-line hard limit on every source file under src/agent_harness/.

    Auto-discovery (not a hardcoded whitelist): any new .py added under the
    package — including sub-packages like squad/ — is checked automatically.
    Excludes __init__.py and templates/ (template files are data, not code).
    """
    for path in sorted(PKG.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            path.relative_to(PKG / "templates")
            continue
        except ValueError:
            pass
        relative_path = path.relative_to(ROOT).as_posix()
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        assert_true(line_count <= 280, f"{relative_path} 过长: {line_count} 行")


def check_runbook_mentions_main_commands() -> None:
    runbook_text = (ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
    for command in (
        "make check",
        "make test",
        "make ci",
        "make assess",
        "make upgrade-plan",
        "make upgrade-apply",
        "make init",
    ):
        assert_true(command in runbook_text, f"运行手册缺少命令说明: {command}")


def check_github_templates() -> None:
    pr_text = (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    bug_text = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md").read_text(encoding="utf-8")
    feature_text = (ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md").read_text(encoding="utf-8")
    assert_true("make check" in pr_text, "PR 模板必须要求验证命令")
    assert_true("docs/product.md" in bug_text, "Bug 模板必须指向仓库文档")
    assert_true("验收标准" in feature_text, "功能模板必须要求验收标准")


def check_framework_has_no_sample_service() -> None:
    sample_root = ROOT / "src" / "ticket_router"
    sample_sources = list(sample_root.glob("*.py")) if sample_root.exists() else []
    assert_true(not sample_sources, "框架仓库不应保留样例业务代码")


def check_example_config_is_valid_json() -> None:
    import json

    config_text = (ROOT / "examples" / "init-config.example.json").read_text(encoding="utf-8")
    data = json.loads(config_text)
    for key in ("project_name", "project_type", "run_command", "test_command", "check_command", "ci_command"):
        assert_true(key in data, f"示例配置缺少字段: {key}")


def check_dogfood_drift() -> None:
    """Detect if skill/rule templates changed but generated files were not re-synced.

    Only checks .claude/commands/, .claude/rules/, and .claude/settings.json —
    these are purely template-generated. Docs and other files may have manual edits.
    """
    import json
    pj = ROOT / ".agent-harness" / "project.json"
    if not pj.exists():
        return  # dogfood not applied yet, skip
    sys.path.insert(0, str(ROOT / "src"))
    from agent_harness.initializer import SUPERPOWERS_ROOT, TEMPLATE_ROOT, prepare_initialization
    from agent_harness.templating import render_templates
    answers = json.loads(pj.read_text(encoding="utf-8"))
    answers["project_name"] = answers.get("project_name", "")
    answers["summary"] = answers.get("project_summary", "")
    if "commands" in answers and isinstance(answers["commands"], dict):
        cmds = answers["commands"]
        answers.setdefault("run_command", cmds.get("run", "TODO"))
        answers.setdefault("test_command", cmds.get("test", "TODO"))
        answers.setdefault("check_command", cmds.get("check", "TODO"))
        answers.setdefault("ci_command", cmds.get("ci", "TODO"))
    _, _, context = prepare_initialization(ROOT, answers)
    rendered = render_templates(TEMPLATE_ROOT, context)
    if SUPERPOWERS_ROOT.is_dir():
        from agent_harness.skills_registry import apply_to_rendered_dict  # Issue #27
        sp_rendered = render_templates(SUPERPOWERS_ROOT, context)
        apply_to_rendered_dict(SUPERPOWERS_ROOT, sp_rendered)
        rendered.update(sp_rendered)
    check_prefixes = (".claude/commands/", ".claude/rules/", ".claude/hooks/", ".claude/settings.json")
    drifted = []
    for rel_path, expected in rendered.items():
        if not any(rel_path.startswith(p) for p in check_prefixes):
            continue
        actual_path = ROOT / rel_path
        if not actual_path.exists():
            drifted.append(f"  缺失: {rel_path}")
        elif actual_path.read_text(encoding="utf-8") != expected:
            drifted.append(f"  过时: {rel_path}")
    if drifted:
        detail = "\n".join(drifted[:5])
        hint = "运行 make dogfood 同步"
        raise SystemExit(f"技能/规则模板已变更但生成产物未同步（{len(drifted)} 个文件）：\n{detail}\n{hint}")


def check_count_consistency() -> None:
    """Ensure hardcoded test/skill counts match reality."""
    # --- actual test count (count def test_ methods in test files) ---
    test_method_re = re.compile(r"^\s+def test_", re.MULTILINE)
    actual_tests = 0
    for tf in sorted((ROOT / "tests").glob("test_*.py")):
        actual_tests += len(test_method_re.findall(tf.read_text(encoding="utf-8")))

    # --- actual skill count ---
    skill_dir = PKG / "templates" / "superpowers" / ".claude" / "commands"
    actual_skills = len(list(skill_dir.glob("*.md.tmpl")))

    # --- scan files for stale counts ---
    scan_files = [
        ROOT / "AGENTS.md", ROOT / "CONTRIBUTING.md", ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "docs" / "product.md", ROOT / "docs" / "architecture.md",
        ROOT / "docs" / "usage-guide.md", ROOT / "docs" / "runbook.md",
        ROOT / "docs" / "release.md", ROOT / "docs" / "workflow.md",
        ROOT / ".agent-harness" / "project.json",
    ]
    test_re = re.compile(r"(\d+)\s*个(?:回归)?测试")
    skill_re = re.compile(r"(\d+)\s*个(?:工作流)?技能(?:命令|模板)?")

    errors: list[str] = []
    for path in scan_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT))
        for m in test_re.finditer(text):
            found = int(m.group(1))
            if found != actual_tests:
                errors.append(f"  {rel}: 写了 {found} 个测试，实际 {actual_tests}")
        for m in skill_re.finditer(text):
            found = int(m.group(1))
            if found != actual_skills:
                errors.append(f"  {rel}: 写了 {found} 个技能，实际 {actual_skills}")
    if errors:
        detail = "\n".join(errors[:10])
        raise SystemExit(f"文档中的计数与实际不一致：\n{detail}")


def check_skill_documentation_coverage() -> None:
    """Every skill must appear in key documentation files."""
    skill_dir = PKG / "templates" / "superpowers" / ".claude" / "commands"
    skills = sorted(
        "/" + f.stem.removesuffix(".md")
        for f in skill_dir.glob("*.md.tmpl")
    )

    # Files where every skill must be mentioned (as /skill-name)
    # README is excluded — it's a summary that groups skills by category
    must_mention_all = {
        "workflow rule": PKG / "templates" / "superpowers" / ".claude" / "rules" / "superpowers-workflow.md.tmpl",
        "decision tree": PKG / "templates" / "superpowers" / ".claude" / "commands" / "use-superpowers.md.tmpl",
        "evolve comparison": PKG / "templates" / "superpowers" / ".claude" / "commands" / "evolve.md.tmpl",
        "usage-guide": ROOT / "docs" / "usage-guide.md",
    }

    errors: list[str] = []
    for label, path in must_mention_all.items():
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        # Issue #27: use-superpowers.md.tmpl uses <<SKILL_*>> placeholders.
        # Render via skills_registry so the decision-tree check sees actual skill names.
        if label == "decision tree":
            from agent_harness.skills_registry import load_registry, render_all
            try:
                content = render_all(content, load_registry(PKG / "templates" / "superpowers"))
            except (FileNotFoundError, ValueError):
                pass
        for skill in skills:
            if skill == "/use-superpowers" and label == "decision tree":
                continue
            if skill not in content:
                errors.append(f"  {label}: 缺少 {skill}")

    # Check that every directory created by superpowers templates is documented in usage-guide file tree
    superpowers_tmpl = PKG / "templates" / "superpowers"
    gitkeep_dirs = set()
    for gk in superpowers_tmpl.rglob(".gitkeep.tmpl"):
        rel = str(gk.parent.relative_to(superpowers_tmpl))
        gitkeep_dirs.add(rel)

    if gitkeep_dirs:
        usage_guide = ROOT / "docs" / "usage-guide.md"
        if usage_guide.exists():
            ug_content = usage_guide.read_text(encoding="utf-8")
            for d in sorted(gitkeep_dirs):
                # Check the last component of the path appears in the file tree
                dirname = d.split("/")[-1]
                if dirname not in ug_content:
                    errors.append(f"  usage-guide 文件树: 缺少目录 {d}")

    if errors:
        detail = "\n".join(errors[:15])
        raise SystemExit(f"技能文档覆盖不完整：\n{detail}")


def main() -> None:
    check_required_files()
    check_agents_length()
    check_adapter_files_point_to_agents()
    check_markdown_references()
    check_command_surface()
    check_module_sizes()
    check_runbook_mentions_main_commands()
    check_github_templates()
    check_framework_has_no_sample_service()
    check_example_config_is_valid_json()
    check_dogfood_drift()
    check_count_consistency()
    check_skill_documentation_coverage()
    print("repository checks passed")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
