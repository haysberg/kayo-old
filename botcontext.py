"""_summary_."""
import logging
import sys

import discord
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Base


class BotContext:
    """_summary_."""

    def __init__(self):
        """_summary_."""
        self.engine = (create_engine("sqlite://"))
        Session = sessionmaker(bind=self.engine)

        global session
        self.session = Session()
        Base.metadata.create_all(self.engine)

        # Initializing core objects
        dotenv.load_dotenv()
        self.bot = discord.Bot()
        self.subscribe = self.bot.create_group("subscribe", "Subscribing to leagues and teams")

        # Logging
        self.logger = logging.getLogger('discord')
        self.logger = logging.getLogger()
        logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
        self.logger.addHandler(handler)
