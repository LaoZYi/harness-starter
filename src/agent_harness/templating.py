from __future__ import annotations

import logging
import re
from pathlib import Path

PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-z0-9_]+)\s*}}")
_log = logging.getLogger(__name__)


def render_template(template_text: str, context: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            _log.warning("模板占位符 {{%s}} 无对应值，已替换为空串", key)
        return context.get(key, "")

    return PLACEHOLDER_PATTERN.sub(replace, template_text)


def render_templates(
    template_root: Path,
    context: dict[str, str],
    *,
    exclude: list[str] | None = None,
) -> dict[str, str]:
    exclude_set = set(exclude or [])
    rendered: dict[str, str] = {}
    for template_path in sorted(template_root.rglob("*.tmpl")):
        relative_template = template_path.relative_to(template_root)
        output_relative = str(relative_template)[:-5]
        if output_relative in exclude_set:
            continue
        rendered[output_relative] = render_template(template_path.read_text(encoding="utf-8"), context)
    return rendered


def materialize_templates(
    template_root: Path,
    target_root: Path,
    context: dict[str, str],
    *,
    force: bool = False,
    dry_run: bool = False,
    exclude: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    written: list[str] = []
    skipped: list[str] = []

    for output_relative, content in render_templates(template_root, context, exclude=exclude).items():
        output_path = target_root / output_relative

        if not output_path.resolve().is_relative_to(target_root.resolve()):
            continue

        if output_path.exists() and not force:
            skipped.append(output_relative)
            continue

        if not dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
        written.append(output_relative)

    return written, skipped
