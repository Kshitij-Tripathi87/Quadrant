from src.graph.state import GraphState, DocumentChunk
from src.core.vector_store import vector_store_manager
from src.config import settings

def retriever_node(state: GraphState) -> dict:
    """
    Retrieves the top-k candidate chunks from ChromaDB using the active current_query.
    """
    query = state.get("current_query") or state.get("question", "")
    steps = state.get("execution_steps", []).copy()
    steps.append("retriever")

    print(f"[Retriever Node] Querying ChromaDB with: '{query}'")
    docs = vector_store_manager.similarity_search(query=query, k=settings.TOP_K_RETRIEVAL)

    formatted_docs: list[DocumentChunk] = []
    for doc in docs:
        formatted_docs.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "relevance_score": None,
            "reasoning": None,
        })

    print(f"[Retriever Node] Retrieved {len(formatted_docs)} candidate chunks.")
    return {
        "documents": formatted_docs,
        "execution_steps": steps,
    }
