import pytest
from pathlib import Path
from src.ingestion.loader import DocumentLoader

def test_load_markdown_file(tmp_path: Path):
    file_path = tmp_path / "sample_doc.md"
    file_path.write_text("# My Test Guide\n\nThis is a sample technical documentation guide.\n", encoding="utf-8")

    doc = DocumentLoader.load_file(file_path)
    assert doc.metadata["title"] == "My Test Guide"
    assert doc.metadata["source_type"] == "file"
    assert "sample_doc.md" in doc.metadata["filename"]
    assert "This is a sample technical documentation guide." in doc.page_content

def test_load_unsupported_file_format(tmp_path: Path):
    file_path = tmp_path / "archive.zip"
    file_path.write_bytes(b"dummy binary data")

    with pytest.raises(ValueError, match="Unsupported file format"):
        DocumentLoader.load_file(file_path)

def test_load_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        DocumentLoader.load_file("nonexistent_file_path_12345.md")

def test_load_directory(tmp_path: Path):
    (tmp_path / "doc1.md").write_text("# Doc 1\nContent 1", encoding="utf-8")
    (tmp_path / "doc2.txt").write_text("Text content 2", encoding="utf-8")
    (tmp_path / "doc3.bin").write_bytes(b"binary")

    docs = DocumentLoader.load_directory(tmp_path)
    assert len(docs) == 2
    titles = [d.metadata.get("title") for d in docs]
    assert "Doc 1" in titles
