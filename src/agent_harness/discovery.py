from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from .models import ProjectProfile

PROJECT_TYPES = ("backend-service", "web-app", "cli-tool", "library", "worker")
SENSITIVITY_LEVELS = ("standard", "internal", "high")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_toml(path: Path) -> dict[str, object]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _parse_make_targets(path: Path) -> set[str]:
    if not path.exists():
        return set()

    targets: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("\t") or ":" not in line:
            continue
        target = line.split(":", 1)[0].strip()
        if target and not target.startswith("."):
            targets.add(target)
    return targets


def _detect_source_paths(root: Path) -> list[str]:
    candidates = ["src", "app", "apps", "packages", "services", "api"]
    return [name for name in candidates if (root / name).exists()]


def _detect_test_paths(root: Path) -> list[str]:
    candidates = ["tests", "test", "__tests__"]
    return [name for name in candidates if (root / name).exists()]


def _detect_docs_paths(root: Path) -> list[str]:
    candidates = ["docs", ".agent-harness", ".github"]
    return [name for name in candidates if (root / name).exists()]


def _detect_ci_paths(root: Path) -> list[str]:
    ci_candidates = []
    if (root / ".github" / "workflows").exists():
        ci_candidates.append(".github/workflows")
    if (root / ".gitlab-ci.yml").exists():
        ci_candidates.append(".gitlab-ci.yml")
    return ci_candidates


def _collect_text_for_detection(root: Path) -> str:
    chunks: list[str] = []
    for candidate in ["package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml"]:
        path = root / candidate
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks).lower()


def _detect_external_systems(root: Path) -> list[str]:
    text = _collect_text_for_detection(root)
    mapping = {
        "postgres": ("postgres", "psycopg", "sqlalchemy"),
        "redis": ("redis",),
        "mysql": ("mysql",),
        "stripe": ("stripe",),
        "openai": ("openai",),
        "s3": ("boto3", "s3"),
        "kafka": ("kafka",),
    }
    systems = [label for label, keywords in mapping.items() if any(keyword in text for keyword in keywords)]
    return systems


def _detect_language(root: Path) -> str:
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        return "python"
    if (root / "package.json").exists():
        if (root / "tsconfig.json").exists():
            return "typescript"
        return "javascript"
    if (root / "go.mod").exists():
        return "go"
    if (root / "Cargo.toml").exists():
        return "rust"
    return "unknown"


def _detect_package_manager(root: Path, language: str) -> str:
    if (root / "uv.lock").exists():
        return "uv"
    if (root / "poetry.lock").exists():
        return "poetry"
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "package-lock.json").exists():
        return "npm"
    if language == "python":
        return "pip"
    return "unknown"


def _detect_project_name(root: Path, language: str) -> tuple[str, str]:
    if language == "python" and (root / "pyproject.toml").exists():
        data = _read_toml(root / "pyproject.toml")
        project = data.get("project", {})
        if isinstance(project, dict):
            name = str(project.get("name", root.name))
            summary = str(project.get("description", "待补充项目目标"))
            return name, summary
    if (root / "package.json").exists():
        data = _read_json(root / "package.json")
        name = str(data.get("name", root.name))
        summary = str(data.get("description", "待补充项目目标"))
        return name, summary
    return root.name, "待补充项目目标"


def _detect_project_type(root: Path, language: str) -> str:
    if any((root / name).exists() for name in ("next.config.js", "next.config.mjs", "vite.config.ts", "vite.config.js")):
        return "web-app"
    if (root / "worker.toml").exists() or (root / "wrangler.toml").exists():
        return "worker"
    if (root / "package.json").exists():
        data = _read_json(root / "package.json")
        if data.get("bin"):
            return "cli-tool"
    if language == "python" and (root / "src").exists() and any((root / "src").glob("*/cli.py")):
        return "cli-tool"
    return "backend-service"


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


def _detect_commands(root: Path, language: str, project_slug: str) -> tuple[str, str, str, str]:
    make_targets = _parse_make_targets(root / "Makefile")
    if {"run", "test", "check", "ci"}.issubset(make_targets):
        return ("make run", "make test", "make check", "make ci")

    if (root / "package.json").exists():
        data = _read_json(root / "package.json")
        scripts = data.get("scripts", {})
        if isinstance(scripts, dict):
            run = "npm run dev" if "dev" in scripts else "npm run start" if "start" in scripts else "TODO"
            test = "npm test" if "test" in scripts else "TODO"
            check = "npm run lint" if "lint" in scripts else "npm run check" if "check" in scripts else "TODO"
            ci = "npm run ci" if "ci" in scripts else f"{check} && {test}" if check != "TODO" and test != "TODO" else "TODO"
            return (run, test, check, ci)

    if language == "python":
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

    return ("TODO", "TODO", "TODO", "TODO")


def _detect_deploy_target(root: Path) -> str:
    if (root / "vercel.json").exists():
        return "vercel"
    if (root / "wrangler.toml").exists():
        return "cloudflare"
    if (root / "Dockerfile").exists():
        return "docker"
    if (root / "fly.toml").exists():
        return "fly.io"
    return "未定"


def _detect_has_production(root: Path) -> bool:
    if (root / ".github" / "workflows").exists():
        for path in (root / ".github" / "workflows").glob("*.y*ml"):
            if "deploy" in path.stem.lower() or "release" in path.stem.lower():
                return True
    return False


def _detect_sensitivity(root: Path) -> str:
    text = _collect_text_for_detection(root)
    high_keywords = ("billing", "payment", "auth", "security", "token", "customer data")
    internal_keywords = ("user", "customer", "redis", "postgres")
    if any(keyword in text for keyword in high_keywords):
        return "high"
    if any(keyword in text for keyword in internal_keywords):
        return "internal"
    return "standard"


def discover_project(root: Path) -> ProjectProfile:
    root = root.resolve()
    language = _detect_language(root)
    project_name, summary = _detect_project_name(root, language)
    project_slug = _slugify(project_name)
    project_type = _detect_project_type(root, language)
    run_command, test_command, check_command, ci_command = _detect_commands(root, language, project_slug)
    notes: list[str] = []
    if run_command == "TODO":
        notes.append("没有探测到稳定的运行命令，需要初始化时手动确认。")
    if test_command == "TODO":
        notes.append("没有探测到测试命令，需要初始化时补全。")
    sensitivity = _detect_sensitivity(root)

    return ProjectProfile(
        root=str(root),
        project_name=project_name,
        project_slug=project_slug,
        summary=summary,
        project_type=project_type if project_type in PROJECT_TYPES else "backend-service",
        language=language,
        package_manager=_detect_package_manager(root, language),
        run_command=run_command,
        test_command=test_command,
        check_command=check_command,
        ci_command=ci_command,
        deploy_target=_detect_deploy_target(root),
        has_production=_detect_has_production(root),
        sensitivity=sensitivity if sensitivity in SENSITIVITY_LEVELS else "standard",
        source_paths=_detect_source_paths(root),
        test_paths=_detect_test_paths(root),
        docs_paths=_detect_docs_paths(root),
        ci_paths=_detect_ci_paths(root),
        external_systems=_detect_external_systems(root),
        notes=notes,
    )
