"""Three-way merge for text files and JSON config files.

Used by the upgrade system to merge framework template updates with
user-edited content, preserving both sides where possible and inserting
conflict markers when both sides changed the same region.
"""
from __future__ import annotations

import json
from difflib import SequenceMatcher

CONFLICT_CURRENT = "<<<<<<< 当前内容"
CONFLICT_SEP = "======="
CONFLICT_NEW = ">>>>>>> 框架更新"


def merge3(base: str, current: str, new: str) -> tuple[str, list[str]]:
    """Line-based three-way merge.

    Returns (merged_text, conflict_descriptions).
    Empty conflict list means clean merge.
    """
    if current == base:
        return new, []
    if new == base:
        return current, []
    if current == new:
        return current, []

    base_lines = base.splitlines(keepends=True)
    cur_lines = current.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    merged: list[str] = []
    conflicts: list[str] = []

    for tag, region_base, region_cur, region_new in _walk_regions(base_lines, cur_lines, new_lines):
        if tag == "clean":
            merged.extend(region_cur if region_cur != region_base else region_new)
        elif tag == "conflict":
            conflicts.append(f"行 {len(merged) + 1} 附近：双方都修改了同一区域")
            merged.append(CONFLICT_CURRENT + "\n")
            merged.extend(region_cur)
            merged.append(CONFLICT_SEP + "\n")
            merged.extend(region_new)
            merged.append(CONFLICT_NEW + "\n")

    result = "".join(merged)
    if not result.endswith("\n") and (current.endswith("\n") or new.endswith("\n")):
        result += "\n"
    return result, conflicts


def _walk_regions(
    base: list[str], cur: list[str], new: list[str],
) -> list[tuple[str, list[str], list[str], list[str]]]:
    """Yield (tag, base_region, cur_region, new_region) tuples.

    tag is 'clean' or 'conflict'.
    """
    sm_cur = SequenceMatcher(None, base, cur)
    sm_new = SequenceMatcher(None, base, new)

    cur_ops = _expand_opcodes(sm_cur.get_opcodes(), "cur")
    new_ops = _expand_opcodes(sm_new.get_opcodes(), "new")

    cur_changed = set()
    for op, b1, b2, _, _ in cur_ops:
        if op != "equal":
            for i in range(b1, max(b2, b1 + 1)):
                cur_changed.add(i)

    new_changed = set()
    for op, b1, b2, _, _ in new_ops:
        if op != "equal":
            for i in range(b1, max(b2, b1 + 1)):
                new_changed.add(i)

    overlap = cur_changed & new_changed

    if not overlap:
        return _merge_no_conflict(base, cur, new, sm_cur, sm_new)

    return _merge_with_conflict(base, cur, new, sm_cur, sm_new, overlap)


def _expand_opcodes(opcodes: list[tuple[str, int, int, int, int]], label: str):
    return opcodes


def _merge_no_conflict(base, cur, new, sm_cur, sm_new):
    """Both sides changed, but different regions. Apply both."""
    result_lines: list[str] = []
    cur_map: dict[int, list[str]] = {}
    new_map: dict[int, list[str]] = {}

    for tag, b1, b2, c1, c2 in sm_cur.get_opcodes():
        if tag == "replace":
            cur_map[b1] = cur[c1:c2]
        elif tag == "insert":
            cur_map.setdefault(b1, []).extend(cur[c1:c2])
        elif tag == "delete":
            cur_map[b1] = []

    for tag, b1, b2, n1, n2 in sm_new.get_opcodes():
        if tag == "replace":
            new_map[b1] = new[n1:n2]
        elif tag == "insert":
            new_map.setdefault(b1, []).extend(new[n1:n2])
        elif tag == "delete":
            new_map[b1] = []

    for i, line in enumerate(base):
        if i in cur_map:
            result_lines.extend(cur_map[i])
        elif i in new_map:
            result_lines.extend(new_map[i])
        else:
            result_lines.append(line)

    # Append trailing inserts
    end = len(base)
    if end in cur_map:
        result_lines.extend(cur_map[end])
    if end in new_map:
        result_lines.extend(new_map[end])

    return [("clean", base, result_lines, result_lines)]


def _merge_with_conflict(base, cur, new, sm_cur, sm_new, overlap):
    """Regions overlap — produce conflict markers for overlapping parts."""
    regions: list[tuple[str, list[str], list[str], list[str]]] = []

    cur_opcodes = sm_cur.get_opcodes()
    new_opcodes = sm_new.get_opcodes()

    # Simple approach: split into chunks by base line ranges
    # For each base range, check if it's in overlap
    cur_lookup = _build_replacement_lookup(base, cur, cur_opcodes)
    new_lookup = _build_replacement_lookup(base, new, new_opcodes)

    i = 0
    while i < len(base):
        cur_has = i in cur_lookup
        new_has = i in new_lookup

        if cur_has and new_has and i in overlap:
            # Conflict: both modified this region
            cr = cur_lookup[i]
            nr = new_lookup[i]
            skip = max(cr["base_end"], nr["base_end"]) - i
            regions.append(("conflict", base[i:i + skip], cr["lines"], nr["lines"]))
            i += max(skip, 1)
        elif cur_has:
            cr = cur_lookup[i]
            skip = cr["base_end"] - i
            regions.append(("clean", base[i:i + skip], cr["lines"], cr["lines"]))
            i += max(skip, 1)
        elif new_has:
            nr = new_lookup[i]
            skip = nr["base_end"] - i
            regions.append(("clean", base[i:i + skip], nr["lines"], nr["lines"]))
            i += max(skip, 1)
        else:
            regions.append(("clean", [base[i]], [base[i]], [base[i]]))
            i += 1

    return regions


def _build_replacement_lookup(base, target, opcodes):
    lookup = {}
    for tag, b1, b2, t1, t2 in opcodes:
        if tag in ("replace", "delete", "insert"):
            lookup[b1] = {"base_end": max(b2, b1 + 1), "lines": target[t1:t2]}
    return lookup


def json_merge(
    base: str,
    current: str,
    new: str,
    framework_keys: set[str] | None = None,
) -> tuple[str, list[str]]:
    """Structured JSON merge.

    - framework_keys: updated from new template version
    - User keys: preserved from current
    - New keys (in new but not in base): added
    - Removed keys (in base but not in new): removed with warning
    """
    try:
        cur_data = json.loads(current)
    except json.JSONDecodeError:
        return new, ["project.json 格式错误，已用框架版本覆盖"]

    new_data = json.loads(new)
    base_data = json.loads(base) if base else {}
    fw_keys = framework_keys or set()
    warnings: list[str] = []

    merged = dict(cur_data)

    for key in fw_keys:
        if key in new_data:
            merged[key] = new_data[key]

    for key in new_data:
        if key not in merged:
            merged[key] = new_data[key]
            warnings.append(f"新增字段: {key}")

    for key in list(base_data.keys()):
        if key not in new_data and key in merged and key in fw_keys:
            del merged[key]
            warnings.append(f"框架移除字段: {key}")

    return json.dumps(merged, indent=2, ensure_ascii=False) + "\n", warnings
