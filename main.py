"""_summary_.

Returns:
    _type_: _description_
"""
import logging
import os
from datetime import datetime

import discord
import requests
from discord.ext import tasks
from sqlalchemy import select

import botcontext
from model import Alert
from model import League
from model import Match
from model import Team

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
    all_leagues = []
    for league_dict in data:
        league = League(**{k: league_dict[k] for k in dir(League) if k in league_dict})
        all_leagues.append(league)
        instance.session.merge(league)
    instance.session.commit()


def get_leagues(ctx: discord.AutocompleteContext = None):
    """_summary_.

    Args:
        ctx (discord.AutocompleteContext, optional): _description_.
        Defaults to None.

    Returns:
        _type_: _description_
    """
    return [x[0] for x in instance.session.execute(select(League)).all()]

def get_team_by_name(team_name):
    return instance.session.execute(select(Team).where(Team.name == team_name)).one()[0]

def get_league_by_slug(league_slug):
    return instance.session.execute(select(League).where(League.slug == league_slug)).one()[0]

def get_alerts(ctx: discord.AutocompleteContext = None):
    """_summary_.

    Args:
        ctx (discord.AutocompleteContext, optional): _description_.
        Defaults to None.

    Returns:
        _type_: _description_
    """
    return [x[0] for x in instance.session.execute(select(Alert)).all()]


def fetch_events_and_teams():
    """_summary_.

    Args:
        listOfLeagues (_type_): _description_

    Returns:
        _type_: _description_
    """
    url = "https://esports-api.service.valorantesports.com/persisted/val/getSchedule?hl=en-US&sport=val&leagueId="
    for league in get_leagues():
        url = url + f'{league.id},'
    url = url[:-1]
    payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
    response = requests.get(url, headers=payload)

    data = response.json()["data"]

    # Going through all the teams in the upcoming events
    for i in data["schedule"]["events"]:
        # Creating both teams and flushing them to the DB
        team_a_dict = i["match"]["teams"][0]
        team_a = Team(**{k: team_a_dict[k] for k in dir(League) if k in team_a_dict})
        instance.session.merge(team_a)

        team_b_dict = i["match"]["teams"][1]
        team_b = Team(**{k: team_b_dict[k] for k in dir(League) if k in team_b_dict})
        instance.session.merge(team_b)

        match_dict = i["match"]
        match = Match(
            id=match_dict["id"],
            startTime=datetime.strptime(i["startTime"], "%Y-%m-%dT%H:%M:%SZ"),
            bo_count=i["match"]["strategy"]["count"],
            league_slug=i["league"]["slug"],
            team_a=team_a.name,
            team_b=team_b.name
        )
        instance.session.merge(match)
    instance.session.commit()

    return data

def get_matches():
    """_summary_.

    Args:
        ctx (discord.AutocompleteContext, optional): _description_.
        Defaults to None.

    Returns:
        _type_: _description_
    """
    return [x[0] for x in instance.session.execute(select(Match)).all()]

def get_upcoming_matches():
    in_5_mins = datetime.now() + datetime.timedelta(minutes=5)
    return [x[0] for x in instance.session.execute(select(Match).where(in_5_mins > Match.startTime).where(Match.startTime < datetime.now())).all()]

def get_teams(ctx: discord.AutocompleteContext = None):
    """_summary_.

    Args:
        ctx (discord.AutocompleteContext, optional): _description_.
        Defaults to None.

    Returns:
        _type_: _description_
    """
    return [x[0] for x in instance.session.execute(select(Team)).all()]


def get_team_names(ctx: discord.AutocompleteContext = None):
    """_summary_.

    Args:
        ctx (discord.AutocompleteContext, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    return [team.name for team in get_teams()]


def get_league_names(ctx: discord.AutocompleteContext = None):
    """_summary_.

    Args:
        ctx (discord.AutocompleteContext, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    return [league.name for league in get_leagues()]


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


def create_team_alert(team_name, channel_id):
    """_summary_.

    Args:
        league_name (_type_): _description_
        channel_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    team = instance.session.execute(
        select(Team.name).where(Team.name == team_name)
    ).one()
    team_name = team.name
    alert = Alert(channel_id=channel_id, team_name=team_name)
    instance.session.add(alert)
    instance.session.commit()
    return alert


def get_alerts_teams(team_a, team_b):
    return [x[0] for x in instance.session.execute(select(Alert).where(Alert.team_name == team_a).where(Alert.team_name == team_b)).all()]


async def embed_alert(team_a, team_b, league, match):
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

async def send_match_alert(channel_id, match):
    channel = instance.bot.get_channel(channel_id)
    team_a = get_team_by_name(match.team_a)
    team_b = get_team_by_name(match.team_b)
    league = get_league_by_slug(match.league_slug), 
    await channel.send(embed=embed_alert(team_a, team_b, league, match))

def refresh_data():
    """_summary_."""
    instance.logger.info("Refreshing leagues...")
    for league in fetch_leagues():
        instance.session.merge(league)
    instance.session.commit()

    instance.logger.info("Refreshing events...")


# BOT LOGIC


# Fetching initial data
@instance.bot.event
async def on_ready():
    """_summary_."""
    fetch_leagues()

    fetch_events_and_teams()
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

        await ctx.respond(f"Successfully created an alert for {league} !")


@instance.subscribe.command(name="team", description="Subscribe to team alerts")
async def subscribe_team(
    ctx: discord.ApplicationContext,
    team: discord.Option(
        discord.SlashCommandOptionType.string,
        autocomplete=discord.utils.basic_autocomplete(get_team_names),
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
        alert = create_team_alert(team, ctx.channel_id)
        instance.logger.info(f"Created alert {str(alert)}")

        # await ctx.respond(f"{[team.name for team in get_teams()]} !")
        await ctx.respond(f"Successfully created an alert for {team} !")


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
        for league in get_leagues():
            create_league_alert(league.name, ctx.channel_id)
        await ctx.respond("Subscribed to all the different leagues !")


@tasks.loop(seconds=300)
async def checkForMatches():
    """_summary_.

    Returns:
        _type_: _description_
    """
    for match in get_upcoming_matches():
        for alert in get_alerts_teams(match.team_a, match.team_b):
            if alert.team_name != None:
                if alert.team_name == match.team_a or alert.team_name == match.team_b :
                    send_match_alert(alert.channel_id, match)

    return 0

instance.bot.run(os.getenv("DISCORD_TOKEN"))
