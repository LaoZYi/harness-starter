from __future__ import annotations

import re
from pathlib import Path

PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-z0-9_]+)\s*}}")


def render_template(template_text: str, context: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        return context.get(match.group(1), "")

    return PLACEHOLDER_PATTERN.sub(replace, template_text)


def materialize_templates(
    template_root: Path,
    target_root: Path,
    context: dict[str, str],
    *,
    force: bool = False,
) -> tuple[list[str], list[str]]:
    written: list[str] = []
    skipped: list[str] = []

    for template_path in sorted(template_root.rglob("*.tmpl")):
        relative_template = template_path.relative_to(template_root)
        output_relative = Path(str(relative_template)[:-5])
        output_path = target_root / output_relative
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists() and not force:
            skipped.append(str(output_relative))
            continue

        content = render_template(template_path.read_text(encoding="utf-8"), context)
        output_path.write_text(content, encoding="utf-8")
        written.append(str(output_relative))

    return written, skipped

