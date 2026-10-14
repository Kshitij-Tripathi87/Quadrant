from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.graph.state import GraphState
from src.core.llm import get_llm

GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an elite AI Technical Documentation Assistant.
Your mission is to provide accurate, concise, and developer-friendly answers based EXCLUSIVELY on the provided retrieved documentation context.

GUIDELINES:
1. Strict Grounding: Rely ONLY on the provided context. Do NOT fabricate functions, parameters, or explanations not supported by the context.
2. Code Clarity: When providing code snippets, include clean, idiomatic Python code with clear comments.
3. Citations & References: Cite your sources inline or at the end of sections using the format: `[Source: <Document Title> > <Section>]`.
4. Tone & Style: Be direct, professional, and practical. Avoid fluff.
5. Insufficient Context: If the context does not contain enough information to answer the question with certainty, clearly state: "The indexed documentation does not contain sufficient details to answer this question." Do not guess."""
    ),
    (
        "human",
        """User Question:
{question}

Query Intent:
{query_type}

Retrieved Technical Documentation Context:
{context}

Provide a complete, grounded answer with clear code examples (if applicable) and source citations:"""
    )
])

def generator_node(state: GraphState) -> dict:
    """
    Generates the final answer grounded in relevant documents with source citations.
    """
    question = state.get("question", "")
    query_type = state.get("query_type", "conceptual")
    relevant_docs = state.get("relevant_documents", [])
    steps = state.get("execution_steps", []).copy()
    steps.append("generator")

    # If no relevant documents exist after all retries and fallback
    if not relevant_docs:
        generation = (
            "I'm sorry, but the indexed technical documentation does not contain "
            "relevant information to answer your question accurately. "
            "Please check your question or consider uploading additional documentation via the `/ingest` endpoint."
        )
        return {
            "generation": generation,
            "sources": [],
            "execution_steps": steps,
        }

    # Format context and citations
    context_parts: List[str] = []
    sources: List[Dict[str, Any]] = []

    for i, doc in enumerate(relevant_docs, 1):
        meta = doc.get("metadata", {})
        title = meta.get("title") or meta.get("filename") or f"Doc {i}"
        header = meta.get("header_path", "General")
        source_url = meta.get("source", "local")
        content = doc.get("content", "")

        context_parts.append(
            f"--- Context {i} [Source: {title} | Section: {header}] ---\n{content}\n"
        )

        sources.append({
            "source": source_url,
            "title": title,
            "header_path": header,
            "snippet": content[:200] + ("..." if len(content) > 200 else ""),
        })

    full_context = "\n".join(context_parts)

    try:
        llm = get_llm(temperature=0.1)
        chain = GENERATION_PROMPT | llm | StrOutputParser()
        answer = chain.invoke({
            "question": question,
            "query_type": query_type,
            "context": full_context,
        })
    except Exception as e:
        print(f"[Generator Node] Error invoking LLM: {e}")
        answer = f"Error generating answer: {e}\n\nRetrieved context was:\n{full_context[:500]}..."

    return {
        "generation": answer,
        "sources": sources,
        "execution_steps": steps,
    }
