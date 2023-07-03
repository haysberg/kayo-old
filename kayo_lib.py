import requests
import json
from pymongo import MongoClient
import os



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