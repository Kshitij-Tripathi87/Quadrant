import pytest
from src.graph.nodes.hallucination import verify_citations_fast, hallucination_check_node
from src.graph.state import GraphState, DocumentChunk

def test_verify_citations_fast_with_source_tags():
    docs = [
        DocumentChunk(
            content="FastAPI dependency injection enables code reuse.",
            metadata={"title": "FastAPI Guide", "source": "fastapi.md"}
        )
    ]
    # Answer cites source properly
    gen_with_citation = "FastAPI uses Depends for dependencies [Source: FastAPI Guide > Dependencies]."
    assert verify_citations_fast(gen_with_citation, docs) is True

def test_verify_citations_fast_with_disclaimer():
    docs = []
    disclaimer = "The indexed documentation does not contain sufficient details to answer this question."
    assert verify_citations_fast(disclaimer, docs) is True

def test_hallucination_node_grounded():
    state: GraphState = {
        "generation": "FastAPI uses Depends [Source: FastAPI Guide].",
        "relevant_documents": [
            DocumentChunk(content="FastAPI guide content", metadata={"title": "FastAPI Guide"})
        ],
        "execution_steps": [],
    }
    result = hallucination_check_node(state)
    assert result["hallucination_grade"] == "grounded"
    assert "hallucination_check" in result["execution_steps"]
