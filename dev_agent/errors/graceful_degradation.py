"""Graceful degradation strategies for failed integrations and services."""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .exceptions import DevAgentError, ServiceError


class DegradationLevel(Enum):
    """Levels of service degradation."""

    NONE = "none"
    MINIMAL = "minimal"
    PARTIAL = "partial"
    SIGNIFICANT = "significant"
    COMPLETE = "complete"


class ServiceType(Enum):
    """Types of services that can be degraded."""

    AI_SERVICE = "ai_service"
    VECTOR_DATABASE = "vector_database"
    CODE_ANALYSIS = "code_analysis"
    TEMPLATE_ENGINE = "template_engine"
    FILE_OPERATIONS = "file_operations"
    NETWORK_SERVICE = "network_service"
    CACHE_SERVICE = "cache_service"


@dataclass
class DegradationStrategy:
    """Configuration for a degradation strategy."""

    service_type: ServiceType
    degradation_level: DegradationLevel
    fallback_method: str
    performance_impact: float  # 0.0 to 1.0, where 1.0 is no impact
    feature_availability: float  # 0.0 to 1.0, where 1.0 is full availability
    description: str
    auto_recovery_enabled: bool = True
    recovery_check_interval: float = 60.0  # seconds


@dataclass
class ServiceHealth:
    """Health status of a service."""

    service_name: str
    service_type: ServiceType
    is_healthy: bool
    last_check: float
    failure_count: int
    success_count: int
    current_degradation: DegradationLevel
    recovery_attempts: int


class DegradationManager:
    """Manages graceful degradation of services."""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.service_health: dict[str, ServiceHealth] = {}
        self.degradation_strategies: dict[ServiceType, list[DegradationStrategy]] = {}
        self.active_degradations: dict[str, DegradationStrategy] = {}
        self.fallback_handlers: dict[str, Callable] = {}
        self.recovery_tasks: dict[str, asyncio.Task] = {}
        
        self._setup_default_strategies()

    def _setup_default_strategies(self) -> None:
        """Set up default degradation strategies for common services."""
        # AI Service degradation strategies
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.AI_SERVICE,
            degradation_level=DegradationLevel.MINIMAL,
            fallback_method="cached_responses",
            performance_impact=0.9,
            feature_availability=0.8,
            description="Use cached AI responses when available",
        ))
        
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.AI_SERVICE,
            degradation_level=DegradationLevel.PARTIAL,
            fallback_method="template_based_generation",
            performance_impact=0.7,
            feature_availability=0.6,
            description="Use template-based code generation instead of AI",
        ))
        
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.AI_SERVICE,
            degradation_level=DegradationLevel.SIGNIFICANT,
            fallback_method="static_templates",
            performance_impact=0.5,
            feature_availability=0.3,
            description="Use static templates with minimal customization",
        ))

        # Vector Database degradation strategies
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.VECTOR_DATABASE,
            degradation_level=DegradationLevel.MINIMAL,
            fallback_method="in_memory_cache",
            performance_impact=0.8,
            feature_availability=0.9,
            description="Use in-memory vector cache for recent queries",
        ))
        
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.VECTOR_DATABASE,
            degradation_level=DegradationLevel.PARTIAL,
            fallback_method="text_search",
            performance_impact=0.6,
            feature_availability=0.7,
            description="Use text-based search instead of vector similarity",
        ))
        
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.VECTOR_DATABASE,
            degradation_level=DegradationLevel.SIGNIFICANT,
            fallback_method="keyword_matching",
            performance_impact=0.4,
            feature_availability=0.4,
            description="Use simple keyword matching for code search",
        ))

        # Code Analysis degradation strategies
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.CODE_ANALYSIS,
            degradation_level=DegradationLevel.MINIMAL,
            fallback_method="cached_analysis",
            performance_impact=0.9,
            feature_availability=0.8,
            description="Use cached analysis results when available",
        ))
        
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.CODE_ANALYSIS,
            degradation_level=DegradationLevel.PARTIAL,
            fallback_method="basic_parsing",
            performance_impact=0.7,
            feature_availability=0.6,
            description="Use basic file parsing instead of AST analysis",
        ))
        
        self.add_degradation_strategy(DegradationStrategy(
            service_type=ServiceType.CODE_ANALYSIS,
            degradation_level=DegradationLevel.SIGNIFICANT,
            fallback_method="file_listing",
            performance_impact=0.5,
            feature_availability=0.3,
            description="Use simple file listing without analysis",
        ))

    def add_degradation_strategy(self, strategy: DegradationStrategy) -> None:
        """Add a degradation strategy for a service type."""
        if strategy.service_type not in self.degradation_strategies:
            self.degradation_strategies[strategy.service_type] = []
        
        self.degradation_strategies[strategy.service_type].append(strategy)
        
        # Sort strategies by degradation level (least degraded first)
        self.degradation_strategies[strategy.service_type].sort(
            key=lambda s: list(DegradationLevel).index(s.degradation_level)
        )

    def register_service(
        self, service_name: str, service_type: ServiceType, is_healthy: bool = True
    ) -> None:
        """Register a service for health monitoring."""
        self.service_health[service_name] = ServiceHealth(
            service_name=service_name,
            service_type=service_type,
            is_healthy=is_healthy,
            last_check=time.time(),
            failure_count=0,
            success_count=0,
            current_degradation=DegradationLevel.NONE,
            recovery_attempts=0,
        )

    def register_fallback_handler(
        self, fallback_method: str, handler: Callable
    ) -> None:
        """Register a fallback handler for a specific method."""
        self.fallback_handlers[fallback_method] = handler

    async def handle_service_failure(
        self, service_name: str, error: DevAgentError
    ) -> DegradationStrategy | None:
        """Handle service failure and apply appropriate degradation."""
        if service_name not in self.service_health:
            self.logger.warning(f"Unknown service failed: {service_name}")
            return None

        health = self.service_health[service_name]
        health.failure_count += 1
        health.is_healthy = False
        health.last_check = time.time()

        # Determine appropriate degradation level
        degradation_level = self._calculate_degradation_level(health)
        
        # Find appropriate strategy
        strategy = self._find_degradation_strategy(health.service_type, degradation_level)
        
        if strategy:
            await self._apply_degradation(service_name, strategy)
            
            # Start recovery monitoring if enabled
            if strategy.auto_recovery_enabled:
                await self._start_recovery_monitoring(service_name, strategy)
        
        return strategy

    def _calculate_degradation_level(self, health: ServiceHealth) -> DegradationLevel:
        """Calculate appropriate degradation level based on service health."""
        failure_rate = health.failure_count / max(health.failure_count + health.success_count, 1)
        
        if failure_rate < 0.1:
            return DegradationLevel.MINIMAL
        elif failure_rate < 0.3:
            return DegradationLevel.PARTIAL
        elif failure_rate < 0.7:
            return DegradationLevel.SIGNIFICANT
        else:
            return DegradationLevel.COMPLETE

    def _find_degradation_strategy(
        self, service_type: ServiceType, target_level: DegradationLevel
    ) -> DegradationStrategy | None:
        """Find appropriate degradation strategy for service type and level."""
        strategies = self.degradation_strategies.get(service_type, [])
        
        # Find strategy with matching or closest degradation level
        for strategy in strategies:
            if strategy.degradation_level == target_level:
                return strategy
        
        # If no exact match, find closest strategy
        level_values = list(DegradationLevel)
        target_index = level_values.index(target_level)
        
        best_strategy = None
        best_distance = float('inf')
        
        for strategy in strategies:
            strategy_index = level_values.index(strategy.degradation_level)
            distance = abs(strategy_index - target_index)
            
            if distance < best_distance:
                best_distance = distance
                best_strategy = strategy
        
        return best_strategy

    async def _apply_degradation(
        self, service_name: str, strategy: DegradationStrategy
    ) -> None:
        """Apply degradation strategy to service."""
        self.active_degradations[service_name] = strategy
        
        health = self.service_health[service_name]
        health.current_degradation = strategy.degradation_level
        
        self.logger.info(
            f"Applied {strategy.degradation_level.value} degradation to {service_name}: "
            f"{strategy.description}"
        )
        
        # Execute fallback handler if available
        if strategy.fallback_method in self.fallback_handlers:
            try:
                handler = self.fallback_handlers[strategy.fallback_method]
                await self._execute_fallback_handler(handler, service_name, strategy)
            except Exception as e:
                self.logger.error(f"Fallback handler failed for {service_name}: {e!s}")

    async def _execute_fallback_handler(
        self, handler: Callable, service_name: str, strategy: DegradationStrategy
    ) -> None:
        """Execute fallback handler with proper error handling."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(service_name, strategy)
            else:
                handler(service_name, strategy)
        except Exception as e:
            self.logger.error(f"Error executing fallback handler: {e!s}")
            raise

    async def _start_recovery_monitoring(
        self, service_name: str, strategy: DegradationStrategy
    ) -> None:
        """Start monitoring service for recovery."""
        if service_name in self.recovery_tasks:
            self.recovery_tasks[service_name].cancel()
        
        self.recovery_tasks[service_name] = asyncio.create_task(
            self._monitor_service_recovery(service_name, strategy)
        )

    async def _monitor_service_recovery(
        self, service_name: str, strategy: DegradationStrategy
    ) -> None:
        """Monitor service for recovery and restore normal operation."""
        health = self.service_health[service_name]
        
        while service_name in self.active_degradations:
            try:
                await asyncio.sleep(strategy.recovery_check_interval)
                
                # Attempt to check service health
                is_recovered = await self._check_service_recovery(service_name)
                
                if is_recovered:
                    await self._restore_service(service_name)
                    break
                else:
                    health.recovery_attempts += 1
                    
                    # Escalate degradation if recovery attempts fail
                    if health.recovery_attempts > 5:
                        await self._escalate_degradation(service_name)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring recovery for {service_name}: {e!s}")
                await asyncio.sleep(strategy.recovery_check_interval)

    async def _check_service_recovery(self, service_name: str) -> bool:
        """Check if service has recovered."""
        # This is a placeholder - in real implementation, this would
        # perform actual health checks specific to each service type
        health = self.service_health[service_name]
        
        # Simple recovery check - in practice, this would be service-specific
        try:
            # Simulate health check
            await asyncio.sleep(0.1)
            
            # For demo purposes, assume recovery after some attempts
            if health.recovery_attempts >= 3:
                return True
            
            return False
            
        except Exception:
            return False

    async def _restore_service(self, service_name: str) -> None:
        """Restore service to normal operation."""
        if service_name in self.active_degradations:
            strategy = self.active_degradations.pop(service_name)
            
            health = self.service_health[service_name]
            health.is_healthy = True
            health.current_degradation = DegradationLevel.NONE
            health.recovery_attempts = 0
            health.success_count += 1
            
            self.logger.info(f"Service {service_name} recovered from {strategy.degradation_level.value} degradation")
            
            # Cancel recovery monitoring
            if service_name in self.recovery_tasks:
                self.recovery_tasks[service_name].cancel()
                del self.recovery_tasks[service_name]

    async def _escalate_degradation(self, service_name: str) -> None:
        """Escalate degradation level if recovery continues to fail."""
        if service_name not in self.active_degradations:
            return
        
        current_strategy = self.active_degradations[service_name]
        health = self.service_health[service_name]
        
        # Find next level of degradation
        current_level_index = list(DegradationLevel).index(current_strategy.degradation_level)
        
        if current_level_index < len(DegradationLevel) - 1:
            next_level = list(DegradationLevel)[current_level_index + 1]
            next_strategy = self._find_degradation_strategy(health.service_type, next_level)
            
            if next_strategy:
                self.logger.warning(
                    f"Escalating degradation for {service_name} from "
                    f"{current_strategy.degradation_level.value} to {next_strategy.degradation_level.value}"
                )
                
                await self._apply_degradation(service_name, next_strategy)

    def report_service_success(self, service_name: str) -> None:
        """Report successful service operation."""
        if service_name in self.service_health:
            health = self.service_health[service_name]
            health.success_count += 1
            health.last_check = time.time()
            
            # If service was degraded but showing success, consider recovery
            if health.current_degradation != DegradationLevel.NONE:
                # Reset failure count on success
                health.failure_count = max(0, health.failure_count - 1)

    def get_service_status(self, service_name: str) -> dict[str, Any] | None:
        """Get current status of a service."""
        if service_name not in self.service_health:
            return None
        
        health = self.service_health[service_name]
        strategy = self.active_degradations.get(service_name)
        
        return {
            "service_name": service_name,
            "service_type": health.service_type.value,
            "is_healthy": health.is_healthy,
            "current_degradation": health.current_degradation.value,
            "failure_count": health.failure_count,
            "success_count": health.success_count,
            "recovery_attempts": health.recovery_attempts,
            "last_check": health.last_check,
            "active_strategy": {
                "fallback_method": strategy.fallback_method,
                "performance_impact": strategy.performance_impact,
                "feature_availability": strategy.feature_availability,
                "description": strategy.description,
            } if strategy else None,
        }

    def get_all_service_statuses(self) -> dict[str, dict[str, Any]]:
        """Get status of all registered services."""
        return {
            service_name: self.get_service_status(service_name)
            for service_name in self.service_health
        }

    def get_degradation_impact(self) -> dict[str, float]:
        """Get overall impact of current degradations."""
        if not self.active_degradations:
            return {"performance_impact": 1.0, "feature_availability": 1.0}
        
        total_performance = 1.0
        total_availability = 1.0
        
        for strategy in self.active_degradations.values():
            total_performance *= strategy.performance_impact
            total_availability *= strategy.feature_availability
        
        return {
            "performance_impact": total_performance,
            "feature_availability": total_availability,
        }

    async def shutdown(self) -> None:
        """Shutdown degradation manager and cleanup resources."""
        # Cancel all recovery tasks
        for task in self.recovery_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.recovery_tasks:
            await asyncio.gather(*self.recovery_tasks.values(), return_exceptions=True)
        
        self.recovery_tasks.clear()
        self.active_degradations.clear()


# Default fallback handlers for common services

async def cached_responses_fallback(service_name: str, strategy: DegradationStrategy) -> None:
    """Fallback handler for using cached AI responses."""
    # Implementation would access cached responses
    pass

async def template_based_generation_fallback(service_name: str, strategy: DegradationStrategy) -> None:
    """Fallback handler for template-based code generation."""
    # Implementation would use template engine instead of AI
    pass

async def in_memory_cache_fallback(service_name: str, strategy: DegradationStrategy) -> None:
    """Fallback handler for in-memory vector cache."""
    # Implementation would use in-memory cache for vector operations
    pass

async def text_search_fallback(service_name: str, strategy: DegradationStrategy) -> None:
    """Fallback handler for text-based search."""
    # Implementation would use text search instead of vector similarity
    pass

async def basic_parsing_fallback(service_name: str, strategy: DegradationStrategy) -> None:
    """Fallback handler for basic code parsing."""
    # Implementation would use simple parsing instead of AST analysis
    pass


def create_default_degradation_manager(logger: logging.Logger | None = None) -> DegradationManager:
    """Create degradation manager with default fallback handlers."""
    manager = DegradationManager(logger)
    
    # Register default fallback handlers
    manager.register_fallback_handler("cached_responses", cached_responses_fallback)
    manager.register_fallback_handler("template_based_generation", template_based_generation_fallback)
    manager.register_fallback_handler("in_memory_cache", in_memory_cache_fallback)
    manager.register_fallback_handler("text_search", text_search_fallback)
    manager.register_fallback_handler("basic_parsing", basic_parsing_fallback)
    
    return manager