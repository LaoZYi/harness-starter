from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

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
    "mobile-app", "monorepo", "data-pipeline", "meta", "document",
)
SENSITIVITY_LEVELS = ("standard", "internal", "high")


def _read_json(path: Path) -> dict[str, Any]:  # Any：JSON 结构由外部决定，运行时校验
    return json.loads(path.read_text(encoding="utf-8"))


def _read_toml(path: Path) -> dict[str, Any]:  # Any：同上
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
    return [n for n in ("src", "app", "apps", "packages", "services", "api") if (root / n).exists()]


def _detect_test_paths(root: Path) -> list[str]:
    return [n for n in ("tests", "test", "__tests__") if (root / n).exists()]


def _detect_docs_paths(root: Path) -> list[str]:
    return [n for n in ("docs", ".agent-harness", ".github") if (root / n).exists()]


def _detect_ci_paths(root: Path) -> list[str]:
    paths: list[str] = []
    if (root / ".github" / "workflows").exists():
        paths.append(".github/workflows")
    if (root / ".gitlab-ci.yml").exists():
        paths.append(".gitlab-ci.yml")
    return paths


def _collect_text_for_detection(root: Path) -> str:
    names = ("package.json", "pyproject.toml", "requirements.txt", "go.mod",
             "Cargo.toml", "Gemfile", "composer.json", "pom.xml", "build.gradle")
    chunks = [(root / n).read_text(encoding="utf-8") for n in names if (root / n).exists()]
    return "\n".join(chunks).lower()


def _detect_external_systems(root: Path) -> list[str]:
    text = _collect_text_for_detection(root)
    mapping = {
        "postgres": ("postgres", "psycopg", "sqlalchemy"), "redis": ("redis",),
        "mysql": ("mysql",), "stripe": ("stripe",), "openai": ("openai",),
        "s3": ("boto3", "s3"), "kafka": ("kafka",),
    }
    return [k for k, ws in mapping.items() if any(w in text for w in ws)]


def _detect_project_name(root: Path, language: str) -> tuple[str, str]:
    if language == "python" and (root / "pyproject.toml").exists():
        proj = _read_toml(root / "pyproject.toml").get("project", {})
        if isinstance(proj, dict):
            return str(proj.get("name", root.name)), str(proj.get("description", "待补充项目目标"))
    if (root / "package.json").exists():
        data = _read_json(root / "package.json")
        return str(data.get("name", root.name)), str(data.get("description", "待补充项目目标"))
    return root.name, "待补充项目目标"


def _read_safe(path: Path) -> str:
    """Read file text, return empty string on OS errors."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _detect_project_type(root: Path, language: str) -> str:  # noqa: C901
    # --- high-priority: meta / monorepo / mobile / data-pipeline / web-app --
    svc_dir = root / "services"
    if svc_dir.is_dir() and any(svc_dir.glob("*.y*ml")):
        if not any((root / d).is_dir() and d != "services" for d in ("src", "app", "apps", "packages")):
            return "meta"
    if (root / "pnpm-workspace.yaml").exists() or (root / "lerna.json").exists():
        return "monorepo"
    pkg: dict[str, Any] = {}
    js_deps: dict[str, Any] = {}
    if (root / "package.json").exists():
        pkg = _read_json(root / "package.json")
        if pkg.get("workspaces"):
            return "monorepo"
        js_deps = {**dict(pkg.get("dependencies", {})), **dict(pkg.get("devDependencies", {}))}
        if "react-native" in js_deps:
            return "mobile-app"
    if (root / "pubspec.yaml").exists():
        return "mobile-app"
    if (root / "ios").is_dir() and (root / "android").is_dir():
        return "mobile-app"
    if "expo" in js_deps or any((root / n).exists() for n in ("capacitor.config.ts", "capacitor.config.json")):
        return "mobile-app"
    if (root / "dbt_project.yml").exists() or (root / "dagster.yaml").exists() or (root / "dags").is_dir() or (root / "prefect.yaml").exists() or (root / "luigi.cfg").exists() or (root / "pipeline.py").exists() or (root / "Kedrofile").exists() or (root / "kedro_cli.py").exists():
        return "data-pipeline"
    if any((root / n).exists() for n in ("next.config.js", "next.config.mjs", "vite.config.ts", "vite.config.js", "webpack.config.js", "angular.json", "nuxt.config.ts", "nuxt.config.js", "svelte.config.js", "astro.config.mjs")):
        return "web-app"
    # --- worker (expanded) --------------------------------------------------
    if (root / "worker.toml").exists() or (root / "wrangler.toml").exists():
        return "worker"
    if language == "python":
        if any((root / f).exists() for f in ("celery.py", "celeryconfig.py")):
            return "worker"
        if (root / "tasks.py").exists() and "celery" in _read_safe(root / "tasks.py").lower():
            return "worker"
        dt = _collect_text_for_detection(root)
        if any(w in dt for w in ("rq==", "huey==", '"rq"', '"huey"', "'rq'", "'huey'")):
            return "worker"
    if any((root / f).exists() for f in ("sidekiq.yml", "sidekiq.yaml")):
        return "worker"
    if (root / "Procfile").exists() and "worker:" in _read_safe(root / "Procfile"):
        return "worker"
    if js_deps and any(d in js_deps for d in ("bull", "bullmq")):
        return "worker"
    # --- cli-tool (expanded) ------------------------------------------------
    if pkg and pkg.get("bin"):
        return "cli-tool"
    if language == "python":
        src = root / "src"
        if src.exists() and (any(src.glob("*/cli.py")) or any(src.glob("*/__main__.py"))):
            return "cli-tool"
        dt = _collect_text_for_detection(root)
        if any(w in dt for w in ("click", "typer", "argparse")):
            return "cli-tool"
    if language == "go":
        if (root / "cmd").is_dir():
            return "cli-tool"
        if (root / "go.mod").exists() and "cobra" in _read_safe(root / "go.mod").lower():
            return "cli-tool"
    if language == "rust" and (root / "Cargo.toml").exists():
        try:
            cargo = _read_toml(root / "Cargo.toml")
            cdeps = {**dict(cargo.get("dependencies", {})), **dict(cargo.get("dev-dependencies", {}))}
            if "clap" in cdeps:
                return "cli-tool"
        except Exception:
            pass
    # --- library (new) ------------------------------------------------------
    if _is_library(root, language, pkg, js_deps):
        return "library"
    # --- backend-service (positive signals then fallback) -------------------
    if (root / "Dockerfile").exists():
        return "backend-service"
    dt = _collect_text_for_detection(root)
    svc_kw = ("flask", "fastapi", "django", "starlette", "express", "fastify",
              "koa", "@nestjs/core", "net/http", "gin-gonic", "echo", "gofiber",
              "fiber", "spring-boot")
    if any(w in dt for w in svc_kw):
        return "backend-service"
    return "backend-service"


def _is_library(root: Path, lang: str, pkg: dict[str, object], js_deps: dict[str, object]) -> bool:
    """Heuristic: project is a distributable library, not an app."""
    has_docker = (root / "Dockerfile").exists()
    svc_py = ("flask", "fastapi", "django", "starlette")
    if lang == "python" and (root / "pyproject.toml").exists():
        tool = _read_toml(root / "pyproject.toml").get("tool", {})
        if (isinstance(tool, dict) and "setuptools" in tool) or (root / "setup.cfg").exists():
            if not has_docker and not any(w in _collect_text_for_detection(root) for w in svc_py):
                return True
    if lang == "python" and (root / "src").is_dir():
        has_pkg = any(d.is_dir() and (d / "__init__.py").exists() for d in (root / "src").iterdir())
        app_globs = ("*/cli.py", "*/app.py", "*/main.py", "*/__main__.py")
        if has_pkg and not any((root / "src").glob(g) for g in app_globs):
            return True
    if pkg:
        has_entry = any(pkg.get(k) for k in ("main", "module", "exports"))
        web_fw = {"express", "fastify", "koa", "@nestjs/core", "next", "nuxt", "react-dom"}
        if has_entry and not pkg.get("bin") and not (web_fw & set(js_deps)):
            return True
    if lang == "rust" and (root / "Cargo.toml").exists():
        ct = _read_safe(root / "Cargo.toml")
        if "[lib]" in ct and "[[bin]]" not in ct:
            return True
    if lang == "go" and (root / "go.mod").exists() and not (root / "main.go").exists():
        return True
    if list(root.glob("*.gemspec")):
        return True
    if not has_docker and any((root / f).exists() for f in ("VERSION", "version.txt")):
        dt = _collect_text_for_detection(root)
        if not any(w in dt for w in ("flask", "fastapi", "django", "express", "fastify")):
            return True
    return False


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
    wf = root / ".github" / "workflows"
    if wf.exists():
        return any("deploy" in p.stem.lower() or "release" in p.stem.lower() for p in wf.glob("*.y*ml"))
    return False


def _detect_sensitivity(root: Path) -> str:
    text = _collect_text_for_detection(root)
    if any(w in text for w in ("billing", "payment", "auth", "security", "token", "customer data")):
        return "high"
    if any(w in text for w in ("user", "customer", "redis", "postgres")):
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
        root=str(root), project_name=project_name, project_slug=project_slug,
        summary=summary,
        project_type=project_type if project_type in PROJECT_TYPES else "backend-service",
        language=language, package_manager=detect_package_manager(root, language),
        run_command=run_command, test_command=test_command,
        check_command=check_command, ci_command=ci_command,
        deploy_target=_detect_deploy_target(root),
        has_production=_detect_has_production(root),
        sensitivity=sensitivity if sensitivity in SENSITIVITY_LEVELS else "standard",
        source_paths=_detect_source_paths(root), test_paths=_detect_test_paths(root),
        docs_paths=_detect_docs_paths(root), ci_paths=_detect_ci_paths(root),
        external_systems=_detect_external_systems(root), notes=notes,
        testing_framework=detect_testing_framework(root, language),
        orm=detect_orm(dep_text), api_docs=detect_api_docs(root),
    )
