from abc import ABC, abstractmethod
from dataclasses import dataclass

from .checks.base import CheckResult


@dataclass
class FormatterConfig:
    verbose: bool = False


class Formatter(ABC):
    """Base class for output formatters."""

    def __init__(self, config: FormatterConfig) -> None:
        self.config = config

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
            if self.config.verbose:
                lines.append(f"  # {result.comment}")
        return "\n".join(lines)
