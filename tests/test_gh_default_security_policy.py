from unittest.mock import MagicMock

import httpx
import pytest

from rsrr.base import Context
from rsrr.checks.gh_default_security_policy import Check


def _make_context(repos):
    return Context(data={"gh_repos": repos})


def _mock_github_get(orgs_with_policy):
    """Return a github_get that succeeds for orgs with a SECURITY.md, 404s otherwise."""

    async def fake_get(url):
        for org in orgs_with_policy:
            if f"/repos/{org}/.github/contents/SECURITY.md" in url:
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
async def test_org_has_security_policy():
    ctx = _make_context(["https://github.com/myorg/repo-a"])
    ctx.github_get = _mock_github_get(orgs_with_policy=["myorg"])
    result = await Check(ctx).run()
    assert result == {"myorg": True}


@pytest.mark.asyncio
async def test_org_missing_security_policy():
    ctx = _make_context(["https://github.com/myorg/repo-a"])
    ctx.github_get = _mock_github_get(orgs_with_policy=[])
    result = await Check(ctx).run()
    assert result == {"myorg": False}


@pytest.mark.asyncio
async def test_multiple_orgs():
    ctx = _make_context(
        [
            "https://github.com/org-a/repo1",
            "https://github.com/org-b/repo2",
        ]
    )
    ctx.github_get = _mock_github_get(orgs_with_policy=["org-a"])
    result = await Check(ctx).run()
    assert result == {"org-a": True, "org-b": False}


@pytest.mark.asyncio
async def test_no_repos():
    ctx = _make_context([])
    result = await Check(ctx).run()
    assert result == {}
