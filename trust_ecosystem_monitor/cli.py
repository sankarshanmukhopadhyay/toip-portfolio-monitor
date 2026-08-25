from __future__ import annotations

import argparse
import sys

from .engine import collect
from .profile import DEFAULT_PROFILE_PATH
from .site import render_catalog
from .validation import validate


def main() -> int:
    parser = argparse.ArgumentParser(prog="trust-ecosystem-monitor")
    sub = parser.add_subparsers(dest="command", required=True)

    collect_cmd = sub.add_parser(
        "collect",
        help="Collect one ecosystem profile into profile-scoped evidence and reporting",
    )
    collect_cmd.add_argument("--lookback-days", type=int, default=7)
    collect_cmd.add_argument("--output-root", default=".")
    collect_cmd.add_argument(
        "--profile",
        default=str(DEFAULT_PROFILE_PATH),
        help="Organization profile TOML file (defaults to TrustOverIP)",
    )

    site_cmd = sub.add_parser(
        "site",
        help="Render the top-level Trust Ecosystem Monitor catalog from generated ecosystem reports",
    )
    site_cmd.add_argument("--root", default=".")

    validate_cmd = sub.add_parser(
        "validate",
        help="Validate repository structure and, when requested, every configured ecosystem's generated evidence",
    )
    validate_cmd.add_argument("--root", default=".")
    validate_cmd.add_argument(
        "--require-generated",
        action="store_true",
        help="Require a current generated report for every configured organization profile",
    )

    args = parser.parse_args()
    if args.command == "collect":
        path = collect(args.lookback_days, args.output_root, args.profile)
        print(path)
        return 0
    if args.command == "site":
        render_catalog(args.root)
        print("ecosystem catalog rendered")
        return 0

    errors = validate(args.root, require_generated=args.require_generated)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validation passed")
    return 0
