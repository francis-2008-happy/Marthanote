# backend/app/api.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse 
from google.api_core import exceptions as google_exceptions
from .embeddings import add_chunks_to_index, search, reset_index
from .embeddings import add_chunks_to_index, search, reset_index, create_embedding
import os
from PyPDF2 import PdfReader
from docx import Document
import re
from pydantic import BaseModel
import google.generativeai as genai
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import time
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

UPLOAD_FOLDER = "./data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --------------------------
# Health check
# --------------------------
@router.get("/health")
async def health():
    return {"status": "ok"}


# --------------------------
# Text preprocessing
# --------------------------
def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text


def remove_stopwords(text: str) -> str:
    stop_words = set(stopwords.words("english"))
    word_tokens = word_tokenize(text)
    filtered_text = [w for w in word_tokens if not w.lower() in stop_words]
    return " ".join(filtered_text)


def chunk_text(text: str, chunk_size=500, chunk_overlap=150):
    """Splits text into overlapping chunks."""
    words = text.split()
    if not words:
        return []
    return [
        " ".join(words[i : i + chunk_size])
        for i in range(0, len(words), chunk_size - chunk_overlap)
    ]


# --------------------------
# Upload endpoint
# --------------------------
def process_file_in_background(file_location: str, filename: str):
    """This function runs in the background to process the uploaded file."""
    text = ""
    if filename.endswith(".pdf"):
        reader = PdfReader(file_location)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    elif filename.endswith(".docx"):
        doc = Document(file_location)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif filename.endswith(".txt"):
        with open(file_location, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        print(f"Unsupported file type: {filename}")
        return

    # Preprocess & chunk
    processed_text = preprocess_text(text)
    text_without_stopwords = remove_stopwords(processed_text)
    chunks = chunk_text(text_without_stopwords, chunk_size=500, chunk_overlap=150)
    if chunks:
        add_chunks_to_index(chunks)

@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Add the slow processing job to the background
    background_tasks.add_task(
        process_file_in_background, file_location, file.filename
    )

    return {"filename": file.filename, "message": "File upload started in background."}


# --------------------------
# Reset endpoint
# --------------------------
@router.post("/reset")
async def reset():
    """Clears the existing FAISS index to allow for a new document context."""
    reset_index()
    return {"message": "Backend context reset successfully."}


# --------------------------
# Ask endpoint
# --------------------------
class Question(BaseModel):
    question: str


@router.post("/ask")
async def ask_question(q: Question):
    try:
        # Get top chunks
        relevant_chunks = search(q.question, top_k=3)
        context_text = "\n".join(relevant_chunks)

        # Gemini Chat
        prompt = f"Based on the provided context below, please answer the question. If the context does not contain the answer, say 'I do not have enough information to answer that question.'\n\nContext:\n{context_text}\n\nQuestion: {q.question}\nAnswer:"

        model = genai.GenerativeModel("gemini-pro-latest")
        response = model.generate_content(prompt)
        answer = response.text
        source_chunks = relevant_chunks

    except google_exceptions.ServiceUnavailable as e:
        error_message = "The backend server could not connect to Google's AI service. This is likely a network or DNS issue on the server."
        print(f"ERROR: {error_message}\nDetails: {e}")
        return JSONResponse(status_code=503, content={"answer": error_message})

    except google_exceptions.RetryError as e:
        error_message = "The request to Google's AI service timed out. This might be due to a network issue or the service being temporarily unavailable."
        print(f"ERROR: {error_message}\nDetails: {e}")
        return JSONResponse(status_code=504, content={"answer": error_message})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"An unexpected error occurred: {str(e)}"})

    return {"answer": answer, "source_chunks": source_chunks}
