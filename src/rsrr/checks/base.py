from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Union

ScalarResult = Union[int, float, bool, str]

Category = Literal[
    "Blueprints",
    "CI/CD: Releases",
    "CI/CD: Tools",
    "Communication",
    "Community Health Files",
    "Contributions",
    "Otterdog",
    "SBOM",
    "Security Posture",
    "Security Team",
    "Setup",
    "Static Analysis",
    "Survey",
    "Vulnerability Management",
    "Vulnerability Reporting",
]


@dataclass
class Config:
    gh_org: str | None = None
    gh_repo: str | None = None

    @property
    def gh_org_url(self) -> str | None:
        if not self.gh_org:
            raise ValueError("GitHub org name required")
        return f"https://github.com/{self.gh_org}"

    @property
    def gh_repo_url(self) -> str | None:
        if not all(self.gh_org, self.gh_repo):
            raise ValueError("GitHub org and repo name required")
        return f"https://github.com/{self.gh_org}/{self.gh_repo}"


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
    - category: Category - One of the predefined categories
    - run() - Async method that returns a scalar value

    The config is available via self.config.
    """

    name: str
    comment: str
    category: Category

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    async def run(self) -> ScalarResult:
        """Execute the check and return a scalar value (int, float, bool, or str)."""
        ...
