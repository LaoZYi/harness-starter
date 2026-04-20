"""_resolve_answers 优先级契约（GitLab Issue #20）。

CLI > .harness.json(config) > .agent-harness/project.json > profile(discover) > None
"""
from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from agent_harness.cli import _resolve_answers
from agent_harness.models import ProjectProfile


def _make_profile(root: str, **overrides: object) -> ProjectProfile:
    defaults: dict[str, object] = {
        "root": root,
        "project_name": "profile-name",
        "project_slug": "profile-name",
        "summary": "profile summary",
        "project_type": "worker",
        "language": "python",
        "package_manager": "pip",
        "run_command": "python -m app",
        "test_command": "pytest",
        "check_command": "ruff check .",
        "ci_command": "make ci",
        "deploy_target": "docker",
        "has_production": False,
        "sensitivity": "standard",
    }
    defaults.update(overrides)
    return ProjectProfile(**defaults)  # type: ignore[arg-type]


def _make_args(**overrides: object) -> argparse.Namespace:
    base: dict[str, object] = {
        "project_name": None, "project_slug": None, "summary": None,
        "project_type": None, "language": None, "package_manager": None,
        "run_command": None, "test_command": None, "check_command": None,
        "ci_command": None, "deploy_target": None, "sensitivity": None,
        "has_production": False, "no_production": False,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def _write_project_json(target: Path, content: dict[str, object]) -> None:
    pj_dir = target / ".agent-harness"
    pj_dir.mkdir(parents=True, exist_ok=True)
    (pj_dir / "project.json").write_text(json.dumps(content), encoding="utf-8")


class ResolveAnswersProjectJsonTests(unittest.TestCase):
    """正常路径：project.json 应作为 upgrade 场景真相源。"""

    def test_reads_project_json_when_no_cli_or_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            _write_project_json(target, {
                "project_name": "测试管控平台",
                "project_type": "backend-service",
                "package_manager": "pnpm",
            })
            profile = _make_profile(str(target))  # profile 给 worker 类默认
            answers = _resolve_answers(_make_args(), profile, {})
            self.assertEqual(answers["project_name"], "测试管控平台")
            self.assertEqual(answers["project_type"], "backend-service")
            self.assertEqual(answers["package_manager"], "pnpm")

    def test_cli_beats_project_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            _write_project_json(target, {"project_name": "from-project-json"})
            profile = _make_profile(str(target))
            answers = _resolve_answers(
                _make_args(project_name="from-cli"), profile, {}
            )
            self.assertEqual(answers["project_name"], "from-cli")

    def test_harness_config_beats_project_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            _write_project_json(target, {"project_name": "from-project-json"})
            profile = _make_profile(str(target))
            answers = _resolve_answers(
                _make_args(), profile, {"project_name": "from-harness-json"}
            )
            self.assertEqual(answers["project_name"], "from-harness-json")


class ResolveAnswersFallthroughTests(unittest.TestCase):
    """边界 & 错误路径。"""

    def test_fallthrough_to_profile_when_project_json_missing(self) -> None:
        # init 场景：project.json 尚未创建。保证不回归。
        with tempfile.TemporaryDirectory() as tmp:
            profile = _make_profile(tmp, project_name="from-profile")
            answers = _resolve_answers(_make_args(), profile, {})
            self.assertEqual(answers["project_name"], "from-profile")

    def test_partial_project_json_falls_through_for_missing_keys(self) -> None:
        # project.json 只填了 project_name，其他字段应 fallthrough 到 profile。
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            _write_project_json(target, {"project_name": "only-this"})
            profile = _make_profile(str(target), project_type="library")
            answers = _resolve_answers(_make_args(), profile, {})
            self.assertEqual(answers["project_name"], "only-this")
            self.assertEqual(answers["project_type"], "library")

    def test_corrupt_project_json_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            pj = target / ".agent-harness"
            pj.mkdir(parents=True, exist_ok=True)
            (pj / "project.json").write_text("{ not valid json", encoding="utf-8")
            profile = _make_profile(str(target), project_name="from-profile")
            answers = _resolve_answers(_make_args(), profile, {})
            # 损坏文件应被忽略并 fallthrough，而非 crash
            self.assertEqual(answers["project_name"], "from-profile")


if __name__ == "__main__":
    unittest.main()
