from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "CLAUDE.md",
    ROOT / "scripts" / "discover_project.py",
    ROOT / "scripts" / "assess_project.py",
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
    ROOT / "src" / "agent_harness" / "__init__.py",
    ROOT / "src" / "agent_harness" / "models.py",
    ROOT / "src" / "agent_harness" / "discovery.py",
    ROOT / "src" / "agent_harness" / "assessment.py",
    ROOT / "src" / "agent_harness" / "upgrade.py",
    ROOT / "src" / "agent_harness" / "templating.py",
    ROOT / "src" / "agent_harness" / "initializer.py",
    ROOT / "tests" / "test_discovery.py",
    ROOT / "tests" / "test_assessment.py",
    ROOT / "tests" / "test_apply_upgrade.py",
    ROOT / "tests" / "test_upgrade.py",
    ROOT / "tests" / "test_initializer.py",
    ROOT / "tests" / "test_init_script.py",
    ROOT / "templates" / "common" / "AGENTS.md.tmpl",
    ROOT / "templates" / "common" / "CLAUDE.md.tmpl",
    ROOT / "templates" / "common" / "CONTRIBUTING.md.tmpl",
    ROOT / "templates" / "common" / ".github" / "PULL_REQUEST_TEMPLATE.md.tmpl",
    ROOT / "templates" / "common" / ".github" / "ISSUE_TEMPLATE" / "bug_report.md.tmpl",
    ROOT / "templates" / "common" / ".github" / "ISSUE_TEMPLATE" / "feature_request.md.tmpl",
    ROOT / "templates" / "common" / ".github" / "ISSUE_TEMPLATE" / "config.yml.tmpl",
    ROOT / "templates" / "common" / "docs" / "product.md.tmpl",
    ROOT / "templates" / "common" / "docs" / "architecture.md.tmpl",
    ROOT / "templates" / "common" / "docs" / "workflow.md.tmpl",
    ROOT / "templates" / "common" / "docs" / "release.md.tmpl",
    ROOT / "templates" / "common" / "docs" / "runbook.md.tmpl",
    ROOT / "templates" / "common" / ".agent-harness" / "init-summary.md.tmpl",
    ROOT / "templates" / "common" / ".agent-harness" / "project.json.tmpl",
    ROOT / "presets" / "backend-service.json",
    ROOT / "presets" / "web-app.json",
    ROOT / "presets" / "cli-tool.json",
    ROOT / "presets" / "library.json",
    ROOT / "presets" / "worker.json",
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
    for path in [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "CLAUDE.md", ROOT / "CONTRIBUTING.md"]:
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_PATTERN.findall(text):
            target = ROOT / match
            assert_true(target.exists(), f"{path.name} 引用了不存在的文档: {match}")


def check_command_surface() -> None:
    makefile_text = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("check:", "test:", "ci:", "discover:", "assess:", "upgrade-plan:", "upgrade-apply:", "init:"):
        assert_true(target in makefile_text, f"Makefile 缺少目标: {target[:-1]}")


def check_module_sizes() -> None:
    for relative_path in [
        "src/agent_harness/discovery.py",
        "src/agent_harness/assessment.py",
        "src/agent_harness/upgrade.py",
        "src/agent_harness/initializer.py",
        "src/agent_harness/templating.py",
    ]:
        path = ROOT / relative_path
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        assert_true(line_count <= 280, f"{relative_path} 过长: {line_count} 行")


def check_runbook_mentions_main_commands() -> None:
    runbook_text = (ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
    for command in (
        "make check",
        "make test",
        "make ci",
        "make discover",
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
    print("repository checks passed")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
