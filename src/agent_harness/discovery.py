from __future__ import annotations

import json
import tomllib
from pathlib import Path

from ._shared import slugify
from .lang_detect import (
    detect_api_docs,
    detect_commands,
    detect_language,
    detect_orm,
    detect_package_manager,
    detect_testing_framework,
)
from .models import ProjectProfile

PROJECT_TYPES = (
    "backend-service", "web-app", "cli-tool", "library", "worker",
    "mobile-app", "monorepo", "data-pipeline", "meta",
)
SENSITIVITY_LEVELS = ("standard", "internal", "high")



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
    candidates = [
        "package.json", "pyproject.toml", "requirements.txt", "go.mod",
        "Cargo.toml", "Gemfile", "composer.json", "pom.xml", "build.gradle",
    ]
    for candidate in candidates:
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
    # Meta repo: service registry or dependency graph without source code
    services_dir = root / "services"
    if services_dir.is_dir() and any(services_dir.glob("*.y*ml")):
        source_dirs = {"src", "app", "apps", "packages", "services"}
        has_code = any((root / d).is_dir() and d != "services" for d in source_dirs)
        if not has_code:
            return "meta"
    if (root / "pnpm-workspace.yaml").exists() or (root / "lerna.json").exists():
        return "monorepo"
    if (root / "package.json").exists():
        data = _read_json(root / "package.json")
        if data.get("workspaces"):
            return "monorepo"
        deps = {**dict(data.get("dependencies", {})), **dict(data.get("devDependencies", {}))}
        if "react-native" in deps:
            return "mobile-app"
    if (root / "pubspec.yaml").exists():
        return "mobile-app"
    if (root / "ios").is_dir() and (root / "android").is_dir():
        return "mobile-app"
    if (root / "dbt_project.yml").exists() or (root / "dagster.yaml").exists():
        return "data-pipeline"
    if (root / "dags").is_dir():
        return "data-pipeline"
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
    language = detect_language(root)
    project_name, summary = _detect_project_name(root, language)
    project_slug = slugify(project_name)
    project_type = _detect_project_type(root, language)
    make_targets = _parse_make_targets(root / "Makefile")
    run_command, test_command, check_command, ci_command = detect_commands(
        root, language, project_slug, make_targets,
    )
    notes: list[str] = []
    if run_command == "TODO":
        notes.append("没有探测到稳定的运行命令，需要初始化时手动确认。")
    if test_command == "TODO":
        notes.append("没有探测到测试命令，需要初始化时补全。")
    sensitivity = _detect_sensitivity(root)
    dep_text = _collect_text_for_detection(root)

    return ProjectProfile(
        root=str(root),
        project_name=project_name,
        project_slug=project_slug,
        summary=summary,
        project_type=project_type if project_type in PROJECT_TYPES else "backend-service",
        language=language,
        package_manager=detect_package_manager(root, language),
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
        testing_framework=detect_testing_framework(root, language),
        orm=detect_orm(dep_text),
        api_docs=detect_api_docs(root),
    )
