"""Unit tests for the CostTracker class.

This module tests token usage recording, cost calculation, budget threshold
warnings, and report generation functionality.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from dev_agent.llm.cost_tracker import PRICING, CostTracker
from dev_agent.models.enums import LLMOperationType, PhaseType


class TestCostTrackerInitialization:
    """Test CostTracker initialization and configuration."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        tracker = CostTracker()
        
        assert tracker.current_phase == PhaseType.INDEXING
        assert tracker.budget_threshold is None
        assert tracker.budget_limit is None
        assert tracker.get_current_cost() == 0.0
        assert tracker.get_total_tokens() == 0

    def test_init_with_phase(self) -> None:
        """Test initialization with specific phase."""
        tracker = CostTracker(current_phase=PhaseType.SPECIFICATION)
        
        assert tracker.current_phase == PhaseType.SPECIFICATION

    def test_init_with_budget_threshold(self) -> None:
        """Test initialization with budget threshold."""
        tracker = CostTracker(budget_threshold=10.0)
        
        assert tracker.budget_threshold == 10.0

    def test_init_with_budget_limit(self) -> None:
        """Test initialization with budget limit."""
        tracker = CostTracker(budget_limit=50.0)
        
        assert tracker.budget_limit == 50.0

    def test_init_with_all_parameters(self) -> None:
        """Test initialization with all parameters."""
        tracker = CostTracker(
            current_phase=PhaseType.DESIGN,
            budget_threshold=10.0,
            budget_limit=50.0,
        )
        
        assert tracker.current_phase == PhaseType.DESIGN
        assert tracker.budget_threshold == 10.0
        assert tracker.budget_limit == 50.0

    def test_init_negative_threshold_raises_error(self) -> None:
        """Test that negative budget threshold raises ValueError."""
        with pytest.raises(ValueError, match="budget_threshold must be non-negative"):
            CostTracker(budget_threshold=-1.0)

    def test_init_negative_limit_raises_error(self) -> None:
        """Test that negative budget limit raises ValueError."""
        with pytest.raises(ValueError, match="budget_limit must be non-negative"):
            CostTracker(budget_limit=-1.0)

    def test_init_threshold_greater_than_limit_raises_error(self) -> None:
        """Test that threshold > limit raises ValueError."""
        with pytest.raises(ValueError, match="budget_threshold must be <= budget_limit"):
            CostTracker(budget_threshold=100.0, budget_limit=50.0)


class TestPhaseManagement:
    """Test workflow phase management."""

    def test_set_phase(self) -> None:
        """Test setting the current phase."""
        tracker = CostTracker(current_phase=PhaseType.INDEXING)
        
        tracker.set_phase(PhaseType.SPECIFICATION)
        
        assert tracker.current_phase == PhaseType.SPECIFICATION

    def test_operations_recorded_in_correct_phase(self) -> None:
        """Test that operations are recorded in the current phase."""
        tracker = CostTracker(current_phase=PhaseType.INDEXING)
        
        tracker.record_completion(100, 200)
        tracker.set_phase(PhaseType.SPECIFICATION)
        tracker.record_completion(150, 250)
        
        report = tracker.get_report()
        
        assert PhaseType.INDEXING in report.by_phase
        assert PhaseType.SPECIFICATION in report.by_phase


class TestCompletionRecording:
    """Test recording completion operations."""

    def test_record_completion_basic(self) -> None:
        """Test basic completion recording."""
        tracker = CostTracker()
        
        cost = tracker.record_completion(
            prompt_tokens=100,
            completion_tokens=200,
            model="gpt-4",
        )
        
        assert cost > 0
        assert tracker.get_total_tokens() == 300
        assert tracker.get_current_cost() == cost

    def test_record_completion_returns_correct_cost(self) -> None:
        """Test that record_completion returns correct cost."""
        tracker = CostTracker()
        
        # GPT-4: $0.03 per 1K prompt, $0.06 per 1K completion
        expected_cost = (100 / 1000) * 0.03 + (200 / 1000) * 0.06
        
        cost = tracker.record_completion(100, 200, "gpt-4")
        
        assert abs(cost - expected_cost) < 0.0001

    def test_record_completion_different_models(self) -> None:
        """Test recording completions with different models."""
        tracker = CostTracker()
        
        cost_gpt4 = tracker.record_completion(100, 200, "gpt-4")
        cost_gpt35 = tracker.record_completion(100, 200, "gpt-3.5-turbo")
        
        # GPT-4 should be more expensive than GPT-3.5
        assert cost_gpt4 > cost_gpt35

    def test_record_completion_negative_tokens_raises_error(self) -> None:
        """Test that negative token counts raise ValueError."""
        tracker = CostTracker()
        
        with pytest.raises(ValueError, match="prompt_tokens must be non-negative"):
            tracker.record_completion(-100, 200)
        
        with pytest.raises(ValueError, match="completion_tokens must be non-negative"):
            tracker.record_completion(100, -200)

    def test_record_multiple_completions(self) -> None:
        """Test recording multiple completion operations."""
        tracker = CostTracker()
        
        cost1 = tracker.record_completion(100, 200)
        cost2 = tracker.record_completion(150, 250)
        cost3 = tracker.record_completion(200, 300)
        
        total_cost = cost1 + cost2 + cost3
        
        assert abs(tracker.get_current_cost() - total_cost) < 0.0001
        assert tracker.get_total_tokens() == 1200  # (100+200) + (150+250) + (200+300)


class TestStreamingRecording:
    """Test recording streaming operations."""

    def test_record_streaming_basic(self) -> None:
        """Test basic streaming recording."""
        tracker = CostTracker()
        
        cost = tracker.record_streaming(
            prompt_tokens=100,
            completion_tokens=200,
            model="gpt-4",
        )
        
        assert cost > 0
        assert tracker.get_total_tokens() == 300

    def test_record_streaming_uses_same_pricing_as_completion(self) -> None:
        """Test that streaming uses same pricing as regular completion."""
        tracker = CostTracker()
        
        completion_cost = tracker.record_completion(100, 200, "gpt-4")
        streaming_cost = tracker.record_streaming(100, 200, "gpt-4")
        
        assert abs(completion_cost - streaming_cost) < 0.0001

    def test_record_streaming_tracked_separately(self) -> None:
        """Test that streaming operations are tracked separately."""
        tracker = CostTracker()
        
        tracker.record_completion(100, 200)
        tracker.record_streaming(100, 200)
        
        report = tracker.get_report()
        
        assert "completion" in report.by_operation
        assert "streaming" in report.by_operation

    def test_record_streaming_negative_tokens_raises_error(self) -> None:
        """Test that negative token counts raise ValueError."""
        tracker = CostTracker()
        
        with pytest.raises(ValueError, match="prompt_tokens must be non-negative"):
            tracker.record_streaming(-100, 200)
        
        with pytest.raises(ValueError, match="completion_tokens must be non-negative"):
            tracker.record_streaming(100, -200)


class TestEmbeddingRecording:
    """Test recording embedding operations."""

    def test_record_embedding_basic(self) -> None:
        """Test basic embedding recording."""
        tracker = CostTracker()
        
        cost = tracker.record_embedding(
            tokens=1000,
            model="text-embedding-ada-002",
        )
        
        assert cost > 0
        assert tracker.get_total_tokens() == 1000

    def test_record_embedding_returns_correct_cost(self) -> None:
        """Test that record_embedding returns correct cost."""
        tracker = CostTracker()
        
        # text-embedding-ada-002: $0.0001 per 1K tokens
        expected_cost = (1000 / 1000) * 0.0001
        
        cost = tracker.record_embedding(1000, "text-embedding-ada-002")
        
        assert abs(cost - expected_cost) < 0.000001

    def test_record_embedding_negative_tokens_raises_error(self) -> None:
        """Test that negative token count raises ValueError."""
        tracker = CostTracker()
        
        with pytest.raises(ValueError, match="tokens must be non-negative"):
            tracker.record_embedding(-1000)

    def test_record_multiple_embeddings(self) -> None:
        """Test recording multiple embedding operations."""
        tracker = CostTracker()
        
        cost1 = tracker.record_embedding(1000)
        cost2 = tracker.record_embedding(2000)
        cost3 = tracker.record_embedding(1500)
        
        total_cost = cost1 + cost2 + cost3
        
        assert abs(tracker.get_current_cost() - total_cost) < 0.000001
        assert tracker.get_total_tokens() == 4500


class TestCostCalculation:
    """Test cost calculation methods."""

    def test_calculate_cost_gpt4(self) -> None:
        """Test cost calculation for GPT-4."""
        tracker = CostTracker()
        
        # GPT-4: $0.03 per 1K prompt, $0.06 per 1K completion
        expected = (1000 / 1000) * 0.03 + (2000 / 1000) * 0.06
        
        cost = tracker.calculate_cost(1000, 2000, "gpt-4")
        
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_gpt35_turbo(self) -> None:
        """Test cost calculation for GPT-3.5 Turbo."""
        tracker = CostTracker()
        
        # GPT-3.5 Turbo: $0.0015 per 1K prompt, $0.002 per 1K completion
        expected = (1000 / 1000) * 0.0015 + (2000 / 1000) * 0.002
        
        cost = tracker.calculate_cost(1000, 2000, "gpt-3.5-turbo")
        
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_unknown_model_defaults_to_gpt4(self) -> None:
        """Test that unknown models default to GPT-4 pricing."""
        tracker = CostTracker()
        
        cost_unknown = tracker.calculate_cost(1000, 2000, "unknown-model")
        cost_gpt4 = tracker.calculate_cost(1000, 2000, "gpt-4")
        
        assert abs(cost_unknown - cost_gpt4) < 0.0001

    def test_calculate_cost_negative_tokens_raises_error(self) -> None:
        """Test that negative tokens raise ValueError."""
        tracker = CostTracker()
        
        with pytest.raises(ValueError, match="prompt_tokens must be non-negative"):
            tracker.calculate_cost(-1000, 2000)
        
        with pytest.raises(ValueError, match="completion_tokens must be non-negative"):
            tracker.calculate_cost(1000, -2000)

    def test_calculate_embedding_cost(self) -> None:
        """Test embedding cost calculation."""
        tracker = CostTracker()
        
        # text-embedding-ada-002: $0.0001 per 1K tokens
        expected = (5000 / 1000) * 0.0001
        
        cost = tracker.calculate_embedding_cost(5000, "text-embedding-ada-002")
        
        assert abs(cost - expected) < 0.000001

    def test_calculate_embedding_cost_negative_tokens_raises_error(self) -> None:
        """Test that negative tokens raise ValueError."""
        tracker = CostTracker()
        
        with pytest.raises(ValueError, match="tokens must be non-negative"):
            tracker.calculate_embedding_cost(-1000)


class TestReportGeneration:
    """Test usage report generation."""

    def test_get_report_empty(self) -> None:
        """Test getting report with no operations."""
        tracker = CostTracker()
        
        report = tracker.get_report()
        
        assert report.total_prompt_tokens == 0
        assert report.total_completion_tokens == 0
        assert report.total_embedding_tokens == 0
        assert report.total_cost == 0.0
        assert report.operations_count == 0

    def test_get_report_with_completions(self) -> None:
        """Test report generation with completion operations."""
        tracker = CostTracker()
        
        tracker.record_completion(100, 200)
        tracker.record_completion(150, 250)
        
        report = tracker.get_report()
        
        assert report.total_prompt_tokens == 250
        assert report.total_completion_tokens == 450
        assert report.operations_count == 2
        assert report.total_cost > 0

    def test_get_report_with_embeddings(self) -> None:
        """Test report generation with embedding operations."""
        tracker = CostTracker()
        
        tracker.record_embedding(1000)
        tracker.record_embedding(2000)
        
        report = tracker.get_report()
        
        assert report.total_embedding_tokens == 3000
        assert report.operations_count == 2

    def test_get_report_with_mixed_operations(self) -> None:
        """Test report with mixed operation types."""
        tracker = CostTracker()
        
        tracker.record_completion(100, 200)
        tracker.record_streaming(150, 250)
        tracker.record_embedding(1000)
        
        report = tracker.get_report()
        
        assert report.operations_count == 3
        assert "completion" in report.by_operation
        assert "streaming" in report.by_operation
        assert "embedding" in report.by_operation

    def test_get_report_by_phase(self) -> None:
        """Test report breakdown by phase."""
        tracker = CostTracker(current_phase=PhaseType.INDEXING)
        
        tracker.record_completion(100, 200)
        tracker.set_phase(PhaseType.SPECIFICATION)
        tracker.record_completion(150, 250)
        
        report = tracker.get_report()
        
        assert PhaseType.INDEXING in report.by_phase
        assert PhaseType.SPECIFICATION in report.by_phase
        assert report.by_phase[PhaseType.INDEXING] > 0
        assert report.by_phase[PhaseType.SPECIFICATION] > 0

    def test_get_phase_report(self) -> None:
        """Test getting report for specific phase."""
        tracker = CostTracker(current_phase=PhaseType.INDEXING)
        
        tracker.record_completion(100, 200)
        tracker.set_phase(PhaseType.SPECIFICATION)
        tracker.record_completion(150, 250)
        
        indexing_report = tracker.get_phase_report(PhaseType.INDEXING)
        spec_report = tracker.get_phase_report(PhaseType.SPECIFICATION)
        
        assert indexing_report.operations_count == 1
        assert spec_report.operations_count == 1
        assert indexing_report.total_prompt_tokens == 100
        assert spec_report.total_prompt_tokens == 150

    def test_get_phase_report_empty_phase(self) -> None:
        """Test getting report for phase with no operations."""
        tracker = CostTracker()
        
        tracker.record_completion(100, 200)
        
        design_report = tracker.get_phase_report(PhaseType.DESIGN)
        
        assert design_report.operations_count == 0
        assert design_report.total_cost == 0.0


class TestBudgetThresholds:
    """Test budget threshold warnings."""

    def test_check_budget_threshold_no_threshold_set(self) -> None:
        """Test that no warning when no threshold set."""
        tracker = CostTracker()
        
        tracker.record_completion(1000, 2000)
        
        assert not tracker.check_budget_threshold()

    def test_check_budget_threshold_below_threshold(self) -> None:
        """Test no warning when below threshold."""
        tracker = CostTracker(budget_threshold=10.0)
        
        tracker.record_completion(100, 200)  # Small operation
        
        assert not tracker.check_budget_threshold()

    def test_check_budget_threshold_exceeds_threshold(self) -> None:
        """Test warning when threshold exceeded."""
        tracker = CostTracker(budget_threshold=0.01)
        
        tracker.record_completion(1000, 2000)  # Expensive operation
        
        assert tracker.check_budget_threshold()

    def test_check_budget_threshold_at_threshold(self) -> None:
        """Test warning when exactly at threshold."""
        tracker = CostTracker(budget_threshold=0.09)
        
        # This should cost exactly $0.09
        tracker.record_completion(1000, 2000, "gpt-4")
        
        assert tracker.check_budget_threshold()

    def test_check_budget_limit_exceeded(self) -> None:
        """Test error when hard limit exceeded."""
        tracker = CostTracker(budget_limit=0.01)
        
        tracker.record_completion(1000, 2000)
        
        assert tracker.check_budget_threshold()

    def test_check_budget_threshold_and_limit(self) -> None:
        """Test both threshold and limit."""
        tracker = CostTracker(budget_threshold=0.05, budget_limit=0.10)
        
        # First operation exceeds threshold but not limit
        tracker.record_completion(500, 1000)
        assert tracker.check_budget_threshold()
        
        # Second operation exceeds limit
        tracker.record_completion(500, 1000)
        assert tracker.check_budget_threshold()


class TestUtilityMethods:
    """Test utility methods."""

    def test_get_current_cost(self) -> None:
        """Test getting current total cost."""
        tracker = CostTracker()
        
        cost1 = tracker.record_completion(100, 200)
        cost2 = tracker.record_completion(150, 250)
        
        expected_total = cost1 + cost2
        
        assert abs(tracker.get_current_cost() - expected_total) < 0.0001

    def test_get_total_tokens(self) -> None:
        """Test getting total token count."""
        tracker = CostTracker()
        
        tracker.record_completion(100, 200)
        tracker.record_completion(150, 250)
        tracker.record_embedding(1000)
        
        assert tracker.get_total_tokens() == 1700  # 300 + 400 + 1000

    def test_reset(self) -> None:
        """Test resetting the tracker."""
        tracker = CostTracker(budget_threshold=10.0)
        
        tracker.record_completion(100, 200)
        tracker.record_embedding(1000)
        
        assert tracker.get_current_cost() > 0
        assert tracker.get_total_tokens() > 0
        
        tracker.reset()
        
        assert tracker.get_current_cost() == 0.0
        assert tracker.get_total_tokens() == 0
        assert tracker.budget_threshold == 10.0  # Budget settings preserved

    def test_repr(self) -> None:
        """Test string representation."""
        tracker = CostTracker(current_phase=PhaseType.SPECIFICATION)
        
        tracker.record_completion(100, 200)
        
        repr_str = repr(tracker)
        
        assert "CostTracker" in repr_str
        assert "specification" in repr_str
        assert "operations=1" in repr_str


class TestPricingConstants:
    """Test pricing constants."""

    def test_pricing_has_all_models(self) -> None:
        """Test that PRICING dict has all expected models."""
        expected_models = [
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-3.5-turbo",
            "text-embedding-ada-002",
        ]
        
        for model in expected_models:
            assert model in PRICING

    def test_pricing_has_correct_structure(self) -> None:
        """Test that pricing entries have correct structure."""
        # Completion models should have prompt and completion prices
        for model in ["gpt-4", "gpt-4-32k", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"]:
            assert "prompt" in PRICING[model]
            assert "completion" in PRICING[model]
            assert PRICING[model]["prompt"] > 0
            assert PRICING[model]["completion"] > 0
        
        # Embedding models should have embedding price
        assert "embedding" in PRICING["text-embedding-ada-002"]
        assert PRICING["text-embedding-ada-002"]["embedding"] > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_tokens(self) -> None:
        """Test recording operations with zero tokens."""
        tracker = CostTracker()
        
        cost = tracker.record_completion(0, 0)
        
        assert cost == 0.0
        assert tracker.get_total_tokens() == 0

    def test_very_large_token_counts(self) -> None:
        """Test with very large token counts."""
        tracker = CostTracker()
        
        # 100K tokens
        cost = tracker.record_completion(50000, 50000)
        
        assert cost > 0
        assert tracker.get_total_tokens() == 100000

    def test_many_small_operations(self) -> None:
        """Test tracking many small operations."""
        tracker = CostTracker()
        
        # Record 1000 small operations
        for _ in range(1000):
            tracker.record_completion(10, 20)
        
        report = tracker.get_report()
        
        assert report.operations_count == 1000
        assert report.total_tokens == 30000  # 30 tokens * 1000

    def test_mixed_phases_and_operations(self) -> None:
        """Test complex scenario with mixed phases and operations."""
        tracker = CostTracker(current_phase=PhaseType.INDEXING)
        
        # Indexing phase
        tracker.record_embedding(5000)
        tracker.record_embedding(3000)
        
        # Specification phase
        tracker.set_phase(PhaseType.SPECIFICATION)
        tracker.record_completion(200, 400)
        tracker.record_streaming(150, 350)
        
        # Design phase
        tracker.set_phase(PhaseType.DESIGN)
        tracker.record_completion(300, 600)
        
        report = tracker.get_report()
        
        assert report.operations_count == 5
        assert len(report.by_phase) == 3
        assert PhaseType.INDEXING in report.by_phase
        assert PhaseType.SPECIFICATION in report.by_phase
        assert PhaseType.DESIGN in report.by_phase
