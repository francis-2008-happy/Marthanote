# Marthanote — Upgrade Notes & Run Instructions

This file documents the recent upgrade work done to add production-level features.

Key changes
- Per-document FAISS indices and index storage under `./data/indices`.
- SQLite + SQLAlchemy models for `Document` and `ChatMessage` in `backend/app/models.py`.
- New API router in `backend/app/api_v2.py` exposing endpoints:
  - `POST /api/upload` (returns document id; background processing generates summary & embeddings)
  - `GET /api/documents` (list documents)
  - `GET /api/documents/{id}` (document details)
  - `POST /api/documents/{id}/set-active` (mark active document)
  - `POST /api/ask` (ask a question; supports `document_id` or global search)
  - Chat history endpoints: `GET/DELETE /api/chat-history/{document_id}`
- Streamlit frontend updated at `frontend/streamlit_app.py` with a sidebar, upload, and chat UI.

Quickstart
1. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Add a `.env` with your `GEN_API_KEY`:

```ini
GEN_API_KEY=sk-...
```

3. Start the backend:

```bash
uvicorn backend.app.main:app --reload
```

4. Start the frontend:

```bash
streamlit run frontend/streamlit_app.py
```

Running Tests

```bash
pytest -q
```

Notes
- If you hit issues with `faiss-cpu` installation, consider using a platform-specific wheel or `pip install faiss-cpu==1.7.3`.
- The Gemini API package requirement is `google-generativeai` (verify the package name/version for your environment).
