import asyncio
import importlib
import pkgutil
from pathlib import Path

from .checks import BaseCheck, CheckResult, Config


def discover_checks(package_path: Path) -> dict[str, type[BaseCheck]]:
    """Discover all check classes in the checks package.

    Returns a dict mapping check IDs (module names) to check classes.
    """
    checks: dict[str, type[BaseCheck]] = {}

    for module_info in pkgutil.iter_modules([str(package_path)]):
        if module_info.name in ("base", "__init__"):
            continue

        module = importlib.import_module(
            f".checks.{module_info.name}", package="rsrr"
        )

        if hasattr(module, "Check") and issubclass(module.Check, BaseCheck):
            checks[module_info.name] = module.Check

    return checks


async def run_check(
    check_id: str, check_cls: type[BaseCheck], config: Config
) -> CheckResult:
    """Run a single check and return the result."""
    check = check_cls(config)
    try:
        value = await check.run()
        return CheckResult(
            name=check.name,
            comment=check.comment,
            value=value,
            success=True,
        )
    except Exception as e:
        return CheckResult(
            name=check.name,
            comment=check.comment,
            value=None,
            success=False,
            error=str(e),
        )


async def run_checks(
    checks: dict[str, type[BaseCheck]], config: Config
) -> list[tuple[str, CheckResult]]:
    """Run all checks in parallel and return results."""
    tasks = [
        run_check(check_id, check_cls, config) for check_id, check_cls in checks.items()
    ]
    results = await asyncio.gather(*tasks)
    return list(zip(checks.keys(), results))
