import argparse
import asyncio
import sys
from pathlib import Path

from .formatters import FORMATTERS
from .runner import discover_checks, run_checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rsrr",
        description="Run predefined checks and report results",
    )
    parser.add_argument(
        "checks",
        nargs="*",
        metavar="CHECK",
        help="Specific check IDs to run (runs all if not specified)",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available checks and exit",
    )
    parser.add_argument(
        "-f", "--format",
        choices=list(FORMATTERS.keys()),
        default="plain",
        help="Output format (default: plain)",
    )
    return parser.parse_args()


def list_checks(checks: dict) -> None:
    """Print available checks."""
    print("Available checks:\n")
    for check_id, check_cls in sorted(checks.items()):
        print(f"  {check_id}")
        print(f"    {check_cls.name}: {check_cls.comment}")
        print()


async def main_async() -> int:
    args = parse_args()

    checks_dir = Path(__file__).parent / "checks"
    all_checks = discover_checks(checks_dir)

    if args.list:
        list_checks(all_checks)
        return 0

    # Filter checks if specific ones requested
    if args.checks:
        unknown = set(args.checks) - set(all_checks.keys())
        if unknown:
            print(f"Unknown checks: {', '.join(sorted(unknown))}", file=sys.stderr)
            print(f"Use --list to see available checks", file=sys.stderr)
            return 1
        checks_to_run = {k: v for k, v in all_checks.items() if k in args.checks}
    else:
        checks_to_run = all_checks

    if not checks_to_run:
        print("No checks to run", file=sys.stderr)
        return 1

    results = await run_checks(checks_to_run)

    formatter = FORMATTERS[args.format]()
    print(formatter.format(results))

    # Exit with error if any check failed
    failed = any(not result.success for _, result in results)
    return 1 if failed else 0


def main() -> None:
    sys.exit(asyncio.run(main_async()))


if __name__ == "__main__":
    main()
