from __future__ import annotations

import json
import unittest

from agent_harness._merge3 import CONFLICT_CURRENT, CONFLICT_NEW, json_merge, merge3


class Merge3NoConflictTests(unittest.TestCase):
    def test_user_unchanged_takes_new(self) -> None:
        base = "line1\nline2\nline3\n"
        current = base  # user didn't change
        new = "line1\nline2-updated\nline3\n"
        merged, conflicts = merge3(base, current, new)
        self.assertEqual(conflicts, [])
        self.assertIn("line2-updated", merged)

    def test_framework_unchanged_keeps_user(self) -> None:
        base = "line1\nline2\nline3\n"
        current = "line1\nuser-edit\nline3\n"
        new = base  # framework didn't change
        merged, conflicts = merge3(base, current, new)
        self.assertEqual(conflicts, [])
        self.assertIn("user-edit", merged)

    def test_both_same_change(self) -> None:
        base = "line1\nline2\n"
        current = "line1\nchanged\n"
        new = "line1\nchanged\n"
        merged, conflicts = merge3(base, current, new)
        self.assertEqual(conflicts, [])
        self.assertEqual(merged, "line1\nchanged\n")

    def test_different_regions_both_applied(self) -> None:
        base = "aaa\nbbb\nccc\nddd\n"
        current = "aaa\nBBB\nccc\nddd\n"  # user changed line 2
        new = "aaa\nbbb\nccc\nDDD\n"  # framework changed line 4
        merged, conflicts = merge3(base, current, new)
        self.assertEqual(conflicts, [])
        self.assertIn("BBB", merged)
        self.assertIn("DDD", merged)


class Merge3ConflictTests(unittest.TestCase):
    def test_same_line_conflict(self) -> None:
        base = "line1\noriginal\nline3\n"
        current = "line1\nuser-version\nline3\n"
        new = "line1\nframework-version\nline3\n"
        merged, conflicts = merge3(base, current, new)
        self.assertTrue(len(conflicts) > 0)
        self.assertIn(CONFLICT_CURRENT, merged)
        self.assertIn(CONFLICT_NEW, merged)
        self.assertIn("user-version", merged)
        self.assertIn("framework-version", merged)

    def test_conflict_preserves_surrounding(self) -> None:
        base = "keep1\noriginal\nkeep2\n"
        current = "keep1\nuser\nkeep2\n"
        new = "keep1\nfw\nkeep2\n"
        merged, conflicts = merge3(base, current, new)
        self.assertIn("keep1", merged)
        self.assertIn("keep2", merged)


class Merge3NewSectionTests(unittest.TestCase):
    def test_framework_adds_section(self) -> None:
        base = "# Title\n\ncontent\n"
        current = "# Title\n\nuser content\n"  # user edited
        new = "# Title\n\ncontent\n\n## New Section\n\nnew stuff\n"  # framework added
        merged, conflicts = merge3(base, current, new)
        self.assertIn("New Section", merged)
        self.assertIn("user content", merged)


class JsonMergeTests(unittest.TestCase):
    def test_user_keys_preserved(self) -> None:
        base = json.dumps({"a": 1, "b": 2})
        current = json.dumps({"a": 1, "b": 2, "user_key": "mine"})
        new = json.dumps({"a": 1, "b": 3})
        merged, _ = json_merge(base, current, new)
        data = json.loads(merged)
        self.assertEqual(data["user_key"], "mine")

    def test_framework_keys_updated(self) -> None:
        base = json.dumps({"version": "1.0", "user_note": "hi"})
        current = json.dumps({"version": "1.0", "user_note": "hi"})
        new = json.dumps({"version": "2.0", "user_note": "hi"})
        merged, _ = json_merge(base, current, new, framework_keys={"version"})
        data = json.loads(merged)
        self.assertEqual(data["version"], "2.0")

    def test_new_key_added(self) -> None:
        base = json.dumps({"a": 1})
        current = json.dumps({"a": 1})
        new = json.dumps({"a": 1, "new_feature": True})
        merged, warnings = json_merge(base, current, new)
        data = json.loads(merged)
        self.assertTrue(data["new_feature"])
        self.assertTrue(any("新增" in w for w in warnings))

    def test_invalid_user_json_falls_back(self) -> None:
        base = json.dumps({"a": 1})
        current = "NOT VALID JSON"
        new = json.dumps({"a": 2})
        merged, warnings = json_merge(base, current, new)
        data = json.loads(merged)
        self.assertEqual(data["a"], 2)
        self.assertTrue(any("格式错误" in w for w in warnings))
