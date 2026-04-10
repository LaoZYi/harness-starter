"""Sync cross-service context from a meta repo into individual service repos."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .cli_utils import console
from .models import ServiceContext
from .sync_render import generate_microservice_rule as generate_microservice_rule  # noqa: E501
from .sync_render import generate_service_context_md as generate_service_context_md  # noqa: E501


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


_MAX_COPY_SIZE = 50 * 1024 * 1024  # 50 MB


def _copy_file(src: Path, dest: Path) -> None:
    """Copy a file, using text mode for text files and binary mode for others."""
    size = src.stat().st_size
    if size > _MAX_COPY_SIZE:
        console.print(f"  [yellow]![/yellow] {src.name} 超过 {_MAX_COPY_SIZE // (1024*1024)}MB，跳过")
        return
    try:
        content = src.read_text(encoding="utf-8")
        dest.write_text(content, encoding="utf-8")
    except UnicodeDecodeError:
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


def _is_git_repo(path: Path) -> bool:
    """Return True if path is a git repo (works for normal repos and worktrees)."""
    git_path = path / ".git"
    return git_path.is_dir() or git_path.is_file()


def _sync_one(target: Path, meta_root: Path, registry: dict, graph: dict, *, dry_run: bool) -> list[str]:
    if not _is_git_repo(target):
        console.print(f"  [yellow]![/yellow] {target.name} 不是 git 仓库，跳过")
        return []
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
