"""Core helpers for initializing AI-agent harness files in other repositories."""

from .assessment import assess_project
from .discovery import discover_project
from .initializer import initialize_project
from .models import AssessmentResult, InitializationResult, ProjectProfile, UpgradePlanResult
from .upgrade import plan_upgrade

__all__ = [
    "AssessmentResult",
    "InitializationResult",
    "ProjectProfile",
    "UpgradePlanResult",
    "assess_project",
    "discover_project",
    "initialize_project",
    "plan_upgrade",
]
