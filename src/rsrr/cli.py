import asyncio
import sys
from pathlib import Path

import click

from .context import Context
from .formatters import FormatterConfig, PlainFormatter
from .runner import discover_checks, discover_queries, run_checks, run_queries


def get_all_checks() -> dict:
    """Discover and return all available checks."""
    checks_dir = Path(__file__).parent / "checks"
    return discover_checks(checks_dir)


def get_all_queries() -> dict:
    """Discover and return all available queries."""
    queries_dir = Path(__file__).parent / "queries"
    return discover_queries(queries_dir)


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


@main.command("list-queries")
def list_queries_cmd() -> None:
    """List available queries."""
    all_queries = get_all_queries()
    click.echo("Available queries:\n")
    for query_id, query_cls in sorted(all_queries.items()):
        click.echo(f"  {query_id}")
        click.echo(f"    {query_cls.name}: {query_cls.comment}")
        click.echo()


@main.command("query")
@click.argument("queries", nargs=-1, metavar="QUERY")
@click.option(
    "--ef-project-id",
    default=None,
    help="Eclipse Foundation project ID",
)
@click.option(
    "--context-file",
    default="context.json",
    type=click.Path(),
    help="Path to context JSON file",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def query_cmd(
    queries: tuple[str, ...],
    ef_project_id: str | None,
    context_file: str,
    verbose: bool,
) -> None:
    """Run queries and save results to context file.

    If QUERY arguments are provided, only those queries are run.
    Otherwise, all available queries are run.
    """
    context = Context(ef_project_id=ef_project_id)
    context_path = Path(context_file)
    sys.exit(asyncio.run(query_async(queries, context, context_path, verbose)))


async def query_async(
    queries: tuple[str, ...],
    context: Context,
    context_path: Path,
    verbose: bool,
) -> int:
    all_queries = get_all_queries()

    # Filter queries if specific ones requested
    if queries:
        unknown = set(queries) - set(all_queries.keys())
        if unknown:
            click.echo(f"Unknown queries: {', '.join(sorted(unknown))}", err=True)
            click.echo("Use 'rsrr list-queries' to see available queries", err=True)
            return 1
        queries_to_run = {k: v for k, v in all_queries.items() if k in queries}
    else:
        queries_to_run = all_queries

    if not queries_to_run:
        click.echo("No queries to run", err=True)
        return 1

    results = await run_queries(queries_to_run, context)

    # Display results
    for query_id, result in results:
        status = "ok" if result.success else "err"
        if result.success:
            click.echo(f"[{status}] {result.name} [{query_id}]")
            if verbose:
                click.echo(f"  # {result.comment}")
        else:
            click.echo(f"[{status}] {result.name} [{query_id}]: {result.error}")

    # Save context
    context.save(context_path)
    click.echo(f"\nContext saved to {context_path}")

    # Exit with error if any query failed
    failed = any(not result.success for _, result in results)
    return 1 if failed else 0


@main.command()
@click.argument("checks", nargs=-1, metavar="CHECK")
@click.option(
    "--context-file",
    default="context.json",
    type=click.Path(exists=True),
    help="Path to context JSON file",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def run(
    checks: tuple[str, ...],
    context_file: str,
    verbose: bool,
) -> None:
    """Run checks using context from file.

    If CHECK arguments are provided, only those checks are run.
    Otherwise, all available checks are run.
    """
    context_path = Path(context_file)
    context = Context.load(context_path)
    formatter_config = FormatterConfig(verbose=verbose)
    sys.exit(asyncio.run(run_async(checks, context, formatter_config)))


async def run_async(
    checks: tuple[str, ...], context: Context, formatter_config: FormatterConfig
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

    results = await run_checks(checks_to_run, context)

    click.echo(PlainFormatter(formatter_config).format(results))

    # Exit with error if any check failed
    failed = any(not result.success for _, result in results)
    return 1 if failed else 0


if __name__ == "__main__":
    main()
