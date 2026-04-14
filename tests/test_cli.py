from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_TEST_CONFIG = {
    "project_name": "Test Project",
    "project_slug": "test-project",
    "summary": "For testing",
    "project_type": "backend-service",
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


def _run_harness(*args: str) -> subprocess.CompletedProcess[str]:
    import os
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "agent_harness", *args],
        capture_output=True, text=True, env=env,
    )


def _init_test_project(target: Path, **overrides: object) -> subprocess.CompletedProcess[str]:
    config = {**_TEST_CONFIG, **overrides}
    target.mkdir(parents=True, exist_ok=True)
    cfg_path = target / "_test_config.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    return _run_harness("init", str(target), "--config", str(cfg_path), "--non-interactive", "--no-git-commit")


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
            result = _init_test_project(target, project_name="CLI Test")
            self.assertEqual(result.returncode, 0, result.stderr)
            pj = json.loads((target / ".agent-harness" / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(pj["project_name"], "CLI Test")


class AutoConfigDiscoveryTests(unittest.TestCase):
    def test_auto_discovers_harness_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            (target / ".harness.json").write_text(json.dumps({**_TEST_CONFIG, "project_name": "Auto Found"}), encoding="utf-8")
            result = _run_harness("init", str(target), "--non-interactive", "--no-git-commit")
            self.assertEqual(result.returncode, 0, result.stderr)
            pj = json.loads((target / ".agent-harness" / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(pj["project_name"], "Auto Found")


class UpgradePlanTests(unittest.TestCase):
    def test_upgrade_plan_after_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            cfg_path = target / "_test_config.json"
            cfg_path.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")
            _run_harness("init", str(target), "--config", str(cfg_path), "--non-interactive", "--no-git-commit")
            result = _run_harness("upgrade", "plan", str(target), "--config", str(cfg_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("未变", result.stdout)


class UpgradeApplyTests(unittest.TestCase):
    def test_upgrade_apply_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            cfg_path = target / "_test_config.json"
            cfg_path.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")
            _run_harness("init", str(target), "--config", str(cfg_path), "--non-interactive", "--no-git-commit")
            result = _run_harness("upgrade", "apply", str(target), "--config", str(cfg_path), "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("预演完成", result.stdout)


class DoctorTests(unittest.TestCase):
    def test_doctor_on_initialized_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _init_test_project(target)
            result = _run_harness("doctor", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("健康检查", result.stdout)
            self.assertIn("AGENTS.md", result.stdout)

    def test_doctor_on_uninitialized_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_harness("doctor", tmpdir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("尚未初始化", result.stderr)


class ExportTests(unittest.TestCase):
    def test_export_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _init_test_project(target)
            result = _run_harness("export", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("项目画像", result.stdout)
            self.assertIn("Test Project", result.stdout)

    def test_export_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _init_test_project(target)
            result = _run_harness("export", str(target), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("project", data)

    def test_export_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _init_test_project(target)
            out_file = Path(tmpdir) / "snapshot.md"
            result = _run_harness("export", str(target), "-o", str(out_file))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out_file.exists())
            self.assertIn("项目画像", out_file.read_text(encoding="utf-8"))

    def test_export_on_uninitialized_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_harness("export", tmpdir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("尚未初始化", result.stderr)


class StatsTests(unittest.TestCase):
    def test_stats_empty_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _init_test_project(target)
            result = _run_harness("stats", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("没有记录", result.stdout)

    def test_stats_with_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            _init_test_project(target)
            tl = target / ".agent-harness" / "task-log.md"
            tl.write_text("# Task Log\n\n## 2025-04-01 添加登录\n- 需求：登录功能\n\n## 2025-04-02 返工：登录修复\n- 用户反馈：有 bug\n", encoding="utf-8")
            result = _run_harness("stats", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("任务统计", result.stdout)

    def test_stats_on_uninitialized_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_harness("stats", tmpdir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("尚未初始化", result.stderr)


class PluginTests(unittest.TestCase):
    def test_plugin_rules_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            rules_dir = target / ".harness-plugins" / "rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "custom.md").write_text("# Custom\n项目：{{project_name}}", encoding="utf-8")
            _init_test_project(target)
            custom = target / ".claude" / "rules" / "custom.md"
            self.assertTrue(custom.exists())
            self.assertIn("Test Project", custom.read_text(encoding="utf-8"))

    def test_plugin_templates_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            tmpl_dir = target / ".harness-plugins" / "templates" / "docs"
            tmpl_dir.mkdir(parents=True)
            (tmpl_dir / "custom-guide.md").write_text("# Guide for {{project_name}}", encoding="utf-8")
            _init_test_project(target)
            guide = target / "docs" / "custom-guide.md"
            self.assertTrue(guide.exists())
            self.assertIn("Test Project", guide.read_text(encoding="utf-8"))

    def test_plugin_tmpl_suffix_stripped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            # rules with .md.tmpl suffix
            rules_dir = target / ".harness-plugins" / "rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "team-rule.md.tmpl").write_text("# {{project_name}} 团队规则", encoding="utf-8")
            # templates with .tmpl suffix
            tmpl_dir = target / ".harness-plugins" / "templates" / "docs"
            tmpl_dir.mkdir(parents=True)
            (tmpl_dir / "onboarding.md.tmpl").write_text("# {{project_name}} 入职指南", encoding="utf-8")
            _init_test_project(target)
            # .tmpl suffix should be stripped
            rule = target / ".claude" / "rules" / "team-rule.md"
            self.assertTrue(rule.exists(), ".tmpl suffix should be stripped from rule filename")
            self.assertIn("Test Project", rule.read_text(encoding="utf-8"))
            self.assertFalse((target / ".claude" / "rules" / "team-rule.md.tmpl").exists())
            doc = target / "docs" / "onboarding.md"
            self.assertTrue(doc.exists(), ".tmpl suffix should be stripped from template filename")
            self.assertIn("Test Project", doc.read_text(encoding="utf-8"))
            self.assertFalse((target / "docs" / "onboarding.md.tmpl").exists())


class GitCommitTests(unittest.TestCase):
    def test_no_git_commit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            subprocess.run(["git", "init", str(target)], capture_output=True)
            _init_test_project(target)
            log = subprocess.run(["git", "-C", str(target), "log", "--oneline"], capture_output=True, text=True)
            self.assertNotIn("initialize agent harness", log.stdout)

    def test_git_commit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            subprocess.run(["git", "init", str(target)], capture_output=True)
            subprocess.run(["git", "-C", str(target), "config", "user.email", "test@test.com"], capture_output=True)
            subprocess.run(["git", "-C", str(target), "config", "user.name", "Test"], capture_output=True)
            cfg_path = target / "_test_config.json"
            cfg_path.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")
            result = _run_harness("init", str(target), "--config", str(cfg_path), "--non-interactive", "--git-commit")
            self.assertEqual(result.returncode, 0, result.stderr)
            log = subprocess.run(["git", "-C", str(target), "log", "--oneline"], capture_output=True, text=True)
            self.assertIn("initialize agent harness", log.stdout)

    def test_git_commit_missing_identity_is_graceful(self) -> None:
        """缺 git user.email/user.name 时应友好提示+跳过 commit，不抛 CalledProcessError。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            subprocess.run(["git", "init", str(target)], capture_output=True)
            # 显式不设 user.email/name，并通过环境变量隔绝全局 config
            cfg_path = target / "_test_config.json"
            cfg_path.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")
            env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
            result = subprocess.run(
                [sys.executable, "-m", "agent_harness", "init", str(target),
                 "--config", str(cfg_path), "--non-interactive", "--git-commit"],
                capture_output=True, text=True, env=env,
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
            # 未创建 commit（log 为空或 git log 返回非 0）
            log = subprocess.run(
                ["git", "-C", str(target), "log", "--oneline"],
                capture_output=True, text=True, env=env,
            )
            self.assertNotIn("initialize agent harness", log.stdout)
            # 输出中含友好提示
            self.assertIn("未配置 git user.email", result.stdout + result.stderr)


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_copies_files_then_inits(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scaffold = Path(tmpdir) / "framework"
            scaffold.mkdir()
            (scaffold / "src").mkdir()
            (scaffold / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
            (scaffold / "package.json").write_text('{"name": "fw"}', encoding="utf-8")

            target = Path(tmpdir) / "new-project"
            cfg = Path(tmpdir) / "cfg.json"
            cfg.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")
            result = _run_harness("init", str(target), "--scaffold", str(scaffold), "--config", str(cfg), "--non-interactive", "--no-git-commit")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / "src" / "main.py").exists())
            self.assertTrue((target / "AGENTS.md").exists())
            self.assertIn("hello", (target / "src" / "main.py").read_text(encoding="utf-8"))

    def test_scaffold_skips_git_and_node_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scaffold = Path(tmpdir) / "framework"
            scaffold.mkdir()
            (scaffold / ".git").mkdir()
            (scaffold / ".git" / "config").write_text("git stuff", encoding="utf-8")
            (scaffold / "node_modules").mkdir()
            (scaffold / "node_modules" / "pkg.js").write_text("module", encoding="utf-8")
            (scaffold / "index.js").write_text("// app", encoding="utf-8")

            target = Path(tmpdir) / "new-project"
            cfg = Path(tmpdir) / "cfg.json"
            cfg.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")
            _run_harness("init", str(target), "--scaffold", str(scaffold), "--config", str(cfg), "--non-interactive", "--no-git-commit")
            self.assertTrue((target / "index.js").exists())
            self.assertFalse((target / ".git" / "config").exists())
            self.assertFalse((target / "node_modules").exists())


class NoSubcommandTests(unittest.TestCase):
    def test_no_subcommand_shows_help(self) -> None:
        result = _run_harness()
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
