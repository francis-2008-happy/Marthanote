# backend/app/api.py
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import os
from PyPDF2 import PdfReader
from docx import Document
import re

router = APIRouter()

UPLOAD_FOLDER = "./data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Health check (already exists)
@router.get("/health")
async def health():
    return {"status": "ok"}


# --------------------------
# Upload endpoint
# --------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Save uploaded file
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Extract text
    text = ""
    if file.filename.endswith(".pdf"):
        reader = PdfReader(file_location)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    elif file.filename.endswith(".docx"):
        doc = Document(file_location)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file.filename.endswith(".txt"):
        with open(file_location, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        return JSONResponse({"error": "Unsupported file type"}, status_code=400)

    # Preprocess text
    text = preprocess_text(text)
    chunks = chunk_text(text, chunk_size=500)  # ~500 tokens per chunk

    return {"filename": file.filename, "chunks_count": len(chunks)}


# --------------------------
# Preprocessing helper
# --------------------------
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)  # remove extra spaces
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    return text


def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i : i + chunk_size]))
    return chunks
