# Technology Stack & Tooling Document

## 1. Core Technology Selection Rationale

| Layer | Component | Selected Technology | Rationale & Alternatives Considered |
|---|---|---|---|
| **Programming Language** | Runtime | **Python 3.11** | Industry standard for AI/ML engineering, mature LangGraph & LangChain ecosystem, high-performance async features. |
| **Workflow Orchestration** | Graph Engine | **LangGraph (`langgraph`)** | StateGraph architecture enables cyclic self-corrective loops (CRAG), conditional edges, node inspection, and state isolation. Superior to linear DAGs (e.g. standard chains). |
| **API Framework** | Web Server | **FastAPI + Uvicorn** | High-performance asynchronous REST API, native OpenAPI/Swagger documentation, robust Pydantic v2 data validation, simple background task support. |
| **Data Validation** | Schema Typing | **Pydantic v2** | High-speed C-based validation, automatic JSON schema generation for LLM structured output parsing (`with_structured_output`). |
| **Vector Database** | Embedding Store | **ChromaDB** | Embedded, serverless, zero external infrastructure required. Excellent metadata filtering, persistence to disk, and seamless LangChain integration. |
| **Embeddings** | Text Vectorization | **FastEmbed / Sentence-Transformers (`all-MiniLM-L6-v2`)** + **OpenAI / Gemini Embeddings** | Dual-strategy: Local fast embedding model (`all-MiniLM-L6-v2`) runs completely offline with zero API latency/rate limits, with instant toggle to OpenAI `text-embedding-3-small` or Gemini Embeddings via config. |
| **LLM Inference** | Intelligence Engine | **Multi-Provider Adapter (Groq / OpenAI / Gemini / Anthropic)** | Defaults to high-throughput, low-cost models: **Groq (`llama-3.3-70b-versatile`)**, **OpenAI (`gpt-4o-mini`)**, or **Gemini Flash**. Easily configured via single `.env` setting. |
| **Search Fallback** | External Retrieval | **DuckDuckGo / Tavily Search** | Fallback when vector store docs do not answer query. DuckDuckGo requires no API key; Tavily offers AI-optimized snippets if API key is provided. |
| **Persistence** | Data & Feedback Store | **SQLite (`aiosqlite` / `sqlite3`)** | Zero-config, lightweight relational storage for user feedback (`POST /feedback`), query logs, and session conversations. |
| **Web Frontend** | User Interface | **Modern Embedded Web App (HTML5 / Vanilla CSS / JS)** + **Optional Streamlit** | Clean, responsive UI with real-time streaming, collapsible source drawer, citation badges, thumbs-up/down feedback controls, and document drag-and-drop. |
| **Testing & Quality** | Test Suite | **Pytest + HTTPX + Coverage** | Async test client for FastAPI, mock LLM fixtures for deterministic CI/CD testing. |

---

## 2. Dependency Breakdown (`requirements.txt`)

```text
# Web Framework & Core
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
python-multipart>=0.0.9
python-dotenv>=1.0.1
aiosqlite>=0.20.0

# LangChain & LangGraph Ecosystem
langgraph>=0.1.0
langchain>=0.2.0
langchain-core>=0.2.0
langchain-community>=0.2.0
langchain-text-splitters>=0.2.0

# LLM Providers (Multi-Provider Support)
langchain-groq>=0.1.0
langchain-openai>=0.1.0
langchain-google-genai>=1.0.0
langchain-anthropic>=0.1.0

# Vector Store & Embeddings
chromadb>=0.5.0
fastembed>=0.3.0
sentence-transformers>=3.0.0

# Search & Scraping
duckduckgo-search>=6.0.0
tavily-python>=0.3.0
beautifulsoup4>=4.12.0
httpx>=0.27.0

# Testing & Dev
pytest>=8.2.0
pytest-asyncio>=0.23.0
```

---

## 3. Environment Configuration (`.env.example`)

```bash
# Application Configuration
APP_NAME="RAG Technical Documentation Assistant"
APP_ENV="development"
PORT=8000
HOST="0.0.0.0"

# LLM Provider Configuration: "groq" | "openai" | "gemini" | "anthropic"
DEFAULT_LLM_PROVIDER="groq"
GROQ_API_KEY=""
OPENAI_API_KEY=""
GEMINI_API_KEY=""
ANTHROPIC_API_KEY=""

# Model Names
GROQ_MODEL="llama-3.3-70b-versatile"
OPENAI_MODEL="gpt-4o-mini"
GEMINI_MODEL="gemini-1.5-flash"

# Embedding Configuration: "fastembed" | "openai" | "huggingface"
EMBEDDING_PROVIDER="fastembed"
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"

# Search Fallback: "duckduckgo" | "tavily"
SEARCH_PROVIDER="duckduckgo"
TAVILY_API_KEY=""

# Retrieval & Evaluation Parameters
TOP_K_RETRIEVAL=4
MAX_RETRIES=2
SIMILARITY_THRESHOLD=0.7

# Storage Paths
CHROMA_PERSIST_DIRECTORY="./data/chroma_db"
SQLITE_DB_PATH="./data/app_storage.db"
DOCS_DIRECTORY="./data/raw_documents"
```

---

## 4. Multi-Provider LLM Factory Pattern

To guarantee that the user and evaluators can run the project regardless of which API key they have (or even with a free Groq or Gemini key), we implement an extensible **LLM Factory**:

```python
# app/core/llm.py
from langchain_core.language_models.chat_models import BaseChatModel

def get_llm(temperature: float = 0.0) -> BaseChatModel:
    provider = settings.DEFAULT_LLM_PROVIDER.lower()
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=settings.GROQ_MODEL, temperature=temperature, api_key=settings.GROQ_API_KEY)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=settings.OPENAI_MODEL, temperature=temperature, api_key=settings.OPENAI_API_KEY)
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, temperature=temperature, google_api_key=settings.GEMINI_API_KEY)
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=temperature, api_key=settings.ANTHROPIC_API_KEY)
    raise ValueError(f"Unsupported LLM provider: {provider}")
```

This ensures complete freedom and zero vendor lock-in for Express Analytics evaluators.
