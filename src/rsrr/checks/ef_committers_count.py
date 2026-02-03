from .base import BaseCheck


class Check(BaseCheck):
    name = "EF Project Committer Count"
    comment = "Gets the number of committers for the Eclipse Foundation project"

    async def run(self) -> int:
        project_data = self.context.query_results.get("ef_project")
        if not project_data:
            raise ValueError("Run 'rsrr query ef_project' first")
        return len(project_data[0]["committers"])
