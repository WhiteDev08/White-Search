import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain_pinecone import PineconeVectorStore

import sys
from pathlib import Path
base_dir=Path(__file__).parent.parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0,str(base_dir))

class QueryLLM:

    def __init__(self):
        self.embedding_model=GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        self.llm=init_chat_model("google_genai:gemini-2.5-flash")
        self.db=PineconeVectorStore(index_name=os.getenv("INDEX_NAME"),embedding=self.embedding_model)
        self.query=""
        self.context=""

    
    async def context_retriever(self,query:str):

        try:
            response=self.db.similarity_search(query,k=3)
            self.context="\n".join([r.page_content for r in response])
            self.query=query
            print("Context retrieved successfully")
            print(self.context)

        except Exception as e:
            print(f"Error retrieving context: {e}")
            self.context="No context found"

    async def query_llm(self):

        try:

            basic_prompt=f""" You are a helpful assistant that can answer questions about the following context:
            {self.context}
            Question: {self.query}
            Answer:
            """

            response=await self.llm.ainvoke(basic_prompt)
            return response.content

        except Exception as e:
            print(f"Error querying LLM: {e}")
            return "Sorry, I can't answer that question"


