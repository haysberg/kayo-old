"""Contains the dataclass for Teams and useful functions."""
import discord
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

import kayo
from kayo import instance
from kayo.model import Base


class Team(Base):
    """Represents a Team.

    Args:
        kayo.model.Base: Base class.
    """

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(60), primary_key=True)
    image: Mapped[str] = mapped_column(String(500))
    alerts: Mapped[list["kayo.alert.Alert"]] = relationship(
        default_factory=list, back_populates="teams"
    )


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
