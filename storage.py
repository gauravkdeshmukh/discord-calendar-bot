"""Per-user token storage backed by a local JSON file."""

import json
import os

TOKENS_FILE = "tokens.json"


def _load() -> dict:
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE) as f:
            return json.load(f)
    return {}


def _save(data: dict):
    with open(TOKENS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_token(discord_user_id: str, token_data: dict):
    data = _load()
    data[discord_user_id] = token_data
    _save(data)


def get_token(discord_user_id: str) -> dict | None:
    return _load().get(discord_user_id)


def delete_token(discord_user_id: str):
    data = _load()
    data.pop(discord_user_id, None)
    _save(data)


def has_token(discord_user_id: str) -> bool:
    return discord_user_id in _load()
