import uuid
from fastapi import APIRouter, HTTPException, status
from src.api.schemas import QueryRequest, QueryResponse, SourceCitation
from src.graph.workflow import rag_app
from src.storage.repository import storage_repo

router = APIRouter(prefix="/query", tags=["Query"])

@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit question to documentation assistant",
    description="Executes the self-corrective LangGraph workflow and returns a grounded answer with citations."
)
async def query_documentation(request: QueryRequest) -> QueryResponse:
    session_id = request.session_id or str(uuid.uuid4())

    try:
        initial_state = {
            "question": request.question,
            "current_query": request.question,
            "retry_count": 0,
            "execution_steps": [],
        }

        # Execute LangGraph StateGraph
        final_state = rag_app.invoke(initial_state)

        answer = final_state.get("generation", "No answer generated.")
        query_type = final_state.get("query_type", "conceptual")
        raw_sources = final_state.get("sources", [])
        retries = final_state.get("retry_count", 0)
        grounded = final_state.get("hallucination_grade", "grounded")
        steps = final_state.get("execution_steps", [])

        citations = [
            SourceCitation(
                source=s.get("source", ""),
                title=s.get("title", ""),
                header_path=s.get("header_path", ""),
                snippet=s.get("snippet", ""),
            )
            for s in raw_sources
        ]

        # Record in SQLite audit log
        query_id = storage_repo.save_query(
            question=request.question,
            answer=answer,
            session_id=session_id,
            query_type=query_type,
            retries=retries,
            sources=raw_sources,
            grounded=grounded,
        )

        return QueryResponse(
            query_id=query_id,
            session_id=session_id,
            answer=answer,
            query_type=query_type,
            sources=citations,
            retries_used=retries,
            grounded=grounded,
            execution_steps=steps,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing documentation assistant: {str(e)}"
        )
