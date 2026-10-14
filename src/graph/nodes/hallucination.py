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

def hallucination_check_node(state: GraphState) -> dict:
    """
    Evaluates whether the generated answer is grounded in the retrieved documents (Self-RAG).
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

    context_str = "\n\n".join([doc.get("content", "") for doc in relevant_docs])

    try:
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(HallucinationGrade)
        chain = HALLUCINATION_PROMPT | structured_llm
        result: HallucinationGrade = chain.invoke({
            "context": context_str[:3000],
            "generation": generation,
        })
        grade = result.binary_score
        print(f"[Hallucination Check] Evaluation: {grade} ({result.explanation})")
    except Exception as e:
        print(f"[Hallucination Check] Failed or skipped: {e}")
        grade = "grounded"

    return {
        "hallucination_grade": grade,
        "execution_steps": steps,
    }
