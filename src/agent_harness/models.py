from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProjectProfile:
    root: str
    project_name: str
    project_slug: str
    summary: str
    project_type: str
    language: str
    package_manager: str
    run_command: str
    test_command: str
    check_command: str
    ci_command: str
    deploy_target: str
    has_production: bool
    sensitivity: str
    source_paths: list[str] = field(default_factory=list)
    test_paths: list[str] = field(default_factory=list)
    docs_paths: list[str] = field(default_factory=list)
    ci_paths: list[str] = field(default_factory=list)
    external_systems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class InitializationResult:
    target_root: str
    context: dict[str, str]
    written_files: list[str]
    skipped_files: list[str]
    dry_run: bool = False
    summary_path: str | None = None


@dataclass(slots=True)
class AssessmentResult:
    score: int
    readiness: str
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class UpgradePlanResult:
    target_root: str
    create_files: list[str] = field(default_factory=list)
    update_files: list[str] = field(default_factory=list)
    unchanged_files: list[str] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)


@dataclass(slots=True)
class UpgradeExecutionResult:
    target_root: str
    created_files: list[str] = field(default_factory=list)
    updated_files: list[str] = field(default_factory=list)
    unchanged_files: list[str] = field(default_factory=list)
    backup_root: str | None = None
