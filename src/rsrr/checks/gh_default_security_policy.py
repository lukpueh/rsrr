import httpx

from .base import BaseCheck


class Check(BaseCheck):
    name = "GitHub Default Security Policy"
    comment = "Checks if the organization has a default SECURITY.md in .github repo"

    async def run(self) -> bool:
        if not self.config.gh_org:
            raise ValueError("GitHub org name required (--gh-org)")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{self.config.gh_org}/.github/contents/SECURITY.md",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            return response.status_code == 200
