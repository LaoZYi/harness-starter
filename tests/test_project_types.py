from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_harness.discovery import discover_project


class ProjectTypeDetectionTests(unittest.TestCase):
    def test_monorepo_from_pnpm_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pnpm-workspace.yaml").write_text("packages:\n  - 'packages/*'\n", encoding="utf-8")
            (root / "package.json").write_text('{"name": "mono"}', encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "monorepo")

    def test_monorepo_from_lerna(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "lerna.json").write_text('{"version": "1.0.0"}', encoding="utf-8")
            (root / "package.json").write_text('{"name": "mono"}', encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "monorepo")

    def test_monorepo_from_package_json_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pkg = {"name": "mono", "workspaces": ["packages/*"]}
            (root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "monorepo")

    def test_mobile_app_from_flutter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pubspec.yaml").write_text("name: my_app\n", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "mobile-app")

    def test_mobile_app_from_react_native(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pkg = {"name": "app", "dependencies": {"react-native": "^0.72"}}
            (root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "mobile-app")

    def test_data_pipeline_from_dbt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "dbt_project.yml").write_text("name: my_dbt\n", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "data-pipeline")

    def test_data_pipeline_from_airflow_dags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "dags").mkdir()
            (root / "dags" / "my_dag.py").write_text("", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "data-pipeline")

    def test_monorepo_priority_over_web_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pnpm-workspace.yaml").write_text("packages:\n  - 'apps/*'\n", encoding="utf-8")
            (root / "package.json").write_text('{"name": "mono"}', encoding="utf-8")
            (root / "next.config.js").write_text("module.exports = {}", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "monorepo")


if __name__ == "__main__":
    unittest.main()
