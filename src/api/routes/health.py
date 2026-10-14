from fastapi import APIRouter, status
from src.api.schemas import HealthResponse
from src.config import settings
from src.core.vector_store import vector_store_manager

router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System health and vector index readiness",
)
async def health_check() -> HealthResponse:
    vector_count = vector_store_manager.count()

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        llm_provider=settings.DEFAULT_LLM_PROVIDER,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        vector_store_count=vector_count,
    )
