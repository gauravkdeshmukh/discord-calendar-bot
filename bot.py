"""Discord bot — slash commands for Google Calendar."""

import logging

import discord
from discord import app_commands

from google_calendar import get_auth_url, create_event
from storage import has_token, delete_token

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


@client.tree.command(name="connect", description="Link your Google Calendar to this bot")
async def connect(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    url = get_auth_url(state=user_id)
    await interaction.response.send_message(
        f"Click the link below to connect **your** Google Calendar:\n{url}\n\n"
        "After authorizing, come back and use `/create_event`.",
        ephemeral=True,
    )


@client.tree.command(name="disconnect", description="Unlink your Google Calendar from this bot")
async def disconnect(interaction: discord.Interaction):
    delete_token(str(interaction.user.id))
    await interaction.response.send_message(
        "Your Google Calendar has been disconnected.", ephemeral=True
    )


@client.tree.command(name="create_event", description="Create an event on your Google Calendar")
@app_commands.describe(
    title="Event title",
    date="Date in YYYY-MM-DD format (e.g. 2025-06-15)",
    time="Start time in HH:MM 24h UTC format (e.g. 14:30)",
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
    user_id = str(interaction.user.id)

    if not has_token(user_id):
        await interaction.response.send_message(
            "You haven't linked your Google Calendar yet. Use `/connect` first.",
            ephemeral=True,
        )
        return

    if not (1 <= duration <= 1440):
        await interaction.response.send_message(
            "Duration must be between 1 and 1440 minutes.", ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)

    try:
        result = create_event(
            discord_user_id=user_id,
            title=title,
            date=date,
            time=time,
            duration_minutes=duration,
            description=description,
        )
        log.info("Event created for user %s: %s", user_id, title)

        embed = discord.Embed(
            title="Event Created",
            description=f"**{title}** has been added to your Google Calendar.",
            color=discord.Color.green(),
        )
        embed.add_field(name="Date", value=date, inline=True)
        embed.add_field(name="Time (UTC)", value=time, inline=True)
        embed.add_field(name="Duration", value=f"{duration} min", inline=True)
        if description:
            embed.add_field(name="Description", value=description, inline=False)
        if result["link"]:
            embed.add_field(name="Open in Calendar", value=result["link"], inline=False)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")

        await interaction.followup.send(embed=embed)

    except PermissionError:
        await interaction.followup.send(
            "Your Google Calendar is not connected. Use `/connect` first.", ephemeral=True
        )
    except ValueError as e:
        await interaction.followup.send(f"Invalid input: {e}", ephemeral=True)
    except Exception:
        log.exception("Unexpected error creating event for user %s", user_id)
        await interaction.followup.send(
            "An unexpected error occurred. Please try again later.", ephemeral=True
        )
