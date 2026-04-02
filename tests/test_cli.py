from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_harness(*args: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    import os

    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "agent_harness", *args],
        capture_output=True,
        text=True,
        env=env,
    )


class InitAssessOnlyTests(unittest.TestCase):
    def test_assess_only_outputs_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_harness("init", tmpdir, "--assess-only")
            self.assertEqual(result.returncode, 0)
            self.assertIn("探测结果", result.stdout)
            self.assertIn("评估结果", result.stdout)

    def test_assess_only_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_harness("init", tmpdir, "--assess-only", "--json")
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            self.assertIn("profile", data)
            self.assertIn("assessment", data)


class InitWithConfigTests(unittest.TestCase):
    def test_init_with_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "configured-project"
            config_path = Path(tmpdir) / "init.json"
            config_path.write_text(
                json.dumps({
                    "project_name": "CLI Test",
                    "project_slug": "cli-test",
                    "summary": "Test from CLI",
                    "project_type": "backend-service",
                    "language": "python",
                    "package_manager": "uv",
                    "run_command": "uv run python -m cli_test",
                    "test_command": "uv run pytest",
                    "check_command": "uv run ruff check .",
                    "ci_command": "make ci",
                    "deploy_target": "docker",
                    "has_production": True,
                    "sensitivity": "internal",
                }),
                encoding="utf-8",
            )

            result = _run_harness("init", str(target), "--config", str(config_path), "--non-interactive")
            self.assertEqual(result.returncode, 0, result.stderr)

            project_json = json.loads((target / ".agent-harness" / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project_json["project_name"], "CLI Test")


class AutoConfigDiscoveryTests(unittest.TestCase):
    def test_auto_discovers_harness_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            (target / ".harness.json").write_text(
                json.dumps({
                    "project_name": "Auto Discovered",
                    "project_slug": "auto-discovered",
                    "summary": "Found via .harness.json",
                    "project_type": "cli-tool",
                    "language": "go",
                    "package_manager": "go",
                    "run_command": "go run .",
                    "test_command": "go test ./...",
                    "check_command": "golangci-lint run",
                    "ci_command": "make ci",
                    "deploy_target": "binary",
                    "has_production": False,
                    "sensitivity": "standard",
                }),
                encoding="utf-8",
            )

            result = _run_harness("init", str(target), "--non-interactive")
            self.assertEqual(result.returncode, 0, result.stderr)

            project_json = json.loads((target / ".agent-harness" / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project_json["project_name"], "Auto Discovered")


class UpgradePlanTests(unittest.TestCase):
    def test_upgrade_plan_after_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            config_path = target / "cfg.json"
            config_path.write_text(
                json.dumps({
                    "project_name": "Upgrade Test",
                    "project_slug": "upgrade-test",
                    "summary": "For upgrade",
                    "project_type": "library",
                    "language": "python",
                    "package_manager": "pip",
                    "run_command": "python -m lib",
                    "test_command": "pytest",
                    "check_command": "ruff check .",
                    "ci_command": "make ci",
                    "deploy_target": "pypi",
                    "has_production": False,
                    "sensitivity": "standard",
                }),
                encoding="utf-8",
            )

            _run_harness("init", str(target), "--config", str(config_path), "--non-interactive")
            result = _run_harness("upgrade", "plan", str(target), "--config", str(config_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("未变", result.stdout)


class UpgradeApplyTests(unittest.TestCase):
    def test_upgrade_apply_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            config_path = target / "cfg.json"
            config_path.write_text(
                json.dumps({
                    "project_name": "Apply Test",
                    "project_slug": "apply-test",
                    "summary": "For apply",
                    "project_type": "web-app",
                    "language": "typescript",
                    "package_manager": "npm",
                    "run_command": "npm start",
                    "test_command": "npm test",
                    "check_command": "npm run lint",
                    "ci_command": "npm run ci",
                    "deploy_target": "vercel",
                    "has_production": True,
                    "sensitivity": "standard",
                }),
                encoding="utf-8",
            )

            _run_harness("init", str(target), "--config", str(config_path), "--non-interactive")
            result = _run_harness("upgrade", "apply", str(target), "--config", str(config_path), "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("预演完成", result.stdout)


class NoSubcommandTests(unittest.TestCase):
    def test_no_subcommand_shows_help(self) -> None:
        result = _run_harness()
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
