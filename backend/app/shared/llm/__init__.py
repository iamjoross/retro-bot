"""Shared LLM infrastructure for the application"""

from functools import lru_cache
from .tinyllama import TinyLlamaLLM
from app.shared.config import settings


# Simple cached instance for the single model we use
@lru_cache(maxsize=1)
def get_assistant_llm() -> TinyLlamaLLM:
    """Get or create the cached TinyLlama LLM instance"""
    llm = TinyLlamaLLM(
        model_name=settings.MODEL_ASSISTANT,
        max_tokens=settings.MAX_NEW_TOKENS,
        temperature=settings.TEMPERATURE,
        top_p=settings.TOP_P,
        cache_dir=settings.HF_HOME,
    )

    # Load the model synchronously (will be cached)
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In async context - model loading will happen later
            return llm
        else:
            loop.run_until_complete(llm.load_model())
    except RuntimeError:
        # No event loop
        asyncio.run(llm.load_model())

    return llm


__all__ = [
    "TinyLlamaLLM",
    "get_assistant_llm",
]
