"""Contract tests for scripts/check_repo.py guards.

Locks down two behaviors:
1. check_module_sizes auto-discovers all .py files under src/agent_harness/
   (including sub-packages like squad/) — no hardcoded whitelist.
2. A new oversized module, anywhere under the package, fails the check.

Historical context: squad/cli.py once reached 303 lines because the old
whitelist-based check_module_sizes didn't enumerate the squad/ package.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "agent_harness"
CHECK_SCRIPT = ROOT / "scripts" / "check_repo.py"


def _load_check_module():
    spec = importlib.util.spec_from_file_location("check_repo_under_test", CHECK_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckModuleSizesAutoDiscoveryTests(unittest.TestCase):
    """check_module_sizes must auto-scan src/agent_harness/, not rely on a list."""

    def test_all_package_py_files_are_checked_not_whitelist(self) -> None:
        """Every .py in src/agent_harness/ (except __init__.py and templates/)
        must be within the 280-line budget — proven by running check_repo.py
        cleanly on the real tree."""
        oversized = []
        for path in sorted(PKG.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            try:
                path.relative_to(PKG / "templates")
                continue
            except ValueError:
                pass
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > 280:
                oversized.append(f"{path.relative_to(ROOT)}: {line_count}")
        self.assertEqual(
            oversized, [],
            f"Modules exceeding 280-line hard limit: {oversized}. "
            "Split the file(s) per AGENTS.md architectural constraint."
        )

    def test_squad_subpackage_is_covered(self) -> None:
        """squad/*.py must be seen by check_module_sizes (regression guard)."""
        check = _load_check_module()
        # Force an oversized squad file in a sandbox copy and confirm the check fails.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            # Mirror just what check_module_sizes needs.
            pkg_dir = tmp_root / "src" / "agent_harness" / "squad"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "offender.py").write_text("x = 0\n" * 281, encoding="utf-8")
            # Patch module globals to point at the sandbox.
            original_root = check.ROOT
            original_pkg = check.PKG
            check.ROOT = tmp_root
            check.PKG = tmp_root / "src" / "agent_harness"
            try:
                with self.assertRaises(SystemExit) as ctx:
                    check.check_module_sizes()
                self.assertIn("squad/offender.py", str(ctx.exception))
                self.assertIn("过长", str(ctx.exception))
            finally:
                check.ROOT = original_root
                check.PKG = original_pkg

    def test_init_py_and_templates_are_skipped(self) -> None:
        """__init__.py and templates/ must not be evaluated against the 280-line limit."""
        check = _load_check_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            pkg = tmp_root / "src" / "agent_harness"
            pkg.mkdir(parents=True)
            # Oversized __init__.py should pass (exclusion).
            (pkg / "__init__.py").write_text("x = 0\n" * 500, encoding="utf-8")
            # Oversized template-embedded .py should pass (exclusion).
            tmpl = pkg / "templates" / "common"
            tmpl.mkdir(parents=True)
            (tmpl / "sample.py").write_text("x = 0\n" * 500, encoding="utf-8")
            original_root, original_pkg = check.ROOT, check.PKG
            check.ROOT = tmp_root
            check.PKG = pkg
            try:
                check.check_module_sizes()  # should not raise
            finally:
                check.ROOT = original_root
                check.PKG = original_pkg


class CheckRepoEndToEndTests(unittest.TestCase):
    """Running scripts/check_repo.py on the live tree must succeed."""

    def test_check_repo_passes_on_clean_tree(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECK_SCRIPT)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(
            result.returncode, 0,
            f"check_repo.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )


if __name__ == "__main__":
    unittest.main()
