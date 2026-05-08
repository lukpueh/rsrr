from typing import Any

from ..base import BaseCheck


class Check(BaseCheck):
    name = "GitHub Security Advisories"
    comment = "Fetches all security advisories for a GitHub repo"

    async def run(self) -> list[dict[str, Any]]:
        if not self.ctx.gh_repo:
            raise ValueError("--gh-repo is required for this check")

        owner, repo = self.ctx.gh_repo.split("/", 1)
        advisories: list[dict[str, Any]] = []
        url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/security-advisories?per_page=100"
        )

        while url:
            response = await self.ctx.github_get(url)
            advisories.extend(response.json())
            url = response.links.get("next", {}).get("url")

        return advisories
