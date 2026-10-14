from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.graph.state import GraphState
from src.core.llm import get_llm

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a specialized query reformulation assistant for a technical documentation search engine.
The previous search query failed to retrieve relevant documents.
Look at the initial question and the previous query attempt.
Formulate an improved, alternative search query:
- Strip complex conversational grammar.
- Focus on the core technical entities, fundamental keywords, or related concepts.
- Broaden terms slightly if the previous query was overly restrictive.
Respond ONLY with the reformulated query string without quotes or preamble."""
    ),
    (
        "human",
        "Initial Question: {question}\nPrevious Query: {current_query}\nRetry Attempt: {retry_count}"
    )
])

def query_rewriter_node(state: GraphState) -> dict:
    """
    Reformulates the query when retrieval yields zero relevant documents.
    Increments retry_count.
    """
    question = state.get("question", "")
    current_query = state.get("current_query") or question
    retry_count = state.get("retry_count", 0) + 1
    steps = state.get("execution_steps", []).copy()
    steps.append(f"query_rewriter_retry_{retry_count}")

    print(f"[Query Rewriter Node] Initiating retry #{retry_count} for query: '{current_query}'")

    try:
        llm = get_llm(temperature=0.2)
        chain = REWRITE_PROMPT | llm | StrOutputParser()
        new_query = chain.invoke({
            "question": question,
            "current_query": current_query,
            "retry_count": retry_count,
        }).strip()
    except Exception as e:
        print(f"[Query Rewriter] Error rewriting query: {e}")
        new_query = f"{question} documentation guide reference"

    print(f"[Query Rewriter Node] Rewritten query: '{new_query}'")

    return {
        "current_query": new_query,
        "retry_count": retry_count,
        "execution_steps": steps,
    }
