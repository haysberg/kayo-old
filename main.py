"""_summary_.

Returns:
    _type_: _description_
"""
import logging
import os
from typing import List

import discord
import requests
from sqlalchemy import select

import botcontext
from model import Alert
from model import League

global instance
instance = botcontext.BotContext()


def fetch_leagues():
    """_summary_.

    Returns:
        _type_: _description_
    """
    # The league endpoint
    url = "https://esports-api.service.valorantesports.com/persisted/val/getLeagues?hl=en-US&sport=val"
    payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
    response = requests.get(url, headers=payload)
    data = response.json()["data"]["leagues"]
    all_leagues: List[League] = ()
    for league_dict in data:
        league = League(**{k: league_dict[k] for k in dir(League) if k in league_dict})
        all_leagues.append(league)
    return all_leagues


def get_league_names(ctx: discord.AutocompleteContext = None):
    """_summary_.

    Args:
        ctx (discord.AutocompleteContext, optional): _description_.
        Defaults to None.

    Returns:
        _type_: _description_
    """
    res = []
    for row in instance.session.execute(select(League.name)).all():
        res.append(str(row.name))
    return res


def fetch_events(listOfLeagues):
    """_summary_.

    Args:
        listOfLeagues (_type_): _description_

    Returns:
        _type_: _description_
    """
    url = "https://esports-api.service.valorantesports.com/persisted/val/getSchedule?hl=en-US&sport=val&leagueId="
    for league in listOfLeagues:
        url = url + f'{listOfLeagues[league]["id"]},'
    url = url[:-1]
    payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
    response = requests.get(url, headers=payload)

    print(url)

    return response.json()["data"]["schedule"]["events"]


def create_league_alert(league_name, channel_id):
    """_summary_.

    Args:
        league_name (_type_): _description_
        channel_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    league = instance.session.execute(
        select(League.id).where(League.name == league_name)
    ).one()
    league_id = league.id
    alert = Alert(channel_id=channel_id, league_id=league_id)
    instance.session.add(alert)
    instance.session.commit()
    return alert


async def embed_league(team_a, team_b, league, match):
    """_summary_.

    Args:
        team_a (_type_): _description_
        team_b (_type_): _description_
        league (_type_): _description_
        match (_type_): _description_

    Returns:
        _type_: _description_
    """
    embed = discord.Embed(
        title=f'{team_a["name"]} ⚔️ {team_b["name"]}',
        description=f'{league["name"]} - BO{match["strategy"]["count"]}',
        color=discord.Colour.red(),
    )

    embed.add_field(name="Inline Field 1", value="Inline Field 1", inline=True)
    embed.add_field(name="Inline Field 2", value="Inline Field 2", inline=True)
    embed.add_field(name="Inline Field 3", value="Inline Field 3", inline=True)

    # embed.set_footer(text="Coucou") # footers can have icons too
    # embed.set_author(name="Team", icon_url="https://example.com/link-to-my-image.png")
    # embed.set_thumbnail(url="https://example.com/link-to-my-thumbnail.png")
    embed.set_image(url=f'{league["image"]}')

    return embed


# BOT LOGIC


# Fetching initial data
@instance.bot.event
async def on_ready():
    """_summary_."""
    for league in fetch_leagues():
        instance.session.merge(league)
    instance.session.commit()

    # logging.info(f"Downloaded {len(listOfLeagues)} leagues.")

    # listOfEvents = kayo.fetch_events(listOfLeagues)
    # logging.info(f"Downloaded {len(listOfEvents)} schedules.")

    # logging.info(f"{bot.user} is online! 🚀")


@instance.bot.event
async def on_disconnect():
    """_summary_."""
    logging.error(f"{instance.bot.user} is disconnected ! 💣")


@instance.bot.command(description="Sends the bot's latency.")
async def ping(ctx):
    """_summary_.

    Args:
        ctx (_type_): _description_
    """
    latency_ms = round(instance.bot.latency * 1000)
    await ctx.respond(f"Pong! Latency is {latency_ms} ms")


@instance.subscribe.command(name="league", description="Subscribe to league alerts")
async def subscribe_league(
    ctx: discord.ApplicationContext,
    league: discord.Option(
        discord.SlashCommandOptionType.string,
        autocomplete=discord.utils.basic_autocomplete(get_league_names),
    ),
):
    """_summary_.

    Args:
        ctx (discord.ApplicationContext): _description_
        league (discord.Option, optional): _description_.
        Defaults to discord.utils.basic_autocomplete(get_league_names) ).
    """
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond(
            "Sorry, only Administrators are allowed to run this command !"
        )
    else:
        alert = create_league_alert(league, ctx.channel_id)
        instance.logger.info(f"Created alert {str(alert)}")
        await ctx.respond(f"Successfully created an alert for {league}` !")


@instance.subscribe.command(
    name="all_leagues", description="Subscribe to league alerts"
)
async def subscribe_all_leagues(ctx: discord.ApplicationContext):
    """_summary_.

    Args:
        ctx (discord.ApplicationContext): _description_
    """
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond(
            "Sorry, only Administrators are allowed to run this command !"
        )
    else:
        for league in get_league_names():
            create_league_alert(league, ctx.channel_id)
        await ctx.respond("Subscribed to all the different leagues !")


instance.bot.run(os.getenv("DISCORD_TOKEN"))
