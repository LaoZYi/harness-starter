"""Skills lint — consistency checker for skills-registry.json.

Three checks (CI-strict):
1. Every registry skill has a matching `commands/<id>.md.tmpl` file
2. Every `.md.tmpl` file is registered (orphan detection)
3. `expected_in_lfg=true` skills actually appear in `lfg.md.tmpl`
"""
from __future__ import annotations

import re
from pathlib import Path

from .skills_registry import expected_in_lfg, load_registry

SUPERPOWERS_TEMPLATE_REL = "src/agent_harness/templates/superpowers"
COMMON_TEMPLATE_REL = "src/agent_harness/templates/common"


def run(repo_root: Path) -> tuple[bool, list[str]]:
    """Run all lint checks against the framework repo root.

    Returns (ok, errors). ok=True iff errors is empty.
    """
    errors: list[str] = []
    repo_root = Path(repo_root)
    sp_template = repo_root / SUPERPOWERS_TEMPLATE_REL

    try:
        registry = load_registry(sp_template)
    except (FileNotFoundError, ValueError) as exc:
        return False, [f"registry load failed: {exc}"]

    registry_ids = {s["id"] for s in registry["skills"]}
    file_ids = _discover_skill_file_ids(repo_root)

    missing_files = registry_ids - file_ids
    for skill_id in sorted(missing_files):
        errors.append(
            f"registry contains '{skill_id}' but no commands/{skill_id}.md.tmpl found"
        )

    orphan_files = file_ids - registry_ids
    for skill_id in sorted(orphan_files):
        errors.append(
            f"orphan: commands/{skill_id}.md.tmpl exists but not in skills-registry.json"
        )

    lfg_template = sp_template / ".claude" / "commands" / "lfg.md.tmpl"
    if lfg_template.exists():
        lfg_text = lfg_template.read_text(encoding="utf-8")
        for skill in expected_in_lfg(registry):
            pattern = re.escape(skill) + r"\b"
            if not re.search(pattern, lfg_text):
                errors.append(
                    f"{skill} is expected_in_lfg=true but not referenced in lfg.md.tmpl"
                )

    return len(errors) == 0, errors


def _discover_skill_file_ids(repo_root: Path) -> set[str]:
    """Discover skill IDs from .md.tmpl filenames under superpowers + common templates."""
    ids: set[str] = set()
    for rel in (SUPERPOWERS_TEMPLATE_REL, COMMON_TEMPLATE_REL):
        cmds_dir = repo_root / rel / ".claude" / "commands"
        if not cmds_dir.exists():
            continue
        for tmpl in cmds_dir.glob("*.md.tmpl"):
            ids.add(tmpl.name[: -len(".md.tmpl")])
    return ids


def main(argv: list[str] | None = None) -> int:
    """Entry for `harness skills lint <target>` CLI binding."""
    import argparse

    parser = argparse.ArgumentParser(prog="harness skills lint")
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Repo root containing src/agent_harness/templates/superpowers/",
    )
    args = parser.parse_args(argv)

    ok, errors = run(Path(args.target).resolve())
    if ok:
        print("[skills-lint] OK — registry consistent with templates")
        return 0

    print("[skills-lint] FAIL")
    for err in errors:
        print(f"  - {err}")
    return 1


def register_subcommand(subs) -> None:
    """Register `harness skills lint` subcommand on argparse subparsers (Issue #27)."""
    skills_p = subs.add_parser("skills", help="skills-registry 一致性检查（Issue #27）")
    skills_subs = skills_p.add_subparsers(dest="skills_command")
    lint_p = skills_subs.add_parser("lint", help="检查 registry 与 templates / lfg 的一致性")
    lint_p.add_argument("target", nargs="?", default=".", help="框架仓库根目录")
    lint_p.set_defaults(func=lambda args: main([args.target]))


if __name__ == "__main__":
    raise SystemExit(main())
