"""Tests for Discord slash command logic (no live Discord connection required)."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("CALLBACK_URL", "http://localhost:8080")
os.environ.setdefault("DISCORD_TOKEN", "test-discord-token")

import storage
import bot
from bot import connect, disconnect, create_event_command


@pytest.fixture(autouse=True)
def tmp_tokens(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "TOKENS_FILE", str(tmp_path / "tokens.json"))


def _mock_interaction(user_id: str = "12345", username: str = "TestUser") -> MagicMock:
    interaction = MagicMock()
    interaction.user.id = int(user_id)
    interaction.user.display_name = username
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


# --- /connect ---

@pytest.mark.asyncio
async def test_connect_sends_ephemeral_auth_url():
    interaction = _mock_interaction("111")
    with patch("bot.get_auth_url", return_value="https://auth.google.com/fake"):
        await connect.callback(interaction)

    interaction.response.send_message.assert_called_once()
    args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True
    assert "https://auth.google.com/fake" in args[0]


@pytest.mark.asyncio
async def test_connect_uses_correct_discord_user_id_as_state():
    interaction = _mock_interaction("999")
    captured_state = {}

    def fake_auth_url(state):
        captured_state["state"] = state
        return "https://auth.url"

    with patch("bot.get_auth_url", side_effect=fake_auth_url):
        await connect.callback(interaction)

    assert captured_state["state"] == "999"


# --- /disconnect ---

@pytest.mark.asyncio
async def test_disconnect_removes_token():
    storage.save_token("222", {"token": "t"})
    interaction = _mock_interaction("222")
    await disconnect.callback(interaction)
    assert not storage.has_token("222")


@pytest.mark.asyncio
async def test_disconnect_sends_ephemeral_confirmation():
    interaction = _mock_interaction("333")
    await disconnect.callback(interaction)
    _, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True


# --- /create_event ---

@pytest.mark.asyncio
async def test_create_event_prompts_connect_when_no_token():
    interaction = _mock_interaction("444")
    await create_event_command.callback(interaction, "Meeting", "2025-06-15", "10:00", 60, "")
    interaction.response.send_message.assert_called_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "/connect" in args[0]
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_create_event_rejects_invalid_duration():
    interaction = _mock_interaction("555")
    storage.save_token("555", {"token": "t"})
    await create_event_command.callback(interaction, "Test", "2025-06-15", "10:00", 0, "")
    interaction.response.send_message.assert_called_once()
    _, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_create_event_success_sends_embed():
    interaction = _mock_interaction("666")
    storage.save_token("666", {"token": "t"})

    with patch("bot.create_event", return_value={"id": "ev1", "link": "https://cal.link"}):
        await create_event_command.callback(interaction, "Standup", "2025-06-15", "09:00", 30, "Sync")

    interaction.response.defer.assert_called_once()
    interaction.followup.send.assert_called_once()
    _, kwargs = interaction.followup.send.call_args
    embed = kwargs.get("embed")
    assert embed is not None
    assert embed.title == "Event Created"


@pytest.mark.asyncio
async def test_create_event_invalid_date_sends_ephemeral_error():
    interaction = _mock_interaction("777")
    storage.save_token("777", {"token": "t"})

    with patch("bot.create_event", side_effect=ValueError("Invalid date or time format.")):
        await create_event_command.callback(interaction, "Test", "bad-date", "10:00", 60, "")

    _, kwargs = interaction.followup.send.call_args
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_create_event_unexpected_error_is_generic():
    """Users must never see raw exception messages (security + UX)."""
    interaction = _mock_interaction("888")
    storage.save_token("888", {"token": "t"})

    with patch("bot.create_event", side_effect=Exception("Internal DB error with secrets")):
        await create_event_command.callback(interaction, "Test", "2025-06-15", "10:00", 60, "")

    args, kwargs = interaction.followup.send.call_args
    assert "Internal DB error" not in args[0]
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_create_event_not_connected_error_prompts_connect():
    interaction = _mock_interaction("999")
    storage.save_token("999", {"token": "t"})

    with patch("bot.create_event", side_effect=PermissionError("not_connected")):
        await create_event_command.callback(interaction, "Test", "2025-06-15", "10:00", 60, "")

    args, kwargs = interaction.followup.send.call_args
    assert "/connect" in args[0]
    assert kwargs.get("ephemeral") is True
