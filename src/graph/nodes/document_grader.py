from typing import Literal, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.graph.state import GraphState, DocumentChunk
from src.core.llm import get_llm

class GradeChunk(BaseModel):
    binary_score: Literal["relevant", "irrelevant"] = Field(
        description="Score whether the document contains information, keywords, or code relevant to the question."
    )
    reasoning: str = Field(
        description="Brief explanation why this document is relevant or irrelevant."
    )

GRADER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an objective document relevance evaluator for technical documentation RAG pipelines.
Your job is to assess whether a retrieved document chunk is relevant to the user question.
Grade as 'relevant' if the document contains keywords, semantic concepts, architecture details, or code samples that help answer the question.
Grade as 'irrelevant' if the document is unrelated, off-topic, or cannot assist in answering the question.
Be rigorous but reasonable."""
    ),
    (
        "human",
        "Retrieved Document:\n\n{document}\n\nUser Question: {question}"
    )
])

def document_grader_node(state: GraphState) -> dict:
    """
    Evaluates retrieved chunks, scoring each as 'relevant' or 'irrelevant'.
    Retains only relevant documents in state['relevant_documents'].
    """
    question = state.get("question", "")
    documents = state.get("documents", [])
    steps = state.get("execution_steps", []).copy()
    steps.append("document_grader")

    print(f"[Document Grader Node] Grading {len(documents)} retrieved chunk(s)...")

    relevant_docs: List[DocumentChunk] = []
    
    try:
        llm = get_llm(temperature=0.0)
        structured_grader = llm.with_structured_output(GradeChunk)
        grader_chain = GRADER_PROMPT | structured_grader

        for doc in documents:
            content = doc.get("content", "")
            try:
                res: GradeChunk = grader_chain.invoke({
                    "document": content,
                    "question": question
                })
                score = res.binary_score
                reasoning = res.reasoning
            except Exception as e:
                print(f"[Document Grader] Error grading chunk: {e}, defaulting to 'relevant'")
                score = "relevant"
                reasoning = "Grading fallback"

            graded_chunk: DocumentChunk = {
                "content": content,
                "metadata": doc.get("metadata", {}),
                "relevance_score": score,
                "reasoning": reasoning,
            }

            if score == "relevant":
                relevant_docs.append(graded_chunk)

    except Exception as e:
        print(f"[Document Grader] LLM error: {e}. Passing documents through as fallback.")
        relevant_docs = documents

    print(f"[Document Grader Node] {len(relevant_docs)} / {len(documents)} chunks deemed relevant.")

    return {
        "relevant_documents": relevant_docs,
        "execution_steps": steps,
    }
