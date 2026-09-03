from __future__ import annotations

import argparse
import json
from pathlib import Path

from .workflow import bootstrap, status, validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage an auditable agentic research workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("bootstrap", help="Create a workflow run from an intake note")
    create.add_argument("--intake", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)

    show = subparsers.add_parser("status", help="Show stage and gate status")
    show.add_argument("--run-dir", type=Path, required=True)

    check = subparsers.add_parser("validate", help="Validate files, dependencies, and review gates")
    check.add_argument("--run-dir", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "bootstrap":
        output = bootstrap(args.intake, args.output)
        print(f"Created workflow run: {output}")
        return 0

    if args.command == "status":
        print(json.dumps(status(args.run_dir), indent=2))
        return 0

    issues = validate(args.run_dir)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1
    print("Workflow validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

