from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from rsrr.base import Context
from rsrr.checks.ef_committers import Check


def _make_context(committers):
    return Context(data={"ef_project": [{"committers": committers}]})


def _mock_client(url_responses):
    """Return a mock AsyncClient that returns responses based on URL."""
    mock_client = AsyncMock()

    async def fake_get(url):
        if url in url_responses:
            resp = MagicMock()
            resp.json.return_value = url_responses[url]
            resp.raise_for_status = MagicMock()
            return resp
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        raise httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

    mock_client.get = fake_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@pytest.mark.asyncio
async def test_fetches_committer_profiles():
    ctx = _make_context([
        {"username": "alice", "url": "https://api.eclipse.org/account/profile/alice"},
        {"username": "bob", "url": "https://api.eclipse.org/account/profile/bob"},
    ])
    mock = _mock_client({
        "https://api.eclipse.org/account/profile/alice": {
            "name": "alice",
            "full_name": "Alice A",
            "github_handle": "alice-gh",
        },
        "https://api.eclipse.org/account/profile/bob": {
            "name": "bob",
            "full_name": "Bob B",
            "github_handle": "bob-gh",
        },
    })

    with patch("rsrr.checks.ef_committers.httpx.AsyncClient", return_value=mock):
        result = await Check(ctx).run()

    assert len(result) == 2
    assert result[0]["name"] == "alice"
    assert result[1]["name"] == "bob"


@pytest.mark.asyncio
async def test_skips_committer_without_url():
    ctx = _make_context([
        {"username": "alice", "url": ""},
        {"username": "bob", "url": "https://api.eclipse.org/account/profile/bob"},
    ])
    mock = _mock_client({
        "https://api.eclipse.org/account/profile/bob": {"name": "bob"},
    })

    with patch("rsrr.checks.ef_committers.httpx.AsyncClient", return_value=mock):
        result = await Check(ctx).run()

    assert len(result) == 1
    assert result[0]["name"] == "bob"


@pytest.mark.asyncio
async def test_api_error_skips_committer():
    ctx = _make_context([
        {"username": "alice", "url": "https://api.eclipse.org/account/profile/alice"},
        {"username": "bob", "url": "https://api.eclipse.org/account/profile/bob"},
    ])
    mock = _mock_client({
        "https://api.eclipse.org/account/profile/bob": {"name": "bob"},
    })

    with patch("rsrr.checks.ef_committers.httpx.AsyncClient", return_value=mock):
        result = await Check(ctx).run()

    assert len(result) == 1
    assert result[0]["name"] == "bob"


@pytest.mark.asyncio
async def test_no_committers():
    ctx = _make_context([])
    mock = _mock_client({})

    with patch("rsrr.checks.ef_committers.httpx.AsyncClient", return_value=mock):
        result = await Check(ctx).run()

    assert result == []
