from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ticket_router.cli import _build_ticket, _load_payload


class CliHelpersTests(unittest.TestCase):
    def test_load_payload_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ticket.json"
            path.write_text(
                json.dumps(
                    {
                        "title": "service down",
                        "description": "api unavailable",
                        "customer_tier": "pro",
                        "channel": "email",
                    }
                ),
                encoding="utf-8",
            )

            payload = _load_payload(str(path))

        self.assertEqual(payload["title"], "service down")

    def test_build_ticket_requires_all_fields(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            _build_ticket({"title": "missing fields"})

        self.assertIn("缺少必填字段", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
