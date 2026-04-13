"""Tests for JSON spec parsing in agent_harness.squad.spec (Issue #25 迁 yaml→json)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_harness.squad.spec import SpecError, parse_spec


class ParseSpecTests(unittest.TestCase):
    def _write(self, data: dict) -> Path:
        tmp = Path(tempfile.mkdtemp()) / "spec.json"
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return tmp

    def test_parse_valid_json_spec(self) -> None:
        path = self._write({
            "task_id": "auth-rewrite",
            "base_branch": "master",
            "workers": [
                {"name": "scout-auth", "capability": "scout",
                 "prompt": "探索 src/auth/"},
                {"name": "builder-auth", "capability": "builder",
                 "depends_on": ["scout-auth"], "prompt": "实现 auth"},
            ],
        })
        s = parse_spec(path)
        self.assertEqual(s.task_id, "auth-rewrite")
        self.assertEqual(s.base_branch, "master")
        self.assertEqual(len(s.workers), 2)
        self.assertEqual(s.workers[0].name, "scout-auth")
        self.assertEqual(s.workers[0].capability, "scout")
        self.assertEqual(s.workers[1].depends_on, ["scout-auth"])

    def test_reject_circular_dependency(self) -> None:
        path = self._write({
            "task_id": "circular",
            "base_branch": "main",
            "workers": [
                {"name": "a", "capability": "builder",
                 "depends_on": ["b"], "prompt": "a"},
                {"name": "b", "capability": "builder",
                 "depends_on": ["a"], "prompt": "b"},
            ],
        })
        with self.assertRaises(SpecError) as ctx:
            parse_spec(path)
        self.assertIn("循环", str(ctx.exception))

    def test_reject_unknown_capability(self) -> None:
        path = self._write({
            "task_id": "bad-cap",
            "base_branch": "main",
            "workers": [{"name": "w1", "capability": "overlord", "prompt": "x"}],
        })
        with self.assertRaises(SpecError) as ctx:
            parse_spec(path)
        self.assertIn("capability", str(ctx.exception))

    def test_reject_missing_required_fields(self) -> None:
        path = self._write({"task_id": "missing-workers", "base_branch": "main"})
        with self.assertRaises(SpecError):
            parse_spec(path)

    def test_reject_unsafe_worker_name(self) -> None:
        path = self._write({
            "task_id": "injection",
            "base_branch": "main",
            "workers": [
                {"name": "w1; rm -rf /", "capability": "builder", "prompt": "x"},
            ],
        })
        with self.assertRaises(SpecError) as ctx:
            parse_spec(path)
        self.assertIn("名称", str(ctx.exception))

    def test_reject_unknown_dependency(self) -> None:
        path = self._write({
            "task_id": "dangling-dep",
            "base_branch": "main",
            "workers": [
                {"name": "a", "capability": "builder",
                 "depends_on": ["ghost"], "prompt": "x"},
            ],
        })
        with self.assertRaises(SpecError) as ctx:
            parse_spec(path)
        self.assertIn("依赖", str(ctx.exception))

    def test_reject_duplicate_worker_names(self) -> None:
        path = self._write({
            "task_id": "dup",
            "base_branch": "main",
            "workers": [
                {"name": "a", "capability": "builder", "prompt": "x"},
                {"name": "a", "capability": "scout", "prompt": "y"},
            ],
        })
        with self.assertRaises(SpecError):
            parse_spec(path)

    def test_reject_yaml_suffix_with_migration_hint(self) -> None:
        """Issue #25 破坏性变更：.yaml spec 明确拒绝，给迁移提示。"""
        tmp = Path(tempfile.mkdtemp()) / "spec.yaml"
        tmp.write_text("task_id: x\n", encoding="utf-8")
        with self.assertRaises(SpecError) as ctx:
            parse_spec(tmp)
        self.assertIn("JSON", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
