from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import Ticket
from .router import route_ticket

REQUIRED_FIELDS = ("title", "description", "customer_tier", "channel")


def _load_payload(path_arg: str | None) -> dict[str, object]:
    if path_arg:
        try:
            return json.loads(Path(path_arg).read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SystemExit(f"输入文件不存在: {path_arg}") from exc

    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("需要从标准输入或文件路径提供 JSON 工单")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit("输入不是合法 JSON") from exc


def _build_ticket(payload: dict[str, object]) -> Ticket:
    missing_fields = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing_fields:
        raise SystemExit(f"缺少必填字段: {', '.join(missing_fields)}")

    return Ticket(
        title=str(payload["title"]),
        description=str(payload["description"]),
        customer_tier=str(payload["customer_tier"]),
        channel=str(payload["channel"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Route a support ticket from JSON input.")
    parser.add_argument("input", nargs="?", help="Optional path to a JSON file")
    args = parser.parse_args()

    payload = _load_payload(args.input)
    ticket = _build_ticket(payload)
    result = route_ticket(ticket)
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
