from fastapi import FastAPI,UploadFile,File,Form
import shutil
from confluent_kafka import Producer
from src.config import producer_conf
import json

import os
from dotenv import load_dotenv
load_dotenv()


from mongo.database_functions import get_document
from src.microservices.query import QueryLLM

app = FastAPI()

producer = Producer(producer_conf)


@app.post("/upload")
async def upload(file:UploadFile=File,user_id:str=Form(...)):
    
    file_path=f"uploads/{file.filename}"

    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    if os.path.exists(file_path):
        return{"status":"file already exists!"}

    with open(file_path,"wb") as f:
        shutil.copyfileobj(file.file,f)
        
    event = {
        "file_path": file_path,
        "user_id":user_id
    }

    producer.produce(
        "document-uploaded",
        json.dumps(event)
    )

    producer.flush()

    return {
        "status": "Submitted and processing..."
    }


@app.get("/status/{user_id}")
async def get_status(user_id:str):

    try:
        document=await get_document(user_id)

        if document:
            return{
            "Status":document["stages"]
        }

        raise ValueError()
        
    except ValueError as e:
        return{
            "Status":"Document not found!"
        }


@app.post("/chat")
async def chat(query:str):

    try:
        LLM=QueryLLM()
        print("Retrieving context...")

        await LLM.context_retriever(query)
        print("Context retrieved successfully")

        print("Querying LLM...")
        response=await LLM.query_llm()
        print("LLM queried successfully")

        return{
            "response":response
        }
        
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return{
            "response":"Sorry, I can't answer that question"
        }

