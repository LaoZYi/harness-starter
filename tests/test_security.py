"""测试 agent_harness.security 模块的输入校验函数。

策略：
- sanitize_name: 与 agent.py `_AGENT_ID_RE` / squad/spec.py `_NAME_PATTERN` 等价
- sanitize_path: 确保路径不逃逸 base_dir（含符号链接）
- sanitize_content: 截断模式为抛异常（显式告警），null / 非常规控制字符剥除
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from agent_harness.security import (
    SecurityError,
    sanitize_content,
    sanitize_name,
    sanitize_path,
)


class SanitizeNameTests(unittest.TestCase):
    def test_accepts_valid_lowercase(self):
        self.assertEqual(sanitize_name("scout"), "scout")
        self.assertEqual(sanitize_name("worker-1"), "worker-1")
        self.assertEqual(sanitize_name("a"), "a")
        self.assertEqual(sanitize_name("0agent"), "0agent")
        self.assertEqual(sanitize_name("a" * 31), "a" * 31)

    def test_rejects_empty(self):
        with self.assertRaises(SecurityError):
            sanitize_name("")

    def test_rejects_too_long(self):
        with self.assertRaises(SecurityError):
            sanitize_name("a" * 32)

    def test_rejects_uppercase(self):
        with self.assertRaises(SecurityError):
            sanitize_name("Scout")

    def test_rejects_leading_dash(self):
        with self.assertRaises(SecurityError):
            sanitize_name("-worker")

    def test_rejects_underscore(self):
        with self.assertRaises(SecurityError):
            sanitize_name("worker_1")

    def test_rejects_path_separators(self):
        for bad in ("worker/1", "worker\\1", "../worker"):
            with self.assertRaises(SecurityError):
                sanitize_name(bad)

    def test_rejects_null_byte(self):
        with self.assertRaises(SecurityError):
            sanitize_name("work\x00er")

    def test_rejects_non_string(self):
        with self.assertRaises(SecurityError):
            sanitize_name(None)  # type: ignore[arg-type]
        with self.assertRaises(SecurityError):
            sanitize_name(42)  # type: ignore[arg-type]

    def test_security_error_is_value_error(self):
        """向后兼容：现有 except ValueError 继续生效"""
        with self.assertRaises(ValueError):
            sanitize_name("BAD")


class SanitizePathTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        (self.base / "ok").mkdir()
        (self.base / "ok" / "file.txt").write_text("hi")

    def tearDown(self):
        self._tmp.cleanup()

    def test_accepts_relative_inside(self):
        result = sanitize_path("ok/file.txt", self.base)
        self.assertEqual(result, self.base / "ok" / "file.txt")

    def test_accepts_nested(self):
        result = sanitize_path("ok", self.base)
        self.assertEqual(result, self.base / "ok")

    def test_rejects_parent_traversal(self):
        with self.assertRaises(SecurityError):
            sanitize_path("../outside", self.base)

    def test_rejects_deep_traversal(self):
        with self.assertRaises(SecurityError):
            sanitize_path("ok/../../outside", self.base)

    def test_rejects_absolute_escape(self):
        with self.assertRaises(SecurityError):
            sanitize_path("/etc/passwd", self.base)

    def test_rejects_symlink_escape(self):
        outside = Path(tempfile.mkdtemp())
        try:
            link = self.base / "escape"
            os.symlink(outside, link)
            with self.assertRaises(SecurityError):
                sanitize_path("escape", self.base)
        finally:
            import shutil

            shutil.rmtree(outside, ignore_errors=True)

    def test_rejects_null_byte(self):
        with self.assertRaises(SecurityError):
            sanitize_path("ok\x00/file", self.base)

    def test_accepts_base_itself(self):
        self.assertEqual(sanitize_path(".", self.base), self.base)


class SanitizeContentTests(unittest.TestCase):
    def test_accepts_normal_text(self):
        text = "hello world\n第二行\ttab"
        self.assertEqual(sanitize_content(text), text)

    def test_strips_null_bytes(self):
        self.assertEqual(sanitize_content("hel\x00lo"), "hello")

    def test_strips_control_chars_but_keeps_whitespace(self):
        raw = "a\x01b\x02c\nd\te\rf\x7fg"
        self.assertEqual(sanitize_content(raw), "abc\nd\te\rfg")

    def test_oversize_raises(self):
        """超长时抛异常而非静默截断，避免掩盖攻击"""
        with self.assertRaises(SecurityError):
            sanitize_content("x" * 100_001)

    def test_oversize_custom_limit(self):
        with self.assertRaises(SecurityError):
            sanitize_content("x" * 11, max_len=10)
        self.assertEqual(sanitize_content("x" * 10, max_len=10), "x" * 10)

    def test_rejects_non_string(self):
        with self.assertRaises(SecurityError):
            sanitize_content(b"bytes")  # type: ignore[arg-type]

    def test_empty_is_allowed(self):
        self.assertEqual(sanitize_content(""), "")


if __name__ == "__main__":
    unittest.main()
