"""Knowledge artifacts — 结构化知识制品，供后续任务 refs 复用（compound intelligence）。

吸收自 Danau5tin/multi-agent-coding-system（TerminalBench #13）的 context store
设计。与 `agent.py` 的自由日志 `diary_append` 互补，提供机器可解析的格式。

块格式写入 diary.md：

    ## artifact
    - ts: 2026-04-14T...
    - type: exploration
    - summary: 单行摘要
    - refs: file1, file2
    ```
    详细内容
    ```

Issue #30。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import agent as _agent


# 允许的 artifact_type：小写字母+数字+连字符+下划线，长度 1-32
_ARTIFACT_TYPE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")

# diary 中 artifact 块的锚点正则（解析用）
_ARTIFACT_BLOCK_RE = re.compile(
    r"^## artifact\s*\n"
    r"- ts: (?P<ts>.+?)\n"
    r"- type: (?P<type>.+?)\n"
    r"- summary: (?P<summary>.+?)\n"
    r"(?:- refs: (?P<refs>.*?)\n)?"
    r"(?:```\n(?P<content>.*?)\n```\n)?",
    re.MULTILINE | re.DOTALL,
)


def _validate_artifact_type(artifact_type: str) -> None:
    if not isinstance(artifact_type, str) or not _ARTIFACT_TYPE_PATTERN.fullmatch(artifact_type):
        raise _agent.AgentError(
            f"artifact_type 不合法（仅允许小写字母/数字/连字符/下划线，长度 1-32）：{artifact_type!r}"
        )


def diary_append_artifact(
    project_root: Path,
    agent_id: str,
    *,
    artifact_type: str,
    summary: str,
    content: str = "",
    refs: list[str] | None = None,
    ts: str | None = None,
) -> str:
    """Append a structured knowledge artifact block to the agent's diary.md."""
    _agent._validate_id(agent_id)
    _validate_artifact_type(artifact_type)
    if not isinstance(summary, str) or not summary.strip():
        raise _agent.AgentError("artifact summary 不能为空")
    summary = summary.replace("\n", " ").strip()
    content = content if isinstance(content, str) else ""
    refs = refs or []
    if not isinstance(refs, list) or any(not isinstance(r, str) for r in refs):
        raise _agent.AgentError("artifact refs 必须是字符串列表")
    _agent.init_agent(project_root, agent_id)
    timestamp = ts or _agent._now_iso()
    lines = [
        "\n## artifact",
        f"- ts: {timestamp}",
        f"- type: {artifact_type}",
        f"- summary: {summary}",
        f"- refs: {', '.join(refs)}" if refs else "- refs: ",
        "```",
        content,
        "```",
        "",
    ]
    block = "\n".join(lines)
    with _agent._locked_append(_agent.agent_dir(project_root, agent_id) / "diary.md") as f:
        f.write(block)
    return block


def extract_artifacts(project_root: Path, agent_id: str) -> list[dict[str, Any]]:
    """Parse artifact blocks out of an agent's diary.md. Order preserved."""
    _agent._validate_id(agent_id)
    text = _agent.diary_read(project_root, agent_id)
    if not text:
        return []
    result: list[dict[str, Any]] = []
    for m in _ARTIFACT_BLOCK_RE.finditer(text):
        refs_raw = (m.group("refs") or "").strip()
        refs = [r.strip() for r in refs_raw.split(",") if r.strip()] if refs_raw else []
        result.append({
            "ts": m.group("ts").strip(),
            "type": m.group("type").strip(),
            "summary": m.group("summary").strip(),
            "refs": refs,
            "content": (m.group("content") or "").strip(),
            "agent_id": agent_id,
        })
    return result


def render_artifacts_section(project_root: Path, agent_ids: list[str]) -> str:
    """Return the Markdown '## Artifacts' section for aggregate()."""
    all_artifacts: list[dict[str, Any]] = []
    for aid in agent_ids:
        all_artifacts.extend(extract_artifacts(project_root, aid))
    if not all_artifacts:
        return ""
    parts = [
        "\n## Artifacts\n",
        "> 结构化知识制品，供后续任务通过 refs 复用。\n",
    ]
    for art in all_artifacts:
        refs_str = f" (refs: {', '.join(art['refs'])})" if art["refs"] else ""
        parts.append(
            f"- [{art['agent_id']}] [{art['type']}] {art['summary']}{refs_str}"
        )
    parts.append("")
    return "\n".join(parts)


__all__ = ["diary_append_artifact", "extract_artifacts", "render_artifacts_section"]
