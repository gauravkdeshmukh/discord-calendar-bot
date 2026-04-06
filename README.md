# Discord Calendar Bot

A simple Discord bot that lets any server member create Google Calendar events via a slash command.

## Commands

| Command | Description |
|---|---|
| `/create_event title date time [duration] [description]` | Create a calendar event |

**Example:**
```
/create_event title:Team Standup date:2025-06-15 time:09:00 duration:30 description:Daily sync
```

---

## Setup

### 1. Prerequisites

- Python 3.10+
- A Discord application + bot token
- A Google Cloud project with the Calendar API enabled

---

### 2. Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications) → New Application.
2. Under **Bot**, click **Reset Token** and copy it.
3. Under **OAuth2 > URL Generator**, select scopes: `bot`, `applications.commands`.
4. Select bot permission: **Send Messages**. Copy the URL and invite the bot to your server.

---

### 3. Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → New Project.
2. Enable **Google Calendar API**.
3. Go to **APIs & Services > Credentials** → Create **OAuth 2.0 Client ID** (Desktop app).
4. Download the JSON file and save it as `credentials.json` in the project root.

> `credentials.json` is listed in `.gitignore` — never commit it.

---

### 4. Install & Configure

```bash
# Clone / enter the repo
cd discord-calendar-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set DISCORD_TOKEN and optionally GOOGLE_CALENDAR_ID
```

---

### 5. Authenticate with Google (one-time)

```bash
python -c "from google_calendar import get_calendar_service; get_calendar_service()"
```

A browser window will open. Sign in and grant access. This saves `token.json` locally for future runs.

> `token.json` is listed in `.gitignore` — never commit it.

---

### 6. Run the Bot

```bash
python bot.py
```

---

## Security Notes

- `DISCORD_TOKEN`, `credentials.json`, and `token.json` are **never committed** (enforced by `.gitignore`).
- All secrets are loaded from environment variables via `.env`.
- Errors shown to Discord users are generic; full details are only logged server-side.
- The bot uses the minimum required Google OAuth scope (`calendar.events` write-only).

---

## File Structure

```
discord-calendar-bot/
├── bot.py               # Discord bot + slash command
├── google_calendar.py   # Google Calendar API wrapper
├── requirements.txt
├── .env.example         # Template — copy to .env
├── .gitignore
└── README.md
```
