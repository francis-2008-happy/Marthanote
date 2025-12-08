# Marthanote — Document AI Assistant

This project is a Document AI Assistant (RAG-style) that lets you upload documents, index them with
FAISS embeddings, and ask questions using Google's Gemini LLM. It includes a Streamlit frontend and a FastAPI backend.

Features implemented:
- Multi-document uploads with per-document FAISS indices
- Auto-generate concise AI summary on upload (Gemini)
- Persistent document metadata and chat history (SQLite + SQLAlchemy)
- Sidebar document history, active-document selection
- Chat-style interface with session memory in frontend + backend chat history

Requirements
------------
- Create a Python virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Environment variables
---------------------
- `GEN_API_KEY`: Your Google Generative AI API key. Store this in a `.env` file at project root.

Example `.env`:

```ini
GEN_API_KEY=sk-....
```

Run the backend
--------------
Start the FastAPI backend (serves the `/api` endpoints):

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run the frontend
----------------
Start the Streamlit app:

```bash
streamlit run frontend/streamlit_app.py
```

Testing
-------
Run the unit tests with pytest:

```bash
pytest -q
```

Notes & next steps
------------------
- The app currently stores per-document FAISS indices under `./data/indices` and the SQLite DB at `./data/marthanote.db`.
- Background processing generates summaries and embeddings after upload — the upload endpoint returns immediately with a document ID and a placeholder summary. The frontend polls for updated summaries (manual refresh supported).
- For production readiness consider:
  - Moving from SQLite to PostgreSQL
  - Adding authentication and per-user document isolation
  - Running FAISS and embeddings in background worker (Celery/RQ)

If you'd like, I can:
- Add real-time polling on the frontend to show when summary embedding is ready
- Add Dockerfiles and a docker-compose for local development
