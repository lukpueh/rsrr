import asyncio
import sys
import logging
import json
from pathlib import Path

import click

from .checks import Context
from .runner import discover_checks, run_checks

logger = logging.getLogger(__name__)


def get_all_checks() -> dict:
    """Discover and return all available checks."""
    checks_dir = Path(__file__).parent / "checks"
    return discover_checks(checks_dir)


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Rapid Security Review Runner -- Runs an extensible set of checks for
    Eclipse Foundation Rapid Security Reviews."""

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("list")
def list_cmd() -> None:
    """List available checks."""
    all_checks = get_all_checks()
    click.echo("Available checks:\n")
    for check_id, check_cls in sorted(all_checks.items()):
        click.echo(f"  {check_id}")
        click.echo(f"    {check_cls.name}: {check_cls.comment}")
        click.echo()


@main.command()
@click.argument("checks", nargs=-1, metavar="CHECK")
@click.option(
    "--ef-project-id",
    default=None,
    help="Eclipse Foundation project ID",
)
def run(
    checks: tuple[str, ...],
    ef_project_id: str | None,
) -> None:
    """Run checks.

    If CHECK arguments are provided, only those checks are run.
    Otherwise, all available checks are run.
    """
    ctx = Context(ef_project_id=ef_project_id)
    sys.exit(asyncio.run(run_async(checks, ctx)))


async def run_async(checks: tuple[str, ...], ctx: Context) -> int:
    all_checks = get_all_checks()

    # Filter checks if specific ones requested
    if checks:
        unknown = set(checks) - set(all_checks.keys())
        if unknown:
            click.echo(f"Unknown checks: {', '.join(sorted(unknown))}", err=True)
            click.echo("Use 'rsrr list' to see available checks", err=True)
            return 1
        checks_to_run = {k: v for k, v in all_checks.items() if k in checks}
    else:
        checks_to_run = all_checks

    if not checks_to_run:
        click.echo("No checks to run", err=True)
        return 1

    try:
        await run_checks(checks_to_run, ctx)
    except ValueError as e:
        logger.error(e)

    click.echo(json.dumps(ctx.data))

    return 0


if __name__ == "__main__":
    main()
