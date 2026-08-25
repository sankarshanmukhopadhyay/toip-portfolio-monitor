from __future__ import annotations

import argparse
import sys

from .core import collect, validate
from .site import render_site


def main() -> int:
    parser = argparse.ArgumentParser(prog="toip-monitor")
    sub = parser.add_subparsers(dest="command", required=True)

    collect_cmd = sub.add_parser("collect", help="Discover ToIP repositories, collect evidence, and render the weekly brief")
    collect_cmd.add_argument("--lookback-days", type=int, default=7)
    collect_cmd.add_argument("--output-root", default=".")

    site_cmd = sub.add_parser("site", help="Render the decision-grade GitHub Pages information architecture from latest evidence")
    site_cmd.add_argument("--root", default=".")

    validate_cmd = sub.add_parser("validate", help="Validate repository structure and, when requested, current generated evidence")
    validate_cmd.add_argument("--root", default=".")
    validate_cmd.add_argument(
        "--require-generated",
        action="store_true",
        help="Require docs/data/latest.json to use the current schema and include all generated intelligence collections",
    )

    args = parser.parse_args()
    if args.command == "collect":
        path = collect(args.lookback_days, args.output_root)
        print(path)
        return 0
    if args.command == "site":
        render_site(args.root)
        print("site rendered")
        return 0

    errors = validate(args.root, require_generated=args.require_generated)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validation passed")
    return 0
