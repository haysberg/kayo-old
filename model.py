"""_summary_."""
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import MappedAsDataclass
from sqlalchemy.orm import relationship


class Base(MappedAsDataclass, DeclarativeBase):
    """Base SQLalchemy Class.

    Args:
        DeclarativeBase (sqlalchemy.orm.DeclarativeBase): Don't question it.
    """

    pass


class League(Base):
    """An object used to represent a League.

    Args:
        Base: Base class.
    """

    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    region: Mapped[str] = mapped_column(String(60))
    image: Mapped[str] = mapped_column(String(500))
    alerts: Mapped[list["Alert"]] = relationship(
        default_factory=list, back_populates="leagues"
    )

    def __repr__(self) -> str:
        """Formats the representation when using print() for example.

        Returns:
            str: Description of self.
        """
        return f"League(id={self.id!r}, name={self.name!r}, slug={self.slug!r}), region={self.region!r})"


class Team(Base):
    """Represents a Team.

    Args:
        Base: Base class.
    """

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(60), primary_key=True)
    image: Mapped[str] = mapped_column(String(500))
    alerts: Mapped[list["Alert"]] = relationship(
        default_factory=list, back_populates="teams"
    )


class Alert(Base):
    """A Class used to represent an alert.

    Args:
        Base (kayo.Base): Default ORM Base Class.
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    channel_id: Mapped[int] = mapped_column()
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=True)
    team_name: Mapped[str] = mapped_column(ForeignKey("teams.name"), nullable=True)

    leagues: Mapped[League] = relationship(default=None)
    teams: Mapped[Team] = relationship(default=None)

    __table_args__ = (UniqueConstraint('channel_id', 'league_id', name='channel_league_alert_uc'), UniqueConstraint('channel_id', 'team_name', name='channel_team_alert_uc'))

    def is_team_alert(self):
        """Checks if an alert is for a Team.

        Returns:
            Boolean: If an alert is for a Team.
        """
        return self.team_name is not None


class Match(Base):
    """Represents a Match between two teams.

    Args:
        Base: Base class
    """

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leagues.id"))
    startTime: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    bo_count: Mapped[int] = mapped_column(String(60))
    blockName: Mapped[str] = mapped_column(String(60))
    team_a: Mapped[str] = mapped_column(ForeignKey("teams.name"))
    team_b: Mapped[str] = mapped_column(ForeignKey("teams.name"))

    league: Mapped[League] = relationship(default=None)
