"""Tests for the OAuth callback web endpoint."""

import os
from unittest.mock import patch

import pytest
from aiohttp.test_utils import TestClient, TestServer
from aiohttp import web

os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("CALLBACK_URL", "http://localhost:8080")
os.environ.setdefault("DISCORD_TOKEN", "test-discord-token")

import storage


# Import the callback handler directly to avoid starting the full bot
async def oauth_callback(request: web.Request) -> web.Response:
    """Inline copy of main.oauth_callback for isolated testing."""
    from main import oauth_callback as _cb
    return await _cb(request)


@pytest.fixture
def app():
    application = web.Application()
    application.router.add_get("/oauth/callback", oauth_callback)
    return application


@pytest.fixture
async def client(aiohttp_client, app, tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "TOKENS_FILE", str(tmp_path / "tokens.json"))
    return await aiohttp_client(app)


# --- success path ---

@pytest.mark.asyncio
async def test_callback_stores_token_on_success(client):
    fake_token = {"token": "t", "refresh_token": "r", "token_uri": "u",
                  "client_id": "c", "client_secret": "s", "scopes": []}

    with patch("main.exchange_code", return_value=fake_token):
        resp = await client.get("/oauth/callback?code=auth_code&state=discord_123")

    assert resp.status == 200
    assert storage.has_token("discord_123")


@pytest.mark.asyncio
async def test_callback_response_contains_success_message(client):
    fake_token = {"token": "t", "refresh_token": "r", "token_uri": "u",
                  "client_id": "c", "client_secret": "s", "scopes": []}

    with patch("main.exchange_code", return_value=fake_token):
        resp = await client.get("/oauth/callback?code=auth_code&state=discord_456")

    text = await resp.text()
    assert "Connected" in text


# --- missing parameters ---

@pytest.mark.asyncio
async def test_callback_missing_code_returns_400(client):
    resp = await client.get("/oauth/callback?state=discord_123")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_callback_missing_state_returns_400(client):
    resp = await client.get("/oauth/callback?code=some_code")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_callback_missing_both_returns_400(client):
    resp = await client.get("/oauth/callback")
    assert resp.status == 400


# --- exchange failure ---

@pytest.mark.asyncio
async def test_callback_exchange_failure_returns_500(client):
    with patch("main.exchange_code", side_effect=Exception("Google error")):
        resp = await client.get("/oauth/callback?code=bad_code&state=discord_789")

    assert resp.status == 500
    text = await resp.text()
    # Must not leak internal error details
    assert "Google error" not in text


@pytest.mark.asyncio
async def test_callback_does_not_store_token_on_failure(client):
    with patch("main.exchange_code", side_effect=Exception("fail")):
        await client.get("/oauth/callback?code=bad&state=discord_999")

    assert not storage.has_token("discord_999")
