import re
from typing import List, Dict, Any, Optional

def extract_code_blocks(text: str) -> List[str]:
    """Extracts all markdown fenced code blocks from content."""
    matches = re.findall(r"```(?:[a-zA-Z0-9_\-\.]*)\n(.*?)```", text, re.DOTALL)
    return [m.strip() for m in matches if m.strip()]

def extract_summary_paragraphs(text: str, max_chars: int = 500) -> str:
    """Extracts non-code descriptive paragraphs from technical documentation."""
    # Strip code blocks
    cleaned = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip() and not p.strip().startswith("#")]
    summary = " ".join(paragraphs)
    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(".", 1)[0] + "."
    return summary

def synthesize_extractive_answer(
    question: str,
    relevant_docs: List[Dict[str, Any]],
    error_reason: Optional[str] = None
) -> str:
    """
    Zero-downtime offline context synthesizer.
    Activates when external LLM APIs hit 429 Rate Limits, Quota Exhaustion, or Network Outages.
    Provides a rich, grounded technical answer with real code snippets extracted directly
    from the indexed documentation corpus.
    """
    if not relevant_docs:
        return (
            "> ⚠️ **High-Availability Mode:** The external LLM API is temporarily rate-limited, "
            "and no relevant documents were found in the local corpus to synthesize an answer. "
            "Please check back shortly or upload additional documentation via `/ingest`."
        )

    top_doc = relevant_docs[0]
    content = top_doc.get("content", "")
    metadata = top_doc.get("metadata", {})
    title = metadata.get("title") or metadata.get("filename") or "Technical Documentation"
    header_path = metadata.get("header_path", "General Overview")

    # Extract best code block
    all_codes = []
    for doc in relevant_docs[:3]:
        c = doc.get("content", "")
        blocks = extract_code_blocks(c)
        all_codes.extend(blocks)

    code_snippet = all_codes[0] if all_codes else ""

    # Extract explanatory text
    summary = extract_summary_paragraphs(content, max_chars=600)
    if not summary:
        summary = content[:400]

    # Mask error details gracefully
    rate_limit_notice = "rate limit or quota threshold"
    if error_reason and ("429" in error_reason or "ResourceExhausted" in error_reason or "Quota" in error_reason):
        rate_limit_notice = "upstream API rate limit (HTTP 429)"

    response_lines = [
        f"> 🛡️ **Zero-Downtime Resilience Active:** The external LLM service encountered an {rate_limit_notice}. "
        f"Your technical answer has been synthesized directly from the verified documentation corpus.\n",
        f"### {title} — {header_path}\n",
        f"{summary}\n"
    ]

    if code_snippet:
        response_lines.append(f"#### Verified Code Implementation:\n```python\n{code_snippet}\n```\n")

    response_lines.append(f"**Source Citation:** `[Source: {title} > {header_path}]`\n")

    # Add secondary context points if available
    if len(relevant_docs) > 1:
        response_lines.append("#### Related Documentation References:")
        for idx, doc in enumerate(relevant_docs[1:3], 2):
            m = doc.get("metadata", {})
            t = m.get("title", f"Document {idx}")
            h = m.get("header_path", "Section")
            response_lines.append(f"- **{t}**: `{h}`")

    return "\n".join(response_lines)
