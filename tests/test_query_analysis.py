import pytest
from src.graph.nodes.query_analysis import (
    classify_intent_heuristic,
    expand_query_fast,
    query_analysis_node,
)
from src.graph.state import GraphState

def test_intent_classification():
    assert classify_intent_heuristic("How do I implement dependencies with yield in FastAPI?") == "how-to"
    assert classify_intent_heuristic("Why does my LangGraph StateGraph fail with recursion error?") == "troubleshooting"
    assert classify_intent_heuristic("What is the return type and parameter signature for get_db?") == "api_reference"
    assert classify_intent_heuristic("Explain the difference between RPC and RESTful architecture.") == "conceptual"

def test_query_expansion():
    # Expands yield with cleanup contextmanager
    expanded = expand_query_fast("How does yield work?")
    assert "dependencies cleanup contextmanager" in expanded

    # Expands stategraph with workflow conditional edges
    expanded_graph = expand_query_fast("What is StateGraph?")
    assert "LangGraph workflow conditional edges" in expanded_graph

    # Preserves non-triggering queries
    normal = "Simple question about python"
    assert expand_query_fast(normal) == normal

def test_query_analysis_node():
    state: GraphState = {
        "question": "How to implement dependencies with yield in FastAPI?",
        "execution_steps": [],
    }
    result = query_analysis_node(state)
    assert result["query_type"] == "how-to"
    assert "current_query" in result
    assert "dependencies cleanup contextmanager" in result["current_query"]
    assert "query_analysis" in result["execution_steps"]
