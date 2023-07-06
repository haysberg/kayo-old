"""_summary_."""
import json
import logging
import sys

import discord
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Base

import logging
import os
from datetime import datetime

import discord
import requests
from sqlalchemy import select

from model import Alert
from model import League
from model import Match
from model import Team


class BotContext:
    """_summary_."""

    def __init__(self):
        """_summary_."""
        if os.getenv("DEPLOYED") == "production" :
            self.engine = (create_engine("sqlite:///db/kayo.db"))
        else :
            self.engine = (create_engine("sqlite:///:memory:"))
        Session = sessionmaker(bind=self.engine)

        global session
        self.session = Session()
        Base.metadata.create_all(self.engine)

        # Initializing core objects
        dotenv.load_dotenv()
        self.bot = discord.Bot()
        self.subscribe = self.bot.create_group("subscribe", "Subscribing to leagues and teams")

        # Logging
        self.logger = logging.getLogger('discord')        

        if os.getenv("DEPLOYED") == "production" :
            self.logger.setLevel(logging.INFO)
            self.logger = logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        else :
            self.logger.setLevel(logging.DEBUG)
            self.logger = logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
        

        self.logger = logging.getLogger()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
        self.logger.addHandler(handler)

        # Opening JSON file
        with open('referential.json') as json_file:
            self.referential = json.load(json_file)


global instance
instance = BotContext()


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
            blockName=i["blockName"],
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

def get_alerts_league(league_slug):
    league = instance.session.execute(select(League).where(League.slug == league_slug)).one()[0]
    return [x[0] for x in instance.session.execute(select(Alert).where(Alert.league_id == league.id)).all()]


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
        title=f'{team_a.name} ⚔️ {team_b.name}',
        description=f'{league.name} · {match.blockName} · BO{match.bo_count}',
        color=discord.Colour.red(),
    )

    if team_a.name in instance.referential["teams"]:
        embed.add_field(name=f'{team_a.name}\'s stream', value=f'[Link]({instance.referential["teams"][team_a.name]})', inline=True)
    if league.name in instance.referential["leagues"]:
        embed.add_field(name="Official stream", value=f'[Link]({instance.referential["leagues"][league.name]})', inline=True)
    if team_b.name in instance.referential["teams"]:
        embed.add_field(name=f'{team_b.name}\'s stream', value=f'[Link]({instance.referential["teams"][team_b.name]})', inline=True)
    embed.set_thumbnail(url=f'{league.image}')

    return embed

async def send_match_alert(channel_id, match):
    channel = instance.bot.get_channel(channel_id)
    team_a = get_team_by_name(match.team_a)
    team_b = get_team_by_name(match.team_b)
    league = get_league_by_slug(match.league_slug),
    await channel.send(embed=await embed_alert(team_a, team_b, league[0], match))

def refresh_data():
    """_summary_."""
    instance.logger.info("Refreshing leagues...")
    for league in fetch_leagues():
        instance.session.merge(league)
    instance.session.commit()

    instance.logger.info("Refreshing events...")