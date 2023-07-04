import os
from typing import List

import discord
import requests
from sqlalchemy import select
import logging
import sys
import os
import discord
import dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from model import Base

import sqlalchemy as db

from model import League

class BotContext:
    def __init__(self):
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
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
        self.logger.addHandler(handler)