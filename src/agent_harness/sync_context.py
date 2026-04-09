"""Sync cross-service context from a meta repo into individual service repos."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .cli_utils import console


@dataclass(slots=True)
class ServiceContext:
    name: str
    owner: str = ""
    summary: str = ""
    repo: str = ""
    provides: list[str] = field(default_factory=list)
    upstreams: dict[str, list[str]] = field(default_factory=dict)
    downstreams: dict[str, list[str]] = field(default_factory=dict)


def _load_yaml(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SystemExit(f"错误：YAML 解析失败 {path.name}：{e}") from e
    return data if isinstance(data, dict) else {}


def _parse_consumes(consumes: list) -> dict[str, list[str]]:
    """Parse the consumes list from dependency-graph into {target: [endpoints]}."""
    result: dict[str, list[str]] = {}
    for item in consumes:
        if isinstance(item, dict):
            for t, ep in item.items():
                result.setdefault(str(t), []).append(str(ep))
        elif isinstance(item, str) and ":" in item:
            t, ep = item.split(":", 1)
            result.setdefault(t.strip(), []).append(ep.strip())
    return result


def load_meta(meta_root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    registry = _load_yaml(meta_root / "services" / "registry.yaml")
    graph = _load_yaml(meta_root / "services" / "dependency-graph.yaml")
    return registry, graph


def detect_meta_root(hint: Path | None = None) -> Path | None:
    if hint and (hint / "services").is_dir():
        return hint.resolve()
    cwd = Path.cwd().resolve()
    if (cwd / "services" / "registry.yaml").exists():
        return cwd
    return None


def _load_stored_meta(target: Path) -> Path | None:
    pj = target / ".agent-harness" / "project.json"
    if not pj.exists():
        return None
    data = json.loads(pj.read_text(encoding="utf-8"))
    meta_str = data.get("meta_repo")
    if meta_str and Path(meta_str).is_dir():
        return Path(meta_str).resolve()
    return None


def _store_meta_path(target: Path, meta_root: Path) -> None:
    pj = target / ".agent-harness" / "project.json"
    if not pj.exists():
        return
    data = json.loads(pj.read_text(encoding="utf-8"))
    data["meta_repo"] = str(meta_root)
    pj.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def find_service_name(target: Path, registry: dict[str, dict]) -> str | None:
    target = target.resolve()
    pj = target / ".agent-harness" / "project.json"
    candidates: list[str] = []
    if pj.exists():
        data = json.loads(pj.read_text(encoding="utf-8"))
        candidates.extend([str(data.get("project_name", "")), str(data.get("project_slug", ""))])
    candidates.append(target.name)
    reg_lower = {k.lower(): k for k in registry}
    for c in candidates:
        c = c.strip().lower()
        if c and c in reg_lower:
            return reg_lower[c]
    return None


def extract_service_context(
    service_name: str, registry: dict[str, dict], graph: dict[str, dict],
) -> ServiceContext:
    reg = registry.get(service_name, {})
    svc_graph = graph.get(service_name, {})
    provides = [str(p) for p in svc_graph.get("provides", [])]
    downstreams = _parse_consumes(svc_graph.get("consumes", []))
    upstreams: dict[str, list[str]] = {}
    for other, og in graph.items():
        if other == service_name:
            continue
        for t, eps in _parse_consumes(og.get("consumes", [])).items():
            if t == service_name:
                upstreams.setdefault(other, []).extend(eps)
    return ServiceContext(
        name=service_name, owner=str(reg.get("owner", "")),
        summary=str(reg.get("summary", "")), repo=str(reg.get("repo", "")),
        provides=provides, upstreams=upstreams, downstreams=downstreams,
    )


def _fmt_table(header: tuple[str, str], rows: dict[str, list[str]]) -> str:
    lines = [f"| {header[0]} | {header[1]} |", "|--------|-----------|"]
    for svc, eps in sorted(rows.items()):
        lines.append(f"| {svc} | {', '.join(f'`{e}`' for e in eps)} |")
    return "\n".join(lines)


def generate_service_context_md(ctx: ServiceContext) -> str:
    lines = [f"# 服务上下文 — {ctx.name}\n", "> 本文件由 `harness sync` 自动生成，请勿手动编辑。\n"]
    lines.append("## 基本信息\n")
    lines.append(f"- 服务名：{ctx.name}")
    if ctx.owner:
        lines.append(f"- 负责人：{ctx.owner}")
    if ctx.summary:
        lines.append(f"- 职责：{ctx.summary}")
    lines.append("\n## 对外接口\n")
    lines.extend(f"- `{ep}`" for ep in ctx.provides) if ctx.provides else lines.append("（尚未在 dependency-graph 中记录）")
    lines.append("\n## 上游服务（谁调我）\n")
    lines.append(_fmt_table(("调用方", "调用的接口"), ctx.upstreams) if ctx.upstreams else "（暂无已知上游）")
    lines.append("\n## 下游服务（我调谁）\n")
    lines.append(_fmt_table(("被调方", "调用的接口"), ctx.downstreams) if ctx.downstreams else "（暂无已知下游）")
    lines.append("\n## 接口变更影响范围\n")
    if ctx.upstreams:
        lines.append(f"修改对外接口时需协调：**{', '.join(sorted(ctx.upstreams.keys()))}**")
    else:
        lines.append("当前无已知调用方，变更影响范围较小。")
    lines.append("")
    return "\n".join(lines)


def generate_microservice_rule(ctx: ServiceContext) -> str:
    impact = ", ".join(sorted(ctx.upstreams.keys())) if ctx.upstreams else "（暂无已知调用方）"
    return (
        f"# 微服务协作规则\n\n"
        f"本服务（{ctx.name}）是微服务集群的一部分。跨服务上下文见 `docs/service-context.md`。\n\n"
        f"## 何时需要跨服务上下文\n\n"
        f"- 修改 docs/service-context.md 中列出的对外接口时\n"
        f"- 排查涉及上下游服务的问题时\n"
        f"- 需要了解请求的数据流方向时\n\n"
        f"## 接口变更规则\n\n"
        f"- 先查 docs/service-context.md 确认调用方：{impact}\n"
        f"- 接口变更必须向后兼容，或提前协调上游调用方\n"
        f"- 变更后通知 meta repo 更新 dependency-graph，然后重新运行 `harness sync`\n"
    )


def _copy_file(src: Path, dest: Path) -> None:
    """Copy a file, using text mode for text files and binary mode for others."""
    try:
        content = src.read_text(encoding="utf-8")
        dest.write_text(content, encoding="utf-8")
    except (UnicodeDecodeError, ValueError):
        dest.write_bytes(src.read_bytes())


def _distribute_plugins(meta_root: Path, target: Path, *, dry_run: bool = False) -> list[str]:
    plugins_root = meta_root / "shared-plugins"
    if not plugins_root.is_dir():
        return []
    written: list[str] = []
    for src_dir, dest_prefix in [("rules", ".claude/rules"), ("templates", "")]:
        src = plugins_root / src_dir
        if not src.is_dir():
            continue
        for f in sorted(src.rglob("*")):
            if f.is_dir() or f.is_symlink() or f.name.startswith("."):
                continue
            rel = str(f.relative_to(src))
            out_rel = f"{dest_prefix}/{rel}" if dest_prefix else rel
            if not dry_run:
                dest = target / out_rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                _copy_file(f, dest)
            written.append(out_rel)
    return written


def _distribute_domain(meta_root: Path, target: Path, domain: str, *, dry_run: bool = False) -> list[str]:
    """Distribute business domain knowledge files to the service repo."""
    if "/" in domain or "\\" in domain or domain in (".", ".."):
        console.print(f"  [yellow]![/yellow] domain 值不合法：'{domain}'，跳过领域分发")
        return []
    domain_dir = meta_root / "business" / "domains" / domain
    if not domain_dir.is_dir():
        return []
    written: list[str] = []
    for f in sorted(domain_dir.rglob("*")):
        if f.is_dir() or f.is_symlink() or f.name.startswith("."):
            continue
        rel = f"docs/domain/{f.relative_to(domain_dir)}"
        if not dry_run:
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            _copy_file(f, dest)
        written.append(rel)
    return written


def _sync_one(target: Path, meta_root: Path, registry: dict, graph: dict, *, dry_run: bool) -> list[str]:
    service_name = find_service_name(target, registry)
    if not service_name:
        console.print(f"  [yellow]![/yellow] 无法匹配服务名 '{target.name}'，跳过")
        return []
    ctx = extract_service_context(service_name, registry, graph)
    written: list[str] = []
    for rel, content in [
        ("docs/service-context.md", generate_service_context_md(ctx)),
        (".claude/rules/microservice.md", generate_microservice_rule(ctx)),
    ]:
        if not dry_run:
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
        written.append(rel)
    written.extend(_distribute_plugins(meta_root, target, dry_run=dry_run))
    domain = str(registry.get(service_name, {}).get("domain", ""))
    if domain:
        written.extend(_distribute_domain(meta_root, target, domain, dry_run=dry_run))
    if not dry_run:
        _store_meta_path(target, meta_root)
    for rel in written:
        console.print(f"  [green]+[/green] {rel}")
    return written


def resolve_meta(meta_arg: str | None, target: Path | None = None) -> Path:
    if meta_arg:
        p = Path(meta_arg).resolve()
        if (p / "services").is_dir():
            return p
        raise SystemExit(f"错误：{p} 不是有效的 meta repo（缺少 services/ 目录）")
    auto = detect_meta_root()
    if auto:
        return auto
    if target:
        stored = _load_stored_meta(target)
        if stored:
            return stored
    raise SystemExit(
        "错误：未指定 meta repo。请用以下方式之一：\n"
        "  1. 在 meta repo 目录内运行 harness sync --all\n"
        "  2. 用 --meta 指定路径：harness sync <target> --meta /path/to/meta"
    )


def _resolve_repo(repo_path: str, meta_root: Path) -> Path:
    """Resolve a repo path (absolute or relative to meta_root), expanding ~."""
    repo = Path(repo_path).expanduser()
    if not repo.is_absolute():
        repo = (meta_root / repo).resolve()
    return repo


def run_sync(target: Path, meta_root: Path, *, dry_run: bool = False) -> list[str]:
    target, meta_root = target.resolve(), meta_root.resolve()
    registry, graph = load_meta(meta_root)
    if not registry and not graph:
        raise SystemExit(f"错误：meta repo 中未找到有效数据：{meta_root / 'services'}")
    console.print(f"\n[bold]{target.name}[/bold]  {target}")
    return _sync_one(target, meta_root, registry, graph, dry_run=dry_run)


def run_sync_all(meta_root: Path, *, dry_run: bool = False) -> dict[str, list[str]]:
    meta_root = meta_root.resolve()
    registry, graph = load_meta(meta_root)
    if not registry:
        raise SystemExit("错误：services/registry.yaml 为空或不存在")
    results: dict[str, list[str]] = {}
    for svc_name, info in registry.items():
        repo_path = str(info.get("repo", ""))
        if not repo_path:
            console.print(f"  [yellow]![/yellow] {svc_name}: 缺少 repo，跳过")
            continue
        repo = _resolve_repo(repo_path, meta_root)
        if not repo.is_dir():
            console.print(f"  [yellow]![/yellow] {svc_name}: {repo} 不存在，跳过")
            continue
        console.print(f"\n[bold]{svc_name}[/bold]  {repo}")
        results[svc_name] = _sync_one(repo, meta_root, registry, graph, dry_run=dry_run)
    n = sum(len(v) for v in results.values())
    console.print(f"\n[bold green]同步完成[/bold green]  {len(results)} 个服务，{n} 个文件")
    return results
