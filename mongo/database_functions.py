import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
from mongo.config import collection


async def insert_document(doc):

    try:
        print(f"Inserting document for user {doc['user_id']}")
        collection.insert_one({"user_id":doc['user_id'],"stages":doc['stages']})
        print(f"Document inserted for user {doc['user_id']}")
    except Exception as e:
        print(f"Error inserting document for user {doc['user_id']}: {e}")
        raise e

async def get_document(user_id):
    try:
        print(f"Getting document for user {user_id}")
        document = collection.find_one({"user_id":user_id})
        print(f"Document found!")
        return document
    
    except Exception as e:
        print(f"Error getting document for user {user_id}: {e}")
        raise e


async def update_document(doc):
    try:
        print(f"Updating document for user {doc['user_id']}")
        collection.update_one({"user_id":doc['user_id']},{"$set":{"stages":doc['stages']}})
        print(f"Document updated for user {doc['user_id']}")
    except Exception as e:
        print(f"Error updating document for user {doc['user_id']}: {e}")
        raise e
