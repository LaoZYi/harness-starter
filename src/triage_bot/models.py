from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum


class QueueName(StrEnum):
    BILLING = "billing"
    SUPPORT = "support"
    SECURITY = "security"
    PRODUCT = "product"


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def label(self) -> str:
        return self.name.lower()

    def escalate(self, steps: int = 1) -> "Priority":
        return Priority(min(int(self) + steps, int(Priority.CRITICAL)))


@dataclass(frozen=True, slots=True)
class Ticket:
    title: str
    description: str
    customer_tier: str
    channel: str

    @property
    def combined_text(self) -> str:
        return f"{self.title} {self.description}".lower()


@dataclass(frozen=True, slots=True)
class TriageResult:
    queue: QueueName
    priority: Priority
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "queue": self.queue.value,
            "priority": self.priority.label,
            "reasons": list(self.reasons),
        }

