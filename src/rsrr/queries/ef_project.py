import httpx

from .base import BaseQuery


class Query(BaseQuery):
    """Fetches Eclipse Foundation project data from the API."""

    name = "EF Project Data"
    comment = "Fetches Eclipse Foundation project data"
    result_key = "ef_project"

    async def run(self) -> list[dict]:
        if not self.context.ef_project_id_normalized:
            raise ValueError("EF project ID required (--ef-project-id)")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://projects.eclipse.org/api/projects/{self.context.ef_project_id_normalized}",
            )
        response.raise_for_status()
        return response.json()[0]
