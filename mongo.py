from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import re, os

client = MongoClient("mongodb+srv://admin:admin@ridemap.o2xus.mongodb.net/")

try:
    client.admin.command('ismaster')
    print("Connected successfully!!!")
except ConnectionFailure as e:
    print(f"Could not connect to MongoDB: {e}")
    exit(1)

db = client["UNISYS"]
notesdb = db["NOTES"]