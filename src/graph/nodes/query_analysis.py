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

def resolve_follow_up_context(question: str, chat_history: list) -> str:
    """
    Enables intelligent multi-turn conversation memory by expanding follow-up
    questions containing pronouns (it, that, this, etc.) with key technical terms
    from the previous user turn.
    """
    if not chat_history:
        return question

    q_lower = question.lower()
    has_pronoun = bool(re.search(r"\b(it|this|that|its|these|those)\b", q_lower)) or len(question.split()) <= 4
    if has_pronoun:
        # Find the most recent user turn
        last_user_q = ""
        for turn in reversed(chat_history):
            if turn.get("role") == "user":
                last_user_q = turn.get("content", "")
                break
        if last_user_q:
            common = {"how", "what", "when", "where", "which", "does", "using", "with", "from", "have", "this", "that", "show", "example", "please", "code"}
            prior_terms = [w for w in re.findall(r"[a-zA-Z_]{4,}", last_user_q) if w.lower() not in common]
            if prior_terms:
                contextual_subject = " ".join(prior_terms[:3])
                return f"{question} ({contextual_subject})"
    return question

def query_analysis_node(state: GraphState) -> dict:
    """
    Analyzes the user's question with zero network overhead.
    Instant classification and expansion preserves low latency.
    """
    question = state.get("question", "")
    chat_history = state.get("chat_history", [])
    steps = state.get("execution_steps", []).copy()
    steps.append("query_analysis")

    # Contextualize follow-up questions using session conversation memory
    contextualized_q = resolve_follow_up_context(question, chat_history)
    query_type = classify_intent_heuristic(question)
    expanded = expand_query_fast(contextualized_q)

    return {
        "current_query": expanded,
        "query_type": query_type,
        "execution_steps": steps,
    }
