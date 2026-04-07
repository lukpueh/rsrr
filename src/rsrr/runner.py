import asyncio
import importlib.util
import pkgutil
import logging
from pathlib import Path

from .base import BaseCheck, Context

logger = logging.getLogger(__name__)


def discover_checks(package_path: Path) -> dict[str, type[BaseCheck]]:
    """Discover all check implementations in a directory.

    Loads each .py module (except base.py and __init__.py) from package_path
    and collects those that export a Check class inheriting from BaseCheck.

    Returns a dict mapping check IDs (module names) to check classes.
    """
    checks: dict[str, type[BaseCheck]] = {}

    for module_info in pkgutil.iter_modules([str(package_path)]):
        if module_info.name in ("base", "__init__"):
            continue

        module_file = package_path / f"{module_info.name}.py"
        spec = importlib.util.spec_from_file_location(module_info.name, module_file)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "Check") and issubclass(module.Check, BaseCheck):
            checks[module_info.name] = module.Check

    return checks


async def run_check(check_id: str, check_cls: type[BaseCheck], ctx: Context) -> bool:
    """Run a single check and return whether it succeeded."""
    check = check_cls(ctx)
    try:
        value = await check.run()
        ctx.data[check_id] = value
        return True
    except Exception as e:
        logger.error(f"{check_id}: {e}")
        return False


async def run_checks(checks: dict[str, type[BaseCheck]], ctx: Context):
    """Run all checks respecting dependencies.

    Checks are run in waves. Each wave runs checks whose dependencies have
    all completed. If a check fails, all checks that depend on it (directly
    or transitively) are skipped.
    """
    completed: set[str] = set()
    failed: set[str] = set()
    pending = dict(checks)

    while pending:
        # Skip checks that depend on a failed check (loop for transitive deps)
        while True:
            skipped = {
                check_id
                for check_id, check_cls in pending.items()
                if any(dep in failed for dep in check_cls.depends_on)
            }
            if not skipped:
                break
            for check_id in skipped:
                logger.warning(f"{check_id}: skipped (dependency failed)")
                failed.add(check_id)
                del pending[check_id]

        if not pending:
            break

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
            run_check(check_id, check_cls, ctx) for check_id, check_cls in ready.items()
        ]
        results = await asyncio.gather(*tasks)

        # Record results and mark as completed or failed
        for check_id, succeeded in zip(ready.keys(), results):
            if succeeded:
                completed.add(check_id)
            else:
                failed.add(check_id)
            del pending[check_id]
