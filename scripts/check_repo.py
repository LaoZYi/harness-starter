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
    ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml",
    ROOT / "docs" / "product.md",
    ROOT / "docs" / "architecture.md",
    ROOT / "docs" / "workflow.md",
    ROOT / "docs" / "release.md",
    ROOT / "docs" / "runbook.md",
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
    for target in ("check:", "test:", "ci:"):
        assert_true(target in makefile_text, f"Makefile 缺少目标: {target[:-1]}")


def check_module_sizes() -> None:
    for relative_path in ["src/ticket_router/router.py", "src/ticket_router/models.py"]:
        path = ROOT / relative_path
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        assert_true(line_count <= 220, f"{relative_path} 过长: {line_count} 行")


def check_runbook_mentions_main_commands() -> None:
    runbook_text = (ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
    for command in ("make check", "make test", "make ci", "make run"):
        assert_true(command in runbook_text, f"运行手册缺少命令说明: {command}")


def check_github_templates() -> None:
    pr_text = (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    bug_text = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md").read_text(encoding="utf-8")
    feature_text = (ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md").read_text(encoding="utf-8")
    assert_true("make check" in pr_text, "PR 模板必须要求验证命令")
    assert_true("docs/product.md" in bug_text, "Bug 模板必须指向仓库文档")
    assert_true("验收标准" in feature_text, "功能模板必须要求验收标准")


def main() -> None:
    check_required_files()
    check_agents_length()
    check_adapter_files_point_to_agents()
    check_markdown_references()
    check_command_surface()
    check_module_sizes()
    check_runbook_mentions_main_commands()
    check_github_templates()
    print("repository checks passed")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
