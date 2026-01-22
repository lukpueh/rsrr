import httpx

from .base import BaseCheck


class Check(BaseCheck):
    name = "EF Project Committer Count"
    comment = "Gets the number of committers for the Eclipse Foundation project"

    async def run(self) -> int:
        if not self.config.ef_project_id_normalized:
            raise ValueError("EF project ID required (--ef-project-id)")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://projects.eclipse.org/api/projects/{self.config.ef_project_id_normalized}",
            )
        response.raise_for_status()
        return len(response.json()[0]["committers"])
