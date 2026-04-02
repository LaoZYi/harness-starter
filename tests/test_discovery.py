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


    def test_empty_directory_returns_unknown_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile = discover_project(root)
        self.assertEqual(profile.language, "unknown")
        self.assertEqual(profile.project_type, "backend-service")

    def test_detects_go_project_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "go.mod").write_text("module example.com/svc\n\ngo 1.21\n", encoding="utf-8")
            (root / "cmd").mkdir()
            (root / "tests").mkdir()
            profile = discover_project(root)
        self.assertEqual(profile.language, "go")
        self.assertEqual(profile.package_manager, "go-modules")
        self.assertEqual(profile.test_command, "go test ./...")
        self.assertEqual(profile.testing_framework, "go-test")


if __name__ == "__main__":
    unittest.main()

