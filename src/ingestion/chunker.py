import uuid
from datetime import datetime, timezone
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

NAMESPACE_RAG = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

class TechnicalDocumentChunker:
    """
    Two-Tier Chunking Engine for Technical Documentation:
    1. Structure-aware splitting using Markdown headers.
    2. Length-bounded recursive splitting preserving code blocks and syntax.
    """

    HEADERS_TO_SPLIT_ON = [
        ("#", "Header_1"),
        ("##", "Header_2"),
        ("###", "Header_3"),
    ]

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.HEADERS_TO_SPLIT_ON,
            strip_headers=False,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\n```",   # Code block boundaries
                "\n```\n",
                "\n\n",      # Paragraph boundaries
                "\n",        # Line boundaries
                ". ",        # Sentences
                " ",
                "",
            ],
            keep_separator=True,
        )

    def chunk_document(self, document: Document) -> List[Document]:
        """
        Splits a single document into semantically rich chunks with hierarchical metadata.
        """
        raw_text = document.page_content
        base_meta = document.metadata.copy()

        # Step 1: Split along markdown headers
        try:
            header_splits = self.header_splitter.split_text(raw_text)
        except Exception:
            header_splits = [Document(page_content=raw_text, metadata={})]

        if not header_splits:
            header_splits = [Document(page_content=raw_text, metadata={})]

        final_chunks: List[Document] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for split in header_splits:
            # Extract breadcrumb header path
            headers = []
            for h in ["Header_1", "Header_2", "Header_3"]:
                if h in split.metadata:
                    headers.append(split.metadata[h])
            header_path = " > ".join(headers) if headers else base_meta.get("title", "Overview")

            # Step 2: Split with recursive character splitter
            sub_chunks = self.text_splitter.split_text(split.page_content)
            for idx, text in enumerate(sub_chunks):
                clean_text = text.strip()
                if not clean_text:
                    continue

                # Generate deterministic chunk id
                chunk_unique_str = f"{base_meta.get('source', '')}::{header_path}::{idx}::{clean_text[:50]}"
                chunk_id = str(uuid.uuid5(NAMESPACE_RAG, chunk_unique_str))

                chunk_metadata = {
                    **base_meta,
                    "header_path": header_path,
                    "chunk_id": chunk_id,
                    "chunk_index": idx,
                    "char_count": len(clean_text),
                    "ingested_at": now_iso,
                }

                # Ensure primitive types for ChromaDB
                safe_metadata = {
                    k: (str(v) if not isinstance(v, (str, int, float, bool)) else v)
                    for k, v in chunk_metadata.items()
                }

                final_chunks.append(
                    Document(page_content=clean_text, metadata=safe_metadata)
                )

        return final_chunks

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Process a list of documents into chunks."""
        all_chunks: List[Document] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
