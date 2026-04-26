"""Integration tests for the generated .claude/hooks/ shell scripts.

Covers Issue #13 — Stop + PreCompact hooks absorbed from MemPalace.
2026-04-26: stop hook 范式革命——从内容形式识别(grep 状态字段)换轨到行为信号
(transcript 解析 AI 是否写过 current-task.md) + mtime 兜底,彻底消除内容形式
误拦(反模式 1 第 6 次复现的根治)。

Approach: spawn the real bash script, feed stdin JSON, inspect stdout +
exit code + side effects. We do NOT mock — hooks must work under Claude
Code's actual invocation contract (verified via /source-verify at plan time).
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOP_TMPL = ROOT / "src" / "agent_harness" / "templates" / "common" / ".claude" / "hooks" / "stop.sh.tmpl"
PRECOMPACT_TMPL = ROOT / "src" / "agent_harness" / "templates" / "common" / ".claude" / "hooks" / "pre-compact.sh.tmpl"
SETTINGS_TMPL = ROOT / "src" / "agent_harness" / "templates" / "common" / ".claude" / "settings.json.tmpl"


def _prepare_project(tmp: Path, current_task_body: str | None) -> Path:
    """Render hook scripts into a sandbox project and return project root."""
    proj = tmp / "proj"
    (proj / ".agent-harness").mkdir(parents=True)
    (proj / ".claude" / "hooks").mkdir(parents=True)
    # Copy scripts (tmpl content is plain bash — no {{vars}} in hooks).
    (proj / ".claude" / "hooks" / "stop.sh").write_text(
        STOP_TMPL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (proj / ".claude" / "hooks" / "pre-compact.sh").write_text(
        PRECOMPACT_TMPL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    if current_task_body is not None:
        (proj / ".agent-harness" / "current-task.md").write_text(
            current_task_body, encoding="utf-8"
        )
    return proj


def _make_tool_use(name: str, input_dict: dict) -> dict:
    """构造一条 Claude Code transcript 中 assistant 的 tool_use 行(JSONL 格式)。"""
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "tool_" + name, "name": name, "input": input_dict},
            ],
        },
    }


def _write_transcript(proj: Path, entries: list) -> Path:
    """把 entries 写成 JSONL transcript,返回路径。"""
    transcript = proj / "transcript.jsonl"
    with transcript.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return transcript


def _set_mtime_age(path: Path, age_seconds: int) -> None:
    """把文件 mtime 调到 age_seconds 秒之前(用于模拟跨会话续做)。"""
    target = time.time() - age_seconds
    os.utime(path, (target, target))


def _run_stop(
    proj: Path,
    stdin_json: str = "{}",
    transcript_lines: list | None = None,
    extra_env: dict | None = None,
) -> subprocess.CompletedProcess:
    """如 transcript_lines 给定,自动写文件 + 注入 transcript_path 到 stdin。"""
    if transcript_lines is not None:
        transcript = _write_transcript(proj, transcript_lines)
        # 如果调用者没显式给 stdin_json,就用我们生成的;否则保留调用者的
        if stdin_json == "{}":
            stdin_json = json.dumps({
                "session_id": "test-session",
                "hook_event_name": "Stop",
                "transcript_path": str(transcript),
            })
    env = {"CLAUDE_PROJECT_DIR": str(proj), "PATH": "/usr/bin:/bin:/usr/local/bin"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(proj / ".claude" / "hooks" / "stop.sh")],
        input=stdin_json, capture_output=True, text=True,
        env=env,
    )


def _run_precompact(proj: Path, stdin_json: str = '{"trigger":"auto"}') -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(proj / ".claude" / "hooks" / "pre-compact.sh")],
        input=stdin_json, capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(proj), "PATH": "/usr/bin:/bin:/usr/local/bin",
             "HARNESS_AGENT": "test-runner"},
    )


class StopHookBehaviorTests(unittest.TestCase):
    """Verify the four-way decision logic."""

    def test_no_current_task_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=None)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")  # no JSON → pass

    def test_empty_current_task_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body="")
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")

    def test_awaiting_verification_passes(self) -> None:
        body = "# Current Task\n\n## 状态：待验证\n\n- [ ] 归档与收尾\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             f"Expected pass for 待验证 state, got: {r.stdout!r}")

    def test_awaiting_user_confirmation_passes(self) -> None:
        """方案已出、等用户确认需求方向 — 不该被误拦。"""
        body = "# Current Task\n\n## 状态：待用户确认\n\n- [ ] 方案草稿\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             f"Expected pass for 待用户确认 state, got: {r.stdout!r}")

    def test_awaiting_requirement_confirmation_passes(self) -> None:
        body = "# Current Task\n\n## 状态：待需求确认\n\n- [ ] 规格草稿\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             f"Expected pass for 待需求确认 state, got: {r.stdout!r}")

    # --- 通用状态字段放行(2026-04-25 扩展):
    # 从 5 个字面白名单改为通用 `## 状态[:：]<非空>` 字段标记。
    # 任何 AI 主动声明的状态都视为"已显式思考过当前阶段",放行。

    def test_halfwidth_colon_state_passes(self) -> None:
        """半角冒号 '状态:' 也应放行——AI 不一定记得用全角。"""
        body = "# Current Task\n\n## 状态: 待验证\n\n- [ ] 收尾\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             f"Expected pass for halfwidth-colon state, got: {r.stdout!r}")

    def test_custom_state_word_passes(self) -> None:
        """自定义状态词('等用户回复')也应放行——白名单穷举不可行。"""
        body = "# Current Task\n\n## 状态:等用户回复\n\n- [ ] 草稿\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             f"Expected pass for custom state word, got: {r.stdout!r}")

    def test_state_with_description_passes(self) -> None:
        """状态字段含空格和长描述也应放行。"""
        body = "# Current Task\n\n## 状态: 暂停沟通,等待用户决策方向\n\n- [ ] 步骤\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             f"Expected pass for state with description, got: {r.stdout!r}")

    def test_state_research_passes(self) -> None:
        """`状态:调研中` 之类的过程性状态也放行——只要 AI 主动声明阶段。"""
        body = "# Current Task\n\n## 状态:调研中\n\n- [ ] 探索\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             f"Expected pass for 调研中 state, got: {r.stdout!r}")

    def test_empty_state_field_still_blocks(self) -> None:
        """`## 状态:` 后只有空白不算标记——防偷懒,继续 block。

        2026-04-26 更新:新范式下还需 mtime 老 + 无 transcript 才会 block;
        否则 mtime 兜底会放行。这里调老 mtime 模拟"AI 静默丢进度"场景。
        """
        body = "# Current Task\n\n## 状态:   \n\n- [ ] 未完成\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            _set_mtime_age(proj / ".agent-harness" / "current-task.md", 7200)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block",
                             "Empty state value must not be treated as a valid mark")

    def test_unchecked_checkbox_blocks(self) -> None:
        """未勾 + mtime 老 + 无 transcript → block(真"静默丢进度"场景)。"""
        body = "# Current Task\n\n- [x] 第1步\n- [ ] 第2步未完成\n- [ ] 第3步\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            _set_mtime_age(proj / ".agent-harness" / "current-task.md", 7200)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIn("current-task.md", data["reason"])
            self.assertIn("checkbox", data["reason"])

    def test_all_checked_passes(self) -> None:
        body = "# Current Task\n\n- [x] 第1步\n- [x] 第2步\n- [x] 第3步\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")

    def test_skip_sentinel_overrides_unchecked(self) -> None:
        """Manual escape hatch: touch .stop-hook-skip to bypass the guard."""
        body = "# Current Task\n\n- [ ] 未完成但我要强制停\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            (proj / ".agent-harness" / ".stop-hook-skip").touch()
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             "skip sentinel must bypass the block")

    def test_block_reason_is_valid_json_with_multiline(self) -> None:
        """The reason is multi-line + contains quotes and Chinese — must be valid JSON.

        2026-04-26: 新范式下需 mtime 老 + 无 transcript 才进入 block 路径。
        """
        body = "# Current Task\n- [ ] step one\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            _set_mtime_age(proj / ".agent-harness" / "current-task.md", 7200)
            r = _run_stop(proj)
            # Parse must not raise
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIsInstance(data["reason"], str)
            # Must contain an actual newline (JSON unescape handles it)
            self.assertIn("\n", data["reason"])

    def test_consumes_stdin_without_hang(self) -> None:
        """Hook must not hang on stdin; Claude Code sends JSON we discard."""
        body = "# Current Task\n- [x] done\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            stdin_json = json.dumps({
                "session_id": "abc", "hook_event_name": "Stop",
                "transcript_path": "/tmp/t.jsonl",
            })
            r = _run_stop(proj, stdin_json=stdin_json)
            self.assertEqual(r.returncode, 0)


class StopHookBehaviorSignalTests(unittest.TestCase):
    """2026-04-26 范式革命:行为信号(transcript)+ mtime 兜底取代内容形式识别。

    核心目标:不损失硬保护功能,但消除全部 8 类内容形式误拦。
    """

    # === 行为信号:本会话 transcript 中 AI 写过 current-task.md → 放行 ===

    def test_transcript_write_tool_passes(self) -> None:
        """transcript 含 Write current-task.md → 放行(即使有未勾)。"""
        body = "# Task\n\n- [ ] 还没勾的步骤\n"
        transcript = [
            _make_tool_use("Write", {
                "file_path": "/proj/.agent-harness/current-task.md",
                "content": "# Task\n\n## 阶段:调研中\n\n- [ ] 还没勾的步骤\n",
            }),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj, transcript_lines=transcript)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "",
                             f"Behavior signal (Write) must pass, got: {r.stdout!r}")

    def test_transcript_edit_tool_passes(self) -> None:
        body = "# Task\n\n- [ ] 推进中\n"
        transcript = [
            _make_tool_use("Edit", {
                "file_path": "/proj/.agent-harness/current-task.md",
                "old_string": "x", "new_string": "y",
            }),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj, transcript_lines=transcript)
            self.assertEqual(r.stdout.strip(), "")

    def test_transcript_multiedit_tool_passes(self) -> None:
        body = "# Task\n\n- [ ] 推进中\n"
        transcript = [
            _make_tool_use("MultiEdit", {
                "file_path": "/proj/.agent-harness/current-task.md",
                "edits": [{"old_string": "a", "new_string": "b"}],
            }),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj, transcript_lines=transcript)
            self.assertEqual(r.stdout.strip(), "")

    def test_transcript_bash_writes_passes(self) -> None:
        """Bash 命令字符串里含 current-task.md(echo > / sed -i 等) → 放行。"""
        body = "# Task\n\n- [ ] 推进中\n"
        transcript = [
            _make_tool_use("Bash", {
                "command": "echo '## 状态:done' >> .agent-harness/current-task.md",
                "description": "更新进度",
            }),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj, transcript_lines=transcript)
            self.assertEqual(r.stdout.strip(), "")

    def test_transcript_only_read_blocks(self) -> None:
        """只 Read 不算管理——AI 看了文件但没改 + mtime 老 + 未勾 → block。"""
        body = "# Task\n\n- [ ] 还没勾\n"
        transcript = [
            _make_tool_use("Read", {
                "file_path": "/proj/.agent-harness/current-task.md",
            }),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            cur = proj / ".agent-harness" / "current-task.md"
            _set_mtime_age(cur, 7200)  # 2 小时前
            r = _run_stop(proj, transcript_lines=transcript)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block",
                             "Read 不算行为信号,加上 mtime 老 + 未勾应该 block")

    # === mtime 兜底:跨会话续做时,文件最近改过 → 放行 ===

    def test_recent_mtime_passes(self) -> None:
        """transcript 无写入但 mtime 最近 5 分钟 → 放行(跨会话续做场景)。"""
        body = "# Task\n\n- [ ] 跨会话续做\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            # 不传 transcript_lines + 不动 mtime(当前时间) → 应放行
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "",
                             "Recent mtime should pass even without transcript signal")

    def test_old_mtime_no_transcript_blocks(self) -> None:
        """无 transcript + mtime > 30 分钟 + 未勾 → block(真保护场景)。"""
        body = "# Task\n\n- [ ] 静默丢的进度\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            cur = proj / ".agent-harness" / "current-task.md"
            _set_mtime_age(cur, 7200)  # 2 小时前
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block",
                             "Old mtime + no transcript + unchecked must block (核心保护场景)")

    def test_mtime_threshold_env_override(self) -> None:
        """HARNESS_STOP_HOOK_MTIME_SECONDS=10 + mtime 60 秒前 → block(阈值生效)。"""
        body = "# Task\n\n- [ ] 未完\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            cur = proj / ".agent-harness" / "current-task.md"
            _set_mtime_age(cur, 60)
            r = _run_stop(proj, extra_env={"HARNESS_STOP_HOOK_MTIME_SECONDS": "10"})
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block",
                             "环境变量阈值 10s + mtime 60s 前应当触发 block")

    # === 占位符识别:任务已收尾 ===

    def test_placeholder_no_task_passes(self) -> None:
        """文件含「(无进行中的任务)」占位符 → 放行(无视未勾 checkbox 残留)。"""
        body = "# Current Task\n\n（无进行中的任务）\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            cur = proj / ".agent-harness" / "current-task.md"
            _set_mtime_age(cur, 7200)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "")

    # === 8 类历史误拦 case 回归(transcript 命中即放行) ===

    def _assert_passes_with_write_signal(self, body: str, label: str) -> None:
        """共用断言:有 Write current-task.md 信号时,任意内容形式都放行。"""
        transcript = [
            _make_tool_use("Write", {
                "file_path": "/proj/.agent-harness/current-task.md",
                "content": body,
            }),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            cur = proj / ".agent-harness" / "current-task.md"
            _set_mtime_age(cur, 7200)  # 故意把 mtime 调老,验证 transcript 信号独立放行
            r = _run_stop(proj, transcript_lines=transcript)
            self.assertEqual(r.returncode, 0, f"{label}: stderr={r.stderr}")
            self.assertEqual(r.stdout.strip(), "",
                             f"{label}: transcript Write 应放行,got {r.stdout!r}")

    def test_regression_synonym_phase_field(self) -> None:
        self._assert_passes_with_write_signal(
            "# Task\n\n## 阶段：调研中\n\n- [ ] todo\n",
            "同义词字段名 ## 阶段:")

    def test_regression_synonym_progress_field(self) -> None:
        self._assert_passes_with_write_signal(
            "# Task\n\n## 进度：50%\n\n- [ ] todo\n",
            "同义词字段名 ## 进度:")

    def test_regression_synonym_status_english(self) -> None:
        self._assert_passes_with_write_signal(
            "# Task\n\n## Status: pending\n\n- [ ] todo\n",
            "英文字段名 ## Status:")

    def test_regression_h1_state_heading(self) -> None:
        self._assert_passes_with_write_signal(
            "# 状态：待验证\n\n- [ ] todo\n",
            "标题级别 # 状态: (1 个井号)")

    def test_regression_h3_state_heading(self) -> None:
        self._assert_passes_with_write_signal(
            "# Task\n\n### 状态：待验证\n\n- [ ] todo\n",
            "标题级别 ### 状态: (3 个井号)")

    def test_regression_bold_state(self) -> None:
        self._assert_passes_with_write_signal(
            "# Task\n\n**状态**：待验证\n\n- [ ] todo\n",
            "粗体非标题 **状态**:")

    def test_regression_blockquote_state(self) -> None:
        self._assert_passes_with_write_signal(
            "# Task\n\n> ## 状态：待验证\n\n- [ ] todo\n",
            "块引用 > ## 状态:")

    def test_regression_bom_file(self) -> None:
        self._assert_passes_with_write_signal(
            "﻿## 状态：待验证\n\n- [ ] todo\n",
            "BOM 开头文件")

    def test_regression_nested_subcheckbox(self) -> None:
        self._assert_passes_with_write_signal(
            "# Task\n\n- [x] 顶层完成\n  - [ ] 子项占位\n",
            "嵌套缩进的子 checkbox")

    def test_regression_codeblock_unchecked(self) -> None:
        self._assert_passes_with_write_signal(
            "# Task\n\n参考片段:\n```md\n- [ ] 这是教程示例\n```\n",
            "代码块里的 - [ ] 教程示例")

    # === 降级路径:transcript 缺失/损坏时 mtime 兜底,都不满足才 block ===

    def test_missing_transcript_path_falls_back_to_mtime(self) -> None:
        """stdin 无 transcript_path 字段 + mtime 最近 → 放行(mtime 兜底生效)。"""
        body = "# Task\n\n- [ ] 推进中\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj, stdin_json='{"session_id":"x"}')  # 无 transcript_path
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "",
                             "缺 transcript_path 时 mtime 最近应放行")

    def test_invalid_transcript_path_falls_back(self) -> None:
        """transcript_path 指向不存在文件 + mtime 老 → block(降级安全)。"""
        body = "# Task\n\n- [ ] 推进中\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            cur = proj / ".agent-harness" / "current-task.md"
            _set_mtime_age(cur, 7200)
            r = _run_stop(
                proj,
                stdin_json='{"transcript_path":"/nonexistent/path.jsonl"}',
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block",
                             "transcript 不存在 + mtime 老 + 未勾应 block (降级安全)")

    def test_corrupt_transcript_blocks_when_old(self) -> None:
        """transcript 是 garbage(非 JSON)+ mtime 老 → block(python 解析失败安全降级)。"""
        body = "# Task\n\n- [ ] 推进中\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            cur = proj / ".agent-harness" / "current-task.md"
            _set_mtime_age(cur, 7200)
            transcript = proj / "transcript.jsonl"
            transcript.write_text("this is not json at all\n{garbage\n", encoding="utf-8")
            r = _run_stop(
                proj,
                stdin_json=json.dumps({"transcript_path": str(transcript)}),
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block",
                             "transcript 损坏 + mtime 老 应安全降级到 block")


class PreCompactHookTests(unittest.TestCase):
    def test_appends_audit_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body="")
            r = _run_precompact(proj, stdin_json='{"trigger":"auto"}')
            self.assertEqual(r.returncode, 0, r.stderr)
            audit = proj / ".agent-harness" / "audit.jsonl"
            self.assertTrue(audit.is_file())
            line = audit.read_text(encoding="utf-8").strip()
            data = json.loads(line)
            self.assertEqual(data["op"], "update")
            self.assertEqual(data["file"], "current-task.md")
            self.assertEqual(data["agent"], "test-runner")
            self.assertIn("pre-compact", data["summary"])
            self.assertIn("auto", data["summary"])

    def test_emits_stderr_hint(self) -> None:
        """Claude Code injects stderr into system-message — must contain guidance."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body="")
            r = _run_precompact(proj)
            self.assertIn("压缩", r.stderr)
            self.assertIn("current-task.md", r.stderr)
            self.assertIn("/compound", r.stderr)

    def test_does_not_block_on_malformed_stdin(self) -> None:
        """Even with garbage stdin, PreCompact must not fail (no decision control)."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body="")
            r = _run_precompact(proj, stdin_json="not-json-at-all")
            self.assertEqual(r.returncode, 0)
            # audit must still be written with trigger=unknown
            audit = proj / ".agent-harness" / "audit.jsonl"
            self.assertTrue(audit.is_file())
            self.assertIn("unknown", audit.read_text(encoding="utf-8"))


class SettingsJsonContractTests(unittest.TestCase):
    """Verify settings.json.tmpl has the right structure per /source-verify findings."""

    def _load(self) -> dict:
        raw = SETTINGS_TMPL.read_text(encoding="utf-8")
        # Template contains {{test_command_shell}} — strip for JSON parse
        stripped = raw.replace("{{test_command_shell}}", "TEST_CMD_PLACEHOLDER")
        return json.loads(stripped)

    def test_has_stop_and_precompact(self) -> None:
        s = self._load()
        self.assertIn("Stop", s["hooks"])
        self.assertIn("PreCompact", s["hooks"])

    def test_stop_has_no_matcher(self) -> None:
        """Per docs: Stop doesn't support matcher, adding it is silently ignored.
        We omit to stay spec-compliant."""
        s = self._load()
        for block in s["hooks"]["Stop"]:
            self.assertNotIn("matcher", block,
                             "Stop hook must not declare a matcher field (spec: not supported)")

    def test_stop_command_invokes_stop_sh(self) -> None:
        s = self._load()
        cmd = s["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("stop.sh", cmd)

    def test_precompact_command_invokes_pre_compact_sh(self) -> None:
        s = self._load()
        cmd = s["hooks"]["PreCompact"][0]["hooks"][0]["command"]
        self.assertIn("pre-compact.sh", cmd)

    def test_preserves_existing_events(self) -> None:
        """Regression guard — adding Stop/PreCompact must not drop SessionStart/PreToolUse."""
        s = self._load()
        self.assertIn("SessionStart", s["hooks"])
        self.assertIn("PreToolUse", s["hooks"])


if __name__ == "__main__":
    unittest.main()
