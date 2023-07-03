import os
import logging
import sys
from pymongo import MongoClient
import discord
import dotenv
import requests

# Initializing core objects
dotenv.load_dotenv()
bot = discord.Bot()

def get_database():
   db = MongoClient(os.getenv("MONGO_URI"))

   return db['users']

def insert_into_db(user_id, item):
    dbname = get_database()
    collection_name = dbname[user_id]
    collection_name.insert_many([item])


def fetch_leagues():
    # The league endpoint
    url = "https://esports-api.service.valorantesports.com/persisted/val/getLeagues?hl=fr-FR&sport=val"
    payload = {"x-api-key": os.getenv("RIOT_API_KEY")}
    response = requests.get(url, headers=payload)
    return response.json()

#return [id, name, region]
def list_leagues():
    leagues = fetch_leagues()
    return_leagues = {}
    for league in leagues["data"]["leagues"]:
        return_leagues[league["name"]] = [league["id"], league["name"],league["region"]]
    return return_leagues

#all leagues
leagues = list_leagues()

# Logging
logger = logging.getLogger('discord')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
logger.addHandler(handler)

@bot.event
async def on_ready():
    logging.info(f"{bot.user} is ready and online! 🚀")

@bot.event
async def on_disconnect():
    logging.error(f"{bot.user} is going offline ! 💣")

@bot.slash_command()
async def hello(ctx, name: str = None):
    name = name or ctx.author.name
    await ctx.respond(f"Hello {name}!")

@bot.command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    latency_ms = round(bot.latency * 1000)
    await ctx.respond(f"Pong! Latency is {latency_ms} ms")

@bot.command(description="Subscribe the channel to a league.")
async def add(ctx, league: str):
    if league == None or league not in leagues:
        await ctx.respond(f"Please specify a league!")
        return
    item_1 = {
    "channelID" : str(ctx.channel.id),
    "leagueID" : leagues[league][0],
    "leagueName" : leagues[league][1],
    "leagueRegion" : leagues[league][2]
    }
    insert_into_db("alerts", item_1)
    await ctx.respond(f"Added !👍")

bot.run(os.getenv("DISCORD_TOKEN"))