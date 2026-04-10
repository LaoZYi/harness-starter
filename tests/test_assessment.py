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


class TypeSpecificAssessmentTests(unittest.TestCase):
    """Assessment should give bonus points for type-specific project structure signals."""

    def test_backend_service_bonus_for_dockerfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
            profile = _make_profile(root=str(root), project_type="backend-service")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_web_app_bonus_for_build_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "vite.config.ts").write_text("export default {}\n", encoding="utf-8")
            profile = _make_profile(root=str(root), project_type="web-app")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_cli_tool_bonus_for_cli_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src = root / "src" / "myapp"
            src.mkdir(parents=True)
            (src / "cli.py").write_text("import click\n", encoding="utf-8")
            profile = _make_profile(root=str(root), project_type="cli-tool")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_library_bonus_for_version_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text('[project]\nname = "mylib"\nversion = "1.0.0"\n', encoding="utf-8")
            profile = _make_profile(root=str(root), project_type="library", language="python")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_monorepo_bonus_for_workspace_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pnpm-workspace.yaml").write_text("packages:\n  - packages/*\n", encoding="utf-8")
            profile = _make_profile(root=str(root), project_type="monorepo")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_data_pipeline_bonus_for_dags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dags = root / "dags"
            dags.mkdir()
            (dags / "daily.py").write_text("# dag\n", encoding="utf-8")
            profile = _make_profile(root=str(root), project_type="data-pipeline")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_worker_bonus_for_worker_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "worker.toml").write_text("[worker]\n", encoding="utf-8")
            profile = _make_profile(root=str(root), project_type="worker")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_mobile_app_bonus_for_platform_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "ios").mkdir()
            (root / "android").mkdir()
            profile = _make_profile(root=str(root), project_type="mobile-app")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_meta_bonus_for_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            services = root / "services"
            services.mkdir()
            (services / "registry.yaml").write_text("services:\n  api: {}\n", encoding="utf-8")
            profile = _make_profile(root=str(root), project_type="meta")
            result = assess_project(profile, root=root)
        self.assertIn("type_specific", result.dimensions)
        self.assertGreater(result.dimensions["type_specific"], 0)

    def test_no_bonus_when_signals_absent(self) -> None:
        """Empty directory should get 0 type_specific bonus for any type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for ptype in ("backend-service", "web-app", "cli-tool"):
                profile = _make_profile(root=str(root), project_type=ptype)
                result = assess_project(profile, root=root)
                self.assertEqual(result.dimensions.get("type_specific", 0), 0, f"{ptype} should have 0 bonus on empty dir")

    def test_type_specific_recommendations(self) -> None:
        """When type-specific signals are missing, assessment should recommend adding them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile = _make_profile(root=str(root), project_type="backend-service")
            result = assess_project(profile, root=root)
        # Should have a recommendation about health check or deployment config
        type_recs = [r for r in result.recommendations if "健康检查" in r or "Dockerfile" in r]
        self.assertTrue(type_recs, "backend-service should have type-specific recommendations")


if __name__ == "__main__":
    unittest.main()
