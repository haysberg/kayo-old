import os
import logging
import sys
import discord
import dotenv
import kayo_lib
import requests

# Initializing core objects
dotenv.load_dotenv()
bot = discord.Bot()
subscribe = bot.create_group("subscribe", "Subscribing to leagues and teams")
listOfTeams = dict()
listOfLeagues = dict()

# Logging
logger = logging.getLogger('discord')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
logger.addHandler(handler)

# Fetching initial data
@bot.event
async def on_ready():
    for league in kayo_lib.fetch_leagues() :
        listOfLeagues[league["name"]] = league
    logging.info(f"Downloaded {len(listOfLeagues)} leagues.")
    logging.info(f"{bot.user} is online! 🚀")

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
    league: discord.Option(discord.SlashCommandOptionType.string, autocomplete=discord.utils.basic_autocomplete(listOfLeagues.keys()))
):
    await ctx.respond(f'League info : `{listOfLeagues[league]}` !')


# @bot.command(description="Subscribe the channel to a league.")
# async def add(ctx, league: str):
#     if league == None or league not in leagues:
#         await ctx.respond(f"Please specify a league!")
#         return
#     item_1 = {
#     "channelID" : str(ctx.channel.id),
#     "leagueID" : leagues[league][0],
#     "leagueName" : leagues[league][1],
#     "leagueRegion" : leagues[league][2]
#     }
#     insert_into_db("alerts", item_1)
#     await ctx.respond(f"Added !👍")

bot.run(os.getenv("DISCORD_TOKEN"))