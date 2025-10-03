"""LLM integration layer for dev-agent.

This module provides abstract interfaces and implementations for LLM providers,
with Azure OpenAI as the primary implementation.
"""

from dev_agent.llm.base import IEmbeddingClient, ILLMClient

__all__ = ["ILLMClient", "IEmbeddingClient"]
