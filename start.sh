#!/bin/sh

python src/microservices/ingestion.py &
python src/microservices/embedding.py &
python src/microservices/chunking.py &
streamlit run frontend/app.py &
uvicorn src.main:app --host 0.0.0.0 --port 8000

wait