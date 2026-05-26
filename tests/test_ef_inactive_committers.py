import logging

import pytest

from rsrr.base import Context
from rsrr.checks.ef_inactive_committers import Check


def _make_context(ef_committers, activity):
    return Context(
        data={
            "ef_committers": ef_committers,
            "gh_repo_commit_activity": activity,
        }
    )


def _ef_committer(first_name, last_name, github_handle=""):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "github_handle": github_handle,
    }


def _activity(committer_logins):
    """Build activity data with given logins."""
    return {
        "https://github.com/org/repo": {
            "commit_count": len(committer_logins),
            "committers": [
                {"name": "", "email": f"{login}@example.com", "login": login}
                for login in committer_logins
            ],
        }
    }


@pytest.mark.asyncio
async def test_active_committer_not_listed():
    ctx = _make_context(
        [_ef_committer("Alice", "A", "alice-gh")],
        _activity(["alice-gh"]),
    )
    result = await Check(ctx).run()
    assert result == []


@pytest.mark.asyncio
async def test_inactive_committer_listed():
    ctx = _make_context(
        [_ef_committer("Bob", "B", "bob-gh")],
        _activity(["alice-gh"]),
    )
    result = await Check(ctx).run()
    assert len(result) == 1
    assert result[0] == {
        "first_name": "Bob",
        "last_name": "B",
        "github_handle": "bob-gh",
        "reason": "no_recent_commits",
    }


@pytest.mark.asyncio
async def test_no_github_handle_warns(caplog):
    ctx = _make_context(
        [_ef_committer("Carol", "C")],
        _activity(["alice-gh"]),
    )
    with caplog.at_level(logging.WARNING):
        result = await Check(ctx).run()

    assert len(result) == 1
    assert result[0]["reason"] == "no_github_handle"
    assert "Carol C" in caplog.text
    assert "no GitHub handle" in caplog.text


@pytest.mark.asyncio
async def test_case_insensitive_match():
    ctx = _make_context(
        [_ef_committer("Alice", "A", "Alice-GH")],
        _activity(["alice-gh"]),
    )
    result = await Check(ctx).run()
    assert result == []


@pytest.mark.asyncio
async def test_mixed_active_and_inactive():
    ctx = _make_context(
        [
            _ef_committer("Alice", "A", "alice-gh"),
            _ef_committer("Bob", "B", "bob-gh"),
            _ef_committer("Carol", "C"),
        ],
        _activity(["alice-gh"]),
    )
    result = await Check(ctx).run()
    assert len(result) == 2
    names = [(r["first_name"], r["reason"]) for r in result]
    assert ("Bob", "no_recent_commits") in names
    assert ("Carol", "no_github_handle") in names


@pytest.mark.asyncio
async def test_no_committers():
    ctx = _make_context([], _activity(["alice-gh"]))
    result = await Check(ctx).run()
    assert result == []


@pytest.mark.asyncio
async def test_no_activity():
    ctx = _make_context(
        [_ef_committer("Alice", "A", "alice-gh")],
        {},
    )
    result = await Check(ctx).run()
    assert len(result) == 1
    assert result[0]["reason"] == "no_recent_commits"
