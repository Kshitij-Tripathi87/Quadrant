import pytest
from langchain_core.documents import Document
from src.ingestion.chunker import TechnicalDocumentChunker

def test_chunker_hierarchical_headers():
    doc = Document(
        page_content="# FastAPI Guide\n\nOverview text.\n\n## Dependencies\n\n```python\nasync def get_db():\n    yield db\n```\n",
        metadata={"source": "fastapi.md", "title": "FastAPI Guide", "source_type": "file"}
    )
    chunker = TechnicalDocumentChunker(chunk_size=400, chunk_overlap=50)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 1
    # Check that header path was preserved in metadata
    assert any("Dependencies" in c.metadata.get("header_path", "") for c in chunks)
    # Check code fence preservation
    assert any("```python" in c.page_content for c in chunks)
    # Check chunk_id exists
    for chunk in chunks:
        assert "chunk_id" in chunk.metadata
        assert len(chunk.metadata["chunk_id"]) > 10
