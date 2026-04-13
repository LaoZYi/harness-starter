"""tmux command construction and availability checks for squad."""
from __future__ import annotations

import re
import shlex
import shutil
import subprocess


class TmuxError(RuntimeError):
    """Raised for tmux-related problems (missing binary, invalid names)."""


_SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")


def _validate_name(kind: str, value: str) -> None:
    if not isinstance(value, str) or not _SAFE_NAME.match(value):
        raise TmuxError(
            f"{kind} 名称不合法（仅允许小写字母/数字/连字符，长度 1-41）：{value!r}"
        )


def build_new_session_cmd(session: str) -> list[str]:
    """Build `tmux new-session -d -s <session>` command list."""
    _validate_name("session", session)
    return ["tmux", "new-session", "-d", "-s", session]


def build_new_window_cmd(
    session: str,
    window: str,
    cwd: str,
    system_prompt_file: str,
    task_prompt_file: str,
) -> list[str]:
    """Build `tmux new-window ... <shell-cmd>` to launch a Claude Code worker.

    Worker launch shape:
        cd <cwd> && claude \\
            --append-system-prompt "$(cat <system_prompt_file>)" \\
            "$(cat <task_prompt_file>)"
    """
    _validate_name("session", session)
    _validate_name("window", window)

    # shlex.quote all path arguments so spaces / metacharacters in project
    # roots (e.g. "/Users/alice/my projects/...") don't break the subshell or
    # enable command injection.
    q_cwd = shlex.quote(cwd)
    q_sys = shlex.quote(system_prompt_file)
    q_task = shlex.quote(task_prompt_file)
    shell_cmd = (
        f"cd {q_cwd} && "
        f"claude "
        f"--append-system-prompt \"$(cat {q_sys})\" "
        f"\"$(cat {q_task})\""
    )

    return [
        "tmux",
        "new-window",
        "-t",
        session,
        "-n",
        window,
        "-d",
        shell_cmd,
    ]


def build_list_windows_cmd(session: str) -> list[str]:
    """Build `tmux list-windows -t <session> -F '#{window_name}'` command.

    Caller runs this and splits stdout on newlines to get active window names.
    Used by `squad advance` to detect already-launched workers (idempotent spawn).
    """
    _validate_name("session", session)
    return ["tmux", "list-windows", "-t", session, "-F", "#{window_name}"]


def list_windows(session: str) -> list[str]:
    """Run `tmux list-windows` and return window names. Returns [] if session
    doesn't exist or tmux is unavailable (not an error — advance can still
    proceed, just treats all workers as unlaunched)."""
    try:
        result = subprocess.run(
            build_list_windows_cmd(session),
            capture_output=True, text=True, check=False,
        )
    except (FileNotFoundError, TmuxError):
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def ensure_tmux_available() -> str:
    """Return tmux version string, or raise TmuxError with install hint."""
    path = shutil.which("tmux")
    if not path:
        raise TmuxError(
            "未找到 tmux。请先安装（macOS: `brew install tmux` / Debian/Ubuntu: "
            "`sudo apt install tmux`），然后重试。"
        )
    # Use the resolved path (not bare "tmux") so later subprocess calls are
    # consistent with the availability probe under any PATH mutation.
    result = subprocess.run([path, "-V"], capture_output=True, text=True)
    if result.returncode != 0:
        raise TmuxError(f"tmux -V 执行失败：{result.stderr or result.stdout}")
    return result.stdout.strip()
