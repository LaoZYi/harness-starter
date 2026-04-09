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

    for tag, region_cur, region_new in _walk_regions(base_lines, cur_lines, new_lines):
        if tag == "clean":
            merged.extend(region_cur)
        elif tag == "conflict":
            conflicts.append(f"行 {len(merged) + 1} 附近：双方都修改了同一区域")
            _ensure_trailing_newline(region_cur)
            _ensure_trailing_newline(region_new)
            merged.append(CONFLICT_CURRENT + "\n")
            merged.extend(region_cur)
            merged.append(CONFLICT_SEP + "\n")
            merged.extend(region_new)
            merged.append(CONFLICT_NEW + "\n")

    result = "".join(merged)
    if not result.endswith("\n") and (current.endswith("\n") or new.endswith("\n")):
        result += "\n"
    return result, conflicts


def _ensure_trailing_newline(lines: list[str]) -> None:
    """Ensure last line ends with \\n so conflict markers render correctly."""
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"


def _build_edit_maps(base, target, opcodes):
    """Build separate maps for inserts (prepend before base[i]) and replacements.

    Returns (pre_map, replace_map, delete_set):
    - pre_map[i] = lines to insert BEFORE base[i]
    - replace_map[i] = {"end": b2, "lines": [...]} to replace base[i:b2]
    - delete_set = set of base indices to delete
    """
    pre_map: dict[int, list[str]] = {}
    replace_map: dict[int, dict] = {}
    delete_set: set[int] = set()

    for tag, b1, b2, t1, t2 in opcodes:
        if tag == "insert":
            pre_map.setdefault(b1, []).extend(target[t1:t2])
        elif tag == "replace":
            replace_map[b1] = {"end": b2, "lines": target[t1:t2]}
        elif tag == "delete":
            for j in range(b1, b2):
                delete_set.add(j)

    return pre_map, replace_map, delete_set


def _walk_regions(base, cur, new):
    """Yield (tag, cur_region, new_region) tuples."""
    sm_cur = SequenceMatcher(None, base, cur)
    sm_new = SequenceMatcher(None, base, new)

    cur_pre, cur_rep, cur_del = _build_edit_maps(base, cur, sm_cur.get_opcodes())
    new_pre, new_rep, new_del = _build_edit_maps(base, new, sm_new.get_opcodes())

    # Determine which base indices are changed by each side
    cur_changed: set[int] = set()
    for b1, info in cur_rep.items():
        cur_changed.update(range(b1, info["end"]))
    cur_changed |= cur_del
    # Inserts at position i affect position i but don't consume base[i]
    for i in cur_pre:
        if i < len(base):
            cur_changed.add(i)

    new_changed: set[int] = set()
    for b1, info in new_rep.items():
        new_changed.update(range(b1, info["end"]))
    new_changed |= new_del
    for i in new_pre:
        if i < len(base):
            new_changed.add(i)

    overlap = cur_changed & new_changed
    # Only count as overlap if both sides actually modified (not just inserted nearby)
    real_overlap = set()
    for i in overlap:
        cur_modified = i in cur_del or any(b1 <= i < info["end"] for b1, info in cur_rep.items())
        new_modified = i in new_del or any(b1 <= i < info["end"] for b1, info in new_rep.items())
        cur_inserted = i in cur_pre
        new_inserted = i in new_pre
        if (cur_modified and new_modified) or (cur_modified and new_inserted) or (new_modified and cur_inserted):
            real_overlap.add(i)

    regions: list[tuple[str, list[str], list[str]]] = []
    i = 0
    while i < len(base):
        # Emit pre-inserts for position i (if no conflict at i)
        if i not in real_overlap:
            if i in cur_pre:
                regions.append(("clean", cur_pre[i], cur_pre[i]))
            elif i in new_pre:
                regions.append(("clean", new_pre[i], new_pre[i]))

        if i in real_overlap:
            # Find the extent of the overlapping region
            end = i + 1
            while end < len(base) and end in real_overlap:
                end += 1
            # Collect what each side produces for this region
            cur_out = _collect_side_output(base, cur_pre, cur_rep, cur_del, i, end)
            new_out = _collect_side_output(base, new_pre, new_rep, new_del, i, end)
            if cur_out == new_out:
                regions.append(("clean", cur_out, new_out))
            else:
                regions.append(("conflict", cur_out, new_out))
            i = end
        elif i in cur_rep:
            info = cur_rep[i]
            regions.append(("clean", info["lines"], info["lines"]))
            i = info["end"]
        elif i in new_rep:
            info = new_rep[i]
            regions.append(("clean", info["lines"], info["lines"]))
            i = info["end"]
        elif i in cur_del:
            i += 1  # skip deleted line
        elif i in new_del:
            i += 1
        else:
            regions.append(("clean", [base[i]], [base[i]]))
            i += 1

    # Trailing inserts/content beyond base
    end = len(base)
    cur_trail = cur_pre.get(end, [])
    new_trail = new_pre.get(end, [])
    if cur_trail and new_trail:
        if cur_trail == new_trail:
            regions.append(("clean", cur_trail, new_trail))
        else:
            regions.append(("conflict", cur_trail, new_trail))
    elif cur_trail:
        regions.append(("clean", cur_trail, cur_trail))
    elif new_trail:
        regions.append(("clean", new_trail, new_trail))

    return regions


def _collect_side_output(base, pre_map, rep_map, del_set, start, end):
    """Collect what one side produces for base[start:end]."""
    out: list[str] = []
    i = start
    while i < end:
        if i in pre_map:
            out.extend(pre_map[i])
        if i in rep_map:
            out.extend(rep_map[i]["lines"])
            i = rep_map[i]["end"]
        elif i in del_set:
            i += 1
        else:
            out.append(base[i])
            i += 1
    return out


def json_merge(
    base: str,
    current: str,
    new: str,
    framework_keys: set[str] | None = None,
) -> tuple[str, list[str]]:
    """Structured JSON merge.

    - framework_keys: updated from new template version (shallow replace)
    - User keys: preserved from current
    - New keys (in new but not in base): added
    - Removed keys (in base but not in new): removed with warning

    Note: framework_keys replacement is shallow. If a framework key maps to
    a nested object, the entire object is replaced, not deep-merged.
    """
    try:
        cur_data = json.loads(current)
    except json.JSONDecodeError:
        return new, ["project.json 格式错误，已用框架版本覆盖"]

    try:
        new_data = json.loads(new)
    except json.JSONDecodeError:
        return current, ["框架模板渲染的 JSON 格式错误，保留用户版本"]

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
