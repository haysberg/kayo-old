"""_summary_."""
import asyncio
import os
from datetime import datetime
from datetime import timezone

import discord

import kayo
from kayo import instance
from kayo.league import fetch_leagues
from kayo.league import get_leagues
from kayo.league import League
from kayo.match import Match
from kayo.match import upsert_matches
from kayo.team import Team


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

    kayo.team.upsert_teams(list_of_teams)
    upsert_matches(list_of_matches)
    instance.logger.info('Finished updating Matches and Teams !')


async def fetch_teams_from_league(league: League, list_of_teams, list_of_matches):
    """Gets teams and matches from a League.

    Args:
        league (League): The League object to extract into from.
        list_of_teams (List[Team]): List of Teams to be upserted in the DB later.
        list_of_matches (List[Matches]): List of Matches to be upserted in the DB later.
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


async def embed_alert(match):
    """Creates a discord.Embed object to be sent by send_match_alert().

    Args:
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
