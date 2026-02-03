import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Context:
    """Context holds CLI configuration and query results."""

    # CLI configuration
    ef_project_id: str | None = None

    # Query results storage
    query_results: dict[str, Any] = field(default_factory=dict)

    @property
    def ef_project_id_normalized(self) -> str | None:
        """Return project ID with dots replaced by underscores (API format)."""
        if self.ef_project_id is None:
            return None
        return self.ef_project_id.replace(".", "_")

    def save(self, path: Path) -> None:
        """Save context to JSON file."""
        data = {
            "ef_project_id": self.ef_project_id,
            "query_results": self.query_results,
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "Context":
        """Load context from JSON file."""
        data = json.loads(path.read_text())
        return cls(
            ef_project_id=data.get("ef_project_id"),
            query_results=data.get("query_results", {}),
        )
