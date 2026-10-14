from typing import List
from fastapi import APIRouter, status
from src.api.schemas import DocumentListResponse, DocumentItem
from src.core.vector_store import vector_store_manager
from src.storage.repository import storage_repo

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all indexed documents in the corpus",
    description="Returns metadata, chunk statistics, and titles for all indexed documentation."
)
async def list_documents() -> DocumentListResponse:
    db_docs = storage_repo.get_indexed_documents()
    chroma_catalog = vector_store_manager.get_document_catalog()
    total_vectors = vector_store_manager.count()

    items: List[DocumentItem] = []
    seen_sources = set()

    for row in db_docs:
        source = row.get("source", "")
        seen_sources.add(source)
        items.append(
            DocumentItem(
                source=source,
                title=row.get("title") or "Technical Document",
                chunk_count=row.get("chunk_count", 0),
                source_type=row.get("source_type", "file"),
                ingested_at=str(row.get("ingested_at", "")),
            )
        )

    for cat in chroma_catalog:
        src = cat.get("source", "")
        if src not in seen_sources:
            items.append(
                DocumentItem(
                    source=src,
                    title=cat.get("title", "Document"),
                    chunk_count=cat.get("chunk_count", 0),
                    source_type="file",
                    ingested_at=cat.get("last_ingested", "N/A"),
                )
            )

    return DocumentListResponse(
        total_documents=len(items),
        total_vectors=total_vectors,
        documents=items,
    )
