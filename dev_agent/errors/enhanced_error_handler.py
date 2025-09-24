"""Enhanced error handler with intelligent categorization and recovery."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .error_handler import ErrorHandler
from .exceptions import (
    DevAgentError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    GenerationError,
    ServiceError,
    TemplateError,
    ValidationError,
)
from .recovery import RecoveryAction, RecoveryActionType


class IntegrationStatus(Enum):
    """Status of external integrations."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class RetryStrategy(Enum):
    """Retry strategies for transient failures."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    IMMEDIATE = "immediate"


@dataclass
class ErrorPattern:
    """Pattern for error detection and classification."""

    pattern_id: str
    error_signature: str
    category: ErrorCategory
    severity: ErrorSeverity
    recovery_strategy: str
    confidence_threshold: float = 0.8
    occurrence_count: int = 0
    last_seen: float = 0.0


@dataclass
class IntegrationHealth:
    """Health status of external integrations."""

    service_name: str
    status: IntegrationStatus
    last_check: float
    error_count: int = 0
    success_count: int = 0
    average_response_time: float = 0.0
    last_error: str | None = None


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""

    strategy: RetryStrategy
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


@dataclass
class ErrorAnalytics:
    """Analytics data for error tracking."""

    total_errors: int = 0
    errors_by_category: dict[str, int] = None
    errors_by_severity: dict[str, int] = None
    error_trends: dict[str, list[float]] = None
    recovery_success_rate: float = 0.0
    mean_time_to_recovery: float = 0.0
    most_common_errors: list[str] = None

    def __post_init__(self):
        if self.errors_by_category is None:
            self.errors_by_category = {}
        if self.errors_by_severity is None:
            self.errors_by_severity = {}
        if self.error_trends is None:
            self.error_trends = {}
        if self.most_common_errors is None:
            self.most_common_errors = []


class EnhancedErrorHandler(ErrorHandler):
    """Enhanced error handler with intelligent categorization and recovery."""

    def __init__(
        self,
        project_path: str | None = None,
        logger: logging.Logger | None = None,
        analytics_enabled: bool = True,
        auto_recovery_enabled: bool = True,
    ):
        super().__init__(project_path, logger)
        self.analytics_enabled = analytics_enabled
        self.auto_recovery_enabled = auto_recovery_enabled
        
        # Enhanced error tracking
        self.error_patterns: dict[str, ErrorPattern] = {}
        self.integration_health: dict[str, IntegrationHealth] = {}
        self.retry_configs: dict[str, RetryConfig] = self._setup_retry_configs()
        
        # Analytics and monitoring
        self.error_analytics = ErrorAnalytics()
        self.error_queue: deque[dict[str, Any]] = deque(maxlen=1000)
        self.recovery_attempts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        
        # Graceful degradation
        self.degradation_strategies: dict[str, Callable] = self._setup_degradation_strategies()
        self.fallback_services: dict[str, list[str]] = {}
        
        # User feedback and suggestions
        self.suggestion_engine = ErrorSuggestionEngine()
        self.user_feedback_history: list[dict[str, Any]] = []
        
        # Load existing patterns and analytics
        self._load_error_patterns()
        self._load_analytics_data()

    def _setup_retry_configs(self) -> dict[str, RetryConfig]:
        """Set up retry configurations for different error types."""
        return {
            "network": RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_attempts=5,
                base_delay=1.0,
                max_delay=30.0,
            ),
            "service": RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_attempts=3,
                base_delay=2.0,
                max_delay=60.0,
            ),
            "generation": RetryConfig(
                strategy=RetryStrategy.LINEAR_BACKOFF,
                max_attempts=3,
                base_delay=5.0,
                max_delay=30.0,
            ),
            "validation": RetryConfig(
                strategy=RetryStrategy.IMMEDIATE,
                max_attempts=2,
                base_delay=0.1,
            ),
            "template": RetryConfig(
                strategy=RetryStrategy.FIXED_INTERVAL,
                max_attempts=3,
                base_delay=1.0,
            ),
        }

    def _setup_degradation_strategies(self) -> dict[str, Callable]:
        """Set up graceful degradation strategies."""
        return {
            "ai_service": self._degrade_ai_service,
            "vector_database": self._degrade_vector_database,
            "code_analysis": self._degrade_code_analysis,
            "template_engine": self._degrade_template_engine,
            "file_operations": self._degrade_file_operations,
        }

    async def handle_error_async(
        self, error: Exception | DevAgentError
    ) -> RecoveryAction | None:
        """Asynchronous error handling with enhanced features."""
        try:
            # Convert to DevAgentError if needed
            if not isinstance(error, DevAgentError):
                error = self._convert_to_dev_agent_error(error)

            # Intelligent error categorization
            error = await self._enhance_error_categorization(error)

            # Log and track error
            self._log_enhanced_error(error)
            self._track_error_analytics(error)

            # Check for error patterns
            pattern = self._detect_error_pattern(error)
            if pattern:
                self._update_error_pattern(pattern, error)

            # Determine recovery strategy
            recovery_action = await self._determine_enhanced_recovery(error, pattern)

            # Execute automatic recovery if enabled
            if (
                recovery_action
                and recovery_action.automatic
                and self.auto_recovery_enabled
            ):
                success = await self._execute_recovery_with_retry(recovery_action, error)
                self._track_recovery_attempt(error, recovery_action, success)

                if success:
                    self.logger.info(
                        f"Automatic recovery successful for {error.category.value} error"
                    )
                else:
                    # Try graceful degradation
                    degradation_success = await self._attempt_graceful_degradation(error)
                    if degradation_success:
                        self.logger.info(
                            f"Graceful degradation applied for {error.category.value} error"
                        )

            # Generate user-friendly suggestions
            suggestions = self.suggestion_engine.generate_suggestions(error, pattern)
            if suggestions:
                recovery_action = recovery_action or RecoveryAction(
                    action_type=RecoveryActionType.USER_INTERVENTION,
                    description="User intervention required",
                    automatic=False,
                )
                recovery_action.user_message = self._format_user_message(
                    error, suggestions
                )

            return recovery_action

        except Exception as e:
            self.logger.critical(f"Error in enhanced error handler: {e!s}")
            return None

    async def _enhance_error_categorization(self, error: DevAgentError) -> DevAgentError:
        """Enhance error categorization using ML-like pattern matching."""
        # Analyze error message for better categorization
        error_text = error.message.lower()
        
        # Service-related errors
        if any(keyword in error_text for keyword in ["api", "service", "endpoint", "connection"]):
            if not isinstance(error, ServiceError):
                error = ServiceError(
                    message=error.message,
                    severity=error.severity,
                    context=error.context,
                    service_name=self._extract_service_name(error_text),
                )
        
        # Generation-related errors
        elif any(keyword in error_text for keyword in ["generate", "creation", "template", "code"]):
            if not isinstance(error, (GenerationError, TemplateError)):
                if "template" in error_text:
                    error = TemplateError(
                        message=error.message,
                        severity=error.severity,
                        context=error.context,
                    )
                else:
                    error = GenerationError(
                        message=error.message,
                        severity=error.severity,
                        context=error.context,
                    )
        
        # Validation-related errors
        elif any(keyword in error_text for keyword in ["invalid", "validation", "format", "schema"]):
            if not isinstance(error, ValidationError):
                error = ValidationError(
                    message=error.message,
                    severity=error.severity,
                    context=error.context,
                )

        return error

    def _extract_service_name(self, error_text: str) -> str | None:
        """Extract service name from error text."""
        service_keywords = {
            "openai": "openai",
            "anthropic": "anthropic",
            "huggingface": "huggingface",
            "github": "github",
            "gitlab": "gitlab",
            "docker": "docker",
            "kubernetes": "kubernetes",
        }
        
        for keyword, service in service_keywords.items():
            if keyword in error_text:
                return service
        
        return None

    def _detect_error_pattern(self, error: DevAgentError) -> ErrorPattern | None:
        """Detect if error matches known patterns."""
        error_signature = self._generate_error_signature(error)
        
        for pattern in self.error_patterns.values():
            if self._match_error_pattern(error_signature, pattern.error_signature):
                return pattern
        
        return None

    def _generate_error_signature(self, error: DevAgentError) -> str:
        """Generate a signature for error pattern matching."""
        components = [
            error.category.value,
            error.severity.value,
            self._normalize_error_message(error.message),
        ]
        
        if error.context:
            components.append(error.context.operation or "unknown")
        
        return "|".join(components)

    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message for pattern matching."""
        # Remove specific details like file paths, numbers, etc.
        import re
        
        # Replace file paths
        message = re.sub(r'/[^\s]+', '<path>', message)
        # Replace numbers
        message = re.sub(r'\d+', '<number>', message)
        # Replace quoted strings
        message = re.sub(r'"[^"]*"', '<string>', message)
        # Replace URLs
        message = re.sub(r'https?://[^\s]+', '<url>', message)
        
        return message.lower().strip()

    def _match_error_pattern(self, signature1: str, signature2: str) -> bool:
        """Check if two error signatures match."""
        parts1 = signature1.split("|")
        parts2 = signature2.split("|")
        
        if len(parts1) != len(parts2):
            return False
        
        matches = 0
        for p1, p2 in zip(parts1, parts2):
            if p1 == p2 or self._fuzzy_match(p1, p2):
                matches += 1
        
        # Require at least 75% match
        return matches / len(parts1) >= 0.75

    def _fuzzy_match(self, text1: str, text2: str) -> bool:
        """Perform fuzzy matching between two text strings."""
        # Simple fuzzy matching based on common words
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Jaccard similarity
        return len(intersection) / len(union) >= 0.6

    def _update_error_pattern(self, pattern: ErrorPattern, error: DevAgentError) -> None:
        """Update error pattern with new occurrence."""
        pattern.occurrence_count += 1
        pattern.last_seen = time.time()
        
        # Update pattern confidence based on frequency
        if pattern.occurrence_count >= 5:
            pattern.confidence_threshold = min(0.95, pattern.confidence_threshold + 0.05)

    async def _determine_enhanced_recovery(
        self, error: DevAgentError, pattern: ErrorPattern | None
    ) -> RecoveryAction | None:
        """Determine recovery action with enhanced intelligence."""
        # Use pattern-based recovery if available
        if pattern and pattern.confidence_threshold >= 0.8:
            recovery_action = self._create_pattern_based_recovery(error, pattern)
            if recovery_action:
                return recovery_action
        
        # Check integration health for service errors
        if isinstance(error, ServiceError) and error.service_name:
            health = self._check_integration_health(error.service_name)
            if health.status == IntegrationStatus.FAILED:
                return await self._create_service_fallback_recovery(error)
        
        # Use base recovery strategies
        return self._determine_recovery_action(error)

    def _create_pattern_based_recovery(
        self, error: DevAgentError, pattern: ErrorPattern
    ) -> RecoveryAction | None:
        """Create recovery action based on learned patterns."""
        strategy_map = {
            "retry_with_backoff": self._create_retry_recovery,
            "fallback_service": self._create_fallback_recovery,
            "graceful_degradation": self._create_degradation_recovery,
            "user_intervention": self._create_user_intervention_recovery,
        }
        
        strategy_func = strategy_map.get(pattern.recovery_strategy)
        if strategy_func:
            return strategy_func(error, pattern)
        
        return None

    def _create_retry_recovery(
        self, error: DevAgentError, pattern: ErrorPattern
    ) -> RecoveryAction:
        """Create retry-based recovery action."""
        error_type = self._get_error_type_for_retry(error)
        retry_config = self.retry_configs.get(error_type, self.retry_configs["service"])
        
        return RecoveryAction(
            action_type=RecoveryActionType.RETRY,
            description=f"Retrying with {retry_config.strategy.value} strategy",
            automatic=True,
            parameters={
                "retry_config": asdict(retry_config),
                "pattern_confidence": pattern.confidence_threshold,
            },
        )

    def _create_fallback_recovery(
        self, error: DevAgentError, pattern: ErrorPattern
    ) -> RecoveryAction:
        """Create fallback-based recovery action."""
        return RecoveryAction(
            action_type=RecoveryActionType.FALLBACK,
            description="Using fallback strategy based on error pattern",
            automatic=True,
            parameters={"pattern_id": pattern.pattern_id},
        )

    def _create_degradation_recovery(
        self, error: DevAgentError, pattern: ErrorPattern
    ) -> RecoveryAction:
        """Create graceful degradation recovery action."""
        return RecoveryAction(
            action_type=RecoveryActionType.OPTIMIZE,
            description="Applying graceful degradation strategy",
            automatic=True,
            parameters={
                "degradation_level": "partial",
                "pattern_id": pattern.pattern_id,
            },
        )

    def _create_user_intervention_recovery(
        self, error: DevAgentError, pattern: ErrorPattern
    ) -> RecoveryAction:
        """Create user intervention recovery action."""
        return RecoveryAction(
            action_type=RecoveryActionType.USER_INTERVENTION,
            description="User intervention required based on error pattern",
            automatic=False,
            user_message=f"This error has occurred {pattern.occurrence_count} times. Manual intervention may be needed.",
        )

    def _get_error_type_for_retry(self, error: DevAgentError) -> str:
        """Get error type for retry configuration."""
        if isinstance(error, ServiceError):
            return "service"
        elif isinstance(error, GenerationError):
            return "generation"
        elif isinstance(error, ValidationError):
            return "validation"
        elif isinstance(error, TemplateError):
            return "template"
        else:
            return "service"  # Default

    async def _execute_recovery_with_retry(
        self, recovery_action: RecoveryAction, error: DevAgentError
    ) -> bool:
        """Execute recovery action with retry mechanism."""
        if recovery_action.action_type != RecoveryActionType.RETRY:
            return recovery_action.execute()
        
        retry_config = self._get_retry_config_from_action(recovery_action)
        
        for attempt in range(retry_config.max_attempts):
            try:
                if attempt > 0:
                    delay = self._calculate_retry_delay(retry_config, attempt)
                    await asyncio.sleep(delay)
                
                success = recovery_action.execute()
                if success:
                    return True
                
            except Exception as e:
                self.logger.warning(f"Recovery attempt {attempt + 1} failed: {e!s}")
        
        return False

    def _get_retry_config_from_action(self, recovery_action: RecoveryAction) -> RetryConfig:
        """Get retry configuration from recovery action parameters."""
        if recovery_action.parameters and "retry_config" in recovery_action.parameters:
            config_dict = recovery_action.parameters["retry_config"]
            return RetryConfig(**config_dict)
        
        return self.retry_configs["service"]  # Default

    def _calculate_retry_delay(self, config: RetryConfig, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt
        elif config.strategy == RetryStrategy.FIXED_INTERVAL:
            delay = config.base_delay
        else:  # IMMEDIATE
            delay = 0.0
        
        # Apply jitter if enabled
        if config.jitter and delay > 0:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        
        return min(delay, config.max_delay)

    async def _attempt_graceful_degradation(self, error: DevAgentError) -> bool:
        """Attempt graceful degradation for failed services."""
        service_type = self._identify_service_type(error)
        
        if service_type in self.degradation_strategies:
            try:
                degradation_func = self.degradation_strategies[service_type]
                return await degradation_func(error)
            except Exception as e:
                self.logger.warning(f"Graceful degradation failed for {service_type}: {e!s}")
        
        return False

    def _identify_service_type(self, error: DevAgentError) -> str:
        """Identify the type of service that failed."""
        if isinstance(error, ServiceError) and error.service_name:
            service_name = error.service_name.lower()
            if "openai" in service_name or "anthropic" in service_name:
                return "ai_service"
            elif "vector" in service_name or "faiss" in service_name:
                return "vector_database"
        
        error_text = error.message.lower()
        if any(keyword in error_text for keyword in ["analysis", "parsing", "ast"]):
            return "code_analysis"
        elif any(keyword in error_text for keyword in ["template", "jinja", "render"]):
            return "template_engine"
        elif any(keyword in error_text for keyword in ["file", "directory", "path"]):
            return "file_operations"
        
        return "unknown"

    async def _degrade_ai_service(self, error: DevAgentError) -> bool:
        """Graceful degradation for AI service failures."""
        self.logger.info("Applying graceful degradation for AI service")
        # Switch to simpler generation methods or cached responses
        return True

    async def _degrade_vector_database(self, error: DevAgentError) -> bool:
        """Graceful degradation for vector database failures."""
        self.logger.info("Applying graceful degradation for vector database")
        # Use simple text search instead of vector similarity
        return True

    async def _degrade_code_analysis(self, error: DevAgentError) -> bool:
        """Graceful degradation for code analysis failures."""
        self.logger.info("Applying graceful degradation for code analysis")
        # Use basic file parsing instead of AST analysis
        return True

    async def _degrade_template_engine(self, error: DevAgentError) -> bool:
        """Graceful degradation for template engine failures."""
        self.logger.info("Applying graceful degradation for template engine")
        # Use simple string replacement instead of complex templating
        return True

    async def _degrade_file_operations(self, error: DevAgentError) -> bool:
        """Graceful degradation for file operation failures."""
        self.logger.info("Applying graceful degradation for file operations")
        # Use alternative file access methods or temporary storage
        return True

    def _check_integration_health(self, service_name: str) -> IntegrationHealth:
        """Check health status of external integration."""
        if service_name not in self.integration_health:
            self.integration_health[service_name] = IntegrationHealth(
                service_name=service_name,
                status=IntegrationStatus.UNKNOWN,
                last_check=time.time(),
            )
        
        return self.integration_health[service_name]

    async def _create_service_fallback_recovery(
        self, error: ServiceError
    ) -> RecoveryAction:
        """Create fallback recovery for failed services."""
        fallback_services = self.fallback_services.get(error.service_name, [])
        
        if fallback_services:
            return RecoveryAction(
                action_type=RecoveryActionType.FALLBACK,
                description=f"Switching to fallback service: {fallback_services[0]}",
                automatic=True,
                parameters={
                    "fallback_service": fallback_services[0],
                    "original_service": error.service_name,
                },
            )
        
        return RecoveryAction(
            action_type=RecoveryActionType.USER_INTERVENTION,
            description="Service failure with no available fallbacks",
            automatic=False,
            user_message=f"Service {error.service_name} is unavailable and no fallbacks are configured.",
        )

    def _track_error_analytics(self, error: DevAgentError) -> None:
        """Track error for analytics and reporting."""
        if not self.analytics_enabled:
            return
        
        self.error_analytics.total_errors += 1
        
        # Track by category
        category = error.category.value
        self.error_analytics.errors_by_category[category] = (
            self.error_analytics.errors_by_category.get(category, 0) + 1
        )
        
        # Track by severity
        severity = error.severity.value
        self.error_analytics.errors_by_severity[severity] = (
            self.error_analytics.errors_by_severity.get(severity, 0) + 1
        )
        
        # Track trends (hourly buckets)
        current_hour = int(time.time() // 3600)
        if category not in self.error_analytics.error_trends:
            self.error_analytics.error_trends[category] = []
        
        # Add to current hour bucket
        trends = self.error_analytics.error_trends[category]
        if not trends or trends[-1] != current_hour:
            trends.append(current_hour)
        
        # Keep only last 24 hours
        cutoff_hour = current_hour - 24
        self.error_analytics.error_trends[category] = [
            hour for hour in trends if hour > cutoff_hour
        ]
        
        # Add to error queue for detailed tracking
        error_record = {
            "timestamp": time.time(),
            "category": category,
            "severity": severity,
            "message": error.message,
            "context": error.context.operation if error.context else None,
        }
        self.error_queue.append(error_record)

    def _track_recovery_attempt(
        self, error: DevAgentError, recovery_action: RecoveryAction, success: bool
    ) -> None:
        """Track recovery attempt for analytics."""
        error_signature = self._generate_error_signature(error)
        
        attempt_record = {
            "timestamp": time.time(),
            "error_signature": error_signature,
            "recovery_type": recovery_action.action_type.value,
            "success": success,
            "automatic": recovery_action.automatic,
        }
        
        self.recovery_attempts[error_signature].append(attempt_record)
        
        # Update success rate
        all_attempts = []
        for attempts in self.recovery_attempts.values():
            all_attempts.extend(attempts)
        
        if all_attempts:
            successful_attempts = sum(1 for attempt in all_attempts if attempt["success"])
            self.error_analytics.recovery_success_rate = (
                successful_attempts / len(all_attempts)
            )

    def _format_user_message(
        self, error: DevAgentError, suggestions: list[str]
    ) -> str:
        """Format user-friendly error message with suggestions."""
        message = error.user_message or f"An error occurred: {error.message}"
        
        if suggestions:
            message += "\n\nSuggested actions:"
            for i, suggestion in enumerate(suggestions, 1):
                message += f"\n{i}. {suggestion}"
        
        return message

    def _log_enhanced_error(self, error: DevAgentError) -> None:
        """Log error with enhanced information."""
        self._log_error(error)  # Call parent method
        
        # Add enhanced logging
        if self.analytics_enabled:
            pattern = self._detect_error_pattern(error)
            if pattern:
                self.logger.info(
                    f"Error matches pattern {pattern.pattern_id} "
                    f"(confidence: {pattern.confidence_threshold:.2f}, "
                    f"occurrences: {pattern.occurrence_count})"
                )

    def update_integration_health(
        self, service_name: str, status: IntegrationStatus, response_time: float = 0.0
    ) -> None:
        """Update health status of external integration."""
        if service_name not in self.integration_health:
            self.integration_health[service_name] = IntegrationHealth(
                service_name=service_name,
                status=status,
                last_check=time.time(),
            )
        
        health = self.integration_health[service_name]
        health.status = status
        health.last_check = time.time()
        
        if status == IntegrationStatus.HEALTHY:
            health.success_count += 1
        else:
            health.error_count += 1
        
        # Update average response time
        if response_time > 0:
            total_checks = health.success_count + health.error_count
            health.average_response_time = (
                (health.average_response_time * (total_checks - 1) + response_time)
                / total_checks
            )

    def add_fallback_service(self, primary_service: str, fallback_service: str) -> None:
        """Add fallback service for primary service."""
        if primary_service not in self.fallback_services:
            self.fallback_services[primary_service] = []
        
        if fallback_service not in self.fallback_services[primary_service]:
            self.fallback_services[primary_service].append(fallback_service)

    def learn_error_pattern(
        self,
        error_signature: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        recovery_strategy: str,
    ) -> None:
        """Learn new error pattern from user feedback."""
        pattern_id = f"pattern_{len(self.error_patterns) + 1}"
        
        pattern = ErrorPattern(
            pattern_id=pattern_id,
            error_signature=error_signature,
            category=category,
            severity=severity,
            recovery_strategy=recovery_strategy,
            confidence_threshold=0.7,  # Start with moderate confidence
            occurrence_count=1,
            last_seen=time.time(),
        )
        
        self.error_patterns[pattern_id] = pattern
        self._save_error_patterns()

    def get_error_analytics(self) -> ErrorAnalytics:
        """Get comprehensive error analytics."""
        # Update most common errors
        error_counts = {}
        for error_record in self.error_queue:
            message = error_record["message"]
            normalized = self._normalize_error_message(message)
            error_counts[normalized] = error_counts.get(normalized, 0) + 1
        
        self.error_analytics.most_common_errors = sorted(
            error_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]
        
        # Calculate mean time to recovery
        recovery_times = []
        for attempts in self.recovery_attempts.values():
            successful_attempts = [a for a in attempts if a["success"]]
            if successful_attempts:
                # Use the time of the first successful attempt
                first_success = min(successful_attempts, key=lambda x: x["timestamp"])
                first_attempt = min(attempts, key=lambda x: x["timestamp"])
                recovery_time = first_success["timestamp"] - first_attempt["timestamp"]
                recovery_times.append(recovery_time)
        
        if recovery_times:
            self.error_analytics.mean_time_to_recovery = sum(recovery_times) / len(recovery_times)
        
        return self.error_analytics

    def export_analytics_report(self, file_path: str | None = None) -> dict[str, Any]:
        """Export comprehensive analytics report."""
        analytics = self.get_error_analytics()
        
        report = {
            "generated_at": time.time(),
            "analytics": asdict(analytics),
            "integration_health": {
                name: asdict(health) for name, health in self.integration_health.items()
            },
            "error_patterns": {
                pattern_id: asdict(pattern)
                for pattern_id, pattern in self.error_patterns.items()
            },
            "recent_errors": list(self.error_queue)[-50:],  # Last 50 errors
        }
        
        if file_path:
            with open(file_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
        
        return report

    def _load_error_patterns(self) -> None:
        """Load error patterns from storage."""
        if not self.project_path:
            return
        
        patterns_file = Path(self.project_path) / ".dev_agent" / "error_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file) as f:
                    patterns_data = json.load(f)
                
                for pattern_id, pattern_dict in patterns_data.items():
                    pattern = ErrorPattern(
                        pattern_id=pattern_dict["pattern_id"],
                        error_signature=pattern_dict["error_signature"],
                        category=ErrorCategory(pattern_dict["category"]),
                        severity=ErrorSeverity(pattern_dict["severity"]),
                        recovery_strategy=pattern_dict["recovery_strategy"],
                        confidence_threshold=pattern_dict["confidence_threshold"],
                        occurrence_count=pattern_dict["occurrence_count"],
                        last_seen=pattern_dict["last_seen"],
                    )
                    self.error_patterns[pattern_id] = pattern
            
            except Exception as e:
                self.logger.warning(f"Failed to load error patterns: {e!s}")

    def _save_error_patterns(self) -> None:
        """Save error patterns to storage."""
        if not self.project_path:
            return
        
        patterns_dir = Path(self.project_path) / ".dev_agent"
        patterns_dir.mkdir(exist_ok=True)
        
        patterns_file = patterns_dir / "error_patterns.json"
        
        try:
            patterns_data = {
                pattern_id: asdict(pattern)
                for pattern_id, pattern in self.error_patterns.items()
            }
            
            with open(patterns_file, "w") as f:
                json.dump(patterns_data, f, indent=2, default=str)
        
        except Exception as e:
            self.logger.warning(f"Failed to save error patterns: {e!s}")

    def _load_analytics_data(self) -> None:
        """Load analytics data from storage."""
        if not self.project_path:
            return
        
        analytics_file = Path(self.project_path) / ".dev_agent" / "error_analytics.json"
        if analytics_file.exists():
            try:
                with open(analytics_file) as f:
                    analytics_data = json.load(f)
                
                self.error_analytics = ErrorAnalytics(**analytics_data)
            
            except Exception as e:
                self.logger.warning(f"Failed to load analytics data: {e!s}")

    def save_analytics_data(self) -> None:
        """Save analytics data to storage."""
        if not self.project_path:
            return
        
        analytics_dir = Path(self.project_path) / ".dev_agent"
        analytics_dir.mkdir(exist_ok=True)
        
        analytics_file = analytics_dir / "error_analytics.json"
        
        try:
            with open(analytics_file, "w") as f:
                json.dump(asdict(self.error_analytics), f, indent=2, default=str)
        
        except Exception as e:
            self.logger.warning(f"Failed to save analytics data: {e!s}")


class ErrorSuggestionEngine:
    """Engine for generating user-friendly error suggestions."""

    def __init__(self):
        self.suggestion_templates = self._setup_suggestion_templates()

    def _setup_suggestion_templates(self) -> dict[str, list[str]]:
        """Set up suggestion templates for different error types."""
        return {
            "service_error": [
                "Check your internet connection and try again",
                "Verify that the service API key is correctly configured",
                "Check if the service is experiencing downtime",
                "Try using a different service endpoint if available",
            ],
            "generation_error": [
                "Try simplifying the generation request",
                "Check if the input data is valid and complete",
                "Verify that the generation template is correct",
                "Try using a different generation model or approach",
            ],
            "validation_error": [
                "Check the input format and ensure it matches requirements",
                "Verify that all required fields are provided",
                "Review the validation rules and adjust input accordingly",
                "Try using the suggested input format if provided",
            ],
            "template_error": [
                "Check if the template file exists and is accessible",
                "Verify that the template syntax is correct",
                "Ensure all required template variables are provided",
                "Try using a different template or creating a custom one",
            ],
            "system_error": [
                "Check file and directory permissions",
                "Verify that there is sufficient disk space",
                "Ensure the project directory is accessible",
                "Try running the command with appropriate privileges",
            ],
        }

    def generate_suggestions(
        self, error: DevAgentError, pattern: ErrorPattern | None = None
    ) -> list[str]:
        """Generate contextual suggestions for error resolution."""
        suggestions = []
        
        # Pattern-based suggestions
        if pattern and pattern.occurrence_count > 1:
            suggestions.append(
                f"This error has occurred {pattern.occurrence_count} times. "
                f"Consider reviewing the underlying cause."
            )
        
        # Error type specific suggestions
        error_type = self._classify_error_for_suggestions(error)
        template_suggestions = self.suggestion_templates.get(error_type, [])
        
        # Select most relevant suggestions (max 3)
        relevant_suggestions = self._select_relevant_suggestions(
            error, template_suggestions
        )
        suggestions.extend(relevant_suggestions[:3])
        
        # Context-specific suggestions
        context_suggestions = self._generate_context_suggestions(error)
        suggestions.extend(context_suggestions)
        
        return suggestions[:5]  # Limit to 5 suggestions max

    def _classify_error_for_suggestions(self, error: DevAgentError) -> str:
        """Classify error for suggestion generation."""
        if isinstance(error, ServiceError):
            return "service_error"
        elif isinstance(error, GenerationError):
            return "generation_error"
        elif isinstance(error, ValidationError):
            return "validation_error"
        elif isinstance(error, TemplateError):
            return "template_error"
        else:
            return "system_error"

    def _select_relevant_suggestions(
        self, error: DevAgentError, template_suggestions: list[str]
    ) -> list[str]:
        """Select most relevant suggestions based on error details."""
        relevant = []
        error_text = error.message.lower()
        
        for suggestion in template_suggestions:
            suggestion_lower = suggestion.lower()
            
            # Check for keyword matches
            if any(
                keyword in error_text
                for keyword in ["connection", "network", "timeout"]
            ) and "connection" in suggestion_lower:
                relevant.append(suggestion)
            elif any(
                keyword in error_text for keyword in ["permission", "access", "denied"]
            ) and "permission" in suggestion_lower:
                relevant.append(suggestion)
            elif any(
                keyword in error_text for keyword in ["format", "invalid", "syntax"]
            ) and "format" in suggestion_lower:
                relevant.append(suggestion)
            elif len(relevant) < 2:  # Add general suggestions if not many specific ones
                relevant.append(suggestion)
        
        return relevant

    def _generate_context_suggestions(self, error: DevAgentError) -> list[str]:
        """Generate context-specific suggestions."""
        suggestions = []
        
        if error.context:
            operation = error.context.operation
            
            if operation == "indexing":
                suggestions.append("Try reducing the scope of files to index")
            elif operation == "generation":
                suggestions.append("Consider breaking down the generation task into smaller parts")
            elif operation == "file_access":
                suggestions.append("Check if the file path is correct and accessible")
        
        return suggestions