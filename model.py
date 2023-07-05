"""_summary_."""
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    """_summary_.

    Args:
        DeclarativeBase (_type_): _description_
    """

    pass


class Alert(Base):
    """_summary_.

    Args:
        Base (_type_): _description_
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column()
    league_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leagues.id"))
    team_name: Mapped[Optional[str]] = mapped_column(ForeignKey("teams.name"))

    __table_args__ = (UniqueConstraint('channel_id', 'league_id', name='channel_league_alert_uc'), UniqueConstraint('channel_id', 'team_name', name='channel_team_alert_uc'))

    def is_team_alert(self):
        return self.team_name != None


class Match(Base):
    """_summary_.

    Args:
        Base (_type_): _description_
    """

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    startTime: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    bo_count: Mapped[int] = mapped_column()
    league_slug: Mapped[int] = mapped_column(ForeignKey("leagues.slug"))
    team_a: Mapped[str] = mapped_column(ForeignKey("teams.name"))
    team_b: Mapped[str] = mapped_column(ForeignKey("teams.name"))


class League(Base):
    """_summary_.

    Args:
        Base (_type_): _description_
    """

    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    region: Mapped[str] = mapped_column(String(60))
    image: Mapped[str] = mapped_column(String(500))

    def __repr__(self) -> str:
        """_summary_.

        Returns:
            str: _description_
        """
        return f"League(id={self.id!r}, name={self.name!r}, slug={self.slug!r}), region={self.region!r})"


class Team(Base):
    """_summary_.

    Args:
        Base (_type_): _description_
    """

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(60), primary_key=True)
    code: Mapped[str] = mapped_column(String(60), nullable=True)
    image: Mapped[str] = mapped_column(String(500))
