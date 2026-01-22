from datetime import datetime, timedelta

import httpx

from .base import BaseCheck


class Check(BaseCheck):
    name = "GitHub Distinct Committers Past Year"
    comment = "Gets the number of distinct committers in the organization in the past year"

    async def run(self) -> int:
        if not self.config.gh_org:
            raise ValueError("GitHub org name required (--gh-org)")

        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        committers: set[str] = set()
        page = 1
        per_page = 100

        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    "https://api.github.com/search/commits",
                    params={
                        "q": f"org:{self.config.gh_org} committer-date:>{one_year_ago}",
                        "per_page": per_page,
                        "page": page,
                    },
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    committer = item.get("committer")
                    if committer and committer.get("login"):
                        committers.add(committer["login"])

                # GitHub search API returns max 1000 results
                if page * per_page >= min(data.get("total_count", 0), 1000):
                    break

                page += 1

        return len(committers)
