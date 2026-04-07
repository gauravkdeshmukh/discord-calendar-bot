"""Tests for per-user token storage."""

import json
import os
import pytest

import storage


@pytest.fixture(autouse=True)
def tmp_tokens(tmp_path, monkeypatch):
    """Redirect TOKENS_FILE to a temp file for every test."""
    tokens_path = tmp_path / "tokens.json"
    monkeypatch.setattr(storage, "TOKENS_FILE", str(tokens_path))
    yield tokens_path


def test_save_and_get_token():
    storage.save_token("123", {"token": "abc", "refresh_token": "xyz"})
    result = storage.get_token("123")
    assert result == {"token": "abc", "refresh_token": "xyz"}


def test_get_token_missing_returns_none():
    assert storage.get_token("nonexistent") is None


def test_has_token_true():
    storage.save_token("456", {"token": "t"})
    assert storage.has_token("456") is True


def test_has_token_false():
    assert storage.has_token("456") is False


def test_delete_token():
    storage.save_token("789", {"token": "t"})
    storage.delete_token("789")
    assert storage.has_token("789") is False


def test_delete_nonexistent_token_is_safe():
    storage.delete_token("does_not_exist")  # must not raise


def test_save_overwrites_existing():
    storage.save_token("111", {"token": "old"})
    storage.save_token("111", {"token": "new"})
    assert storage.get_token("111")["token"] == "new"


def test_multiple_users_isolated():
    storage.save_token("u1", {"token": "t1"})
    storage.save_token("u2", {"token": "t2"})
    assert storage.get_token("u1")["token"] == "t1"
    assert storage.get_token("u2")["token"] == "t2"
