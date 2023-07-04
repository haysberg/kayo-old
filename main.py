import logging
import os
import sys

import discord
import dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import sqlalchemy as db

import kayo

engine = (create_engine("sqlite://"))
Session = sessionmaker(bind=engine)
session = Session()
kayo.Base.metadata.create_all(engine)

# Initializing core objects
dotenv.load_dotenv()
bot = discord.Bot()
subscribe = bot.create_group("subscribe", "Subscribing to leagues and teams")

# Logging
logger = logging.getLogger('discord')
logger = logging.getLogger()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
logger.addHandler(handler)

# Fetching initial data
@bot.event
async def on_ready():
    for league in kayo.fetch_leagues():
        session.merge(league)
    session.commit()

    # logging.info(f"Downloaded {len(listOfLeagues)} leagues.")

    # listOfEvents = kayo.fetch_events(listOfLeagues)
    # logging.info(f"Downloaded {len(listOfEvents)} schedules.")

    # logging.info(f"{bot.user} is online! 🚀")

@bot.event
async def on_disconnect():
    logging.error(f"{bot.user} is disconnected ! 💣")

@bot.command(description="Sends the bot's latency.")
async def ping(ctx):
    latency_ms = round(bot.latency * 1000)
    await ctx.respond(f"Pong! Latency is {latency_ms} ms")

@subscribe.command(name="league", description="Subscribe to league alerts")
async def subscribe_league(
    ctx: discord.ApplicationContext,
    league: discord.Option(discord.SlashCommandOptionType.string, autocomplete=discord.utils.basic_autocomplete(select(kayo.League.)))
):
    if not ctx.author.guild_permissions.administrator :
        await ctx.respond(f'Sorry, only Administrators are allowed to run this command !')
    else :
        db.alerts_leagues.insert_one({"channel_id" : ctx.channel_id, "league_id" : listOfLeagues[league]["id"]})
        await ctx.respond(f'League info : `{listOfLeagues[league]}` !')

@subscribe.command(name="all_leagues", description="Subscribe to league alerts")
async def subscribe_all_leagues(
    ctx: discord.ApplicationContext
):
    if not ctx.author.guild_permissions.administrator :
        await ctx.respond(f'Sorry, only Administrators are allowed to run this command !')
    else :
        for league in listOfLeagues :
            db.alerts_leagues.insert_one({"channel_id" : ctx.channel_id, "league_id" : listOfLeagues[league]["id"]})
        await ctx.respond(f'Subscribed to {len(listOfLeagues)} different leagues !')

bot.run(os.getenv("DISCORD_TOKEN"))
