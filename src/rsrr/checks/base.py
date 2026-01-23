from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

ScalarResult = Union[int, float, bool, str]


@dataclass
class Config:
    gh_org: str | None = None
    gh_repo: str | None = None
    ef_project_id: str | None = None

    @property
    def ef_project_id_normalized(self) -> str | None:
        if self.ef_project_id is None:
            return None
        return self.ef_project_id.replace(".", "_")


@dataclass
class CheckResult:
    name: str
    comment: str
    value: ScalarResult | None
    success: bool
    error: str | None = None


class BaseCheck(ABC):
    """Base class for all checks."""

    name: str
    comment: str

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    async def run(self) -> ScalarResult:
        """Execute the check and return a scalar value (int, float, bool, or str)."""
        ...
