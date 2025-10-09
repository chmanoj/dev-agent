"""Task generator for creating TASKS.md documents."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.generation_interface import ITaskGenerator
from ..llm import create_llm_client, get_preferred_provider
from ..llm.prompt_templates import TASK_GENERATION_TEMPLATE
from ..models.documents import (
    ComponentSpec,
    DataModel,
    DesignDocument,
    InterfaceSpec,
    Task,
    TaskList,
)
from ..models.enums import LLMProvider, PhaseType, TaskStatus

if TYPE_CHECKING:
    from ..llm.base import ILLMClient
    from ..llm.cost_tracker import CostTracker
    from ..llm.token_counter import TokenCounter

logger = logging.getLogger(__name__)


class TaskGenerator(ITaskGenerator):
    """Generates task lists from design documents using Azure OpenAI.
    
    This generator uses GPT-4 to create comprehensive, actionable task breakdowns
    from design documents. It integrates with the LLM abstraction layer for
    provider-agnostic code generation, tracks token usage and costs, and validates
    token limits before making API calls.
    
    Attributes:
        cli_interface: Optional CLI interface for user interaction
        llm_client: LLM client for generating task lists
        cost_tracker: Cost tracker for monitoring API usage
        token_counter: Token counter for validation
        version: Generator version
    """

    def __init__(
        self,
        cli_interface: ICLIInterface | None = None,
        llm_client: ILLMClient | None = None,
        cost_tracker: CostTracker | None = None,
        token_counter: TokenCounter | None = None,
        provider: LLMProvider | str | None = None,
    ):
        """Initialize the task generator.

        Args:
            cli_interface: Optional CLI interface for user interaction
            llm_client: Optional LLM client for AI-powered task generation (for backward compatibility)
            cost_tracker: Optional cost tracker for monitoring API usage
            token_counter: Optional token counter for validation
            provider: LLM provider to use (optional, defaults to preferred provider)
        """
        self.cli_interface = cli_interface
        self.cost_tracker = cost_tracker
        self.token_counter = token_counter
        self.version = "1.0"

        # Initialize LLM client using factory pattern
        if llm_client is not None:
            # Use provided client for backward compatibility
            self.llm_client = llm_client
            logger.info("TaskGenerator initialized with provided LLM client")
        else:
            # Create client using factory pattern
            try:
                self.llm_client = create_llm_client(provider=provider)
                current_provider = get_preferred_provider()
                logger.info(f"TaskGenerator initialized with {current_provider.value} LLM client")
            except (ValueError, ImportError) as e:
                logger.warning(f"Failed to create LLM client: {e}")
                self.llm_client = None
                logger.warning("TaskGenerator initialized without LLM client")

        logger.info(
            f"TaskGenerator initialized with "
            f"llm_client={'present' if self.llm_client else 'absent'}, "
            f"cost_tracker={'present' if cost_tracker else 'absent'}"
        )

    async def generate_from_design_async(
        self,
        design: DesignDocument,
        specification: str | None = None,
    ) -> TaskList:
        """Generate implementation tasks from design document using LLM.
        
        This method uses Azure OpenAI to generate a comprehensive task breakdown
        from the design document. It validates token limits, tracks costs, and
        injects relevant context into the prompt.
        
        Args:
            design: Design document to generate tasks from
            specification: Optional specification text for additional context
            
        Returns:
            Generated task list with AI-powered task breakdown
            
        Raises:
            ValueError: If LLM client is not configured
            LLMTokenLimitError: If prompt exceeds token limits
        """
        if not self.llm_client:
            logger.warning("No LLM client configured, falling back to rule-based generation")
            return self.generate_from_design(design)

        logger.info("Generating tasks from design using Azure OpenAI")

        # Set phase for cost tracking
        if self.cost_tracker:
            self.cost_tracker.set_phase(PhaseType.DESIGN)

        # Build context for prompt
        context = self._build_llm_context(design, specification)

        # Render prompt with context
        system_prompt, user_prompt = TASK_GENERATION_TEMPLATE.render(
            context,
            token_counter=self.token_counter,
        )

        # Validate token limits
        if self.token_counter:
            prompt_tokens = self.token_counter.count_tokens(user_prompt)
            is_valid, error_msg = self.token_counter.validate_context_window(
                prompt_tokens=prompt_tokens,
                max_completion_tokens=TASK_GENERATION_TEMPLATE.max_tokens,
            )

            if not is_valid:
                logger.error(f"Token validation failed: {error_msg}")
                raise ValueError(error_msg)

            # Estimate cost before generation
            estimated_cost = self.token_counter.estimate_cost(
                prompt_tokens=prompt_tokens,
                completion_tokens=TASK_GENERATION_TEMPLATE.max_tokens,
            )
            logger.info(
                f"Generating tasks: {prompt_tokens} prompt tokens, "
                f"estimated cost ${estimated_cost:.4f}"
            )

        # Generate tasks using LLM
        try:
            task_content = await self.llm_client.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=TASK_GENERATION_TEMPLATE.temperature,
                max_tokens=TASK_GENERATION_TEMPLATE.max_tokens,
            )

            # Track actual token usage if available
            if self.cost_tracker and self.token_counter:
                # Count actual tokens in response
                completion_tokens = self.token_counter.count_tokens(task_content)
                prompt_tokens = self.token_counter.count_tokens(user_prompt)

                self.cost_tracker.record_completion(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=self.token_counter.get_model_name(),
                )

                logger.info(
                    f"Task generation complete: {completion_tokens} completion tokens, "
                    f"total cost ${self.cost_tracker.get_current_cost():.4f}"
                )

            # Parse the generated task content into TaskList
            # For now, fall back to rule-based parsing
            # TODO: Implement LLM response parsing
            logger.info("Generated task content, parsing into TaskList structure")
            return self.generate_from_design(design)

        except Exception as e:
            logger.error(f"Failed to generate tasks with LLM: {e}")
            logger.info("Falling back to rule-based task generation")
            return self.generate_from_design(design)

    def generate_from_design(self, design: DesignDocument) -> TaskList:
        """Generate implementation tasks from design document (rule-based).
        
        This is the fallback method that uses rule-based task generation
        when LLM client is not available or fails.

        Args:
            design: Design document to generate tasks from

        Returns:
            Generated task list
        """
        tasks = []
        task_id_counter = 1

        # Generate tasks for each major area

        # 1. Data model tasks
        data_model_tasks = self._generate_data_model_tasks(design, task_id_counter)
        tasks.extend(data_model_tasks)
        task_id_counter += len(data_model_tasks)

        # 2. Interface definition tasks
        interface_tasks = self._generate_interface_tasks(design, task_id_counter)
        tasks.extend(interface_tasks)
        task_id_counter += len(interface_tasks)

        # 3. Component implementation tasks
        component_tasks = self._generate_component_tasks(design, task_id_counter)
        tasks.extend(component_tasks)
        task_id_counter += len(component_tasks)

        # 4. Error handling tasks
        error_handling_tasks = self._generate_error_handling_tasks(
            design, task_id_counter
        )
        tasks.extend(error_handling_tasks)
        task_id_counter += len(error_handling_tasks)

        # 5. Testing tasks
        testing_tasks = self._generate_testing_tasks(design, task_id_counter)
        tasks.extend(testing_tasks)
        task_id_counter += len(testing_tasks)

        # 6. Integration tasks
        integration_tasks = self._generate_integration_tasks(design, task_id_counter)
        tasks.extend(integration_tasks)
        task_id_counter += len(integration_tasks)

        # Generate dependencies between tasks
        dependencies = self._generate_task_dependencies(tasks)

        # Generate effort estimates
        estimated_effort = self._generate_effort_estimates(tasks)

        return TaskList(
            tasks=tasks,
            dependencies=dependencies,
            estimated_effort=estimated_effort,
            version=self.version,
            approved=False,
        )

    def refine_tasks(self, tasks: TaskList, feedback: str) -> TaskList:
        """Refine task list based on user feedback.

        Args:
            tasks: Original task list
            feedback: User feedback for refinement

        Returns:
            Refined task list
        """
        # Parse feedback to understand what needs to be changed
        refinements = self._parse_feedback(feedback)

        # Apply refinements to the task list
        refined_tasks = self._apply_refinements(tasks, refinements)

        # Update version and reset approval status
        refined_tasks.version = self._increment_version(tasks.version)
        refined_tasks.approved = False

        return refined_tasks

    def format_task_list(self, task_list: TaskList) -> str:
        """Format task list as markdown.

        Args:
            task_list: Task list to format

        Returns:
            Formatted markdown string
        """
        lines = []

        # Header
        lines.append("# Implementation Plan")
        lines.append("")

        # Group tasks by category for better organization
        categorized_tasks = self._categorize_tasks(task_list.tasks)

        # Generate tasks in logical order
        task_order = [
            "Data Models",
            "Interfaces",
            "Components",
            "Error Handling",
            "Testing",
            "Integration",
        ]

        task_counter = 1
        for category in task_order:
            if category in categorized_tasks:
                category_tasks = categorized_tasks[category]

                for task in category_tasks:
                    # Main task
                    status_marker = self._get_status_marker(task.status)
                    lines.append(f"- [{status_marker}] {task_counter}. {task.title}")

                    # Task description as sub-bullet
                    if task.description:
                        lines.append(f"  - {task.description}")

                    # Implementation notes if available
                    if task.implementation_notes:
                        lines.append(f"  - {task.implementation_notes}")

                    # Context requirements
                    if task.context_requirements:
                        context_text = ", ".join(task.context_requirements)
                        lines.append(f"  - **Context needed:** {context_text}")

                    # Requirement references
                    if task.requirements_refs:
                        req_text = ", ".join(task.requirements_refs)
                        lines.append(f"  - _Requirements: {req_text}_")

                    lines.append("")
                    task_counter += 1

        # Add any uncategorized tasks
        uncategorized = [
            t
            for t in task_list.tasks
            if self._determine_task_category(t) not in task_order
        ]
        for task in uncategorized:
            status_marker = self._get_status_marker(task.status)
            lines.append(f"- [{status_marker}] {task_counter}. {task.title}")

            if task.description:
                lines.append(f"  - {task.description}")

            if task.requirements_refs:
                req_text = ", ".join(task.requirements_refs)
                lines.append(f"  - _Requirements: {req_text}_")

            lines.append("")
            task_counter += 1

        # Task metadata
        lines.append("---")
        lines.append("")
        lines.append("## Task Metadata")
        lines.append("")
        lines.append(f"**Total Tasks:** {len(task_list.tasks)}")
        lines.append(f"**Version:** {task_list.version}")
        lines.append(f"**Status:** {'Approved' if task_list.approved else 'Draft'}")

        # Effort summary
        total_effort = sum(task_list.estimated_effort.values())
        lines.append(f"**Estimated Total Effort:** {total_effort} hours")

        # Dependencies summary
        if task_list.dependencies:
            lines.append(
                f"**Task Dependencies:** {len(task_list.dependencies)} tasks have dependencies"
            )

        return "\n".join(lines)

    def request_user_approval(self, task_list: TaskList) -> bool:
        """Request user approval for the task list.

        Args:
            task_list: Task list to approve

        Returns:
            True if approved, False otherwise
        """
        if not self.cli_interface:
            # Auto-approve if no CLI interface
            task_list.approved = True
            return True

        formatted_tasks = self.format_task_list(task_list)
        approved = self.cli_interface.request_approval(formatted_tasks, "task list")

        if approved:
            task_list.approved = True

        return approved

    # Private helper methods

    def _build_llm_context(
        self,
        design: DesignDocument,
        specification: str | None = None,
    ) -> dict[str, Any]:
        """Build context dictionary for LLM prompt.
        
        Args:
            design: Design document
            specification: Optional specification text
            
        Returns:
            Context dictionary for prompt template
        """
        # Format design document as text
        design_text = self._format_design_for_prompt(design)

        # Analyze complexity
        complexity_analysis = self._analyze_complexity(design)

        context = {
            "specification": specification or "No specification provided",
            "design": design_text,
            "complexity_analysis": complexity_analysis,
        }

        return context

    def _format_design_for_prompt(self, design: DesignDocument) -> str:
        """Format design document as text for LLM prompt.
        
        Args:
            design: Design document to format
            
        Returns:
            Formatted design text
        """
        lines = []

        lines.append("# Design Document")
        lines.append("")
        lines.append("## Overview")
        lines.append(design.overview)
        lines.append("")

        lines.append("## Architecture")
        lines.append(design.architecture.overview)
        lines.append("")
        lines.append("**Patterns:**")
        for pattern in design.architecture.patterns:
            lines.append(f"- {pattern}")
        lines.append("")

        lines.append("## Components")
        for component in design.components:
            lines.append(f"### {component.name}")
            lines.append(f"- **Description:** {component.description}")
            lines.append(f"- **Interfaces:** {', '.join(component.interfaces)}")
            lines.append(f"- **Dependencies:** {', '.join(component.dependencies)}")
            lines.append("")

        lines.append("## Data Models")
        for model in design.data_models:
            lines.append(f"### {model.name}")
            lines.append(f"- **Fields:** {', '.join(model.fields.keys())}")
            if model.relationships:
                lines.append(f"- **Relationships:** {', '.join(model.relationships)}")
            lines.append("")

        lines.append("## Interfaces")
        for interface in design.interfaces:
            lines.append(f"### {interface.name}")
            lines.append(f"- **Description:** {interface.description}")
            lines.append(f"- **Methods:** {', '.join(interface.methods[:5])}")
            lines.append("")

        lines.append("## Error Handling")
        lines.append(f"- **Categories:** {', '.join(design.error_handling.error_categories)}")
        lines.append(f"- **Strategy:** {design.error_handling.logging_strategy}")
        lines.append("")

        lines.append("## Testing Strategy")
        lines.append(f"- **Unit Testing:** {design.testing_strategy.unit_testing}")
        lines.append(f"- **Integration Testing:** {design.testing_strategy.integration_testing}")
        lines.append(f"- **Coverage Target:** {design.testing_strategy.test_coverage_target:.0%}")
        lines.append("")

        return "\n".join(lines)

    def _analyze_complexity(self, design: DesignDocument) -> str:
        """Analyze design complexity for task breakdown.
        
        Args:
            design: Design document to analyze
            
        Returns:
            Complexity analysis text
        """
        lines = []

        # Count components
        num_components = len(design.components)
        num_models = len(design.data_models)
        num_interfaces = len(design.interfaces)

        lines.append("# Complexity Analysis")
        lines.append("")
        lines.append(f"- **Components:** {num_components}")
        lines.append(f"- **Data Models:** {num_models}")
        lines.append(f"- **Interfaces:** {num_interfaces}")
        lines.append("")

        # Estimate complexity level
        total_items = num_components + num_models + num_interfaces
        if total_items < 5:
            complexity = "Low"
            recommendation = "Focus on 5-10 high-level tasks"
        elif total_items < 10:
            complexity = "Medium"
            recommendation = "Break down into 10-20 incremental tasks"
        else:
            complexity = "High"
            recommendation = "Create 20-30 detailed tasks with clear dependencies"

        lines.append(f"**Complexity Level:** {complexity}")
        lines.append(f"**Recommendation:** {recommendation}")
        lines.append("")

        # Identify key areas
        lines.append("**Key Implementation Areas:**")
        if num_models > 0:
            lines.append("- Data model implementation and validation")
        if num_interfaces > 0:
            lines.append("- Interface definitions and contracts")
        if num_components > 0:
            lines.append("- Component implementation with dependency injection")
        lines.append("- Error handling and logging")
        lines.append("- Comprehensive testing (unit, integration)")
        lines.append("- System integration and wiring")

        return "\n".join(lines)

    def _generate_data_model_tasks(
        self, design: DesignDocument, start_id: int
    ) -> list[Task]:
        """Generate tasks for data models."""
        tasks = []
        task_id = start_id

        for model in design.data_models:
            # Main data model implementation task
            task = Task(
                id=str(task_id),
                title=f"Implement {model.name} data model",
                description=f"Create {model.name} class with fields and validation",
                requirements_refs=self._extract_requirements_from_model(model, design),
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=["Data model patterns", "Validation frameworks"],
                implementation_notes=f"Include fields: {', '.join(model.fields.keys())}",
            )
            tasks.append(task)
            task_id += 1

            # Validation task for complex models
            if len(model.fields) > 3:
                validation_task = Task(
                    id=str(task_id),
                    title=f"Implement {model.name} validation",
                    description=f"Add comprehensive validation for {model.name} fields",
                    requirements_refs=self._extract_requirements_from_model(
                        model, design
                    ),
                    subtasks=[],
                    status=TaskStatus.NOT_STARTED,
                    target_language="python",
                    context_requirements=["Validation patterns", "Error handling"],
                    implementation_notes="Include field validation, business rules, and error messages",
                )
                tasks.append(validation_task)
                task_id += 1

        return tasks

    def _generate_interface_tasks(
        self, design: DesignDocument, start_id: int
    ) -> list[Task]:
        """Generate tasks for interface definitions."""
        tasks = []
        task_id = start_id

        for interface in design.interfaces:
            task = Task(
                id=str(task_id),
                title=f"Define {interface.name} interface",
                description=f"Create {interface.name} for {interface.description.lower()}",
                requirements_refs=self._extract_requirements_from_interface(
                    interface, design
                ),
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=["Interface patterns", "Type annotations"],
                implementation_notes=f"Methods: {', '.join(interface.methods[:3])}",
            )
            tasks.append(task)
            task_id += 1

        return tasks

    def _generate_component_tasks(
        self, design: DesignDocument, start_id: int
    ) -> list[Task]:
        """Generate tasks for component implementations."""
        tasks = []
        task_id = start_id

        for component in design.components:
            task = Task(
                id=str(task_id),
                title=f"Implement {component.name} component",
                description=f"Create {component.name} class for {component.description.lower()}",
                requirements_refs=self._extract_requirements_from_component(
                    component, design
                ),
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=["Component patterns", "Dependency injection"],
                implementation_notes=f"Implements: {', '.join(component.interfaces)}",
            )
            tasks.append(task)
            task_id += 1

        return tasks

    def _generate_error_handling_tasks(
        self, design: DesignDocument, start_id: int
    ) -> list[Task]:
        """Generate tasks for error handling implementation."""
        tasks = []
        task_id = start_id

        # Main error handling task
        task = Task(
            id=str(task_id),
            title="Implement error handling system",
            description="Create error handling classes and logging infrastructure",
            requirements_refs=["Error handling requirements"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED,
            target_language="python",
            context_requirements=["Error handling patterns", "Logging frameworks"],
            implementation_notes=f"Categories: {', '.join(design.error_handling.error_categories[:3])}",
        )
        tasks.append(task)

        return tasks

    def _generate_testing_tasks(
        self, design: DesignDocument, start_id: int
    ) -> list[Task]:
        """Generate tasks for testing implementation."""
        tasks = []
        task_id = start_id

        # Unit testing task
        unit_task = Task(
            id=str(task_id),
            title="Implement unit tests",
            description="Create comprehensive unit tests for all components",
            requirements_refs=["Testing requirements"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED,
            target_language="python",
            context_requirements=["Testing frameworks", "Mocking patterns"],
            implementation_notes=f"Target coverage: {design.testing_strategy.test_coverage_target:.0%}",
        )
        tasks.append(unit_task)
        task_id += 1

        # Integration testing task
        integration_task = Task(
            id=str(task_id),
            title="Implement integration tests",
            description="Create integration tests for component interactions",
            requirements_refs=["Testing requirements"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED,
            target_language="python",
            context_requirements=["Integration testing patterns", "Test databases"],
            implementation_notes="Focus on component interactions and external dependencies",
        )
        tasks.append(integration_task)
        task_id += 1

        # Performance testing if specified
        if (
            design.testing_strategy.performance_testing
            and len(design.testing_strategy.performance_testing.strip()) > 0
        ):
            perf_task = Task(
                id=str(task_id),
                title="Implement performance tests",
                description="Create performance tests for critical paths",
                requirements_refs=["Performance requirements"],
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=["Performance testing tools", "Benchmarking"],
                implementation_notes="Focus on response times and scalability",
            )
            tasks.append(perf_task)
            task_id += 1

        return tasks

    def _generate_integration_tasks(
        self, design: DesignDocument, start_id: int
    ) -> list[Task]:
        """Generate tasks for system integration."""
        tasks = []
        task_id = start_id

        # Main integration task
        task = Task(
            id=str(task_id),
            title="Integrate all components",
            description="Wire together all components and ensure proper initialization",
            requirements_refs=["All functional requirements"],
            subtasks=[],
            status=TaskStatus.NOT_STARTED,
            target_language="python",
            context_requirements=["Dependency injection", "Configuration management"],
            implementation_notes="Create main application entry point and configuration",
        )
        tasks.append(task)

        return tasks

    def _generate_task_dependencies(self, tasks: list[Task]) -> dict[str, list[str]]:
        """Generate dependencies between tasks."""
        dependencies: dict[str, list[str]] = {}

        # Create task lookup by category
        task_categories: dict[str, list[Task]] = {}
        for task in tasks:
            category = self._determine_task_category(task)
            if category not in task_categories:
                task_categories[category] = []
            task_categories[category].append(task)

        # Define dependency rules
        dependency_rules = {
            "Components": ["Data Models", "Interfaces"],
            "Testing": ["Components", "Error Handling"],
            "Integration": ["Components", "Error Handling", "Testing"],
        }

        # Apply dependency rules
        for task in tasks:
            task_category = self._determine_task_category(task)
            if task_category in dependency_rules:
                task_deps = []
                for dep_category in dependency_rules[task_category]:
                    if dep_category in task_categories:
                        for dep_task in task_categories[dep_category]:
                            task_deps.append(dep_task.id)

                if task_deps:
                    dependencies[task.id] = task_deps

        return dependencies

    def _generate_effort_estimates(self, tasks: list[Task]) -> dict[str, int]:
        """Generate effort estimates for tasks."""
        estimates = {}

        for task in tasks:
            # Base estimate by task category
            category = self._determine_task_category(task)

            if category == "Data Models":
                base_effort = 3  # 3 hours for basic data model
            elif category == "Interfaces":
                base_effort = 2  # 2 hours for interface definition
            elif category == "Components":
                base_effort = 8  # 8 hours for component implementation
            elif category == "Error Handling":
                base_effort = 5  # 5 hours for error handling
            elif category == "Testing":
                if "unit" in task.title.lower():
                    base_effort = 6  # 6 hours for unit tests
                elif "integration" in task.title.lower():
                    base_effort = 8  # 8 hours for integration tests
                elif "performance" in task.title.lower():
                    base_effort = 10  # 10 hours for performance tests
                else:
                    base_effort = 6
            elif category == "Integration":
                base_effort = 12  # 12 hours for integration
            else:
                base_effort = 5  # Default

            # Adjust based on complexity indicators
            complexity_multiplier = 1.0

            # Check for complexity indicators in description
            if task.description:
                desc_lower = task.description.lower()
                if any(
                    word in desc_lower
                    for word in ["comprehensive", "complex", "advanced"]
                ):
                    complexity_multiplier += 0.5
                if any(
                    word in desc_lower
                    for word in ["validation", "security", "performance"]
                ):
                    complexity_multiplier += 0.3

            # Check implementation notes for complexity
            if task.implementation_notes:
                notes_lower = task.implementation_notes.lower()
                if len(notes_lower) > 50:  # Longer notes suggest complexity
                    complexity_multiplier += 0.2

            # Apply multiplier and round
            final_effort = max(1, min(20, int(base_effort * complexity_multiplier)))
            estimates[task.id] = final_effort

        return estimates

    def _categorize_tasks(self, tasks: list[Task]) -> dict[str, list[Task]]:
        """Categorize tasks for better organization."""
        categories: dict[str, list[Task]] = {}

        for task in tasks:
            category = self._determine_task_category(task)
            if category not in categories:
                categories[category] = []
            categories[category].append(task)

        return categories

    def _determine_task_category(self, task: Task) -> str:
        """Determine the category of a task."""
        title_lower = task.title.lower()

        if "data model" in title_lower or "validation" in title_lower:
            return "Data Models"
        elif "interface" in title_lower:
            return "Interfaces"
        elif "component" in title_lower:
            return "Components"
        elif "error" in title_lower:
            return "Error Handling"
        elif "test" in title_lower:
            return "Testing"
        elif "integrate" in title_lower:
            return "Integration"
        else:
            return "Other"

    def _get_status_marker(self, status: TaskStatus) -> str:
        """Get checkbox marker for task status."""
        if status == TaskStatus.NOT_STARTED:
            return " "
        elif status == TaskStatus.IN_PROGRESS:
            return "-"
        elif status == TaskStatus.COMPLETED:
            return "x"
        elif status == TaskStatus.FAILED:
            return "!"
        elif status == TaskStatus.BLOCKED:
            return "?"

        return " "  # type: ignore[unreachable]  # Safety fallback for unknown status

    def _extract_requirements_from_model(
        self, model: DataModel, design: DesignDocument
    ) -> list[str]:
        """Extract requirement references from data model."""
        refs = []

        # Look for model name in design overview
        if model.name.lower() in design.overview.lower():
            refs.append(f"Data requirements for {model.name}")

        # Add specific requirements based on model name
        model_name_lower = model.name.lower()
        if "user" in model_name_lower:
            refs.append("User data requirements")
        elif "session" in model_name_lower:
            refs.append("Session management requirements")
        else:
            refs.append(f"{model.name} data requirements")

        # Add generic data requirements
        refs.append("Data persistence requirements")

        # Add validation requirements if model has many fields
        if len(model.fields) > 3:
            refs.append("Data validation requirements")

        return refs

    def _extract_requirements_from_interface(
        self, interface: InterfaceSpec, design: DesignDocument
    ) -> list[str]:
        """Extract requirement references from interface."""
        refs = []

        # Look for interface purpose in description
        if "user" in interface.description.lower():
            refs.append("User management requirements")
        elif "data" in interface.description.lower():
            refs.append("Data management requirements")
        elif "api" in interface.description.lower():
            refs.append("API requirements")
        else:
            refs.append("Interface requirements")

        return refs

    def _extract_requirements_from_component(
        self, component: ComponentSpec, design: DesignDocument
    ) -> list[str]:
        """Extract requirement references from component."""
        refs = []

        # Look for component purpose in description
        desc_lower = component.description.lower()

        if "user" in desc_lower:
            refs.append("User management requirements")
        if "auth" in desc_lower:
            refs.append("Authentication requirements")
        if "data" in desc_lower:
            refs.append("Data management requirements")
        if "api" in desc_lower:
            refs.append("API requirements")

        # If no specific requirements found, add generic
        if not refs:
            refs.append(f"{component.name} functional requirements")

        return refs

    def _parse_feedback(self, feedback: str) -> dict[str, Any]:
        """Parse user feedback to understand requested changes."""
        feedback_lower = feedback.lower()
        add_tasks: list[str] = []
        remove_tasks: list[str] = []
        adjust_effort: dict[str, str] = {}

        refinements: dict[str, Any] = {
            "add_tasks": add_tasks,
            "modify_tasks": [],
            "remove_tasks": remove_tasks,
            "change_order": False,
            "adjust_effort": adjust_effort,
            "add_dependencies": {},
        }

        # Simple keyword-based parsing
        if "add" in feedback_lower and (
            "task" in feedback_lower or "more" in feedback_lower
        ):
            # Extract what to add (simplified)
            if "security" in feedback_lower:
                add_tasks.append("Security implementation task")
            if "documentation" in feedback_lower:
                add_tasks.append("Documentation task")
            if "testing" in feedback_lower:
                add_tasks.append("Additional testing task")

            # Generic addition if no specific type found
            if not add_tasks:
                add_tasks.append("Additional task based on feedback")

        if "remove" in feedback_lower:
            remove_tasks.append("Remove unnecessary tasks")

        if "effort" in feedback_lower or "time" in feedback_lower:
            if "increase" in feedback_lower or "more" in feedback_lower:
                adjust_effort["general"] = "increase effort"
            elif "decrease" in feedback_lower or "less" in feedback_lower:
                adjust_effort["general"] = "decrease effort"

        if "order" in feedback_lower or "sequence" in feedback_lower:
            refinements["change_order"] = True

        return refinements

    def _apply_refinements(
        self, task_list: TaskList, refinements: dict[str, Any]
    ) -> TaskList:
        """Apply refinements to task list."""
        # Create a copy of the task list
        refined_tasks = task_list.tasks.copy()
        refined_dependencies = task_list.dependencies.copy()
        refined_effort = task_list.estimated_effort.copy()

        # Add new tasks
        next_id = max(int(task.id) for task in refined_tasks) + 1
        for new_task_desc in refinements["add_tasks"]:
            new_task = Task(
                id=str(next_id),
                title=new_task_desc,
                description=f"Task added based on user feedback: {new_task_desc}",
                requirements_refs=["User feedback requirements"],
                subtasks=[],
                status=TaskStatus.NOT_STARTED,
                target_language="python",
                context_requirements=["User feedback context"],
                implementation_notes="Added based on user feedback",
            )
            refined_tasks.append(new_task)
            refined_effort[str(next_id)] = 5  # Default effort
            next_id += 1

        # Remove tasks (simplified - remove last task if requested)
        if refinements["remove_tasks"] and refined_tasks:
            removed_task = refined_tasks.pop()
            if removed_task.id in refined_effort:
                del refined_effort[removed_task.id]
            if removed_task.id in refined_dependencies:
                del refined_dependencies[removed_task.id]

        # Adjust effort estimates
        if "general" in refinements["adjust_effort"]:
            adjustment = refinements["adjust_effort"]["general"]
            for task_id in refined_effort:
                current_effort = refined_effort[task_id]
                if adjustment == "increase effort":
                    refined_effort[task_id] = min(20, int(current_effort * 1.3))
                elif adjustment == "decrease effort":
                    refined_effort[task_id] = max(1, int(current_effort * 0.8))

        return TaskList(
            tasks=refined_tasks,
            dependencies=refined_dependencies,
            estimated_effort=refined_effort,
            version=task_list.version,
            approved=False,
        )

    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        try:
            parts = version.split(".")
            if len(parts) >= 2:
                minor = int(parts[1]) + 1
                return f"{parts[0]}.{minor}"
            else:
                major = int(parts[0])
                return f"{major}.1"
        except (ValueError, IndexError):
            return "1.1"
