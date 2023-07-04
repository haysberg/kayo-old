import requests
import json
from pymongo import MongoClient
import os
import discord



def get_database():
   db = MongoClient(os.getenv("MONGO_URI"))
   return db['users']

def insert_into_db(user_id, item):
    dbname = get_database()
    collection_name = dbname[user_id]
    collection_name.insert_many([item])

def fetch_leagues():
    # The league endpoint
    url = "https://esports-api.service.valorantesports.com/persisted/val/getLeagues?hl=en-US&sport=val"
    payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
    response = requests.get(url, headers=payload)
    return response.json()["data"]["leagues"]

def fetch_events(listOfLeagues):
    url = 'https://esports-api.service.valorantesports.com/persisted/val/getSchedule?hl=en-US&sport=val&leagueId='
    for league in listOfLeagues :
        url = url + f'{listOfLeagues[league]["id"]},'
    url = url[:-1]
    payload = {"X-Api-Key": os.getenv("RIOT_API_KEY")}
    response = requests.get(url, headers=payload)

    print(url)

    return response.json()["data"]["schedule"]["events"]

async def embed_league(team_a, team_b, league, match):
    embed = discord.Embed(
        title=f'{team_a["name"]} ⚔️ {team_b["name"]}',
        description=f'{league["name"]} - BO{match["strategy"]["count"]}',
        color=discord.Colour.red(),
    )

    embed.add_field(name="Inline Field 1", value="Inline Field 1", inline=True)
    embed.add_field(name="Inline Field 2", value="Inline Field 2", inline=True)
    embed.add_field(name="Inline Field 3", value="Inline Field 3", inline=True)
 
    # embed.set_footer(text="Coucou") # footers can have icons too
    # embed.set_author(name="Team", icon_url="https://example.com/link-to-my-image.png")
    # embed.set_thumbnail(url="https://example.com/link-to-my-thumbnail.png")
    embed.set_image(url=f'{league["image"]}')
 
    return embed