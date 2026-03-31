"""Production-oriented starter package for ticket routing."""

from .models import Priority, QueueName, Ticket, TriageResult
from .router import route_ticket

__all__ = [
    "Priority",
    "QueueName",
    "Ticket",
    "TriageResult",
    "route_ticket",
]
