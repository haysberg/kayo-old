"""_summary_."""
import json
import logging
import os
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import discord
import dotenv
import requests
from sqlalchemy import create_engine
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from model import Alert
from model import Base
from model import League
from model import Match
from model import Team

dotenv.load_dotenv()
LOGLEVEL = os.environ.get('LOGLEVEL').upper()


class BotContext:
    """Contains all the useful objects to interact with the database and the logger."""

    def __init__(self):
        """Creates all the objects."""
        if os.getenv("DEPLOYED") == "production":
            self.engine = (create_engine("sqlite:///db/kayo.db"))
        else:
            self.engine = (create_engine("sqlite:///:memory:"))
        Session = sessionmaker(bind=self.engine)

        global session
        self.session = Session()
        Base.metadata.create_all(self.engine)

        # Initializing core objects
        self.bot = discord.Bot()
        self.subscribe = self.bot.create_group("subscribe", "Subscribing to leagues and teams")
        self.unsubscribe = self.bot.create_group("unsubscribe", "Deleting alerts for leagues and teams")

        # Logging
        self.logger = logging.getLogger('discord')
        self.logger.setLevel(level=LOGLEVEL)
        self.logger = logging.getLogger("sqlalchemy.engine").setLevel(level=LOGLEVEL)

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
    """Downloads all the leagues and inserts them in the database."""
    # The league endpoint
    instance.logger.info('Fetching Leagues...')
    url = "https://esports-api.service.valorantesports.com/persisted/val/getLeagues?hl=en-US&sport=val"
    try:
        payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
        response = requests.get(url, headers=payload)
        data = response.json()["data"]["leagues"]
        all_leagues = []
        for league_dict in data:
            league = League(**{k: league_dict[k] for k in dir(League) if k in league_dict})
            all_leagues.append(league)
            instance.session.merge(league)
        instance.session.commit()
    except requests.RequestException as e:
        instance.logger.error(f'Error while fetching the leagues: {e}')
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while inserting leagues into the database: {e}')


def get_leagues(ctx: discord.AutocompleteContext = None):
    """Gets all the leagues currently in the database.

    Args:
        ctx (discord.AutocompleteContext, optional): Used when called from autocompletion.
        Defaults to None.

    Returns:
        List[League]: The list of leagues.
    """
    try:
        instance.logger.info('Getting all the leagues from DB...')
        return [x[0] for x in instance.session.execute(select(League)).all()]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting leagues from the database: {e}')


def get_team_by_name(team_name):
    """Returns a team object based on its name.

    Args:
        team_name (str): The team's name.

    Returns:
        Team: A single team object.
    """
    try:
        return instance.session.execute(select(Team).where(Team.name == team_name)).one()[0]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting a league from the database: {e}')


def get_league_by_slug(league_slug):
    """Returns a League object based on its slug.

    Args:
        league_slug (str): The league's slug.

    Returns:
        League: A single League object.
    """
    try:
        return instance.session.execute(select(League).where(League.slug == league_slug)).one()[0]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting a league from the database: {e}')


def get_alerts(ctx: discord.AutocompleteContext = None):
    """Gets all the alerts from the database.

    Args:
        ctx (discord.AutocompleteContext, optional): Used when called from autocompletion.
        Defaults to None.

    Returns:
        List[Alert]: All the alerts in the database.
    """
    try:
        return [x[0] for x in instance.session.execute(select(Alert)).all()]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting an alert from the database: {e}')


def fetch_events_and_teams():
    """Downloads events and teams from the Riot API. Then inserts it in the database.

    Returns:
        dict: the response of the API as a JSON
    """
    url = "https://esports-api.service.valorantesports.com/persisted/val/getSchedule?hl=en-US&sport=val&leagueId="
    for league in get_leagues():
        payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
        response = requests.get(f'{url}{league.id}', headers=payload)
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
                startTime=datetime.strptime(i["startTime"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz=None),
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
    """Gets all the matches in the database.

    Returns:
       List[Match]: All the matches in the database.
    """
    try:
        return [x[0] for x in instance.session.execute(select(Match)).all()]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting matches from the database: {e}')


def get_upcoming_matches():
    """Gets all the matches happening in the next 5 minutes in the database.

    Returns:
        List[Matches]: All the matches happening in the next 5 minutes.
    """
    try:
        in_5_mins = datetime.now() + timedelta(minutes=5)
        instance.logger.info(f'Checking for new matches in between {datetime.now()} and {in_5_mins}')
        return [x[0] for x in instance.session.execute(select(Match).where(in_5_mins > Match.startTime, Match.startTime > datetime.now())).all()]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting matches from the database: {e}')


def get_teams(ctx: discord.AutocompleteContext = None):
    """Get all the teams currently in the database.

    Args:
        ctx (discord.AutocompleteContext, optional): Used when called from autocompletion.
        Defaults to None.

    Returns:
        List[Team]: All the Teams in the database.
    """
    return [x[0] for x in instance.session.execute(select(Team)).all()]


def get_team_names(ctx: discord.AutocompleteContext = None):
    """Gets a list of all the team names currently in the database.

    Args:
        ctx (discord.AutocompleteContext, optional): Used when called from autocompletion. Defaults to None.

    Returns:
        List[str]: List of Team names.
    """
    return [team.name for team in get_teams()]


def get_league_names(ctx: discord.AutocompleteContext = None):
    """Gets a list of all the League names currently in the database.

    Args:
        ctx (discord.AutocompleteContext, optional): Used when called from autocompletion. Defaults to None.

    Returns:
        List[str]: List of League names.
    """
    return [league.name for league in get_leagues()]


def create_league_alert(league_name, channel_id):
    """Creates an Alert to get notifications for a specific League.

    Args:
        league_name (str): The League's name.
        channel_id (int): Integer representing a single Discord channel.

    Returns:
        Alert: The Alert object created.
    """
    instance.logger.info(f'Creating an alert for league name: {league_name} in channel id: {channel_id}')
    try:
        league = instance.session.execute(
            select(League.id).where(League.name == league_name)
        ).one()
        if instance.session.execute(select(Alert).where(Alert.channel_id == channel_id, Alert.league_id == league.id)).first() is not None:
            alert = instance.session.execute(select(Alert).where(Alert.channel_id == channel_id, Alert.league_id == league.id)).first()
            return alert[0]
        else:
            alert = Alert(channel_id=channel_id, league_id=league.id)
            instance.session.add(alert)
            instance.session.commit()
            instance.logger.info('Successfully created an alert !')
        return alert
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while creating alert: {str(e)}')
        raise discord.ext.commands.errors.CommandError


def create_team_alert(team_name, channel_id):
    """Creates an Alert to get notifications for a specific Team.

    Args:
        team_name (str): The Team's name.
        channel_id (int): Integer representing a single Discord channel.

    Returns:
        Alert: The Alert object created.
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
    """Retrieves Alert objects from the database based on the Team the Alert follows.

    Args:
        team_a (str): One of the Team's names facing each other.
        team_b (str): One of the Team's names facing each other.

    Returns:
        List[Alert]: List of alerts
    """
    return [x[0] for x in instance.session.execute(select(Alert).where(Alert.team_name == team_a or Alert.team_name == team_b)).all()]


def get_alerts_league(league_slug):
    """Retrieves Alert objects from the database based on the League the Alert follows.

    Args:
        league_slug (str): League.slug of the League object

    Returns:
        List[Alert]: List of alerts
    """
    league = instance.session.execute(select(League).where(League.slug == league_slug)).one()[0]
    return [x[0] for x in instance.session.execute(select(Alert).where(Alert.league_id == league.id)).all()]


async def embed_alert(team_a, team_b, league, match):
    """Creates a discord.Embed object to be sent by send_match_alert().

    Args:
        team_a (Team): Team object for the notification
        team_b (Team): Team object for the notification
        league (League): League in which both Teams are facing off
        match (Match): The Match in which both Teams will face off

    Returns:
        discord.Embed: The discord.Embed object representing the alert
    """
    embed = discord.Embed(
        title=f'{team_a.name} ⚔️ {team_b.name}',
        description=f'{league.name} · {match.blockName} · BO{match.bo_count}',
        color=discord.Colour.red(),
    )

    embed.set_footer(text=f'Starts at {match.startTime.replace(tzinfo=datetime.now().astimezone().tzinfo).astimezone(tz=timezone.utc).strftime("%-I:%M")} · UTC · {match.startTime.strftime("%A %-d")}')

    if team_a.name in instance.referential["teams"]:
        embed.add_field(name=f'{team_a.name}\'s stream', value=f'[Link]({instance.referential["teams"][team_a.name]})', inline=True)
    if league.name in instance.referential["leagues"]:
        embed.add_field(name="Official stream", value=f'[Link]({instance.referential["leagues"][league.name]})', inline=True)
    if team_b.name in instance.referential["teams"]:
        embed.add_field(name=f'{team_b.name}\'s stream', value=f'[Link]({instance.referential["teams"][team_b.name]})', inline=True)
    embed.set_thumbnail(url=f'{league.image}')

    return embed


async def send_match_alert(channel_id, match):
    """Sends an alert to a specified channel_id for a specific Match.

    Args:
        channel_id (int): Integer representing a single Discord channel.
        match (Match): Match object for which we wish to send an Alert.
    """
    channel = instance.bot.get_channel(channel_id)
    team_a = get_team_by_name(match.team_a)
    team_b = get_team_by_name(match.team_b)
    league = get_league_by_slug(match.league_slug),
    await channel.send(embed=await embed_alert(team_a, team_b, league[0], match))


def refresh_data():
    """Fetches the data again."""
    instance.logger.info("Refreshing leagues...")
    for league in fetch_leagues():
        instance.session.merge(league)
    instance.session.commit()

    instance.logger.info("Refreshing events...")


def delete_alert(channel_id, league=None, team=None):
    """Deletes an alert based on the parameters given.

    Args:
        channel_id (Integer): Channel ID the command has been issued in
        league (League, optional): The League you would like to delete from alerts. Defaults to None.
        team_name (str, optional): The Team's name.
    """
    if league is not None:
        instance.session.execute(delete(Alert).where(Alert.channel_id == channel_id, Alert.league_id == league.id))
    if team is not None:
        instance.session.execute(delete(Alert).where(Alert.channel_id == channel_id, Alert.team_name == team.name))
    instance.session.commit()
