"""
Precision Latency & Time-To-First-Token (TTFT) Diagnostic Profiler
Measures exact millisecond execution time of each pipeline stage and LLM first-token generation.
"""

import sys
import time
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.graph.nodes.query_analysis import query_analysis_node
from src.graph.nodes.retriever import retriever_node
from src.graph.nodes.document_grader import document_grader_node
from src.graph.nodes.generator import GENERATION_PROMPT
from src.graph.nodes.hallucination import hallucination_check_node
from src.core.llm import get_llm

def profile_pipeline(query: str):
    print("=" * 70)
    print("⏱️  DOCUGRAPH AI: LATENCY & TTFT PRECISION PROFILER")
    print("=" * 70)
    print(f"Query: '{query}'\n")

    t_start = time.perf_counter()

    # Stage 1: Query Analysis
    t0 = time.perf_counter()
    state = {
        "question": query,
        "current_query": query,
        "retry_count": 0,
        "execution_steps": [],
    }
    qa_res = query_analysis_node(state)
    state.update(qa_res)
    t_qa = time.perf_counter()
    lat_qa_ms = (t_qa - t0) * 1000

    # Stage 2: ChromaDB Vector Retrieval (FastEmbed ONNX)
    t1 = time.perf_counter()
    ret_res = retriever_node(state)
    state.update(ret_res)
    t_ret = time.perf_counter()
    lat_ret_ms = (t_ret - t1) * 1000

    # Stage 3: Document Grading
    t2 = time.perf_counter()
    grade_res = document_grader_node(state)
    state.update(grade_res)
    t_grade = time.perf_counter()
    lat_grade_ms = (t_grade - t2) * 1000

    # Stage 4: Generator Preparation & TTFT (Streaming First Token)
    t3 = time.perf_counter()
    relevant_docs = state.get("relevant_documents", [])
    context_parts = []
    sources = []
    for i, doc in enumerate(relevant_docs, 1):
        meta = doc.get("metadata", {})
        title = meta.get("title") or meta.get("filename") or f"Doc {i}"
        header = meta.get("header_path", "General")
        content = doc.get("content", "")
        context_parts.append(f"--- Context {i} [Source: {title} | Section: {header}] ---\n{content}\n")
        sources.append({"title": title, "header_path": header})
    full_context = "\n".join(context_parts)

    llm = get_llm(temperature=0.1)
    prompt_value = GENERATION_PROMPT.format_messages(
        question=query,
        query_type=state.get("query_type", "conceptual"),
        context=full_context,
    )

    t_stream_start = time.perf_counter()
    first_token_time = None
    accumulated_tokens = []

    for chunk in llm.stream(prompt_value):
        text = chunk.content
        if isinstance(text, list):
            text = "".join([t if isinstance(t, str) else str(t) for t in text])
        elif not isinstance(text, str):
            text = str(text) if text else ""
        if first_token_time is None and text:
            first_token_time = time.perf_counter()
        accumulated_tokens.append(text)

    t_gen_done = time.perf_counter()
    generation_text = "".join(accumulated_tokens)

    # Time to First Token metrics
    ttft_from_request_ms = (first_token_time - t_start) * 1000 if first_token_time else 0
    ttft_llm_internal_ms = (first_token_time - t_stream_start) * 1000 if first_token_time else 0
    lat_full_gen_ms = (t_gen_done - t3) * 1000

    state["generation"] = generation_text
    state["sources"] = sources

    # Stage 5: Hallucination Check (Self-RAG)
    t4 = time.perf_counter()
    hallucination_res = hallucination_check_node(state)
    state.update(hallucination_res)
    t_hallucination = time.perf_counter()
    lat_hallucination_ms = (t_hallucination - t4) * 1000

    t_end = time.perf_counter()
    total_pipeline_ms = (t_end - t_start) * 1000

    print("-" * 70)
    print("STAGE-BY-STAGE LATENCY BREAKDOWN:")
    print("-" * 70)
    print(f"1. Query Analysis Node:       {lat_qa_ms:8.2f} ms   (Regex Intent Classification & Fast Expansion)")
    print(f"2. ChromaDB Retrieval Node:   {lat_ret_ms:8.2f} ms   (FastEmbed ONNX all-MiniLM-L6-v2 + Cosine Similarity)")
    print(f"3. Document Grading Node:     {lat_grade_ms:8.2f} ms   (Batch Relevance Assessment)")
    print(f"4. LLM Generation (Full):     {lat_full_gen_ms:8.2f} ms   (Gemini 3.5 Flash Lite Synthesis)")
    print(f"   ├─ LLM Engine TTFT:        {ttft_llm_internal_ms:8.2f} ms   (Prompt prefill to first chunk)")
    print(f"5. Hallucination Check Node:  {lat_hallucination_ms:8.2f} ms   (Fast-path Inline Citation Verification)")
    print("-" * 70)
    print(f"👉 PIPELINE TIME-TO-FIRST-TOKEN (TTFT): {ttft_from_request_ms:8.2f} ms  (~{ttft_from_request_ms/1000:.2f} s from request submit)")
    print(f"👉 TOTAL END-TO-END PIPELINE LATENCY:   {total_pipeline_ms:8.2f} ms  (~{total_pipeline_ms/1000:.2f} s full completion)")
    print(f"👉 GENERATED TOKENS / CHARS:           {len(generation_text)} characters (~{len(generation_text)//4} tokens)")
    print(f"👉 GENERATION SPEED:                   {(len(generation_text)//4) / ((lat_full_gen_ms - ttft_llm_internal_ms)/1000):.1f} tokens/second")
    print("=" * 70)

if __name__ == "__main__":
    profile_pipeline("How do I create and send an envelope using the DocuSign Python SDK?")
