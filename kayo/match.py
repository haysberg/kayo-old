"""Contains the Match dataclass and functions to interact with it."""
import os
from datetime import datetime
from datetime import timedelta
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from kayo import instance
from kayo.league import League
from kayo.model import Base


class Match(Base):
    """Represents a Match between two teams.

    Args:
        kayo.model.Base: Base class
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
