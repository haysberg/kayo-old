"""KAY/O Initialization module."""
import json
import logging
import os
import sys

import aiohttp
import discord
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

dotenv.load_dotenv()
LOGLEVEL = os.environ.get('LOGLEVEL').upper()


class BotContext:
    """Contains all the useful objects to interact with the database and the logger."""

    def __init__(self):
        """Creates all the objects."""
        LOGFORMAT = '%(asctime)s:%(levelname)s:%(message)s'
        logging.basicConfig(filename='./db/kayo.log', encoding='utf-8', level=LOGLEVEL, format=LOGFORMAT)
        self.logger = logging.getLogger('discord')
        self.logger.setLevel(level=LOGLEVEL)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
        self.logger.addHandler(handler)

        if LOGLEVEL == "DEBUG":
            logging.getLogger("sqlalchemy.engine").setLevel(level=LOGLEVEL)

        self.http_client = aiohttp.ClientSession()

        if os.getenv("DEPLOYED") == "production":
            self.engine = (create_engine("sqlite:///db/kayo.db"))
        else:
            self.engine = (create_engine("sqlite:///:memory:", echo=True))

        Session = sessionmaker(bind=self.engine)
        global session
        self.session = Session()

        # Initializing core objects
        if os.environ.get('DEPLOYED').upper() == "PRODUCTION":
            self.bot = discord.Bot()
        else:
            self.bot = discord.Bot(debug_guilds=[int(os.environ.get('DEBUG_GUILD'))])
        self.subscribe = self.bot.create_group("subscribe", "Subscribing to leagues and teams")
        self.unsubscribe = self.bot.create_group("unsubscribe", "Deleting alerts for leagues and teams")

        # Opening JSON file
        with open('./referential.json') as json_file:
            self.referential = json.load(json_file)


global instance
instance = BotContext()
