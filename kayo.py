import json
import os
from typing import List
from typing import Optional

import discord
import requests
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from types import SimpleNamespace

class Base(DeclarativeBase):
    pass

class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    slug: Mapped[str] = mapped_column(String(60))
    region: Mapped[str] = mapped_column(String(60))
    image: Mapped[str] = mapped_column(String(500))

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    startTime: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    bo_count: Mapped[int] = mapped_column()
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    team_a: Mapped[str] = mapped_column(ForeignKey("teams.name"))
    team_b: Mapped[str] = mapped_column(ForeignKey("teams.name"))

class Team(Base):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(60), primary_key=True)
    code: Mapped[str] = mapped_column(String(60))
    image: Mapped[str] = mapped_column(String(500))

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column()
    league_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leagues.id"))
    team_name: Mapped[Optional[str]] = mapped_column(ForeignKey("teams.name"))
    __table_args__ = (UniqueConstraint('channel_id', 'league_id', name='channel_league_alert_uc'), UniqueConstraint('channel_id', 'team_name', name='channel_team_alert_uc'))


def get_database():
   db = MongoClient(os.getenv("MONGO_URI"))
   return db['users']

def insert_into_db(user_id, item):
    dbname = get_database()
    collection_name = dbname[user_id]
    collection_name.insert_many([item])

def fetch_leagues():
    # The league endpoint
    url = "https://esports-api.service.valorantesports.com/persisted/val/getLeagues?hl=en-US&sport=val"
    payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
    response = requests.get(url, headers=payload)
    data = response.json()["data"]["leagues"]
    all_leagues:List[League] = list()
    for league_dict in data :
        league = League(**{k: league_dict[k] for k in ('id', 'name', 'slug', 'region', 'image') if k in league_dict})
        all_leagues.append(league)
    return all_leagues

def fetch_events(listOfLeagues):
    url = 'https://esports-api.service.valorantesports.com/persisted/val/getSchedule?hl=en-US&sport=val&leagueId='
    for league in listOfLeagues :
        url = url + f'{listOfLeagues[league]["id"]},'
    url = url[:-1]
    payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
    response = requests.get(url, headers=payload)

    print(url)

    return response.json()["data"]["schedule"]["events"]

async def embed_league(team_a, team_b, league, match):
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
