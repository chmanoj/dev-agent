"""Data models for onboarding and setup wizard."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class UserPreferences:
    """User preferences saved during setup.

    Attributes:
        azure_configured: Whether Azure OpenAI has been configured
        preferred_editor: User's preferred code editor (optional)
        cost_warnings_enabled: Whether to show cost warnings
        budget_threshold: Budget threshold for cost warnings (optional)
        auto_approve_phases: Whether to auto-approve workflow phases
        verbose_output: Whether to show verbose output in CLI
    """

    azure_configured: bool = False
    preferred_editor: str | None = None
    cost_warnings_enabled: bool = True
    budget_threshold: float | None = None
    auto_approve_phases: bool = False
    verbose_output: bool = False


@dataclass
class OnboardingStep:
    """Single step in the onboarding flow.

    Attributes:
        title: Step title displayed to user
        description: Detailed description of the step
        action: Callable that executes the step, returns True on success
        help_text: Additional help text for the step
        estimated_time: Estimated time to complete (e.g., "2 minutes")
        skippable: Whether the step can be skipped
        completed: Whether the step has been completed
    """

    title: str
    description: str
    action: Callable[[], bool]
    help_text: str
    estimated_time: str
    skippable: bool = False
    completed: bool = False


@dataclass
class SetupResult:
    """Result of setup wizard execution.

    Attributes:
        azure_configured: Whether Azure OpenAI was successfully configured
        preferences_saved: Whether user preferences were saved
        sample_project_created: Whether a sample project was created
        ready_to_use: Whether the system is ready to use
        errors: List of errors encountered during setup
        skipped_steps: List of step titles that were skipped
    """

    azure_configured: bool = False
    preferences_saved: bool = False
    sample_project_created: bool = False
    ready_to_use: bool = False
    errors: list[str] = field(default_factory=list)
    skipped_steps: list[str] = field(default_factory=list)


@dataclass
class OnboardingFlow:
    """Onboarding flow with steps and guidance.

    Attributes:
        steps: List of onboarding steps
        tips: List of helpful tips
        warnings: List of warnings or important notes
    """

    steps: list[OnboardingStep] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
