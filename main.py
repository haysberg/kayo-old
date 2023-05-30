import os
import logging
import sys

import discord
import dotenv

# Initializing core objects
dotenv.load_dotenv()
bot = discord.Bot()

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

bot.run(os.getenv("DISCORD_TOKEN"))