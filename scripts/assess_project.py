from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_harness import assess_project, discover_project


def main() -> None:
    parser = argparse.ArgumentParser(description="Assess how ready a repository is for harness initialization.")
    parser.add_argument("target", nargs="?", default=".", help="Target repository path")
    parser.add_argument("--json", action="store_true", help="Print raw JSON")
    args = parser.parse_args()

    profile = discover_project(Path(args.target))
    result = assess_project(profile)
    payload = {
        "profile": asdict(profile),
        "assessment": asdict(result),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"readiness: {result.readiness}")
    print(f"score: {result.score}")
    if result.strengths:
        print("strengths:")
        for item in result.strengths:
            print(f"- {item}")
    if result.gaps:
        print("gaps:")
        for item in result.gaps:
            print(f"- {item}")
    if result.recommendations:
        print("recommendations:")
        for item in result.recommendations:
            print(f"- {item}")


if __name__ == "__main__":
    main()
