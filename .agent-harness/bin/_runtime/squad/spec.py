"""JSON spec parsing for /squad — worker definitions, dependency validation.

Issue #25：从 YAML 迁到 JSON，去除 PyYAML 依赖以支持项目内嵌运行时
（`.agent-harness/bin/squad`）纯 stdlib 的约束。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from _runtime.security import NAME_PATTERN


_ALLOWED_CAPABILITIES = ("orchestrator", "scout", "builder", "reviewer")


class SpecError(ValueError):
    """Raised when a squad spec fails validation."""


@dataclass
class Worker:
    name: str
    capability: str
    prompt: str
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Spec:
    task_id: str
    base_branch: str
    workers: list[Worker]


def parse_spec(path: Path) -> Spec:
    """Parse a JSON spec file into a validated Spec object.

    Raises SpecError on any validation failure. 提示：旧版 YAML spec 可用以下
    方式转换：`python -c "import yaml,json,sys; json.dump(yaml.safe_load(open('spec.yaml')), open('spec.json','w'), ensure_ascii=False, indent=2)"`
    """
    if not path.is_file():
        raise SpecError(f"spec 文件不存在：{path}")

    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        raise SpecError(
            f"Issue #25 起 spec 只支持 JSON（去 PyYAML 依赖）。请把 {path} 转为 "
            f".json：先手工 yaml→json，或用 `python -c \"import yaml,json; "
            f"json.dump(yaml.safe_load(open('{path}')), open('{path.with_suffix('.json')}','w'), "
            f"ensure_ascii=False, indent=2)\"`"
        )

    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SpecError(f"JSON 解析失败：{exc}") from exc

    if not isinstance(raw, dict):
        raise SpecError("spec 顶层必须是 mapping")

    task_id = raw.get("task_id")
    base_branch = raw.get("base_branch")
    workers_raw = raw.get("workers")

    if not task_id or not isinstance(task_id, str):
        raise SpecError("缺少必填字段 task_id")
    if not NAME_PATTERN.match(task_id):
        raise SpecError(f"task_id 名称不合法（仅允许小写字母/数字/连字符，长度 1-31）：{task_id!r}")
    if not base_branch or not isinstance(base_branch, str):
        raise SpecError("缺少必填字段 base_branch")
    if not isinstance(workers_raw, list) or not workers_raw:
        raise SpecError("缺少必填字段 workers（至少 1 个）")

    workers = [_parse_worker(w, idx) for idx, w in enumerate(workers_raw)]
    _validate_worker_set(workers)

    return Spec(task_id=task_id, base_branch=base_branch, workers=workers)


def _parse_worker(data: Any, idx: int) -> Worker:
    if not isinstance(data, dict):
        raise SpecError(f"workers[{idx}] 必须是 mapping")

    name = data.get("name")
    capability = data.get("capability")
    prompt = data.get("prompt")
    depends_on = data.get("depends_on", [])

    if not name or not isinstance(name, str):
        raise SpecError(f"workers[{idx}] 缺少 name")
    if not NAME_PATTERN.match(name):
        raise SpecError(
            f"workers[{idx}] 名称不合法（仅允许小写字母/数字/连字符，长度 1-31）：{name!r}"
        )
    if capability not in _ALLOWED_CAPABILITIES:
        raise SpecError(
            f"workers[{idx}] capability 必须是 {_ALLOWED_CAPABILITIES} 之一，收到 {capability!r}"
        )
    if not prompt or not isinstance(prompt, str):
        raise SpecError(f"workers[{idx}] 缺少 prompt")
    if not isinstance(depends_on, list) or not all(isinstance(x, str) for x in depends_on):
        raise SpecError(f"workers[{idx}] depends_on 必须是字符串列表")

    return Worker(name=name, capability=capability, prompt=prompt, depends_on=list(depends_on))


def _validate_worker_set(workers: list[Worker]) -> None:
    names = [w.name for w in workers]
    seen: set[str] = set()
    for n in names:
        if n in seen:
            raise SpecError(f"worker 名称重复：{n}")
        seen.add(n)

    name_set = set(names)
    for w in workers:
        for dep in w.depends_on:
            if dep not in name_set:
                raise SpecError(f"worker {w.name!r} 依赖不存在的 worker：{dep!r}")

    _check_no_cycle(workers)


def _check_no_cycle(workers: list[Worker]) -> None:
    """DFS 着色法检测依赖环。WHITE=未访问, GRAY=访问中, BLACK=完成。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {w.name: WHITE for w in workers}
    adj = {w.name: w.depends_on for w in workers}

    def dfs(node: str, stack: list[str]) -> None:
        color[node] = GRAY
        for nxt in adj[node]:
            if color[nxt] == GRAY:
                cycle = stack[stack.index(nxt):] + [nxt]
                raise SpecError(f"worker 依赖存在循环：{' -> '.join(cycle)}")
            if color[nxt] == WHITE:
                dfs(nxt, stack + [nxt])
        color[node] = BLACK

    for w in workers:
        if color[w.name] == WHITE:
            dfs(w.name, [w.name])
