from __future__ import annotations

import json
from pathlib import Path

LANG_MARKERS: list[tuple[str, str]] = [
    ("pyproject.toml", "python"),
    ("requirements.txt", "python"),
    ("setup.py", "python"),
    ("go.mod", "go"),
    ("Cargo.toml", "rust"),
    ("pom.xml", "java"),
    ("build.gradle", "java"),
    ("build.gradle.kts", "kotlin"),
    ("Gemfile", "ruby"),
    ("composer.json", "php"),
    ("package.json", "javascript"),
]

PKG_MARKERS: list[tuple[str, str]] = [
    ("uv.lock", "uv"),
    ("poetry.lock", "poetry"),
    ("pnpm-lock.yaml", "pnpm"),
    ("yarn.lock", "yarn"),
    ("package-lock.json", "npm"),
    ("go.sum", "go-modules"),
    ("Cargo.lock", "cargo"),
    ("Gemfile.lock", "bundler"),
    ("composer.lock", "composer"),
]

PKG_FALLBACKS: dict[str, str] = {
    "python": "pip",
    "go": "go-modules",
    "rust": "cargo",
    "java": "maven",
    "kotlin": "gradle",
    "ruby": "bundler",
    "php": "composer",
    "javascript": "npm",
    "typescript": "npm",
}

LANG_COMMANDS: dict[str, dict[str, str]] = {
    "go": {"run": "go run .", "test": "go test ./...", "check": "go vet ./...", "ci": "go vet ./... && go test ./..."},
    "rust": {"run": "cargo run", "test": "cargo test", "check": "cargo clippy", "ci": "cargo clippy && cargo test"},
    "java": {"run": "TODO", "test": "mvn test", "check": "mvn verify", "ci": "mvn verify"},
    "kotlin": {"run": "TODO", "test": "gradle test", "check": "gradle check", "ci": "gradle check"},
    "ruby": {"run": "TODO", "test": "bundle exec rspec", "check": "bundle exec rubocop", "ci": "bundle exec rubocop && bundle exec rspec"},
    "php": {"run": "php artisan serve", "test": "composer test", "check": "composer check", "ci": "composer check && composer test"},
}

TESTING_MARKERS: list[tuple[str, str]] = [
    ("jest.config.js", "jest"),
    ("jest.config.ts", "jest"),
    ("jest.config.mjs", "jest"),
    ("vitest.config.ts", "vitest"),
    ("vitest.config.js", "vitest"),
    ("vitest.config.mts", "vitest"),
    ("pytest.ini", "pytest"),
    ("conftest.py", "pytest"),
    ("setup.cfg", "pytest"),
    (".rspec", "rspec"),
    ("phpunit.xml", "phpunit"),
    ("phpunit.xml.dist", "phpunit"),
]

ORM_KEYWORDS: list[tuple[str, str]] = [
    ("prisma", "prisma"),
    ("sqlalchemy", "sqlalchemy"),
    ("activerecord", "activerecord"),
    ("gorm", "gorm"),
    ("diesel", "diesel"),
    ("sequelize", "sequelize"),
    ("typeorm", "typeorm"),
    ("django.db", "django-orm"),
]


def detect_language(root: Path) -> str:
    for marker, language in LANG_MARKERS:
        if (root / marker).exists():
            if language == "javascript" and (root / "tsconfig.json").exists():
                return "typescript"
            return language
    return "unknown"


def detect_package_manager(root: Path, language: str) -> str:
    for marker, manager in PKG_MARKERS:
        if (root / marker).exists():
            return manager
    return PKG_FALLBACKS.get(language, "unknown")


def detect_commands(
    root: Path,
    language: str,
    project_slug: str,
    make_targets: set[str] | None = None,
) -> tuple[str, str, str, str]:
    if make_targets is None:
        make_targets = set()
    if {"run", "test", "check", "ci"}.issubset(make_targets):
        return ("make run", "make test", "make check", "make ci")

    if (root / "package.json").exists():
        data = json.loads((root / "package.json").read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        if isinstance(scripts, dict):
            run = "npm run dev" if "dev" in scripts else "npm run start" if "start" in scripts else "TODO"
            test = "npm test" if "test" in scripts else "TODO"
            check = "npm run lint" if "lint" in scripts else "npm run check" if "check" in scripts else "TODO"
            ci = "npm run ci" if "ci" in scripts else f"{check} && {test}" if check != "TODO" and test != "TODO" else "TODO"
            return (run, test, check, ci)

    if language == "python":
        return _detect_python_commands(root, project_slug)

    if language == "java" and (root / "build.gradle").exists():
        return ("TODO", "gradle test", "gradle check", "gradle check")

    defaults = LANG_COMMANDS.get(language)
    if defaults:
        return (defaults["run"], defaults["test"], defaults["check"], defaults["ci"])

    return ("TODO", "TODO", "TODO", "TODO")


def _detect_python_commands(root: Path, project_slug: str) -> tuple[str, str, str, str]:
    run = "TODO"
    module_name = _detect_python_module_name(root, project_slug)
    if module_name and (root / "src" / module_name / "cli.py").exists():
        run = f"PYTHONPATH=src python -m {module_name}.cli"
    elif module_name and (root / "src" / module_name / "__main__.py").exists():
        run = f"PYTHONPATH=src python -m {module_name}"
    test = "python -m unittest discover -s tests -v" if (root / "tests").exists() else "TODO"
    check = "python scripts/check_repo.py" if (root / "scripts" / "check_repo.py").exists() else "TODO"
    ci = f"{check} && {test}" if test != "TODO" else check
    return (run, test, check, ci)


def _detect_python_module_name(root: Path, project_slug: str) -> str | None:
    src_root = root / "src"
    if not src_root.exists():
        return None
    preferred = project_slug.replace("-", "_")
    if (src_root / preferred).exists():
        return preferred
    for path in src_root.iterdir():
        if path.is_dir() and (path / "cli.py").exists():
            return path.name
    for path in src_root.iterdir():
        if path.is_dir() and (path / "__main__.py").exists():
            return path.name
    return None


def detect_testing_framework(root: Path, language: str) -> str | None:
    for marker, framework in TESTING_MARKERS:
        if (root / marker).exists():
            return framework
    if language == "go":
        return "go-test"
    return None


def detect_orm(text: str) -> str | None:
    lower = text.lower()
    for keyword, orm in ORM_KEYWORDS:
        if keyword in lower:
            return orm
    return None


def detect_api_docs(root: Path) -> str | None:
    for name in ("openapi.yaml", "openapi.yml", "openapi.json", "swagger.yaml", "swagger.yml", "swagger.json"):
        if (root / name).exists():
            return "openapi"
    return None
