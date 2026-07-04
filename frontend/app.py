"""
RAG Pipeline — Streamlit Frontend
Calls FastAPI endpoints only (never microservice functions directly).
"""

import json
from datetime import datetime

import requests
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Pipeline",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.chat-user {
    background: #334155;
    color: #f8fafc;
    padding: 0.85rem 1.1rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.5rem 0;
    max-width: 80%;
    margin-left: auto;
}
.chat-bot {
    background: #1e293b;
    color: #e2e8f0;
    padding: 0.85rem 1.1rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.5rem 0;
    max-width: 85%;
    border: 1px solid #334155;
}

.sidebar-brand {
    font-size: 1.3rem;
    font-weight: 700;
    color: #e2e8f0;
    padding: 0.5rem 0 1rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state defaults ───────────────────────────────────────────────────
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = "http://localhost:8000"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ── API helpers ──────────────────────────────────────────────────────────────
def api_upload(user_id: str, uploaded_file) -> dict:
    url = f"{st.session_state.api_base_url.rstrip('/')}/upload"
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "text/plain")}
    data = {"user_id": user_id}
    resp = requests.post(url, files=files, data=data, timeout=60)
    resp.raise_for_status()
    return resp.json()


def api_status(user_id: str) -> dict:
    url = f"{st.session_state.api_base_url.rstrip('/')}/status/{user_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def api_chat(query: str) -> dict:
    url = f"{st.session_state.api_base_url.rstrip('/')}/chat"
    resp = requests.post(url, params={"query": query}, timeout=120)
    resp.raise_for_status()
    return resp.json()


def serialize_status(data) -> str:
    """Pretty-print status payload, handling non-JSON-serializable values."""
    def default(o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return str(o)

    return json.dumps(data, indent=2, default=default)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-brand">🧠 RAG Pipeline</p>', unsafe_allow_html=True)
    st.caption("Event-driven document ingestion & retrieval")

    page = st.radio(
        "Navigate",
        ["ℹ️ Info", "📤 Upload", "💬 Query", "📊 Status"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**API Settings**")
    st.session_state.api_base_url = st.text_input(
        "FastAPI base URL",
        value=st.session_state.api_base_url,
        placeholder="http://localhost:8000",
    )

    if st.button("🔌 Test connection", use_container_width=True):
        try:
            r = requests.get(f"{st.session_state.api_base_url.rstrip('/')}/docs", timeout=5)
            if r.status_code == 200:
                st.success("API reachable")
            else:
                st.warning(f"API responded with {r.status_code}")
        except requests.RequestException as exc:
            st.error(f"Cannot reach API: {exc}")

    st.divider()
    st.caption("Powered by Kafka · MongoDB · Pinecone · Gemini")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — INFO
# ══════════════════════════════════════════════════════════════════════════════
if page == "ℹ️ Info":
    st.title("Retrieval-Augmented Generation Pipeline")
    st.caption(
        "Upload documents, track processing stages in real time, and ask questions "
        "grounded in your knowledge base — all through an event-driven Kafka workflow."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📤 Upload")
        st.write(
            "Submit a text document with your user ID. The file is sent to the "
            "`POST /upload` endpoint and published to Kafka for async processing."
        )
    with col2:
        st.subheader("📊 Status")
        st.write(
            "Monitor ingestion progress via `GET /status/{user_id}`. "
            "Stages tracked: ingestion → chunking → embedding."
        )
    with col3:
        st.subheader("💬 Query")
        st.write(
            "Ask natural-language questions through `POST /chat`. "
            "Context is retrieved from Pinecone and answered by Gemini."
        )

    st.markdown("### Pipeline Architecture")
    st.markdown(
        """
```
┌──────────┐    Kafka     ┌───────────┐    Kafka     ┌──────────┐    Kafka     ┌───────────┐
│  Upload  │ ──────────▶  │ Ingestion │ ──────────▶  │ Chunking │ ──────────▶  │ Embedding │
│ (FastAPI)│              │  Service  │              │  Service │              │  Service  │
└──────────┘              └───────────┘              └──────────┘              └───────────┘
      │                          │                          │                          │
      │                          └──────────────────────────┴──────────────────────────┘
      │                                                     │
      │                                              MongoDB (stages)
      │                                                     │
      └─────────────────────────────────────────────────────┴──▶ Pinecone (vectors)
                                                                    │
                                                              Query (FastAPI)
                                                                    │
                                                              Gemini LLM
```
"""
    )

    st.markdown("### API Endpoints")
    endpoints = [
        ("POST", "/upload", "Upload a document with user_id (multipart form)"),
        ("GET", "/status/{user_id}", "Get processing stages for a user"),
        ("POST", "/chat?query=...", "Ask a question and receive an LLM response"),
    ]
    for method, path, desc in endpoints:
        badge_color = {"POST": "#475569", "GET": "#10b981"}[method]
        st.markdown(
            f'<span style="background:{badge_color};color:white;padding:2px 8px;'
            f'border-radius:4px;font-size:0.8rem;font-weight:600;">{method}</span> '
            f'<code>{path}</code> — {desc}',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📤 Upload":
    st.title("📤 Upload Document")
    st.caption("Submit a text file for ingestion. Processing runs asynchronously via Kafka.")

    with st.form("upload_form", clear_on_submit=False):
        user_id = st.text_input(
            "User ID",
            placeholder="e.g. user_123",
            help="Unique identifier to track your documents and processing status.",
        )
        uploaded_file = st.file_uploader(
            "Choose a text file",
            type=["txt", "md", "csv", "json"],
            help="Supported formats: .txt, .md, .csv, .json",
        )
        submitted = st.form_submit_button("🚀 Upload & Process", use_container_width=True)

    if submitted:
        if not user_id.strip():
            st.error("Please enter a User ID.")
        elif uploaded_file is None:
            st.error("Please select a file to upload.")
        else:
            with st.spinner("Uploading to FastAPI…"):
                try:
                    result = api_upload(user_id.strip(), uploaded_file)
                    st.success(result.get("status", "Upload submitted."))
                    st.info(
                        "Your document is being processed. "
                        "Check the **Status** page to monitor progress."
                    )
                except requests.HTTPError as exc:
                    st.error(f"Upload failed ({exc.response.status_code}): {exc.response.text}")
                except requests.RequestException as exc:
                    st.error(f"Could not reach API: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — QUERY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬 Query":
    st.title("💬 Ask a Question")
    st.caption("Query your knowledge base. Answers are generated via `POST /chat`.")

    col_chat, col_side = st.columns([3, 1])
    with col_side:
        if st.button("🗑️ Clear history", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    with col_chat:
        for turn in st.session_state.chat_history:
            st.markdown(
                f'<div class="chat-user">{turn["question"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="chat-bot">{turn["answer"]}</div>',
                unsafe_allow_html=True,
            )

    with st.form("query_form"):
        question = st.text_area(
            "Your question",
            placeholder="What is this document about?",
            height=100,
        )
        ask = st.form_submit_button("✨ Ask", use_container_width=True)

    if ask:
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Retrieving context and querying LLM…"):
                try:
                    result = api_chat(question.strip())
                    answer = result.get("response", "No response received.")
                    st.session_state.chat_history.append(
                        {
                            "question": question.strip(),
                            "answer": answer,
                            "time": datetime.now().isoformat(),
                        }
                    )
                    st.rerun()
                except requests.HTTPError as exc:
                    st.error(f"Query failed ({exc.response.status_code}): {exc.response.text}")
                except requests.RequestException as exc:
                    st.error(f"Could not reach API: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — STATUS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Status":
    st.title("📊 Processing Status")
    st.caption("Track document ingestion stages via `GET /status/{user_id}`.")

    status_user_id = st.text_input(
        "User ID",
        placeholder="Enter the same User ID used during upload",
        key="status_user_id",
    )

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        fetch = st.button("🔍 Fetch Status", use_container_width=True)

    if fetch:
        if not status_user_id.strip():
            st.error("Please enter a User ID.")
        else:
            with st.spinner("Fetching status from FastAPI…"):
                try:
                    result = api_status(status_user_id.strip())
                    status_payload = result.get("Status")

                    if status_payload is None:
                        st.warning("No record found for this User ID.")
                    elif isinstance(status_payload, str):
                        st.error(status_payload)
                    else:
                        stages = status_payload
                        st.success(f"Record found for **{status_user_id.strip()}**")
                        expected = ["ingestion", "chunking", "embedding"]
                        completed = {s.get("stage") for s in stages}

                        st.markdown("### Pipeline Progress")
                        prog_cols = st.columns(len(expected))
                        for i, stage_name in enumerate(expected):
                            done = stage_name in completed
                            with prog_cols[i]:
                                if done:
                                    st.success(f"**{i + 1}. {stage_name.title()}** — processed")
                                else:
                                    st.warning(f"**{i + 1}. {stage_name.title()}** — pending")

                        if stages:
                            st.markdown("### Stage Details")
                            for stage in stages:
                                st.markdown(
                                    f"- **{stage.get('stage', 'unknown').title()}** — "
                                    f"{stage.get('status', 'N/A')}"
                                )

                        with st.expander("Raw API response"):
                            st.code(serialize_status(result), language="json")

                except requests.HTTPError as exc:
                    st.error(f"Status request failed ({exc.response.status_code}): {exc.response.text}")
                except requests.RequestException as exc:
                    st.error(f"Could not reach API: {exc}")
