from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..context import Context


@dataclass
class QueryResult:
    """Result of a query execution."""

    name: str
    comment: str
    data: Any
    success: bool
    error: str | None = None


class BaseQuery(ABC):
    """Base class for all queries."""

    name: str
    comment: str
    result_key: str  # Key used to store result in context

    def __init__(self, context: "Context") -> None:
        self.context = context

    @abstractmethod
    async def run(self) -> Any:
        """Execute query and return data to be stored in context."""
        ...
