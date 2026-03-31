from __future__ import annotations

import json

from .models import Ticket
from .router import route_ticket


def main() -> None:
    demo_ticket = Ticket(
        title="Refund request for duplicate charge",
        description="Customer was charged twice and asked for a refund in chat.",
        customer_tier="pro",
        channel="chat",
    )
    result = route_ticket(demo_ticket)
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

