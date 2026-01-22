from datetime import datetime, timedelta

import httpx

from .base import BaseCheck


class Check(BaseCheck):
    name = "GitHub Commits Past Year"
    comment = "Gets the total number of commits in the organization in the past year"

    async def run(self) -> int:
        if not self.config.gh_org:
            raise ValueError("GitHub org name required (--gh-org)")

        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/search/commits",
                params={"q": f"org:{self.config.gh_org} committer-date:>{one_year_ago}"},
                headers={
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            response.raise_for_status()
            return response.json()["total_count"]
