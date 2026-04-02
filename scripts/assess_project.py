from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_harness import assess_project, discover_project
from agent_harness.cli_utils import bold, green, red, yellow


def main() -> None:
    parser = argparse.ArgumentParser(description="Assess how ready a repository is for harness initialization.")
    parser.add_argument("target", nargs="?", default=".", help="Target repository path")
    parser.add_argument("--json", action="store_true", help="Print raw JSON")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    profile = discover_project(target)
    result = assess_project(profile, root=target)
    payload = {
        "profile": asdict(profile),
        "assessment": asdict(result),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    color = green if result.readiness == "high" else yellow if result.readiness == "medium" else red
    print(f"readiness: {color(result.readiness)}")
    print(f"score: {bold(str(result.score))}")
    print(f"confidence: {result.confidence}")
    if result.dimensions:
        print("dimensions:")
        for dim_name, dim_score in result.dimensions.items():
            print(f"  {dim_name}: {dim_score}")
    if result.strengths:
        print("strengths:")
        for item in result.strengths:
            print(f"  {green('+')} {item}")
    if result.gaps:
        print("gaps:")
        for item in result.gaps:
            print(f"  {red('-')} {item}")
    if result.recommendations:
        print("recommendations:")
        for item in result.recommendations:
            print(f"  {yellow('>')} {item}")


if __name__ == "__main__":
    main()
