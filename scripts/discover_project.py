from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_harness.discovery import discover_project


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover project metadata for harness initialization.")
    parser.add_argument("target", nargs="?", default=".", help="Target repository path")
    parser.add_argument("--json", action="store_true", help="Print raw JSON")
    args = parser.parse_args()

    profile = discover_project(Path(args.target))
    payload = asdict(profile)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"project_name: {profile.project_name}")
    print(f"project_type: {profile.project_type}")
    print(f"language: {profile.language}")
    print(f"package_manager: {profile.package_manager}")
    print(f"run_command: {profile.run_command}")
    print(f"test_command: {profile.test_command}")
    print(f"check_command: {profile.check_command}")
    print(f"ci_command: {profile.ci_command}")
    print(f"deploy_target: {profile.deploy_target}")
    print(f"has_production: {profile.has_production}")
    print(f"sensitivity: {profile.sensitivity}")
    print(f"source_paths: {', '.join(profile.source_paths) or '无'}")
    print(f"external_systems: {', '.join(profile.external_systems) or '无'}")
    if profile.notes:
        print("notes:")
        for note in profile.notes:
            print(f"- {note}")


if __name__ == "__main__":
    main()

