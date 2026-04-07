"""Tests for google_calendar helpers."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("CALLBACK_URL", "http://localhost:8080")

import google_calendar
import storage


@pytest.fixture(autouse=True)
def tmp_tokens(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "TOKENS_FILE", str(tmp_path / "tokens.json"))


# --- get_auth_url ---

def test_get_auth_url_contains_state():
    url = google_calendar.get_auth_url(state="discord_user_99")
    assert "discord_user_99" in url
    assert "accounts.google.com" in url


def test_get_auth_url_contains_redirect():
    url = google_calendar.get_auth_url(state="x")
    assert "localhost%3A8080" in url or "localhost:8080" in url


# --- create_event input validation ---

def test_create_event_invalid_date_raises():
    storage.save_token("u1", _fake_token())
    with pytest.raises(ValueError, match="Invalid date or time"):
        google_calendar.create_event("u1", "Test", "not-a-date", "10:00", 30, "")


def test_create_event_invalid_time_raises():
    storage.save_token("u1", _fake_token())
    with pytest.raises(ValueError, match="Invalid date or time"):
        google_calendar.create_event("u1", "Test", "2025-06-15", "25:99", 30, "")


def test_create_event_no_token_raises():
    with pytest.raises(PermissionError):
        google_calendar.create_event("no_user", "Test", "2025-06-15", "10:00", 30, "")


# --- create_event success ---

def test_create_event_calls_api_correctly():
    storage.save_token("u2", _fake_token())

    mock_service = MagicMock()
    mock_service.events().insert().execute.return_value = {
        "id": "evt123",
        "htmlLink": "https://calendar.google.com/event?id=evt123",
    }

    with patch("google_calendar._get_user_service", return_value=mock_service):
        result = google_calendar.create_event("u2", "Standup", "2025-06-15", "09:00", 30, "Daily sync")

    assert result["id"] == "evt123"
    assert "calendar.google.com" in result["link"]

    insert_call = mock_service.events().insert.call_args
    body = insert_call.kwargs["body"]
    assert body["summary"] == "Standup"
    assert body["description"] == "Daily sync"
    assert "2025-06-15T09:00:00" in body["start"]["dateTime"]
    assert "2025-06-15T09:30:00" in body["end"]["dateTime"]


def test_create_event_duration_applied():
    storage.save_token("u3", _fake_token())

    mock_service = MagicMock()
    mock_service.events().insert().execute.return_value = {"id": "x", "htmlLink": ""}

    with patch("google_calendar._get_user_service", return_value=mock_service):
        google_calendar.create_event("u3", "Long meeting", "2025-06-15", "10:00", 90, "")

    body = mock_service.events().insert.call_args.kwargs["body"]
    assert "11:30:00" in body["end"]["dateTime"]


# --- helpers ---

def _fake_token() -> dict:
    return {
        "token": "fake-token",
        "refresh_token": "fake-refresh",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "scopes": ["https://www.googleapis.com/auth/calendar.events"],
    }
