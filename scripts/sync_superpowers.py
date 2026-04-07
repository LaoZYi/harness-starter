"""Sync superpowers skills from upstream obra/superpowers repository.

Fetches latest SKILL.md files via GitHub API, caches them locally,
and reports changes against the previous cached version.
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

REPO = "obra/superpowers"

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


def _get_head_sha() -> str:
    data = _fetch_json(f"repos/{REPO}/commits/main")
    return data["sha"][:12]


def fetch_skills() -> dict[str, str]:
    """Fetch all skill contents from upstream. Returns {skill_name: content}."""
    skills: dict[str, str] = {}
    for skill_name in SKILL_MAP:
        try:
            content = _gh_api(f"repos/{REPO}/contents/skills/{skill_name}/SKILL.md")
            skills[skill_name] = content
        except RuntimeError as e:
            print(f"  [WARN] 跳过 {skill_name}: {e}", file=sys.stderr)
    return skills


def save_cache(skills: dict[str, str]) -> None:
    """Save fetched skills to cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in skills.items():
        skill_dir = CACHE_DIR / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    sha = _get_head_sha()
    VERSION_FILE.write_text(
        json.dumps({
            "sha": sha,
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "skills": sorted(skills.keys()),
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_cache() -> dict[str, str]:
    """Load previously cached skills. Returns {skill_name: content}."""
    cached: dict[str, str] = {}
    if not CACHE_DIR.is_dir():
        return cached
    for name in SKILL_MAP:
        path = CACHE_DIR / name / "SKILL.md"
        if path.exists():
            cached[name] = path.read_text(encoding="utf-8")
    return cached


def report(old: dict[str, str], new: dict[str, str]) -> None:
    """Print sync status report."""
    all_skills = sorted(set(list(old.keys()) + list(new.keys()) + list(SKILL_MAP.keys())))
    print(f"\n{'Skill':<40} {'状态':<12} {'本地模板'}")
    print("-" * 80)
    changes = 0
    for name in all_skills:
        tmpl = SKILL_MAP.get(name, "???")
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
        print(f"上游 commit: {ver.get('sha', '?')}  缓存时间: {ver.get('date', '?')}")


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
        try:
            new_content = _gh_api(f"repos/{REPO}/contents/skills/{args.diff}/SKILL.md")
        except RuntimeError as e:
            print(f"拉取失败: {e}", file=sys.stderr)
            sys.exit(1)
        show_diff(args.diff, old, {args.diff: new_content})
        return

    print(f"正在从 {REPO} 拉取 {len(SKILL_MAP)} 个 skills...")
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
