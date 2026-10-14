from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import GraphState
from src.core.llm import get_llm

class QueryAnalysisOutput(BaseModel):
    expanded_query: str = Field(
        description="Expanded, keyword-rich search query optimized for vector similarity retrieval."
    )
    query_type: Literal["conceptual", "how-to", "troubleshooting", "api_reference"] = Field(
        description="Technical intent classification of the question."
    )
    reasoning: str = Field(
        description="Brief explanation of the expansion and classification decisions."
    )

QUERY_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert AI Technical Query Analyzer for software engineering documentation.
Analyze the user's technical question.
1. Classify the query into one of:
   - 'conceptual': Explaining architectural concepts, theory, design patterns.
   - 'how-to': Step-by-step guides, usage tutorials, how to perform a task.
   - 'troubleshooting': Debugging errors, edge cases, fixing unexpected behaviors.
   - 'api_reference': Specific classes, methods, parameters, return types, schemas.
2. Rewrite or expand the query to maximize semantic vector search retrieval:
   - Resolve ambiguous terms or missing context.
   - Include key technical synonyms, relevant library names (FastAPI, LangGraph, Pydantic, etc.).
   - Keep the expanded query concise, focused, and free of conversational filler."""
    ),
    ("human", "User question: {question}")
])

def query_analysis_node(state: GraphState) -> dict:
    """
    Analyzes the user's question, classifying intent and expanding it for retrieval.
    """
    question = state.get("question", "")
    steps = state.get("execution_steps", []).copy()
    steps.append("query_analysis")

    try:
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(QueryAnalysisOutput)
        chain = QUERY_ANALYSIS_PROMPT | structured_llm
        result: QueryAnalysisOutput = chain.invoke({"question": question})

        return {
            "current_query": result.expanded_query,
            "query_type": result.query_type,
            "execution_steps": steps,
        }
    except Exception as e:
        print(f"[Query Analysis Node] Fallback due to: {e}")
        return {
            "current_query": question,
            "query_type": "conceptual",
            "execution_steps": steps,
        }
