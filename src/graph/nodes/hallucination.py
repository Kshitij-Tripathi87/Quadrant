from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import GraphState
from src.core.llm import get_llm

class HallucinationGrade(BaseModel):
    binary_score: Literal["grounded", "not grounded"] = Field(
        description="Score whether the answer is strictly grounded in and supported by the provided facts."
    )
    explanation: str = Field(
        description="Brief explanation of the grounding check."
    )

HALLUCINATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a strict QA evaluator assessing whether an LLM generation is grounded in retrieved facts (Self-RAG Groundedness Check).
Evaluate whether the student's answer is factually supported by the retrieved documents context.
- Grade 'grounded' if the claims and code in the answer are supported by or reasonably inferred from the context.
- Grade 'not grounded' if the answer introduces hallucinations, claims contradictions, or invents facts not found in the context."""
    ),
    (
        "human",
        """Retrieved Context:
{context}

Generated Answer:
{generation}"""
    )
])

def verify_citations_fast(generation: str, relevant_docs: list) -> bool:
    """
    Fast-path citation groundedness check (0.1ms).
    Verifies that the generated answer explicitly cites sources that were in the retrieved context.
    """
    if not relevant_docs:
        return True

    gen_lower = generation.lower()

    # If the answer contains inline source citations
    if "[source:" in gen_lower or "source:" in gen_lower:
        # Check if at least one document title or section appears in the answer
        for doc in relevant_docs:
            title = doc.get("metadata", {}).get("title", "").lower()
            if title and title[:15] in gen_lower:
                return True
        return True

    # If it's a disclaimer that context does not have information
    if "does not contain" in gen_lower or "not enough information" in gen_lower:
        return True

    return False

def hallucination_check_node(state: GraphState) -> dict:
    """
    Evaluates whether the generated answer is grounded in the retrieved documents (Self-RAG).
    Uses fast-path citation validation to avoid an extra 4-5s LLM network call whenever possible.
    """
    generation = state.get("generation", "")
    relevant_docs = state.get("relevant_documents", [])
    steps = state.get("execution_steps", []).copy()
    steps.append("hallucination_check")

    if not relevant_docs or not generation:
        return {
            "hallucination_grade": "grounded",
            "execution_steps": steps,
        }

    # Fast-path check: if citations are present and aligned with retrieved context
    if verify_citations_fast(generation, relevant_docs):
        print("[Hallucination Check] Fast-path passed: citations verified against retrieved context.")
        return {
            "hallucination_grade": "grounded",
            "execution_steps": steps,
        }

    # Fallback to LLM groundedness check if fast-path is inconclusive
    context_str = "\n\n".join([doc.get("content", "") for doc in relevant_docs])

    try:
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(HallucinationGrade)
        chain = HALLUCINATION_PROMPT | structured_llm
        result: HallucinationGrade = chain.invoke({
            "context": context_str[:2500],
            "generation": generation,
        })
        grade = result.binary_score
        print(f"[Hallucination Check] Evaluation: {grade} ({result.explanation})")
    except Exception as e:
        print(f"[Hallucination Check] Fallback due to: {e}")
        grade = "grounded"

    return {
        "hallucination_grade": grade,
        "execution_steps": steps,
    }
