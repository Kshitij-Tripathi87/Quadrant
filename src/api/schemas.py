from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# --- /query models ---
class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="Natural language question to ask the documentation assistant.",
        json_schema_extra={"example": "How do I use yield in FastAPI dependencies?"},
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID to track conversation history.",
    )

class SourceCitation(BaseModel):
    source: str = Field(description="Origin source URL or file path.")
    title: str = Field(description="Title of the source document.")
    header_path: str = Field(description="Hierarchical section path.")
    snippet: str = Field(description="Brief text excerpt from the relevant chunk.")

class QueryResponse(BaseModel):
    query_id: str = Field(description="Unique ID for this query run.")
    session_id: str = Field(description="Session ID for chat memory.")
    answer: str = Field(description="Generated answer grounded in technical documentation.")
    query_type: str = Field(description="Classified intent (conceptual, how-to, troubleshooting, api_reference).")
    sources: List[SourceCitation] = Field(default_factory=list, description="Citations used in answer.")
    retries_used: int = Field(default=0, description="Number of query reformulations executed.")
    grounded: str = Field(description="Self-RAG Groundedness check result ('grounded' or 'not grounded').")
    execution_steps: List[str] = Field(default_factory=list, description="Nodes traversed in the LangGraph workflow.")
    execution_time_ms: float = Field(default=0.0, description="End-to-end execution latency in milliseconds.")

# --- /query/history models ---
class HistoryItem(BaseModel):
    id: str
    session_id: str
    question: str
    answer: str
    query_type: Optional[str] = "conceptual"
    retries: int = 0
    grounded: Optional[str] = "grounded"
    sources: List[SourceCitation] = Field(default_factory=list)
    created_at: Optional[str] = None

class HistoryResponse(BaseModel):
    session_id: str
    total_messages: int
    messages: List[HistoryItem]

class SessionListItem(BaseModel):
    session_id: str
    question: str
    created_at: str
    turn_count: int

class SessionListResponse(BaseModel):
    sessions: List[SessionListItem]


# --- /ingest models ---
class IngestRequest(BaseModel):
    urls: Optional[List[str]] = Field(
        default=None,
        description="List of documentation URLs to crawl and index.",
        json_schema_extra={"example": ["https://fastapi.tiangolo.com/tutorial/dependencies/"]},
    )

class IngestResponse(BaseModel):
    status: str
    indexed_documents: int
    total_chunks: int
    message: str

# --- /documents models ---
class DocumentItem(BaseModel):
    source: str
    title: str
    chunk_count: int
    source_type: Optional[str] = "file"
    ingested_at: Optional[str] = None

class DocumentListResponse(BaseModel):
    total_documents: int
    total_vectors: int
    documents: List[DocumentItem]

# --- /feedback models ---
class FeedbackRequest(BaseModel):
    query_id: str = Field(..., description="ID of the query being rated.")
    rating: Literal["up", "down"] = Field(..., description="'up' for thumbs up, 'down' for thumbs down.")
    comment: Optional[str] = Field(default=None, max_length=1000, description="Optional user commentary.")

class FeedbackResponse(BaseModel):
    feedback_id: str
    status: str = "recorded"
    message: str

# --- /health models ---
class HealthResponse(BaseModel):
    status: str
    app_name: str
    llm_provider: str
    model_name: Optional[str] = "gemini-3.5-flash-lite"
    embedding_provider: str
    vector_store_count: int

