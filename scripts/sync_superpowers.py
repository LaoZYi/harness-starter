"""Sync skills from upstream repositories (obra/superpowers + EveryInc/compound-engineering-plugin).

Fetches latest SKILL.md files via GitHub API, caches them locally,
and reports changes against the previous cached version.

Note: absorbed projects (addyosmani/agent-skills, joelparkerhenderson/architecture-decision-record)
are NOT tracked here — their upstream changes are monitored by /evolve step 1.5 instead,
which reads from closed GitHub Issues with the 'evolution' label.
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from datetime import UTC, datetime
from difflib import unified_diff
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".superpowers-upstream" / "skills"
VERSION_FILE = ROOT / ".superpowers-upstream" / "version.json"
TEMPLATE_DIR = ROOT / "src" / "agent_harness" / "templates" / "superpowers" / ".claude" / "commands"

SUPERPOWERS_REPO = "obra/superpowers"
COMPOUND_REPO = "EveryInc/compound-engineering-plugin"

# upstream skill directory name -> local template filename
SKILL_MAP: dict[str, str] = {
    "brainstorming": "brainstorm.md.tmpl",
    "writing-plans": "write-plan.md.tmpl",
    "test-driven-development": "tdd.md.tmpl",
    "systematic-debugging": "debug.md.tmpl",
    "executing-plans": "execute-plan.md.tmpl",
    "subagent-driven-development": "subagent-dev.md.tmpl",
    "dispatching-parallel-agents": "dispatch-agents.md.tmpl",
    "requesting-code-review": "request-review.md.tmpl",
    "receiving-code-review": "receive-review.md.tmpl",
    "using-git-worktrees": "use-worktrees.md.tmpl",
    "finishing-a-development-branch": "finish-branch.md.tmpl",
    "writing-skills": "write-skill.md.tmpl",
    "verification-before-completion": "verify.md.tmpl",
    "using-superpowers": "use-superpowers.md.tmpl",
}

# compound-engineering upstream skill -> local template filename
COMPOUND_SKILL_MAP: dict[str, str] = {
    "ce-ideate": "ideate.md.tmpl",
    "ce-compound": "compound.md.tmpl",
    "ce-review": "multi-review.md.tmpl",
    "lfg": "lfg.md.tmpl",
    "git-commit": "git-commit.md.tmpl",
    "todo-create": "todo.md.tmpl",
}

GSTACK_REPO = "garrytan/gstack"

# gstack upstream skill -> local template filename
GSTACK_SKILL_MAP: dict[str, str] = {
    "cso": "cso.md.tmpl",
    "retro": "retro.md.tmpl",
    "document-release": "doc-release.md.tmpl",
    "health": "health.md.tmpl",
    "careful": "careful.md.tmpl",
}

ALL_SKILL_MAPS: list[tuple[str, str, dict[str, str]]] = [
    (SUPERPOWERS_REPO, "skills/{name}/SKILL.md", SKILL_MAP),
    (COMPOUND_REPO, "plugins/compound-engineering/skills/{name}/SKILL.md", COMPOUND_SKILL_MAP),
    (GSTACK_REPO, "{name}/SKILL.md", GSTACK_SKILL_MAP),
]


def _fetch_json(url: str) -> dict:
    """Fetch JSON from GitHub API. Tries gh CLI first, falls back to curl."""
    endpoint = url.removeprefix("https://api.github.com/") if url.startswith("https://") else url
    # Try gh CLI
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    # Fallback to curl for public repos
    api_url = f"https://api.github.com/{endpoint}"
    result = subprocess.run(
        ["curl", "-sS", "-H", "Accept: application/vnd.github.v3+json", api_url],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"API request failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _gh_api(endpoint: str) -> str:
    data = _fetch_json(endpoint)
    if "content" not in data:
        msg = data.get("message", "unknown error")
        raise RuntimeError(f"GitHub API error: {msg}")
    return base64.b64decode(data["content"]).decode("utf-8")


def _combined_skill_map() -> dict[str, str]:
    """Merge all skill maps into one."""
    combined: dict[str, str] = {}
    for _, _, skill_map in ALL_SKILL_MAPS:
        combined.update(skill_map)
    return combined


def fetch_skills() -> dict[str, str]:
    """Fetch all skill contents from all upstream repos. Returns {skill_name: content}."""
    skills: dict[str, str] = {}
    for repo, path_tmpl, skill_map in ALL_SKILL_MAPS:
        for skill_name in skill_map:
            try:
                path = path_tmpl.format(name=skill_name)
                content = _gh_api(f"repos/{repo}/contents/{path}")
                skills[skill_name] = content
            except RuntimeError as e:
                print(f"  [WARN] 跳过 {repo}/{skill_name}: {e}", file=sys.stderr)
    return skills


def save_cache(skills: dict[str, str]) -> None:
    """Save fetched skills to cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in skills.items():
        skill_dir = CACHE_DIR / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    VERSION_FILE.write_text(
        json.dumps({
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "skills": sorted(skills.keys()),
            "repos": [r for r, _, _ in ALL_SKILL_MAPS],
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_cache() -> dict[str, str]:
    """Load previously cached skills. Returns {skill_name: content}."""
    cached: dict[str, str] = {}
    if not CACHE_DIR.is_dir():
        return cached
    combined = _combined_skill_map()
    for name in combined:
        path = CACHE_DIR / name / "SKILL.md"
        if path.exists():
            cached[name] = path.read_text(encoding="utf-8")
    return cached


def report(old: dict[str, str], new: dict[str, str]) -> None:
    """Print sync status report."""
    combined = _combined_skill_map()
    all_skills = sorted(set(list(old.keys()) + list(new.keys()) + list(combined.keys())))
    print(f"\n{'Skill':<40} {'状态':<12} {'本地模板'}")
    print("-" * 80)
    changes = 0
    for name in all_skills:
        tmpl = combined.get(name, "???")
        has_local = (TEMPLATE_DIR / tmpl).exists() if tmpl != "???" else False
        if name in new and name not in old:
            status = "NEW"
            changes += 1
        elif name in old and name not in new:
            status = "REMOVED"
            changes += 1
        elif name in old and name in new and old[name] != new[name]:
            status = "MODIFIED"
            changes += 1
        elif name in old and name in new:
            status = "unchanged"
        else:
            status = "not cached"
        local_mark = "OK" if has_local else "MISSING"
        print(f"  {name:<38} {status:<12} {tmpl} [{local_mark}]")
    print(f"\n共 {len(all_skills)} 个 skills，{changes} 个有变化。")
    if VERSION_FILE.exists():
        ver = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
        print(f"缓存时间: {ver.get('date', '?')}")


def show_diff(skill_name: str, old: dict[str, str], new: dict[str, str]) -> None:
    """Show unified diff for a specific skill."""
    old_text = old.get(skill_name, "")
    new_text = new.get(skill_name, "")
    if old_text == new_text:
        print(f"{skill_name}: 无变化")
        return
    diff = unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=f"cached/{skill_name}/SKILL.md",
        tofile=f"upstream/{skill_name}/SKILL.md",
    )
    print("".join(diff) or f"{skill_name}: 无变化")


def main() -> None:
    parser = argparse.ArgumentParser(description="同步 superpowers 上游 skills")
    parser.add_argument("--check", action="store_true", help="只对比缓存，不拉取")
    parser.add_argument("--diff", metavar="SKILL", help="显示指定 skill 的详细 diff")
    args = parser.parse_args()

    old = load_cache()

    if args.check:
        if not old:
            print("缓存为空，请先运行: python scripts/sync_superpowers.py")
            sys.exit(1)
        report({}, old)
        return

    if args.diff:
        if not old:
            print("缓存为空，请先运行一次完整同步。")
            sys.exit(1)
        print(f"正在拉取 {args.diff} 的最新版本...")
        found = False
        for repo, path_tmpl, skill_map in ALL_SKILL_MAPS:
            if args.diff in skill_map:
                try:
                    path = path_tmpl.format(name=args.diff)
                    new_content = _gh_api(f"repos/{repo}/contents/{path}")
                    show_diff(args.diff, old, {args.diff: new_content})
                    found = True
                except RuntimeError as e:
                    print(f"拉取失败: {e}", file=sys.stderr)
                break
        if not found:
            print(f"未找到 skill: {args.diff}", file=sys.stderr)
            sys.exit(1)
        return

    total = sum(len(m) for _, _, m in ALL_SKILL_MAPS)
    repos = ", ".join(r for r, _, _ in ALL_SKILL_MAPS)
    print(f"正在从 {repos} 拉取 {total} 个 skills...")
    new = fetch_skills()
    if not new:
        print("未能拉取任何 skill，请检查网络和 gh 认证。", file=sys.stderr)
        sys.exit(1)

    report(old, new)
    save_cache(new)
    print(f"\n缓存已更新到 {CACHE_DIR.relative_to(ROOT)}/")
    print("如需更新本地模板，请人工对比上游变更后修改模板文件。")


if __name__ == "__main__":
    main()
