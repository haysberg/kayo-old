import discord
from sqlalchemy import ForeignKey, UniqueConstraint, select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kayo.model import Base
from kayo.league import League
from kayo.team import Team


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

from kayo import instance

def create_league_alert(league, channel_id):
    """Creates an Alert to get notifications for a specific League.

    Args:
        league (str): The League object.
        channel_id (int): Integer representing a single Discord channel.

    Returns:
        Alert: The Alert object created.
    """
    instance.logger.info(f'Creating an alert for league: {league} in channel id: {channel_id}')
    try:
        if (a := instance.session.execute(select(Alert).where(Alert.channel_id == channel_id, Alert.league_id == league.id)).first()) is not None:
            instance.logger.info(f'Alert for league {league} already exists, sending the existing Alert object : {a}')
            return a[0]
        else:
            alert = Alert(channel_id=channel_id, league_id=league.id, team_name=None)
            league.alerts.append(alert)
            instance.session.add(alert)
            instance.session.commit()
            instance.logger.info('Successfully created an alert : {alert} !')
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


def get_alerts_by_channel_id(channel_id):
    """Get all the alerts for a specific channel.

    Args:
        channel_id (int): Identifier for the channel.
    """
    try:
        return [x[0] for x in instance.session.execute(select(Alert).where(Alert.channel_id == channel_id)).all()]
    except SQLAlchemyError as e:
        instance.logger.error(f'Error while getting an alert from the database: {e}')


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
