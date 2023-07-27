import os

import discord
import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, relationship
from kayo.model import Base
import kayo


from sqlalchemy import String, select


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
    alerts: Mapped[list["kayo.alert.Alert"]] = relationship(
        default_factory=list, back_populates="leagues"
    )

    def __repr__(self) -> str:
        """Formats the representation when using print() for example.

        Returns:
            str: Description of self.
        """
        return f"League(id={self.id!r}, name={self.name!r}, slug={self.slug!r}), region={self.region!r})"


def get_league_names(ctx: discord.AutocompleteContext = None):
    """Gets a list of all the League names currently in the database.

    Args:
        ctx (discord.AutocompleteContext, optional): Used when called from autocompletion. Defaults to None.

    Returns:
        List[str]: List of League names.
    """
    return [league.name for league in get_leagues()]


def get_league_by_id(league_id):
    """Returns a League object based on its slug.

    Args:
        league_id (str): The League's id number.

    Returns:
        League: A single League object.
    """
    try:
        return kayo.kayo.instance.session.execute(select(League).where(League.id == league_id)).one()[0]
    except SQLAlchemyError as e:
        kayo.kayo.instance.logger.error(f'Error while getting a league from the database: {e}')


def get_league_by_name(league_name):
    """Returns a League object based on its slug.

    Args:
        league_name (str): The League's name.

    Returns:
        League: A single League object.
    """
    try:
        return kayo.instance.session.execute(select(League).where(League.name == league_name)).one()[0]
    except SQLAlchemyError as e:
        kayo.instance.logger.error(f'Error while getting a league from the database: {e}')


def get_league_by_slug(league_slug):
    """Returns a League object based on its slug.

    Args:
        league_slug (str): The league's slug.

    Returns:
        League: A single League object.
    """
    try:
        return kayo.instance.session.execute(select(League).where(League.slug == league_slug)).one()[0]
    except SQLAlchemyError as e:
        kayo.instance.logger.error(f'Error while getting a league from the database: {e}')


def get_leagues(ctx: discord.AutocompleteContext = None):
    """Gets all the leagues currently in the database.

    Args:
        ctx (discord.AutocompleteContext, optional): Used when called from autocompletion.
        Defaults to None.

    Returns:
        List[League]: The list of leagues.
    """
    try:
        kayo.instance.logger.info('Getting all the leagues from DB...')
        return [x[0] for x in kayo.instance.session.execute(select(League)).all()]
    except SQLAlchemyError as e:
        kayo.instance.logger.error(f'Error while getting leagues from the database: {e}')


def fetch_leagues():
    """Downloads all the leagues and inserts them in the database."""
    # The league endpoint
    kayo.instance.logger.info('Fetching Leagues...')
    url = "https://esports-api.service.valorantesports.com/persisted/val/getLeagues?hl=en-US&sport=val"
    try:
        payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
        response = requests.get(url, headers=payload)
        data = response.json()["data"]["leagues"]
        for league_dict in data:
            league = League(**{k: league_dict[k] for k in dir(League) if k in league_dict})
            kayo.instance.session.merge(league)
        kayo.instance.session.commit()
    except requests.RequestException as e:
        kayo.instance.logger.error(f'Error while fetching the leagues: {e}')
    except SQLAlchemyError as e:
        kayo.instance.logger.error(f'Error while inserting leagues into the database: {e}')
