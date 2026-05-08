import asyncio
import json
import os
from typing import Any

from ..base import BaseCheck


class Check(BaseCheck):
    name = "Zizmor"
    comment = "Runs zizmor GitHub Actions security audit on a GitHub repo"

    async def run(self) -> list[dict[str, Any]]:
        if not self.ctx.gh_repo:
            raise ValueError("--gh-repo is required for this check")

        env = os.environ.copy()
        if self.ctx.gh_token:
            env["GH_TOKEN"] = self.ctx.gh_token

        proc = await asyncio.create_subprocess_exec(
            "zizmor", "--format", "json", self.ctx.gh_repo,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()

        # zizmor exits non-zero when findings exist, so only fail on actual errors
        if proc.returncode not in (0, 1):
            raise RuntimeError(f"zizmor failed: {stderr.decode().strip()}")

        return json.loads(stdout) if stdout.strip() else []
