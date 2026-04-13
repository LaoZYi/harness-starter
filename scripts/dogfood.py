"""Re-sync generated skill/rule files from templates (dogfooding).

Only syncs .claude/commands/, .claude/rules/, and .claude/settings.json.
Does NOT touch hand-written docs (AGENTS.md, CLAUDE.md, docs/, etc.).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_harness.initializer import SUPERPOWERS_ROOT, TEMPLATE_ROOT, prepare_initialization  # noqa: E402
from agent_harness.runtime_install import install_runtime  # noqa: E402
from agent_harness.templating import render_templates  # noqa: E402

SYNC_PREFIXES = (".claude/commands/", ".claude/rules/", ".claude/hooks/", ".claude/settings.json")


def main() -> None:
    pj = ROOT / ".agent-harness" / "project.json"
    if not pj.exists():
        print("未找到 .agent-harness/project.json，请先运行 harness init。", file=sys.stderr)
        sys.exit(1)
    answers = json.loads(pj.read_text(encoding="utf-8"))
    answers["project_name"] = answers.get("project_name", "")
    answers["summary"] = answers.get("project_summary", "")
    # Flatten nested "commands" dict to flat keys expected by prepare_initialization()
    if "commands" in answers and isinstance(answers["commands"], dict):
        cmds = answers["commands"]
        answers.setdefault("run_command", cmds.get("run", "TODO"))
        answers.setdefault("test_command", cmds.get("test", "TODO"))
        answers.setdefault("check_command", cmds.get("check", "TODO"))
        answers.setdefault("ci_command", cmds.get("ci", "TODO"))
    _, _, context = prepare_initialization(ROOT, answers)
    rendered = render_templates(TEMPLATE_ROOT, context)
    if SUPERPOWERS_ROOT.is_dir():
        rendered.update(render_templates(SUPERPOWERS_ROOT, context))

    updated = 0
    created = 0
    for rel_path, expected in sorted(rendered.items()):
        if not any(rel_path.startswith(p) for p in SYNC_PREFIXES):
            continue
        actual_path = ROOT / rel_path
        if not actual_path.exists():
            actual_path.parent.mkdir(parents=True, exist_ok=True)
            actual_path.write_text(expected, encoding="utf-8")
            created += 1
            print(f"  + {rel_path}")
        elif actual_path.read_text(encoding="utf-8") != expected:
            actual_path.write_text(expected, encoding="utf-8")
            updated += 1
            print(f"  ~ {rel_path}")
    install_runtime(ROOT)  # Issue #24: 刷新本仓库的 .agent-harness/bin/ 运行时
    print(f"\n同步完成：{created} 个新增，{updated} 个更新；bin/_runtime 已刷新")


if __name__ == "__main__":
    main()
