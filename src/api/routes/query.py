import time
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from src.api.schemas import (
    QueryRequest,
    QueryResponse,
    SourceCitation,
    HistoryResponse,
    HistoryItem,
    SessionListResponse,
    SessionListItem,
)
from src.graph.workflow import rag_app
from src.storage.repository import storage_repo

router = APIRouter(prefix="/query", tags=["Query"])

# In-memory query cache for instant (sub-10ms) responses
_QUERY_CACHE = {}

@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit question to documentation assistant",
    description="Executes the self-corrective LangGraph workflow and returns a grounded answer with citations."
)
async def query_documentation(request: QueryRequest) -> QueryResponse:
    session_id = request.session_id or str(uuid.uuid4())
    start_time = time.perf_counter()
    cache_key = request.question.strip().lower()

    # Check in-memory query cache for instant response
    if cache_key in _QUERY_CACHE:
        cached = _QUERY_CACHE[cache_key]
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        query_id = storage_repo.save_query(
            question=request.question,
            answer=cached.answer,
            session_id=session_id,
            query_type=cached.query_type,
            retries=cached.retries_used,
            sources=[s.model_dump() for s in cached.sources],
            grounded=cached.grounded,
        )
        return QueryResponse(
            query_id=query_id,
            session_id=session_id,
            answer=cached.answer,
            query_type=cached.query_type,
            sources=cached.sources,
            retries_used=cached.retries_used,
            grounded=cached.grounded,
            execution_steps=cached.execution_steps,
            execution_time_ms=latency,
        )

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
        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

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

        response = QueryResponse(
            query_id=query_id,
            session_id=session_id,
            answer=answer,
            query_type=query_type,
            sources=citations,
            retries_used=retries,
            grounded=grounded,
            execution_steps=steps,
            execution_time_ms=execution_time_ms,
        )

        # Cache for future identical/similar requests
        _QUERY_CACHE[cache_key] = response

        return response


    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing documentation assistant: {str(e)}"
        )


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Retrieve session query history",
    description="Returns previous queries and answers for a given session ID."
)
async def get_query_history(
    session_id: str = Query(..., description="Unique session identifier"),
    limit: int = Query(50, ge=1, le=100, description="Max messages to fetch")
) -> HistoryResponse:
    try:
        records = storage_repo.get_session_queries(session_id=session_id, limit=limit)
        items = []
        for r in records:
            sources = [
                SourceCitation(
                    source=s.get("source", ""),
                    title=s.get("title", ""),
                    header_path=s.get("header_path", ""),
                    snippet=s.get("snippet", ""),
                )
                for s in r.get("sources", [])
            ]
            items.append(
                HistoryItem(
                    id=r["id"],
                    session_id=r["session_id"],
                    question=r["question"],
                    answer=r["answer"],
                    query_type=r.get("query_type", "conceptual"),
                    retries=r.get("retries", 0),
                    grounded=r.get("grounded", "grounded"),
                    sources=sources,
                    created_at=r.get("created_at"),
                )
            )

        return HistoryResponse(
            session_id=session_id,
            total_messages=len(items),
            messages=items,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session history: {str(e)}"
        )


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="List recent active conversation sessions",
    description="Returns recent conversation sessions for sidebar navigation."
)
async def list_recent_sessions(
    limit: int = Query(20, ge=1, le=50, description="Max sessions to return")
) -> SessionListResponse:
    try:
        rows = storage_repo.get_recent_sessions(limit=limit)
        sessions = [
            SessionListItem(
                session_id=row["session_id"],
                question=row["question"],
                created_at=str(row["created_at"]),
                turn_count=row["turn_count"],
            )
            for row in rows
        ]
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sessions: {str(e)}"
        )


@router.delete(
    "/history/{session_id}",
    summary="Clear conversation history",
    description="Deletes all queries associated with a specific session."
)
async def clear_session_history(session_id: str):
    try:
        deleted = storage_repo.clear_session_queries(session_id)
        return {"session_id": session_id, "deleted_count": deleted, "status": "cleared"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}"
        )
