"""Helpers for squad worker provisioning: worktree, settings, prompts."""
from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from .capability import render_settings
from .spec import Spec, Worker
from .state import squad_dir


_SQUAD_CONTEXT_TEMPLATE = """\
你是 squad 成员。严格遵守以下约束：

- 你的身份：{worker_name}（capability={capability}）
- 当前 squad task_id：{task_id}
- 状态文件路径（向 coordinator 汇报请 append 这里）：
  {status_file}
- 共享目录（本 squad 成员间可读，各自 workers/<name>/ 只可自己写）：
  {squad_dir}

硬规则：
1. 禁止再派遣子 squad 或调用 /squad create（防止递归）
2. 禁止直接写 .agent-harness/lessons.md；如有教训，写到
   {worker_dir}/lessons.pending.md（由 coordinator 合并）
3. 你的工具权限由 .claude/settings.local.json 强制，请勿尝试绕过
4. 完成一个关键步骤后，向 status 文件 append 一行 JSON：
   {{"worker": "{worker_name}", "event": "milestone|done|blocked",
     "message": "<简述>"}}
5. 若被阻塞等待依赖，写 event=blocked 后退出；coordinator 会在依赖完成后重启你
"""


def run_check(cmd: list[str], desc: str) -> None:
    """Run a subprocess and raise RuntimeError with quoted cmd on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"{desc} 失败：{' '.join(shlex.quote(c) for c in cmd)}\n"
            f"stderr: {result.stderr}"
        )


def provision_worker_worktree(root: Path, spec: Spec, w: Worker, dry_run: bool = False) -> Path:
    """Create git worktree for this worker. MVP: uses `.worktrees/wt/squad-<task>-<worker>`.

    In dry_run mode, just create a plain directory (no git worktree) so the rest of
    the pipeline can write settings/prompts and we can assert on them in tests.
    """
    wt_dir = root / ".worktrees" / "wt" / f"squad-{spec.task_id}-{w.name}"
    branch = f"wt/squad-{spec.task_id}-{w.name}"
    if wt_dir.exists():
        return wt_dir
    if dry_run:
        wt_dir.mkdir(parents=True, exist_ok=True)
        return wt_dir
    run_check(
        ["git", "-C", str(root), "worktree", "add", str(wt_dir), "-b", branch, spec.base_branch],
        f"创建 worktree {wt_dir}",
    )
    return wt_dir


def write_worker_files(root: Path, spec: Spec, w: Worker, wt: Path) -> None:
    """Render .claude/settings.local.json, squad-context.md, task-prompt.md."""
    claude_dir = wt / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 1. settings.local.json (capability-enforced)
    settings = render_settings(w.capability)
    (claude_dir / "settings.local.json").write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 2. squad-context.md (system prompt)
    status_file = squad_dir(root, spec.task_id) / "status.jsonl"
    worker_dir = squad_dir(root, spec.task_id) / "workers" / w.name
    worker_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "squad-context.md").write_text(
        _SQUAD_CONTEXT_TEMPLATE.format(
            worker_name=w.name,
            capability=w.capability,
            task_id=spec.task_id,
            status_file=str(status_file),
            squad_dir=str(squad_dir(root, spec.task_id)),
            worker_dir=str(worker_dir),
        ),
        encoding="utf-8",
    )

    # 3. task-prompt.md (positional arg)
    (wt / "task-prompt.md").write_text(w.prompt, encoding="utf-8")
