import os
from typing import Optional
from langchain_core.embeddings import Embeddings
from src.config import settings

def get_embeddings(provider: Optional[str] = None) -> Embeddings:
    """
    Factory function returning the configured embeddings model.
    Defaults to FastEmbed (sentence-transformers/all-MiniLM-L6-v2),
    which runs 100% locally with zero API cost and zero rate limits.
    """
    selected_provider = (provider or settings.EMBEDDING_PROVIDER).lower()

    if selected_provider == "fastembed":
        try:
            from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
            return FastEmbedEmbeddings(model_name=settings.EMBEDDING_MODEL)
        except Exception as e:
            print(f"[Embeddings] FastEmbed error ({e}), falling back to HuggingFace / OpenAI")
            pass

    if selected_provider == "openai":
        api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings.")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)

    # Fallback: try FastEmbed or HuggingFace
    try:
        from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
        return FastEmbedEmbeddings(model_name=settings.EMBEDDING_MODEL)
    except Exception:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
