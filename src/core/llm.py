import os
from typing import Optional, List
from langchain_core.language_models.chat_models import BaseChatModel
from src.config import settings

def _build_single_llm(
    provider: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> BaseChatModel:
    """Builds an individual ChatModel instance without fallbacks."""
    selected_provider = provider.lower()

    if selected_provider == "groq":
        api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model or settings.GROQ_MODEL,
            temperature=temperature,
            api_key=api_key,
        )

    elif selected_provider == "openai":
        api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=temperature,
            api_key=api_key,
        )

    elif selected_provider == "gemini":
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model or settings.GEMINI_MODEL,
            temperature=temperature,
            google_api_key=api_key,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: '{selected_provider}'. Supported: 'groq', 'openai', 'gemini'."
        )


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    with_failover: bool = True,
) -> BaseChatModel:
    """
    Factory function returning a resilient LLM instance.
    Automatically chains backup models & cross-provider fallbacks using .with_fallbacks()
    to seamlessly handle HTTP 429 Rate Limits, Quota Exhaustion, and Outages.
    """
    selected_provider = (provider or settings.DEFAULT_LLM_PROVIDER).lower()
    primary = _build_single_llm(selected_provider, model=model, temperature=temperature)

    if not with_failover:
        return primary

    fallbacks: List[BaseChatModel] = []

    # 1. Intra-provider model fallback (e.g. Gemini flash-lite -> Gemini 1.5 flash)
    if selected_provider == "gemini":
        gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            current_model = model or settings.GEMINI_MODEL
            alt_models = ["gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"]
            for alt in alt_models:
                if alt != current_model:
                    try:
                        fallbacks.append(_build_single_llm("gemini", model=alt, temperature=temperature))
                    except Exception:
                        pass

    # 2. Cross-provider fallback to Groq (if key configured)
    groq_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if selected_provider != "groq" and groq_key:
        try:
            fallbacks.append(_build_single_llm("groq", temperature=temperature))
        except Exception:
            pass

    # 3. Cross-provider fallback to OpenAI (if key configured)
    openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    if selected_provider != "openai" and openai_key:
        try:
            fallbacks.append(_build_single_llm("openai", temperature=temperature))
        except Exception:
            pass

    if fallbacks:
        return primary.with_fallbacks(fallbacks)

    return primary
