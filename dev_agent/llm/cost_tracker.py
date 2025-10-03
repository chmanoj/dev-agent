"""Cost tracking for Azure OpenAI API usage.

This module provides the CostTracker class for monitoring token usage and costs
across all LLM operations. It supports per-operation tracking, per-phase aggregation,
budget threshold warnings, and comprehensive usage reporting.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from dev_agent.models.cost_tracking import CostReport, TokenUsage
from dev_agent.models.enums import LLMOperationType, PhaseType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Azure OpenAI pricing (as of 2024-02-15)
# These are example prices - update with actual Azure pricing
PRICING = {
    "gpt-4": {
        "prompt": 0.03,  # per 1K tokens
        "completion": 0.06,  # per 1K tokens
    },
    "gpt-4-32k": {
        "prompt": 0.06,
        "completion": 0.12,
    },
    "gpt-4-turbo": {
        "prompt": 0.01,
        "completion": 0.03,
    },
    "gpt-4o": {
        "prompt": 0.005,
        "completion": 0.015,
    },
    "gpt-3.5-turbo": {
        "prompt": 0.0015,
        "completion": 0.002,
    },
    "text-embedding-ada-002": {
        "embedding": 0.0001,  # per 1K tokens
    },
}


class CostTracker:
    """Track Azure OpenAI usage and costs across operations.
    
    This class provides comprehensive tracking of token usage and costs for all
    Azure OpenAI operations. It supports per-operation recording, per-phase
    aggregation, budget threshold warnings, and detailed usage reporting.
    
    The tracker maintains a session-level view of all operations and can generate
    reports broken down by workflow phase and operation type.
    
    Attributes:
        current_phase: Current workflow phase being tracked
        budget_threshold: Budget threshold in USD for warnings (None = no limit)
        budget_limit: Hard budget limit in USD (None = no limit)
        _operations: List of all recorded TokenUsage records
        _start_time: When tracking started
        
    Example:
        ```python
        tracker = CostTracker(
            current_phase=PhaseType.SPECIFICATION,
            budget_threshold=10.0,
            budget_limit=50.0,
        )
        
        # Record a completion operation
        tracker.record_completion(
            prompt_tokens=150,
            completion_tokens=300,
            model="gpt-4",
        )
        
        # Check if approaching budget
        if tracker.check_budget_threshold():
            print("Warning: Approaching budget limit!")
        
        # Get usage report
        report = tracker.get_report()
        print(f"Total cost: ${report.total_cost:.2f}")
        ```
    """

    def __init__(
        self,
        current_phase: PhaseType = PhaseType.INDEXING,
        budget_threshold: float | None = None,
        budget_limit: float | None = None,
    ) -> None:
        """Initialize the cost tracker.
        
        Args:
            current_phase: Initial workflow phase
            budget_threshold: Budget threshold for warnings in USD (None = no threshold)
            budget_limit: Hard budget limit in USD (None = no limit)
            
        Raises:
            ValueError: If budget_threshold or budget_limit is negative
        """
        if budget_threshold is not None and budget_threshold < 0:
            raise ValueError("budget_threshold must be non-negative")
        if budget_limit is not None and budget_limit < 0:
            raise ValueError("budget_limit must be non-negative")
        if (
            budget_threshold is not None
            and budget_limit is not None
            and budget_threshold > budget_limit
        ):
            raise ValueError("budget_threshold must be <= budget_limit")
        
        self.current_phase = current_phase
        self.budget_threshold = budget_threshold
        self.budget_limit = budget_limit
        self._operations: list[TokenUsage] = []
        self._start_time = datetime.now()
        
        logger.info(
            f"CostTracker initialized for phase {current_phase.value}, "
            f"threshold=${budget_threshold}, limit=${budget_limit}"
        )

    def set_phase(self, phase: PhaseType) -> None:
        """Set the current workflow phase.
        
        All subsequent operations will be recorded under this phase.
        
        Args:
            phase: New workflow phase
        """
        logger.info(f"Switching phase from {self.current_phase.value} to {phase.value}")
        self.current_phase = phase

    def record_completion(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4",
    ) -> float:
        """Record a completion operation and return estimated cost.
        
        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            model: Model name used (e.g., "gpt-4", "gpt-4-turbo")
            
        Returns:
            Estimated cost in USD for this operation
            
        Raises:
            ValueError: If token counts are negative
        """
        if prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=model,
        )
        
        usage = TokenUsage(
            operation_type=LLMOperationType.COMPLETION,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            timestamp=datetime.now(),
            phase=self.current_phase,
            model=model,
        )
        
        self._operations.append(usage)
        
        logger.debug(
            f"Recorded completion: {prompt_tokens} prompt + {completion_tokens} "
            f"completion tokens, cost=${cost:.4f}, model={model}"
        )
        
        # Check budget after recording
        self.check_budget_threshold()
        
        return cost

    def record_streaming(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4",
    ) -> float:
        """Record a streaming completion operation.
        
        Streaming operations are tracked separately from regular completions
        for reporting purposes, but use the same pricing.
        
        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens streamed
            model: Model name used
            
        Returns:
            Estimated cost in USD for this operation
            
        Raises:
            ValueError: If token counts are negative
        """
        if prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=model,
        )
        
        usage = TokenUsage(
            operation_type=LLMOperationType.STREAMING,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            timestamp=datetime.now(),
            phase=self.current_phase,
            model=model,
        )
        
        self._operations.append(usage)
        
        logger.debug(
            f"Recorded streaming: {prompt_tokens} prompt + {completion_tokens} "
            f"completion tokens, cost=${cost:.4f}, model={model}"
        )
        
        self.check_budget_threshold()
        
        return cost

    def record_embedding(
        self,
        tokens: int,
        model: str = "text-embedding-ada-002",
    ) -> float:
        """Record an embedding operation.
        
        Args:
            tokens: Number of tokens embedded
            model: Embedding model name
            
        Returns:
            Estimated cost in USD for this operation
            
        Raises:
            ValueError: If tokens is negative
        """
        if tokens < 0:
            raise ValueError("tokens must be non-negative")
        
        cost = self.calculate_embedding_cost(tokens=tokens, model=model)
        
        usage = TokenUsage(
            operation_type=LLMOperationType.EMBEDDING,
            prompt_tokens=tokens,
            completion_tokens=0,
            total_tokens=tokens,
            estimated_cost=cost,
            timestamp=datetime.now(),
            phase=self.current_phase,
            model=model,
        )
        
        self._operations.append(usage)
        
        logger.debug(
            f"Recorded embedding: {tokens} tokens, cost=${cost:.4f}, model={model}"
        )
        
        self.check_budget_threshold()
        
        return cost

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4",
    ) -> float:
        """Calculate cost for a completion operation.
        
        Uses current Azure OpenAI pricing for the specified model.
        
        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            model: Model name (e.g., "gpt-4", "gpt-4-turbo")
            
        Returns:
            Estimated cost in USD
            
        Raises:
            ValueError: If token counts are negative
        """
        if prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        
        # Get pricing for model, default to gpt-4 if unknown
        pricing = PRICING.get(model, PRICING["gpt-4"])
        
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost

    def calculate_embedding_cost(
        self,
        tokens: int,
        model: str = "text-embedding-ada-002",
    ) -> float:
        """Calculate cost for an embedding operation.
        
        Args:
            tokens: Number of tokens embedded
            model: Embedding model name
            
        Returns:
            Estimated cost in USD
            
        Raises:
            ValueError: If tokens is negative
        """
        if tokens < 0:
            raise ValueError("tokens must be non-negative")
        
        # Get pricing for model, default to text-embedding-ada-002 if unknown
        pricing = PRICING.get(model, PRICING["text-embedding-ada-002"])
        
        return (tokens / 1000) * pricing["embedding"]

    def get_report(self) -> CostReport:
        """Generate a comprehensive usage report.
        
        Creates a CostReport with aggregated statistics across all operations,
        broken down by workflow phase and operation type.
        
        Returns:
            CostReport with complete usage statistics
        """
        report = CostReport.create_empty(start_time=self._start_time)
        
        for usage in self._operations:
            report.add_usage(usage)
        
        logger.info(
            f"Generated report: {report.operations_count} operations, "
            f"${report.total_cost:.4f} total cost"
        )
        
        return report

    def get_phase_report(self, phase: PhaseType) -> CostReport:
        """Generate a usage report for a specific workflow phase.
        
        Args:
            phase: Workflow phase to report on
            
        Returns:
            CostReport containing only operations from the specified phase
        """
        phase_operations = [op for op in self._operations if op.phase == phase]
        
        if not phase_operations:
            return CostReport.create_empty(start_time=self._start_time)
        
        report = CostReport.create_empty(start_time=phase_operations[0].timestamp)
        
        for usage in phase_operations:
            report.add_usage(usage)
        
        logger.info(
            f"Generated phase report for {phase.value}: "
            f"{report.operations_count} operations, ${report.total_cost:.4f}"
        )
        
        return report

    def check_budget_threshold(self) -> bool:
        """Check if budget threshold has been exceeded.
        
        Logs a warning if the current cost exceeds the budget threshold.
        Logs an error if the current cost exceeds the hard budget limit.
        
        Returns:
            True if threshold exceeded, False otherwise
        """
        if self.budget_threshold is None and self.budget_limit is None:
            return False
        
        current_cost = sum(op.estimated_cost for op in self._operations)
        
        # Check hard limit first
        if self.budget_limit is not None and current_cost >= self.budget_limit:
            logger.error(
                f"BUDGET LIMIT EXCEEDED: Current cost ${current_cost:.2f} "
                f">= limit ${self.budget_limit:.2f}"
            )
            return True
        
        # Check threshold
        if self.budget_threshold is not None and current_cost >= self.budget_threshold:
            logger.warning(
                f"Budget threshold exceeded: Current cost ${current_cost:.2f} "
                f">= threshold ${self.budget_threshold:.2f}"
            )
            if self.budget_limit is not None:
                remaining = self.budget_limit - current_cost
                logger.warning(f"Remaining budget: ${remaining:.2f}")
            return True
        
        return False

    def get_current_cost(self) -> float:
        """Get the current total cost across all operations.
        
        Returns:
            Total cost in USD
        """
        return sum(op.estimated_cost for op in self._operations)

    def get_total_tokens(self) -> int:
        """Get the total token count across all operations.
        
        Returns:
            Total token count
        """
        return sum(op.total_tokens for op in self._operations)

    def reset(self) -> None:
        """Reset the tracker, clearing all recorded operations.
        
        This preserves the budget settings but clears all usage data.
        """
        logger.info("Resetting cost tracker")
        self._operations = []
        self._start_time = datetime.now()

    def __repr__(self) -> str:
        """Return string representation of the tracker."""
        return (
            f"CostTracker(phase={self.current_phase.value}, "
            f"operations={len(self._operations)}, "
            f"cost=${self.get_current_cost():.4f})"
        )
