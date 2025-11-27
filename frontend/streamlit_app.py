import streamlit as st
import requests

# =========================
# Page Config
# =========================
st.set_page_config(page_title="Marty AI", page_icon="🤖", layout="centered")

API_URL = "http://127.0.0.1:8000/api"

# =========================
# Session State
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "last_uploaded_file_id" not in st.session_state:
    st.session_state.last_uploaded_file_id = None

# =========================
# Dark Mode Toggle
# =========================
st.session_state.dark_mode = st.toggle("🌙 Dark Mode", st.session_state.dark_mode)

bg_color = "#0f172a" if st.session_state.dark_mode else "#f9fafb"
card_color = "#020617" if st.session_state.dark_mode else "#ffffff"
text_color = "#e2e8f0" if st.session_state.dark_mode else "#020617"
user_bubble = "#2563eb"
bot_bubble = "#1e293b" if st.session_state.dark_mode else "#e5e7eb"

# =========================
# Custom CSS
# =========================
st.markdown(
    f"""
<style>

.stApp {{
    background-color: {bg_color};
}}

.main-container {{
    max-width: 750px;
    margin: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
}}

h1 {{
    text-align: center;
    margin-bottom: 10px;
    font-size: 32px;
    color: {text_color};
}}

.card {{
    background: {card_color};
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.05);
}}

.chat-history {{
    max-height: 450px;
    overflow-y: auto;
}}

.chat-bubble {{
    max-width: 80%;
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
    font-size: 15px;
    line-height: 1.5;
}}

.user-bubble {{
    background: {user_bubble};
    color: white;
    margin-left: auto;
}}

.bot-bubble {{
    background: {bot_bubble};
    color: {text_color};
}}

.fixed-input {{
    padding-top: 5px;
}}

::-webkit-scrollbar {{
    width: 6px;
}}

::-webkit-scrollbar-thumb {{
    background-color: #94a3b8;
    border-radius: 10px;
}}

</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Main Container
# =========================
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# -------------------------
# Header
# -------------------------
st.markdown("<h1> Marty AI</h1>", unsafe_allow_html=True)

# -------------------------
# File Upload Card
# -------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📎 Drag & drop or upload a document",
    type=["pdf", "docx", "txt"],
    label_visibility="collapsed",
)

if uploaded_file and uploaded_file.file_id != st.session_state.last_uploaded_file_id:
    with st.spinner("Processing document..."):
        try:
            # Step 1: Reset the backend context
            reset_res = requests.post(f"{API_URL}/reset", timeout=10)
            reset_res.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            # Step 2: Upload the new file
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            upload_res = requests.post(f"{API_URL}/upload", files=files, timeout=30)
            upload_res.raise_for_status()

            st.success("✅ File uploaded successfully")
            st.session_state.last_uploaded_file_id = uploaded_file.file_id
            st.session_state.messages = []  # Clear frontend chat history
            st.rerun()

        except requests.exceptions.RequestException as e:
            # This will catch connection errors, timeouts, and bad status codes
            error_message = f"❌ **API Error:** Could not communicate with the backend."
            if e.response:
                # If the server responded with an error, show it
                error_message += f"\n\n**Status Code:** `{e.response.status_code}`"
                error_message += f"\n\n**Reason:** `{e.response.reason}`"
                error_message += f"\n\nThis error comes from the backend server. Please ensure the `/api/reset` and `/api/upload` endpoints are working correctly."
            st.error(error_message)

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Chat Area
# -------------------------
st.markdown("<div class='card chat-history'>", unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown(
        "<div style='color: gray; text-align: center;'>Start by asking a question...</div>",
        unsafe_allow_html=True,
    )

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f"<div class='chat-bubble user-bubble'>{msg['content']}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='chat-bubble bot-bubble'>{msg['content']}</div>",
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Input Box
# -------------------------
question = st.chat_input("Ask a question...")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Chat Logic
# =========================
if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.spinner("Thinking..."):
        try:
            res = requests.post(f"{API_URL}/ask", json={"question": question}, timeout=30)
            res.raise_for_status()  # Raise an exception for bad status codes
            answer = res.json().get("answer", "No answer returned from API.")

        except requests.exceptions.RequestException as e:
            answer = f"❌ **API Error:** Could not get an answer from the backend."
            if e.response:
                answer += f"\n\n**Status Code:** `{e.response.status_code}`"
                answer += f"\n\n**Reason:** `{e.response.reason}`"
            else:
                answer += "\n\nCould not connect to the backend. Is the server running?"

    st.session_state.messages.append({"role": "assistant", "content": answer})

    st.rerun()

