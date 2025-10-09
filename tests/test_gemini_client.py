"""Unit tests for Google Gemini LLM client.

This module tests the GeminiClient implementation including completion
generation, streaming, token counting, cost estimation, retry logic, and
comprehensive error handling for all Gemini exception types.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.api_core import exceptions as google_exceptions
from pydantic import SecretStr

from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTokenLimitError,
)
from dev_agent.llm.gemini_client import GeminiClient
from dev_agent.models.llm_config import GeminiConfig


@pytest.fixture
def gemini_config() -> GeminiConfig:
    """Create test Gemini configuration."""
    return GeminiConfig(
        api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),
        model_name="gemini-pro",
        embedding_model="embedding-001",
        api_endpoint="generativelanguage.googleapis.com",
        max_output_tokens=2048,
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_retries=3,
        timeout=60,
        batch_size=16,
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        },
    )


@pytest.fixture
def mock_gemini_model():
    """Create mock Gemini GenerativeModel."""
    model = MagicMock()

    # Mock successful completion response
    completion_response = MagicMock()
    completion_response.text = "Generated completion text"
    completion_response.usage_metadata = MagicMock(
        prompt_token_count=100,
        candidates_token_count=200,
        total_token_count=300,
    )

    model.generate_content_async = AsyncMock(return_value=completion_response)

    return model


@pytest.fixture
def mock_genai():
    """Create mock google.generativeai module."""
    with patch("dev_agent.llm.gemini_client.genai") as mock:
        # Mock GenerativeModel
        mock_model = MagicMock()
        mock.GenerativeModel.return_value = mock_model

        # Mock token counting
        mock_count_response = MagicMock()
        mock_count_response.total_tokens = 50
        mock.count_tokens.return_value = mock_count_response

        # Mock generation config
        mock.types.GenerationConfig = MagicMock()

        yield mock


@pytest.fixture
def gemini_client(gemini_config):
    """Create GeminiClient with mocked dependencies."""
    return GeminiClient(config=gemini_config)


class TestGeminiClientInitialization:
    """Test Gemini client initialization."""

    def test_initialization_with_config(self, gemini_config, mock_genai):
        """Test client initializes correctly with configuration."""
        client = GeminiClient(config=gemini_config)

        assert client.config == gemini_config
        assert client.model is not None
        assert client.tokenizer is not None

        # Verify genai.configure was called with API key
        mock_genai.configure.assert_called_once_with(
            api_key=gemini_config.get_api_key_value()
        )

        # Verify GenerativeModel was created with correct parameters
        mock_genai.GenerativeModel.assert_called_once()
        call_args = mock_genai.GenerativeModel.call_args
        assert call_args.kwargs["model_name"] == "gemini-pro"

    @pytest.mark.usefixtures("mock_genai")
    def test_initialization_with_safety_settings(self, gemini_config):
        """Test client initializes with safety settings."""
        client = GeminiClient(config=gemini_config)

        # Verify safety settings are built correctly
        safety_settings = client._build_safety_settings()
        assert len(safety_settings) == 2
        assert safety_settings[0]["category"] == "HARM_CATEGORY_HARASSMENT"
        assert safety_settings[0]["threshold"] == "BLOCK_MEDIUM_AND_ABOVE"

    @pytest.mark.usefixtures("mock_genai")
    def test_initialization_without_safety_settings(self):
        """Test client initializes without safety settings."""
        config = GeminiConfig(
            api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),
            model_name="gemini-pro",
        )
        client = GeminiClient(config=config)

        safety_settings = client._build_safety_settings()
        assert safety_settings is None


class TestGenerateCompletion:
    """Test completion generation."""

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_genai")
    async def test_generate_completion_success(self, gemini_client):
        """Test successful completion generation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "Generated Python function"
        gemini_client.model.generate_content_async = AsyncMock(
            return_value=mock_response
        )

        result = await gemini_client.generate_completion(
            prompt="Write a Python function",
            system_prompt="You are a Python expert",
            temperature=0.7,
            max_tokens=1000,
        )

        assert result == "Generated Python function"
        gemini_client.model.generate_content_async.assert_called_once()

        # Verify call arguments
        call_args = gemini_client.model.generate_content_async.call_args
        assert (
            "You are a Python expert\n\nWrite a Python function"
            in call_args.kwargs["contents"]
        )

    @pytest.mark.asyncio
    async def test_generate_completion_without_system_prompt(self, gemini_client):
        """Test completion generation without system prompt."""
        mock_response = MagicMock()
        mock_response.text = "Generated function"
        gemini_client.model.generate_content_async = AsyncMock(
            return_value=mock_response
        )

        result = await gemini_client.generate_completion(
            prompt="Write a function",
            temperature=0.5,
            max_tokens=500,
        )

        assert result == "Generated function"

        # Verify only user prompt is used
        call_args = gemini_client.model.generate_content_async.call_args
        assert call_args.kwargs["contents"] == "Write a function"

    @pytest.mark.asyncio
    async def test_generate_completion_token_limit_exceeded(self, gemini_client):
        """Test error when token limit is exceeded."""
        # Mock count_tokens to return a large number that exceeds the limit
        gemini_client.count_tokens = MagicMock(return_value=35000)

        with pytest.raises(LLMTokenLimitError) as exc_info:
            await gemini_client.generate_completion(
                prompt="test prompt",
                max_tokens=2000,
            )

        assert "30000" in str(exc_info.value)
        assert "exceeds Gemini limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_completion_empty_response(self, gemini_client):
        """Test handling of empty completion response."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.text = None
        gemini_client.model.generate_content_async = AsyncMock(
            return_value=mock_response
        )

        result = await gemini_client.generate_completion(prompt="test")

        assert result == ""

    @pytest.mark.asyncio
    async def test_generate_completion_with_custom_parameters(self, gemini_client):
        """Test completion generation with custom parameters."""
        mock_response = MagicMock()
        mock_response.text = "Custom response"
        gemini_client.model.generate_content_async = AsyncMock(
            return_value=mock_response
        )

        result = await gemini_client.generate_completion(
            prompt="test prompt",
            temperature=0.3,
            max_tokens=1500,
        )

        assert result == "Custom response"

        # Verify generation config was updated
        call_args = gemini_client.model.generate_content_async.call_args
        generation_config = call_args.kwargs["generation_config"]
        assert generation_config is not None


class TestGenerateStreaming:
    """Test streaming completion generation."""

    @pytest.mark.asyncio
    async def test_generate_streaming_success(self, gemini_client):
        """Test successful streaming completion."""

        # Mock streaming response
        async def mock_stream():
            chunks = [
                MagicMock(text="Hello"),
                MagicMock(text=" world"),
                MagicMock(text="!"),
            ]
            for chunk in chunks:
                yield chunk

        gemini_client.model.generate_content_async = AsyncMock(
            return_value=mock_stream()
        )

        # Collect streamed tokens
        tokens = [
            token
            async for token in gemini_client.generate_streaming(
                prompt="Say hello",
                system_prompt="You are helpful",
            )
        ]

        assert tokens == ["Hello", " world", "!"]
        assert "".join(tokens) == "Hello world!"

    @pytest.mark.asyncio
    async def test_generate_streaming_with_empty_chunks(self, gemini_client):
        """Test streaming handles empty content chunks."""

        # Mock streaming response with some empty chunks
        async def mock_stream():
            chunks = [
                MagicMock(text="Hello"),
                MagicMock(text=None),  # Empty chunk
                MagicMock(text=" world"),
                MagicMock(text=""),  # Empty string
            ]
            for chunk in chunks:
                yield chunk

        gemini_client.model.generate_content_async = AsyncMock(
            return_value=mock_stream()
        )

        tokens = [
            token async for token in gemini_client.generate_streaming(prompt="test")
        ]

        assert tokens == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_generate_streaming_token_limit_exceeded(self, gemini_client):
        """Test streaming raises error when token limit exceeded."""
        # Mock count_tokens to return a large number that exceeds the limit
        gemini_client.count_tokens = MagicMock(return_value=35000)

        with pytest.raises(LLMTokenLimitError):
            async for _ in gemini_client.generate_streaming(
                prompt="test prompt",
                max_tokens=2000,
            ):
                pass

    @pytest.mark.asyncio
    async def test_generate_streaming_without_system_prompt(self, gemini_client):
        """Test streaming without system prompt."""

        async def mock_stream():
            yield MagicMock(text="Response")

        gemini_client.model.generate_content_async = AsyncMock(
            return_value=mock_stream()
        )

        tokens = [
            token async for token in gemini_client.generate_streaming(prompt="test")
        ]

        assert tokens == ["Response"]

        # Verify call was made with correct prompt
        call_args = gemini_client.model.generate_content_async.call_args
        assert call_args.kwargs["contents"] == "test"
        assert call_args.kwargs["stream"] is True


class TestTokenCounting:
    """Test token counting functionality."""

    def test_count_tokens_with_gemini_api(self, gemini_client, mock_genai):
        """Test counting tokens using Gemini API."""
        # Mock successful token counting
        mock_response = MagicMock()
        mock_response.total_tokens = 42
        mock_genai.count_tokens.return_value = mock_response

        count = gemini_client.count_tokens("Hello, world!")

        assert count == 42
        mock_genai.count_tokens.assert_called_once_with(
            model="gemini-pro",
            contents="Hello, world!",
        )

    def test_count_tokens_fallback_to_tiktoken(self, gemini_client, mock_genai):
        """Test fallback to tiktoken when Gemini API fails."""
        # Mock Gemini API failure
        mock_genai.count_tokens.side_effect = Exception("API error")

        count = gemini_client.count_tokens("Hello, world!")

        # Should fall back to tiktoken and return a reasonable count
        assert isinstance(count, int)
        assert count > 0
        assert count < 10  # Should be a small number for short text

    def test_count_tokens_empty_string(self, gemini_client, mock_genai):
        """Test counting tokens in empty string."""
        mock_response = MagicMock()
        mock_response.total_tokens = 0
        mock_genai.count_tokens.return_value = mock_response

        count = gemini_client.count_tokens("")

        assert count == 0

    def test_count_tokens_long_text(self, gemini_client, mock_genai):
        """Test counting tokens in longer text."""
        mock_response = MagicMock()
        mock_response.total_tokens = 500
        mock_genai.count_tokens.return_value = mock_response

        text = "This is a longer piece of text " * 100
        count = gemini_client.count_tokens(text)

        assert count == 500


class TestCostEstimation:
    """Test cost estimation functionality."""

    def test_estimate_cost_basic(self, gemini_client):
        """Test basic cost estimation."""
        cost = gemini_client.estimate_cost(
            prompt_tokens=100,
            completion_tokens=200,
        )

        assert isinstance(cost, float)
        assert cost > 0
        # Gemini Pro: $0.50 per 1M input + $1.50 per 1M output
        # = (100/1000000)*0.50 + (200/1000000)*1.50 = 0.00005 + 0.0003 = 0.00035
        expected_cost = (100 / 1_000_000) * 0.50 + (200 / 1_000_000) * 1.50
        assert abs(cost - expected_cost) < 0.000001

    def test_estimate_cost_zero_tokens(self, gemini_client):
        """Test cost estimation with zero tokens."""
        cost = gemini_client.estimate_cost(
            prompt_tokens=0,
            completion_tokens=0,
        )

        assert cost == 0.0

    def test_estimate_cost_only_prompt(self, gemini_client):
        """Test cost estimation with only prompt tokens."""
        cost = gemini_client.estimate_cost(
            prompt_tokens=1_000_000,  # 1M tokens
            completion_tokens=0,
        )

        assert cost == 0.50  # $0.50 per 1M tokens for Gemini input

    def test_estimate_cost_only_completion(self, gemini_client):
        """Test cost estimation with only completion tokens."""
        cost = gemini_client.estimate_cost(
            prompt_tokens=0,
            completion_tokens=1_000_000,  # 1M tokens
        )

        assert cost == 1.50  # $1.50 per 1M tokens for Gemini output


class TestErrorHandling:
    """Test error handling for various Gemini API errors."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, gemini_client):
        """Test handling of authentication errors."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.PermissionDenied("Invalid API key")
        )

        with pytest.raises(LLMAuthenticationError) as exc_info:
            await gemini_client.generate_completion(prompt="test")

        error_message = str(exc_info.value).lower()
        assert "authenticate" in error_message
        assert "gemini" in error_message
        assert "makersuite.google.com" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, gemini_client):
        """Test handling of rate limit errors."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.ResourceExhausted("Rate limit exceeded")
        )

        # Rate limit errors should be retried by tenacity, but eventually raise
        with pytest.raises(google_exceptions.ResourceExhausted):
            await gemini_client.generate_completion(prompt="test")

    @pytest.mark.asyncio
    async def test_timeout_error(self, gemini_client):
        """Test handling of timeout errors."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.DeadlineExceeded("Request timed out")
        )

        # Timeout errors should be retried by tenacity, but eventually raise
        with pytest.raises(google_exceptions.DeadlineExceeded):
            await gemini_client.generate_completion(prompt="test")

    @pytest.mark.asyncio
    async def test_bad_request_error(self, gemini_client):
        """Test handling of bad request errors."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.InvalidArgument("Invalid model name")
        )

        with pytest.raises(LLMBadRequestError) as exc_info:
            await gemini_client.generate_completion(prompt="test")

        assert "Invalid request parameters" in str(exc_info.value)
        assert "model name and parameters are correct" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_general_api_error(self, gemini_client):
        """Test handling of general API errors."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.GoogleAPIError("Internal server error")
        )

        with pytest.raises(LLMAPIError) as exc_info:
            await gemini_client.generate_completion(prompt="test")

        assert "Gemini service error" in str(exc_info.value)
        assert "service status" in str(exc_info.value)


class TestStreamingErrorHandling:
    """Test error handling during streaming."""

    @pytest.mark.asyncio
    async def test_streaming_authentication_error(self, gemini_client):
        """Test authentication error during streaming."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.PermissionDenied("Invalid API key")
        )

        with pytest.raises(LLMAuthenticationError):
            async for _ in gemini_client.generate_streaming(prompt="test"):
                pass

    @pytest.mark.asyncio
    async def test_streaming_rate_limit_error(self, gemini_client):
        """Test rate limit error during streaming."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.ResourceExhausted("Rate limit exceeded")
        )

        with pytest.raises(LLMRateLimitError):
            async for _ in gemini_client.generate_streaming(prompt="test"):
                pass

    @pytest.mark.asyncio
    async def test_streaming_timeout_error(self, gemini_client):
        """Test timeout error during streaming."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.DeadlineExceeded("Request timed out")
        )

        with pytest.raises(LLMTimeoutError):
            async for _ in gemini_client.generate_streaming(prompt="test"):
                pass

    @pytest.mark.asyncio
    async def test_streaming_bad_request_error(self, gemini_client):
        """Test bad request error during streaming."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.InvalidArgument("Invalid parameters")
        )

        with pytest.raises(LLMBadRequestError):
            async for _ in gemini_client.generate_streaming(prompt="test"):
                pass

    @pytest.mark.asyncio
    async def test_streaming_general_api_error(self, gemini_client):
        """Test general API error during streaming."""
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.GoogleAPIError("Server error")
        )

        with pytest.raises(LLMAPIError):
            async for _ in gemini_client.generate_streaming(prompt="test"):
                pass


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_then_success(self, gemini_client):
        """Test retry succeeds after rate limit error."""
        call_count = 0

        async def side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise google_exceptions.ResourceExhausted("Rate limit")
            # Second call succeeds
            response = MagicMock()
            response.text = "Success after retry"
            return response

        gemini_client.model.generate_content_async = AsyncMock(side_effect=side_effect)

        result = await gemini_client.generate_completion(prompt="test")

        assert result == "Success after retry"
        assert call_count == 2  # Should have retried once

    @pytest.mark.asyncio
    async def test_retry_on_timeout_then_success(self, gemini_client):
        """Test retry succeeds after timeout error."""
        call_count = 0

        async def side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise google_exceptions.DeadlineExceeded("Timeout")
            # Second call succeeds
            response = MagicMock()
            response.text = "Success after timeout"
            return response

        gemini_client.model.generate_content_async = AsyncMock(side_effect=side_effect)

        result = await gemini_client.generate_completion(prompt="test")

        assert result == "Success after timeout"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_authentication_error(self, gemini_client):
        """Test authentication errors are not retried."""
        call_count = 0

        async def side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            raise google_exceptions.PermissionDenied("Invalid key")

        gemini_client.model.generate_content_async = AsyncMock(side_effect=side_effect)

        with pytest.raises(LLMAuthenticationError):
            await gemini_client.generate_completion(prompt="test")

        # Should only be called once (no retries for auth errors)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_on_bad_request_error(self, gemini_client):
        """Test bad request errors are not retried."""
        call_count = 0

        async def side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            raise google_exceptions.InvalidArgument("Invalid params")

        gemini_client.model.generate_content_async = AsyncMock(side_effect=side_effect)

        with pytest.raises(LLMBadRequestError):
            await gemini_client.generate_completion(prompt="test")

        # Should only be called once (no retries for bad request)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_exhaustion_on_rate_limit(self, gemini_client):
        """Test retry exhaustion after max attempts."""
        # Mock persistent rate limit error
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.ResourceExhausted("Persistent rate limit")
        )

        # Should eventually raise the original exception after retries
        with pytest.raises(google_exceptions.ResourceExhausted):
            await gemini_client.generate_completion(prompt="test")

    @pytest.mark.asyncio
    async def test_retry_exhaustion_on_timeout(self, gemini_client):
        """Test retry exhaustion after max attempts for timeout."""
        # Mock persistent timeout error
        gemini_client.model.generate_content_async = AsyncMock(
            side_effect=google_exceptions.DeadlineExceeded("Persistent timeout")
        )

        # Should eventually raise the original exception after retries
        with pytest.raises(google_exceptions.DeadlineExceeded):
            await gemini_client.generate_completion(prompt="test")


class TestPromptBuilding:
    """Test prompt building functionality."""

    def test_build_prompt_with_system_prompt(self, gemini_client):
        """Test building prompt with system prompt."""
        result = gemini_client._build_prompt(
            prompt="Write a function",
            system_prompt="You are a Python expert",
        )

        assert result == "You are a Python expert\n\nWrite a function"

    def test_build_prompt_without_system_prompt(self, gemini_client):
        """Test building prompt without system prompt."""
        result = gemini_client._build_prompt(
            prompt="Write a function",
            system_prompt=None,
        )

        assert result == "Write a function"

    def test_build_prompt_empty_prompts(self, gemini_client):
        """Test building prompt with empty strings."""
        result = gemini_client._build_prompt(
            prompt="",
            system_prompt="",
        )

        assert result == ""


class TestSafetySettings:
    """Test safety settings functionality."""

    def test_build_safety_settings_with_config(self, gemini_client):
        """Test building safety settings from configuration."""
        safety_settings = gemini_client._build_safety_settings()

        assert len(safety_settings) == 2
        assert safety_settings[0]["category"] == "HARM_CATEGORY_HARASSMENT"
        assert safety_settings[0]["threshold"] == "BLOCK_MEDIUM_AND_ABOVE"
        assert safety_settings[1]["category"] == "HARM_CATEGORY_HATE_SPEECH"
        assert safety_settings[1]["threshold"] == "BLOCK_MEDIUM_AND_ABOVE"

    @pytest.mark.usefixtures("mock_genai")
    def test_build_safety_settings_empty_config(self):
        """Test building safety settings with empty configuration."""
        config = GeminiConfig(
            api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),
            model_name="gemini-pro",
            safety_settings={},
        )
        client = GeminiClient(config=config)

        safety_settings = client._build_safety_settings()

        assert safety_settings is None


class TestConfigurationIntegration:
    """Test integration with different configuration options."""

    @pytest.mark.usefixtures("mock_genai")
    def test_client_with_minimal_config(self):
        """Test client with minimal configuration."""
        config = GeminiConfig(
            api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),
            model_name="gemini-pro",
        )
        client = GeminiClient(config=config)

        assert client.config.temperature == 0.7  # Default value
        assert client.config.max_output_tokens == 2048  # Default value
        assert client.config.top_p == 0.95  # Default value
        assert client.config.top_k == 40  # Default value

    @pytest.mark.usefixtures("mock_genai")
    def test_client_with_custom_config(self):
        """Test client with custom configuration."""
        config = GeminiConfig(
            api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),
            model_name="gemini-1.5-pro",
            temperature=0.3,
            max_output_tokens=4096,
            top_p=0.8,
            top_k=20,
        )
        client = GeminiClient(config=config)

        assert client.config.temperature == 0.3
        assert client.config.max_output_tokens == 4096
        assert client.config.top_p == 0.8
        assert client.config.top_k == 20

    def test_client_with_different_models(self, mock_genai):
        """Test client with different Gemini models."""
        models = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]

        for model_name in models:
            config = GeminiConfig(
                api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),
                model_name=model_name,
            )
            client = GeminiClient(config=config)

            assert client.config.model_name == model_name
            # Verify GenerativeModel was called with correct model name
            mock_genai.GenerativeModel.assert_called()
            call_args = mock_genai.GenerativeModel.call_args
            assert call_args.kwargs["model_name"] == model_name
