from pathlib import Path
from typing import List
from langchain_core.documents import Document
from src.config import settings
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import TechnicalDocumentChunker
from src.core.vector_store import vector_store_manager

def index_documents(documents: List[Document]) -> int:
    """
    Chunks and indexes a list of documents into the persistent ChromaDB store.
    Returns the total number of chunks added.
    """
    if not documents:
        return 0

    chunker = TechnicalDocumentChunker()
    chunks = chunker.chunk_documents(documents)
    print(f"Split {len(documents)} document(s) into {len(chunks)} technical chunk(s).")

    vector_store_manager.add_documents(chunks)
    print(f"Successfully indexed {len(chunks)} chunks into ChromaDB.")
    return len(chunks)

def seed_default_corpus() -> int:
    """
    Loads all markdown/text files in settings.DOCS_DIRECTORY and indexes them.
    """
    docs_dir = Path(settings.DOCS_DIRECTORY)
    if not docs_dir.exists():
        print(f"Documents directory not found: {docs_dir}")
        return 0

    print(f"Loading seed documents from: {docs_dir}...")
    documents = DocumentLoader.load_directory(docs_dir)
    if not documents:
        print("No documents found to index.")
        return 0

    print(f"Found {len(documents)} raw document(s). Starting indexing pipeline...")
    chunker = TechnicalDocumentChunker()
    total_indexed = 0
    from src.storage.repository import storage_repo

    for doc in documents:
        chunks = chunker.chunk_documents([doc])
        if chunks:
            vector_store_manager.add_documents(chunks)
            total_indexed += len(chunks)
            source_path = doc.metadata.get("source", "")
            title = doc.metadata.get("title") or Path(source_path).stem.replace("_", " ").title()
            storage_repo.record_document(
                source=source_path,
                title=title,
                chunk_count=len(chunks),
                source_type="file",
            )
    print(f"Successfully indexed and registered {total_indexed} chunks across {len(documents)} documents.")
    return total_indexed

if __name__ == "__main__":
    count = seed_default_corpus()
    total = vector_store_manager.count()
    print(f"Indexing complete! Total chunks now in vector store: {total}")
