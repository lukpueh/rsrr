from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

ScalarResult = Union[int, float, bool, str]


@dataclass
class CheckResult:
    name: str
    comment: str
    value: ScalarResult | None
    success: bool
    error: str | None = None


class BaseCheck(ABC):
    """Base class for all checks.

    To create a new check, subclass this and implement:
    - name: str - Display name for the check
    - comment: str - Description of what the check does
    - run() - Async method that returns a scalar value
    """

    name: str
    comment: str

    @abstractmethod
    async def run(self) -> ScalarResult:
        """Execute the check and return a scalar value (int, float, bool, or str)."""
        ...
