from __future__ import annotations

from .models import Priority, QueueName, Ticket, TriageResult

SECURITY_KEYWORDS = ("breach", "data leak", "security", "vulnerability")
BILLING_KEYWORDS = ("invoice", "refund", "payment", "charge")
PRODUCT_KEYWORDS = ("feature", "roadmap", "integration")
INCIDENT_KEYWORDS = ("outage", "service down", "unavailable", "latency")


def _contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def route_ticket(ticket: Ticket) -> TriageResult:
    text = ticket.combined_text
    reasons: list[str] = []
    queue = QueueName.SUPPORT
    priority = Priority.MEDIUM

    if _contains_keyword(text, SECURITY_KEYWORDS):
        queue = QueueName.SECURITY
        priority = Priority.HIGH
        reasons.append("命中安全关键词")
    elif _contains_keyword(text, BILLING_KEYWORDS):
        queue = QueueName.BILLING
        reasons.append("命中计费关键词")
    elif _contains_keyword(text, PRODUCT_KEYWORDS):
        queue = QueueName.PRODUCT
        reasons.append("命中产品反馈关键词")
    elif _contains_keyword(text, INCIDENT_KEYWORDS):
        queue = QueueName.SUPPORT
        priority = Priority.HIGH
        reasons.append("命中可用性事件关键词")
    else:
        reasons.append("落入默认支持队列")

    if ticket.customer_tier.lower() == "enterprise":
        priority = priority.escalate()
        reasons.append("企业客户优先级提升")

    if ticket.channel.lower() == "chat" and len(ticket.description) > 280:
        priority = priority.escalate()
        reasons.append("长聊天工单优先级提升")

    return TriageResult(queue=queue, priority=priority, reasons=tuple(reasons))
