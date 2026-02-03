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
        run_check(check_id, check_cls, context)
        for check_id, check_cls in checks.items()
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
    """Run queries respecting dependencies, parallel within each level.

    Returns a list of (query id, result) tuples in execution order.
    """
    # Build mapping from result_key to query_id
    result_key_to_id: dict[str, str] = {}
    for query_id, query_cls in queries.items():
        result_key_to_id[query_cls.result_key] = query_id

    # Track which queries have been executed and their results
    executed: set[str] = set()  # result_keys that have been executed
    all_results: list[tuple[str, QueryResult]] = []

    # Get result_keys already available in context (from previous runs)
    available = set(context.query_results.keys())

    remaining = dict(queries)

    while remaining:
        # Find queries whose dependencies are satisfied
        ready: dict[str, type[BaseQuery]] = {}
        for query_id, query_cls in remaining.items():
            deps_satisfied = all(
                dep in executed or dep in available for dep in query_cls.depends_on
            )
            if deps_satisfied:
                ready[query_id] = query_cls

        if not ready:
            # No queries can run - circular dependency or missing dependency
            missing_deps = []
            for query_id, query_cls in remaining.items():
                for dep in query_cls.depends_on:
                    if dep not in executed and dep not in available:
                        if (
                            dep not in result_key_to_id
                            or result_key_to_id[dep] not in queries
                        ):
                            missing_deps.append(f"{query_id} requires '{dep}'")
            if missing_deps:
                raise ValueError(
                    f"Missing query dependencies: {', '.join(missing_deps)}"
                )
            raise ValueError("Circular dependency detected among queries")

        # Run ready queries in parallel
        tasks = [
            run_query(query_id, query_cls, context)
            for query_id, query_cls in ready.items()
        ]
        results = await asyncio.gather(*tasks)

        # Record results and mark as executed
        for query_id, result in zip(ready.keys(), results):
            all_results.append((query_id, result))
            query_cls = ready[query_id]
            executed.add(query_cls.result_key)
            del remaining[query_id]

    return all_results
