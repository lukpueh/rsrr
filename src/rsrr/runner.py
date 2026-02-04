import asyncio
import importlib
import pkgutil
from pathlib import Path

from .checks import BaseCheck, CheckResult, Context


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


async def run_check(
    check_id: str, check_cls: type[BaseCheck], ctx: Context
) -> CheckResult:
    """Run a single check and return the result."""
    check = check_cls(ctx)
    common = {"name": check.name, "comment": check.comment}
    try:
        value = await check.run()
        ctx.data[check_id] = value
        return CheckResult(**common, value=value, success=True)
    except Exception as e:
        return CheckResult(**common, value=None, success=False, error=str(e))


async def run_checks(
    checks: dict[str, type[BaseCheck]], ctx: Context
) -> list[tuple[str, CheckResult]]:
    """Run all checks respecting dependencies.

    Checks are run in waves. Each wave runs checks whose dependencies have
    all completed. Returns a list of (check_id, result) tuples.
    """
    results: list[tuple[str, CheckResult]] = []
    completed: set[str] = set()
    pending = dict(checks)

    while pending:
        # Find checks whose dependencies are all completed
        ready = {
            check_id: check_cls
            for check_id, check_cls in pending.items()
            if all(dep in completed for dep in check_cls.depends_on)
        }

        if not ready:
            # No checks are ready but some are pending - circular dependency
            raise ValueError(
                f"Circular or unsatisfied dependencies detected. "
                f"Pending checks: {list(pending.keys())}"
            )

        # Run ready checks in parallel
        tasks = [
            run_check(check_id, check_cls, ctx)
            for check_id, check_cls in ready.items()
        ]
        wave_results = await asyncio.gather(*tasks)

        # Record results and mark as completed
        for check_id, result in zip(ready.keys(), wave_results):
            results.append((check_id, result))
            completed.add(check_id)
            del pending[check_id]

    return results
