from __future__ import annotations

import unittest

from agent_harness.assessment import assess_project
from agent_harness.models import ProjectProfile


class AssessProjectTests(unittest.TestCase):
    def test_flags_missing_commands_and_tests(self) -> None:
        profile = ProjectProfile(
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

        result = assess_project(profile)

        self.assertEqual(result.readiness, "low")
        self.assertTrue(result.gaps)
        self.assertTrue(any("运行命令未识别" in gap for gap in result.gaps))
        self.assertTrue(result.recommendations)


if __name__ == "__main__":
    unittest.main()
