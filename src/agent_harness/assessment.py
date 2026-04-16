from __future__ import annotations

from pathlib import Path

from .models import AssessmentResult, ProjectProfile


def _score_detection(profile: ProjectProfile) -> tuple[int, list[str], list[str], list[str]]:
    score = 100
    strengths: list[str] = []
    gaps: list[str] = []
    recommendations: list[str] = []

    if profile.language != "unknown":
        strengths.append(f"已识别主要语言：{profile.language}")
    else:
        score -= 20
        gaps.append("未识别主要语言")
        recommendations.append("补充语言和构建工具信息，再执行初始化。")

    if profile.source_paths:
        strengths.append(f"已识别源码目录：{', '.join(profile.source_paths)}")
    else:
        score -= 15
        gaps.append("未识别源码目录")
        recommendations.append("在初始化前确认源码目录，避免文档和 runbook 写错。")

    if profile.test_paths:
        strengths.append(f"已识别测试目录：{', '.join(profile.test_paths)}")
    else:
        score -= 15
        gaps.append("未识别测试目录")
        recommendations.append("尽快明确测试入口，避免 harness 只剩文档没有验证链。")

    if profile.ci_paths:
        strengths.append(f"已识别 CI 入口：{', '.join(profile.ci_paths)}")
    else:
        score -= 10
        gaps.append("未识别 CI 配置")
        recommendations.append("接入 harness 后尽快把 check/test 命令纳入 CI。")

    for label, command in [
        ("运行命令", profile.run_command),
        ("测试命令", profile.test_command),
        ("检查命令", profile.check_command),
        ("CI 命令", profile.ci_command),
    ]:
        if command != "TODO":
            strengths.append(f"{label}已识别：{command}")
        else:
            score -= 10
            gaps.append(f"{label}未识别")
            recommendations.append(f"初始化时手动确认{label}，避免生成的 runbook 不可执行。")

    if profile.has_production:
        strengths.append("已探测到生产相关信号")
    else:
        recommendations.append("如果项目已有线上环境，请在初始化时显式标记 has_production。")

    if profile.external_systems:
        strengths.append(f"检测到外部系统：{', '.join(profile.external_systems)}")
    else:
        recommendations.append("如果项目依赖数据库、队列或第三方 API，请在初始化后补到 docs/architecture.md。")

    return score, strengths, gaps, recommendations


def _score_code_quality(root: Path) -> tuple[int, list[str], list[str]]:
    bonus = 0
    strengths: list[str] = []
    recommendations: list[str] = []
    linter_markers = [
        ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml",
        "ruff.toml", ".pylintrc", ".rubocop.yml", ".golangci.yml",
        "eslint.config.js", "eslint.config.mjs",
    ]
    formatter_markers = [".prettierrc", ".prettierrc.json", ".prettierrc.js", "rustfmt.toml", ".editorconfig"]

    has_linter = any((root / m).exists() for m in linter_markers)
    if not has_linter and (root / "pyproject.toml").exists():
        text = (root / "pyproject.toml").read_text(encoding="utf-8")
        has_linter = "[tool.ruff]" in text or "[tool.pylint]" in text

    has_formatter = any((root / m).exists() for m in formatter_markers)

    if has_linter:
        bonus += 5
        strengths.append("已配置代码检查工具")
    else:
        recommendations.append("建议配置 linter（如 ruff、eslint、golangci-lint）以提高代码一致性。")
    if has_formatter:
        bonus += 5
        strengths.append("已配置代码格式化工具")

    return bonus, strengths, recommendations


def _score_testing(root: Path) -> tuple[int, list[str], list[str]]:
    testing_markers = [
        "jest.config.js", "jest.config.ts", "jest.config.mjs",
        "vitest.config.ts", "vitest.config.js",
        "pytest.ini", "conftest.py", ".rspec", "phpunit.xml",
    ]
    has_config = any((root / m).exists() for m in testing_markers)
    if not has_config and (root / "pyproject.toml").exists():
        text = (root / "pyproject.toml").read_text(encoding="utf-8")
        has_config = "[tool.pytest" in text

    if has_config:
        return 5, ["已配置测试框架"], []
    return 0, [], ["建议添加测试框架配置文件，让 CI 和 agent 能自动发现测试入口。"]


def _score_documentation(root: Path) -> tuple[int, list[str], list[str]]:
    readme = root / "README.md"
    if readme.exists():
        lines = [l for l in readme.read_text(encoding="utf-8").splitlines() if l.strip()]
        if len(lines) >= 10:
            return 5, ["README.md 内容充实"], []
        return 2, ["README.md 存在但内容较少"], ["建议补充 README.md 的项目说明、使用方式和开发指引。"]
    return 0, [], ["建议创建 README.md，让新成员和 agent 能快速了解项目。"]


def _compute_confidence(profile: ProjectProfile) -> str:
    unknowns = 0
    if profile.language == "unknown":
        unknowns += 1
    if profile.package_manager == "unknown":
        unknowns += 1
    for cmd in [profile.run_command, profile.test_command, profile.check_command, profile.ci_command]:
        if cmd == "TODO":
            unknowns += 1
    if profile.deploy_target == "未定":
        unknowns += 1
    if unknowns <= 1:
        return "high"
    if unknowns <= 3:
        return "medium"
    return "low"


def _score_type_specific(root: Path, project_type: str) -> tuple[int, list[str], list[str]]:
    """Score type-specific project structure signals. Returns (bonus, strengths, recommendations)."""
    checkers: dict[str, tuple[list[tuple[str, ...]], list[str]]] = {
        "backend-service": (
            [("Dockerfile",), ("docker-compose.yml", "docker-compose.yaml"),
             ("openapi.yaml", "openapi.yml", "swagger.json", "swagger.yaml", "docs/api/")],
            ["建议添加 Dockerfile 或 docker-compose 以明确部署方式。",
             "建议添加健康检查端点（/health），便于编排系统监控。",
             "建议添加 API 文档（openapi.yaml/swagger.json），便于前后端协作。"],
        ),
        "web-app": (
            [("vite.config.ts", "vite.config.js", "next.config.js", "next.config.mjs", "webpack.config.js"),
             ("public/",), ("public/assets/", "static/", "images/", "assets/")],
            ["建议添加前端构建配置（vite/next/webpack），明确构建流程。",
             "建议创建 public/ 目录存放静态资源。",
             "建议创建静态资源目录（static/assets/），规范化资源管理。"],
        ),
        "cli-tool": (
            [("**/cli.py", "**/cli.ts", "**/main.go", "**/cmd/"), ("README.md",),
             ("completions/", "man/", "**/completion.py", "**/completion.ts")],
            ["建议创建明确的 CLI 入口文件（cli.py/main.go/cmd/），便于定位命令逻辑。",
             "建议在 README.md 中添加用法示例，方便使用者快速上手。",
             "建议添加 shell 补全脚本或 man page（completions/man/），提升体验。"],
        ),
        "library": (
            [("VERSION", "pyproject.toml", "package.json", "Cargo.toml"),
             ("CHANGELOG.md", "CHANGELOG", "HISTORY.md", "HISTORY.rst"), ("examples/", "tests/", "test/")],
            ["建议在项目元数据中声明版本号，便于 SemVer 管理。",
             "建议添加 CHANGELOG 文件，记录版本变更历史。",
             "建议创建 examples/ 或 tests/ 目录，展示用法并保障质量。"],
        ),
        "worker": (
            [("worker.toml", "wrangler.toml", "celery.py", "celeryconfig.py", "**/tasks.py"),
             ("**/celery.py", "**/celeryconfig.py", "**/tasks/"),
             ("redis.conf", "rabbitmq.conf", "**/queue_config.py", "**/sqs.py")],
            ["建议添加 worker 配置文件（worker.toml/celery），明确队列和并发设置。",
             "建议将异步任务集中到 tasks/ 目录，便于发现和管理。",
             "建议添加队列配置（Redis/RabbitMQ/SQS），明确消息队列连接。"],
        ),
        "mobile-app": (
            [("ios/",), ("android/",), ("pubspec.yaml",)],
            ["建议确认 ios/android 目录或 Flutter 配置（pubspec.yaml）完整。"],
        ),
        "monorepo": (
            [("pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json"),
             ("**/package.json", "**/Cargo.toml", "**/pyproject.toml"),
             (".eslintrc", ".eslintrc.js", "tsconfig.json", "rustfmt.toml", "biome.json")],
            ["建议添加工作区配置（pnpm-workspace/lerna/nx/turbo），明确包依赖关系。",
             "建议确认子目录中包含独立的包配置文件（package.json/Cargo.toml）。",
             "建议在根目录配置共享工具（eslint/tsconfig/rustfmt），统一代码规范。"],
        ),
        "data-pipeline": (
            [("dags/", "pipelines/", "dbt_project.yml", "dagster.yaml"),
             ("**/*.sql", "models/", "**/models/*.yml"),
             ("profiles.yml", "connections.yaml", "**/airflow.cfg")],
            ["建议创建 DAG/pipeline 目录，明确数据流程结构。",
             "建议添加 schema 定义（SQL/dbt models），明确数据模型。",
             "建议添加连接配置（profiles.yml/connections），明确数据源。"],
        ),
        "meta": (
            [("services/registry.yaml", "services/registry.yml"),
             ("services/dependency-graph.yaml", "services/dependency-graph.yml"), ("business/", "shared-plugins/")],
            ["建议创建 services/registry.yaml，注册所有服务信息。",
             "建议创建 services/dependency-graph.yaml，描述服务间依赖。", "建议创建 business/ 或 shared-plugins/ 目录，集中组织元知识。"],
        ),
    }
    signal_groups, recs = checkers.get(project_type, ([], []))
    bonus = 0
    strengths: list[str] = []
    recommendations: list[str] = []
    for i, candidates in enumerate(signal_groups):
        found = _check_signal(root, candidates)
        if found:
            bonus += 3
            strengths.append(f"已检测到{project_type}特征文件：{found}")
        elif i < len(recs):
            recommendations.append(recs[i])
    return bonus, strengths, recommendations


def _check_signal(root: Path, candidates: tuple[str, ...]) -> str:
    """Check if any of the candidate files/dirs exist. Returns the found name or empty string."""
    for c in candidates:
        if "**/" in c:
            if any(root.rglob(c.replace("**/", ""))):
                return c.split("/")[-1]
        elif c.endswith("/"):
            if (root / c.rstrip("/")).is_dir():
                return c.rstrip("/")
        else:
            if (root / c).exists():
                return c
    # For library, check if pyproject.toml has version field
    return ""


def assess_project(profile: ProjectProfile, root: Path | None = None) -> AssessmentResult:
    base_score, strengths, gaps, recommendations = _score_detection(profile)
    dimensions: dict[str, int] = {"detection": max(base_score, 0)}
    bonus = 0

    if root is not None:
        qb, qs, qr = _score_code_quality(root)
        bonus += qb
        strengths.extend(qs)
        recommendations.extend(qr)
        dimensions["code_quality"] = qb

        tb, ts, tr = _score_testing(root)
        bonus += tb
        strengths.extend(ts)
        recommendations.extend(tr)
        dimensions["testing"] = tb

        db, ds, dr = _score_documentation(root)
        bonus += db
        strengths.extend(ds)
        recommendations.extend(dr)
        dimensions["documentation"] = db

        tsb, tss, tsr = _score_type_specific(root, profile.project_type)
        bonus += tsb
        strengths.extend(tss)
        recommendations.extend(tsr)
        dimensions["type_specific"] = tsb

    final_score = min(max(base_score + bonus, 0), 100)
    confidence = _compute_confidence(profile)
    readiness = "high" if final_score >= 80 else "medium" if final_score >= 55 else "low"

    return AssessmentResult(
        score=final_score,
        readiness=readiness,
        strengths=strengths,
        gaps=gaps,
        recommendations=recommendations,
        confidence=confidence,
        dimensions=dimensions,
    )
