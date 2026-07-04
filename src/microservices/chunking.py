from confluent_kafka import Consumer, Producer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

from pathlib import Path
import sys

base_dir=Path(__file__).parent.parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0,str(base_dir))

import asyncio

from src.config import consumer_conf, producer_conf

from mongo.database_functions import update_document,get_document

consumer = Consumer(consumer_conf)
producer = Producer(producer_conf)

consumer.subscribe(["document-loaded"])

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

async def main():
    while True:

        msg = consumer.poll(1)

        if msg is None:
            continue

        data=json.loads(msg.value().decode())

        content = data["content"]

        chunks = splitter.split_text(content)

        event = {
            "user_id": data["user_id"],
            "chunks": [
                {"chunk_id": str(idx), "chunk_text": chunk}
                for idx, chunk in enumerate(chunks)
            ]
        }

        producer.produce(
            "document-chunked",
            json.dumps(event)
        )
        
        document=await get_document(data["user_id"])

        document["stages"].append({
            "stage":"chunking",
            "status":"processed!"
        })
        await update_document(document)

        producer.flush()

        print(f"Created {len(chunks)} chunks")

asyncio.run(main())