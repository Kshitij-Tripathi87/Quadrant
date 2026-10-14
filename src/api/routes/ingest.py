import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from langchain_core.documents import Document
from src.api.schemas import IngestRequest, IngestResponse
from src.ingestion.loader import DocumentLoader
from src.ingestion.indexer import index_documents
from src.storage.repository import storage_repo
from src.config import settings

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest new documents from URLs",
    description="Crawls, cleans, chunks, and indexes documents from a list of URLs."
)
async def ingest_urls(payload: IngestRequest) -> IngestResponse:
    if not payload.urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No URLs provided for ingestion."
        )

    loaded_docs: List[Document] = []
    for url in payload.urls:
        try:
            doc = await DocumentLoader.load_url(url)
            loaded_docs.append(doc)
        except Exception as e:
            print(f"[Ingest URL] Failed to load {url}: {e}")

    if not loaded_docs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract content from the provided URLs."
        )

    total_chunks = index_documents(loaded_docs)

    for doc in loaded_docs:
        storage_repo.record_document(
            source=doc.metadata.get("source", ""),
            title=doc.metadata.get("title", "Web Document"),
            chunk_count=total_chunks // len(loaded_docs),
            source_type="url",
        )

    return IngestResponse(
        status="success",
        indexed_documents=len(loaded_docs),
        total_chunks=total_chunks,
        message=f"Successfully indexed {len(loaded_docs)} document(s) into {total_chunks} chunks."
    )

@router.post(
    "/upload",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest technical documentation files",
    description="Upload local .md, .txt, or .html documentation files to chunk and index."
)
async def ingest_files(files: List[UploadFile] = File(...)) -> IngestResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded."
        )

    upload_dir = Path(settings.DOCS_DIRECTORY) / "uploaded"
    upload_dir.mkdir(parents=True, exist_ok=True)

    loaded_docs: List[Document] = []
    for uploaded_file in files:
        filename = uploaded_file.filename or "uploaded_doc.txt"
        file_path = upload_dir / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

        try:
            doc = DocumentLoader.load_file(file_path)
            loaded_docs.append(doc)
        except Exception as e:
            print(f"[Ingest File] Error reading {filename}: {e}")

    if not loaded_docs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not read or parse uploaded files."
        )

    total_chunks = index_documents(loaded_docs)

    for doc in loaded_docs:
        storage_repo.record_document(
            source=doc.metadata.get("source", ""),
            title=doc.metadata.get("title", doc.metadata.get("filename", "File")),
            chunk_count=total_chunks // len(loaded_docs),
            source_type="file",
        )

    return IngestResponse(
        status="success",
        indexed_documents=len(loaded_docs),
        total_chunks=total_chunks,
        message=f"Successfully uploaded and indexed {len(loaded_docs)} file(s) into {total_chunks} chunks."
    )
