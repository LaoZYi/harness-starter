from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_harness.lang_detect import (
    detect_commands,
    detect_language,
    detect_orm,
    detect_package_manager,
    detect_testing_framework,
)


class DetectLanguageTests(unittest.TestCase):
    def test_detects_go_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "go.mod").write_text("module example.com/foo\n\ngo 1.21\n", encoding="utf-8")
            self.assertEqual(detect_language(root), "go")
            self.assertEqual(detect_package_manager(root, "go"), "go-modules")

    def test_detects_rust_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "Cargo.toml").write_text('[package]\nname = "foo"\n', encoding="utf-8")
            self.assertEqual(detect_language(root), "rust")
            self.assertEqual(detect_package_manager(root, "rust"), "cargo")

    def test_detects_java_maven_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pom.xml").write_text("<project></project>", encoding="utf-8")
            self.assertEqual(detect_language(root), "java")
            self.assertEqual(detect_package_manager(root, "java"), "maven")

    def test_detects_java_gradle_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "build.gradle").write_text("apply plugin: 'java'", encoding="utf-8")
            self.assertEqual(detect_language(root), "java")

    def test_detects_ruby_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "Gemfile").write_text("source 'https://rubygems.org'\n", encoding="utf-8")
            self.assertEqual(detect_language(root), "ruby")
            self.assertEqual(detect_package_manager(root, "ruby"), "bundler")

    def test_detects_php_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "composer.json").write_text('{"name": "vendor/app"}', encoding="utf-8")
            self.assertEqual(detect_language(root), "php")
            self.assertEqual(detect_package_manager(root, "php"), "composer")

    def test_detects_typescript_with_tsconfig(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "package.json").write_text('{"name": "app"}', encoding="utf-8")
            (root / "tsconfig.json").write_text("{}", encoding="utf-8")
            self.assertEqual(detect_language(root), "typescript")

    def test_empty_directory_returns_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.assertEqual(detect_language(root), "unknown")
            self.assertEqual(detect_package_manager(root, "unknown"), "unknown")


class DetectCommandsTests(unittest.TestCase):
    def test_makefile_overrides_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "go.mod").write_text("module example.com/foo", encoding="utf-8")
            targets = {"run", "test", "check", "ci"}
            run, test, check, ci = detect_commands(root, "go", "foo", targets)
            self.assertEqual(run, "make run")
            self.assertEqual(test, "make test")

    def test_go_commands_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run, test, check, ci = detect_commands(root, "go", "foo", set())
            self.assertEqual(run, "go run .")
            self.assertEqual(test, "go test ./...")
            self.assertEqual(check, "go vet ./...")

    def test_rust_commands_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run, test, check, ci = detect_commands(root, "rust", "foo", set())
            self.assertEqual(run, "cargo run")
            self.assertEqual(test, "cargo test")

    def test_java_gradle_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "build.gradle").write_text("apply plugin: 'java'", encoding="utf-8")
            run, test, check, ci = detect_commands(root, "java", "foo", set())
            self.assertEqual(test, "gradle test")


class DetectTestingFrameworkTests(unittest.TestCase):
    def test_detects_jest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "jest.config.js").write_text("module.exports = {}", encoding="utf-8")
            self.assertEqual(detect_testing_framework(root, "javascript"), "jest")

    def test_detects_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "conftest.py").write_text("", encoding="utf-8")
            self.assertEqual(detect_testing_framework(root, "python"), "pytest")

    def test_go_always_has_go_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.assertEqual(detect_testing_framework(root, "go"), "go-test")


class DetectOrmTests(unittest.TestCase):
    def test_detects_prisma(self) -> None:
        text = '{"dependencies": {"@prisma/client": "^5.0"}}'
        self.assertEqual(detect_orm(text), "prisma")

    def test_detects_sqlalchemy(self) -> None:
        text = 'sqlalchemy>=2.0'
        self.assertEqual(detect_orm(text), "sqlalchemy")

    def test_returns_none_for_no_orm(self) -> None:
        text = '{"dependencies": {"express": "^4.0"}}'
        self.assertIsNone(detect_orm(text))


if __name__ == "__main__":
    unittest.main()
