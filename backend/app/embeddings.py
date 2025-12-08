"""
Enhanced multi-document FAISS embedding system.
Maintains separate FAISS indices per document for isolated search context.
Supports both document-specific and global search modes.
"""

import os
import faiss
import numpy as np
import pickle
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path

load_dotenv()
GEN_API_KEY = os.getenv("GEN_API_KEY")
genai.configure(api_key=GEN_API_KEY)

# --------------------------
# Configuration
# --------------------------
EMBED_MODEL = "models/text-embedding-004"  # Gemini embedding model (768 dims)
INDICES_DIR = "./data/indices"  # Directory for per-document indices
os.makedirs(INDICES_DIR, exist_ok=True)

# In-memory cache for loaded indices
_index_cache = {}  # {document_id: (index, id_to_chunk)}


# --------------------------
# Helper: Get index file paths
# --------------------------
def _get_index_paths(document_id: str):
    """Get paths for a document's index and ID map files."""
    index_path = os.path.join(INDICES_DIR, f"{document_id}.index")
    id_map_path = os.path.join(INDICES_DIR, f"{document_id}_id_map.pkl")
    return index_path, id_map_path


# --------------------------
# Initialize/Load FAISS index for a document
# --------------------------
def _load_or_create_index(document_id: str):
    """Load existing index or create new one for a document."""
    if document_id in _index_cache:
        return _index_cache[document_id]

    index_path, id_map_path = _get_index_paths(document_id)

    if os.path.exists(index_path) and os.path.exists(id_map_path):
        index = faiss.read_index(index_path)
        with open(id_map_path, "rb") as f:
            id_to_chunk = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(768)  # 768 dims for text-embedding-004
        id_to_chunk = {}

    _index_cache[document_id] = (index, id_to_chunk)
    return index, id_to_chunk


# --------------------------
# Save index to disk
# --------------------------
def _save_index(document_id: str, index, id_to_chunk):
    """Persist index and ID map to disk."""
    index_path, id_map_path = _get_index_paths(document_id)
    
    faiss.write_index(index, index_path)
    with open(id_map_path, "wb") as f:
        pickle.dump(id_to_chunk, f)


# --------------------------
# Create embedding
# --------------------------
def create_embedding(text: str) -> np.ndarray:
    """Generate embedding vector using Gemini API."""
    result = genai.embed_content(model=EMBED_MODEL, content=text)
    return np.array(result["embedding"], dtype=np.float32)


def create_embeddings(texts: list) -> list:
    """Generate embeddings for a list of texts in a single call (batch).

    Returns a list of numpy arrays.
    """
    if not texts:
        return []
    # Attempt to use batch embedding API by passing list to content
    result = genai.embed_content(model=EMBED_MODEL, content=texts)
    embeddings_out = []
    # Result may be a single embedding or a list depending on SDK; handle both
    if isinstance(result, dict) and "embedding" in result:
        # Single result
        embeddings_out.append(np.array(result["embedding"], dtype=np.float32))
    else:
        # Expecting iterable of embeddings
        for item in result:
            emb = item.get("embedding") if isinstance(item, dict) else item
            embeddings_out.append(np.array(emb, dtype=np.float32))

    return embeddings_out


# --------------------------
# Add chunks to a document's index
# --------------------------
def add_chunks_to_index(document_id: str, chunks):
    """Add text chunks to a specific document's FAISS index."""
    index, id_to_chunk = _load_or_create_index(document_id)
    # Batch embeddings to reduce API calls and speed up processing
    batch_size = 16
    total = len(chunks)
    added = 0
    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        vecs = create_embeddings(batch)
        if not vecs:
            continue
        arr = np.vstack(vecs).astype(np.float32)
        index.add(arr)
        # Map new ids to chunks
        start_id = index.ntotal - arr.shape[0]
        for offset, chunk_text in enumerate(batch):
            id_to_chunk[start_id + offset] = chunk_text
        added += arr.shape[0]

    _save_index(document_id, index, id_to_chunk)
    print(f"✓ Added {added} chunks to document {document_id}")


# --------------------------
# Search within a document or globally
# --------------------------
def search(query: str, document_id: str = None, top_k=5):
    """
    Search for similar chunks.
    
    Args:
        query: Search query text
        document_id: If provided, search only in this document. 
                    If None, search across all documents (global search)
        top_k: Number of results to return
    
    Returns:
        List of relevant text chunks
    """
    # Limit top_k to prevent noise from large corpora
    max_k = 5
    k = min(top_k, max_k)

    query_vec = create_embedding(query)

    if document_id:
        # Document-specific search
        index, id_to_chunk = _load_or_create_index(document_id)
        if index.ntotal == 0:
            return []

        k = min(k, index.ntotal)
        D, I = index.search(np.array([query_vec]), k)
        results = [id_to_chunk[i] for i in I[0] if i in id_to_chunk]
        return results
    else:
        # Global search across all documents
        all_results = []
        
        # Iterate through all documents
        for index_file in os.listdir(INDICES_DIR):
            if index_file.endswith(".index"):
                doc_id = index_file.replace(".index", "")
                index, id_to_chunk = _load_or_create_index(doc_id)
                
                if index.ntotal == 0:
                    continue

                search_k = min(k, index.ntotal)
                D, I = index.search(np.array([query_vec]), search_k)
                
                for distance, idx in zip(D[0], I[0]):
                    if idx in id_to_chunk:
                        all_results.append((distance, id_to_chunk[idx]))

        # Sort by distance and return top k
        all_results.sort(key=lambda x: x[0])
        return [chunk for _, chunk in all_results[:k]]


# --------------------------
# Delete document index
# --------------------------
def delete_index(document_id: str):
    """Remove a document's FAISS index and ID map."""
    index_path, id_map_path = _get_index_paths(document_id)
    
    if os.path.exists(index_path):
        os.remove(index_path)
    if os.path.exists(id_map_path):
        os.remove(id_map_path)
    
    if document_id in _index_cache:
        del _index_cache[document_id]
    
    print(f"✓ Deleted index for document {document_id}")


# --------------------------
# Get document statistics
# --------------------------
def get_index_stats(document_id: str):
    """Get statistics about a document's index."""
    index, id_to_chunk = _load_or_create_index(document_id)
    return {
        "chunk_count": index.ntotal,
        "embedding_dimension": index.d,
    }


# --------------------------
# Clear all indices (for testing/reset)
# --------------------------
def reset_all_indices():
    """Delete all document indices. Use with caution."""
    import shutil
    
    _index_cache.clear()
    
    if os.path.exists(INDICES_DIR):
        shutil.rmtree(INDICES_DIR)
    
    os.makedirs(INDICES_DIR, exist_ok=True)
    print("✓ All indices have been reset.")
