import httpx

from .base import BaseCheck


class Check(BaseCheck):
    name = "GitHub Organization"
    comment = "Checks if the GitHub organization is indeed an organization"

    async def run(self) -> str:
        if not self.config.gh_org:
            raise ValueError("GitHub org name required (--gh-org)")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/users/{self.config.gh_org}",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
        response.raise_for_status()
        data = response.json()
        if data["type"] == "Organization":
            return True
        return False
