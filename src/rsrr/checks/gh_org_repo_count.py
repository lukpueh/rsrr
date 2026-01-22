import httpx

from .base import BaseCheck


class Check(BaseCheck):
    name = "GitHub Organization Repo Count"
    comment = "Gets the number of repositories in the organization"

    async def run(self) -> int:
        if not self.config.gh_org:
            raise ValueError("GitHub org name required (--gh-org)")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/orgs/{self.config.gh_org}",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                },
            )
        response.raise_for_status()
        return response.json()["public_repos"]
