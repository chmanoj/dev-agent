"""Unit tests for TokenCounter class."""

from __future__ import annotations

import pytest

from dev_agent.llm.token_counter import ModelType, TokenCounter


class TestTokenCounterInitialization:
    """Test TokenCounter initialization."""

    def test_init_with_gpt4(self) -> None:
        """Test initialization with GPT-4 model."""
        counter = TokenCounter("gpt-4")
        assert counter.model == ModelType.GPT_4
        assert counter.get_model_name() == "gpt-4"

    def test_init_with_gpt4_turbo(self) -> None:
        """Test initialization with GPT-4 Turbo model."""
        counter = TokenCounter("gpt-4-turbo")
        assert counter.model == ModelType.GPT_4_TURBO
        assert counter.get_model_name() == "gpt-4-turbo"

    def test_init_with_gpt4_32k(self) -> None:
        """Test initialization with GPT-4 32K model."""
        counter = TokenCounter("gpt-4-32k")
        assert counter.model == ModelType.GPT_4_32K
        assert counter.get_model_name() == "gpt-4-32k"

    def test_init_with_gpt4o(self) -> None:
        """Test initialization with GPT-4o model."""
        counter = TokenCounter("gpt-4o")
        assert counter.model == ModelType.GPT_4O
        assert counter.get_model_name() == "gpt-4o"

    def test_init_with_gpt35_turbo(self) -> None:
        """Test initialization with GPT-3.5 Turbo model."""
        counter = TokenCounter("gpt-3.5-turbo")
        assert counter.model == ModelType.GPT_35_TURBO
        assert counter.get_model_name() == "gpt-3.5-turbo"

    def test_init_with_unsupported_model(self) -> None:
        """Test initialization with unsupported model raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported model"):
            TokenCounter("unsupported-model")

    def test_init_with_deployment_name(self) -> None:
        """Test initialization with Azure deployment name containing model."""
        counter = TokenCounter("my-gpt-4-deployment")
        assert counter.model == ModelType.GPT_4


class TestTokenCounting:
    """Test token counting functionality."""

    def test_count_tokens_simple_text(self) -> None:
        """Test counting tokens in simple text."""
        counter = TokenCounter("gpt-4")
        text = "Hello, world!"
        token_count = counter.count_tokens(text)
        assert token_count > 0
        assert isinstance(token_count, int)

    def test_count_tokens_empty_string(self) -> None:
        """Test counting tokens in empty string returns 0."""
        counter = TokenCounter("gpt-4")
        assert counter.count_tokens("") == 0

    def test_count_tokens_none_raises_error(self) -> None:
        """Test counting tokens with None raises ValueError."""
        counter = TokenCounter("gpt-4")
        with pytest.raises(ValueError, match="Text cannot be None"):
            counter.count_tokens(None)  # type: ignore

    def test_count_tokens_known_example(self) -> None:
        """Test token counting accuracy with known example."""
        counter = TokenCounter("gpt-4")
        # "Hello" is typically 1 token in GPT-4
        text = "Hello"
        token_count = counter.count_tokens(text)
        assert token_count == 1

    def test_count_tokens_multiline_text(self) -> None:
        """Test counting tokens in multiline text."""
        counter = TokenCounter("gpt-4")
        text = """This is a multiline
        text with several
        lines of content."""
        token_count = counter.count_tokens(text)
        assert token_count > 10

    def test_count_tokens_code(self) -> None:
        """Test counting tokens in code."""
        counter = TokenCounter("gpt-4")
        code = """
def hello_world():
    print("Hello, world!")
    return True
"""
        token_count = counter.count_tokens(code)
        assert token_count > 10

    def test_count_tokens_special_characters(self) -> None:
        """Test counting tokens with special characters."""
        counter = TokenCounter("gpt-4")
        text = "Hello! @#$%^&*() 你好"
        token_count = counter.count_tokens(text)
        assert token_count > 0


class TestMessageTokenCounting:
    """Test token counting for chat messages."""

    def test_count_messages_tokens_single_message(self) -> None:
        """Test counting tokens in single message."""
        counter = TokenCounter("gpt-4")
        messages = [{"role": "user", "content": "Hello"}]
        token_count = counter.count_messages_tokens(messages)
        # Should be more than just the content tokens due to formatting
        assert token_count > counter.count_tokens("Hello")

    def test_count_messages_tokens_multiple_messages(self) -> None:
        """Test counting tokens in multiple messages."""
        counter = TokenCounter("gpt-4")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        token_count = counter.count_messages_tokens(messages)
        assert token_count > 10

    def test_count_messages_tokens_with_name(self) -> None:
        """Test counting tokens in messages with name field."""
        counter = TokenCounter("gpt-4")
        messages = [
            {"role": "user", "content": "Hello", "name": "Alice"},
        ]
        token_count = counter.count_messages_tokens(messages)
        assert token_count > counter.count_tokens("Hello")

    def test_count_messages_tokens_empty_list(self) -> None:
        """Test counting tokens in empty message list returns 0."""
        counter = TokenCounter("gpt-4")
        assert counter.count_messages_tokens([]) == 0

    def test_count_messages_tokens_invalid_format(self) -> None:
        """Test counting tokens with invalid message format raises ValueError."""
        counter = TokenCounter("gpt-4")
        with pytest.raises(ValueError, match="must be a dictionary"):
            counter.count_messages_tokens(["not a dict"])  # type: ignore

    def test_count_messages_tokens_missing_role(self) -> None:
        """Test counting tokens with missing role raises ValueError."""
        counter = TokenCounter("gpt-4")
        with pytest.raises(ValueError, match="must have 'role' and 'content'"):
            counter.count_messages_tokens([{"content": "Hello"}])

    def test_count_messages_tokens_missing_content(self) -> None:
        """Test counting tokens with missing content raises ValueError."""
        counter = TokenCounter("gpt-4")
        with pytest.raises(ValueError, match="must have 'role' and 'content'"):
            counter.count_messages_tokens([{"role": "user"}])


class TestCostEstimation:
    """Test cost estimation functionality."""

    def test_estimate_cost_prompt_only(self) -> None:
        """Test cost estimation for prompt tokens only."""
        counter = TokenCounter("gpt-4")
        cost = counter.estimate_cost(prompt_tokens=1000, completion_tokens=0)
        # GPT-4 prompt: $0.03 per 1K tokens
        assert cost == pytest.approx(0.03, rel=1e-6)

    def test_estimate_cost_with_completion(self) -> None:
        """Test cost estimation with prompt and completion tokens."""
        counter = TokenCounter("gpt-4")
        cost = counter.estimate_cost(prompt_tokens=1000, completion_tokens=1000)
        # GPT-4: $0.03 prompt + $0.06 completion per 1K tokens
        assert cost == pytest.approx(0.09, rel=1e-6)

    def test_estimate_cost_gpt4_turbo(self) -> None:
        """Test cost estimation for GPT-4 Turbo."""
        counter = TokenCounter("gpt-4-turbo")
        cost = counter.estimate_cost(prompt_tokens=1000, completion_tokens=1000)
        # GPT-4 Turbo: $0.01 prompt + $0.03 completion per 1K tokens
        assert cost == pytest.approx(0.04, rel=1e-6)

    def test_estimate_cost_gpt35_turbo(self) -> None:
        """Test cost estimation for GPT-3.5 Turbo."""
        counter = TokenCounter("gpt-3.5-turbo")
        cost = counter.estimate_cost(prompt_tokens=1000, completion_tokens=1000)
        # GPT-3.5 Turbo: $0.0015 prompt + $0.002 completion per 1K tokens
        assert cost == pytest.approx(0.0035, rel=1e-6)

    def test_estimate_cost_zero_tokens(self) -> None:
        """Test cost estimation with zero tokens."""
        counter = TokenCounter("gpt-4")
        cost = counter.estimate_cost(prompt_tokens=0, completion_tokens=0)
        assert cost == 0.0

    def test_estimate_cost_negative_tokens_raises_error(self) -> None:
        """Test cost estimation with negative tokens raises ValueError."""
        counter = TokenCounter("gpt-4")
        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            counter.estimate_cost(prompt_tokens=-100, completion_tokens=0)

        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            counter.estimate_cost(prompt_tokens=0, completion_tokens=-100)

    def test_estimate_cost_fractional_tokens(self) -> None:
        """Test cost estimation with fractional token counts."""
        counter = TokenCounter("gpt-4")
        cost = counter.estimate_cost(prompt_tokens=500, completion_tokens=250)
        # 500 * 0.03/1000 + 250 * 0.06/1000 = 0.015 + 0.015 = 0.03
        assert cost == pytest.approx(0.03, rel=1e-6)


class TestContextWindowValidation:
    """Test context window validation."""

    def test_validate_context_window_within_limit(self) -> None:
        """Test validation passes when within context window."""
        counter = TokenCounter("gpt-4")
        is_valid, error_msg = counter.validate_context_window(
            prompt_tokens=4000,
            max_completion_tokens=4000,
        )
        assert is_valid is True
        assert error_msg == ""

    def test_validate_context_window_exceeds_limit(self) -> None:
        """Test validation fails when exceeding context window."""
        counter = TokenCounter("gpt-4")
        is_valid, error_msg = counter.validate_context_window(
            prompt_tokens=7000,
            max_completion_tokens=4000,
        )
        assert is_valid is False
        assert "Token limit exceeded" in error_msg
        assert "8192" in error_msg  # GPT-4 context limit

    def test_validate_context_window_gpt4_32k(self) -> None:
        """Test validation with GPT-4 32K context window."""
        counter = TokenCounter("gpt-4-32k")
        is_valid, error_msg = counter.validate_context_window(
            prompt_tokens=20000,
            max_completion_tokens=10000,
        )
        assert is_valid is True
        assert error_msg == ""

    def test_validate_context_window_gpt4_turbo(self) -> None:
        """Test validation with GPT-4 Turbo large context window."""
        counter = TokenCounter("gpt-4-turbo")
        is_valid, error_msg = counter.validate_context_window(
            prompt_tokens=100000,
            max_completion_tokens=20000,
        )
        assert is_valid is True
        assert error_msg == ""

    def test_validate_context_window_at_exact_limit(self) -> None:
        """Test validation at exact context window limit."""
        counter = TokenCounter("gpt-4")
        is_valid, error_msg = counter.validate_context_window(
            prompt_tokens=4192,
            max_completion_tokens=4000,
        )
        assert is_valid is True
        assert error_msg == ""

    def test_validate_context_window_one_over_limit(self) -> None:
        """Test validation fails when one token over limit."""
        counter = TokenCounter("gpt-4")
        is_valid, error_msg = counter.validate_context_window(
            prompt_tokens=4193,
            max_completion_tokens=4000,
        )
        assert is_valid is False
        assert "Token limit exceeded" in error_msg

    def test_validate_context_window_negative_tokens_raises_error(self) -> None:
        """Test validation with negative tokens raises ValueError."""
        counter = TokenCounter("gpt-4")
        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            counter.validate_context_window(
                prompt_tokens=-100,
                max_completion_tokens=4000,
            )

        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            counter.validate_context_window(
                prompt_tokens=4000,
                max_completion_tokens=-100,
            )


class TestHelperMethods:
    """Test helper methods."""

    def test_get_context_limit_gpt4(self) -> None:
        """Test getting context limit for GPT-4."""
        counter = TokenCounter("gpt-4")
        assert counter.get_context_limit() == 8192

    def test_get_context_limit_gpt4_32k(self) -> None:
        """Test getting context limit for GPT-4 32K."""
        counter = TokenCounter("gpt-4-32k")
        assert counter.get_context_limit() == 32768

    def test_get_context_limit_gpt4_turbo(self) -> None:
        """Test getting context limit for GPT-4 Turbo."""
        counter = TokenCounter("gpt-4-turbo")
        assert counter.get_context_limit() == 128000

    def test_get_pricing_gpt4(self) -> None:
        """Test getting pricing for GPT-4."""
        counter = TokenCounter("gpt-4")
        pricing = counter.get_pricing()
        assert pricing["prompt"] == 0.03
        assert pricing["completion"] == 0.06

    def test_get_pricing_returns_copy(self) -> None:
        """Test that get_pricing returns a copy, not reference."""
        counter = TokenCounter("gpt-4")
        pricing1 = counter.get_pricing()
        pricing2 = counter.get_pricing()
        pricing1["prompt"] = 999.0
        assert pricing2["prompt"] == 0.03  # Should not be modified

    def test_get_model_name(self) -> None:
        """Test getting model name."""
        counter = TokenCounter("gpt-4-turbo")
        assert counter.get_model_name() == "gpt-4-turbo"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_long_text(self) -> None:
        """Test counting tokens in very long text."""
        counter = TokenCounter("gpt-4")
        long_text = "word " * 10000  # 10,000 words
        token_count = counter.count_tokens(long_text)
        assert token_count > 10000

    def test_unicode_text(self) -> None:
        """Test counting tokens in unicode text."""
        counter = TokenCounter("gpt-4")
        unicode_text = "Hello 世界 🌍 مرحبا"
        token_count = counter.count_tokens(unicode_text)
        assert token_count > 0

    def test_whitespace_only(self) -> None:
        """Test counting tokens in whitespace-only text."""
        counter = TokenCounter("gpt-4")
        whitespace = "   \n\t  \n  "
        token_count = counter.count_tokens(whitespace)
        assert token_count >= 0

    def test_different_models_same_text(self) -> None:
        """Test that different models may have different token counts."""
        text = "This is a test sentence."
        counter_gpt4 = TokenCounter("gpt-4")
        counter_gpt35 = TokenCounter("gpt-3.5-turbo")

        count_gpt4 = counter_gpt4.count_tokens(text)
        count_gpt35 = counter_gpt35.count_tokens(text)

        # Both should count tokens (may be same or different)
        assert count_gpt4 > 0
        assert count_gpt35 > 0
