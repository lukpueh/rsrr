import httpx

from .base import BaseQuery


class Query(BaseQuery):
    name = "GitHub Default Security Policy"
    comment = "Checks if the organization has a default SECURITY.md in .github repo"
    depends_on = ["ef_project"]
    result_key = "gh_security_policy_file"

    async def run(self) -> bool:
        gh_org = self.context.query_results["ef_project"]["github"]["org"]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{gh_org}/.github/contents/SECURITY.md",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            return response.json()
