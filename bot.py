"""Discord bot with /create_event slash command."""

import os
import logging

import discord
from discord import app_commands
from dotenv import load_dotenv

from google_calendar import create_event

load_dotenv()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

if not DISCORD_TOKEN:
    raise EnvironmentError("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


class CalendarBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        log.info("Slash commands synced.")

    async def on_ready(self):
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)


client = CalendarBot()


@client.tree.command(name="create_event", description="Create a Google Calendar event")
@app_commands.describe(
    title="Event title",
    date="Date in YYYY-MM-DD format (e.g. 2025-06-15)",
    time="Start time in HH:MM 24h format, UTC (e.g. 14:30)",
    duration="Duration in minutes (default: 60)",
    description="Optional event description",
)
async def create_event_command(
    interaction: discord.Interaction,
    title: str,
    date: str,
    time: str,
    duration: int = 60,
    description: str = "",
):
    # Validate duration
    if duration <= 0 or duration > 1440:
        await interaction.response.send_message(
            "Duration must be between 1 and 1440 minutes.", ephemeral=True
        )
        return

    # Defer so we have time to call the API
    await interaction.response.defer(ephemeral=False, thinking=True)

    try:
        result = create_event(
            title=title,
            date=date,
            time=time,
            duration_minutes=duration,
            description=description,
            calendar_id=CALENDAR_ID,
        )
        log.info(
            "Event created by %s: %s (ID: %s)", interaction.user, title, result["id"]
        )
        embed = discord.Embed(
            title="Event Created",
            description=f"**{title}** has been added to the calendar.",
            color=discord.Color.green(),
        )
        embed.add_field(name="Date", value=date, inline=True)
        embed.add_field(name="Time (UTC)", value=time, inline=True)
        embed.add_field(name="Duration", value=f"{duration} min", inline=True)
        if description:
            embed.add_field(name="Description", value=description, inline=False)
        if result["link"]:
            embed.add_field(name="Open in Calendar", value=result["link"], inline=False)
        embed.set_footer(text=f"Created by {interaction.user.display_name}")

        await interaction.followup.send(embed=embed)

    except ValueError as e:
        await interaction.followup.send(f"Invalid input: {e}", ephemeral=True)
    except FileNotFoundError as e:
        log.error("credentials.json missing: %s", e)
        await interaction.followup.send(
            "Bot configuration error: Google credentials not found. Contact the bot owner.",
            ephemeral=True,
        )
    except Exception as e:
        log.exception("Unexpected error creating event")
        await interaction.followup.send(
            "An unexpected error occurred. Please try again later.", ephemeral=True
        )


client.run(DISCORD_TOKEN, log_handler=None)
