import os
from backend.app import embeddings


def test_search_on_empty_indices():
    # Ensure reset_all_indices clears indices directory
    embeddings.reset_all_indices()
    results = embeddings.search("anything", document_id=None)
    assert isinstance(results, list)
    assert results == []


def test_create_and_delete_index(tmp_path):
    # Create a temporary document id and add a small chunk
    doc_id = "test-doc-123"
    embeddings.reset_all_indices()
    embeddings.add_chunks_to_index(doc_id, ["hello world this is a test chunk"])
    stats = embeddings.get_index_stats(doc_id)
    assert stats["chunk_count"] >= 1
    embeddings.delete_index(doc_id)
    # After delete, search should yield empty
    results = embeddings.search("hello", document_id=doc_id)
    assert results == []
