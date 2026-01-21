import json
from abc import ABC, abstractmethod

from .checks.base import CheckResult


class Formatter(ABC):
    """Base class for output formatters."""

    @abstractmethod
    def format(self, results: list[tuple[str, CheckResult]]) -> str:
        """Format check results for output."""
        ...


class PlainFormatter(Formatter):
    """Plain text output formatter."""

    def format(self, results: list[tuple[str, CheckResult]]) -> str:
        lines = []
        for check_id, result in results:
            status = "✓" if result.success else "✗"
            value_str = result.error if result.error else repr(result.value)
            lines.append(f"{status} {result.name} [{check_id}]: {value_str}")
            lines.append(f"  # {result.comment}")
        return "\n".join(lines)


class JsonFormatter(Formatter):
    """JSON output formatter."""

    def format(self, results: list[tuple[str, CheckResult]]) -> str:
        data = []
        for check_id, result in results:
            data.append({
                "id": check_id,
                "name": result.name,
                "comment": result.comment,
                "value": result.value,
                "success": result.success,
                "error": result.error,
            })
        return json.dumps(data, indent=2)


FORMATTERS: dict[str, type[Formatter]] = {
    "plain": PlainFormatter,
    "json": JsonFormatter,
}
