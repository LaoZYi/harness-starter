from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_harness.assessment import assess_project
from agent_harness.models import ProjectProfile


def _make_profile(**overrides: object) -> ProjectProfile:
    defaults: dict[str, object] = dict(
        root="/tmp/example",
        project_name="example",
        project_slug="example",
        summary="demo",
        project_type="backend-service",
        language="python",
        package_manager="pip",
        run_command="TODO",
        test_command="TODO",
        check_command="TODO",
        ci_command="TODO",
        deploy_target="未定",
        has_production=False,
        sensitivity="standard",
        source_paths=["src"],
        test_paths=[],
        docs_paths=[],
        ci_paths=[],
        external_systems=[],
        notes=[],
    )
    defaults.update(overrides)
    return ProjectProfile(**defaults)


class AssessProjectTests(unittest.TestCase):
    def test_flags_missing_commands_and_tests(self) -> None:
        profile = _make_profile()
        result = assess_project(profile)
        self.assertEqual(result.readiness, "low")
        self.assertTrue(result.gaps)
        self.assertTrue(any("运行命令未识别" in gap for gap in result.gaps))
        self.assertTrue(result.recommendations)

    def test_high_readiness_with_all_fields(self) -> None:
        profile = _make_profile(
            run_command="make run",
            test_command="make test",
            check_command="make check",
            ci_command="make ci",
            test_paths=["tests"],
            ci_paths=[".github/workflows"],
        )
        result = assess_project(profile)
        self.assertEqual(result.readiness, "high")
        self.assertGreaterEqual(result.score, 80)

    def test_medium_readiness_with_some_gaps(self) -> None:
        profile = _make_profile(
            run_command="make run",
            test_command="make test",
            test_paths=["tests"],
        )
        result = assess_project(profile)
        self.assertEqual(result.readiness, "medium")

    def test_confidence_low_with_many_unknowns(self) -> None:
        profile = _make_profile(language="unknown")
        result = assess_project(profile)
        self.assertEqual(result.confidence, "low")

    def test_confidence_high_with_few_unknowns(self) -> None:
        profile = _make_profile(
            run_command="make run",
            test_command="make test",
            check_command="make check",
            ci_command="make ci",
            deploy_target="docker",
        )
        result = assess_project(profile)
        self.assertEqual(result.confidence, "high")

    def test_dimensions_populated_when_root_given(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text("# Example\n\n" + "description\n" * 15, encoding="utf-8")
            (root / "conftest.py").write_text("", encoding="utf-8")
            profile = _make_profile(root=str(root))
            result = assess_project(profile, root=root)
        self.assertIn("detection", result.dimensions)
        self.assertIn("testing", result.dimensions)
        self.assertIn("documentation", result.dimensions)
        self.assertGreater(result.dimensions["testing"], 0)
        self.assertGreater(result.dimensions["documentation"], 0)


if __name__ == "__main__":
    unittest.main()
