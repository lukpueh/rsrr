import asyncio
import json
from typing import Any

from ..base import BaseCheck


class Check(BaseCheck):
    name = "Zizmor"
    comment = "Runs zizmor GitHub Actions security audit on the cloned repo"
    depends_on = ["gh_repo_clone"]

    async def run(self) -> list[dict[str, Any]]:
        repo_path = self.ctx.data["gh_repo_clone"]

        env: dict[str, str] = {}
        if self.ctx.gh_token:
            env["GH_TOKEN"] = self.ctx.gh_token

        proc = await asyncio.create_subprocess_exec(
            "zizmor", "--format", "json", repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env if env else None,
        )
        stdout, stderr = await proc.communicate()

        # zizmor exits non-zero when findings exist, so only fail on actual errors
        if proc.returncode not in (0, 1):
            raise RuntimeError(f"zizmor failed: {stderr.decode().strip()}")

        return json.loads(stdout) if stdout.strip() else []
