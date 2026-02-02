import asyncio
import sys
from pathlib import Path
import json

import click

from .checks import Context
from .formatters import FormatterConfig
from .runner import discover_checks, run_checks


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
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def run(
    checks: tuple[str, ...],
    ef_project_id: str | None,
    verbose: bool,
) -> None:
    """Run checks.

    If CHECK arguments are provided, only those checks are run.
    Otherwise, all available checks are run.
    """
    ctx = Context(ef_project_id=ef_project_id)
    formatter_config = FormatterConfig(verbose=verbose)
    sys.exit(asyncio.run(run_async(checks, ctx, formatter_config)))


async def run_async(
    checks: tuple[str, ...], ctx: Context, formatter_config: FormatterConfig
) -> int:
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

    results = await run_checks(checks_to_run, ctx)

    # Print status info to stderr
    # TODO: Use logging for this instead?
    if formatter_config.verbose:
        for id_, result in results:
            status = f"✓ {id_}" if result.success else f"✗ {id_}: {result.error}"
            click.echo(status, err=True)

    # Print json data to stdout
    click.echo(json.dumps(ctx.data))

    # Exit with error if any check failed
    failed = any(not result.success for _, result in results)
    return 1 if failed else 0


if __name__ == "__main__":
    main()
