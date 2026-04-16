"""Contract tests for /digest-meeting skill (common layer).

/digest-meeting 是 common 层新增技能，把多人讨论的语音转文字记录转为框架
可消费的结构化产物。与 /process-notes 并列，定位为 /lfg 的前置源头。

这些测试锁定：
- 模板文件存在且包含 7 步执行指令
- 声明了 6 类信号 + 4 种格式兼容
- 占位符齐全
- harness init 后命令文件正确生成
- skills-registry.json 有对应条目（category=meta, expected_in_lfg=false）
"""
from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILE = (
    ROOT
    / "src"
    / "agent_harness"
    / "templates"
    / "common"
    / ".claude"
    / "commands"
    / "digest-meeting.md.tmpl"
)
REGISTRY_FILE = (
    ROOT
    / "src"
    / "agent_harness"
    / "templates"
    / "superpowers"
    / "skills-registry.json"
)

_PLACEHOLDER_RE = re.compile(r"\{\{\s*[a-z0-9_]+\s*\}\}")

_BASE_ANSWERS: dict[str, object] = {
    "project_name": "Digest Test",
    "project_slug": "digest-test",
    "summary": "digest-meeting integration test",
    "project_type": "backend-service",
    "language": "python",
    "package_manager": "pip",
    "run_command": "python -m app",
    "test_command": "pytest",
    "check_command": "ruff check .",
    "ci_command": "make ci",
    "deploy_target": "docker",
    "has_production": False,
    "sensitivity": "standard",
}


class DigestMeetingTemplateTests(unittest.TestCase):
    """Template file structural contract."""

    def test_template_file_exists(self) -> None:
        self.assertTrue(
            TEMPLATE_FILE.is_file(),
            f"missing template: {TEMPLATE_FILE}",
        )

    def test_template_contains_seven_steps(self) -> None:
        """模板必须包含 7 步执行指令的锚点关键词。"""
        body = TEMPLATE_FILE.read_text(encoding="utf-8")
        # 每步用 "第 N 步" 作为锚点（中文数字或阿拉伯数字）
        step_markers = ["第 1 步", "第 2 步", "第 3 步",
                        "第 4 步", "第 5 步", "第 6 步", "第 7 步"]
        for marker in step_markers:
            self.assertIn(marker, body, f"模板缺少锚点：{marker}")

    def test_template_declares_six_signal_types(self) -> None:
        """6 类信号必须显式列出。"""
        body = TEMPLATE_FILE.read_text(encoding="utf-8")
        signals = ["决策", "需求", "约束", "待办", "开放问题", "参与者"]
        for sig in signals:
            self.assertIn(sig, body, f"模板缺少信号类别：{sig}")

    def test_template_declares_format_compat(self) -> None:
        """4 种输入格式必须显式声明（启发式检测）。"""
        body = TEMPLATE_FILE.read_text(encoding="utf-8")
        formats = ["飞书", "说话人", "时间戳", "纯文本"]
        for fmt in formats:
            self.assertIn(fmt, body, f"模板缺少格式声明：{fmt}")

    def test_template_has_required_placeholders(self) -> None:
        """必须使用 common 层占位符（不用 <<SKILL_*>>）。"""
        body = TEMPLATE_FILE.read_text(encoding="utf-8")
        for ph in ["{{project_name}}", "{{project_type}}", "{{check_command}}"]:
            self.assertIn(ph, body, f"模板缺少占位符：{ph}")
        # 不允许引入 superpowers 层的双尖括号占位符
        self.assertNotIn("<<SKILL_", body,
                         "common 层模板不应使用 <<SKILL_*>> 占位符")

    def test_template_mentions_both_modes(self) -> None:
        """init / iterate 两种模式必须都提到。"""
        body = TEMPLATE_FILE.read_text(encoding="utf-8")
        self.assertIn("init", body, "模板应提到 init 模式")
        self.assertIn("iterate", body, "模板应提到 iterate 模式")

    def test_template_delegates_to_process_notes_and_lfg(self) -> None:
        """init 串 /process-notes，iterate 提示 /lfg。"""
        body = TEMPLATE_FILE.read_text(encoding="utf-8")
        self.assertIn("/process-notes", body, "init 模式应引用 /process-notes")
        self.assertIn("/lfg", body, "iterate 模式应提示 /lfg")

    def test_template_handles_meta_project(self) -> None:
        """meta 项目应委托给 /meta-create-task。"""
        body = TEMPLATE_FILE.read_text(encoding="utf-8")
        self.assertIn("/meta-create-task", body,
                      "模板应声明 meta 项目委托给 /meta-create-task")

    def test_template_declares_digested_output_dir(self) -> None:
        """产物应写入 notes/digested/，不动原始文件。"""
        body = TEMPLATE_FILE.read_text(encoding="utf-8")
        self.assertIn("notes/digested", body,
                      "模板应声明产物目录 notes/digested/")
        self.assertIn("processed", body,
                      "模板应声明原始文件用 <!-- processed --> 标记")


class DigestMeetingInitTests(unittest.TestCase):
    """End-to-end: harness init generates the command with placeholders replaced."""

    def test_init_generates_digest_meeting_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            cmd_path = root / ".claude" / "commands" / "digest-meeting.md"
            self.assertTrue(cmd_path.exists(),
                            "digest-meeting.md should be generated at init")
            body = cmd_path.read_text(encoding="utf-8")
            # 占位符已替换
            self.assertNotRegex(
                body, _PLACEHOLDER_RE,
                "digest-meeting.md 中仍有未替换占位符",
            )
            self.assertIn("Digest Test", body,
                          "project_name 占位符应被替换为 'Digest Test'")


class DigestMeetingRegistryTests(unittest.TestCase):
    """skills-registry.json 注册约定。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))

    def _find_entry(self) -> dict:
        for s in self.registry["skills"]:
            if s["id"] == "digest-meeting":
                return s
        self.fail("skills-registry.json 缺少 digest-meeting 条目")

    def test_registry_contains_entry(self) -> None:
        ids = {s["id"] for s in self.registry["skills"]}
        self.assertIn("digest-meeting", ids,
                      "skills-registry.json 应包含 digest-meeting")

    def test_registry_entry_is_meta_excluded_from_lfg(self) -> None:
        entry = self._find_entry()
        self.assertEqual(entry["category"], "meta",
                         "digest-meeting 应归为 meta（对标 process-notes）")
        self.assertFalse(entry["expected_in_lfg"],
                         "digest-meeting 不应 expected_in_lfg=true（它是 lfg 前置源头）")
        self.assertIn("exclusion_reason", entry,
                      "expected_in_lfg=false 必须说明 exclusion_reason")
        self.assertTrue(entry["exclusion_reason"].strip(),
                        "exclusion_reason 不能为空")
        # lfg_stage 应为空列表（不参与阶段渲染）
        self.assertEqual(entry.get("lfg_stage") or [], [])


if __name__ == "__main__":
    unittest.main()
