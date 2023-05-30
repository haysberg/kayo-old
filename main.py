import os
import logging
import sys
from pymongo import MongoClient
import discord
import dotenv

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

@bot.command(description="Subscribe the user to a league.")
async def add(ctx):
    item_1 = {
    "league" : "trofor",
    "match" : "2"
    }
    insert_into_db(str(ctx.author.id), item_1)
    await ctx.respond(f"Added!")

bot.run(os.getenv("DISCORD_TOKEN"))