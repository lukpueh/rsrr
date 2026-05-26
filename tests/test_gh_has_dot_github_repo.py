from unittest.mock import MagicMock

import httpx
import pytest

from rsrr.base import Context
from rsrr.checks.gh_has_dot_github_repo import Check


def _make_context(repos):
    return Context(data={"gh_repos": repos})


def _mock_github_get(found_orgs):
    """Return a github_get mock that succeeds for found_orgs, 404s otherwise."""

    async def fake_get(url):
        for org in found_orgs:
            if f"/repos/{org}/.github" in url:
                resp = MagicMock()
                resp.raise_for_status = MagicMock()
                return resp
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        raise httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

    return fake_get


@pytest.mark.asyncio
async def test_org_has_dot_github():
    ctx = _make_context(["https://github.com/myorg/repo-a"])
    ctx.github_get = _mock_github_get(found_orgs=["myorg"])
    check = Check(ctx)
    result = await check.run()
    assert result == {"myorg": True}


@pytest.mark.asyncio
async def test_org_missing_dot_github():
    ctx = _make_context(["https://github.com/myorg/repo-a"])
    ctx.github_get = _mock_github_get(found_orgs=[])
    check = Check(ctx)
    result = await check.run()
    assert result == {"myorg": False}


@pytest.mark.asyncio
async def test_multiple_orgs():
    ctx = _make_context(
        [
            "https://github.com/org-a/repo1",
            "https://github.com/org-b/repo2",
            "https://github.com/org-a/repo3",
        ]
    )
    ctx.github_get = _mock_github_get(found_orgs=["org-a"])
    check = Check(ctx)
    result = await check.run()
    assert result == {"org-a": True, "org-b": False}


@pytest.mark.asyncio
async def test_no_repos():
    ctx = _make_context([])
    check = Check(ctx)
    result = await check.run()
    assert result == {}
