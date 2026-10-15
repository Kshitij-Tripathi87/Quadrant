import pytest
from langchain_core.documents import Document
from src.core.vector_store import vector_store_manager

def test_vector_store_count():
    count = vector_store_manager.count()
    assert count >= 0

def test_vector_store_similarity_search():
    results = vector_store_manager.similarity_search("FastAPI dependencies with yield", k=2)
    assert isinstance(results, list)
    if len(results) > 0:
        first = results[0]
        assert hasattr(first, "page_content")
        assert hasattr(first, "metadata")
        assert len(first.page_content) > 0

def test_vector_store_catalog():
    catalog = vector_store_manager.get_document_catalog()
    assert isinstance(catalog, list)
    for entry in catalog:
        assert "source" in entry
        assert "chunk_count" in entry
        assert entry["chunk_count"] >= 1
