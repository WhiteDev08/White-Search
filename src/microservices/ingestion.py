from confluent_kafka import Consumer, Producer
from langchain_community.document_loaders import TextLoader
import json
import asyncio

import os
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path
base_dir=Path(__file__).parent.parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0,str(base_dir))

from src.config import producer_conf, consumer_conf
from mongo.database_functions import insert_document

consumer = Consumer(consumer_conf)
producer = Producer(producer_conf)

consumer.subscribe(["document-uploaded"])

async def main():
    while True:

        msg = consumer.poll(1)

        if msg is None:
            continue

        data = json.loads(msg.value().decode())

        file_path = data["file_path"]

        loader = TextLoader(file_path)

        docs = loader.load()

        event = {
            "user_id":data["user_id"],
            "file_path": file_path,
            "content": docs[0].page_content
        }
        
        document={
            "user_id":data["user_id"],
            "stages":[
                {
                    "stage":"ingestion",
                    "status":"processed!"
                }
            ]
        }

        await insert_document(document)

        producer.produce(
            "document-loaded",
            json.dumps(event)
        )

        producer.flush()

        print("Document Loaded")

asyncio.run(main())

