"""Tests for enhanced error handler."""

from __future__ import annotations

import json
from datetime import datetime

from dev_agent.errors.enhanced_error_handler import (
    EnhancedErrorHandler,
    ErrorReport,
    ErrorResponse,
    get_enhanced_error_handler,
    handle_error,
)
from dev_agent.errors.exceptions import (
    ConfigurationError,
    DevAgentError,
    ErrorCategory,
    ErrorContext,
)
from dev_agent.errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMCostLimitError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTokenLimitError,
)


class TestEnhancedErrorHandler:
    """Test enhanced error handler functionality."""

    def test_initialization(self):
        """Test handler initialization."""
        handler = EnhancedErrorHandler()
        assert handler is not None
        assert handler.logger is not None
        assert handler.error_history == []

    def test_handle_configuration_error_azure(self):
        """Test handling Azure OpenAI configuration errors."""
        handler = EnhancedErrorHandler()
        error = ConfigurationError(
            message="Azure OpenAI endpoint not configured",
            config_key="AZURE_OPENAI_ENDPOINT",
        )

        response = handler.handle_configuration_error(error)

        assert response.error_type == "ConfigurationError"
        assert "Configuration Error" in response.message
        assert len(response.suggestions) > 0
        assert any("setup" in s.lower() for s in response.suggestions)
        assert response.documentation_link is not None
        assert response.can_retry is True

    def test_handle_configuration_error_api_key(self):
        """Test handling API key configuration errors."""
        handler = EnhancedErrorHandler()
        error = ConfigurationError(
            message="API key not found",
            config_key="AZURE_OPENAI_API_KEY",
        )

        response = handler.handle_configuration_error(error)

        assert "API key" in response.message or any(
            "api key" in s.lower() for s in response.suggestions
        )
        assert any("AZURE_OPENAI_API_KEY" in s for s in response.suggestions)
        assert response.can_retry is True

    def test_handle_configuration_error_deployment(self):
        """Test handling deployment configuration errors."""
        handler = EnhancedErrorHandler()
        error = ConfigurationError(
            message="Deployment name not configured",
            config_key="AZURE_OPENAI_DEPLOYMENT_NAME",
        )

        response = handler.handle_configuration_error(error)

        assert any("deployment" in s.lower() for s in response.suggestions)
        assert response.documentation_link is not None

    def test_handle_api_error_authentication(self):
        """Test handling authentication errors."""
        handler = EnhancedErrorHandler()
        error = LLMAuthenticationError("Invalid API key")

        response = handler.handle_api_error(error)

        assert response.error_type == "LLMAuthenticationError"
        assert "API Error" in response.message
        assert len(response.suggestions) > 0
        assert any("api key" in s.lower() for s in response.suggestions)
        assert response.can_retry is False
        assert response.recovery_action is not None

    def test_handle_api_error_rate_limit(self):
        """Test handling rate limit errors."""
        handler = EnhancedErrorHandler()
        error = LLMRateLimitError("Rate limit exceeded")

        response = handler.handle_api_error(error)

        assert response.error_type == "LLMRateLimitError"
        assert any("retry" in s.lower() for s in response.suggestions)
        assert response.can_retry is True
        assert "retry" in response.recovery_action.lower()

    def test_handle_api_error_timeout(self):
        """Test handling timeout errors."""
        handler = EnhancedErrorHandler()
        error = LLMTimeoutError("Request timed out")

        response = handler.handle_api_error(error)

        assert response.error_type == "LLMTimeoutError"
        assert any("retry" in s.lower() for s in response.suggestions)
        assert response.can_retry is True

    def test_handle_api_error_bad_request(self):
        """Test handling bad request errors."""
        handler = EnhancedErrorHandler()
        error = LLMBadRequestError("Invalid deployment name")

        response = handler.handle_api_error(error)

        assert response.error_type == "LLMBadRequestError"
        assert any("deployment" in s.lower() for s in response.suggestions)
        assert response.can_retry is False

    def test_handle_api_error_token_limit(self):
        """Test handling token limit errors."""
        handler = EnhancedErrorHandler()
        error = LLMTokenLimitError("Token limit exceeded")

        response = handler.handle_api_error(error)

        assert response.error_type == "LLMTokenLimitError"
        assert any("context" in s.lower() or "reduce" in s.lower() for s in response.suggestions)
        assert response.can_retry is True

    def test_handle_api_error_cost_limit(self):
        """Test handling cost limit errors."""
        handler = EnhancedErrorHandler()
        error = LLMCostLimitError("Cost limit exceeded")

        response = handler.handle_api_error(error)

        assert response.error_type == "LLMCostLimitError"
        assert any("budget" in s.lower() for s in response.suggestions)
        assert response.can_retry is False

    def test_handle_api_error_generic(self):
        """Test handling generic API errors."""
        handler = EnhancedErrorHandler()
        error = LLMAPIError("Service unavailable")

        response = handler.handle_api_error(error)

        assert response.error_type == "LLMAPIError"
        assert any("status" in s.lower() for s in response.suggestions)
        assert response.can_retry is True

    def test_handle_workflow_error_indexing(self):
        """Test handling indexing workflow errors."""
        handler = EnhancedErrorHandler()
        error = DevAgentError(
            message="Indexing failed for project due to parsing errors",
            category=ErrorCategory.INDEXING,
            context=ErrorContext(operation="indexing", phase="indexing"),
        )

        response = handler.handle_workflow_error(error)

        assert "Workflow Error" in response.message
        assert any("indexing" in s.lower() or "project" in s.lower() for s in response.suggestions)
        assert response.can_retry is True

    def test_handle_workflow_error_specification(self):
        """Test handling specification workflow errors."""
        handler = EnhancedErrorHandler()
        error = DevAgentError(
            message="Specification generation failed due to missing context",
            category=ErrorCategory.IMPLEMENTATION,
            context=ErrorContext(operation="specification", phase="specification"),
        )

        response = handler.handle_workflow_error(error)

        assert any("specification" in s.lower() or "spec" in s.lower() or "indexing" in s.lower() for s in response.suggestions)
        assert response.documentation_link is not None

    def test_handle_workflow_error_design(self):
        """Test handling design workflow errors."""
        handler = EnhancedErrorHandler()
        error = DevAgentError(
            message="Design generation failed",
            category=ErrorCategory.IMPLEMENTATION,
            context=ErrorContext(operation="design", phase="design"),
        )

        response = handler.handle_workflow_error(error)

        assert any("design" in s.lower() for s in response.suggestions)

    def test_handle_workflow_error_implementation(self):
        """Test handling implementation workflow errors."""
        handler = EnhancedErrorHandler()
        error = DevAgentError(
            message="Task generation failed",
            category=ErrorCategory.IMPLEMENTATION,
            context=ErrorContext(operation="implementation", phase="implementation"),
        )

        response = handler.handle_workflow_error(error)

        assert any("task" in s.lower() or "implementation" in s.lower() for s in response.suggestions)

    def test_handle_workflow_error_state(self):
        """Test handling state workflow errors."""
        handler = EnhancedErrorHandler()
        error = DevAgentError(
            message="State corruption detected in project files",
            category=ErrorCategory.STATE,
            context=ErrorContext(operation="state_load", phase="any"),
        )

        response = handler.handle_workflow_error(error)

        assert any("state" in s.lower() for s in response.suggestions)
        assert any("backup" in s.lower() or "reinitializ" in s.lower() for s in response.suggestions)

    def test_suggest_solutions_configuration(self):
        """Test solution suggestions for configuration errors."""
        handler = EnhancedErrorHandler()
        error = Exception("Configuration variable not set")

        suggestions = handler.suggest_solutions(error)

        assert len(suggestions) > 0
        assert any("setup" in s.lower() or "config" in s.lower() for s in suggestions)

    def test_suggest_solutions_authentication(self):
        """Test solution suggestions for authentication errors."""
        handler = EnhancedErrorHandler()
        error = Exception("Authentication failed with invalid key")

        suggestions = handler.suggest_solutions(error)

        assert any("key" in s.lower() or "auth" in s.lower() for s in suggestions)

    def test_suggest_solutions_network(self):
        """Test solution suggestions for network errors."""
        handler = EnhancedErrorHandler()
        error = Exception("Network connection timeout")

        suggestions = handler.suggest_solutions(error)

        assert any("network" in s.lower() or "connection" in s.lower() for s in suggestions)

    def test_suggest_solutions_file_system(self):
        """Test solution suggestions for file system errors."""
        handler = EnhancedErrorHandler()
        error = Exception("File not found or permission denied")

        suggestions = handler.suggest_solutions(error)

        assert any("file" in s.lower() or "permission" in s.lower() for s in suggestions)

    def test_suggest_solutions_rate_limit(self):
        """Test solution suggestions for rate limit errors."""
        handler = EnhancedErrorHandler()
        error = Exception("Rate limit exceeded")

        suggestions = handler.suggest_solutions(error)

        assert any("rate" in s.lower() or "wait" in s.lower() for s in suggestions)

    def test_suggest_solutions_token_limit(self):
        """Test solution suggestions for token limit errors."""
        handler = EnhancedErrorHandler()
        error = Exception("Token context length exceeded")

        suggestions = handler.suggest_solutions(error)

        assert any("token" in s.lower() or "context" in s.lower() for s in suggestions)

    def test_suggest_solutions_memory(self):
        """Test solution suggestions for memory errors."""
        handler = EnhancedErrorHandler()
        error = Exception("Memory allocation failed")

        suggestions = handler.suggest_solutions(error)

        assert any("memory" in s.lower() for s in suggestions)

    def test_suggest_solutions_generic(self):
        """Test solution suggestions for generic errors."""
        handler = EnhancedErrorHandler()
        error = Exception("Something went wrong")

        suggestions = handler.suggest_solutions(error)

        assert len(suggestions) > 0
        assert any("validate" in s.lower() or "check" in s.lower() for s in suggestions)

    def test_create_error_report(self):
        """Test error report creation."""
        handler = EnhancedErrorHandler()
        error = Exception("Test error")
        context = {"operation": "test", "phase": "testing"}

        report = handler.create_error_report(
            error, context=context, recovery_attempted=True, recovery_successful=True
        )

        assert isinstance(report, ErrorReport)
        assert report.error_type == "Exception"
        assert report.error_message == "Test error"
        assert report.context == context
        assert report.recovery_attempted is True
        assert report.recovery_successful is True
        assert len(report.suggestions) > 0
        assert len(handler.error_history) == 1

    def test_save_error_report(self, tmp_path):
        """Test saving error report to file."""
        handler = EnhancedErrorHandler()
        error = Exception("Test error")
        report = handler.create_error_report(error)

        output_path = tmp_path / "error_report.json"
        handler.save_error_report(report, output_path)

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert data["error_type"] == "Exception"
        assert data["error_message"] == "Test error"
        assert "timestamp" in data
        assert "suggestions" in data

    def test_get_error_history(self):
        """Test getting error history."""
        handler = EnhancedErrorHandler()

        # Create multiple errors
        for i in range(3):
            error = Exception(f"Error {i}")
            handler.create_error_report(error)

        history = handler.get_error_history()
        assert len(history) == 3
        assert all(isinstance(r, ErrorReport) for r in history)

    def test_clear_error_history(self):
        """Test clearing error history."""
        handler = EnhancedErrorHandler()

        # Create some errors
        for i in range(3):
            error = Exception(f"Error {i}")
            handler.create_error_report(error)

        assert len(handler.error_history) == 3

        handler.clear_error_history()
        assert len(handler.error_history) == 0

    def test_format_error_response(self):
        """Test formatting error response for display."""
        handler = EnhancedErrorHandler()
        response = ErrorResponse(
            error_type="TestError",
            message="Test error message",
            suggestions=["Solution 1", "Solution 2", "Solution 3"],
            documentation_link="https://docs.example.com",
            can_retry=True,
            recovery_action="Retry the operation",
        )

        formatted = handler.format_error_response(response)

        assert "Test error message" in formatted
        assert "Solution 1" in formatted
        assert "Solution 2" in formatted
        assert "Solution 3" in formatted
        assert "Retry the operation" in formatted
        assert "https://docs.example.com" in formatted

    def test_global_handler(self):
        """Test global handler instance."""
        handler1 = get_enhanced_error_handler()
        handler2 = get_enhanced_error_handler()

        assert handler1 is handler2  # Same instance

    def test_handle_error_function_configuration(self):
        """Test global handle_error function with configuration error."""
        error = ConfigurationError(
            message="Test configuration error",
            config_key="TEST_KEY",
        )

        response = handle_error(error)

        assert isinstance(response, ErrorResponse)
        assert response.error_type == "ConfigurationError"
        assert len(response.suggestions) > 0

    def test_handle_error_function_llm(self):
        """Test global handle_error function with LLM error."""
        error = LLMAuthenticationError("Test auth error")

        response = handle_error(error)

        assert isinstance(response, ErrorResponse)
        assert response.error_type == "LLMAuthenticationError"
        assert len(response.suggestions) > 0

    def test_handle_error_function_workflow(self):
        """Test global handle_error function with workflow error."""
        error = DevAgentError(
            message="Test workflow error",
            category=ErrorCategory.INDEXING,
        )

        response = handle_error(error)

        assert isinstance(response, ErrorResponse)
        assert len(response.suggestions) > 0

    def test_handle_error_function_generic(self):
        """Test global handle_error function with generic error."""
        error = ValueError("Test generic error")

        response = handle_error(error)

        assert isinstance(response, ErrorResponse)
        assert response.error_type == "ValueError"
        assert len(response.suggestions) > 0

    def test_error_response_dataclass(self):
        """Test ErrorResponse dataclass."""
        response = ErrorResponse(
            error_type="TestError",
            message="Test message",
            suggestions=["Suggestion 1"],
            documentation_link="https://docs.example.com",
            can_retry=True,
            recovery_action="Test action",
            technical_details={"key": "value"},
        )

        assert response.error_type == "TestError"
        assert response.message == "Test message"
        assert response.suggestions == ["Suggestion 1"]
        assert response.documentation_link == "https://docs.example.com"
        assert response.can_retry is True
        assert response.recovery_action == "Test action"
        assert response.technical_details == {"key": "value"}

    def test_error_report_dataclass(self):
        """Test ErrorReport dataclass."""
        now = datetime.now()
        report = ErrorReport(
            timestamp=now,
            error_type="TestError",
            error_message="Test message",
            traceback="Test traceback",
            context={"key": "value"},
            suggestions=["Suggestion 1"],
            recovery_attempted=True,
            recovery_successful=True,
        )

        assert report.timestamp == now
        assert report.error_type == "TestError"
        assert report.error_message == "Test message"
        assert report.traceback == "Test traceback"
        assert report.context == {"key": "value"}
        assert report.suggestions == ["Suggestion 1"]
        assert report.recovery_attempted is True
        assert report.recovery_successful is True
