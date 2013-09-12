from pymongo import MongoClient

client = MongoClient()
db = client.oryx
cache = db.cache