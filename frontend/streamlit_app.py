import streamlit as st
import requests
import time
from typing import List, Optional
import hashlib

# =========================
# Page Config
# =========================
st.set_page_config(page_title="Marty AI", page_icon="🤖", layout="wide")

API_URL = "https://marthanote.onrender.com/api"

# "http://127.0.0.1:8000/api"
# =========================
# Session State Initialization
# =========================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False  # Default to light mode

if "documents" not in st.session_state:
    st.session_state.documents = []

if "active_document" not in st.session_state:
    st.session_state.active_document = None

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "last_upload_time" not in st.session_state:
    st.session_state.last_upload_time = 0

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "processed_docs" not in st.session_state:
    st.session_state.processed_docs = set()

if "uploaded_hashes" not in st.session_state:
    st.session_state.uploaded_hashes = set()

if "last_poll" not in st.session_state:
    st.session_state.last_poll = 0.0

if "poll_interval" not in st.session_state:
    st.session_state.poll_interval = 3.0

if "selected_documents" not in st.session_state:
    st.session_state.selected_documents = set()

if "select_all_checkbox" not in st.session_state:
    st.session_state.select_all_checkbox = False

if "pending_delete" not in st.session_state:
    st.session_state.pending_delete = []

if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if "processing_query" not in st.session_state:
    st.session_state.processing_query = False


# =========================
# Modern Styling
# =========================
def _get_styles(dark: bool):
    """Professional color scheme based on modern AI assistants"""
    if dark:
        bg_color = "#0a0e27"
        secondary_bg = "#1a1f3a"
        card_color = "#16213e"
        text_color = "#e5e7eb"
        text_secondary = "#9ca3af"
        accent = "#10a37f"
        user_bubble = "#2563eb"
        bot_bubble = "#1f2937"
        border_color = "#374151"
    else:
        bg_color = "#ffffff"
        secondary_bg = "#f9fafb"
        card_color = "#ffffff"
        text_color = "#1f2937"
        text_secondary = "#6b7280"
        accent = "#10a37f"
        user_bubble = "#2563eb"
        bot_bubble = "#f3f4f6"
        border_color = "#e5e7eb"

    return {
        "bg": bg_color,
        "secondary_bg": secondary_bg,
        "card": card_color,
        "text": text_color,
        "text_secondary": text_secondary,
        "accent": accent,
        "user_bubble": user_bubble,
        "bot_bubble": bot_bubble,
        "border": border_color,
    }


colors = _get_styles(st.session_state.dark_mode)

# Global CSS styling
st.markdown(
    f"""
    <style>
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {colors["bg"]};
        color: {colors["text"]};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    }}
    /* Remove Streamlit default top padding so content starts at the very top */
    .block-container {{ padding-top: 0rem !important; }}

    /* Top banner styling (prominent bot header) */
    .top-banner {{
        padding: 16px 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 12px;
        box-shadow: 0 6px 18px rgba(2,6,23,0.08);
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    /* Make the chat container scrollable and reserve space for fixed input */
    .chat-container {{
        overflow-y: auto;
        max-height: calc(100vh - 360px);
        padding-right: 8px;
    }}

    /* Ensure main content has bottom padding so messages aren't hidden behind the input */
    .main-card {{
        padding-bottom: 40px;
    }}

    /* Fixed chat input bar styling: keep the input visible when the page scrolls */
    .chat-container {{
        padding-bottom: 140px; /* reserve space for the fixed input */
    }}

    /* Try to target Streamlit's chat input widget and make it sticky at the bottom */
    div[data-testid="stChatInput"] {{
        position: sticky !important;
        bottom: 12px !important;
        z-index: 1200 !important;
        width: 100% !important;
        background: {colors["card"]} !important;
        border-radius: 10px !important;
        padding: 8px !important;
        box-shadow: 0 6px 18px rgba(2,6,23,0.06) !important;
    }}

    /* Fallback selector used by some Streamlit versions */
    .stChatInput {{
        position: sticky !important;
        bottom: 12px !important;
        z-index: 1200 !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {colors["secondary_bg"]};
        border-right: 1px solid {colors["border"]};
    }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        color: {colors["text"]};
        font-weight: 600;
    }}
    
    /* Cards and containers */
    .main-card {{
        background: {colors["card"]};
        border-radius: 12px;
        padding: 24px;
        border: 1px solid {colors["border"]};
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    
    .sidebar-header {{
        padding: 16px 0;
        margin-bottom: 16px;
        border-bottom: 1px solid {colors["border"]};
    }}
    
    .sidebar-header h3 {{
        font-size: 18px;
        font-weight: 700;
        color: {colors["text"]};
        margin: 0;
    }}
    
    /* Document list styling */
    .doc-card {{
        background: {colors["card"]};
        border: 1px solid {colors["border"]};
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .doc-card:hover {{
        background: {colors["secondary_bg"]};
        border-color: {colors["accent"]};
    }}
    
    .doc-card.active {{
        border: 2px solid {colors["accent"]};
        background: {colors["secondary_bg"]};
    }}
    
    .doc-info {{
        flex: 1;
        min-width: 0;
    }}
    
    .doc-title {{
        font-weight: 600;
        color: {colors["text"]};
        font-size: 14px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .doc-summary {{
        color: {colors["text_secondary"]};
        font-size: 12px;
        margin-top: 4px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}
    
    .doc-badge {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
        white-space: nowrap;
    }}
    
    .badge-ready {{
        background: rgba(16, 163, 127, 0.2);
        color: {colors["accent"]};
    }}
    
    .badge-processing {{
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }}
    
    .doc-actions {{
        display: flex;
        gap: 6px;
        flex-shrink: 0;
    }}
    
    /* Chat bubbles */
    .chat-container {{
        display: flex;
        flex-direction: column;
        gap: 16px;
        margin-bottom: 20px;
    }}
    
    .chat-message {{
        display: flex;
        gap: 12px;
        animation: fadeIn 0.3s ease;
    }}
    
    .chat-message.user {{
        justify-content: flex-end;
    }}
    
    .chat-message.assistant {{
        justify-content: flex-start;
    }}
    
    .message-avatar {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 16px;
        flex-shrink: 0;
    }}
    
    .avatar-user {{
        background: {colors["user_bubble"]};
        color: white;
    }}
    
    .avatar-assistant {{
        background: {colors["accent"]};
        color: white;
    }}
    
    .message-content {{
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 15px;
        line-height: 1.5;
        word-wrap: break-word;
    }}
    
    .message-user {{
        background: {colors["user_bubble"]};
        color: white;
        border-radius: 18px 18px 4px 18px;
    }}
    
    .message-assistant {{
        background: {colors["bot_bubble"]};
        color: {colors["text"]};
        border-radius: 18px 18px 18px 4px;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Empty state */
    .empty-state {{
        text-align: center;
        padding: 48px 24px;
        color: {colors["text_secondary"]};
    }}
    
    .empty-state-icon {{
        font-size: 48px;
        margin-bottom: 16px;
    }}
    
    .empty-state-text {{
        font-size: 16px;
        line-height: 1.6;
    }}
    
    /* Upload area */
    .upload-section {{
        background: {colors["secondary_bg"]};
        border: 2px dashed {colors["border"]};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 16px;
        transition: all 0.2s ease;
        cursor: pointer;
    }}
    
    .upload-section:hover {{
        border-color: {colors["accent"]};
        background: {colors["card"]};
    }}
    
    /* Context sidebar */
    .context-box {{
        background: {colors["secondary_bg"]};
        border: 1px solid {colors["border"]};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }}
    
    .context-title {{
        font-weight: 600;
        color: {colors["text"]};
        margin-bottom: 12px;
        font-size: 14px;
    }}
    
    .context-item {{
        color: {colors["text_secondary"]};
        font-size: 13px;
        margin: 8px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: {colors["accent"]} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        padding: 8px 16px !important;
    }}
    
    .stButton > button:hover {{
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
    }}
    
    /* Input */
    .stChatInput {{
        border: 1px solid {colors["border"]} !important;
        border-radius: 24px !important;
        background: {colors["card"]} !important;
    }}
    
    .stChatInput input {{
        color: {colors["text"]} !important;
    }}
    
    /* Checkboxes and inputs */
    .stCheckbox {{
        color: {colors["text"]} !important;
    }}
    
    .stFileUploader {{
        color: {colors["text"]} !important;
    }}
    
    /* Alerts */
    .stAlert {{
        border-radius: 8px !important;
        border: 1px solid {colors["border"]} !important;
    }}
    
    /* Divider */
    hr {{
        border-color: {colors["border"]} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# Helper Functions
# =========================
def add_alert(alert_type: str, message: str):
    """Add an alert to display."""
    st.session_state.alerts.append({"type": alert_type, "message": message})


def display_alerts():
    """Display all alerts."""
    if not st.session_state.alerts:
        return
    for alert in st.session_state.alerts:
        alert_type = alert["type"]
        msg = alert["message"]
        if alert_type == "success":
            st.success(msg, icon="✅")
        elif alert_type == "error":
            st.error(msg, icon="❌")
        else:
            st.info(msg, icon="ℹ️")
    st.session_state.alerts = []


def fetch_documents() -> List[dict]:
    try:
        res = requests.get(f"{API_URL}/documents", timeout=10)
        res.raise_for_status()
        docs = res.json()
        st.session_state.documents = docs
        return docs
    except Exception:
        return st.session_state.documents


def set_active_document(doc_id: str):
    try:
        res = requests.post(f"{API_URL}/documents/{doc_id}/set-active", timeout=10)
        res.raise_for_status()
        st.session_state.active_document = doc_id
    except Exception:
        st.error("Could not set active document on backend")


def delete_document(doc_id: str):
    """Delete a document from the backend and refresh."""
    try:
        res = requests.delete(f"{API_URL}/documents/{doc_id}", timeout=10)
        res.raise_for_status()
        add_alert("success", "Document deleted successfully")
        st.session_state.selected_documents.discard(doc_id)
        if st.session_state.active_document == doc_id:
            st.session_state.active_document = None
        fetch_documents()
    except Exception as e:
        add_alert("error", f"Failed to delete document: {e}")


def regenerate_summary(doc_id: str):
    """Request backend to regenerate summary and embeddings for the given document."""
    try:
        res = requests.post(
            f"{API_URL}/documents/{doc_id}/summary/regenerate", timeout=10
        )
        res.raise_for_status()
        add_alert("success", "Regeneration started. Summary will update when ready.")
        fetch_documents()
    except Exception as e:
        add_alert("error", f"Failed to start regeneration: {e}")


def bulk_delete_documents(document_ids: List[str]):
    """Delete multiple documents via backend bulk endpoint."""
    try:
        payload = {"document_ids": document_ids}
        res = requests.post(
            f"{API_URL}/documents/bulk-delete", json=payload, timeout=30
        )
        res.raise_for_status()
        data = res.json()
        add_alert("success", f"Deleted {data.get('deleted', 0)} documents")
        st.session_state.selected_documents.difference_update(document_ids)
        fetch_documents()
    except Exception as e:
        add_alert("error", f"Bulk delete failed: {e}")


def upload_files(
    files: List[st.runtime.uploaded_file_manager.UploadedFile],
) -> List[dict]:
    results = []
    for f in files:
        files_payload = {"file": (f.name, f.getvalue())}
        try:
            res = requests.post(f"{API_URL}/upload", files=files_payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            results.append(data)
            st.session_state.last_upload_time = time.time()
        except Exception as e:
            st.error(f"Upload failed for {f.name}: {e}")
    fetch_documents()
    return results


def maybe_poll_documents():
    """If any document is still processing, poll the backend periodically to refresh summaries."""
    now = time.time()
    if now - st.session_state.last_poll < st.session_state.poll_interval:
        return

    docs = st.session_state.documents or []
    needs_poll = any("processing" in (d.get("summary") or "").lower() for d in docs)
    if not needs_poll:
        return

    new_docs = fetch_documents()
    st.session_state.last_poll = now

    if any("processing" not in (d.get("summary") or "").lower() for d in new_docs):
        st.rerun()


def ask_question(
    question: str, document_id: Optional[str], document_ids: Optional[List[str]] = None
):
    """Ask a question about document(s)."""
    doc_ids = None
    if document_ids:
        doc_ids = list(document_ids)
    elif document_id:
        doc_ids = [document_id]

    payload = {"question": question, "document_ids": doc_ids, "use_chat_history": True}
    try:
        res = requests.post(f"{API_URL}/ask", json=payload, timeout=60)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"answer": f"API error: {e}", "source_chunks": []}


# =========================
# Main Layout
# =========================

# Sidebar - Document Management
with st.sidebar:
    # Stylish sidebar header with logo and document count
    fetch_documents()
    doc_count = len(st.session_state.documents or [])
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; gap:12px; padding:12px 6px;'>
          <div style='width:44px; height:44px; border-radius:10px; background:{colors['accent']}; display:flex; align-items:center; justify-content:center; font-size:20px; color:white;'>🤖</div>
          <div>
            <div style='font-weight:800; font-size:16px;'>{'Marty AI'}</div>
            <div style='font-size:12px; color:{colors['text_secondary']};'>{doc_count} documents</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Refresh and Settings buttons
    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            fetch_documents()
            st.rerun()
    with col2:
        if st.button("⚙️ Setting", use_container_width=True):
            st.session_state.show_settings = not st.session_state.get("show_settings", False)

    st.divider()

    # Upload area (styled) and quick actions
    st.markdown("####  Upload")
    st.markdown(
        f"<div class='upload-section' style='background:{colors['secondary_bg']};'>Drop files or click to upload (pdf, docx, txt)</div>",
        unsafe_allow_html=True,
    )
    uploaded_files = st.file_uploader("Select files", type=["pdf", "docx", "txt"], accept_multiple_files=True, label_visibility="collapsed")

    # Search/filter documents
    st.markdown("####  Search")
    search_q = st.text_input("Search documents", key="doc_search", placeholder="Search by filename...", label_visibility="collapsed")

    if uploaded_files:
        to_upload = []
        skipped = []
        for f in uploaded_files:
            try:
                content = f.getvalue()
            except Exception:
                skipped.append(f.name)
                continue
            h = hashlib.md5(content).hexdigest()
            if h in st.session_state.uploaded_hashes:
                skipped.append(f.name)
            else:
                to_upload.append((f, h))

        if to_upload:
            files_only = [t[0] for t in to_upload]
            with st.spinner("⏳ Uploading documents..."):
                upload_files(files_only)
            for _, h in to_upload:
                st.session_state.uploaded_hashes.add(h)
            st.rerun()
        else:
            if skipped:
                add_alert("info", f"No new files to upload: {', '.join(skipped)}")

    st.divider()

    # Document list
    st.markdown("#### 📋 Your Documents")
    # Use the latest documents (fetch already called above)

    # Select all control
    all_selected = (
        len(st.session_state.selected_documents) == len(st.session_state.documents)
        and len(st.session_state.documents) > 0
    )
    select_all_checked = st.checkbox(
        "Select all",
        value=all_selected,
        key="select_all_checkbox",
    )

    if select_all_checked:
        ids = [d["id"] for d in st.session_state.documents]
        st.session_state.selected_documents = set(ids)
        for doc_id in ids:
            st.session_state[f"select_{doc_id}"] = True
    else:
        if all_selected:
            ids = [d["id"] for d in st.session_state.documents]
            st.session_state.selected_documents.clear()
            for doc_id in ids:
                st.session_state[f"select_{doc_id}"] = False

    # Bulk delete button
    if st.session_state.selected_documents:
        if st.button("🗑️ Delete Selected", use_container_width=True, type="secondary"):
            ids_to_delete = list(st.session_state.selected_documents)
            if ids_to_delete:
                bulk_delete_documents(ids_to_delete)
                st.session_state.selected_documents.clear()
                st.rerun()

    # Document cards
    docs_to_show = st.session_state.documents or []
    if search_q:
        docs_to_show = [d for d in docs_to_show if search_q.lower() in d.get("filename", "").lower()]

    if not docs_to_show:
        st.markdown(
            "<div style='text-align:center; padding:24px; color: #9ca3af;'>No documents yet.<br>Upload one to get started! ⬆️</div>",
            unsafe_allow_html=True,
        )
    else:
        for doc in docs_to_show:
            is_processing = "processing" in (doc.get("summary") or "").lower()
            badge_class = "badge-processing" if is_processing else "badge-ready"
            badge_text = "⏳ Processing" if is_processing else "✓ Ready"

            is_active = doc["id"] == st.session_state.active_document
            is_selected = doc["id"] in st.session_state.selected_documents

            card_class = "doc-card active" if is_active else "doc-card"

            st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns([0.08, 0.76, 0.16])

            with col1:
                st.checkbox(
                    "select",
                    value=is_selected,
                    key=f"select_{doc['id']}",
                    label_visibility="collapsed",
                )
                if st.session_state[f"select_{doc['id']}"]:
                    st.session_state.selected_documents.add(doc["id"])
                else:
                    st.session_state.selected_documents.discard(doc["id"])

            with col2:
                st.markdown(f"<div class='doc-info'>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='doc-title'>{doc['filename']}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='margin-top:4px;'><span class='doc-badge {badge_class}'>{badge_text}</span></div>",
                    unsafe_allow_html=True,
                )
                summary = doc.get("summary") or "No summary yet"
                st.markdown(
                    f"<div class='doc-summary'>{summary}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            with col3:
                col_open, col_del = st.columns(2)
                with col_open:
                    if st.button(
                        "📂",
                        key=f"open_{doc['id']}",
                        help="Open",
                        use_container_width=True,
                    ):
                        set_active_document(doc["id"])
                        st.rerun()
                with col_del:
                    if st.button(
                        "🗑️",
                        key=f"delete_{doc['id']}",
                        help="Delete",
                        use_container_width=True,
                    ):
                        delete_document(doc["id"])
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # Dark mode toggle at bottom
    st.divider()
    st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_mode")


# Main content area
display_alerts()
maybe_poll_documents()

# Header banner
st.markdown("<div class='main-card'>", unsafe_allow_html=True)
st.markdown(
        f"""
        <div class='top-banner' style='background: linear-gradient(90deg, {colors["accent"]} 0%, #0ea5e9 100%);'>
            <div style='display:flex; align-items:center; gap:12px;'>
                <div style='font-size:36px; font-weight:800;'>🤖</div>
                <div>
                    <div style='font-size:28px; font-weight:800; color:white;'>Marty AI</div>
                    <div style='opacity:0.95; color: rgba(255,255,255,0.95); font-size:13px;'>Your intelligent document assistant</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
)

active_doc = st.session_state.active_document
selected_docs = st.session_state.selected_documents

# Context indicator
if selected_docs:
    selected_names = [
        d.get("filename", "Unknown")
        for d in st.session_state.documents
        if d["id"] in selected_docs
    ]
    st.markdown(
        f"**📌 Analyzing:** {', '.join(selected_names)} • {len(selected_docs)} document{'s' if len(selected_docs) > 1 else ''}"
    )
elif active_doc:
    doc_info = next(
        (d for d in st.session_state.documents if d["id"] == active_doc), None
    )
    if doc_info:
        st.markdown(f"**📌 Analyzing:** {doc_info['filename']}")
else:
    st.markdown("**📌 Analyzing:** All Documents (Global Search)")

st.markdown("</div>", unsafe_allow_html=True)

# Chat interface
st.markdown("<div class='main-card'>", unsafe_allow_html=True)

# Conversation key
if selected_docs:
    convo_key = "selected_" + "_".join(sorted(selected_docs))
elif active_doc:
    convo_key = active_doc
else:
    convo_key = "global"

if convo_key not in st.session_state.conversations:
    st.session_state.conversations[convo_key] = []

# Process pending query
if st.session_state.pending_query and not st.session_state.processing_query:
    pq = st.session_state.pending_query
    st.session_state.processing_query = True
    try:
        resp = ask_question(pq["question"], pq.get("active_doc"), pq.get("doc_ids"))
        answer = resp.get("answer", "No answer returned")
        if answer:
            if pq["convo_key"] not in st.session_state.conversations:
                st.session_state.conversations[pq["convo_key"]] = []
            st.session_state.conversations[pq["convo_key"]].append(
                {"role": "assistant", "content": answer}
            )
    except Exception as e:
        if pq["convo_key"] not in st.session_state.conversations:
            st.session_state.conversations[pq["convo_key"]] = []
        st.session_state.conversations[pq["convo_key"]].append(
            {"role": "assistant", "content": f"API error: {e}"}
        )
    finally:
        st.session_state.pending_query = None
        st.session_state.processing_query = False
        st.rerun()

# Chat and context columns
col_chat, col_context = st.columns([3, 1], gap="large")

with col_chat:
    st.markdown("### 💬 Conversation")

    # Messages display
    if not st.session_state.conversations[convo_key]:
        st.markdown(
            """
            <div class='empty-state'>
                <div class='empty-state-icon'>💭</div>
                <div class='empty-state-text'>No messages yet.<br>Start by asking a question about your documents.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for msg in st.session_state.conversations[convo_key]:
            role = msg.get("role")
            content = msg.get("content")

            if role == "user":
                st.markdown(
                    f"""
                    <div class='chat-message user'>
                        <div class='message-content message-user'>{content}</div>
                        <div class='message-avatar avatar-user'>You</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class='chat-message assistant'>
                        <div class='message-avatar avatar-assistant'>🤖</div>
                        <div class='message-content message-assistant'>{content}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # Input
    st.divider()
    question = st.chat_input("Ask something about your documents...")

    if question:
        st.session_state.conversations[convo_key].append(
            {"role": "user", "content": question}
        )
        st.session_state.pending_query = {
            "convo_key": convo_key,
            "question": question,
            "active_doc": active_doc,
            "doc_ids": list(selected_docs) if selected_docs else None,
        }
        st.rerun()

with col_context:
    st.markdown("<div class='context-box'>", unsafe_allow_html=True)
    st.markdown("### 📍 Context")

    if selected_docs:
        st.markdown(
            "<div class='context-title'>Multiple Documents</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='context-item'>📄 {len(selected_docs)} document{'s' if len(selected_docs) > 1 else ''} selected</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 Regenerate", use_container_width=True, key="regen_multi"):
            first_doc_id = list(selected_docs)[0]
            regenerate_summary(first_doc_id)
            st.rerun()
    elif active_doc:
        doc = next(
            (d for d in st.session_state.documents if d["id"] == active_doc), None
        )
        if doc:
            st.markdown(
                "<div class='context-title'>Active Document</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='context-item'>📄 {doc['filename']}</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "🔄 Regenerate Summary", use_container_width=True, key="regen_single"
            ):
                regenerate_summary(active_doc)
                st.rerun()
    else:
        st.markdown(
            "<div class='context-item'>🔍 Global search across all documents</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
