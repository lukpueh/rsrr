import asyncio
import random

from .base import BaseCheck


class Check(BaseCheck):
    name = "Local Random"
    comment = "Returns a random number (no network required)"

    async def run(self) -> int:
        await asyncio.sleep(0.1)  # Simulate async work
        return random.randint(1, 100)
