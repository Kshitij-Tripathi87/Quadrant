import re
from typing import Literal
from src.graph.state import GraphState

def classify_intent_heuristic(question: str) -> Literal["conceptual", "how-to", "troubleshooting", "api_reference"]:
    """
    Ultra-low latency (<0.1ms) deterministic technical intent classifier.
    Avoids a 4-second network LLM roundtrip for standard developer questions.
    """
    q = question.lower().strip()
    if re.search(r"\b(how\s+to|how\s+do|how\s+can|example|tutorial|implement|guide|create|write|usage|setup)\b", q):
        return "how-to"
    if re.search(r"\b(error|exception|failed|bug|issue|troubleshoot|fix|why\s+does.*fail|traceback|warning|broken)\b", q):
        return "troubleshooting"
    if re.search(r"\b(parameter|signature|argument|return|method|field|attribute|type|schema|endpoint|syntax|class)\b", q):
        return "api_reference"
    return "conceptual"

def expand_query_fast(question: str) -> str:
    """
    Expands common technical terms without introducing external network latency.
    """
    cleaned = question.strip()
    q_lower = cleaned.lower()

    additions = []
    if "yield" in q_lower and "dependency" not in q_lower:
        additions.append("dependencies cleanup contextmanager")
    if "stategraph" in q_lower and "langgraph" not in q_lower:
        additions.append("LangGraph workflow conditional edges")
    if "@field_validator" in q_lower and "pydantic" not in q_lower:
        additions.append("Pydantic v2 validation")
    if "idempotency" in q_lower and "rest" not in q_lower:
        additions.append("REST API HTTP methods")

    if additions:
        return f"{cleaned} {' '.join(additions)}"
    return cleaned

def query_analysis_node(state: GraphState) -> dict:
    """
    Analyzes the user's question with zero network overhead.
    Instant classification and expansion preserves low latency.
    """
    question = state.get("question", "")
    steps = state.get("execution_steps", []).copy()
    steps.append("query_analysis")

    query_type = classify_intent_heuristic(question)
    expanded = expand_query_fast(question)

    return {
        "current_query": expanded,
        "query_type": query_type,
        "execution_steps": steps,
    }
