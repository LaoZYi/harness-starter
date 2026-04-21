"""LFG audit — 10-dimension scorecard for /lfg feature coverage.

Answers the question: "Does /lfg actually wire in every capability the project
has added, or are new features orphaned?" (See lessons.md "单入口技能 ≠
能力接入完整" — the two-checklist approach.)

Static analysis only:
- Reads `templates/superpowers/.claude/commands/lfg.md.tmpl`
- Reads `templates/superpowers/skills-registry.json`
- Reads `templates/common/.claude/rules/*.md.tmpl` + presets' `exclude_rules`

Each dimension scores 0.0-1.0. Total score 0-10. Default pass threshold 7.0.

CLI: `harness lfg audit [--json] [--threshold N] [--repo PATH]` (in lfg_audit_cli.py)
Exit 0 if score >= threshold, 1 if below, 2 on infra failure.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .skills_registry import load_registry

SUPERPOWERS_REL = "src/agent_harness/templates/superpowers"
COMMON_REL = "src/agent_harness/templates/common"
PRESETS_REL = "src/agent_harness/presets"
LFG_TMPL_REL = ".claude/commands/lfg.md.tmpl"


@dataclass
class DimensionScore:
    id: int
    name: str
    score: float  # 0.0 - 1.0
    checks: list[tuple[str, bool]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for _, ok in self.checks if ok)

    @property
    def total(self) -> int:
        return len(self.checks)


@dataclass
class ScoreCard:
    template_path: Path
    dimensions: list[DimensionScore]

    @property
    def total(self) -> float:
        return round(sum(d.score for d in self.dimensions), 2)

    @property
    def max_total(self) -> int:
        return len(self.dimensions)

    def to_json(self) -> dict:
        return {
            "template_path": str(self.template_path),
            "total": self.total,
            "max_total": self.max_total,
            "dimensions": [
                {
                    "id": d.id,
                    "name": d.name,
                    "score": round(d.score, 2),
                    "passed": d.passed,
                    "total": d.total,
                    "checks": [{"name": n, "ok": ok} for n, ok in d.checks],
                    "notes": d.notes,
                }
                for d in self.dimensions
            ],
        }

    def to_console(self) -> str:
        lines = [
            f"# /lfg 威力释放度体检 — {self.total}/{self.max_total}",
            f"  模板：{self.template_path}",
            "",
        ]
        for d in self.dimensions:
            icon = _score_icon(d.score)
            lines.append(
                f"{icon} {d.id:>2}. {d.name}: {d.score:.2f}/1.00"
                f"  ({d.passed}/{d.total} 通过)"
            )
            for name, ok in d.checks:
                check_icon = "✅" if ok else "❌"
                lines.append(f"       {check_icon} {name}")
            for note in d.notes:
                lines.append(f"       ℹ  {note}")
            lines.append("")
        weak = [d for d in self.dimensions if d.score < 0.5]
        if weak:
            lines.append("## 建议优先修补（score < 0.5）")
            for d in weak:
                missing = [n for n, ok in d.checks if not ok]
                lines.append(f"- 维度 {d.id} {d.name}:")
                for m in missing:
                    lines.append(f"    · 缺：{m}")
        else:
            lines.append("## 所有维度 >= 0.5，总体健康")
        return "\n".join(lines)


def _score_icon(score: float) -> str:
    if score >= 0.9:
        return "🟢"
    if score >= 0.5:
        return "🟡"
    return "🔴"


def collect_opt_in_rules(repo_root: Path) -> set[str]:
    """Rules appearing in any preset's `exclude_rules` are opt-in (not baseline)."""
    presets_dir = repo_root / PRESETS_REL
    opt_in: set[str] = set()
    if not presets_dir.exists():
        return opt_in
    for p in presets_dir.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for r in data.get("exclude_rules", []) or []:
            opt_in.add(r)
    return opt_in


def audit(repo_root: Path) -> ScoreCard:
    """Run all 10 dimension checks and return a ScoreCard.

    Raises FileNotFoundError if lfg.md.tmpl is missing, or ValueError /
    json.JSONDecodeError if skills-registry.json is corrupt. These are
    infrastructure failures — refuse to produce a misleading scorecard.
    """
    from .lfg_audit_checks import DIMENSION_CHECKS  # late import avoids cycle

    repo_root = Path(repo_root).resolve()
    lfg_tmpl = repo_root / SUPERPOWERS_REL / LFG_TMPL_REL
    if not lfg_tmpl.is_file():
        raise FileNotFoundError(f"lfg.md.tmpl not found at {lfg_tmpl}")
    lfg_text = lfg_tmpl.read_text(encoding="utf-8")

    # Fail fast on corrupt registry — a 0-scored dim 2 would mask this.
    load_registry(repo_root / SUPERPOWERS_REL)

    dimensions = [check(lfg_text, repo_root) for check in DIMENSION_CHECKS]
    return ScoreCard(template_path=lfg_tmpl, dimensions=dimensions)
