import discord
from sqlalchemy import String, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, relationship

import kayo
from kayo.model import Base
from kayo import instance



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
            instance.logger.info(f'Alert for team {team} already exists, sending the existing Alert object : {a}')
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
