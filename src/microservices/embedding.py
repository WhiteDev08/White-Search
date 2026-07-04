from confluent_kafka import Consumer
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
import os
from dotenv import load_dotenv
load_dotenv()
import json

import sys
from pathlib import Path
base_dir=Path(__file__).parent.parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0,str(base_dir))

import asyncio

from src.config import consumer_conf
from mongo.database_functions import update_document,get_document

consumer = Consumer(consumer_conf)

consumer.subscribe(["document-chunked"])

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

async def main():
    while True:

        msg = consumer.poll(1)

        if msg is None:
            continue

        data = json.loads(msg.value().decode())

        user_id = data["user_id"]
        chunks = data["chunks"]

        documents = [
            Document(page_content=chunk["chunk_text"], metadata={"user_id": user_id})
            for chunk in chunks
        ]
        ids = [f"{user_id}_{chunk['chunk_id']}" for chunk in chunks]

        PineconeVectorStore.from_documents(
            documents,
            embedding=embeddings,
            index_name=os.getenv("INDEX_NAME"),
            ids=ids,
        )

        document = await get_document(user_id)

        document["stages"].append({
            "stage": "embedding",
            "status": "processed!"
        })
        await update_document(document)

        print(f"Stored {len(chunks)} chunks")

asyncio.run(main())