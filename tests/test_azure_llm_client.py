"""Unit tests for Azure OpenAI LLM client.

This module tests the AzureOpenAIClient implementation including completion
generation, streaming, token counting, cost estimation, retry logic, and
comprehensive error handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import (
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from pydantic import SecretStr

from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTokenLimitError,
)
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.models.llm_config import AzureOpenAIConfig


@pytest.fixture
def azure_config() -> AzureOpenAIConfig:
    """Create test Azure OpenAI configuration."""
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
def mock_azure_openai_client():
    """Create mock AsyncAzureOpenAI client."""
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

    client.chat.completions.create = AsyncMock(return_value=completion_response)

    return client


@pytest.fixture
def llm_client(azure_config, mock_azure_openai_client):
    """Create AzureOpenAIClient with mocked Azure client."""
    return AzureOpenAIClient(config=azure_config, client=mock_azure_openai_client)


class TestAzureOpenAIClientInitialization:
    """Test Azure OpenAI client initialization."""

    def test_initialization_with_config(self, azure_config, mock_azure_openai_client):
        """Test client initializes correctly with configuration."""
        client = AzureOpenAIClient(config=azure_config, client=mock_azure_openai_client)

        assert client.config == azure_config
        assert client.client == mock_azure_openai_client
        assert client.token_counter is not None
        assert client.token_counter.get_model_name() == "gpt-4"

    def test_initialization_creates_token_counter(self, azure_config, mock_azure_openai_client):
        """Test token counter is created with correct model."""
        client = AzureOpenAIClient(config=azure_config, client=mock_azure_openai_client)

        assert client.token_counter.get_model_name() == "gpt-4"
        assert client.token_counter.get_context_limit() == 8192


class TestGenerateCompletion:
    """Test completion generation."""

    @pytest.mark.asyncio
    async def test_generate_completion_success(self, llm_client, mock_azure_openai_client):
        """Test successful completion generation."""
        result = await llm_client.generate_completion(
            prompt="Write a Python function",
            system_prompt="You are a Python expert",
            temperature=0.7,
            max_tokens=1000,
        )

        assert result == "Generated completion text"
        mock_azure_openai_client.chat.completions.create.assert_called_once()

        # Verify call arguments
        call_args = mock_azure_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["temperature"] == 0.7
        assert call_args.kwargs["max_tokens"] == 1000
        assert len(call_args.kwargs["messages"]) == 2
        assert call_args.kwargs["messages"][0]["role"] == "system"
        assert call_args.kwargs["messages"][1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_completion_without_system_prompt(
        self, llm_client, mock_azure_openai_client
    ):
        """Test completion generation without system prompt."""
        result = await llm_client.generate_completion(
            prompt="Write a function",
            temperature=0.5,
            max_tokens=500,
        )

        assert result == "Generated completion text"

        # Verify only user message is sent
        call_args = mock_azure_openai_client.chat.completions.create.call_args
        assert len(call_args.kwargs["messages"]) == 1
        assert call_args.kwargs["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_completion_token_limit_exceeded(self, llm_client):
        """Test error when token limit is exceeded."""
        # Create a very long prompt that exceeds context window
        long_prompt = "test " * 10000  # Should exceed GPT-4's 8192 token limit

        with pytest.raises(LLMTokenLimitError) as exc_info:
            await llm_client.generate_completion(
                prompt=long_prompt,
                max_tokens=4000,
            )

        assert "Token limit exceeded" in str(exc_info.value)
        assert "8192" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_completion_empty_response(
        self, llm_client, mock_azure_openai_client
    ):
        """Test handling of empty completion response."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10,
        )
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await llm_client.generate_completion(prompt="test")

        assert result == ""


class TestGenerateStreaming:
    """Test streaming completion generation."""

    @pytest.mark.asyncio
    async def test_generate_streaming_success(self, llm_client, mock_azure_openai_client):
        """Test successful streaming completion."""
        # Mock streaming response
        async def mock_stream():
            chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
            ]
            for chunk in chunks:
                yield chunk

        mock_azure_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )

        # Collect streamed tokens
        tokens = [
            token
            async for token in llm_client.generate_streaming(
                prompt="Say hello",
                system_prompt="You are helpful",
            )
        ]

        assert tokens == ["Hello", " world", "!"]
        assert "".join(tokens) == "Hello world!"

    @pytest.mark.asyncio
    async def test_generate_streaming_with_empty_chunks(
        self, llm_client, mock_azure_openai_client
    ):
        """Test streaming handles empty content chunks."""
        # Mock streaming response with some empty chunks
        async def mock_stream():
            chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),  # Empty
                MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
                MagicMock(choices=[]),  # No choices
            ]
            for chunk in chunks:
                yield chunk

        mock_azure_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )

        tokens = [token async for token in llm_client.generate_streaming(prompt="test")]

        assert tokens == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_generate_streaming_token_limit_exceeded(self, llm_client):
        """Test streaming raises error when token limit exceeded."""
        long_prompt = "test " * 10000

        with pytest.raises(LLMTokenLimitError):
            async for _ in llm_client.generate_streaming(
                prompt=long_prompt,
                max_tokens=4000,
            ):
                pass


class TestTokenCounting:
    """Test token counting functionality."""

    def test_count_tokens_simple_text(self, llm_client):
        """Test counting tokens in simple text."""
        text = "Hello, world!"
        count = llm_client.count_tokens(text)

        assert isinstance(count, int)
        assert count > 0
        assert count < 10  # Should be a small number

    def test_count_tokens_empty_string(self, llm_client):
        """Test counting tokens in empty string."""
        count = llm_client.count_tokens("")

        assert count == 0

    def test_count_tokens_long_text(self, llm_client):
        """Test counting tokens in longer text."""
        text = "This is a longer piece of text " * 100
        count = llm_client.count_tokens(text)

        assert count > 100  # Should be substantial


class TestCostEstimation:
    """Test cost estimation functionality."""

    def test_estimate_cost_basic(self, llm_client):
        """Test basic cost estimation."""
        cost = llm_client.estimate_cost(
            prompt_tokens=100,
            completion_tokens=200,
        )

        assert isinstance(cost, float)
        assert cost > 0
        # GPT-4: $0.03 per 1K prompt + $0.06 per 1K completion
        # = (100/1000)*0.03 + (200/1000)*0.06 = 0.003 + 0.012 = 0.015
        assert abs(cost - 0.015) < 0.001

    def test_estimate_cost_zero_tokens(self, llm_client):
        """Test cost estimation with zero tokens."""
        cost = llm_client.estimate_cost(
            prompt_tokens=0,
            completion_tokens=0,
        )

        assert cost == 0.0

    def test_estimate_cost_only_prompt(self, llm_client):
        """Test cost estimation with only prompt tokens."""
        cost = llm_client.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=0,
        )

        assert cost == 0.03  # $0.03 per 1K tokens for GPT-4 prompt


class TestErrorHandling:
    """Test error handling for various API errors."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, llm_client, mock_azure_openai_client):
        """Test handling of authentication errors."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=AuthenticationError(
                "Invalid API key",
                response=MagicMock(status_code=401),
                body=None,
            )
        )

        with pytest.raises(LLMAuthenticationError) as exc_info:
            await llm_client.generate_completion(prompt="test")

        error_message = str(exc_info.value).lower()
        assert "authenticate" in error_message
        assert "azure" in error_message

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, llm_client, mock_azure_openai_client):
        """Test handling of rate limit errors."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError(
                "Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None,
            )
        )

        # Rate limit errors should be retried, but after max retries should raise
        with pytest.raises(RateLimitError):
            await llm_client.generate_completion(prompt="test")

    @pytest.mark.asyncio
    async def test_timeout_error(self, llm_client, mock_azure_openai_client):
        """Test handling of timeout errors."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )

        # Timeout errors should be retried, but after max retries should raise
        with pytest.raises(APITimeoutError):
            await llm_client.generate_completion(prompt="test")

    @pytest.mark.asyncio
    async def test_bad_request_error(self, llm_client, mock_azure_openai_client):
        """Test handling of bad request errors."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=BadRequestError(
                "Invalid deployment name",
                response=MagicMock(status_code=400),
                body=None,
            )
        )

        with pytest.raises(LLMBadRequestError) as exc_info:
            await llm_client.generate_completion(prompt="test")

        assert "Invalid request" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_error(self, llm_client, mock_azure_openai_client):
        """Test handling of general API errors."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=APIError(
                "Internal server error",
                request=MagicMock(),
                body=None,
            )
        )

        with pytest.raises(LLMAPIError) as exc_info:
            await llm_client.generate_completion(prompt="test")

        assert "service error" in str(exc_info.value).lower()


class TestStreamingErrorHandling:
    """Test error handling during streaming."""

    @pytest.mark.asyncio
    async def test_streaming_authentication_error(
        self, llm_client, mock_azure_openai_client
    ):
        """Test authentication error during streaming."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=AuthenticationError(
                "Invalid API key",
                response=MagicMock(status_code=401),
                body=None,
            )
        )

        with pytest.raises(LLMAuthenticationError):
            async for _ in llm_client.generate_streaming(prompt="test"):
                pass

    @pytest.mark.asyncio
    async def test_streaming_rate_limit_error(
        self, llm_client, mock_azure_openai_client
    ):
        """Test rate limit error during streaming."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError(
                "Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None,
            )
        )

        with pytest.raises(LLMRateLimitError):
            async for _ in llm_client.generate_streaming(prompt="test"):
                pass

    @pytest.mark.asyncio
    async def test_streaming_timeout_error(self, llm_client, mock_azure_openai_client):
        """Test timeout error during streaming."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )

        with pytest.raises(LLMTimeoutError):
            async for _ in llm_client.generate_streaming(prompt="test"):
                pass

    @pytest.mark.asyncio
    async def test_streaming_bad_request_error(
        self, llm_client, mock_azure_openai_client
    ):
        """Test bad request error during streaming."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=BadRequestError(
                "Invalid parameters",
                response=MagicMock(status_code=400),
                body=None,
            )
        )

        with pytest.raises(LLMBadRequestError):
            async for _ in llm_client.generate_streaming(prompt="test"):
                pass

    @pytest.mark.asyncio
    async def test_streaming_api_error(self, llm_client, mock_azure_openai_client):
        """Test general API error during streaming."""
        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=APIError(
                "Server error",
                request=MagicMock(),
                body=None,
            )
        )

        with pytest.raises(LLMAPIError):
            async for _ in llm_client.generate_streaming(prompt="test"):
                pass


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_then_success(
        self, llm_client, mock_azure_openai_client
    ):
        """Test retry succeeds after rate limit error."""
        # First call fails with rate limit, second succeeds
        call_count = 0

        async def side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError(
                    "Rate limit",
                    response=MagicMock(status_code=429),
                    body=None,
                )
            # Second call succeeds
            response = MagicMock()
            response.choices = [
                MagicMock(message=MagicMock(content="Success after retry"))
            ]
            response.usage = MagicMock(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
            )
            return response

        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=side_effect
        )

        result = await llm_client.generate_completion(prompt="test")

        assert result == "Success after retry"
        assert call_count == 2  # Should have retried once

    @pytest.mark.asyncio
    async def test_retry_on_timeout_then_success(
        self, llm_client, mock_azure_openai_client
    ):
        """Test retry succeeds after timeout error."""
        call_count = 0

        async def side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APITimeoutError(request=MagicMock())
            # Second call succeeds
            response = MagicMock()
            response.choices = [
                MagicMock(message=MagicMock(content="Success after timeout"))
            ]
            response.usage = MagicMock(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
            )
            return response

        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=side_effect
        )

        result = await llm_client.generate_completion(prompt="test")

        assert result == "Success after timeout"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_authentication_error(
        self, llm_client, mock_azure_openai_client
    ):
        """Test authentication errors are not retried."""
        call_count = 0

        async def side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            raise AuthenticationError(
                "Invalid key",
                response=MagicMock(status_code=401),
                body=None,
            )

        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=side_effect
        )

        with pytest.raises(LLMAuthenticationError):
            await llm_client.generate_completion(prompt="test")

        # Should only be called once (no retries for auth errors)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_on_bad_request_error(
        self, llm_client, mock_azure_openai_client
    ):
        """Test bad request errors are not retried."""
        call_count = 0

        async def side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            raise BadRequestError(
                "Invalid params",
                response=MagicMock(status_code=400),
                body=None,
            )

        mock_azure_openai_client.chat.completions.create = AsyncMock(
            side_effect=side_effect
        )

        with pytest.raises(LLMBadRequestError):
            await llm_client.generate_completion(prompt="test")

        # Should only be called once (no retries for bad request)
        assert call_count == 1
