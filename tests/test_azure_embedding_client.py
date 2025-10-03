"""Unit tests for Azure OpenAI embedding client."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.models.llm_config import AzureOpenAIConfig

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def azure_config() -> AzureOpenAIConfig:
    """Create Azure OpenAI configuration for testing."""
    return AzureOpenAIConfig(
        endpoint="https://test-resource.openai.azure.com/",
        api_key="test-api-key",
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
def mock_azure_client() -> AsyncMock:
    """Create mock Azure OpenAI client."""
    client = AsyncMock()

    # Mock single embedding response
    single_response = MagicMock()
    single_response.data = [
        MagicMock(embedding=[0.1] * 1536)
    ]
    single_response.usage = MagicMock(total_tokens=10)

    # Mock batch embedding response
    batch_response = MagicMock()
    batch_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536),
    ]
    batch_response.usage = MagicMock(total_tokens=30)

    client.embeddings.create = AsyncMock(return_value=single_response)

    return client


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary cache directory for testing."""
    return tmp_path / "test_cache"


@pytest.fixture
def embedding_client(
    azure_config: AzureOpenAIConfig,
    mock_azure_client: AsyncMock,
    temp_cache_dir: Path,
) -> AzureEmbeddingClient:
    """Create embedding client with mocked Azure client."""
    return AzureEmbeddingClient(
        config=azure_config,
        cache_dir=temp_cache_dir,
        client=mock_azure_client,
    )


def test_client_initialization(
    azure_config: AzureOpenAIConfig,
    temp_cache_dir: Path,
) -> None:
    """Test embedding client initialization."""
    client = AzureEmbeddingClient(
        config=azure_config,
        cache_dir=temp_cache_dir,
    )

    assert client.config == azure_config
    assert client.model == "text-embedding-ada-002"
    assert client.dimension == 1536
    assert client.cache.cache_dir == temp_cache_dir
    assert temp_cache_dir.exists()


def test_client_dimension_property(embedding_client: AzureEmbeddingClient) -> None:
    """Test dimension property returns correct value."""
    assert embedding_client.dimension == 1536


@pytest.mark.asyncio
async def test_embed_text_single(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test embedding single text."""
    text = "def hello(): pass"

    result = await embedding_client.embed_text(text)

    assert len(result) == 1536
    assert all(isinstance(x, float) for x in result)
    mock_azure_client.embeddings.create.assert_called_once()

    # Verify API call parameters
    call_args = mock_azure_client.embeddings.create.call_args
    assert call_args.kwargs["model"] == "text-embedding-ada-002"
    assert call_args.kwargs["input"] == text


@pytest.mark.asyncio
async def test_embed_text_caching(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test embedding caching for repeated texts."""
    text = "def hello(): pass"

    # First call - should hit API
    result1 = await embedding_client.embed_text(text)
    assert mock_azure_client.embeddings.create.call_count == 1

    # Second call - should use cache
    result2 = await embedding_client.embed_text(text)
    assert mock_azure_client.embeddings.create.call_count == 1  # No additional call

    # Results should be identical
    assert result1 == result2

    # Verify cache stats
    stats = embedding_client.cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1


@pytest.mark.asyncio
async def test_embed_batch_empty(embedding_client: AzureEmbeddingClient) -> None:
    """Test embedding empty batch."""
    result = await embedding_client.embed_batch([])

    assert result == []


@pytest.mark.asyncio
async def test_embed_batch_single_text(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test embedding batch with single text."""
    texts = ["def hello(): pass"]

    result = await embedding_client.embed_batch(texts)

    assert len(result) == 1
    assert len(result[0]) == 1536
    mock_azure_client.embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_embed_batch_multiple_texts(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test embedding batch with multiple texts."""
    texts = ["text1", "text2", "text3"]

    # Configure mock to return appropriate response
    batch_response = MagicMock()
    batch_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536),
    ]
    batch_response.usage = MagicMock(total_tokens=30)
    mock_azure_client.embeddings.create.return_value = batch_response

    result = await embedding_client.embed_batch(texts)

    assert len(result) == 3
    assert all(len(emb) == 1536 for emb in result)
    mock_azure_client.embeddings.create.assert_called_once()

    # Verify batch was sent together
    call_args = mock_azure_client.embeddings.create.call_args
    assert call_args.kwargs["input"] == texts


@pytest.mark.asyncio
async def test_embed_batch_with_cache_hits(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test batch embedding with some texts already cached."""
    texts = ["text1", "text2", "text3"]

    # Configure mock for batch response
    batch_response = MagicMock()
    batch_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536),
    ]
    batch_response.usage = MagicMock(total_tokens=30)
    mock_azure_client.embeddings.create.return_value = batch_response

    # First batch - all cache misses
    result1 = await embedding_client.embed_batch(texts)
    assert len(result1) == 3
    assert mock_azure_client.embeddings.create.call_count == 1

    # Second batch with same texts - all cache hits
    result2 = await embedding_client.embed_batch(texts)
    assert len(result2) == 3
    assert mock_azure_client.embeddings.create.call_count == 1  # No additional calls

    # Results should be identical
    assert result1 == result2


@pytest.mark.asyncio
async def test_embed_batch_partial_cache_hits(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test batch embedding with partial cache hits."""
    # First, cache some embeddings
    cached_texts = ["text1", "text2"]
    batch_response1 = MagicMock()
    batch_response1.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
    ]
    batch_response1.usage = MagicMock(total_tokens=20)
    mock_azure_client.embeddings.create.return_value = batch_response1

    await embedding_client.embed_batch(cached_texts)
    assert mock_azure_client.embeddings.create.call_count == 1

    # Now request batch with some cached and some new texts
    all_texts = ["text1", "text2", "text3", "text4"]

    # Configure mock for new texts only
    batch_response2 = MagicMock()
    batch_response2.data = [
        MagicMock(embedding=[0.3] * 1536),
        MagicMock(embedding=[0.4] * 1536),
    ]
    batch_response2.usage = MagicMock(total_tokens=20)
    mock_azure_client.embeddings.create.return_value = batch_response2

    result = await embedding_client.embed_batch(all_texts)

    assert len(result) == 4
    # Should only make one additional API call for the 2 new texts
    assert mock_azure_client.embeddings.create.call_count == 2


@pytest.mark.asyncio
async def test_embed_batch_custom_batch_size(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test batch embedding with custom batch size."""
    texts = [f"text{i}" for i in range(10)]

    # Configure mock to return appropriate responses
    def create_batch_response(count: int) -> MagicMock:
        response = MagicMock()
        response.data = [MagicMock(embedding=[float(i)] * 1536) for i in range(count)]
        response.usage = MagicMock(total_tokens=count * 10)
        return response

    # Use side_effect to return different responses for each call
    mock_azure_client.embeddings.create.side_effect = [
        create_batch_response(3),
        create_batch_response(3),
        create_batch_response(3),
        create_batch_response(1),
    ]

    result = await embedding_client.embed_batch(texts, batch_size=3)

    assert len(result) == 10
    # Should make 4 API calls (3 + 3 + 3 + 1)
    assert mock_azure_client.embeddings.create.call_count == 4


@pytest.mark.asyncio
async def test_embed_batch_invalid_batch_size(
    embedding_client: AzureEmbeddingClient,
) -> None:
    """Test batch embedding with invalid batch size."""
    texts = ["text1", "text2"]

    with pytest.raises(ValueError, match="batch_size must be between 1 and 100"):
        await embedding_client.embed_batch(texts, batch_size=0)

    with pytest.raises(ValueError, match="batch_size must be between 1 and 100"):
        await embedding_client.embed_batch(texts, batch_size=101)


@pytest.mark.asyncio
async def test_embed_batch_preserves_order(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test that batch embedding preserves input order."""
    texts = ["text1", "text2", "text3"]

    # Configure mock with distinct embeddings
    batch_response = MagicMock()
    batch_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536),
    ]
    batch_response.usage = MagicMock(total_tokens=30)
    mock_azure_client.embeddings.create.return_value = batch_response

    result = await embedding_client.embed_batch(texts)

    # Verify order is preserved
    assert result[0][0] == 0.1
    assert result[1][0] == 0.2
    assert result[2][0] == 0.3


@pytest.mark.asyncio
async def test_embed_text_authentication_error(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test handling of authentication errors."""
    from openai import AuthenticationError

    mock_azure_client.embeddings.create.side_effect = AuthenticationError(
        "Invalid API key",
        response=MagicMock(status_code=401),
        body=None,
    )

    with pytest.raises(LLMAuthenticationError) as exc_info:
        await embedding_client.embed_text("test")

    error_message = str(exc_info.value).lower()
    assert "authenticate" in error_message
    assert "azure_openai_api_key" in error_message


@pytest.mark.asyncio
async def test_embed_text_rate_limit_error(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test handling of rate limit errors."""
    from openai import RateLimitError

    mock_azure_client.embeddings.create.side_effect = RateLimitError(
        "Rate limit exceeded",
        response=MagicMock(status_code=429),
        body=None,
    )

    with pytest.raises(LLMRateLimitError) as exc_info:
        await embedding_client.embed_text("test")

    assert "rate limit" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_embed_text_timeout_error(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test handling of timeout errors."""
    from openai import APITimeoutError

    mock_azure_client.embeddings.create.side_effect = APITimeoutError(
        request=MagicMock()
    )

    with pytest.raises(LLMTimeoutError) as exc_info:
        await embedding_client.embed_text("test")

    error_message = str(exc_info.value).lower()
    assert "timed out" in error_message
    assert "60 seconds" in error_message


@pytest.mark.asyncio
async def test_embed_text_bad_request_error(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test handling of bad request errors."""
    from openai import BadRequestError

    mock_azure_client.embeddings.create.side_effect = BadRequestError(
        "Invalid model",
        response=MagicMock(status_code=400),
        body=None,
    )

    with pytest.raises(LLMBadRequestError) as exc_info:
        await embedding_client.embed_text("test")

    assert "invalid" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_embed_text_api_error(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test handling of general API errors."""
    from openai import APIError

    mock_azure_client.embeddings.create.side_effect = APIError(
        "Internal server error",
        request=MagicMock(),
        body=None,
    )

    with pytest.raises(LLMAPIError) as exc_info:
        await embedding_client.embed_text("test")

    assert "API error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_embed_text_unexpected_error(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test handling of unexpected errors."""
    mock_azure_client.embeddings.create.side_effect = RuntimeError("Unexpected error")

    with pytest.raises(LLMAPIError) as exc_info:
        await embedding_client.embed_text("test")

    assert "Unexpected error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_embed_batch_error_handling(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test error handling in batch embedding."""
    from openai import RateLimitError

    texts = ["text1", "text2", "text3"]

    mock_azure_client.embeddings.create.side_effect = RateLimitError(
        "Rate limit exceeded",
        response=MagicMock(status_code=429),
        body=None,
    )

    with pytest.raises(LLMRateLimitError):
        await embedding_client.embed_batch(texts)


def test_estimate_cost(embedding_client: AzureEmbeddingClient) -> None:
    """Test cost estimation for embeddings."""
    # Test with 1000 tokens
    cost = embedding_client.estimate_cost(1000)
    assert cost == 0.0001  # $0.0001 per 1K tokens

    # Test with 10000 tokens
    cost = embedding_client.estimate_cost(10000)
    assert cost == 0.001  # $0.001 for 10K tokens

    # Test with 0 tokens
    cost = embedding_client.estimate_cost(0)
    assert cost == 0.0


@pytest.mark.asyncio
async def test_embed_batch_progress_tracking(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test progress tracking for large batches."""
    # Create a large batch that will trigger progress logging
    texts = [f"text{i}" for i in range(200)]

    # Configure mock to return appropriate responses
    def create_batch_response(count: int) -> MagicMock:
        response = MagicMock()
        response.data = [MagicMock(embedding=[float(i)] * 1536) for i in range(count)]
        response.usage = MagicMock(total_tokens=count * 10)
        return response

    # Create enough responses for all batches (200 texts / 16 per batch = 13 batches)
    mock_azure_client.embeddings.create.side_effect = [
        create_batch_response(16) for _ in range(13)
    ]

    with patch("dev_agent.llm.embeddings.logger") as mock_logger:
        result = await embedding_client.embed_batch(texts, batch_size=16)

        assert len(result) == 200

        # Verify progress logging was called
        info_calls = [call for call in mock_logger.info.call_args_list]
        assert len(info_calls) > 0

        # Check that progress messages were logged
        progress_messages = [
            str(call) for call in info_calls if "Progress" in str(call)
        ]
        assert len(progress_messages) > 0


@pytest.mark.asyncio
async def test_embed_batch_cache_statistics(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test cache statistics tracking during batch embedding."""
    texts = ["text1", "text2", "text3"]

    # Configure mock
    batch_response = MagicMock()
    batch_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536),
    ]
    batch_response.usage = MagicMock(total_tokens=30)
    mock_azure_client.embeddings.create.return_value = batch_response

    # First batch - all misses
    await embedding_client.embed_batch(texts)

    stats = embedding_client.cache.get_stats()
    assert stats["misses"] == 3
    assert stats["hits"] == 0

    # Second batch - all hits
    await embedding_client.embed_batch(texts)

    stats = embedding_client.cache.get_stats()
    assert stats["misses"] == 3
    assert stats["hits"] == 3
    assert stats["hit_rate"] == 50.0


@pytest.mark.asyncio
async def test_embed_text_special_characters(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test embedding text with special characters."""
    texts = [
        "Text with émojis 🎉🎊",
        "Text with\nnewlines\nand\ttabs",
        "Text with unicode: 你好世界",
    ]

    for text in texts:
        result = await embedding_client.embed_text(text)
        assert len(result) == 1536


@pytest.mark.asyncio
async def test_embed_batch_large_batch(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test embedding very large batch."""
    texts = [f"text{i}" for i in range(100)]

    # Configure mock to return appropriate responses
    def create_batch_response(count: int) -> MagicMock:
        response = MagicMock()
        response.data = [MagicMock(embedding=[float(i)] * 1536) for i in range(count)]
        response.usage = MagicMock(total_tokens=count * 10)
        return response

    # Create enough responses for all batches
    mock_azure_client.embeddings.create.side_effect = [
        create_batch_response(16) for _ in range(7)
    ]

    result = await embedding_client.embed_batch(texts, batch_size=16)

    assert len(result) == 100
    assert all(len(emb) == 1536 for emb in result)


@pytest.mark.asyncio
async def test_client_with_default_cache_dir(
    azure_config: AzureOpenAIConfig,
    mock_azure_client: AsyncMock,
) -> None:
    """Test client initialization with default cache directory."""
    client = AzureEmbeddingClient(
        config=azure_config,
        client=mock_azure_client,
    )

    # Should use default cache directory
    assert ".dev_agent/embedding_cache" in str(client.cache.cache_dir)


@pytest.mark.asyncio
async def test_embed_batch_all_cached(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test batch embedding when all texts are already cached."""
    texts = ["text1", "text2", "text3"]

    # Configure mock
    batch_response = MagicMock()
    batch_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536),
    ]
    batch_response.usage = MagicMock(total_tokens=30)
    mock_azure_client.embeddings.create.return_value = batch_response

    # First call to populate cache
    await embedding_client.embed_batch(texts)
    call_count_after_first = mock_azure_client.embeddings.create.call_count

    # Second call should use cache entirely
    result = await embedding_client.embed_batch(texts)

    assert len(result) == 3
    # No additional API calls
    assert mock_azure_client.embeddings.create.call_count == call_count_after_first


@pytest.mark.asyncio
async def test_embed_text_caches_result(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test that embed_text properly caches results."""
    text = "test text"

    # First call
    result1 = await embedding_client.embed_text(text)

    # Verify it was cached
    cached = embedding_client.cache.get(text, embedding_client.model)
    assert cached is not None
    assert cached == result1


@pytest.mark.asyncio
async def test_embed_batch_caches_all_results(
    embedding_client: AzureEmbeddingClient,
    mock_azure_client: AsyncMock,
) -> None:
    """Test that embed_batch caches all results."""
    texts = ["text1", "text2", "text3"]

    # Configure mock
    batch_response = MagicMock()
    batch_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536),
    ]
    batch_response.usage = MagicMock(total_tokens=30)
    mock_azure_client.embeddings.create.return_value = batch_response

    await embedding_client.embed_batch(texts)

    # Verify all were cached
    for text in texts:
        cached = embedding_client.cache.get(text, embedding_client.model)
        assert cached is not None
        assert len(cached) == 1536
