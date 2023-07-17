"""_summary_.

Returns:
    _type_: _description_
"""
import logging
import os

import discord
from discord.ext import commands
from discord.ext import tasks

from kayo import create_league_alert
from kayo import create_team_alert
from kayo import delete_alert
from kayo import fetch_events_and_teams
from kayo import fetch_leagues
from kayo import get_alerts_league
from kayo import get_alerts_teams
from kayo import get_league_names
from kayo import get_leagues
from kayo import get_matches
from kayo import get_team_names
from kayo import get_teams
from kayo import get_upcoming_matches
from kayo import instance
from kayo import send_match_alert

# BOT LOGIC


@instance.bot.event
async def on_ready():
    """Executed when the Discord bot boots up."""
    checkForMatches.start()
    updateDatabase.start()

    logging.info(f"{instance.bot.user} is online! 🚀")


@instance.bot.event
async def on_disconnect():
    """What happens when the bot is disconnected from Discord."""
    logging.error(f"{instance.bot.user} is disconnected ! 💣")


@instance.bot.command(description="Prints out a help message")
async def help(ctx):
    """Displays help.

    Args:
        ctx (discord.ApplicationContext): Information about the current message.
    """
    await ctx.respond("""Hello ! My name is KAY/O and my mission is to send messages when pro matches are about to start. Here is a list of my commands :

    `/subscribe all_leagues` will give you alerts for every single matches happening.
    `/subscribe league [name]` will give you alerts for a specific league (for example, VCT EMEA)
    `/subscribe team [name]` will give you alerts for a specific team (for example, FNATIC)
    `/unsubscribe league [name]` will give you alerts for a specific league (for example, VCT EMEA)
    `/unsubscribe team [name]` will give you alerts for a specific team (for example, FNATIC)
    `/ping` to check if I'm still working. I'm kinda new to this so sometimes I die.

    Please note that the commands are channel-specific. Meaning the alerts will be sent in the channel you sent the command in.

    Except the `ping` command, you need 'Manage Messages' permission to add / remove alerts in a public server.
    You can still DM me if you want the alerts in your DMs though !

    By the way, my code is open source, so check out my code if you want. Link is in my profile description.""")


@instance.bot.command(description="Sends the bot's latency.")
async def ping(ctx):
    """Simple ping command.

    Args:
        ctx (discord.ApplicationContext): Information about the current message.
    """
    latency_ms = round(instance.bot.latency * 1000)
    await ctx.respond(f"Pong! `{latency_ms}` ms")


@instance.subscribe.command(name="league", description="Subscribe to league alerts")
@commands.has_permissions(manage_messages=True)
async def subscribe_league(
    ctx: discord.ApplicationContext,
    league: discord.Option(
        discord.SlashCommandOptionType.string,
        autocomplete=discord.utils.basic_autocomplete(get_league_names),
    ),
):
    """Subscribes the channel to a league.

    Args:
        ctx (discord.ApplicationContext): Information about the current message.
        league (discord.Option): Name of the League to follow.
        Defaults to discord.utils.basic_autocomplete(get_league_names)).
    """
    try:
        alert = create_league_alert(league, ctx.channel_id)
        instance.logger.info(f"Created alert {str(alert)}")
        await ctx.respond(f"Successfully created an alert for {league} !")
    except discord.ext.commands.errors.MissingPermissions:
        await ctx.respond("You need to have the 'Manage Messages' permission to run this command in a server. Feel free to send me a DM !")


@instance.subscribe.command(name="team", description="Subscribe to team alerts")
@commands.has_permissions(manage_messages=True)
async def subscribe_team(
    ctx: discord.ApplicationContext,
    team: discord.Option(
        discord.SlashCommandOptionType.string,
        autocomplete=discord.utils.basic_autocomplete(get_team_names),
    ),
):
    """Subscribe the Discord channel to a Team.

    Args:
        ctx (discord.ApplicationContext): Information about the current message.
        team (discord.Option, optional): Autocomplete.
        Defaults to discord.utils.basic_autocomplete(get_league_names) ).
    """
    try:
        alert = create_team_alert(team, ctx.channel_id)
        instance.logger.info(f"Created alert {str(alert)}")
        await ctx.respond(f"Successfully created an alert for {team} !")
    except discord.ext.commands.errors.MissingPermissions:
        await ctx.respond("You need to have the 'Manage Messages' permission to run this command in a server. Feel free to send me a DM !")


@instance.unsubscribe.command(name="league", description="Delete a league alert for this channel")
@commands.has_permissions(manage_messages=True)
async def unsubscribe_league(
    ctx: discord.ApplicationContext,
    league: discord.Option(
        discord.SlashCommandOptionType.string,
        autocomplete=discord.utils.basic_autocomplete(get_league_names),
    ),
):
    """Subscribes the channel to a league.

    Args:
        ctx (discord.ApplicationContext): Information about the current message.
        league (discord.Option): Name of the League to follow.
        Defaults to discord.utils.basic_autocomplete(get_league_names)).
    """
    try:
        league_obj = [x for x in get_leagues() if x.name == league][0]
        delete_alert(ctx.channel_id, league=league_obj)
        await ctx.respond(f"Successfully deleted an alert for {league} !")
    except discord.ext.commands.errors.MissingPermissions:
        await ctx.respond("You need to have the 'Manage Messages' permission to run this command in a server. Feel free to send me a DM !")


@instance.unsubscribe.command(name="team", description="Delete a team alert for this channel")
@commands.has_permissions(manage_messages=True)
async def unsubscribe_team(
    ctx: discord.ApplicationContext,
    team: discord.Option(
        discord.SlashCommandOptionType.string,
        autocomplete=discord.utils.basic_autocomplete(get_team_names),
    ),
):
    """Subscribe the Discord channel to a Team.

    Args:
        ctx (discord.ApplicationContext): Information about the current message.
        team (discord.Option, optional): Autocomplete.
        Defaults to discord.utils.basic_autocomplete(get_league_names) ).
    """
    try:
        team_obj = [x for x in get_teams() if x.name == team][0]
        delete_alert(ctx.channel_id, team=team_obj)
        await ctx.respond(f"Successfully deleted an alert for {team} !")
    except discord.ext.commands.errors.MissingPermissions:
        await ctx.respond("You need to have the 'Manage Messages' permission to run this command in a server. Feel free to send me a DM !")


@instance.subscribe.command(name="all_leagues", description="Subscribe to league alerts")
@commands.has_permissions(manage_messages=True)
async def subscribe_all_leagues(ctx: discord.ApplicationContext):
    """Susbcribe the channel to all the different leagues.

    Args:
        ctx (discord.ApplicationContext): Information about the current message.
    """
    instance.logger.info('Creating alert...')
    try:
        for league in get_leagues():
            create_league_alert(league.name, ctx.channel_id)
        await ctx.respond("Subscribed to all the different leagues !")
    except discord.ext.commands.errors.MissingPermissions as e:
        instance.logger.error(str(e))


@instance.bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    """Handler for command errors inside Discord.

    Args:
        ctx (discord.ApplicationContext): Information about the current message.
        error (discord.DiscordException): The Discord exception data.

    Raises:
        error: Just here to handle an exception-ception.
    """
    if isinstance(error, discord.ext.commands.errors.MissingPermissions):
        await ctx.respond("You need to have the 'Manage Messages' permission to run this command in a server. Feel free to send me a DM !")
    else:
        raise error  # Here we raise other errors to ensure they aren't ignored


@tasks.loop(seconds=300)
async def checkForMatches():
    """Checks if there is new upcoming matches."""
    instance.logger.info("Checking for alerts to send...")
    for match in get_upcoming_matches():
        for alert in get_alerts_teams(match.team_a, match.team_b):
            await send_match_alert(alert.channel_id, match)
        for alert in get_alerts_league(match.league_slug):
            await send_match_alert(alert.channel_id, match)


@tasks.loop(seconds=1800)
async def updateDatabase():
    """Checks if there is new upcoming matches."""
    instance.logger.info("Updating the database periodically...")
    fetch_leagues()
    fetch_events_and_teams()


if os.getenv("LOGLEVEL") == "DEBUG":
    @instance.bot.command(description="debug command")
    @commands.has_permissions(manage_roles=True, ban_members=True)
    async def debug_alert(ctx):
        """Sends a buttload of alerts for debugging the format.

        Args:
            ctx (discord.ApplicationContext): Information about the current message.
        """
        for match in get_matches():
            await send_match_alert(ctx.channel_id, match)
        await ctx.respond("Sending alerts your way...")

    @instance.subscribe.command(name="all_teams", description="Subscribe to team alerts")
    @commands.has_permissions(manage_roles=True, ban_members=True)
    async def subscribe_all_teams(ctx: discord.ApplicationContext):
        """Susbcribe the channel to all the different leagues.

        Args:
            ctx (discord.ApplicationContext): Information about the current message.
        """
        instance.logger.info('Creating alert...')
        try:
            for team in get_teams():
                create_team_alert(team.name, ctx.channel_id)
            await ctx.respond("Subscribed to all the different teams !")
        except discord.ext.commands.errors.MissingPermissions as e:
            instance.logger.error(str(e))


instance.bot.run(os.getenv("DISCORD_TOKEN"))
