"""Cost tracking models for Azure OpenAI usage.

This module provides dataclasses for tracking token usage and costs across
LLM operations. These models support per-operation tracking and aggregated
reporting for sessions and workflow phases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from dev_agent.models.enums import LLMOperationType, LLMProvider, PhaseType


@dataclass
class TokenUsage:
    """Token usage for a single LLM operation.
    
    This dataclass tracks token consumption and cost for individual operations
    such as completions, embeddings, or streaming requests. It includes metadata
    about the operation type, workflow phase, provider, and timestamp.
    
    Attributes:
        operation_type: Type of LLM operation (completion, embedding, streaming)
        prompt_tokens: Number of tokens in the prompt/input
        completion_tokens: Number of tokens in the completion/output (0 for embeddings)
        total_tokens: Total tokens used (prompt + completion)
        estimated_cost: Estimated cost in USD for this operation
        timestamp: When the operation occurred
        phase: Workflow phase during which operation occurred
        model: Model name used (e.g., "gpt-4", "gemini-pro", "text-embedding-ada-002")
        provider: LLM provider used for the operation
    
    Example:
        ```python
        usage = TokenUsage(
            operation_type=LLMOperationType.COMPLETION,
            prompt_tokens=150,
            completion_tokens=300,
            total_tokens=450,
            estimated_cost=0.027,
            timestamp=datetime.now(),
            phase=PhaseType.SPECIFICATION,
            model="gpt-4",
            provider=LLMProvider.AZURE_OPENAI,
        )
        ```
    """

    operation_type: LLMOperationType
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    timestamp: datetime
    phase: PhaseType
    model: str = "unknown"
    provider: LLMProvider = LLMProvider.AZURE_OPENAI

    def __post_init__(self) -> None:
        """Validate token usage data after initialization."""
        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if self.completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        if self.total_tokens < 0:
            raise ValueError("total_tokens must be non-negative")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost must be non-negative")


@dataclass
class CostReport:
    """Cost report for a session or workflow phase.
    
    This dataclass aggregates token usage and costs across multiple operations,
    providing summaries by phase, operation type, and provider. It supports 
    tracking costs over time and generating detailed usage reports with 
    multi-provider breakdown.
    
    Attributes:
        total_prompt_tokens: Total prompt tokens across all operations
        total_completion_tokens: Total completion tokens across all operations
        total_embedding_tokens: Total embedding tokens across all operations
        total_cost: Total estimated cost in USD
        operations_count: Number of operations tracked
        by_phase: Cost breakdown by workflow phase (PhaseType -> cost)
        by_operation: Token count by operation type (operation name -> token count)
        by_provider: Cost breakdown by provider (LLMProvider -> cost)
        start_time: When tracking started
        end_time: When tracking ended
        operations: List of individual TokenUsage records
    
    Example:
        ```python
        report = CostReport(
            total_prompt_tokens=1000,
            total_completion_tokens=2000,
            total_embedding_tokens=500,
            total_cost=0.15,
            operations_count=10,
            by_phase={PhaseType.SPECIFICATION: 0.08, PhaseType.DESIGN: 0.07},
            by_operation={"completion": 3000, "embedding": 500},
            by_provider={LLMProvider.AZURE_OPENAI: 0.10, LLMProvider.GEMINI: 0.05},
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        print(f"Average cost per operation: ${report.average_cost_per_operation:.4f}")
        print(f"Azure OpenAI cost: ${report.get_provider_cost(LLMProvider.AZURE_OPENAI):.4f}")
        ```
    """

    total_prompt_tokens: int
    total_completion_tokens: int
    total_embedding_tokens: int
    total_cost: float
    operations_count: int
    by_phase: dict[PhaseType, float]
    by_operation: dict[str, int]
    by_provider: dict[LLMProvider, float]
    start_time: datetime
    end_time: datetime
    operations: list[TokenUsage] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate cost report data after initialization."""
        if self.total_prompt_tokens < 0:
            raise ValueError("total_prompt_tokens must be non-negative")
        if self.total_completion_tokens < 0:
            raise ValueError("total_completion_tokens must be non-negative")
        if self.total_embedding_tokens < 0:
            raise ValueError("total_embedding_tokens must be non-negative")
        if self.total_cost < 0:
            raise ValueError("total_cost must be non-negative")
        if self.operations_count < 0:
            raise ValueError("operations_count must be non-negative")
        if self.end_time < self.start_time:
            raise ValueError("end_time must be after start_time")

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens across all operations.
        
        Returns:
            Sum of prompt, completion, and embedding tokens
        """
        return (
            self.total_prompt_tokens
            + self.total_completion_tokens
            + self.total_embedding_tokens
        )

    @property
    def average_cost_per_operation(self) -> float:
        """Calculate average cost per operation.
        
        Returns:
            Average cost in USD, or 0.0 if no operations
        """
        if self.operations_count == 0:
            return 0.0
        return self.total_cost / self.operations_count

    @property
    def average_tokens_per_operation(self) -> float:
        """Calculate average tokens per operation.
        
        Returns:
            Average token count, or 0.0 if no operations
        """
        if self.operations_count == 0:
            return 0.0
        return self.total_tokens / self.operations_count

    @property
    def duration_seconds(self) -> float:
        """Calculate duration of tracking period in seconds.
        
        Returns:
            Duration in seconds
        """
        return (self.end_time - self.start_time).total_seconds()

    def add_usage(self, usage: TokenUsage) -> None:
        """Add a TokenUsage record to this report.
        
        This method updates all aggregate statistics based on the new usage record.
        
        Args:
            usage: TokenUsage record to add
        """
        # Update token counts
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        
        # Embedding operations count as prompt tokens
        if usage.operation_type == LLMOperationType.EMBEDDING:
            self.total_embedding_tokens += usage.total_tokens
        
        # Update cost and count
        self.total_cost += usage.estimated_cost
        self.operations_count += 1
        
        # Update by_phase breakdown
        if usage.phase in self.by_phase:
            self.by_phase[usage.phase] += usage.estimated_cost
        else:
            self.by_phase[usage.phase] = usage.estimated_cost
        
        # Update by_operation breakdown
        op_name = usage.operation_type.value
        if op_name in self.by_operation:
            self.by_operation[op_name] += usage.total_tokens
        else:
            self.by_operation[op_name] = usage.total_tokens
        
        # Update by_provider breakdown
        provider = getattr(usage, 'provider', LLMProvider.AZURE_OPENAI)
        if provider in self.by_provider:
            self.by_provider[provider] += usage.estimated_cost
        else:
            self.by_provider[provider] = usage.estimated_cost
        
        # Add to operations list
        self.operations.append(usage)
        
        # Update end_time to latest operation
        if usage.timestamp > self.end_time:
            self.end_time = usage.timestamp

    def get_phase_cost(self, phase: PhaseType) -> float:
        """Get total cost for a specific workflow phase.
        
        Args:
            phase: Workflow phase to query
            
        Returns:
            Total cost for the phase, or 0.0 if no operations in that phase
        """
        return self.by_phase.get(phase, 0.0)

    def get_operation_tokens(self, operation_type: LLMOperationType) -> int:
        """Get total tokens for a specific operation type.
        
        Args:
            operation_type: Operation type to query
            
        Returns:
            Total tokens for the operation type, or 0 if no operations of that type
        """
        return self.by_operation.get(operation_type.value, 0)

    def get_provider_cost(self, provider: LLMProvider) -> float:
        """Get total cost for a specific provider.
        
        Args:
            provider: LLM provider to query
            
        Returns:
            Total cost for the provider, or 0.0 if no operations with that provider
        """
        return self.by_provider.get(provider, 0.0)

    @classmethod
    def create_empty(cls, start_time: datetime | None = None) -> CostReport:
        """Create an empty cost report.
        
        Args:
            start_time: Start time for the report (defaults to now)
            
        Returns:
            Empty CostReport instance
        """
        now = start_time or datetime.now()
        return cls(
            total_prompt_tokens=0,
            total_completion_tokens=0,
            total_embedding_tokens=0,
            total_cost=0.0,
            operations_count=0,
            by_phase={},
            by_operation={},
            by_provider={},
            start_time=now,
            end_time=now,
            operations=[],
        )
