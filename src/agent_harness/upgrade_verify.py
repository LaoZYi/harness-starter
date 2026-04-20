"""Upgrade 后置校验：返回警告列表（空 = PASS）。

从 upgrade.py 拆出以保持 <= 280 行（AGENTS.md 硬规则）。
"""
from __future__ import annotations

import json
from pathlib import Path

from ._shared import PLACEHOLDER_RE

_FALLBACK_SUMMARY_SENTINEL = "待补充项目目标"

# 渲染产物中若出现 sentinel 但 project.json 已填对应字段 → 变量替换或 answers
# 解析失败（见历史 bug GitLab #20）。只扫用户可见文本的产物文件。
_SCAN_PRODUCTS = ("AGENTS.md", "CLAUDE.md", "docs/product.md")


def _load_project_json_raw(path: Path) -> tuple[dict[str, object], str | None]:
    if not path.exists():
        return {}, None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {}, f"project.json 格式错误：{e}"
    return (loaded if isinstance(loaded, dict) else {}), None


def _scan_placeholders(target_root: Path) -> list[str]:
    out: list[str] = []
    for md in (target_root / "AGENTS.md", target_root / "CLAUDE.md"):
        if md.exists():
            text = md.read_text(encoding="utf-8")
            unfilled = PLACEHOLDER_RE.findall(text)
            if unfilled:
                out.append(f"{md.name} 中存在未填充的占位符：{', '.join(unfilled[:3])}")
    return out


def _scan_summary_sentinel(target_root: Path, pj_data: dict[str, object]) -> list[str]:
    summary_value = pj_data.get("project_summary") or pj_data.get("summary")
    if not (isinstance(summary_value, str) and summary_value
            and summary_value != _FALLBACK_SUMMARY_SENTINEL):
        return []
    out: list[str] = []
    for rel in _SCAN_PRODUCTS:
        p = target_root / rel
        if p.exists() and _FALLBACK_SUMMARY_SENTINEL in p.read_text(encoding="utf-8"):
            out.append(
                f"{rel} 中出现模板 sentinel「{_FALLBACK_SUMMARY_SENTINEL}」，"
                f"但 project.json 的 summary 已填为「{summary_value}」。"
                f"疑似变量替换遗漏或 answers 未读取 project.json（见 GitLab Issue #20）。"
            )
    return out


def _scan_conflict_markers(target_root: Path, category_fn) -> list[str]:
    marker = "<<<<<<< "
    out: list[str] = []
    for md in sorted(p for pat in ("**/*.md", "**/*.yml", "**/*.yaml", "**/*.py", "**/*.toml")
                     for p in target_root.glob(pat)):
        rel = str(md.relative_to(target_root))
        if category_fn(rel) in ("overwrite", "skip"):
            continue
        try:
            if marker in md.read_text(encoding="utf-8"):
                out.append(f"{rel} 中存在未解决的合并冲突标记")
        except (UnicodeDecodeError, OSError):
            pass
    return out


def verify_upgrade(target_root: Path) -> list[str]:
    """Post-upgrade verification. Returns list of warnings (empty = PASS)."""
    from .upgrade import get_category  # 运行时导入避免循环依赖

    target_root = target_root.resolve()
    warnings: list[str] = []

    agents = target_root / "AGENTS.md"
    if agents.exists():
        line_count = len(agents.read_text(encoding="utf-8").splitlines())
        if line_count > 80:
            warnings.append(f"AGENTS.md 超过 80 行（当前 {line_count} 行），建议拆分到 docs/。")

    pj_data, pj_error = _load_project_json_raw(target_root / ".agent-harness" / "project.json")
    if pj_error:
        warnings.append(pj_error)

    warnings.extend(_scan_placeholders(target_root))
    warnings.extend(_scan_summary_sentinel(target_root, pj_data))
    warnings.extend(_scan_conflict_markers(target_root, get_category))
    return warnings
