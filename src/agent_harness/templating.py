from __future__ import annotations

import re
from pathlib import Path

PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-z0-9_]+)\s*}}")


def render_template(template_text: str, context: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        return context.get(match.group(1), "")

    return PLACEHOLDER_PATTERN.sub(replace, template_text)


def render_templates(template_root: Path, context: dict[str, str]) -> dict[str, str]:
    rendered: dict[str, str] = {}
    for template_path in sorted(template_root.rglob("*.tmpl")):
        relative_template = template_path.relative_to(template_root)
        output_relative = str(relative_template)[:-5]
        rendered[output_relative] = render_template(template_path.read_text(encoding="utf-8"), context)
    return rendered


def materialize_templates(
    template_root: Path,
    target_root: Path,
    context: dict[str, str],
    *,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[list[str], list[str]]:
    written: list[str] = []
    skipped: list[str] = []

    for output_relative, content in render_templates(template_root, context).items():
        output_path = target_root / output_relative

        if output_path.exists() and not force:
            skipped.append(output_relative)
            continue

        if not dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
        written.append(output_relative)

    return written, skipped
