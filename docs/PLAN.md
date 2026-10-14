# Master Implementation Plan & Roadmap

## 1. Project Directory Structure

```
RAG_Project_sample/
│
├── .env.example                     # Environment template
├── README.md                        # Comprehensive documentation & evaluation writeup
├── requirements.txt                 # Dependencies
│
├── docs/                            # Core specification documentation
│   ├── PRD.md                       # Product Requirements Document
│   ├── ARCHITECTURE.md              # System Architecture & LangGraph Design
│   ├── TECH_STACK.md                # Tech Stack & Providers Document
│   └── PLAN.md                      # Master Implementation Roadmap
│
├── data/                            # Persistent data storage
│   ├── raw_documents/               # Seed technical documentation (FastAPI, LangGraph, Pydantic)
│   ├── chroma_db/                   # ChromaDB vector store persistent files
│   └── app_storage.db               # SQLite database for feedback and sessions
│
├── src/                             # Core Python Package
│   ├── __init__.py
│   ├── config.py                    # Pydantic Settings & environment loader
│   │
│   ├── core/                        # Core AI & LLM components
│   │   ├── __init__.py
│   │   ├── llm.py                   # Multi-provider LLM Factory (Groq, OpenAI, Gemini)
│   │   ├── embeddings.py            # Embedding model factory (FastEmbed, HuggingFace, OpenAI)
│   │   └── vector_store.py          # ChromaDB client & retriever manager
│   │
│   ├── ingestion/                   # Ingestion & Chunking pipeline
│   │   ├── __init__.py
│   │   ├── loader.py                # Markdown, text, HTML, and URL loaders
│   │   ├── chunker.py               # MarkdownHeaderTextSplitter + RecursiveSplitter
│   │   └── indexer.py               # Document indexing pipeline & seed script
│   │
│   ├── graph/                       # LangGraph Self-Corrective Engine
│   │   ├── __init__.py
│   │   ├── state.py                 # GraphState schema definition
│   │   ├── nodes/                   # Graph nodes
│   │   │   ├── __init__.py
│   │   │   ├── query_analysis.py    # Node 1: Query classification & query rewriting
│   │   │   ├── retriever.py         # Node 2: Vector retrieval
│   │   │   ├── document_grader.py   # Node 3: LLM relevance evaluation (CRAG)
│   │   │   ├── query_rewriter.py    # Node 4: Query reformulation for retry
│   │   │   ├── generator.py         # Node 5: Citation-grounded answer generation
│   │   │   ├── hallucination.py     # Node 6: Groundedness check (Self-RAG)
│   │   │   └── web_search.py        # Node 7: Web search fallback (DuckDuckGo/Tavily)
│   │   ├── edges.py                 # Conditional routing edges
│   │   └── workflow.py              # Compiled StateGraph builder
│   │
│   ├── storage/                     # Persistence & SQLite
│   │   ├── __init__.py
│   │   ├── database.py              # SQLite connection & schema initialization
│   │   └── repository.py            # Queries, sessions, and feedback CRUD
│   │
│   └── api/                         # FastAPI Web Application
│       ├── __init__.py
│       ├── main.py                  # FastAPI app entry point & middleware
│       ├── schemas.py               # Pydantic request/response models
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── query.py             # POST /query endpoint
│       │   ├── ingest.py            # POST /ingest endpoint
│       │   ├── documents.py         # GET /documents endpoint
│       │   ├── feedback.py          # POST /feedback endpoint
│       │   └── health.py            # GET /health & status endpoint
│       └── static/                  # Modern Web UI assets (HTML, CSS, JS)
│           ├── index.html           # Sleek interactive chat UI
│           ├── styles.css           # Premium modern styles (glassmorphism, dark mode)
│           └── app.js               # Frontend interaction logic
│
└── tests/                           # Test suite
    ├── __init__.py
    ├── conftest.py                  # Pytest fixtures & mocks
    ├── test_ingestion.py            # Unit tests for chunking & embedding
    ├── test_graph_nodes.py          # Unit tests for LangGraph nodes & routing
    └── test_api_endpoints.py        # Integration tests for FastAPI endpoints
```

---

## 2. Phase-by-Phase Execution Plan

### Phase 1: Environment & Scaffolding
- Set up `requirements.txt` with tested, compatible versions for Python 3.11.
- Install dependencies into `.venv`.
- Establish `.env.example` and `src/config.py` using `pydantic-settings`.
- Implement `src/core/llm.py` with multi-provider fallback.
- **Verification**: Run diagnostic script verifying LLM factory and embeddings load cleanly.

### Phase 2: Technical Document Corpus & Ingestion Pipeline
- Download and prepare 4 rich technical markdown files in `data/raw_documents/`:
  - `fastapi_overview_dependencies.md`: FastAPI dependency injection, sub-dependencies, yield.
  - `langgraph_core_concepts.md`: StateGraph, nodes, conditional edges, retry limits.
  - `pydantic_v2_validation.md`: Field validation, BaseModel, serialization.
  - `rest_api_best_practices.md`: Status codes, idempotency, error formats.
- Implement `src/ingestion/loader.py` and `src/ingestion/chunker.py` with the two-tier chunking strategy (`MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter`).
- Implement `src/ingestion/indexer.py` to index into ChromaDB with deterministic IDs and rich metadata.
- **Verification**: Run indexing script; verify chunk count, metadata extraction, and vector similarity search.

### Phase 3: LangGraph Self-Corrective Workflow
- Implement `src/graph/state.py` defining the comprehensive `GraphState`.
- Implement individual nodes with structured LLM outputs:
  - `query_analysis.py`: Query expansion and classification.
  - `retriever.py`: Vector search with metadata retention.
  - `document_grader.py`: Evaluator scoring each chunk as "relevant" or "irrelevant".
  - `query_rewriter.py`: Query transformation on failed retrieval.
  - `web_search.py`: Fallback search.
  - `generator.py`: Grounded generation with citation references.
  - `hallucination.py`: Self-RAG groundedness check.
- Implement conditional routing edges (`edges.py`) with retry counter check:
  - `route_after_grading(state)` -> if all irrelevant & retries < max -> rewrite -> retrieve; if relevant -> generate; if retries >= max -> fallback.
- Compile and test graph execution locally with end-to-end trace logging.
- **Verification**: Run unit tests testing both the happy path (relevant docs found) and corrective path (irrelevant docs -> rewrite loop -> fallback).

### Phase 4: Storage, Persistence & FastAPI REST API
- Implement SQLite persistence for conversation sessions and feedback tracking.
- Implement API routers:
  - `POST /query`: Invokes LangGraph, records query log, returns answer, sources, and execution trace.
  - `POST /ingest`: Accepts file uploads (`.md`, `.txt`, `.pdf`) or URLs, runs ingestion pipeline live.
  - `GET /documents`: Queries ChromaDB and SQLite registry for indexed documents and chunk statistics.
  - `POST /feedback`: Stores user thumbs up/down rating and comments.
  - `GET /health`: Healthcheck endpoint.
- Add CORS middleware, request logging, and structured error responses.
- **Verification**: Execute integration tests against all API endpoints using `httpx.AsyncClient`.

### Phase 5: Modern Interactive Web Interface
- Create an embedded, responsive UI served directly at `/` by FastAPI.
- Features:
  - Real-time Q&A with syntax-highlighted code.
  - Interactive source citation drawer (click to inspect retrieved chunk context and headers).
  - Workflow step indicators (shows Query Analysis -> Retrieval -> Grading -> Generation status).
  - Document ingestion tab (upload files or enter URLs to index live).
  - Thumbs up/down feedback widget on every assistant answer.
- **Verification**: Verify UI rendering and end-to-end question answering in browser.

### Phase 6: Documentation, README & Evaluation Deliverables
- Write production-grade `README.md` addressing every point in the take-home prompt:
  - Project Overview & Architecture diagram.
  - Setup instructions (environment, API keys, local startup).
  - Example API requests & responses (`curl` / JSON examples).
  - Thought process, design decisions & tradeoffs (chunking strategy, vector store choice, retry limit rationale).
  - What would be improved with more time (hybrid BM25+dense search, semantic caching, streaming tokens).
- Verify all code and tests pass cleanly.
