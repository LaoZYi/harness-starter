from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agent_harness.discovery import discover_project


class DiscoverProjectTests(unittest.TestCase):
    def test_detects_python_project_from_pyproject_and_makefile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src" / "sample_app").mkdir(parents=True)
            (root / "tests").mkdir()
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "src" / "sample_app" / "cli.py").write_text("", encoding="utf-8")
            (root / "pyproject.toml").write_text(
                textwrap.dedent(
                    """
                    [project]
                    name = "sample-app"
                    description = "Sample service"
                    """
                ).strip(),
                encoding="utf-8",
            )
            (root / "Makefile").write_text(
                textwrap.dedent(
                    """
                    check:
                    test:
                    ci:
                    run:
                    """
                ).strip(),
                encoding="utf-8",
            )
            (root / ".github" / "workflows" / "deploy.yml").write_text("name: deploy", encoding="utf-8")

            profile = discover_project(root)

        self.assertEqual(profile.project_name, "sample-app")
        self.assertEqual(profile.language, "python")
        self.assertEqual(profile.project_type, "cli-tool")
        self.assertEqual(profile.run_command, "make run")
        self.assertEqual(profile.check_command, "make check")
        self.assertTrue(profile.has_production)
        self.assertIn("src", profile.source_paths)


if __name__ == "__main__":
    unittest.main()

