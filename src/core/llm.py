import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from src.config import settings

def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> BaseChatModel:
    """
    Factory function returning the configured LLM instance.
    Supports Groq, OpenAI, Google Gemini, and Anthropic.
    """
    selected_provider = (provider or settings.DEFAULT_LLM_PROVIDER).lower()

    if selected_provider == "groq":
        api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Please add it to your .env file or environment variables."
            )
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model or settings.GROQ_MODEL,
            temperature=temperature,
            api_key=api_key,
        )

    elif selected_provider == "openai":
        api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please add it to your .env file or environment variables."
            )
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=temperature,
            api_key=api_key,
        )

    elif selected_provider == "gemini":
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please add it to your .env file or environment variables."
            )
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
