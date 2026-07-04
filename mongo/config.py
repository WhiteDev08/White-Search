from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

MONGO_CONNECTION_STRING=os.getenv("MONGO_CONNECTION_STRING")
MONGO_DATABASE_NAME=os.getenv("MONGO_DATABASE_NAME")
MONGO_COLLECTION_NAME=os.getenv("MONGO_COLLECTION_NAME")

client=MongoClient(MONGO_CONNECTION_STRING)
db=client[MONGO_DATABASE_NAME]
collection=db[MONGO_COLLECTION_NAME]
