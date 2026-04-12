from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_harness.memory import MAX_LESSONS, MAX_TASKS, rebuild_index


class _HarnessDir:
    """Helper: create a temp harness-initialized project."""

    def __init__(self, lessons: str = "", task_log: str = "") -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".agent-harness").mkdir()
        (self.root / ".agent-harness" / "lessons.md").write_text(lessons, encoding="utf-8")
        (self.root / ".agent-harness" / "task-log.md").write_text(task_log, encoding="utf-8")

    def index_path(self) -> Path:
        return self.root / ".agent-harness" / "memory-index.md"

    def read_index(self) -> str:
        return self.index_path().read_text(encoding="utf-8")

    def cleanup(self) -> None:
        self.tmp.cleanup()


def _make_lessons(count: int) -> str:
    header = "# Lessons Learned\n\n"
    entries = "\n".join(f"## 2026-01-{i:02d} lesson {i}\n\n- detail line\n" for i in range(1, count + 1))
    return header + entries


def _make_task_log(count: int) -> str:
    header = "# Task Log\n\n"
    entries = "\n".join(f"## 2026-02-{i:02d} task {i}\n\n- done\n" for i in range(1, count + 1))
    return header + entries


class RebuildIndexNormalTests(unittest.TestCase):
    """Normal-path behaviors."""

    def test_creates_index_when_missing(self) -> None:
        h = _HarnessDir(lessons=_make_lessons(3), task_log=_make_task_log(2))
        try:
            result = rebuild_index(h.root)
            self.assertEqual(result.status, "created")
            self.assertEqual(result.lessons_count, 3)
            self.assertEqual(result.tasks_count, 2)
            self.assertTrue(h.index_path().exists())
            body = h.read_index()
            self.assertIn("lesson 3", body)
            self.assertIn("task 2", body)
        finally:
            h.cleanup()

    def test_lessons_ordered_newest_first(self) -> None:
        h = _HarnessDir(lessons=_make_lessons(3), task_log="")
        try:
            rebuild_index(h.root)
            body = h.read_index()
            pos3 = body.index("lesson 3")
            pos1 = body.index("lesson 1")
            self.assertLess(pos3, pos1)
        finally:
            h.cleanup()


class RebuildIndexBoundaryTests(unittest.TestCase):
    """Boundary cases: limits, empty sources, malformed headings."""

    def test_limits_lessons_to_max_10(self) -> None:
        h = _HarnessDir(lessons=_make_lessons(15), task_log="")
        try:
            result = rebuild_index(h.root)
            self.assertEqual(result.lessons_count, MAX_LESSONS)
            body = h.read_index()
            self.assertIn("lesson 15", body)
            self.assertIn("lesson 6", body)  # 15 - 10 + 1
            self.assertNotIn("lesson 5", body)
        finally:
            h.cleanup()

    def test_limits_tasks_to_max_5(self) -> None:
        h = _HarnessDir(lessons="", task_log=_make_task_log(8))
        try:
            result = rebuild_index(h.root)
            self.assertEqual(result.tasks_count, MAX_TASKS)
            body = h.read_index()
            self.assertIn("task 8", body)
            self.assertIn("task 4", body)  # 8 - 5 + 1
            self.assertNotIn("task 3", body)
        finally:
            h.cleanup()

    def test_empty_sources_produce_placeholders(self) -> None:
        h = _HarnessDir(lessons="", task_log="")
        try:
            result = rebuild_index(h.root)
            self.assertEqual(result.status, "created")
            self.assertEqual(result.lessons_count, 0)
            self.assertEqual(result.tasks_count, 0)
            body = h.read_index()
            self.assertIn("暂无", body)
        finally:
            h.cleanup()

    def test_missing_lessons_file_does_not_crash(self) -> None:
        h = _HarnessDir(lessons="", task_log="")
        (h.root / ".agent-harness" / "lessons.md").unlink()
        try:
            result = rebuild_index(h.root)
            self.assertEqual(result.status, "created")
            self.assertEqual(result.lessons_count, 0)
        finally:
            h.cleanup()

    def test_ignores_non_h2_lines(self) -> None:
        mixed = (
            "# Title\n\n"
            "## kept 1\n\n"
            "### subheading should be ignored\n\n"
            "some paragraph with ## inline text\n\n"
            "## kept 2\n"
        )
        h = _HarnessDir(lessons=mixed, task_log="")
        try:
            result = rebuild_index(h.root)
            self.assertEqual(result.lessons_count, 2)
            body = h.read_index()
            self.assertIn("kept 1", body)
            self.assertIn("kept 2", body)
            self.assertNotIn("subheading", body)
        finally:
            h.cleanup()

    def test_cjk_headings_preserved(self) -> None:
        lessons = "# Title\n\n## 2026-04-09 中文标题测试\n\n- 详情\n"
        h = _HarnessDir(lessons=lessons, task_log="")
        try:
            rebuild_index(h.root)
            body = h.read_index()
            self.assertIn("中文标题测试", body)
        finally:
            h.cleanup()


class RebuildIndexErrorPathTests(unittest.TestCase):
    """Error/refusal paths."""

    def test_refuses_when_index_exists_without_force(self) -> None:
        h = _HarnessDir(lessons=_make_lessons(2), task_log="")
        try:
            rebuild_index(h.root)  # creates
            original_body = h.read_index()
            result = rebuild_index(h.root)  # refuses
            self.assertEqual(result.status, "refused")
            self.assertEqual(h.read_index(), original_body)
        finally:
            h.cleanup()

    def test_force_overwrites_existing_index(self) -> None:
        h = _HarnessDir(lessons=_make_lessons(2), task_log="")
        try:
            rebuild_index(h.root)
            h.index_path().write_text("# Stale content\n", encoding="utf-8")
            result = rebuild_index(h.root, force=True)
            self.assertEqual(result.status, "rewritten")
            self.assertIn("lesson 2", h.read_index())
            self.assertNotIn("Stale content", h.read_index())
        finally:
            h.cleanup()

    def test_rejects_uninitialized_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                rebuild_index(Path(tmp))


if __name__ == "__main__":
    unittest.main()
