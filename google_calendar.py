"""Google Calendar API — per-user OAuth2."""

import os
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from storage import get_token, save_token

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

_CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}


def _redirect_uri() -> str:
    base = os.environ.get("CALLBACK_URL", "http://localhost:8080").rstrip("/")
    return f"{base}/oauth/callback"


def get_auth_url(state: str) -> str:
    """Return a Google OAuth2 authorization URL for the given state (Discord user ID)."""
    flow = Flow.from_client_config(_CLIENT_CONFIG, scopes=SCOPES, redirect_uri=_redirect_uri())
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="consent",
    )
    return url


def exchange_code(code: str) -> dict:
    """Exchange an authorization code for tokens and return them as a dict."""
    flow = Flow.from_client_config(_CLIENT_CONFIG, scopes=SCOPES, redirect_uri=_redirect_uri())
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or SCOPES),
    }


def _get_user_service(discord_user_id: str):
    """Build and return a Calendar service using the stored token for a Discord user."""
    token_data = get_token(discord_user_id)
    if not token_data:
        raise PermissionError("not_connected")

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(discord_user_id, {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or SCOPES),
        })

    return build("calendar", "v3", credentials=creds)


def create_event(
    discord_user_id: str,
    title: str,
    date: str,
    time: str,
    duration_minutes: int,
    description: str,
) -> dict:
    """Create a Google Calendar event on the user's primary calendar."""
    try:
        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("Invalid date or time format. Use YYYY-MM-DD and HH:MM.")

    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event_body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
    }

    service = _get_user_service(discord_user_id)
    created = service.events().insert(calendarId="primary", body=event_body).execute()

    return {
        "id": created["id"],
        "link": created.get("htmlLink", ""),
    }
