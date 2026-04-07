import logging

import httpx

from ..base import BaseCheck

logger = logging.getLogger(__name__)


class Check(BaseCheck):
    name = "EF Committer Profiles"
    comment = "Fetches detailed profile info for each project committer from the EF API"
    depends_on = ["ef_project"]

    async def run(self) -> list[dict]:
        project = self.ctx.data["ef_project"][0]
        committers = project.get("committers", [])

        results = []
        async with httpx.AsyncClient() as client:
            for committer in committers:
                url = committer.get("url", "")
                username = committer.get("username", "")
                if not url:
                    continue

                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    results.append(response.json())
                except httpx.HTTPStatusError as e:
                    logger.error(f"{username}: {e}")

        return results
