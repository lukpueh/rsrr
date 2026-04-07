from ..base import BaseCheck


class Check(BaseCheck):
    name = "GitHub Default Security Policy"
    comment = "Checks if the organization has a default SECURITY.md in .github repo"
    depends_on = ["ef_project"]

    async def run(self) -> bool:
        gh_org = self.ctx.data["ef_project"][0]["github"]["org"]

        response = await self.ctx.github_get(
            f"https://api.github.com/repos/{gh_org}/.github/contents/SECURITY.md",
        )
        return response.json()
