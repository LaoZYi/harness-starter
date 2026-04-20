"""Answer 解析：融合 CLI 参数、config 文件、project.json 与 discover profile。

从 cli.py 拆出以保持 cli.py <= 280 行（AGENTS.md 硬规则）。

优先级（upgrade 场景的真相源顺序，见 GitLab Issue #20）：
    CLI 参数 > .harness.json (config) > .agent-harness/project.json > profile(discover) > None
"""
from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

from .models import ProjectProfile

PROJECT_FIELDS = (
    "project_name", "project_slug", "summary", "project_type",
    "language", "package_manager", "run_command", "test_command",
    "check_command", "ci_command", "deploy_target", "sensitivity",
)


def load_explicit_config(path: Path) -> dict[str, object]:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise SystemExit("配置文件仅支持 .json 或 .toml")


def auto_discover_config(target: Path) -> dict[str, object]:
    p = target / ".harness.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def merged_config(target: Path, args: argparse.Namespace) -> dict[str, object]:
    explicit = load_explicit_config(Path(args.config).resolve()) if args.config else {}
    return {**auto_discover_config(target), **explicit}


def load_project_json(target: Path) -> dict[str, object]:
    """读 .agent-harness/project.json 并归一化为 PROJECT_FIELDS 扁平 schema。

    project.json 存储的是 rendered schema（`project_summary`、`commands.run/check/test/ci`
    等），与 answers / PROJECT_FIELDS 的扁平命名不同。此函数负责把两种命名对齐，
    保证 `resolve_answers` 对 project.json 的优先级查询真的生效。

    文件缺失或 JSON 解析失败 → 返回 `{}`，让 `resolve_answers` fallthrough 到 profile。
    """
    p = target / ".agent-harness" / "project.json"
    if not p.is_file():
        return {}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, object] = {}
    for key in ("project_name", "project_slug", "project_type", "language",
                "package_manager", "deploy_target", "sensitivity", "has_production"):
        if key in raw:
            normalized[key] = raw[key]
    if "project_summary" in raw:
        normalized["summary"] = raw["project_summary"]
    commands = raw.get("commands")
    if isinstance(commands, dict):
        for pj_key, answer_key in (("run", "run_command"), ("check", "check_command"),
                                    ("test", "test_command"), ("ci", "ci_command")):
            if pj_key in commands:
                normalized[answer_key] = commands[pj_key]
    return normalized


def resolve_answers(
    args: argparse.Namespace, profile: ProjectProfile, config: dict[str, object],
) -> dict[str, object]:
    # 见 GitLab Issue #20：upgrade 跳过 project.json 会把用户真实配置覆盖为模板默认值。
    project_json = load_project_json(Path(profile.root)) if profile.root else {}
    answers: dict[str, object] = {}
    for key in PROJECT_FIELDS:
        cli_value = getattr(args, key.replace("-", "_"), None)
        if cli_value is not None:
            answers[key] = cli_value
        elif key in config:
            answers[key] = config[key]
        elif key in project_json:
            answers[key] = project_json[key]
        else:
            answers[key] = getattr(profile, key, None)
    if args.has_production:
        answers["has_production"] = True
    elif args.no_production:
        answers["has_production"] = False
    elif "has_production" in config:
        answers["has_production"] = bool(config["has_production"])
    elif "has_production" in project_json:
        answers["has_production"] = bool(project_json["has_production"])
    else:
        answers["has_production"] = profile.has_production
    return answers
