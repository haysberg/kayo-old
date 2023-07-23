"""_summary_."""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import aiohttp
import discord
import dotenv
import requests
from sqlalchemy import create_engine
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
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
        # Logging
        logging.basicConfig(filename='./db/kayo.log', encoding='utf-8', level=LOGLEVEL)
        self.logger = logging.getLogger('discord')
        self.logger.setLevel(level=LOGLEVEL)
        self.logger = logging.getLogger("sqlalchemy.engine").setLevel(level=LOGLEVEL)

        self.logger = logging.getLogger()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
        self.logger.addHandler(handler)

        self.http_client = aiohttp.ClientSession()

        if os.getenv("DEPLOYED") == "production":
            self.engine = (create_engine("sqlite:///db/kayo.db"))
        else:
            self.engine = (create_engine("sqlite:///:memory:", echo=True))
        Session = sessionmaker(bind=self.engine)

        global session
        self.session = Session()
        Base.metadata.create_all(self.engine)

        # Initializing core objects
        self.bot = discord.Bot()
        self.subscribe = self.bot.create_group("subscribe", "Subscribing to leagues and teams")
        self.unsubscribe = self.bot.create_group("unsubscribe", "Deleting alerts for leagues and teams")

        # Opening JSON file
        with open('referential.json') as json_file:
            self.referential = json.load(json_file)


global instance
instance = BotContext()


def upsert_teams(
    teams: list[Team]
):
    """Upserts team objects.

    Args:
        teams (list[Team]): Teams to upsert
    """
    # https://www.sqlite.org/limits.html#max_variable_number
    for i in range(0, len(teams), 100):
        stmt = insert(Team).values(
            [
                {
                    "name": team.name,
                    "image": team.image
                }
                for team in teams[
                    i: i + 100
                    if i + 100 < len(teams)
                    else len(teams)
                ]
            ]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["name"],
            set_={"image": stmt.excluded.image},
        )
        instance.session.execute(stmt)
    instance.session.commit()


def upsert_matches(matches: list[Match]):
    """Upserts matches.

    Args:
        matches (list[Match]): Matches to upsert.
    """
    # https://www.sqlite.org/limits.html#max_variable_number
    for i in range(0, len(matches), 100):
        stmt = insert(Match).values(
            [
                {
                    "id": match.id,
                    "league_id": match.league_id,
                    "startTime": match.startTime,
                    "bo_count": match.bo_count,
                    "blockName": match.blockName,
                    "team_a": match.team_a,
                    "team_b": match.team_b,
                }
                for match in matches[
                    i: i + 100
                    if i + 100 < len(matches)
                    else len(matches)
                ]
            ]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "league_id": stmt.excluded.league_id,
                "startTime": stmt.excluded.startTime,
                "bo_count": stmt.excluded.bo_count,
                "blockName": stmt.excluded.blockName,
                "team_a": stmt.excluded.team_a,
                "team_b": stmt.excluded.team_b,
            },
        )
        instance.session.execute(stmt)
    instance.session.commit()


def fetch_leagues():
    """Downloads all the leagues and inserts them in the database."""
    # The league endpoint
    instance.logger.info('Fetching Leagues...')
    url = "https://esports-api.service.valorantesports.com/persisted/val/getLeagues?hl=en-US&sport=val"
    try:
        payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
        response = requests.get(url, headers=payload)
        data = response.json()["data"]["leagues"]
        for league_dict in data:
            league = League(**{k: league_dict[k] for k in dir(League) if k in league_dict})
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


def get_league_by_name(league_name):
    """Returns a League object based on its slug.

    Args:
        league_slug (str): The league's slug.

    Returns:
        League: A single League object.
    """
    try:
        return instance.session.execute(select(League).where(League.name == league_name)).one()[0]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting a league from the database: {e}')


def get_league_by_id(league_id):
    """Returns a League object based on its slug.

    Args:
        league_slug (str): The league's slug.

    Returns:
        League: A single League object.
    """
    try:
        return instance.session.execute(select(League).where(League.id == league_id)).one()[0]
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


def get_alerts_by_channel_id(channel_id):
    """Get all the alerts for a specific channel.

    Args:
        channel_id (int): Identifier for the channel.
    """
    try:
        return [x[0] for x in instance.session.execute(select(Alert).where(Alert.channel_id == channel_id)).all()]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting an alert from the database: {e}')


async def fetch_events_and_teams():
    """Downloads events and teams from the Riot API. Then inserts it in the database.

    Returns:
        dict: the response of the API as a JSON
    """
    list_of_teams = []
    list_of_matches = []
    async with asyncio.TaskGroup() as tg:
        for league in get_leagues():
            tg.create_task(fetch_teams_from_league(league, list_of_teams, list_of_matches))

    upsert_teams(list_of_teams)
    upsert_matches(list_of_matches)
    instance.logger.info('Finished updating Matches and Teams !')


async def fetch_teams_from_league(league: League, list_of_teams, list_of_matches):
    """Gets all the teams from a specific league.

    Args:
        league_id (League): The League to extract teams from.
    """
    url = "https://esports-api.service.valorantesports.com/persisted/val/getSchedule?hl=en-US&sport=val&leagueId="
    headers = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
    try:
        async with instance.http_client.get(f'{url}{league.id}', headers=headers) as response:
            data = await response.json()
            data = data["data"]
            print(data)
            # Going through all the teams in the upcoming events
            for i in data["schedule"]["events"]:
                # Creating both teams and flushing them to the DB
                team_a_dict = i["match"]["teams"][0]
                team_a = Team(**{k: team_a_dict[k] for k in dir(League) if k in team_a_dict})
                list_of_teams.append(team_a)

                team_b_dict = i["match"]["teams"][1]
                team_b = Team(**{k: team_b_dict[k] for k in dir(League) if k in team_b_dict})
                list_of_teams.append(team_b)

                match_dict = i["match"]
                match = Match(
                    id=match_dict["id"],
                    league_id=league.id,
                    startTime=datetime.strptime(i["startTime"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(tz=None),
                    bo_count=i["match"]["strategy"]["count"],
                    blockName=i["blockName"],
                    team_a=team_a.name,
                    team_b=team_b.name
                )
                list_of_matches.append(match)
    except KeyError as e:
        instance.logger.error(f'Error while parsing Riot API data : {e}. Riots API responded with the following response code : {response.status} and data {await response.json()}')
    except AttributeError as e:
        instance.logger.error(f'Problem with parsing team : {e}')
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
        if os.getenv('DEPLOYED') == 'production':
            in_5_mins = datetime.now() + timedelta(minutes=5)
            instance.logger.info(f'Checking for new matches in between {datetime.now()} and {in_5_mins}')
            return [x[0] for x in instance.session.execute(select(Match).where(in_5_mins > Match.startTime, Match.startTime > datetime.now())).all()]
        else:
            return [x[0] for x in instance.session.execute(select(Match).where(Match.startTime > datetime.now())).all()][0:5]
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


def create_league_alert(league, channel_id):
    """Creates an Alert to get notifications for a specific League.

    Args:
        league_name (str): The League's name.
        channel_id (int): Integer representing a single Discord channel.

    Returns:
        Alert: The Alert object created.
    """
    instance.logger.info(f'Creating an alert for league: {league} in channel id: {channel_id}')
    try:
        if (a := instance.session.execute(select(Alert).where(Alert.channel_id == channel_id, Alert.league_id == league.id)).first()) is not None:
            instance.logger.info(f'Alert for league {league} already exists, sending the existing Alert object.')
            return a[0]
        else:
            alert = Alert(channel_id=channel_id, league_id=league.id, team_name=None)
            league.alerts.append(alert)
            instance.session.add(alert)
            instance.session.commit()
            instance.logger.info('Successfully created an alert !')
        return alert
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while creating alert: {str(e)}')
        raise discord.ext.commands.errors.CommandError


def create_team_alert(team, channel_id):
    """Creates an Alert to get notifications for a specific Team.

    Args:
        team (str): The Team object
        channel_id (int): Integer representing a single Discord channel.

    Returns:
        Alert: The Alert object created.
    """
    instance.logger.info(f'Creating an alert for team : {team} in channel id: {channel_id}')
    try:
        if (a := instance.session.execute(select(Alert).where(Alert.channel_id == channel_id, Alert.team_name == team.name)).first()) is not None:
            instance.logger.info(f'Alert for team {team} already exists, sending the existing Alert object.')
            return a[0]
        else:
            alert = Alert(channel_id=channel_id, team_name=team.name, league_id=None)
            team.alerts.append(alert)
            instance.session.add(alert)
            instance.session.commit()
            instance.logger.info('Successfully created an alert !')
        return alert
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while creating alert: {str(e)}')
        raise discord.ext.commands.errors.CommandError


def get_alerts_teams(team_a, team_b):
    """Retrieves Alert objects from the database based on the Team the Alert follows.

    Args:
        team_a (str): One of the Team's names facing each other.
        team_b (str): One of the Team's names facing each other.

    Returns:
        List[Alert]: List of alerts
    """
    return [x[0] for x in instance.session.execute(select(Alert).where((Alert.team_name == team_a) | (Alert.team_name == team_b))).all()]


def get_alerts_team(team_name):
    """Retrieves Alert objects from the database based on the Team the Alert follows.

    Args:
        team_a (str): One of the Team's names facing each other.
        team_b (str): One of the Team's names facing each other.

    Returns:
        List[Alert]: List of alerts
    """
    return [x[0] for x in instance.session.execute(select(Alert).where(Alert.team_name == team_name)).all()]


def get_alerts_league(league):
    """Retrieves Alert objects from the database based on the League the Alert follows.

    Args:
        league (League): League of the League object

    Returns:
        List[Alert]: List of alerts
    """
    instance.logger.info(f'Getting alerts for league {league}')
    return [x[0] for x in instance.session.execute(select(Alert).where(Alert.league_id == league.id)).all()]


async def embed_alert(match):
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
        title=f'{match.team_a} ⚔️ {match.team_b}',
        description=f'{match.league.name} · {match.blockName} · BO{match.bo_count}',
        color=discord.Colour.red(),
    )

    embed.set_footer(text=f'Starts at {match.startTime.replace(tzinfo=datetime.now().astimezone().tzinfo).astimezone(tz=timezone.utc).strftime("%-I:%M")} · UTC · {match.startTime.strftime("%A %-d")}')

    if match.team_a in instance.referential["teams"] and instance.referential["teams"][match.team_a] != "":
        embed.add_field(name=f'{match.team_a}\'s stream', value=f'[Link]({instance.referential["teams"][match.team_a]})', inline=True)

    if match.league.name in instance.referential["leagues"] and instance.referential["leagues"][match.league.name] != "":
        embed.add_field(name="Official stream", value=f'[Link]({instance.referential["leagues"][match.league.name]})', inline=True)

    if match.team_b in instance.referential["teams"] and instance.referential["teams"][match.team_b] != "":
        embed.add_field(name=f'{match.team_b}\'s stream', value=f'[Link]({instance.referential["teams"][match.team_b]})', inline=True)

    embed.set_thumbnail(url=f'{match.league.image}')
    return embed


async def send_match_alert(channel_id, match):
    """Sends an alert to a specified channel_id for a specific Match.

    Args:
        channel_id (int): Integer representing a single Discord channel.
        match (Match): Match object for which we wish to send an Alert.
    """
    channel = instance.bot.get_channel(channel_id)
    await channel.send(embed=await embed_alert(match))


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
