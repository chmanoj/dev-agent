"""Enhanced error handler with user-friendly messages and recovery guidance.

This module provides comprehensive error handling with:
- User-friendly error messages
- Actionable solution suggestions
- Automatic recovery strategies
- Detailed error reports for debugging
"""

from __future__ import annotations

import json
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .exceptions import (
    ConfigurationError,
    DevAgentError,
    ServiceError,
)
from .llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMCostLimitError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTokenLimitError,
)


@dataclass
class ErrorResponse:
    """Structured error response with user-friendly information."""

    error_type: str
    message: str
    suggestions: list[str]
    documentation_link: str | None = None
    can_retry: bool = False
    recovery_action: str | None = None
    technical_details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorReport:
    """Detailed error report for debugging."""

    timestamp: datetime
    error_type: str
    error_message: str
    traceback: str
    context: dict[str, Any]
    suggestions: list[str]
    recovery_attempted: bool
    recovery_successful: bool | None = None


class EnhancedErrorHandler:
    """Enhanced error handler with user-friendly messages and recovery."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize enhanced error handler.

        Args:
            logger: Optional logger instance. If not provided, creates default logger.
        """
        self.logger = logger or self._setup_logger()
        self.error_history: list[ErrorReport] = []

    def _setup_logger(self) -> logging.Logger:
        """Set up default logger."""
        logger = logging.getLogger("dev_agent.enhanced_errors")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def handle_configuration_error(
        self, error: ConfigurationError | Exception
    ) -> ErrorResponse:
        """Handle configuration errors with setup guidance.

        Args:
            error: Configuration error to handle

        Returns:
            ErrorResponse with user-friendly message and setup guidance
        """
        self.logger.error(f"Configuration error: {error}")

        # Determine specific configuration issue
        error_msg = str(error)
        suggestions = []
        doc_link = None
        can_retry = True

        if "azure" in error_msg.lower() or "openai" in error_msg.lower():
            suggestions = [
                "Run 'dev-agent setup' to configure Azure OpenAI interactively",
                "Set AZURE_OPENAI_ENDPOINT environment variable to your Azure OpenAI endpoint",
                "Set AZURE_OPENAI_API_KEY environment variable with your API key",
                "Set AZURE_OPENAI_DEPLOYMENT_NAME for your GPT-4 deployment",
                "Set AZURE_OPENAI_EMBEDDING_DEPLOYMENT for your embedding deployment",
                "Verify your Azure OpenAI resource is active in the Azure portal",
            ]
            doc_link = "https://docs.dev-agent.io/configuration/azure-openai"

        elif "api" in error_msg.lower() and "key" in error_msg.lower():
            suggestions = [
                "Check that AZURE_OPENAI_API_KEY is set in your environment",
                "Verify the API key is valid and not expired",
                "Ensure the API key has the necessary permissions",
                "Run 'dev-agent validate' to test your configuration",
            ]
            doc_link = "https://docs.dev-agent.io/configuration/azure-openai"

        elif "endpoint" in error_msg.lower():
            suggestions = [
                "Verify AZURE_OPENAI_ENDPOINT is set correctly",
                "Ensure the endpoint URL includes 'https://' and ends with '.openai.azure.com/'",
                "Check that the resource name in the endpoint matches your Azure resource",
                "Run 'dev-agent validate' to test connectivity",
            ]
            doc_link = "https://docs.dev-agent.io/configuration/azure-openai"

        elif "deployment" in error_msg.lower():
            suggestions = [
                "Check that AZURE_OPENAI_DEPLOYMENT_NAME matches your GPT-4 deployment",
                "Verify AZURE_OPENAI_EMBEDDING_DEPLOYMENT matches your embedding deployment",
                "Ensure deployments are created in your Azure OpenAI resource",
                "Check deployment names in the Azure portal under your OpenAI resource",
            ]
            doc_link = "https://docs.dev-agent.io/configuration/azure-openai"

        else:
            suggestions = [
                "Run 'dev-agent setup' to configure the system interactively",
                "Check your configuration file at ~/.dev_agent_config",
                "Review environment variables with 'dev-agent validate'",
                "Consult the documentation for configuration requirements",
            ]
            doc_link = "https://docs.dev-agent.io/getting-started/first-time-setup"

        return ErrorResponse(
            error_type="ConfigurationError",
            message=self._format_user_message(
                "Configuration Error",
                str(error),
                "Your dev-agent configuration is incomplete or invalid.",
            ),
            suggestions=suggestions,
            documentation_link=doc_link,
            can_retry=can_retry,
            recovery_action="Run 'dev-agent setup' to configure interactively",
            technical_details={"error": str(error), "type": type(error).__name__},
        )

    def handle_api_error(self, error: LLMError | Exception) -> ErrorResponse:
        """Handle API errors with retry suggestions.

        Args:
            error: API error to handle

        Returns:
            ErrorResponse with retry guidance and troubleshooting steps
        """
        self.logger.error(f"API error: {error}")

        suggestions = []
        doc_link = "https://docs.dev-agent.io/troubleshooting/api-errors"
        can_retry = True
        recovery_action = None

        # Handle specific LLM error types
        if isinstance(error, LLMAuthenticationError):
            suggestions = [
                "Verify your AZURE_OPENAI_API_KEY is correct and not expired",
                "Check that the API key has the necessary permissions",
                "Ensure your Azure OpenAI resource is active",
                "Try regenerating your API key in the Azure portal",
                "Run 'dev-agent validate' to test authentication",
            ]
            recovery_action = "Update your API key and run 'dev-agent validate'"
            can_retry = False

        elif isinstance(error, LLMRateLimitError):
            suggestions = [
                "The system will automatically retry with exponential backoff",
                "Wait a few moments before retrying manually",
                "Consider reducing concurrent operations",
                "Check your rate limit quota in the Azure portal",
                "Consider upgrading your Azure OpenAI tier for higher limits",
            ]
            recovery_action = "Wait and retry automatically (already in progress)"
            can_retry = True

        elif isinstance(error, LLMTimeoutError):
            suggestions = [
                "The system will automatically retry the request",
                "Check your network connection",
                "Verify Azure OpenAI service status at status.azure.com",
                "Consider increasing timeout settings if this persists",
                "Try reducing the size of your request",
            ]
            recovery_action = "Retry with increased timeout"
            can_retry = True

        elif isinstance(error, LLMBadRequestError):
            suggestions = [
                "Check that your deployment names match your Azure configuration",
                "Verify model parameters are within allowed ranges",
                "Ensure your prompt is properly formatted",
                "Review the API documentation for parameter requirements",
                "Run 'dev-agent validate' to check configuration",
            ]
            recovery_action = "Review and correct request parameters"
            can_retry = False

        elif isinstance(error, LLMTokenLimitError):
            suggestions = [
                "The system will automatically reduce context size and retry",
                "Consider using a model with a larger context window",
                "Reduce the amount of code being analyzed at once",
                "Use more specific queries to reduce context requirements",
            ]
            recovery_action = "Reduce context size and retry"
            can_retry = True

        elif isinstance(error, LLMCostLimitError):
            suggestions = [
                "Review your budget limits in the configuration",
                "Reduce the scope of the operation",
                "Use caching to avoid redundant API calls",
                "Consider using a less expensive model for simpler tasks",
            ]
            recovery_action = "Adjust budget limits or reduce operation scope"
            can_retry = False

        elif isinstance(error, LLMAPIError):
            suggestions = [
                "Check Azure OpenAI service status at status.azure.com",
                "The system will automatically retry transient errors",
                "Verify your network connection",
                "Review error details in the logs",
                "Contact Azure support if the issue persists",
            ]
            recovery_action = "Retry automatically (transient errors)"
            can_retry = True

        else:
            # Generic API error
            suggestions = [
                "Check your network connection",
                "Verify Azure OpenAI service is accessible",
                "Review your API configuration with 'dev-agent validate'",
                "Check Azure service status at status.azure.com",
                "Review error logs for more details",
            ]
            recovery_action = "Check configuration and retry"
            can_retry = True

        return ErrorResponse(
            error_type=type(error).__name__,
            message=self._format_user_message(
                "API Error",
                str(error),
                "An error occurred while communicating with Azure OpenAI.",
            ),
            suggestions=suggestions,
            documentation_link=doc_link,
            can_retry=can_retry,
            recovery_action=recovery_action,
            technical_details={"error": str(error), "type": type(error).__name__},
        )

    def handle_workflow_error(self, error: DevAgentError | Exception) -> ErrorResponse:
        """Handle workflow errors with recovery options.

        Args:
            error: Workflow error to handle

        Returns:
            ErrorResponse with recovery options and next steps
        """
        self.logger.error(f"Workflow error: {error}")

        error_msg = str(error)
        suggestions = []
        doc_link = "https://docs.dev-agent.io/user-guides/four-phase-workflow"
        can_retry = True
        recovery_action = None

        # Determine workflow phase and provide specific guidance
        if "indexing" in error_msg.lower():
            suggestions = [
                "Check that the project directory exists and is accessible",
                "Verify you have read permissions for all project files",
                "Ensure there are Python files to index in the project",
                "Try running 'dev-agent init' again with a clean state",
                "Check disk space and memory availability",
            ]
            recovery_action = "Clean state and retry indexing"
            doc_link = "https://docs.dev-agent.io/troubleshooting/indexing-errors"

        elif "specification" in error_msg.lower():
            suggestions = [
                "Ensure indexing completed successfully before generating specs",
                "Check that the codebase was properly analyzed",
                "Verify Azure OpenAI is accessible and configured",
                "Try regenerating with more specific requirements",
                "Review the indexed code patterns for completeness",
            ]
            recovery_action = "Verify indexing and retry specification generation"
            doc_link = "https://docs.dev-agent.io/troubleshooting/specification-errors"

        elif "design" in error_msg.lower():
            suggestions = [
                "Ensure specification phase completed successfully",
                "Verify the specification document is complete and valid",
                "Check that Azure OpenAI is accessible",
                "Try regenerating with clearer design requirements",
                "Review the specification for any ambiguities",
            ]
            recovery_action = "Review specification and retry design generation"
            doc_link = "https://docs.dev-agent.io/troubleshooting/design-errors"

        elif "implementation" in error_msg.lower() or "task" in error_msg.lower():
            suggestions = [
                "Ensure design phase completed successfully",
                "Verify the design document is complete and valid",
                "Check that all dependencies are properly configured",
                "Try regenerating tasks with more specific requirements",
                "Review the design for implementation clarity",
            ]
            recovery_action = "Review design and retry task generation"
            doc_link = "https://docs.dev-agent.io/troubleshooting/implementation-errors"

        elif "state" in error_msg.lower():
            suggestions = [
                "Check that .dev_agent directory exists and is writable",
                "Verify state.json file is not corrupted",
                "Try backing up and reinitializing the project",
                "Ensure you have write permissions to the project directory",
                "Check disk space availability",
            ]
            recovery_action = "Backup state and reinitialize if necessary"
            doc_link = "https://docs.dev-agent.io/troubleshooting/state-errors"

        else:
            suggestions = [
                "Check the current workflow phase with 'dev-agent status'",
                "Review error logs for more details",
                "Try resuming the workflow with 'dev-agent resume'",
                "Verify all prerequisites are met for the current phase",
                "Consider restarting from a clean state if issues persist",
            ]
            recovery_action = "Check status and resume workflow"

        return ErrorResponse(
            error_type=type(error).__name__,
            message=self._format_user_message(
                "Workflow Error",
                str(error),
                "An error occurred during the development workflow.",
            ),
            suggestions=suggestions,
            documentation_link=doc_link,
            can_retry=can_retry,
            recovery_action=recovery_action,
            technical_details={
                "error": str(error),
                "type": type(error).__name__,
                "category": getattr(error, "category", None),
            },
        )

    def suggest_solutions(self, error: Exception) -> list[str]:
        """Suggest solutions based on error type and message.

        Args:
            error: Exception to analyze

        Returns:
            List of actionable solution suggestions
        """
        error_msg = str(error).lower()
        suggestions = []

        # Configuration-related errors
        if any(
            keyword in error_msg
            for keyword in ["config", "environment", "variable", "setting"]
        ):
            suggestions.extend(
                [
                    "Run 'dev-agent setup' to configure interactively",
                    "Check environment variables are set correctly",
                    "Verify configuration file at ~/.dev_agent_config",
                    "Run 'dev-agent validate' to test configuration",
                ]
            )

        # Authentication/API key errors
        if any(keyword in error_msg for keyword in ["auth", "key", "credential"]):
            suggestions.extend(
                [
                    "Verify AZURE_OPENAI_API_KEY is set and valid",
                    "Check API key permissions in Azure portal",
                    "Ensure API key has not expired",
                    "Try regenerating the API key",
                ]
            )

        # Network/connectivity errors
        if any(
            keyword in error_msg
            for keyword in ["network", "connection", "timeout", "unreachable"]
        ):
            suggestions.extend(
                [
                    "Check your internet connection",
                    "Verify Azure OpenAI endpoint is accessible",
                    "Check firewall and proxy settings",
                    "Verify Azure service status at status.azure.com",
                ]
            )

        # File system errors
        if any(
            keyword in error_msg
            for keyword in ["file", "directory", "path", "permission"]
        ):
            suggestions.extend(
                [
                    "Check that the file or directory exists",
                    "Verify you have read/write permissions",
                    "Ensure the path is correct and accessible",
                    "Check disk space availability",
                ]
            )

        # Rate limiting errors
        if any(keyword in error_msg for keyword in ["rate", "limit", "quota"]):
            suggestions.extend(
                [
                    "Wait a few moments before retrying",
                    "System will automatically retry with backoff",
                    "Check rate limits in Azure portal",
                    "Consider upgrading your Azure tier",
                ]
            )

        # Token/context errors
        if any(keyword in error_msg for keyword in ["token", "context", "length"]):
            suggestions.extend(
                [
                    "Reduce the size of your input",
                    "Use more specific queries",
                    "Consider using a model with larger context",
                    "System will automatically optimize context",
                ]
            )

        # Memory/performance errors
        if any(keyword in error_msg for keyword in ["memory", "performance", "slow"]):
            suggestions.extend(
                [
                    "Close other applications to free memory",
                    "Process smaller batches of files",
                    "Enable caching to improve performance",
                    "Check system resource availability",
                ]
            )

        # If no specific suggestions, provide general ones
        if not suggestions:
            suggestions = [
                "Check the error message for specific details",
                "Review the documentation for troubleshooting",
                "Run 'dev-agent validate' to check system health",
                "Check logs for more detailed error information",
                "Try the operation again after addressing any issues",
            ]

        return suggestions

    def create_error_report(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        recovery_attempted: bool = False,
        recovery_successful: bool | None = None,
    ) -> ErrorReport:
        """Create detailed error report for debugging.

        Args:
            error: Exception that occurred
            context: Additional context information
            recovery_attempted: Whether recovery was attempted
            recovery_successful: Whether recovery was successful (if attempted)

        Returns:
            ErrorReport with comprehensive debugging information
        """
        # Get suggestions for this error
        suggestions = self.suggest_solutions(error)

        # Create error report
        report = ErrorReport(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
            context=context or {},
            suggestions=suggestions,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful,
        )

        # Add to history
        self.error_history.append(report)

        # Log the report
        self.logger.error(
            f"Error report created: {report.error_type} - {report.error_message}"
        )

        return report

    def save_error_report(
        self, report: ErrorReport, output_path: Path | str
    ) -> None:
        """Save error report to file for debugging.

        Args:
            report: ErrorReport to save
            output_path: Path to save the report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            "timestamp": report.timestamp.isoformat(),
            "error_type": report.error_type,
            "error_message": report.error_message,
            "traceback": report.traceback,
            "context": report.context,
            "suggestions": report.suggestions,
            "recovery_attempted": report.recovery_attempted,
            "recovery_successful": report.recovery_successful,
        }

        output_path.write_text(json.dumps(report_data, indent=2))
        self.logger.info(f"Error report saved to {output_path}")

    def get_error_history(self) -> list[ErrorReport]:
        """Get error history.

        Returns:
            List of error reports
        """
        return self.error_history

    def clear_error_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()
        self.logger.info("Error history cleared")

    def _format_user_message(
        self, title: str, error_msg: str, description: str
    ) -> str:
        """Format user-friendly error message.

        Args:
            title: Error title
            error_msg: Technical error message
            description: User-friendly description

        Returns:
            Formatted error message
        """
        return f"""❌ {title}

{description}

Error details: {error_msg}

See suggestions below for how to resolve this issue."""

    def format_error_response(self, response: ErrorResponse) -> str:
        """Format error response for display.

        Args:
            response: ErrorResponse to format

        Returns:
            Formatted error message with suggestions
        """
        lines = [
            response.message,
            "",
            "Possible solutions:",
        ]

        for i, suggestion in enumerate(response.suggestions, 1):
            lines.append(f"{i}. {suggestion}")

        if response.recovery_action:
            lines.extend(
                [
                    "",
                    f"Recommended action: {response.recovery_action}",
                ]
            )

        if response.documentation_link:
            lines.extend(
                [
                    "",
                    f"For more help: {response.documentation_link}",
                ]
            )

        return "\n".join(lines)


# Global instance for convenience
_global_handler: EnhancedErrorHandler | None = None


def get_enhanced_error_handler() -> EnhancedErrorHandler:
    """Get global enhanced error handler instance.

    Returns:
        Global EnhancedErrorHandler instance
    """
    global _global_handler  # noqa: PLW0603
    if _global_handler is None:
        _global_handler = EnhancedErrorHandler()
    return _global_handler


def handle_error(error: Exception) -> ErrorResponse:
    """Handle error using global handler.

    Args:
        error: Exception to handle

    Returns:
        ErrorResponse with user-friendly information
    """
    handler = get_enhanced_error_handler()

    # Route to appropriate handler based on error type
    if isinstance(error, ConfigurationError):
        return handler.handle_configuration_error(error)
    elif isinstance(error, LLMError | ServiceError):
        return handler.handle_api_error(error)
    elif isinstance(error, DevAgentError):
        return handler.handle_workflow_error(error)
    else:
        # Generic error handling
        return ErrorResponse(
            error_type=type(error).__name__,
            message=handler._format_user_message(
                "Error",
                str(error),
                "An unexpected error occurred.",
            ),
            suggestions=handler.suggest_solutions(error),
            can_retry=True,
            technical_details={"error": str(error), "type": type(error).__name__},
        )
