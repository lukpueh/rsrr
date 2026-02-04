from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Context:
    ef_project_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def ef_project_id_normalized(self) -> str | None:
        if self.ef_project_id is None:
            return None
        return self.ef_project_id.replace(".", "_")


class BaseCheck(ABC):
    """Base class for all checks."""

    name: str
    comment: str
    depends_on: list[str] = []

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

    @abstractmethod
    async def run(self) -> Any: ...
