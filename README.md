# 🔍 White Search

A production-style Retrieval-Augmented Generation (RAG) system built on an event-driven architecture. Users upload documents through a web interface; the backend processes them asynchronously via Kafka, persists workflow state in MongoDB, stores vector embeddings in Pinecone, and serves grounded answers through a Gemini-powered query layer.

## Overview

This project demonstrates how to build a decoupled, scalable RAG pipeline without monolithic processing. The API layer accepts requests and publishes events — it never blocks on heavy work. Dedicated microservice workers consume those events, transform documents through each stage, and update shared state as they progress. The frontend communicates exclusively with REST endpoints, keeping the UI independent from backend internals.

**Stack:** FastAPI · Kafka · MongoDB · Pinecone · LangChain · Google Gemini · Streamlit

## How It Works

```
Client (Streamlit)
       │
       ▼
  FastAPI Gateway
       │
       ├── POST /upload ──▶ Kafka: document-uploaded
       │                          │
       │                          ▼
       │                    Ingestion Service ──▶ MongoDB (stage: ingestion)
       │                          │
       │                          ▼
       │                    Kafka: document-loaded
       │                          │
       │                          ▼
       │                    Chunking Service ──▶ MongoDB (stage: chunking)
       │                          │
       │                          ▼
       │                    Kafka: document-chunked
       │                          │
       │                          ▼
       │                    Embedding Service ──▶ Pinecone + MongoDB (stage: embedding)
       │
       ├── GET /status/{user_id} ──▶ MongoDB (read pipeline state)
       │
       └── POST /chat ──▶ Pinecone retrieval ──▶ Gemini LLM
```

1. **Upload** — User submits a document with a unique ID. FastAPI saves the file and emits a `document-uploaded` event to Kafka, returning immediately.
2. **Ingestion** — Worker loads the file content and forwards it to the next topic. MongoDB record is created with the first stage marked complete.
3. **Chunking** — Worker splits text into overlapping chunks and publishes each chunk individually.
4. **Embedding** — Worker generates vector embeddings and upserts them into Pinecone. Final stage is recorded in MongoDB.
5. **Status** — Client polls `/status/{user_id}` to see which stages have completed.
6. **Query** — Client sends a question to `/chat`. Relevant chunks are retrieved from Pinecone and passed to Gemini for a context-aware answer.

## Features

- Asynchronous document ingestion with immediate API response
- Loosely coupled microservices communicating via Kafka topics
- Per-user pipeline state persisted and queryable in MongoDB
- Vector similarity search over embedded document chunks
- LLM-generated answers grounded in retrieved context
- Streamlit frontend with upload, query, and status pages

Failure recovery (retries, dead-letter queues, idempotent replays) is **not implemented** for now — the event-driven layout is set up so these can be extended later.

## 📁 Project Structure

```
RAG/
├── frontend/
│   └── app.py                  # Streamlit UI — consumes FastAPI endpoints
├── mongo/
│   ├── config.py               # MongoDB connection
│   └── database_functions.py   # Read/write user stage documents
├── src/
│   ├── main.py                 # FastAPI gateway
│   ├── config.py               # Kafka producer/consumer configuration
│   └── microservices/
│       ├── ingestion.py        # document-uploaded → document-loaded
│       ├── chunking.py         # document-loaded → document-chunked
│       ├── embedding.py        # document-chunked → Pinecone
│       └── query.py            # Retrieval + LLM inference
├── requirements.txt
├── rav.yaml                    # Run scripts (rav run <script>)
└── .env
```

## Concepts

| Concept | Application |
|---|---|
| **Event-driven workflow** | Services communicate through Kafka topics instead of direct calls. Each worker subscribes to one topic and publishes to the next, enabling independent scaling and failure isolation. |
| **Async orchestration** | The upload endpoint returns before processing finishes. Long-running steps (load, split, embed) execute in background workers, coordinated by events rather than synchronous chains. |
| **Stateful workflow** | MongoDB maintains a document per user tracking completed stages. Workers append stage entries as they finish, giving clients a reliable view of pipeline progress. |
| **MongoDB** | Stores `{ user_id, stages: [{ stage, status }] }` — the single source of truth for ingestion state across all microservices. |

## Multi-document vector storage

All uploads share a **single Pinecone index**. Pinecone identifies vectors by ID, not by document — so chunk IDs must be unique across the whole index, not just within one upload.

The embedding service stores each chunk via `PineconeVectorStore.from_documents` with:

- **Vector ID:** `{user_id}_{chunk_index}` (e.g. `ke_1234_0`, `ke_1234_1`) — prevents different uploads from overwriting each other
- **Metadata:** chunk text and `user_id` for traceability

Query retrieval is **global**: `/chat` runs similarity search across the entire index, so answers can draw from any uploaded document. Re-uploading under the same `user_id` replaces that user's previous vectors at the same IDs.

## 🔑 Environment Variables

Create a `.env` file in the project root:

```
PINECONE_API_KEY
GOOGLE_API_KEY
SSL_CA_LOCATION
SSL_CERT_LOCATION
SSL_KEY_LOCATION
BOOTSTRAP_SERVERS
GROUP_ID
INDEX_NAME
MONGO_USERNAME
MONGO_PASSWORD
MONGO_CONNECTION_STRING
MONGO_DATABASE_NAME
MONGO_COLLECTION_NAME
```

## Aiven Kafka Setup

This project uses [Aiven](https://aiven.io/) for managed Kafka with SSL authentication. You'll need connection details and certificate files before the pipeline can publish or consume events.

1. Log in to the [Aiven Console](https://console.aiven.io/) and open your Kafka service.
2. Go to the **Overview** tab — copy the **Bootstrap server** address into `BOOTSTRAP_SERVERS`.
3. Open the **Connection information** section:
   - Download the **CA certificate** → save as `ca.pem` → set `SSL_CA_LOCATION`
   - Under **Access keys**, create or select a service user and download the **Access certificate** and **Access key** → save as `service.cert` and `service.key` → set `SSL_CERT_LOCATION` and `SSL_KEY_LOCATION` accordingly.
4. Create the required Kafka topics in the Aiven console (or via CLI): `document-uploaded`, `document-loaded`, `document-chunked`.

Point each env variable to the absolute path of the downloaded file on your machine.

## 🚀 Getting Started

**1. Create and activate a virtual environment**

```cmd
python -m venv venv
venv\Scripts\activate
```

**2. Install dependencies**

```cmd
pip install -r requirements.txt
```

**3. Start the services** (each in its own terminal, from project root)

FastAPI gateway:

```cmd
rav run server
```

Microservice workers:

```cmd
rav run ingestion
```

```cmd
rav run chunking
```

```cmd
rav run embedding
```

Streamlit frontend:

```cmd
rav run frontend
```

Scripts are defined in `rav.yaml`. List all available commands with:

```cmd
rav run
```

**4. Open the app** 🌐

- API docs → [http://localhost:8000/docs](http://localhost:8000/docs)
- Frontend → [http://localhost:8501](http://localhost:8501)

---

This project is a practical reference for wiring together modern AI infrastructure — not a toy script, but a working pattern you can extend. The separation between API, workers, state store, and vector DB is intentional: it mirrors how production RAG systems handle scale, fault tolerance, and observability. Use it as a starting point to experiment with additional stages, retry logic, dead-letter queues, or deployment to containers.

---
### 🚀 Implementation

<img width="1423" height="491" alt="image" src="https://github.com/user-attachments/assets/e762c6fd-1912-4238-996d-88cfff074cf2" />
<img width="1462" height="827" alt="image" src="https://github.com/user-attachments/assets/91a4ceac-3e14-4656-aedb-80e86b1161e4" />
<img width="1397" height="813" alt="image" src="https://github.com/user-attachments/assets/d3900203-f9e4-431d-abe9-59b36a63ec9b" />
<img width="1420" height="813" alt="image" src="https://github.com/user-attachments/assets/55af6cb9-f5cf-4a37-b1df-5c9d1fff858f" />
