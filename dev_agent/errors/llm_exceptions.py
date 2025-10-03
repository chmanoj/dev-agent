"""Exception classes for LLM operations.

This module defines a hierarchy of exceptions for handling errors that occur
during LLM API interactions, providing clear error messages and resolution
guidance.
"""

from __future__ import annotations


class LLMError(Exception):
    """Base exception for all LLM-related errors.
    
    This is the parent class for all LLM exceptions, allowing code to catch
    all LLM-related errors with a single except clause if needed.
    
    Attributes:
        message: Human-readable error message
        resolution: Optional guidance on how to resolve the error
    """

    def __init__(self, message: str, resolution: str | None = None) -> None:
        """Initialize LLM error.
        
        Args:
            message: Human-readable error message
            resolution: Optional guidance on how to resolve the error
        """
        self.message = message
        self.resolution = resolution
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with optional resolution guidance."""
        if self.resolution:
            return f"{self.message}\n\nResolution: {self.resolution}"
        return self.message


class LLMAuthenticationError(LLMError):
    """Authentication failed with the LLM provider.
    
    This error occurs when API credentials are invalid, expired, or missing.
    
    Example:
        ```python
        raise LLMAuthenticationError(
            "Failed to authenticate with Azure OpenAI",
            "Check that AZURE_OPENAI_API_KEY is set correctly and the key is valid"
        )
        ```
    """

    def __init__(
        self,
        message: str = "Authentication failed with LLM provider",
        resolution: str | None = None,
    ) -> None:
        """Initialize authentication error.
        
        Args:
            message: Human-readable error message
            resolution: Optional guidance on how to resolve the error. If not
                provided, default resolution guidance is used.
        """
        if resolution is None:
            resolution = (
                "1. Verify that your API key is set correctly in environment variables\n"
                "2. Check that the API key has not expired\n"
                "3. Ensure the API key has the necessary permissions\n"
                "4. For Azure OpenAI, verify the endpoint URL is correct"
            )
        super().__init__(message, resolution)


class LLMRateLimitError(LLMError):
    """Rate limit exceeded for the LLM provider.
    
    This error occurs when too many requests are made in a short time period.
    The client should implement retry logic with exponential backoff.
    
    Example:
        ```python
        raise LLMRateLimitError(
            "Azure OpenAI rate limit exceeded",
            "The request will be retried automatically with exponential backoff"
        )
        ```
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        resolution: str | None = None,
    ) -> None:
        """Initialize rate limit error.
        
        Args:
            message: Human-readable error message
            resolution: Optional guidance on how to resolve the error. If not
                provided, default resolution guidance is used.
        """
        if resolution is None:
            resolution = (
                "1. The system will automatically retry with exponential backoff\n"
                "2. Consider reducing the number of concurrent requests\n"
                "3. Check your rate limit quota in the Azure portal\n"
                "4. Consider upgrading your Azure OpenAI tier for higher limits"
            )
        super().__init__(message, resolution)


class LLMTimeoutError(LLMError):
    """Request to the LLM provider timed out.
    
    This error occurs when a request takes longer than the configured timeout
    period. This may be due to network issues or high load on the provider.
    
    Example:
        ```python
        raise LLMTimeoutError(
            "Request to Azure OpenAI timed out after 60 seconds",
            "The request will be retried automatically"
        )
        ```
    """

    def __init__(
        self,
        message: str = "Request timed out",
        resolution: str | None = None,
    ) -> None:
        """Initialize timeout error.
        
        Args:
            message: Human-readable error message
            resolution: Optional guidance on how to resolve the error. If not
                provided, default resolution guidance is used.
        """
        if resolution is None:
            resolution = (
                "1. The system will automatically retry the request\n"
                "2. Check your network connection\n"
                "3. Consider increasing the timeout setting if this persists\n"
                "4. Check Azure OpenAI service status at status.azure.com"
            )
        super().__init__(message, resolution)


class LLMBadRequestError(LLMError):
    """Invalid request parameters sent to the LLM provider.
    
    This error occurs when the request contains invalid parameters, such as
    invalid model names, token limits, or prompt formats.
    
    Example:
        ```python
        raise LLMBadRequestError(
            "Invalid deployment name: gpt-5",
            "Check that the deployment name matches your Azure OpenAI resource"
        )
        ```
    """

    def __init__(
        self,
        message: str = "Invalid request parameters",
        resolution: str | None = None,
    ) -> None:
        """Initialize bad request error.
        
        Args:
            message: Human-readable error message
            resolution: Optional guidance on how to resolve the error. If not
                provided, default resolution guidance is used.
        """
        if resolution is None:
            resolution = (
                "1. Check that all request parameters are valid\n"
                "2. Verify model/deployment names match your configuration\n"
                "3. Ensure token limits are within allowed ranges\n"
                "4. Review the API documentation for parameter requirements"
            )
        super().__init__(message, resolution)


class LLMAPIError(LLMError):
    """General API error from the LLM provider.
    
    This error is used for API errors that don't fit into more specific
    categories, such as server errors or unexpected responses.
    
    Example:
        ```python
        raise LLMAPIError(
            "Azure OpenAI service returned 500 Internal Server Error",
            "The service may be experiencing issues. Check status.azure.com"
        )
        ```
    """

    def __init__(
        self,
        message: str = "LLM API error occurred",
        resolution: str | None = None,
    ) -> None:
        """Initialize API error.
        
        Args:
            message: Human-readable error message
            resolution: Optional guidance on how to resolve the error. If not
                provided, default resolution guidance is used.
        """
        if resolution is None:
            resolution = (
                "1. Check the Azure OpenAI service status at status.azure.com\n"
                "2. Review the error details in the logs\n"
                "3. The system will automatically retry transient errors\n"
                "4. Contact Azure support if the issue persists"
            )
        super().__init__(message, resolution)


class LLMTokenLimitError(LLMError):
    """Token limit exceeded for the request.
    
    This error occurs when the prompt or completion would exceed the model's
    context window or configured token limits.
    
    Example:
        ```python
        raise LLMTokenLimitError(
            "Prompt contains 10000 tokens, exceeds GPT-4 limit of 8192",
            "Reduce the prompt size or use a model with a larger context window"
        )
        ```
    """

    def __init__(
        self,
        message: str = "Token limit exceeded",
        resolution: str | None = None,
    ) -> None:
        """Initialize token limit error.
        
        Args:
            message: Human-readable error message
            resolution: Optional guidance on how to resolve the error. If not
                provided, default resolution guidance is used.
        """
        if resolution is None:
            resolution = (
                "1. Reduce the size of your prompt or context\n"
                "2. Use intelligent truncation to keep only essential information\n"
                "3. Consider using a model with a larger context window (e.g., GPT-4-32k)\n"
                "4. Split the request into multiple smaller requests"
            )
        super().__init__(message, resolution)


class LLMCostLimitError(LLMError):
    """Cost limit exceeded for the operation.
    
    This error occurs when an operation would exceed configured budget
    thresholds or cost limits.
    
    Example:
        ```python
        raise LLMCostLimitError(
            "Operation would cost $5.00, exceeds budget limit of $2.00",
            "Increase the budget limit or reduce the scope of the operation"
        )
        ```
    """

    def __init__(
        self,
        message: str = "Cost limit exceeded",
        resolution: str | None = None,
    ) -> None:
        """Initialize cost limit error.
        
        Args:
            message: Human-readable error message
            resolution: Optional guidance on how to resolve the error. If not
                provided, default resolution guidance is used.
        """
        if resolution is None:
            resolution = (
                "1. Review and adjust your budget limits in the configuration\n"
                "2. Reduce the scope of the operation to use fewer tokens\n"
                "3. Use caching to avoid redundant API calls\n"
                "4. Consider using a less expensive model for simpler tasks"
            )
        super().__init__(message, resolution)
