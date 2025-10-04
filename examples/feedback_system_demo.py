"""Demo of the feedback system capabilities.

This script demonstrates all the feedback system features including
phase transitions, progress indicators, errors, warnings, and success messages.
"""

from __future__ import annotations

import time

from dev_agent.cli.feedback_system import FeedbackSystem
from dev_agent.models.enums import PhaseType


def main() -> None:
    """Run feedback system demonstration."""
    feedback = FeedbackSystem()

    print("\n" + "=" * 70)
    print("FEEDBACK SYSTEM DEMONSTRATION")
    print("=" * 70 + "\n")

    # 1. Phase Start
    print("1. Phase Start Messages:")
    feedback.show_phase_start(PhaseType.INDEXING)
    time.sleep(1)

    # 2. Operation Progress
    print("\n2. Operation Progress:")
    with feedback.show_operation_progress("Processing files", "Analyzing Python code"):
        time.sleep(2)

    # 3. Phase Complete
    print("\n3. Phase Complete with Summary:")
    summary = {
        "files_indexed": 150,
        "functions_found": 450,
        "classes_found": 75,
        "total_tokens": 50000,
    }
    feedback.show_phase_complete(PhaseType.INDEXING, summary)
    time.sleep(1)

    # 4. Success Message
    print("\n4. Success Message:")
    feedback.show_success(
        "Configuration saved successfully",
        next_steps=[
            "Run 'dev-agent init' to start indexing",
            "Check status with 'dev-agent status'",
            "View costs with 'dev-agent cost'",
        ],
    )
    time.sleep(1)

    # 5. Warning Message
    print("\n5. Warning Message:")
    feedback.show_warning(
        "This operation may incur significant Azure OpenAI costs",
        action="Consider setting a budget limit in your configuration",
    )
    time.sleep(1)

    # 6. Error Message
    print("\n6. Error Message with Suggestions:")
    feedback.show_error(
        "Azure OpenAI connection failed",
        suggestions=[
            "Check your AZURE_OPENAI_API_KEY environment variable",
            "Verify your AZURE_OPENAI_ENDPOINT is correct",
            "Ensure you have network connectivity",
            "Check if your API key has expired",
        ],
    )
    time.sleep(1)

    # 7. Info Message
    print("\n7. Informational Message:")
    feedback.show_info(
        "The indexing phase analyzes your codebase structure using Tree-sitter "
        "and generates semantic embeddings via Azure OpenAI. This allows for "
        "context-aware code generation in later phases.",
        title="About Indexing",
    )
    time.sleep(1)

    # 8. Cost Summary
    print("\n8. Cost Summary:")
    feedback.show_cost_summary(
        prompt_tokens=1500,
        completion_tokens=2500,
        total_cost=0.2450,
    )
    time.sleep(1)

    # 9. Confirmation Prompt (simulated)
    print("\n9. Confirmation Prompt:")
    print("(In real usage, this would be interactive)")
    feedback.show_info(
        "The confirm() method provides interactive yes/no prompts with "
        "default values and handles keyboard interrupts gracefully.",
        title="Confirmation Feature",
    )

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
