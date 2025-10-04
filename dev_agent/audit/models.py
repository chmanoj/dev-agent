"""Data models for the audit system.

This module defines Pydantic models for audit results and reports,
ensuring type safety and validation throughout the audit process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


@dataclass
class AuditResult:
    """Result of a single audit check.

    Represents the outcome of testing a specific component or feature
    of the dev-agent system.

    Attributes:
        component: Name of the component being audited
        status: Pass, fail, or warning status
        message: Human-readable description of the result
        details: Additional structured data about the audit
        recommendations: List of suggested actions if issues found
        timestamp: When the audit was performed
    """

    component: str
    status: Literal["pass", "fail", "warning"]
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate the audit result after initialization."""
        if self.status not in ("pass", "fail", "warning"):
            raise ValueError(f"Invalid status: {self.status}")
        if not self.component:
            raise ValueError("Component name cannot be empty")
        if not self.message:
            raise ValueError("Message cannot be empty")


@dataclass
class AuditReport:
    """Complete audit report containing all check results.

    Aggregates all individual audit results into a comprehensive report
    with summary statistics and overall status.

    Attributes:
        timestamp: When the audit was performed
        results: List of all individual audit results
        overall_status: Aggregated status (fail if any fail, warning if any warning, else pass)
        summary: Human-readable summary of the audit
        total_checks: Total number of checks performed
        passed_checks: Number of checks that passed
        failed_checks: Number of checks that failed
        warnings: Number of checks with warnings
    """

    timestamp: datetime
    results: list[AuditResult]
    overall_status: Literal["pass", "fail", "warning"]
    summary: str
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: int = 0

    def __post_init__(self) -> None:
        """Calculate statistics after initialization."""
        self.total_checks = len(self.results)
        self.passed_checks = sum(1 for r in self.results if r.status == "pass")
        self.failed_checks = sum(1 for r in self.results if r.status == "fail")
        self.warnings = sum(1 for r in self.results if r.status == "warning")

        # Validate overall status matches results
        if self.failed_checks > 0 and self.overall_status != "fail":
            raise ValueError("Overall status should be 'fail' when checks failed")
        if self.failed_checks == 0 and self.warnings > 0 and self.overall_status not in ("warning", "pass"):
            raise ValueError("Overall status should be 'warning' or 'pass' when no failures")

    def to_markdown(self) -> str:
        """Generate a markdown report of the audit results.

        Returns:
            Formatted markdown string with audit results
        """
        lines = [
            "# Dev-Agent Audit Report",
            "",
            f"**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Overall Status:** {self.overall_status.upper()}",
            "",
            "## Summary",
            "",
            self.summary,
            "",
            "## Statistics",
            "",
            f"- Total Checks: {self.total_checks}",
            f"- Passed: {self.passed_checks}",
            f"- Failed: {self.failed_checks}",
            f"- Warnings: {self.warnings}",
            "",
            "## Detailed Results",
            "",
        ]

        for result in self.results:
            status_emoji = {
                "pass": "✅",
                "fail": "❌",
                "warning": "⚠️",
            }[result.status]

            lines.extend([
                f"### {status_emoji} {result.component}",
                "",
                f"**Status:** {result.status.upper()}",
                "",
                f"**Message:** {result.message}",
                "",
            ])

            if result.details:
                lines.extend([
                    "**Details:**",
                    "",
                ])
                for key, value in result.details.items():
                    lines.append(f"- {key}: {value}")
                lines.append("")

            if result.recommendations:
                lines.extend([
                    "**Recommendations:**",
                    "",
                ])
                lines.extend(f"- {rec}" for rec in result.recommendations)
                lines.append("")

        return "\n".join(lines)


class AuditConfig(BaseModel):
    """Configuration for audit execution.

    Attributes:
        test_project_path: Path to test project for auditing
        skip_azure_tests: Skip tests requiring Azure OpenAI API
        verbose: Enable verbose output
        save_report: Save report to file
        report_path: Path to save report (if save_report is True)
    """

    test_project_path: str | None = Field(
        default=None,
        description="Path to test project for auditing",
    )
    skip_azure_tests: bool = Field(
        default=False,
        description="Skip tests requiring Azure OpenAI API",
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose output",
    )
    save_report: bool = Field(
        default=True,
        description="Save report to file",
    )
    report_path: str = Field(
        default=".dev_agent/audit_report.md",
        description="Path to save report",
    )
