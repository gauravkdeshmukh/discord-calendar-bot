"""Entry point — runs the Discord bot and OAuth callback web server together."""

import asyncio
import logging
import os

from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

from bot import client
from google_calendar import exchange_code
from storage import save_token

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

if not DISCORD_TOKEN:
    raise EnvironmentError("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


async def oauth_callback(request: web.Request) -> web.Response:
    code = request.query.get("code")
    state = request.query.get("state")  # Discord user ID

    if not code or not state:
        return web.Response(text="Missing code or state.", status=400)

    try:
        token_data = exchange_code(code)
        save_token(state, token_data)
        return web.Response(
            text="<h2 style='font-family:sans-serif'>Connected! ✅<br>You can now use <code>/create_event</code> on Discord.</h2>",
            content_type="text/html",
        )
    except Exception:
        log.exception("OAuth callback error for state=%s", state)
        return web.Response(
            text="Authentication failed. Please try /connect again.", status=500
        )


async def main():
    # Start OAuth callback web server
    app = web.Application()
    app.router.add_get("/oauth/callback", oauth_callback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info("OAuth callback server listening on port %s", PORT)

    # Start Discord bot
    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
