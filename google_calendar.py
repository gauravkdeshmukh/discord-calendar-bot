"""Google Calendar API wrapper with OAuth2 authentication."""

import os
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


def get_calendar_service():
    """Authenticate and return a Google Calendar service object."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    "credentials.json not found. Download it from Google Cloud Console "
                    "(APIs & Services > Credentials > OAuth 2.0 Client ID)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def create_event(
    title: str,
    date: str,
    time: str,
    duration_minutes: int,
    description: str,
    calendar_id: str,
) -> dict:
    """
    Create a Google Calendar event.

    Args:
        title: Event title.
        date: Date string in YYYY-MM-DD format.
        time: Time string in HH:MM (24h) format.
        duration_minutes: Duration of the event in minutes.
        description: Event description (may be empty).
        calendar_id: Target calendar ID.

    Returns:
        Dict with event 'id' and 'link'.

    Raises:
        ValueError: If date/time format is invalid.
        HttpError: If the Google API call fails.
    """
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

    service = get_calendar_service()
    created = (
        service.events()
        .insert(calendarId=calendar_id, body=event_body)
        .execute()
    )

    return {
        "id": created["id"],
        "link": created.get("htmlLink", ""),
    }
