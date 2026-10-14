import pytest
from src.graph.edges import route_after_document_grading
from src.graph.state import GraphState, DocumentChunk

def test_routing_edge_relevant_docs_found():
    state: GraphState = {
        "question": "What is dependency injection?",
        "relevant_documents": [
            DocumentChunk(content="FastAPI dependency injection...", metadata={})
        ],
        "retry_count": 0,
        "max_retries": 2,
    }
    decision = route_after_document_grading(state)
    assert decision == "generate"

def test_routing_edge_retry_triggered():
    state: GraphState = {
        "question": "Unrelated question?",
        "relevant_documents": [],
        "retry_count": 0,
        "max_retries": 2,
    }
    decision = route_after_document_grading(state)
    assert decision == "rewrite"

def test_routing_edge_max_retries_exceeded():
    state: GraphState = {
        "question": "Unrelated question?",
        "relevant_documents": [],
        "retry_count": 2,
        "max_retries": 2,
    }
    decision = route_after_document_grading(state)
    assert decision == "web_search"
