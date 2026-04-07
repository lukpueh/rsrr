from unittest.mock import MagicMock

import httpx
import pytest

from rsrr.base import Context
from rsrr.checks.gh_repo_commit_activity import Check


def _make_context(repos):
    return Context(data={"gh_repos": repos})


def _commit(name, email, login=""):
    return {
        "commit": {"author": {"name": name, "email": email}},
        "author": {"login": login} if login else None,
    }


def _mock_github_get(repo_pages):
    """Return a github_get mock.

    repo_pages maps 'owner/repo' to a list of pages, where each page is a
    list of commit objects.
    """
    call_counts = {}

    async def fake_get(url):
        for key, pages in repo_pages.items():
            if f"/repos/{key}/commits" in url:
                idx = call_counts.get(key, 0)
                call_counts[key] = idx + 1
                page_data = pages[idx] if idx < len(pages) else []
                resp = MagicMock()
                resp.json.return_value = page_data
                return resp
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        raise httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

    return fake_get


@pytest.mark.asyncio
async def test_single_repo():
    ctx = _make_context(["https://github.com/org/repo-a"])
    ctx.github_get = _mock_github_get({
        "org/repo-a": [
            [
                _commit("Alice", "alice@example.com", "alice-gh"),
                _commit("Bob", "bob@example.com", "bob-gh"),
            ],
            [],
        ],
    })
    result = await Check(ctx).run()
    assert result["https://github.com/org/repo-a"]["commit_count"] == 2
    committers = result["https://github.com/org/repo-a"]["committers"]
    assert {"name": "Alice", "email": "alice@example.com", "login": "alice-gh"} in committers
    assert {"name": "Bob", "email": "bob@example.com", "login": "bob-gh"} in committers


@pytest.mark.asyncio
async def test_commit_without_github_author():
    """When commit.author is null (no linked GitHub account), login is empty."""
    ctx = _make_context(["https://github.com/org/repo-a"])
    ctx.github_get = _mock_github_get({
        "org/repo-a": [
            [_commit("Alice", "alice@example.com")],
            [],
        ],
    })
    result = await Check(ctx).run()
    committers = result["https://github.com/org/repo-a"]["committers"]
    assert committers == [{"name": "Alice", "email": "alice@example.com", "login": ""}]


@pytest.mark.asyncio
async def test_deduplicates_committers_by_email():
    ctx = _make_context(["https://github.com/org/repo-a"])
    ctx.github_get = _mock_github_get({
        "org/repo-a": [
            [
                _commit("Alice", "alice@example.com", "alice-gh"),
                _commit("Alice A.", "alice@example.com", "alice-gh"),
            ],
            [],
        ],
    })
    result = await Check(ctx).run()
    assert result["https://github.com/org/repo-a"]["commit_count"] == 2
    committers = result["https://github.com/org/repo-a"]["committers"]
    assert len(committers) == 1
    assert committers[0]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_multiple_pages():
    page1 = [_commit("Alice", "alice@example.com", "alice-gh")] * 100
    page2 = [_commit("Bob", "bob@example.com", "bob-gh")] * 50
    ctx = _make_context(["https://github.com/org/repo-a"])
    ctx.github_get = _mock_github_get({
        "org/repo-a": [page1, page2, []],
    })
    result = await Check(ctx).run()
    assert result["https://github.com/org/repo-a"]["commit_count"] == 150
    committers = result["https://github.com/org/repo-a"]["committers"]
    emails = {c["email"] for c in committers}
    assert emails == {"alice@example.com", "bob@example.com"}


@pytest.mark.asyncio
async def test_api_error():
    ctx = _make_context(["https://github.com/org/missing"])
    ctx.github_get = _mock_github_get({})
    result = await Check(ctx).run()
    assert result["https://github.com/org/missing"] == {
        "commit_count": -1,
        "committers": [],
    }


@pytest.mark.asyncio
async def test_no_repos():
    ctx = _make_context([])
    result = await Check(ctx).run()
    assert result == {}


@pytest.mark.asyncio
async def test_no_commits():
    ctx = _make_context(["https://github.com/org/repo-a"])
    ctx.github_get = _mock_github_get({"org/repo-a": [[]]})
    result = await Check(ctx).run()
    assert result["https://github.com/org/repo-a"] == {
        "commit_count": 0,
        "committers": [],
    }
