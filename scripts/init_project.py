"""Deprecated: use ``harness init`` instead."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.warn("scripts/init_project.py is deprecated; use `harness init`", DeprecationWarning, stacklevel=1)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

argv = sys.argv[1:]
new_argv = ["init"]
i = 0
while i < len(argv):
    if argv[i] == "--target" and i + 1 < len(argv):
        new_argv.insert(1, argv[i + 1])
        i += 2
    else:
        new_argv.append(argv[i])
        i += 1

sys.argv = [sys.argv[0]] + new_argv
from agent_harness.cli import main  # noqa: E402

main()
