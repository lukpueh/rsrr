import asyncio
import importlib
import pkgutil
from pathlib import Path

from .checks import BaseCheck, CheckResult
from .context import Context
from .queries import BaseQuery, QueryResult


def discover_checks(package_path: Path) -> dict[str, type[BaseCheck]]:
    """Discover all check implementations in the checks package.

    Returns a dict mapping check IDs (module names) to check classes.
    """
    checks: dict[str, type[BaseCheck]] = {}

    for module_info in pkgutil.iter_modules([str(package_path)]):
        if module_info.name in ("base", "__init__"):
            continue

        module = importlib.import_module(f".checks.{module_info.name}", package="rsrr")

        if hasattr(module, "Check") and issubclass(module.Check, BaseCheck):
            checks[module_info.name] = module.Check

    return checks


def discover_queries(package_path: Path) -> dict[str, type[BaseQuery]]:
    """Discover all query implementations in the queries package.

    Returns a dict mapping query IDs (module names) to query classes.
    """
    queries: dict[str, type[BaseQuery]] = {}

    for module_info in pkgutil.iter_modules([str(package_path)]):
        if module_info.name in ("base", "__init__"):
            continue

        module = importlib.import_module(f".queries.{module_info.name}", package="rsrr")

        if hasattr(module, "Query") and issubclass(module.Query, BaseQuery):
            queries[module_info.name] = module.Query

    return queries


async def run_check(
    check_id: str, check_cls: type[BaseCheck], context: Context
) -> CheckResult:
    """Run a single check and return the result."""
    check = check_cls(context)
    common = {"name": check.name, "comment": check.comment}
    try:
        value = await check.run()
        return CheckResult(**common, value=value, success=True)
    except Exception as e:
        return CheckResult(**common, value=None, success=False, error=str(e))


async def run_checks(
    checks: dict[str, type[BaseCheck]], context: Context
) -> list[tuple[str, CheckResult]]:
    """Run all checks in parallel and return a list of (check name, result) tuples."""
    tasks = [
        run_check(check_id, check_cls, context) for check_id, check_cls in checks.items()
    ]
    results = await asyncio.gather(*tasks)
    return list(zip(checks.keys(), results))


async def run_query(
    query_id: str, query_cls: type[BaseQuery], context: Context
) -> QueryResult:
    """Run a single query and return the result."""
    query = query_cls(context)
    common = {"name": query.name, "comment": query.comment}
    try:
        data = await query.run()
        context.query_results[query.result_key] = data
        return QueryResult(**common, data=data, success=True)
    except Exception as e:
        return QueryResult(**common, data=None, success=False, error=str(e))


async def run_queries(
    queries: dict[str, type[BaseQuery]], context: Context
) -> list[tuple[str, QueryResult]]:
    """Run all queries in parallel and return a list of (query name, result) tuples."""
    tasks = [
        run_query(query_id, query_cls, context)
        for query_id, query_cls in queries.items()
    ]
    results = await asyncio.gather(*tasks)
    return list(zip(queries.keys(), results))
