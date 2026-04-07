from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rsrr.base import Context
from rsrr.checks.gh_repos import Check


def _make_context(github_repos=None, org="", ignored_repos=None, gh_token=None):
    """Create a Context with ef_project data pre-populated."""
    project = {
        "github_repos": github_repos or [],
        "github": {
            "org": org,
            "ignored_repos": ignored_repos or [],
        },
    }
    return Context(
        gh_token=gh_token,
        data={"ef_project": [project]},
    )


def _mock_github_get(pages):
    """Return a patched github_get that returns pages of repos in sequence."""
    responses = []
    for page in pages:
        mock_resp = MagicMock()
        mock_resp.json.return_value = page
        responses.append(mock_resp)
    return AsyncMock(side_effect=responses)


@pytest.mark.asyncio
async def test_listed_repos_only():
    """Repos from github_repos are included."""
    ctx = _make_context(
        github_repos=[
            {"url": "https://github.com/org/repo-a"},
            {"url": "https://github.com/org/repo-b"},
        ]
    )
    check = Check(ctx)
    result = await check.run()
    assert result == [
        "https://github.com/org/repo-a",
        "https://github.com/org/repo-b",
    ]


@pytest.mark.asyncio
async def test_org_repos_queried():
    """When org is set, repos are fetched from the GitHub API."""
    ctx = _make_context(org="myorg")
    ctx.github_get = _mock_github_get(
        [
            [
                {"html_url": "https://github.com/myorg/repo-x"},
                {"html_url": "https://github.com/myorg/repo-y"},
            ],
            [],  # empty second page stops pagination
        ]
    )
    check = Check(ctx)
    result = await check.run()
    assert "https://github.com/myorg/repo-x" in result
    assert "https://github.com/myorg/repo-y" in result


@pytest.mark.asyncio
async def test_org_repos_merged_with_listed():
    """Org repos and listed repos are merged without duplicates."""
    ctx = _make_context(
        github_repos=[{"url": "https://github.com/myorg/repo-a"}],
        org="myorg",
    )
    ctx.github_get = _mock_github_get(
        [
            [
                {"html_url": "https://github.com/myorg/repo-a"},
                {"html_url": "https://github.com/myorg/repo-b"},
            ],
            [],
        ]
    )
    check = Check(ctx)
    result = await check.run()
    assert result == [
        "https://github.com/myorg/repo-a",
        "https://github.com/myorg/repo-b",
    ]


@pytest.mark.asyncio
async def test_ignored_repos_excluded():
    """Repos in ignored_repos are filtered out."""
    ctx = _make_context(
        github_repos=[
            {"url": "https://github.com/org/keep"},
            {"url": "https://github.com/org/drop"},
        ],
        ignored_repos=["drop"],
    )
    check = Check(ctx)
    result = await check.run()
    assert result == ["https://github.com/org/keep"]


@pytest.mark.asyncio
async def test_ignored_repos_apply_to_org_repos():
    """Ignored repos also filter org-fetched repos."""
    ctx = _make_context(org="myorg", ignored_repos=["secret"])
    ctx.github_get = _mock_github_get(
        [
            [
                {"html_url": "https://github.com/myorg/public"},
                {"html_url": "https://github.com/myorg/secret"},
            ],
            [],
        ]
    )
    check = Check(ctx)
    result = await check.run()
    assert result == ["https://github.com/myorg/public"]


@pytest.mark.asyncio
async def test_empty_org_skips_api_call():
    """When org is empty, no GitHub API call is made."""
    ctx = _make_context(
        github_repos=[{"url": "https://github.com/org/repo"}],
        org="",
    )
    ctx.github_get = AsyncMock()
    check = Check(ctx)
    result = await check.run()
    assert result == ["https://github.com/org/repo"]
    ctx.github_get.assert_not_called()


@pytest.mark.asyncio
async def test_no_repos_returns_empty():
    """No repos listed and no org returns an empty list."""
    ctx = _make_context()
    check = Check(ctx)
    result = await check.run()
    assert result == []
