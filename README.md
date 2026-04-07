# Discord Calendar Bot

<p align="center">
  <img src="assets/icon.png" alt="calendar-bot-by-gd" width="300"/>
</p>

A Discord bot that lets **any user** create events on **their own Google Calendar** directly from Discord — no sharing required.

---

## Commands

| Command | Description |
|---|---|
| `/connect` | Link your personal Google Calendar (one-time per user) |
| `/create_event` | Create an event on your own Google Calendar |
| `/disconnect` | Unlink your Google Calendar |

**Example:**
```
/create_event title:Team Standup date:2025-06-15 time:09:00 duration:30 description:Daily sync
```

---

## How It Works

1. Each user runs `/connect` → receives a personal Google OAuth link (visible only to them)
2. User authorizes the bot to access their own Google Calendar
3. The bot stores their token securely on the server (never shared)
4. `/create_event` creates the event on **that user's** calendar

---

## Setup

### 1. Prerequisites

- Python 3.10+
- A Discord application + bot token
- A Google Cloud project with the Calendar API enabled
- A public URL for the OAuth callback (Railway, VPS, or ngrok for local testing)

---

### 2. Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications) → New Application.
2. Under **Bot**, click **Reset Token** and copy it.
3. Under **OAuth2 > URL Generator**, select scopes: `bot`, `applications.commands`.
4. Select bot permission: **Send Messages**. Copy the URL and invite the bot to your server.

---

### 3. Google OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → New Project.
2. Enable **Google Calendar API**.
3. Go to **APIs & Services > Credentials** → Create **OAuth 2.0 Client ID**.
   - Application type: **Web application**
   - Authorized redirect URI: `https://your-domain.com/oauth/callback`
4. Copy the **Client ID** and **Client Secret**.

---

### 4. Install & Configure

```bash
cd discord-calendar-bot

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — fill in DISCORD_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, CALLBACK_URL
```

---

### 5. Run

```bash
python main.py
```

This starts both the Discord bot and the OAuth callback web server on the configured `PORT`.

---

### 6. Local Testing with ngrok

If you don't have a public server yet:

```bash
ngrok http 8080
# Copy the https URL, e.g. https://abc123.ngrok.io
# Set CALLBACK_URL=https://abc123.ngrok.io in .env
# Add https://abc123.ngrok.io/oauth/callback to your Google OAuth redirect URIs
```

---

## Security Notes

- Each user's Google token is stored in `tokens.json` keyed by Discord user ID — never shared between users
- `tokens.json`, `.env` are in `.gitignore` — never committed
- All secrets are loaded from environment variables
- The bot uses the minimum required Google OAuth scope (`calendar.events` — write-only)
- OAuth state parameter ties the callback to a specific Discord user, preventing token hijacking
- Error messages shown to users are generic; sensitive details only go to server-side logs

---

## File Structure

```
discord-calendar-bot/
├── main.py              # Entry point — runs bot + OAuth web server
├── bot.py               # Discord slash commands
├── google_calendar.py   # Google Calendar API + OAuth helpers
├── storage.py           # Per-user token storage
├── requirements.txt
├── .env.example         # Template — copy to .env
├── .gitignore
├── assets/
│   └── icon.png
└── README.md
```
