from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project
from agent_harness.upgrade import execute_upgrade


_BASE_ANSWERS: dict[str, object] = {
    "project_name": "Refs Test",
    "project_slug": "refs-test",
    "summary": "References generation test",
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

EXPECTED_REFS = [
    "accessibility-checklist.md",
    "performance-checklist.md",
    "security-checklist.md",
    "testing-patterns.md",
]


class ReferencesGenerationTests(unittest.TestCase):
    def test_four_checklists_generated_on_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            refs_dir = root / ".agent-harness" / "references"
            self.assertTrue(refs_dir.is_dir(), "references/ directory should be created")
            for name in EXPECTED_REFS:
                path = refs_dir / name
                self.assertTrue(path.exists(), f"{name} should be generated")

    def test_checklists_have_zh_preamble(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            body = (root / ".agent-harness" / "references" / "security-checklist.md").read_text(encoding="utf-8")
            self.assertIn("L2 温知识层", body)
            self.assertIn("/recall --refs", body)
            self.assertIn("/cso", body)

    def test_checklists_preserve_english_terms(self) -> None:
        """Industry-standard terms (LCP/TTFB/WCAG/OWASP) must stay in English."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            refs = root / ".agent-harness" / "references"
            self.assertIn("LCP", (refs / "performance-checklist.md").read_text(encoding="utf-8"))
            self.assertIn("INP", (refs / "performance-checklist.md").read_text(encoding="utf-8"))
            self.assertIn("WCAG", (refs / "accessibility-checklist.md").read_text(encoding="utf-8"))
            self.assertIn("ARIA", (refs / "accessibility-checklist.md").read_text(encoding="utf-8"))
            self.assertIn("OWASP", (refs / "security-checklist.md").read_text(encoding="utf-8"))
            self.assertIn("CORS", (refs / "security-checklist.md").read_text(encoding="utf-8"))

    def test_upgrade_preserves_user_edits_in_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            sec = root / ".agent-harness" / "references" / "security-checklist.md"
            original = sec.read_text(encoding="utf-8")
            sec.write_text(original + "\n## Project-Specific\n\n- MY-SECRET-MARKER\n", encoding="utf-8")

            execute_upgrade(root, {**_BASE_ANSWERS})
            after = sec.read_text(encoding="utf-8")
            self.assertIn("MY-SECRET-MARKER", after)


if __name__ == "__main__":
    unittest.main()
