"""Error analytics and reporting system for continuous improvement."""

from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .exceptions import DevAgentError, ErrorCategory, ErrorSeverity


@dataclass
class ErrorTrend:
    """Represents error trends over time."""

    category: str
    hourly_counts: list[int]
    daily_counts: list[int]
    weekly_counts: list[int]
    peak_hour: int
    peak_day: int
    trend_direction: str  # "increasing", "decreasing", "stable"


@dataclass
class RecoveryMetrics:
    """Metrics for error recovery effectiveness."""

    total_attempts: int
    successful_recoveries: int
    failed_recoveries: int
    success_rate: float
    average_recovery_time: float
    recovery_methods: dict[str, int]


@dataclass
class ErrorHotspot:
    """Represents areas with high error frequency."""

    location: str  # file path, operation, or service
    error_count: int
    error_types: dict[str, int]
    severity_distribution: dict[str, int]
    first_occurrence: float
    last_occurrence: float


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""

    generated_at: float
    time_period: str
    total_errors: int
    error_trends: list[ErrorTrend]
    recovery_metrics: RecoveryMetrics
    error_hotspots: list[ErrorHotspot]
    top_error_messages: list[tuple[str, int]]
    recommendations: list[str]


class ErrorAnalyticsEngine:
    """Advanced analytics engine for error tracking and analysis."""

    def __init__(self, project_path: str | None = None):
        self.project_path = project_path
        self.error_history: deque[dict[str, Any]] = deque(maxlen=10000)
        self.recovery_history: deque[dict[str, Any]] = deque(maxlen=5000)
        self.analytics_cache: dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes cache TTL

    def record_error(self, error: DevAgentError, context: dict[str, Any] | None = None) -> None:
        """Record error occurrence for analytics."""
        error_record = {
            "timestamp": time.time(),
            "category": error.category.value,
            "severity": error.severity.value,
            "message": error.message,
            "normalized_message": self._normalize_message(error.message),
            "operation": error.context.operation if error.context else None,
            "file_path": error.context.file_path if error.context else None,
            "phase": error.context.phase if error.context else None,
            "recoverable": error.recoverable,
            "context": context or {},
        }
        
        self.error_history.append(error_record)
        self._invalidate_cache()

    def record_recovery_attempt(
        self,
        error_signature: str,
        recovery_method: str,
        success: bool,
        recovery_time: float,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record recovery attempt for analytics."""
        recovery_record = {
            "timestamp": time.time(),
            "error_signature": error_signature,
            "recovery_method": recovery_method,
            "success": success,
            "recovery_time": recovery_time,
            "details": details or {},
        }
        
        self.recovery_history.append(recovery_record)
        self._invalidate_cache()

    def generate_trends_analysis(self, time_period_hours: int = 24) -> list[ErrorTrend]:
        """Generate error trends analysis for specified time period."""
        cache_key = f"trends_{time_period_hours}"
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]

        cutoff_time = time.time() - (time_period_hours * 3600)
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] > cutoff_time
        ]

        trends = []
        categories = set(error["category"] for error in recent_errors)

        for category in categories:
            category_errors = [
                error for error in recent_errors
                if error["category"] == category
            ]
            
            trend = self._calculate_trend_for_category(category, category_errors, time_period_hours)
            trends.append(trend)

        self.analytics_cache[cache_key] = trends
        return trends

    def _calculate_trend_for_category(
        self, category: str, errors: list[dict[str, Any]], time_period_hours: int
    ) -> ErrorTrend:
        """Calculate trend metrics for a specific error category."""
        # Initialize time buckets
        hourly_counts = [0] * min(time_period_hours, 24)
        daily_counts = [0] * min(time_period_hours // 24 + 1, 7)
        weekly_counts = [0] * min(time_period_hours // (24 * 7) + 1, 4)

        current_time = time.time()
        
        # Count errors in time buckets
        for error in errors:
            hours_ago = int((current_time - error["timestamp"]) // 3600)
            days_ago = int((current_time - error["timestamp"]) // (3600 * 24))
            weeks_ago = int((current_time - error["timestamp"]) // (3600 * 24 * 7))

            if hours_ago < len(hourly_counts):
                hourly_counts[-(hours_ago + 1)] += 1
            
            if days_ago < len(daily_counts):
                daily_counts[-(days_ago + 1)] += 1
            
            if weeks_ago < len(weekly_counts):
                weekly_counts[-(weeks_ago + 1)] += 1

        # Find peak times
        peak_hour = hourly_counts.index(max(hourly_counts)) if hourly_counts else 0
        peak_day = daily_counts.index(max(daily_counts)) if daily_counts else 0

        # Determine trend direction
        trend_direction = self._calculate_trend_direction(hourly_counts)

        return ErrorTrend(
            category=category,
            hourly_counts=hourly_counts,
            daily_counts=daily_counts,
            weekly_counts=weekly_counts,
            peak_hour=peak_hour,
            peak_day=peak_day,
            trend_direction=trend_direction,
        )

    def _calculate_trend_direction(self, counts: list[int]) -> str:
        """Calculate trend direction from count data."""
        if len(counts) < 2:
            return "stable"

        # Compare recent half with earlier half
        mid_point = len(counts) // 2
        recent_avg = sum(counts[mid_point:]) / len(counts[mid_point:])
        earlier_avg = sum(counts[:mid_point]) / len(counts[:mid_point])

        if recent_avg > earlier_avg * 1.2:
            return "increasing"
        elif recent_avg < earlier_avg * 0.8:
            return "decreasing"
        else:
            return "stable"

    def generate_recovery_metrics(self, time_period_hours: int = 24) -> RecoveryMetrics:
        """Generate recovery effectiveness metrics."""
        cache_key = f"recovery_{time_period_hours}"
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]

        cutoff_time = time.time() - (time_period_hours * 3600)
        recent_recoveries = [
            recovery for recovery in self.recovery_history
            if recovery["timestamp"] > cutoff_time
        ]

        total_attempts = len(recent_recoveries)
        successful_recoveries = sum(1 for r in recent_recoveries if r["success"])
        failed_recoveries = total_attempts - successful_recoveries

        success_rate = successful_recoveries / total_attempts if total_attempts > 0 else 0.0

        # Calculate average recovery time for successful recoveries
        successful_times = [
            r["recovery_time"] for r in recent_recoveries
            if r["success"] and r["recovery_time"] > 0
        ]
        average_recovery_time = sum(successful_times) / len(successful_times) if successful_times else 0.0

        # Count recovery methods
        recovery_methods = defaultdict(int)
        for recovery in recent_recoveries:
            recovery_methods[recovery["recovery_method"]] += 1

        metrics = RecoveryMetrics(
            total_attempts=total_attempts,
            successful_recoveries=successful_recoveries,
            failed_recoveries=failed_recoveries,
            success_rate=success_rate,
            average_recovery_time=average_recovery_time,
            recovery_methods=dict(recovery_methods),
        )

        self.analytics_cache[cache_key] = metrics
        return metrics

    def identify_error_hotspots(self, time_period_hours: int = 24) -> list[ErrorHotspot]:
        """Identify areas with high error frequency."""
        cache_key = f"hotspots_{time_period_hours}"
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]

        cutoff_time = time.time() - (time_period_hours * 3600)
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] > cutoff_time
        ]

        # Group errors by location (file_path, operation, or "unknown")
        location_groups = defaultdict(list)
        for error in recent_errors:
            location = error.get("file_path") or error.get("operation") or "unknown"
            location_groups[location].append(error)

        hotspots = []
        for location, errors in location_groups.items():
            if len(errors) >= 3:  # Only consider locations with 3+ errors
                error_types = defaultdict(int)
                severity_distribution = defaultdict(int)
                
                timestamps = []
                for error in errors:
                    error_types[error["category"]] += 1
                    severity_distribution[error["severity"]] += 1
                    timestamps.append(error["timestamp"])

                hotspot = ErrorHotspot(
                    location=location,
                    error_count=len(errors),
                    error_types=dict(error_types),
                    severity_distribution=dict(severity_distribution),
                    first_occurrence=min(timestamps),
                    last_occurrence=max(timestamps),
                )
                hotspots.append(hotspot)

        # Sort by error count (descending)
        hotspots.sort(key=lambda x: x.error_count, reverse=True)

        self.analytics_cache[cache_key] = hotspots
        return hotspots

    def get_top_error_messages(self, limit: int = 10, time_period_hours: int = 24) -> list[tuple[str, int]]:
        """Get most common error messages."""
        cutoff_time = time.time() - (time_period_hours * 3600)
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] > cutoff_time
        ]

        message_counts = defaultdict(int)
        for error in recent_errors:
            normalized_message = error["normalized_message"]
            message_counts[normalized_message] += 1

        # Sort by count and return top N
        top_messages = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)
        return top_messages[:limit]

    def generate_recommendations(self) -> list[str]:
        """Generate actionable recommendations based on analytics."""
        recommendations = []

        # Analyze recent trends
        trends = self.generate_trends_analysis(24)
        recovery_metrics = self.generate_recovery_metrics(24)
        hotspots = self.identify_error_hotspots(24)

        # Recommendation based on trends
        increasing_trends = [t for t in trends if t.trend_direction == "increasing"]
        if increasing_trends:
            categories = ", ".join(t.category for t in increasing_trends[:3])
            recommendations.append(
                f"Error rates are increasing for: {categories}. "
                f"Consider investigating root causes and implementing preventive measures."
            )

        # Recommendation based on recovery success rate
        if recovery_metrics.success_rate < 0.7:
            recommendations.append(
                f"Recovery success rate is {recovery_metrics.success_rate:.1%}. "
                f"Consider improving error handling strategies and adding more fallback options."
            )

        # Recommendation based on hotspots
        if hotspots:
            top_hotspot = hotspots[0]
            recommendations.append(
                f"High error frequency detected in '{top_hotspot.location}' "
                f"({top_hotspot.error_count} errors). Consider focused debugging and optimization."
            )

        # Recommendation based on error patterns
        top_messages = self.get_top_error_messages(5)
        if top_messages and top_messages[0][1] > 5:
            recommendations.append(
                f"Most common error: '{top_messages[0][0]}' ({top_messages[0][1]} occurrences). "
                f"Consider implementing specific handling for this error pattern."
            )

        # General recommendations if no specific issues found
        if not recommendations:
            recommendations.append(
                "Error patterns appear normal. Continue monitoring and maintain current error handling practices."
            )

        return recommendations

    def generate_comprehensive_report(self, time_period_hours: int = 24) -> AnalyticsReport:
        """Generate comprehensive analytics report."""
        cutoff_time = time.time() - (time_period_hours * 3600)
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] > cutoff_time
        ]

        report = AnalyticsReport(
            generated_at=time.time(),
            time_period=f"{time_period_hours} hours",
            total_errors=len(recent_errors),
            error_trends=self.generate_trends_analysis(time_period_hours),
            recovery_metrics=self.generate_recovery_metrics(time_period_hours),
            error_hotspots=self.identify_error_hotspots(time_period_hours),
            top_error_messages=self.get_top_error_messages(10, time_period_hours),
            recommendations=self.generate_recommendations(),
        )

        return report

    def export_report(self, report: AnalyticsReport, file_path: str | None = None) -> dict[str, Any]:
        """Export analytics report to file and return as dictionary."""
        report_dict = asdict(report)
        
        # Add human-readable timestamps
        report_dict["generated_at_readable"] = datetime.fromtimestamp(
            report.generated_at
        ).isoformat()

        if file_path:
            with open(file_path, "w") as f:
                json.dump(report_dict, f, indent=2, default=str)

        return report_dict

    def save_analytics_data(self) -> None:
        """Save analytics data to persistent storage."""
        if not self.project_path:
            return

        analytics_dir = Path(self.project_path) / ".dev_agent" / "analytics"
        analytics_dir.mkdir(parents=True, exist_ok=True)

        # Save error history
        error_history_file = analytics_dir / "error_history.json"
        with open(error_history_file, "w") as f:
            json.dump(list(self.error_history), f, indent=2, default=str)

        # Save recovery history
        recovery_history_file = analytics_dir / "recovery_history.json"
        with open(recovery_history_file, "w") as f:
            json.dump(list(self.recovery_history), f, indent=2, default=str)

    def load_analytics_data(self) -> None:
        """Load analytics data from persistent storage."""
        if not self.project_path:
            return

        analytics_dir = Path(self.project_path) / ".dev_agent" / "analytics"
        
        # Load error history
        error_history_file = analytics_dir / "error_history.json"
        if error_history_file.exists():
            try:
                with open(error_history_file) as f:
                    error_data = json.load(f)
                    self.error_history.extend(error_data)
            except Exception as e:
                # Log error but continue
                pass

        # Load recovery history
        recovery_history_file = analytics_dir / "recovery_history.json"
        if recovery_history_file.exists():
            try:
                with open(recovery_history_file) as f:
                    recovery_data = json.load(f)
                    self.recovery_history.extend(recovery_data)
            except Exception as e:
                # Log error but continue
                pass

    def _normalize_message(self, message: str) -> str:
        """Normalize error message for pattern matching."""
        import re
        
        # Remove specific details like file paths, numbers, etc.
        normalized = message.lower()
        
        # Replace file paths
        normalized = re.sub(r'/[^\s]+', '<path>', normalized)
        # Replace numbers
        normalized = re.sub(r'\d+', '<number>', normalized)
        # Replace quoted strings
        normalized = re.sub(r'"[^"]*"', '<string>', normalized)
        # Replace URLs
        normalized = re.sub(r'https?://[^\s]+', '<url>', normalized)
        # Replace UUIDs and hashes
        normalized = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<uuid>', normalized)
        normalized = re.sub(r'[a-f0-9]{32,}', '<hash>', normalized)
        
        return normalized.strip()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self.analytics_cache:
            return False
        
        # For simplicity, we'll use a time-based cache invalidation
        # In a real implementation, you might want more sophisticated cache management
        return hasattr(self, '_cache_timestamp') and (
            time.time() - getattr(self, '_cache_timestamp', 0) < self.cache_ttl
        )

    def _invalidate_cache(self) -> None:
        """Invalidate analytics cache."""
        self.analytics_cache.clear()
        self._cache_timestamp = time.time()


class ErrorReportGenerator:
    """Generates formatted error reports for different audiences."""

    def __init__(self, analytics_engine: ErrorAnalyticsEngine):
        self.analytics_engine = analytics_engine

    def generate_summary_report(self, time_period_hours: int = 24) -> str:
        """Generate a concise summary report."""
        report = self.analytics_engine.generate_comprehensive_report(time_period_hours)
        
        summary = f"""
ERROR ANALYTICS SUMMARY ({report.time_period})
Generated: {datetime.fromtimestamp(report.generated_at).strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
- Total Errors: {report.total_errors}
- Recovery Success Rate: {report.recovery_metrics.success_rate:.1%}
- Average Recovery Time: {report.recovery_metrics.average_recovery_time:.1f}s

TOP ERROR CATEGORIES:
"""
        
        # Add top error categories from trends
        for trend in sorted(report.error_trends, key=lambda x: sum(x.hourly_counts), reverse=True)[:3]:
            total_count = sum(trend.hourly_counts)
            summary += f"- {trend.category.title()}: {total_count} errors ({trend.trend_direction})\n"

        if report.error_hotspots:
            summary += f"\nTOP ERROR HOTSPOT:\n- {report.error_hotspots[0].location}: {report.error_hotspots[0].error_count} errors\n"

        if report.recommendations:
            summary += f"\nKEY RECOMMENDATIONS:\n"
            for i, rec in enumerate(report.recommendations[:2], 1):
                summary += f"{i}. {rec}\n"

        return summary

    def generate_detailed_report(self, time_period_hours: int = 24) -> str:
        """Generate a detailed technical report."""
        report = self.analytics_engine.generate_comprehensive_report(time_period_hours)
        
        detailed = f"""
DETAILED ERROR ANALYTICS REPORT
Generated: {datetime.fromtimestamp(report.generated_at).strftime('%Y-%m-%d %H:%M:%S')}
Time Period: {report.time_period}

EXECUTIVE SUMMARY:
Total Errors: {report.total_errors}
Recovery Attempts: {report.recovery_metrics.total_attempts}
Successful Recoveries: {report.recovery_metrics.successful_recoveries}
Failed Recoveries: {report.recovery_metrics.failed_recoveries}
Overall Success Rate: {report.recovery_metrics.success_rate:.1%}

ERROR TRENDS:
"""
        
        for trend in report.error_trends:
            total_errors = sum(trend.hourly_counts)
            detailed += f"""
{trend.category.upper()}:
- Total Errors: {total_errors}
- Trend: {trend.trend_direction}
- Peak Hour: {trend.peak_hour}
- Hourly Distribution: {trend.hourly_counts}
"""

        detailed += "\nERROR HOTSPOTS:\n"
        for i, hotspot in enumerate(report.error_hotspots[:5], 1):
            detailed += f"""
{i}. {hotspot.location}:
   - Error Count: {hotspot.error_count}
   - Error Types: {hotspot.error_types}
   - Severity Distribution: {hotspot.severity_distribution}
   - Duration: {datetime.fromtimestamp(hotspot.first_occurrence).strftime('%H:%M')} - {datetime.fromtimestamp(hotspot.last_occurrence).strftime('%H:%M')}
"""

        detailed += "\nTOP ERROR MESSAGES:\n"
        for i, (message, count) in enumerate(report.top_error_messages[:5], 1):
            detailed += f"{i}. {message} ({count} occurrences)\n"

        detailed += "\nRECOVERY METHODS:\n"
        for method, count in report.recovery_metrics.recovery_methods.items():
            detailed += f"- {method}: {count} attempts\n"

        detailed += "\nRECOMMendations:\n"
        for i, rec in enumerate(report.recommendations, 1):
            detailed += f"{i}. {rec}\n"

        return detailed

    def generate_dashboard_data(self, time_period_hours: int = 24) -> dict[str, Any]:
        """Generate data suitable for dashboard visualization."""
        report = self.analytics_engine.generate_comprehensive_report(time_period_hours)
        
        dashboard_data = {
            "summary": {
                "total_errors": report.total_errors,
                "success_rate": report.recovery_metrics.success_rate,
                "avg_recovery_time": report.recovery_metrics.average_recovery_time,
            },
            "trends": {
                "categories": [trend.category for trend in report.error_trends],
                "hourly_data": {
                    trend.category: trend.hourly_counts for trend in report.error_trends
                },
                "trend_directions": {
                    trend.category: trend.trend_direction for trend in report.error_trends
                },
            },
            "hotspots": [
                {
                    "location": hotspot.location,
                    "count": hotspot.error_count,
                    "types": hotspot.error_types,
                }
                for hotspot in report.error_hotspots[:10]
            ],
            "top_errors": [
                {"message": msg, "count": count}
                for msg, count in report.top_error_messages[:10]
            ],
            "recovery_methods": report.recovery_metrics.recovery_methods,
            "recommendations": report.recommendations,
        }
        
        return dashboard_data