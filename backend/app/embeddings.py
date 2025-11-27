# backend/app/embeddings.py
import os
import faiss
import numpy as np
import pickle
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEN_API_KEY = os.getenv("GEN_API_KEY")
genai.configure(api_key=GEN_API_KEY)

# --------------------------
# FAISS & Embeddings Setup
# --------------------------
INDEX_PATH = "./data/faiss.index"
ID_MAP_PATH = "./data/id_map.pkl"
EMBED_MODEL = "models/text-embedding-004"  # Gemini embedding model

os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)

# Load or create FAISS index
if os.path.exists(INDEX_PATH) and os.path.exists(ID_MAP_PATH):
    index = faiss.read_index(INDEX_PATH)
    with open(ID_MAP_PATH, "rb") as f:
        id_to_chunk = pickle.load(f)
    print("FAISS index and ID map loaded.")
else:
    index = faiss.IndexFlatL2(768)  # embedding dim for text-embedding-004 is 768
    id_to_chunk = {}
    with open(ID_MAP_PATH, "wb") as f:
        pickle.dump({}, f)
    print("Created new FAISS index.")


# --------------------------
# Reset FAISS index
# --------------------------
def reset_index():
    """Resets the FAISS index and ID map to an empty state."""
    global index, id_to_chunk

    # Re-initialize in-memory variables
    index = faiss.IndexFlatL2(768)
    id_to_chunk = {}

    # Delete old files if they exist to ensure a clean state
    if os.path.exists(INDEX_PATH):
        os.remove(INDEX_PATH)
    if os.path.exists(ID_MAP_PATH):
        os.remove(ID_MAP_PATH)

    print("FAISS index has been reset.")


# --------------------------
# Create embedding
# --------------------------
def create_embedding(text: str) -> np.ndarray:
    result = genai.embed_content(model=EMBED_MODEL, content=text)
    return np.array(result["embedding"], dtype=np.float32)


# --------------------------
# Add chunks to FAISS
# --------------------------
def add_chunks_to_index(chunks):
    global id_to_chunk

    # If the index has no vectors, it might be freshly reset.
    if index.ntotal == 0:
        id_to_chunk = {}

    for chunk in chunks:
        vec = create_embedding(chunk)
        index.add(np.array([vec]))
        id_to_chunk[index.ntotal - 1] = chunk

    faiss.write_index(index, INDEX_PATH)
    with open(ID_MAP_PATH, "wb") as f:
        pickle.dump(id_to_chunk, f)
    print(f"Added {len(chunks)} chunks to FAISS index.")


# --------------------------
# Search top-k similar chunks
# --------------------------
def search(query: str, top_k=5):
    """Search for top_k similar chunks, with a hard limit to avoid noise."""
    # Add a hard limit to top_k to prevent excessive results from large corpora
    if index.ntotal == 0:
        print("Search attempted on an empty index.")
        return [] # Return empty list if index is empty

    max_k = 5
    k = min(top_k, max_k, index.ntotal)
    query_vec = create_embedding(query)
    D, I = index.search(np.array([query_vec]), k)
    results = [id_to_chunk[i] for i in I[0] if i in id_to_chunk]
    return results
