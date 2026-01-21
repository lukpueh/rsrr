import asyncio
import sys
from pathlib import Path

import click

from .formatters import FORMATTERS
from .runner import discover_checks, run_checks


def list_checks(checks: dict) -> None:
    """Print available checks."""
    click.echo("Available checks:\n")
    for check_id, check_cls in sorted(checks.items()):
        click.echo(f"  {check_id}")
        click.echo(f"    {check_cls.name}: {check_cls.comment}")
        click.echo()


@click.command()
@click.argument("checks", nargs=-1, metavar="CHECK")
@click.option(
    "-l", "--list", "list_", is_flag=True, help="List available checks and exit"
)
@click.option(
    "-f",
    "--format",
    "format_",
    type=click.Choice(list(FORMATTERS.keys())),
    default="plain",
    help="Output format (default: plain)",
)
def main(checks: tuple[str, ...], list_: bool, format_: str) -> None:
    """Run predefined checks and report results."""
    sys.exit(asyncio.run(main_async(checks, list_, format_)))


async def main_async(checks: tuple[str, ...], list_: bool, format_: str) -> int:
    checks_dir = Path(__file__).parent / "checks"
    all_checks = discover_checks(checks_dir)

    if list_:
        list_checks(all_checks)
        return 0

    # Filter checks if specific ones requested
    if checks:
        unknown = set(checks) - set(all_checks.keys())
        if unknown:
            click.echo(f"Unknown checks: {', '.join(sorted(unknown))}", err=True)
            click.echo("Use --list to see available checks", err=True)
            return 1
        checks_to_run = {k: v for k, v in all_checks.items() if k in checks}
    else:
        checks_to_run = all_checks

    if not checks_to_run:
        click.echo("No checks to run", err=True)
        return 1

    results = await run_checks(checks_to_run)

    formatter = FORMATTERS[format_]()
    click.echo(formatter.format(results))

    # Exit with error if any check failed
    failed = any(not result.success for _, result in results)
    return 1 if failed else 0


if __name__ == "__main__":
    main()
