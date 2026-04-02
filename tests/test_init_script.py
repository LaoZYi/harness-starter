from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class InitScriptTests(unittest.TestCase):
    def test_script_supports_config_file(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "scripts" / "init_project.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "configured-project"
            config_path = Path(tmpdir) / "init.json"
            config_path.write_text(
                json.dumps(
                    {
                        "project_name": "Configured API",
                        "project_slug": "configured-api",
                        "summary": "Configured from file",
                        "project_type": "backend-service",
                        "language": "python",
                        "package_manager": "uv",
                        "run_command": "uv run python -m configured_api",
                        "test_command": "uv run pytest",
                        "check_command": "uv run ruff check .",
                        "ci_command": "make ci",
                        "deploy_target": "docker",
                        "has_production": True,
                        "sensitivity": "internal",
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), "--target", str(target), "--config", str(config_path), "--non-interactive"],
                check=True,
                capture_output=True,
                text=True,
            )

            project_json = json.loads((target / ".agent-harness" / "project.json").read_text(encoding="utf-8"))

        self.assertIn(".agent-harness/init-summary.md", result.stdout)
        self.assertEqual(project_json["project_name"], "Configured API")
        self.assertIn("harness_version", project_json)
        self.assertEqual(project_json["commands"]["run"], "uv run python -m configured_api")


if __name__ == "__main__":
    unittest.main()
