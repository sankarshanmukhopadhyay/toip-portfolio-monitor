from __future__ import annotations

import argparse
import sys

from .core import collect, validate


def main() -> int:
    parser = argparse.ArgumentParser(prog="toip-monitor")
    sub = parser.add_subparsers(dest="command", required=True)

    collect_cmd = sub.add_parser("collect", help="Discover ToIP repositories, collect evidence, and render the weekly brief")
    collect_cmd.add_argument("--lookback-days", type=int, default=7)
    collect_cmd.add_argument("--output-root", default=".")

    validate_cmd = sub.add_parser("validate", help="Validate repository and generated snapshot structure")
    validate_cmd.add_argument("--root", default=".")

    args = parser.parse_args()
    if args.command == "collect":
        path = collect(args.lookback_days, args.output_root)
        print(path)
        return 0

    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validation passed")
    return 0
