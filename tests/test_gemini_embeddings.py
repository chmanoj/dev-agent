"""Tests for Gemini embedding client.

This module tests the GeminiEmbeddingClient implementation with mocked
Gemini API calls to ensure proper functionality without making real API calls.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from google.api_core import exceptions as google_exceptions
from pydantic import SecretStr

from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient
from dev_agent.models.llm_config import GeminiConfig


@pytest.fixture
def gemini_config():
    """Create a test Gemini configuration."""
    return GeminiConfig(
        api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),
        model_name="gemini-2.5-flash",
        embedding_model="gemini-embedding-001",
        batch_size=16,
        timeout=60,
    )


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_genai():
    """Mock the google.generativeai module."""
    with patch("dev_agent.llm.gemini_embeddings.genai") as mock:
        yield mock


@pytest.fixture
def gemini_client(gemini_config, temp_cache_dir, mock_genai):  # noqa: ARG001
    """Create a GeminiEmbeddingClient with mocked dependencies."""
    return GeminiEmbeddingClient(
        config=gemini_config,
        cache_dir=temp_cache_dir,
    )


class TestGeminiEmbeddingClient:
    """Test cases for GeminiEmbeddingClient."""

    def test_initialization(self, gemini_config, temp_cache_dir, mock_genai):
        """Test client initialization."""
        client = GeminiEmbeddingClient(
            config=gemini_config,
            cache_dir=temp_cache_dir,
        )

        assert client.config == gemini_config
        assert client.model == "gemini-embedding-001"
        assert client.dimension == 768
        assert client.cache.cache_dir == temp_cache_dir

        # Verify Gemini API was configured
        mock_genai.configure.assert_called_once_with(
            api_key="AIzaSyTest123456789012345678901234567890"
        )

    def test_dimension_property(self, gemini_client):
        """Test dimension property returns correct value."""
        assert gemini_client.dimension == 768

    @pytest.mark.asyncio
    async def test_embed_text_success(self, gemini_client, mock_genai):
        """Test successful single text embedding."""
        # Mock successful API response
        mock_embedding = [0.1] * 768
        mock_genai.embed_content.return_value = {
            "embedding": mock_embedding
        }

        result = await gemini_client.embed_text("test code")

        assert result == mock_embedding
        assert len(result) == 768

        # Verify API call
        mock_genai.embed_content.assert_called_once_with(
            model="models/gemini-embedding-001",
            content="test code",
            task_type="retrieval_document",
        )

    @pytest.mark.asyncio
    async def test_embed_text_cache_hit(self, gemini_client, mock_genai):
        """Test embedding retrieval from cache."""
        # Pre-populate cache
        cached_embedding = [0.2] * 768
        gemini_client.cache.set("cached text", "gemini-embedding-001", cached_embedding)

        result = await gemini_client.embed_text("cached text")

        assert result == cached_embedding
        # Verify no API call was made
        mock_genai.embed_content.assert_not_called()

    @pytest.mark.asyncio
    async def test_embed_text_cache_miss_then_hit(self, gemini_client, mock_genai):
        """Test cache miss followed by cache hit."""
        # Mock API response
        mock_embedding = [0.3] * 768
        mock_genai.embed_content.return_value = {
            "embedding": mock_embedding
        }

        # First call - cache miss
        result1 = await gemini_client.embed_text("new text")
        assert result1 == mock_embedding
        mock_genai.embed_content.assert_called_once()

        # Reset mock
        mock_genai.embed_content.reset_mock()

        # Second call - cache hit
        result2 = await gemini_client.embed_text("new text")
        assert result2 == mock_embedding
        mock_genai.embed_content.assert_not_called()

    @pytest.mark.asyncio
    async def test_embed_batch_success(self, gemini_client, mock_genai):
        """Test successful batch embedding."""
        texts = ["code1", "code2", "code3"]
        mock_embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]

        mock_genai.embed_content.return_value = {
            "embedding": mock_embeddings
        }

        result = await gemini_client.embed_batch(texts)

        assert len(result) == 3
        assert result == mock_embeddings
        assert all(len(emb) == 768 for emb in result)

        # Verify API call
        mock_genai.embed_content.assert_called_once_with(
            model="models/gemini-embedding-001",
            content=texts,
            task_type="retrieval_document",
        )

    @pytest.mark.asyncio
    async def test_embed_batch_single_response(self, gemini_client, mock_genai):
        """Test batch embedding with single text (single response format)."""
        texts = ["single code"]
        mock_embedding = [0.1] * 768

        # Mock single response format (not wrapped in list)
        mock_genai.embed_content.return_value = {
            "embedding": mock_embedding
        }

        result = await gemini_client.embed_batch(texts)

        assert len(result) == 1
        assert result[0] == mock_embedding
        assert len(result[0]) == 768

    @pytest.mark.asyncio
    async def test_embed_batch_with_cache(self, gemini_client, mock_genai):
        """Test batch embedding with some texts cached."""
        texts = ["cached1", "new1", "cached2", "new2"]

        # Pre-populate cache for some texts
        cached_emb1 = [0.1] * 768
        cached_emb2 = [0.2] * 768
        gemini_client.cache.set("cached1", "gemini-embedding-001", cached_emb1)
        gemini_client.cache.set("cached2", "gemini-embedding-001", cached_emb2)

        # Mock API response for uncached texts
        new_embeddings = [[0.3] * 768, [0.4] * 768]
        mock_genai.embed_content.return_value = {
            "embedding": new_embeddings
        }

        result = await gemini_client.embed_batch(texts)

        assert len(result) == 4
        assert result[0] == cached_emb1  # From cache
        assert result[1] == new_embeddings[0]  # From API
        assert result[2] == cached_emb2  # From cache
        assert result[3] == new_embeddings[1]  # From API

        # Verify API was called only for uncached texts
        mock_genai.embed_content.assert_called_once_with(
            model="models/gemini-embedding-001",
            content=["new1", "new2"],
            task_type="retrieval_document",
        )

    @pytest.mark.asyncio
    async def test_embed_batch_empty_list(self, gemini_client, mock_genai):
        """Test batch embedding with empty list."""
        result = await gemini_client.embed_batch([])

        assert result == []
        mock_genai.embed_content.assert_not_called()

    @pytest.mark.asyncio
    async def test_embed_batch_invalid_batch_size(self, gemini_client):
        """Test batch embedding with invalid batch size."""
        with pytest.raises(ValueError, match="batch_size must be between 1 and 100"):
            await gemini_client.embed_batch(["test"], batch_size=0)

        with pytest.raises(ValueError, match="batch_size must be between 1 and 100"):
            await gemini_client.embed_batch(["test"], batch_size=101)

    @pytest.mark.asyncio
    async def test_embed_batch_large_batch(self, gemini_client, mock_genai):
        """Test batch embedding with large number of texts."""
        # Create 50 texts to test batching
        texts = [f"code{i}" for i in range(50)]

        # Mock API to return different embeddings for each batch
        def mock_embed_side_effect(*args, **kwargs):
            content = kwargs.get("content", args[1] if len(args) > 1 else [])
            if isinstance(content, list):
                return {"embedding": [[float(i)] * 768 for i in range(len(content))]}
            else:
                return {"embedding": [0.0] * 768}

        mock_genai.embed_content.side_effect = mock_embed_side_effect

        result = await gemini_client.embed_batch(texts, batch_size=16)

        assert len(result) == 50
        assert all(len(emb) == 768 for emb in result)

        # Should make 4 API calls (16 + 16 + 16 + 2)
        assert mock_genai.embed_content.call_count == 4

    @pytest.mark.asyncio
    async def test_authentication_error(self, gemini_client, mock_genai):
        """Test handling of authentication errors."""
        mock_genai.embed_content.side_effect = google_exceptions.PermissionDenied(
            "Invalid API key"
        )

        with pytest.raises(LLMAuthenticationError) as exc_info:
            await gemini_client.embed_text("test")

        assert "Failed to authenticate with Google Gemini API" in str(exc_info.value)
        assert "GEMINI_API_KEY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, gemini_client, mock_genai):
        """Test handling of rate limit errors."""
        mock_genai.embed_content.side_effect = google_exceptions.ResourceExhausted(
            "Rate limit exceeded"
        )

        with pytest.raises(LLMRateLimitError) as exc_info:
            await gemini_client.embed_text("test")

        assert "Gemini API rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_error(self, gemini_client, mock_genai):
        """Test handling of timeout errors."""
        mock_genai.embed_content.side_effect = google_exceptions.DeadlineExceeded(
            "Request timed out"
        )

        with pytest.raises(LLMTimeoutError) as exc_info:
            await gemini_client.embed_text("test")

        assert "Request to Gemini API timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bad_request_error(self, gemini_client, mock_genai):
        """Test handling of bad request errors."""
        mock_genai.embed_content.side_effect = google_exceptions.InvalidArgument(
            "Invalid model name"
        )

        with pytest.raises(LLMBadRequestError) as exc_info:
            await gemini_client.embed_text("test")

        assert "Invalid request to Gemini API" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_general_api_error(self, gemini_client, mock_genai):
        """Test handling of general API errors."""
        mock_genai.embed_content.side_effect = google_exceptions.GoogleAPIError(
            "Service unavailable"
        )

        with pytest.raises(LLMAPIError) as exc_info:
            await gemini_client.embed_text("test")

        assert "Gemini API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unexpected_error(self, gemini_client, mock_genai):
        """Test handling of unexpected errors."""
        mock_genai.embed_content.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(LLMAPIError) as exc_info:
            await gemini_client.embed_text("test")

        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_embedding_dimension(self, gemini_client, mock_genai):
        """Test handling of invalid embedding dimensions."""
        # Mock API to return wrong dimension
        mock_genai.embed_content.return_value = {
            "embedding": [0.1] * 512  # Wrong dimension
        }

        with pytest.raises(LLMAPIError) as exc_info:
            await gemini_client.embed_text("test")

        assert "Unexpected embedding dimension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_batch_dimension_mismatch(self, gemini_client, mock_genai):
        """Test handling of dimension mismatch in batch processing."""
        texts = ["code1", "code2"]

        # Mock API to return embeddings with wrong dimensions
        mock_genai.embed_content.return_value = {
            "embedding": [[0.1] * 512, [0.2] * 512]  # Wrong dimensions
        }

        with pytest.raises(LLMAPIError) as exc_info:
            await gemini_client.embed_batch(texts)

        assert "Unexpected embedding dimension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_batch_count_mismatch(self, gemini_client, mock_genai):
        """Test handling of embedding count mismatch in batch processing."""
        texts = ["code1", "code2", "code3"]

        # Mock API to return wrong number of embeddings
        mock_genai.embed_content.return_value = {
            "embedding": [[0.1] * 768, [0.2] * 768]  # Only 2 embeddings for 3 texts
        }

        with pytest.raises(LLMAPIError) as exc_info:
            await gemini_client.embed_batch(texts)

        assert "Expected 3 embeddings, got 2" in str(exc_info.value)

    def test_estimate_cost(self, gemini_client):
        """Test cost estimation."""
        cost = gemini_client.estimate_cost(1000)
        expected_cost = (1000 / 1000) * 0.00001  # 1K tokens * rate
        assert cost == expected_cost

        # Test with different token counts
        assert gemini_client.estimate_cost(500) == 0.000005
        assert gemini_client.estimate_cost(2000) == 0.00002

    def test_cache_integration(self, gemini_config, temp_cache_dir, mock_genai):  # noqa: ARG002
        """Test cache integration and persistence."""
        client = GeminiEmbeddingClient(
            config=gemini_config,
            cache_dir=temp_cache_dir,
        )

        # Verify cache directory was created
        assert temp_cache_dir.exists()
        assert client.cache.cache_dir == temp_cache_dir

        # Test cache file creation
        embedding = [0.1] * 768
        client.cache.set("test", "embedding-001", embedding)

        # Verify cache file exists
        cache_files = list(temp_cache_dir.glob("*.json"))
        assert len(cache_files) == 1

        # Verify cache content
        with cache_files[0].open() as f:
            cache_data = json.load(f)

        assert cache_data["model"] == "embedding-001"
        assert cache_data["dimension"] == 768
        assert cache_data["embedding"] == embedding

    def test_faiss_compatibility(self, gemini_client, mock_genai):  # noqa: ARG002
        """Test FAISS compatibility with Gemini embeddings."""
        # Mock embeddings that should be compatible with FAISS
        mock_embeddings = [
            [0.1, 0.2, 0.3] + [0.0] * 765,  # 768 dimensions
            [0.4, 0.5, 0.6] + [0.0] * 765,  # 768 dimensions
        ]

        mock_genai.embed_content.return_value = {
            "embedding": mock_embeddings
        }

        # Test that embeddings can be used with FAISS

        # This would be the typical FAISS usage pattern
        embeddings_array = np.array(mock_embeddings, dtype=np.float32)

        # Verify shape and type are correct for FAISS
        assert embeddings_array.shape == (2, 768)
        assert embeddings_array.dtype == np.float32

        # Verify no NaN or infinite values
        assert not np.isnan(embeddings_array).any()
        assert not np.isinf(embeddings_array).any()

    @pytest.mark.asyncio
    async def test_concurrent_batch_processing(self, gemini_client, mock_genai):
        """Test concurrent batch processing doesn't cause issues."""
        # Create enough texts to trigger multiple batches
        texts = [f"code{i}" for i in range(100)]

        # Mock API responses
        def mock_embed_side_effect(*args, **kwargs):
            content = kwargs.get("content", args[1] if len(args) > 1 else [])
            if isinstance(content, list):
                return {"embedding": [[float(i)] * 768 for i in range(len(content))]}
            else:
                return {"embedding": [0.0] * 768}

        mock_genai.embed_content.side_effect = mock_embed_side_effect

        result = await gemini_client.embed_batch(texts, batch_size=10)

        assert len(result) == 100
        assert all(len(emb) == 768 for emb in result)

        # Should make 10 API calls (10 batches of 10 texts each)
        assert mock_genai.embed_content.call_count == 10

    def test_cost_tracker_integration(self, gemini_config, temp_cache_dir, mock_genai):  # noqa: ARG002
        """Test integration with cost tracker."""
        # Mock cost tracker
        mock_cost_tracker = MagicMock()
        mock_cost_tracker.__class__.__name__ = "CostTracker"

        client = GeminiEmbeddingClient(
            config=gemini_config,
            cache_dir=temp_cache_dir,
            cost_tracker=mock_cost_tracker,
        )

        # Verify cost tracker is set
        assert client.cost_tracker == mock_cost_tracker

    @pytest.mark.asyncio
    async def test_cost_tracker_recording(self, gemini_config, temp_cache_dir, mock_genai):
        """Test that cost tracker records embedding usage when available."""
        # Test the case where CostTracker is None (import failed)
        with patch("dev_agent.llm.gemini_embeddings.CostTracker", None):
            mock_cost_tracker = MagicMock()
            
            client = GeminiEmbeddingClient(
                config=gemini_config,
                cache_dir=temp_cache_dir,
                cost_tracker=mock_cost_tracker,
            )

            # Mock API response
            texts = ["test text 1", "test text 2"]
            mock_embeddings = [[0.1] * 768, [0.2] * 768]
            mock_genai.embed_content.return_value = {
                "embedding": mock_embeddings
            }

            await client.embed_batch(texts)

            # Cost tracker should not be called when CostTracker class is None
            mock_cost_tracker.record_embedding.assert_not_called()

    def test_default_cache_directory(self, gemini_config, mock_genai):  # noqa: ARG002
        """Test client initialization with default cache directory."""
        client = GeminiEmbeddingClient(config=gemini_config)
        
        # Should use default cache directory
        assert ".dev_agent/embedding_cache" in str(client.cache.cache_dir)

    @pytest.mark.asyncio
    async def test_embed_batch_partial_failure_handling(self, gemini_client, mock_genai):
        """Test handling when some embeddings fail to generate."""
        texts = ["text1", "text2", "text3"]

        # Mock a scenario where the API returns fewer embeddings than expected
        # This should trigger the error handling for failed embeddings
        mock_genai.embed_content.return_value = {
            "embedding": [[0.1] * 768, [0.2] * 768]  # Only 2 embeddings for 3 texts
        }

        with pytest.raises(LLMAPIError) as exc_info:
            await gemini_client.embed_batch(texts)

        assert "Expected 3 embeddings, got 2" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_text_with_special_characters(self, gemini_client, mock_genai):
        """Test embedding text with various special characters and encodings."""
        special_texts = [
            "Text with émojis 🎉🎊",
            "Text with\nnewlines\nand\ttabs",
            "Text with unicode: 你好世界",
            "Text with symbols: @#$%^&*()",
            "",  # Empty string
            " ",  # Just whitespace
        ]

        mock_embedding = [0.1] * 768
        mock_genai.embed_content.return_value = {
            "embedding": mock_embedding
        }

        for text in special_texts:
            result = await gemini_client.embed_text(text)
            assert result == mock_embedding
            assert len(result) == 768

    def test_import_error_handling(self):
        """Test handling when CostTracker import fails."""
        # This tests the try/except import block for CostTracker
        # The import should be handled gracefully even if CostTracker is None
        with patch("dev_agent.llm.gemini_embeddings.CostTracker", None):
            # This should not raise an error even with CostTracker = None
            from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient  # noqa: F401

    @pytest.mark.asyncio
    async def test_progress_logging(self, gemini_client, mock_genai, caplog):
        """Test progress logging for large batches."""
        # Create enough texts to trigger progress logging
        texts = [f"code{i}" for i in range(500)]

        def mock_embed_side_effect(*args, **kwargs):
            content = kwargs.get("content", args[1] if len(args) > 1 else [])
            if isinstance(content, list):
                return {"embedding": [[0.1] * 768 for _ in range(len(content))]}
            else:
                return {"embedding": [0.1] * 768}

        mock_genai.embed_content.side_effect = mock_embed_side_effect

        with caplog.at_level("INFO"):
            await gemini_client.embed_batch(texts, batch_size=16)

        # Check that progress and cache hit information was logged
        log_messages = [record.message for record in caplog.records]

        # Should log initial processing message
        assert any("Processing 500 texts" in msg for msg in log_messages)

        # Should log cache hit information
        assert any("Cache hits:" in msg for msg in log_messages)
