"""Unit tests for prompt templates module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from dev_agent.llm.prompt_templates import (
    CODE_GENERATION_TEMPLATE,
    DESIGN_TEMPLATE,
    SPECIFICATION_TEMPLATE,
    TASK_GENERATION_TEMPLATE,
    TEMPLATES,
    PromptTemplate,
    get_template,
    inject_context,
)


class TestPromptTemplateInitialization:
    """Test PromptTemplate initialization."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default values."""
        template = PromptTemplate(
            system_prompt="System prompt",
            user_prompt_template="User prompt: {context}",
        )
        assert template.system_prompt == "System prompt"
        assert template.user_prompt_template == "User prompt: {context}"
        assert template.required_context == []
        assert template.max_context_tokens == 6000
        assert template.temperature == 0.7
        assert template.max_tokens == 4000

    def test_init_with_custom_values(self) -> None:
        """Test initialization with custom values."""
        template = PromptTemplate(
            system_prompt="Custom system",
            user_prompt_template="Custom user: {key}",
            required_context=["key"],
            max_context_tokens=4000,
            temperature=0.5,
            max_tokens=2000,
        )
        assert template.system_prompt == "Custom system"
        assert template.user_prompt_template == "Custom user: {key}"
        assert template.required_context == ["key"]
        assert template.max_context_tokens == 4000
        assert template.temperature == 0.5
        assert template.max_tokens == 2000


class TestTemplateRendering:
    """Test template rendering functionality."""

    def test_render_simple_template(self) -> None:
        """Test rendering a simple template with context."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Hello {name}!",
        )
        system, user = template.render({"name": "World"})
        assert system == "System"
        assert user == "Hello World!"

    def test_render_multiple_placeholders(self) -> None:
        """Test rendering template with multiple placeholders."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Name: {name}, Age: {age}, City: {city}",
        )
        context = {"name": "Alice", "age": "30", "city": "NYC"}
        system, user = template.render(context)
        assert user == "Name: Alice, Age: 30, City: NYC"

    def test_render_with_required_context(self) -> None:
        """Test rendering with required context keys."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Required: {key1}, {key2}",
            required_context=["key1", "key2"],
        )
        context = {"key1": "value1", "key2": "value2"}
        system, user = template.render(context)
        assert user == "Required: value1, value2"

    def test_render_missing_required_context_raises_error(self) -> None:
        """Test rendering with missing required context raises ValueError."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Required: {key1}",
            required_context=["key1", "key2"],
        )
        with pytest.raises(ValueError, match="Missing required context keys: \\['key2'\\]"):
            template.render({"key1": "value1"})

    def test_render_undefined_placeholder_raises_error(self) -> None:
        """Test rendering with undefined placeholder raises ValueError."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Value: {undefined_key}",
        )
        with pytest.raises(ValueError, match="Template references undefined context key"):
            template.render({})

    def test_render_with_extra_context(self) -> None:
        """Test rendering with extra context keys (should be ignored)."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Value: {key1}",
        )
        context = {"key1": "value1", "extra_key": "extra_value"}
        system, user = template.render(context)
        assert user == "Value: value1"

    def test_render_multiline_template(self) -> None:
        """Test rendering multiline template."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="""Line 1: {line1}
Line 2: {line2}
Line 3: {line3}""",
        )
        context = {"line1": "First", "line2": "Second", "line3": "Third"}
        system, user = template.render(context)
        assert "Line 1: First" in user
        assert "Line 2: Second" in user
        assert "Line 3: Third" in user


class TestContextInjection:
    """Test context injection functionality."""

    def test_inject_context_simple(self) -> None:
        """Test injecting context into template."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Context: {value}",
        )
        system, user = inject_context(template, {"value": "test"})
        assert system == "System"
        assert user == "Context: test"

    def test_inject_context_with_token_counter(self) -> None:
        """Test injecting context with token counter."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Context: {value}",
            max_context_tokens=100,
        )
        mock_counter = MagicMock()
        mock_counter.count_tokens.return_value = 50  # Within limit

        system, user = inject_context(template, {"value": "test"}, mock_counter)
        assert user == "Context: test"
        mock_counter.count_tokens.assert_called()

    def test_inject_context_missing_required_raises_error(self) -> None:
        """Test injecting context with missing required keys raises error."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Value: {key}",
            required_context=["key"],
        )
        with pytest.raises(ValueError, match="Missing required context keys"):
            inject_context(template, {})


class TestIntelligentTruncation:
    """Test intelligent truncation functionality."""

    def test_truncation_not_needed_when_within_limit(self) -> None:
        """Test that truncation is not applied when within token limit."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Context: {value}",
            max_context_tokens=1000,
        )
        mock_counter = MagicMock()
        mock_counter.count_tokens.return_value = 500  # Within limit

        context = {"value": "Short text"}
        system, user = template.render(context, mock_counter)
        assert user == "Context: Short text"

    def test_truncation_applied_when_exceeds_limit(self) -> None:
        """Test that truncation is applied when exceeding token limit."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Context: {relevant_code_chunks}",
            max_context_tokens=100,
        )
        mock_counter = MagicMock()
        # First call: exceeds limit, second call: within limit after truncation
        mock_counter.count_tokens.side_effect = [200, 80]

        long_text = "x" * 1000
        context = {"relevant_code_chunks": long_text}
        system, user = template.render(context, mock_counter)

        # Should be truncated
        assert "[truncated]" in user
        assert len(user) < len(f"Context: {long_text}")

    def test_truncation_prioritizes_truncatable_keys(self) -> None:
        """Test that truncation prioritizes specific keys."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Code: {relevant_code_chunks}, Other: {other}",
            max_context_tokens=100,
        )
        mock_counter = MagicMock()
        mock_counter.count_tokens.side_effect = [200, 80]

        context = {
            "relevant_code_chunks": "x" * 1000,
            "other": "important",
        }
        system, user = template.render(context, mock_counter)

        # relevant_code_chunks should be truncated, other should remain
        assert "[truncated]" in user
        assert "important" in user

    def test_truncation_stops_at_minimum_length(self) -> None:
        """Test that truncation stops at minimum length threshold."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Context: {relevant_code_chunks}",
            max_context_tokens=10,
        )
        mock_counter = MagicMock()
        # Always return high count to force truncation attempts
        mock_counter.count_tokens.return_value = 1000

        short_text = "short"
        context = {"relevant_code_chunks": short_text}
        system, user = template.render(context, mock_counter)

        # Should not truncate below minimum (100 chars)
        # Since text is already short, it won't be truncated much
        assert "Context:" in user

    def test_truncation_with_multiple_truncatable_keys(self) -> None:
        """Test truncation with multiple truncatable keys."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Code: {relevant_code_chunks}, Patterns: {code_patterns}",
            max_context_tokens=100,
        )
        mock_counter = MagicMock()
        mock_counter.count_tokens.side_effect = [300, 200, 80]

        context = {
            "relevant_code_chunks": "x" * 1000,
            "code_patterns": "y" * 1000,
        }
        system, user = template.render(context, mock_counter)

        # Both should be truncated
        assert "[truncated]" in user

    def test_truncation_preserves_non_truncatable_keys(self) -> None:
        """Test that truncation preserves non-truncatable keys."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Code: {relevant_code_chunks}, Feature: {feature_description}",
            max_context_tokens=100,
        )
        mock_counter = MagicMock()
        mock_counter.count_tokens.side_effect = [200, 80]

        context = {
            "relevant_code_chunks": "x" * 1000,
            "feature_description": "Important feature",
        }
        system, user = template.render(context, mock_counter)

        # Feature description should not be truncated
        assert "Important feature" in user
        assert "[truncated]" in user


class TestPredefinedTemplates:
    """Test predefined template instances."""

    def test_specification_template_exists(self) -> None:
        """Test that specification template is defined."""
        assert SPECIFICATION_TEMPLATE is not None
        assert SPECIFICATION_TEMPLATE.system_prompt != ""
        assert SPECIFICATION_TEMPLATE.user_prompt_template != ""
        assert len(SPECIFICATION_TEMPLATE.required_context) > 0

    def test_specification_template_required_context(self) -> None:
        """Test specification template has required context keys."""
        required = SPECIFICATION_TEMPLATE.required_context
        assert "codebase_summary" in required
        assert "relevant_code_chunks" in required
        assert "detected_patterns" in required
        assert "feature_description" in required

    def test_specification_template_renders(self) -> None:
        """Test specification template can be rendered."""
        context = {
            "codebase_summary": "Summary",
            "relevant_code_chunks": "Code",
            "detected_patterns": "Patterns",
            "feature_description": "Feature",
        }
        system, user = SPECIFICATION_TEMPLATE.render(context)
        assert "Summary" in user
        assert "Code" in user
        assert "Patterns" in user
        assert "Feature" in user

    def test_design_template_exists(self) -> None:
        """Test that design template is defined."""
        assert DESIGN_TEMPLATE is not None
        assert DESIGN_TEMPLATE.system_prompt != ""
        assert DESIGN_TEMPLATE.user_prompt_template != ""
        assert len(DESIGN_TEMPLATE.required_context) > 0

    def test_design_template_required_context(self) -> None:
        """Test design template has required context keys."""
        required = DESIGN_TEMPLATE.required_context
        assert "specification" in required
        assert "existing_architecture" in required
        assert "code_patterns" in required

    def test_design_template_renders(self) -> None:
        """Test design template can be rendered."""
        context = {
            "specification": "Spec",
            "existing_architecture": "Arch",
            "code_patterns": "Patterns",
            "similar_implementations": "Similar",
        }
        system, user = DESIGN_TEMPLATE.render(context)
        assert "Spec" in user
        assert "Arch" in user
        assert "Patterns" in user

    def test_code_generation_template_exists(self) -> None:
        """Test that code generation template is defined."""
        assert CODE_GENERATION_TEMPLATE is not None
        assert CODE_GENERATION_TEMPLATE.system_prompt != ""
        assert CODE_GENERATION_TEMPLATE.user_prompt_template != ""
        assert len(CODE_GENERATION_TEMPLATE.required_context) > 0

    def test_code_generation_template_required_context(self) -> None:
        """Test code generation template has required context keys."""
        required = CODE_GENERATION_TEMPLATE.required_context
        assert "specification" in required
        assert "design" in required
        assert "code_patterns" in required
        assert "similar_code" in required

    def test_code_generation_template_renders(self) -> None:
        """Test code generation template can be rendered."""
        context = {
            "specification": "Spec",
            "design": "Design",
            "code_patterns": "Patterns",
            "similar_code": "Similar",
            "style_requirements": "Style",
        }
        system, user = CODE_GENERATION_TEMPLATE.render(context)
        assert "Spec" in user
        assert "Design" in user
        assert "Patterns" in user

    def test_task_generation_template_exists(self) -> None:
        """Test that task generation template is defined."""
        assert TASK_GENERATION_TEMPLATE is not None
        assert TASK_GENERATION_TEMPLATE.system_prompt != ""
        assert TASK_GENERATION_TEMPLATE.user_prompt_template != ""
        assert len(TASK_GENERATION_TEMPLATE.required_context) > 0

    def test_task_generation_template_required_context(self) -> None:
        """Test task generation template has required context keys."""
        required = TASK_GENERATION_TEMPLATE.required_context
        assert "specification" in required
        assert "design" in required

    def test_task_generation_template_renders(self) -> None:
        """Test task generation template can be rendered."""
        context = {
            "specification": "Spec",
            "design": "Design",
            "complexity_analysis": "Complex",
        }
        system, user = TASK_GENERATION_TEMPLATE.render(context)
        assert "Spec" in user
        assert "Design" in user


class TestTemplateRegistry:
    """Test template registry functionality."""

    def test_templates_registry_contains_all_templates(self) -> None:
        """Test that TEMPLATES registry contains all predefined templates."""
        assert "specification" in TEMPLATES
        assert "design" in TEMPLATES
        assert "code_generation" in TEMPLATES
        assert "task_generation" in TEMPLATES

    def test_get_template_specification(self) -> None:
        """Test getting specification template by name."""
        template = get_template("specification")
        assert template is SPECIFICATION_TEMPLATE

    def test_get_template_design(self) -> None:
        """Test getting design template by name."""
        template = get_template("design")
        assert template is DESIGN_TEMPLATE

    def test_get_template_code_generation(self) -> None:
        """Test getting code generation template by name."""
        template = get_template("code_generation")
        assert template is CODE_GENERATION_TEMPLATE

    def test_get_template_task_generation(self) -> None:
        """Test getting task generation template by name."""
        template = get_template("task_generation")
        assert template is TASK_GENERATION_TEMPLATE

    def test_get_template_invalid_name_raises_error(self) -> None:
        """Test getting template with invalid name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown template: invalid"):
            get_template("invalid")

    def test_get_template_error_message_shows_available(self) -> None:
        """Test that error message shows available templates."""
        with pytest.raises(ValueError, match="Available templates:"):
            get_template("nonexistent")


class TestTemplateConfiguration:
    """Test template configuration values."""

    def test_all_templates_have_reasonable_token_limits(self) -> None:
        """Test that all templates have reasonable token limits."""
        for template in TEMPLATES.values():
            assert template.max_context_tokens > 0
            assert template.max_context_tokens <= 128000  # Max for GPT-4 Turbo
            assert template.max_tokens > 0
            assert template.max_tokens <= 128000

    def test_all_templates_have_valid_temperature(self) -> None:
        """Test that all templates have valid temperature values."""
        for template in TEMPLATES.values():
            assert 0.0 <= template.temperature <= 2.0

    def test_all_templates_have_system_prompts(self) -> None:
        """Test that all templates have non-empty system prompts."""
        for template in TEMPLATES.values():
            assert template.system_prompt != ""
            assert len(template.system_prompt) > 10

    def test_all_templates_have_user_prompts(self) -> None:
        """Test that all templates have non-empty user prompt templates."""
        for template in TEMPLATES.values():
            assert template.user_prompt_template != ""
            assert len(template.user_prompt_template) > 10

    def test_all_templates_have_required_context(self) -> None:
        """Test that all templates specify required context."""
        for template in TEMPLATES.values():
            assert len(template.required_context) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_render_with_empty_context_value(self) -> None:
        """Test rendering with empty string context value."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Value: {key}",
        )
        system, user = template.render({"key": ""})
        assert user == "Value: "

    def test_render_with_numeric_context_value(self) -> None:
        """Test rendering with numeric context value."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Number: {num}",
        )
        system, user = template.render({"num": 42})
        assert user == "Number: 42"

    def test_render_with_none_token_counter(self) -> None:
        """Test rendering with None token counter (no truncation)."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Value: {key}",
        )
        system, user = template.render({"key": "test"}, token_counter=None)
        assert user == "Value: test"

    def test_truncation_with_non_string_value(self) -> None:
        """Test that truncation only applies to string values."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Code: {relevant_code_chunks}, Num: {number}",
            max_context_tokens=100,
        )
        mock_counter = MagicMock()
        mock_counter.count_tokens.side_effect = [200, 80]

        context = {
            "relevant_code_chunks": "x" * 1000,
            "number": 12345,  # Non-string value
        }
        system, user = template.render(context, mock_counter)

        # Number should remain unchanged
        assert "12345" in user

    def test_template_with_special_characters(self) -> None:
        """Test template rendering with special characters."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Special: {text}",
        )
        context = {"text": "Hello! @#$%^&*() 你好"}
        system, user = template.render(context)
        assert "Hello! @#$%^&*() 你好" in user

    def test_template_with_newlines_in_context(self) -> None:
        """Test template rendering with newlines in context."""
        template = PromptTemplate(
            system_prompt="System",
            user_prompt_template="Code:\n{code}",
        )
        context = {"code": "def hello():\n    print('Hello')"}
        system, user = template.render(context)
        assert "def hello():" in user
        assert "print('Hello')" in user
