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

    def test_meta_from_services_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "services").mkdir()
            (root / "services" / "registry.yaml").write_text("payment-service:\n  repo: git@example.com/payment\n", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "meta")

    def test_meta_not_detected_when_source_code_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "services").mkdir()
            (root / "services" / "registry.yaml").write_text("payment-service:\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
            profile = discover_project(root)
        self.assertNotEqual(profile.project_type, "meta")

    # --- web-app detection ---

    def test_web_app_from_next_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "next.config.js").write_text("module.exports = {}", encoding="utf-8")
            (root / "package.json").write_text('{"name": "web"}', encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "web-app")

    def test_web_app_from_vite_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "vite.config.ts").write_text("export default {}", encoding="utf-8")
            (root / "package.json").write_text('{"name": "web"}', encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "web-app")

    # --- cli-tool detection ---

    def test_cli_tool_from_package_json_bin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pkg = {"name": "my-cli", "bin": {"mycli": "./bin/cli.js"}}
            (root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "cli-tool")

    def test_cli_tool_from_python_cli_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "requirements.txt").write_text("click\n", encoding="utf-8")
            pkg = root / "src" / "myapp"
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (pkg / "cli.py").write_text("import click", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "cli-tool")

    # --- worker detection ---

    def test_worker_from_wrangler_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "wrangler.toml").write_text('name = "my-worker"', encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "worker")

    def test_worker_from_celery_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "celeryconfig.py").write_text("broker_url = 'redis://localhost'", encoding="utf-8")
            (root / "requirements.txt").write_text("celery\n", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "worker")

    # --- library detection ---

    def test_library_from_python_package(self) -> None:
        """Python project with setup.cfg/pyproject.toml, no Dockerfile, no server framework."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "setup.cfg").write_text("[metadata]\nname = mylib\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('[build-system]\nrequires = ["setuptools"]\n[tool.setuptools]\npackages = ["mylib"]\n', encoding="utf-8")
            pkg = root / "src" / "mylib"
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text("__version__ = '0.1.0'", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "library")

    def test_library_from_js_package_with_main_no_bin(self) -> None:
        """JS package with main/exports but no bin field → library, not cli-tool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pkg = {"name": "my-lib", "main": "dist/index.js", "module": "dist/index.mjs"}
            (root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "library")

    def test_library_from_gemspec(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "mylib.gemspec").write_text("Gem::Specification.new do |s|\nend", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "library")

    # --- backend-service detection (default fallback + positive signals) ---

    def test_backend_service_from_dockerfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "Dockerfile").write_text("FROM python:3.11", encoding="utf-8")
            (root / "requirements.txt").write_text("flask\n", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "backend-service")

    def test_backend_service_as_default_fallback(self) -> None:
        """Empty project with no signals falls back to backend-service."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("print('hello')", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "backend-service")

    # --- priority tests ---

    def test_monorepo_priority_over_web_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pnpm-workspace.yaml").write_text("packages:\n  - 'apps/*'\n", encoding="utf-8")
            (root / "package.json").write_text('{"name": "mono"}', encoding="utf-8")
            (root / "next.config.js").write_text("module.exports = {}", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "monorepo")

    # --- new detection signal tests ---

    def test_web_app_from_webpack_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "webpack.config.js").write_text("module.exports = {}", encoding="utf-8")
            (root / "package.json").write_text('{"name": "web"}', encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "web-app")

    def test_web_app_from_angular_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "angular.json").write_text('{"version": 1}', encoding="utf-8")
            (root / "package.json").write_text('{"name": "web"}', encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "web-app")

    def test_mobile_app_from_expo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pkg = {"name": "app", "dependencies": {"expo": "~49.0.0"}}
            (root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "mobile-app")

    def test_data_pipeline_from_prefect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "prefect.yaml").write_text("name: my-flow\n", encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "data-pipeline")

    def test_monorepo_priority_over_library(self) -> None:
        """Package.json with both main and workspaces should be monorepo, not library."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pkg = {"name": "mono-lib", "main": "dist/index.js", "workspaces": ["packages/*"]}
            (root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "monorepo")

    def test_cli_tool_priority_over_library(self) -> None:
        """Package.json with both bin and main should be cli-tool, not library."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pkg = {"name": "my-tool", "main": "dist/index.js", "bin": {"mytool": "./bin/cli.js"}}
            (root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
            profile = discover_project(root)
        self.assertEqual(profile.project_type, "cli-tool")


if __name__ == "__main__":
    unittest.main()
