# Product Requirements Document (PRD)

**Project Name:** Self-Corrective RAG Technical Documentation Assistant  
**Target Organization:** Express Analytics — AI/ML Engineer Take-Home  
**Document Version:** 2.0.0 (Comprehensive Engineering Specification)  
**Status:** Approved for Implementation  
**Primary Stack:** Python 3.11+, LangGraph, FastAPI, ChromaDB, Pydantic v2  

---

## 1. Executive Summary & Problem Framing

### 1.1 Problem Statement
Modern software engineering teams spend an estimated 20–30% of their time navigating complex API documentation, framework guides, and release notes. While large language models (LLMs) can answer programming questions, standard Naive RAG (Retrieve-then-Generate) architectures frequently fail when applied to technical documentation:
1. **Vocabulary Mismatch & Semantic Drift:** Natural language user queries (e.g., *"How do I close connections after returning an HTTP response?"*) rarely match the exact terminology used in official manuals (e.g., *"Dependencies with `yield` and contextmanager teardown in ASGI"*).
2. **Context Poisoning & Hallucinations:** Naive retrieval blindly passes top-$k$ vector matches into the prompt context. If the chunks are only superficially related or describe an unrelated module, the LLM hallucinates non-existent function arguments, invalid imports, or outdated syntax.
3. **Absence of Self-Correction:** When retrieval fails to return relevant information, standard pipelines have no mechanism to evaluate chunk quality, reformulate the search query, or route to an alternative fallback path.
4. **Lack of Auditability & Citations:** Developers cannot verify whether the code snippet provided is grounded in official documentation or generated from outdated training data.

### 1.2 System Vision & Core Value Proposition
The **Technical Documentation Assistant** is an agentic, self-corrective RAG system designed specifically for software engineering documentation. Built on a cyclic **LangGraph `StateGraph`**, it integrates principles from **Corrective RAG (CRAG)** and **Self-RAG**:
- It **analyzes and expands** ambiguous user queries with domain synonyms and intent classification.
- It **evaluates retrieved chunks** using an LLM Document Grader, filtering out irrelevant noise.
- It **iteratively rewrites queries and re-retrieves** if initial results fail relevance thresholds, bounded by a strict retry counter (`max_retries = 2`) to mathematically eliminate infinite execution loops.
- It provides a **graceful fallback** (web search via DuckDuckGo/Tavily or high-confidence disclaimers) when documentation lacks coverage.
- It enforces **strict inline citations** and runs an automated **Self-RAG Groundedness Check** to ensure zero code hallucinations.
- It exposes a production-ready **FastAPI** REST interface, conversational session persistence, and user feedback capture.

---

## 2. System Objectives & Measurable KPIs

| Metric | Target | Rationale & Measurement Method |
|---|---|---|
| **Retrieval Relevance Precision** | $\ge 90\%$ | Percentage of chunks passed to the generator that are rated "relevant" by the document grader. |
| **Groundedness / Hallucination Rate** | $0\%$ Hallucinations | Evaluated via automated Self-RAG verification node; all claims and code must map to retrieved chunk content. |
| **Citation Coverage** | $100\%$ | Every substantive technical answer must cite its document title, header path, and source identifier. |
| **Graph Convergence Guarantee** | $100\%$ | Guarantee that every graph execution reaches `END` within a finite number of steps (max 2 rewrites). |
| **P95 Latency (Fast Path)** | $\le 2.5\text{s}$ | Direct retrieval + grading + generation path with high-speed LLM inference (e.g. Groq LLaMA-3.3-70B or GPT-4o-mini). |
| **P95 Latency (Corrective Path)** | $\le 5.0\text{s}$ | Loop including 1 query rewrite and secondary retrieval. |

---

## 3. Personas & User Journeys

### 3.1 Target Personas
1. **Backend & AI Engineer (Primary User):** Wants precise syntax, copy-pasteable code snippets, explanation of lifecycle hooks (e.g. FastAPI `yield` dependencies, LangGraph conditional edges), and links to source docs.
2. **Technical Lead / Reviewer (Evaluator):** Evaluates system correctness, architectural reasoning, graph state management, chunking strategy tradeoffs, and error handling.
3. **Documentation Maintainer (Admin):** Ingests new Markdown files, API references, or URLs and monitors user feedback (`POST /feedback`).

### 3.2 User Journeys & Concrete Scenarios

#### Scenario A: Specific How-To Query (Happy Path)
- **User Action:** Submits *"How do I implement dependency injection with cleanup in FastAPI?"*
- **Query Analysis:** Classifies intent as `how-to`. Expands query to *"FastAPI dependency injection yield context manager teardown cleanup db session"*.
- **Retrieval:** ChromaDB returns top-4 chunks from `fastapi_dependencies.md`.
- **Grading:** Grader node scores chunks; 3 chunks are rated `relevant` (discussing `yield` and teardown), 1 irrelevant chunk is pruned.
- **Routing:** Edge detects $\ge 1$ relevant chunk $\rightarrow$ routes directly to `generator`.
- **Generation:** Synthesizes answer showing `async def get_db(): try: yield db finally: db.close()` with inline citation `[Source: FastAPI Dependencies > Dependencies with yield]`.
- **Verification:** Self-RAG node grades answer as `grounded` $\rightarrow$ returns 200 OK to user.

#### Scenario B: Ambiguous Query (Self-Correction Loop)
- **User Action:** Submits *"What is the state object?"*
- **Query Analysis:** Detects ambiguity. Initial expanded query: *"state object schema"*.
- **Retrieval:** First search returns generic chunks that fail relevance scoring.
- **Grading:** All candidate chunks scored `irrelevant`.
- **Routing:** Conditional edge checks: `relevant == 0` and `retry_count (0) < max_retries (2)` $\rightarrow$ routes to `query_rewriter`.
- **Query Rewriting:** Rewriter analyzes query failure, reformulates to *"LangGraph StateGraph central state schema TypedDict data flow"*, and increments `retry_count = 1`.
- **Secondary Retrieval:** ChromaDB retrieves `langgraph_concepts.md` chunks.
- **Secondary Grading:** Chunks graded `relevant` $\rightarrow$ routes to `generator` $\rightarrow$ answers accurately.

#### Scenario C: Out-of-Corpus Query (Fallback Path)
- **User Action:** Submits *"How do I configure Kubernetes ingress controller with TLS certificates?"*
- **Ingested Corpus:** Only covers FastAPI, LangGraph, Pydantic, REST principles.
- **Execution:** Retrieval returns 0 relevant chunks $\rightarrow$ rewriter retries $\rightarrow$ second retrieval still returns 0 relevant chunks $\rightarrow$ `retry_count` reaches 2.
- **Fallback Routing:** `retry_count >= max_retries` $\rightarrow$ routes to `web_search_fallback` (DuckDuckGo/Tavily) or Fallback Generator.
- **Output:** Returns a transparent, grounded answer with clear disclaimer: *"This topic is not covered in the internal documentation. Based on external fallback search..."* or polite refusal without hallucinating.

---

## 4. Functional Specifications

### 4.1 Document Ingestion & Two-Tier Chunking Engine

#### Multi-Source Loaders
- **Local File Loader:** Recursively ingests `.md`, `.markdown`, `.txt`, `.html` files from `data/raw_documents/`.
- **Web URL Scraper:** Fetches HTML via `httpx`, removes navigational chrome, scripts, stylesheets, and footers with `BeautifulSoup`, and extracts clean readable markdown text.

#### Two-Tier Technical Chunking Strategy
Technical documentation requires specialized chunking because standard fixed-size character splitters break syntactic code blocks and sever headings from context.
1. **Tier 1: Markdown Structural Splitting (`MarkdownHeaderTextSplitter`)**
   - Headers tracked: `# Header_1`, `## Header_2`, `### Header_3`.
   - Each chunk receives a hierarchical `header_path` metadata field (e.g. `FastAPI Tutorial > Dependencies > Yield`).
2. **Tier 2: Code-Preserving Recursive Splitting (`RecursiveCharacterTextSplitter`)**
   - Chunk Size: `800` characters (~160–200 tokens), optimal for technical documentation paragraphs.
   - Chunk Overlap: `150` characters (~30–40 tokens), preventing context boundary loss.
   - Separators: `["\n\n```", "\n```\n", "\n\n", "\n", ". ", " ", ""]`. Prioritizing markdown code fences guarantees Python functions are never split in half.
3. **Deterministic Chunk Hashing:** Each chunk is assigned a deterministic UUID5 generated from `uuid5(NAMESPACE_DNS, f"{source}::{header_path}::{index}::{content[:50]}")`. This guarantees idempotent re-indexing without duplicate records.

### 4.2 Vector Database & Embeddings Architecture

#### ChromaDB Persistent Store
- **Collection Name:** `technical_docs`
- **Persistence Path:** `./data/chroma_db/`
- **Search Modes:** Cosine similarity search and Maximal Marginal Relevance (MMR) for diverse candidate retrieval.
- **Metadata Fields:** `source`, `title`, `header_path`, `chunk_id`, `chunk_index`, `char_count`, `ingested_at`, `source_type`.

#### Multi-Provider Embeddings
- **Default (Local Fast Embeddings):** `sentence-transformers/all-MiniLM-L6-v2` via `fastembed` / HuggingFace. Operates 100% locally with zero API cost, zero rate limits, and sub-15ms embedding latency.
- **Cloud Provider (Configurable):** OpenAI `text-embedding-3-small` or Google Gemini Embeddings selectable via `.env`.

### 4.3 LangGraph Self-Corrective State Machine

#### Comprehensive State Schema (`GraphState`)
```python
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict

class DocumentChunk(TypedDict, total=False):
    content: str
    metadata: Dict[str, Any]
    relevance_score: Optional[str]  # "relevant" | "irrelevant"
    reasoning: Optional[str]

class GraphState(TypedDict, total=False):
    question: str                      # Original raw user query
    current_query: str                 # Active query (rewritten or expanded)
    query_type: Optional[str]          # conceptual | how-to | troubleshooting | api_reference
    chat_history: List[Dict[str, str]] # Conversational session history
    documents: List[DocumentChunk]      # Candidate retrieved documents
    relevant_documents: List[DocumentChunk] # Evaluated relevant documents
    generation: Optional[str]          # Generated final response
    sources: List[Dict[str, Any]]      # Citations list (source, header_path, snippet)
    retry_count: int                   # Number of rewrites executed
    max_retries: int                   # Configurable max retries (default: 2)
    web_search_needed: bool            # True if external web search was invoked
    hallucination_grade: Optional[str] # "grounded" | "not grounded"
    execution_steps: List[str]         # Observability audit trail of executed nodes
```

#### Node Roles & Invariants
1. **Node 1: `query_analysis`**
   - *Input Invariant:* `state["question"]` is a non-empty string.
   - *Action:* Prompts LLM with structured output to classify query into `[conceptual, how-to, troubleshooting, api_reference]` and expand search terms.
   - *Output Invariant:* `state["current_query"]` is populated with expanded query; `state["query_type"]` is assigned.
2. **Node 2: `retriever`**
   - *Input Invariant:* `state["current_query"]` contains search string.
   - *Action:* Queries ChromaDB for top-$k$ chunks ($k=4$) with metadata.
   - *Output Invariant:* `state["documents"]` contains $k$ candidate `DocumentChunk` items.
3. **Node 3: `document_grader` (CRAG Core)**
   - *Input Invariant:* `state["documents"]` is populated.
   - *Action:* Evaluates each chunk individually using structured LLM output (`GradeChunk: binary_score: "relevant" | "irrelevant"`). Discards irrelevant noise.
   - *Output Invariant:* `state["relevant_documents"]` contains only verified relevant chunks.
4. **Node 4: `query_rewriter`**
   - *Input Invariant:* `len(state["relevant_documents"]) == 0` and `state["retry_count"] < state["max_retries"]`.
   - *Action:* Analyzes failed query, strips noisy grammar, injects technical synonyms, and increments `retry_count += 1`.
   - *Output Invariant:* `state["current_query"]` updated; `state["retry_count"]` incremented by 1. Edge loops back to `retriever`.
5. **Node 5: `web_search_fallback`**
   - *Input Invariant:* `len(state["relevant_documents"]) == 0` and `state["retry_count"] >= state["max_retries"]`.
   - *Action:* Invokes DuckDuckGo Search (zero API key required) or Tavily API to fetch up to 3 external documentation snippets.
   - *Output Invariant:* `state["relevant_documents"]` populated with external search results; `state["web_search_needed"] = True`.
6. **Node 6: `generator`**
   - *Input Invariant:* `state["relevant_documents"]` populated (or empty if fallback yielded zero results).
   - *Action:* Synthesizes grounded markdown response using strictly the provided context. Enforces citations in format `[Source: Title > Section]`.
   - *Output Invariant:* `state["generation"]` contains answer; `state["sources"]` contains structured citations.
7. **Node 7: `hallucination_check` (Self-RAG)**
   - *Input Invariant:* `state["generation"]` is populated.
   - *Action:* Evaluates whether claims in `generation` are supported by `relevant_documents`.
   - *Output Invariant:* `state["hallucination_grade"] = "grounded" | "not grounded"`.

#### State Transition & Routing Table
| From Node | Condition | Target Node | Rationale |
|---|---|---|---|
| `START` | Unconditional | `query_analysis` | Prepare and classify query. |
| `query_analysis` | Unconditional | `retriever` | Perform vector retrieval. |
| `retriever` | Unconditional | `document_grader` | Filter candidate chunks. |
| `document_grader` | `len(relevant_documents) > 0` | `generator` | Chunks pass relevance threshold $\rightarrow$ generate answer. |
| `document_grader` | `len(relevant_documents) == 0` AND `retry_count < max_retries` | `query_rewriter` | Retrieval failed $\rightarrow$ reformulate query. |
| `document_grader` | `len(relevant_documents) == 0` AND `retry_count >= max_retries` | `web_search_fallback` | Retries exhausted $\rightarrow$ search external web docs. |
| `query_rewriter` | Cyclic Edge | `retriever` | Re-retrieve using updated query. |
| `web_search_fallback` | Unconditional | `generator` | Generate answer using external search context. |
| `generator` | Unconditional | `hallucination_check` | Verify factual groundedness (Self-RAG). |
| `hallucination_check` | Unconditional | `END` | Return audited response to caller. |

---

## 5. API Interface Specification (FastAPI)

### 5.1 Endpoints Summary Table

| Method | Endpoint | Purpose | Request Body | Success Response | Status Codes |
|---|---|---|---|---|---|
| `POST` | `/api/v1/query` | Submit natural language question | `QueryRequest` | `QueryResponse` | `200`, `400`, `422`, `500` |
| `POST` | `/api/v1/ingest` | Ingest documents from URLs | `IngestRequest` | `IngestResponse` | `201`, `400`, `422`, `500` |
| `POST` | `/api/v1/ingest/upload` | Upload & index doc files | `Multipart/form-data` | `IngestResponse` | `201`, `400`, `422`, `500` |
| `GET` | `/api/v1/documents` | List indexed corpus & stats | None | `DocumentListResponse` | `200`, `500` |
| `POST` | `/api/v1/feedback` | Submit thumbs up/down rating | `FeedbackRequest` | `FeedbackResponse` | `201`, `400`, `422`, `500` |
| `GET` | `/api/v1/health` | Health & vector index status | None | `HealthResponse` | `200`, `503` |

---

## 6. Storage & Database Schema (SQLite)

To support observability, chat session memory, and user evaluation feedback without heavy external database dependencies, an embedded SQLite database is maintained at `./data/app_storage.db`:

```sql
-- Query Audit & Observability Log
CREATE TABLE IF NOT EXISTS queries (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    query_type TEXT,
    retries INTEGER DEFAULT 0,
    sources_json TEXT,
    grounded TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    query_id TEXT NOT NULL,
    rating TEXT CHECK(rating IN ('up', 'down')) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(query_id) REFERENCES queries(id)
);

-- Document Ingestion Registry
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source TEXT UNIQUE NOT NULL,
    title TEXT,
    chunk_count INTEGER DEFAULT 0,
    source_type TEXT CHECK(source_type IN ('file', 'url')),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Edge Cases & Resilience Strategy

| Edge Case | Failure Mode in Naive RAG | Self-Corrective RAG Mitigation |
|---|---|---|
| **Syntactically Malformed Query** (e.g. *"yield fastapi??? db"*) | Retrieval misses exact phrasing; LLM confuses yield with generator functions. | `query_analysis` normalizes punctuation and expands to *"FastAPI dependency injection with yield teardown db session"*. |
| **Out-of-Scope Query** (e.g. *"What is the capital of Japan?"*) | Retrieval returns irrelevant programming docs; LLM hallucinates an answer. | Document grader flags all chunks as `irrelevant` $\rightarrow$ triggers retry $\rightarrow$ reaches `max_retries` $\rightarrow$ issues clean disclaimer: *"The indexed technical documentation does not contain this information."* |
| **Code Snippet Cut in Half** | Broken syntax, missing closing brackets, invalid indentation. | `TechnicalDocumentChunker` splits on Markdown code fence boundaries (````python ... ````), preserving complete code blocks. |
| **Infinite Graph Rewrite Cycle** | Graph loops endlessly if no documents match query. | State tracks `retry_count` $\ge$ `max_retries` (2) as a strict numerical invariant, guaranteeing termination. |
| **External LLM Rate Limiting** | Pipeline crashes with 429 Too Many Requests. | Multi-Provider LLM Factory allows instant switching between Groq, OpenAI, and Gemini; local FastEmbed requires zero external API calls. |
