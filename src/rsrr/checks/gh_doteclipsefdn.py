import httpx

from .base import BaseCheck


class Check(BaseCheck):
    name = "GitHub .eclipsefdn Repo"
    comment = "Checks if the organization has a .eclipsefdn repository"

    async def run(self) -> bool:
        if not self.config.gh_org:
            raise ValueError("GitHub org name required (--gh-org)")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{self.config.gh_org}/.eclipsefdn",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            return response.status_code == 200
