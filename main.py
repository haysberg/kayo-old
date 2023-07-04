import os
import logging
import sys
import discord
import dotenv
import kayo_lib
from pymongo import MongoClient

# Initializing core objects
dotenv.load_dotenv()
db_client = MongoClient(os.getenv("MONGO_URI"))
db = db_client["kayo-testing"]
bot = discord.Bot()
subscribe = bot.create_group("subscribe", "Subscribing to leagues and teams")
listOfTeams = dict()
listOfLeagues = dict()
listOfEvents = []

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

    listOfEvents = kayo_lib.fetch_events(listOfLeagues)
    logging.info(f"Downloaded {len(listOfEvents)} schedules.")

    # print(listOfEvents)
    # for schedule in listOfEvents :
    #     for event in listOfEvents[schedule] :
    #         for match in event["events"]["match"][t]

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