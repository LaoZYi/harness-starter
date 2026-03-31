from __future__ import annotations

import unittest

from ticket_router.models import Priority, QueueName, Ticket
from ticket_router.router import route_ticket


class RouteTicketTests(unittest.TestCase):
    def test_security_ticket_goes_to_security_queue(self) -> None:
        ticket = Ticket(
            title="Possible security breach",
            description="We suspect a data leak in the admin panel.",
            customer_tier="pro",
            channel="email",
        )

        result = route_ticket(ticket)

        self.assertEqual(result.queue, QueueName.SECURITY)
        self.assertEqual(result.priority, Priority.HIGH)
        self.assertIn("命中安全关键词", result.reasons)

    def test_enterprise_billing_ticket_escalates_priority(self) -> None:
        ticket = Ticket(
            title="Invoice mismatch",
            description="The payment total is not correct on our invoice.",
            customer_tier="enterprise",
            channel="web",
        )

        result = route_ticket(ticket)

        self.assertEqual(result.queue, QueueName.BILLING)
        self.assertEqual(result.priority, Priority.HIGH)
        self.assertIn("企业客户优先级提升", result.reasons)

    def test_long_chat_ticket_escalates_default_support_queue(self) -> None:
        ticket = Ticket(
            title="Need help onboarding",
            description="x" * 281,
            customer_tier="free",
            channel="chat",
        )

        result = route_ticket(ticket)

        self.assertEqual(result.queue, QueueName.SUPPORT)
        self.assertEqual(result.priority, Priority.HIGH)
        self.assertIn("长聊天工单优先级提升", result.reasons)

    def test_product_feedback_is_routed_correctly(self) -> None:
        ticket = Ticket(
            title="Feature request",
            description="We need a new integration on the roadmap.",
            customer_tier="pro",
            channel="email",
        )

        result = route_ticket(ticket)

        self.assertEqual(result.queue, QueueName.PRODUCT)
        self.assertEqual(result.priority, Priority.MEDIUM)

    def test_incident_ticket_gets_high_priority_support(self) -> None:
        ticket = Ticket(
            title="Major outage in dashboard",
            description="The service is unavailable for multiple customers.",
            customer_tier="pro",
            channel="email",
        )

        result = route_ticket(ticket)

        self.assertEqual(result.queue, QueueName.SUPPORT)
        self.assertEqual(result.priority, Priority.HIGH)
        self.assertIn("命中可用性事件关键词", result.reasons)


if __name__ == "__main__":
    unittest.main()
