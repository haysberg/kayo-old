from typing import List
from typing import Optional

from sqlalchemy import Column, UniqueConstraint, select
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column()
    league_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leagues.id"))
    team_name: Mapped[Optional[str]] = mapped_column(ForeignKey("teams.name"))
    __table_args__ = (UniqueConstraint('channel_id', 'league_id', name='channel_league_alert_uc'), UniqueConstraint('channel_id', 'team_name', name='channel_team_alert_uc'))

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    startTime: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    bo_count: Mapped[int] = mapped_column()
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    team_a: Mapped[str] = mapped_column(ForeignKey("teams.name"))
    team_b: Mapped[str] = mapped_column(ForeignKey("teams.name"))

class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    slug: Mapped[str] = mapped_column(String(60))
    region: Mapped[str] = mapped_column(String(60))
    image: Mapped[str] = mapped_column(String(500))

class Team(Base):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(60), primary_key=True)
    code: Mapped[str] = mapped_column(String(60))
    image: Mapped[str] = mapped_column(String(500))