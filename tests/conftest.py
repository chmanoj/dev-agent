"""Pytest configuration and shared fixtures for dev-agent tests.

This module provides common fixtures for testing, including mocks for
Azure OpenAI clients, cost trackers, token counters, and other components.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

from dev_agent.llm.cost_tracker import CostTracker
from dev_agent.llm.token_counter import TokenCounter
from dev_agent.models.enums import PhaseType
from dev_agent.models.llm_config import AzureOpenAIConfig

if TYPE_CHECKING:
    from dev_agent.llm.azure_client import AzureOpenAIClient
    from dev_agent.llm.embeddings import AzureEmbeddingClient


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def azure_config() -> AzureOpenAIConfig:
    """Create test Azure OpenAI configuration.
    
    Returns:
        AzureOpenAIConfig with test values
    """
    return AzureOpenAIConfig(
        endpoint="https://test-resource.openai.azure.com/",
        api_key=SecretStr("test-api-key"),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        max_tokens=4000,
        temperature=0.7,
        max_retries=3,
        timeout=60,
        batch_size=16,
    )


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary cache directory for testing.
    
    Args:
        tmp_path: Pytest temporary directory fixture
        
    Returns:
        Path to temporary cache directory
    """
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


# ============================================================================
# Azure OpenAI Client Mocks
# ============================================================================


@pytest.fixture
def mock_azure_openai_client() -> AsyncMock:
    """Create mock AsyncAzureOpenAI client for testing.
    
    This fixture provides a fully mocked Azure OpenAI client with
    realistic responses for completions, streaming, and embeddings.
    
    Returns:
        AsyncMock configured to simulate Azure OpenAI API responses
    """
    client = AsyncMock()

    # Mock successful completion response
    completion_response = MagicMock()
    completion_response.choices = [
        MagicMock(
            message=MagicMock(content="Generated completion text"),
            finish_reason="stop",
        )
    ]
    completion_response.usage = MagicMock(
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
    )
    completion_response.model = "gpt-4"

    client.chat.completions.create = AsyncMock(return_value=completion_response)

    # Mock embedding response
    embedding_response = MagicMock()
    embedding_response.data = [
        MagicMock(embedding=[0.1] * 1536)
    ]
    embedding_response.usage = MagicMock(total_tokens=10)
    embedding_response.model = "text-embedding-ada-002"

    client.embeddings.create = AsyncMock(return_value=embedding_response)

    return client


@pytest.fixture
def mock_streaming_response() -> AsyncMock:
    """Create mock streaming response for testing.
    
    Returns:
        AsyncMock that yields streaming chunks
    """
    async def mock_stream():
        """Generate mock streaming chunks."""
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
        ]
        for chunk in chunks:
            yield chunk

    return mock_stream()


# ============================================================================
# LLM Client Fixtures
# ============================================================================


@pytest.fixture
def mock_llm_client(azure_config: AzureOpenAIConfig, mock_azure_openai_client: AsyncMock) -> AzureOpenAIClient:
    """Create mock LLM client for testing.
    
    This fixture provides a fully configured AzureOpenAIClient with
    mocked Azure OpenAI API calls.
    
    Args:
        azure_config: Azure OpenAI configuration
        mock_azure_openai_client: Mocked Azure OpenAI client
        
    Returns:
        AzureOpenAIClient with mocked API calls
    """
    from dev_agent.llm.azure_client import AzureOpenAIClient
    
    return AzureOpenAIClient(
        config=azure_config,
        client=mock_azure_openai_client,
    )


@pytest.fixture
def mock_embedding_client(
    azure_config: AzureOpenAIConfig,
    mock_azure_openai_client: AsyncMock,
    temp_cache_dir: Path,
) -> AzureEmbeddingClient:
    """Create mock embedding client for testing.
    
    This fixture provides a fully configured AzureEmbeddingClient with
    mocked Azure OpenAI API calls and temporary cache directory.
    
    Args:
        azure_config: Azure OpenAI configuration
        mock_azure_openai_client: Mocked Azure OpenAI client
        temp_cache_dir: Temporary cache directory
        
    Returns:
        AzureEmbeddingClient with mocked API calls
    """
    from dev_agent.llm.embeddings import AzureEmbeddingClient
    
    return AzureEmbeddingClient(
        config=azure_config,
        cache_dir=temp_cache_dir,
        client=mock_azure_openai_client,
    )


# ============================================================================
# Cost Tracking Fixtures
# ============================================================================


@pytest.fixture
def mock_cost_tracker() -> CostTracker:
    """Create mock cost tracker for testing.
    
    Returns:
        CostTracker instance for testing
    """
    return CostTracker(
        current_phase=PhaseType.INDEXING,
        budget_threshold=10.0,
        budget_limit=50.0,
    )


@pytest.fixture
def cost_tracker_no_budget() -> CostTracker:
    """Create cost tracker without budget limits.
    
    Returns:
        CostTracker instance without budget constraints
    """
    return CostTracker(current_phase=PhaseType.INDEXING)


# ============================================================================
# Token Counter Fixtures
# ============================================================================


@pytest.fixture
def mock_token_counter() -> TokenCounter:
    """Create mock token counter for testing.
    
    Returns:
        TokenCounter instance for GPT-4
    """
    return TokenCounter("gpt-4")


@pytest.fixture
def token_counter_gpt4_turbo() -> TokenCounter:
    """Create token counter for GPT-4 Turbo.
    
    Returns:
        TokenCounter instance for GPT-4 Turbo
    """
    return TokenCounter("gpt-4-turbo")


@pytest.fixture
def token_counter_gpt35() -> TokenCounter:
    """Create token counter for GPT-3.5 Turbo.
    
    Returns:
        TokenCounter instance for GPT-3.5 Turbo
    """
    return TokenCounter("gpt-3.5-turbo")


# ============================================================================
# Helper Fixtures
# ============================================================================


@pytest.fixture
def sample_code_text() -> str:
    """Provide sample code text for testing.
    
    Returns:
        Sample Python code as string
    """
    return """
def hello_world():
    \"\"\"Print hello world message.\"\"\"
    print("Hello, world!")
    return True

class Calculator:
    \"\"\"Simple calculator class.\"\"\"
    
    def add(self, a: int, b: int) -> int:
        \"\"\"Add two numbers.\"\"\"
        return a + b
    
    def subtract(self, a: int, b: int) -> int:
        \"\"\"Subtract two numbers.\"\"\"
        return a - b
"""


@pytest.fixture
def sample_code_chunks() -> list[str]:
    """Provide sample code chunks for testing.
    
    Returns:
        List of code chunk strings
    """
    return [
        "def function_one(): pass",
        "def function_two(): pass",
        "class MyClass: pass",
        "import os",
        "from typing import List",
    ]


@pytest.fixture
def sample_embeddings() -> list[list[float]]:
    """Provide sample embeddings for testing.
    
    Returns:
        List of 1536-dimensional embedding vectors
    """
    return [
        [0.1] * 1536,
        [0.2] * 1536,
        [0.3] * 1536,
    ]


# ============================================================================
# Mock Response Builders
# ============================================================================


def create_mock_completion_response(
    content: str = "Generated text",
    prompt_tokens: int = 100,
    completion_tokens: int = 200,
    model: str = "gpt-4",
) -> MagicMock:
    """Create a mock completion response.
    
    Args:
        content: Response content
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        model: Model name
        
    Returns:
        MagicMock configured as completion response
    """
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(content=content),
            finish_reason="stop",
        )
    ]
    response.usage = MagicMock(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    response.model = model
    return response


def create_mock_embedding_response(
    count: int = 1,
    dimension: int = 1536,
    tokens: int = 10,
    model: str = "text-embedding-ada-002",
) -> MagicMock:
    """Create a mock embedding response.
    
    Args:
        count: Number of embeddings
        dimension: Embedding dimension
        tokens: Total tokens used
        model: Model name
        
    Returns:
        MagicMock configured as embedding response
    """
    response = MagicMock()
    response.data = [
        MagicMock(embedding=[float(i) / 10] * dimension)
        for i in range(count)
    ]
    response.usage = MagicMock(total_tokens=tokens)
    response.model = model
    return response


def create_mock_streaming_chunks(texts: list[str]) -> list[MagicMock]:
    """Create mock streaming chunks.
    
    Args:
        texts: List of text chunks to stream
        
    Returns:
        List of MagicMock objects representing streaming chunks
    """
    return [
        MagicMock(choices=[MagicMock(delta=MagicMock(content=text))])
        for text in texts
    ]


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers.
    
    Args:
        config: Pytest configuration object
    """
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires real Azure OpenAI API)",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running",
    )
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async test",
    )


# ============================================================================
# Async Test Support
# ============================================================================


@pytest.fixture
def event_loop():
    """Create event loop for async tests.
    
    Yields:
        Event loop for async test execution
    """
    import asyncio
    
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
