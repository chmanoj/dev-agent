"""Design generator for creating DESIGN.md documents."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..errors.llm_exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTokenLimitError,
)
from ..interfaces.analysis_interface import ICodebaseAnalyzer
from ..interfaces.cli_interface import ICLIInterface
from ..interfaces.generation_interface import IDesignGenerator
from ..llm.prompt_templates import get_template
from ..models.analysis import DesignAnalysis
from ..models.documents import (
    ArchitectureDescription,
    ComponentSpec,
    DataModel,
    DesignDocument,
    ErrorHandlingStrategy,
    InterfaceSpec,
    SpecificationDocument,
    TestingStrategy,
)

if TYPE_CHECKING:
    from ..indexing.vector_database import VectorDatabase
    from ..llm.base import ILLMClient
    from ..llm.cost_tracker import CostTracker
    from ..llm.token_counter import TokenCounter

logger = logging.getLogger(__name__)


class DesignGenerator(IDesignGenerator):
    """Generates design documents from specifications and codebase analysis.
    
    This generator uses Azure OpenAI (GPT-4) to create detailed design documents
    based on specifications, existing architecture, and relevant code patterns
    retrieved via vector search. It integrates with cost tracking and token
    management for efficient API usage.
    
    Example:
        ```python
        from dev_agent.llm.azure_client import AzureOpenAIClient
        from dev_agent.llm.cost_tracker import CostTracker
        from dev_agent.llm.token_counter import TokenCounter
        from dev_agent.indexing.vector_database import VectorDatabase
        
        llm_client = AzureOpenAIClient(config)
        cost_tracker = CostTracker()
        token_counter = TokenCounter()
        vector_db = VectorDatabase(index_path, embedding_client)
        
        generator = DesignGenerator(
            codebase_analyzer=analyzer,
            llm_client=llm_client,
            cost_tracker=cost_tracker,
            token_counter=token_counter,
            vector_db=vector_db,
        )
        
        design = await generator.generate_from_specification_ai(spec, analysis)
        ```
    """

    def __init__(
        self,
        codebase_analyzer: ICodebaseAnalyzer,
        cli_interface: ICLIInterface | None = None,
        llm_client: ILLMClient | None = None,
        cost_tracker: CostTracker | None = None,
        token_counter: TokenCounter | None = None,
        vector_db: VectorDatabase | None = None,
    ):
        """Initialize the design generator.

        Args:
            codebase_analyzer: Codebase analyzer for architecture analysis
            cli_interface: Optional CLI interface for user interaction
            llm_client: LLM client for AI-powered generation (optional for backward compatibility)
            cost_tracker: Cost tracker for monitoring API usage (optional)
            token_counter: Token counter for validation (optional)
            vector_db: Vector database for context retrieval (optional)
        """
        self.codebase_analyzer = codebase_analyzer
        self.cli_interface = cli_interface
        self.llm_client = llm_client
        self.cost_tracker = cost_tracker
        self.token_counter = token_counter
        self.vector_db = vector_db
        self.version = "1.0"

        if llm_client:
            logger.info("DesignGenerator initialized with LLM client")
        else:
            logger.warning(
                "DesignGenerator initialized without LLM client - "
                "AI-powered generation will not be available"
            )

    async def generate_from_specification_ai(
        self,
        spec: SpecificationDocument,
        analysis: DesignAnalysis,
    ) -> DesignDocument:
        """Generate design document using AI from specification and codebase analysis.
        
        This method uses Azure OpenAI (GPT-4) to generate a comprehensive
        design document based on the specification, existing architecture,
        and relevant code patterns retrieved via vector search.

        Args:
            spec: Specification document
            analysis: Design analysis from codebase

        Returns:
            Generated design document
            
        Raises:
            ValueError: If LLM client is not configured
            LLMError: If AI generation fails
        """
        if not self.llm_client:
            raise ValueError(
                "LLM client not configured. Initialize DesignGenerator "
                "with an ILLMClient instance for AI-powered generation."
            )

        logger.info("Generating AI-powered design document from specification")

        try:
            # Retrieve relevant architecture patterns via vector search
            relevant_patterns = await self._retrieve_architecture_patterns(spec)

            # Build context for prompt template
            context = self._build_design_context(
                spec=spec,
                analysis=analysis,
                relevant_patterns=relevant_patterns,
            )

            # Get design template
            template = get_template("design")

            # Validate token limits before generation
            if self.token_counter:
                system_prompt, user_prompt = template.render(context, self.token_counter)
                prompt_tokens = self.token_counter.count_tokens(user_prompt)
                system_tokens = self.token_counter.count_tokens(system_prompt)
                total_prompt_tokens = prompt_tokens + system_tokens

                is_valid, error_msg = self.token_counter.validate_context_window(
                    prompt_tokens=total_prompt_tokens,
                    max_completion_tokens=template.max_tokens,
                )

                if not is_valid:
                    raise LLMTokenLimitError(error_msg)

                logger.info(
                    f"Token validation passed: {total_prompt_tokens} prompt tokens, "
                    f"{template.max_tokens} max completion tokens"
                )
            else:
                system_prompt, user_prompt = template.render(context)

            # Generate design using LLM
            logger.info("Calling Azure OpenAI for design generation...")
            design_content = await self.llm_client.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=template.temperature,
                max_tokens=template.max_tokens,
            )

            # Track cost if tracker available
            if self.cost_tracker and self.token_counter:
                prompt_tokens = self.token_counter.count_tokens(user_prompt + system_prompt)
                completion_tokens = self.token_counter.count_tokens(design_content)
                cost = self.cost_tracker.record_completion(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=self.token_counter.get_model_name(),
                )
                logger.info(
                    f"Design generation cost: ${cost:.4f} "
                    f"({prompt_tokens} + {completion_tokens} tokens)"
                )

            # Parse AI-generated content into structured document
            design_doc = self._parse_ai_design(design_content, spec, analysis)

            logger.info("AI-powered design document generated successfully")
            return design_doc

        except LLMAuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except LLMRateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            raise
        except LLMTimeoutError as e:
            logger.error(f"Request timed out: {e}")
            raise
        except LLMBadRequestError as e:
            logger.error(f"Bad request: {e}")
            raise
        except LLMTokenLimitError as e:
            logger.error(f"Token limit exceeded: {e}")
            raise
        except LLMAPIError as e:
            logger.error(f"API error: {e}")
            raise
        except LLMError as e:
            logger.error(f"LLM error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during AI generation: {e}")
            raise LLMAPIError(
                f"Failed to generate design: {e}",
                "Check logs for details and verify Azure OpenAI configuration"
            ) from e

    def generate_from_specification(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> DesignDocument:
        """Generate design document from specification and codebase analysis.
        
        This is the legacy method that uses rule-based generation.
        For AI-powered generation, use generate_from_specification_ai().

        Args:
            spec: Specification document
            analysis: Design analysis from codebase

        Returns:
            Generated design document
        """
        # Generate overview from specification and analysis
        overview = self._generate_overview(spec, analysis)

        # Create architecture description
        architecture = self._create_architecture_description(spec, analysis)

        # Generate components from analysis and requirements
        components = self._generate_components(spec, analysis)

        # Extract data models from analysis
        data_models = self._generate_data_models(spec, analysis)

        # Generate interfaces from analysis
        interfaces = self._generate_interfaces(spec, analysis)

        # Create error handling strategy
        error_handling = self._create_error_handling_strategy(spec, analysis)

        # Create testing strategy
        testing_strategy = self._create_testing_strategy(spec, analysis)

        return DesignDocument(
            overview=overview,
            architecture=architecture,
            components=components,
            data_models=data_models,
            interfaces=interfaces,
            error_handling=error_handling,
            testing_strategy=testing_strategy,
            version=self.version,
            approved=False,
        )

    def refine_design(self, design: DesignDocument, feedback: str) -> DesignDocument:
        """Refine design based on user feedback.

        Args:
            design: Original design document
            feedback: User feedback for refinement

        Returns:
            Refined design document
        """
        # Parse feedback to understand what needs to be changed
        refinements = self._parse_feedback(feedback)

        # Apply refinements to the design
        refined_design = self._apply_refinements(design, refinements)

        # Update version and reset approval status
        refined_design.version = self._increment_version(design.version)
        refined_design.approved = False

        return refined_design

    def format_design_document(self, design: DesignDocument) -> str:
        """Format design document as markdown.

        Args:
            design: Design document to format

        Returns:
            Formatted markdown string
        """
        lines = []

        # Header
        lines.append("# Design Document")
        lines.append("")

        # Overview
        lines.append("## Overview")
        lines.append("")
        lines.append(design.overview)
        lines.append("")

        # Architecture
        lines.append("## Architecture")
        lines.append("")
        lines.append(design.architecture.overview)
        lines.append("")

        if design.architecture.patterns:
            lines.append("### Architectural Patterns")
            lines.append("")
            for pattern in design.architecture.patterns:
                lines.append(f"- {pattern}")
            lines.append("")

        if design.architecture.components:
            lines.append("### High-Level Components")
            lines.append("")
            for component in design.architecture.components:
                lines.append(f"- {component}")
            lines.append("")

        # Components and Interfaces
        if design.components:
            lines.append("## Components and Interfaces")
            lines.append("")

            for component in design.components:
                lines.append(f"### {component.name}")
                lines.append("")
                lines.append(component.description)
                lines.append("")

                if component.interfaces:
                    lines.append("**Interfaces:**")
                    for interface in component.interfaces:
                        lines.append(f"- {interface}")
                    lines.append("")

                if component.dependencies:
                    lines.append("**Dependencies:**")
                    for dependency in component.dependencies:
                        lines.append(f"- {dependency}")
                    lines.append("")

        # Data Models
        if design.data_models:
            lines.append("## Data Models")
            lines.append("")

            for model in design.data_models:
                lines.append(f"### {model.name}")
                lines.append("")

                if model.fields:
                    lines.append("**Fields:**")
                    for field_name, field_type in model.fields.items():
                        lines.append(f"- `{field_name}`: {field_type}")
                    lines.append("")

                if model.relationships:
                    lines.append("**Relationships:**")
                    for relationship in model.relationships:
                        lines.append(f"- {relationship}")
                    lines.append("")

        # Interfaces
        if design.interfaces:
            lines.append("## Interface Specifications")
            lines.append("")

            for interface in design.interfaces:
                lines.append(f"### {interface.name}")
                lines.append("")
                lines.append(interface.description)
                lines.append("")

                if interface.methods:
                    lines.append("**Methods:**")
                    for method in interface.methods:
                        lines.append(f"- {method}")
                    lines.append("")

        # Error Handling
        lines.append("## Error Handling")
        lines.append("")
        lines.append(f"**Logging Strategy:** {design.error_handling.logging_strategy}")
        lines.append("")

        if design.error_handling.error_categories:
            lines.append("**Error Categories:**")
            for category in design.error_handling.error_categories:
                lines.append(f"- {category}")
            lines.append("")

        if design.error_handling.recovery_mechanisms:
            lines.append("**Recovery Mechanisms:**")
            for mechanism in design.error_handling.recovery_mechanisms:
                lines.append(f"- {mechanism}")
            lines.append("")

        # Testing Strategy
        lines.append("## Testing Strategy")
        lines.append("")
        lines.append(f"**Unit Testing:** {design.testing_strategy.unit_testing}")
        lines.append("")
        lines.append(
            f"**Integration Testing:** {design.testing_strategy.integration_testing}"
        )
        lines.append("")
        lines.append(
            f"**Performance Testing:** {design.testing_strategy.performance_testing}"
        )
        lines.append("")
        lines.append(
            f"**Test Coverage Target:** {design.testing_strategy.test_coverage_target:.0%}"
        )
        lines.append("")

        # Metadata
        lines.append("---")
        lines.append("")
        lines.append("## Document Metadata")
        lines.append("")
        lines.append(f"- **Version:** {design.version}")
        lines.append(f"- **Status:** {'Approved' if design.approved else 'Draft'}")

        return "\n".join(lines)

    def request_user_approval(self, design: DesignDocument) -> bool:
        """Request user approval for the design.

        Args:
            design: Design document to approve

        Returns:
            True if approved, False otherwise
        """
        if not self.cli_interface:
            # Auto-approve if no CLI interface
            design.approved = True
            return True

        formatted_design = self.format_design_document(design)
        approved = self.cli_interface.request_approval(formatted_design, "design")

        if approved:
            design.approved = True

        return approved

    # Private helper methods

    def _generate_overview(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> str:
        """Generate design overview from specification and analysis."""
        overview_parts = []

        # Start with specification introduction context
        overview_parts.append(
            "This design document outlines the technical architecture for the system described in the specification."
        )

        # Add architecture insights from analysis
        if analysis.architecture_overview:
            overview_parts.append(analysis.architecture_overview)

        # Add component count information
        if analysis.components:
            overview_parts.append(
                f"The system is organized into {len(analysis.components)} main components."
            )

        # Add design patterns information
        if analysis.design_patterns:
            patterns_text = ", ".join(analysis.design_patterns[:3])
            overview_parts.append(f"The design incorporates {patterns_text} patterns.")

        # Add quality metrics if available
        if analysis.quality_metrics:
            if "documentation_coverage" in analysis.quality_metrics:
                coverage = analysis.quality_metrics["documentation_coverage"]
                if coverage > 0.7:
                    overview_parts.append(
                        "The codebase demonstrates good documentation practices."
                    )
                elif coverage < 0.3:
                    overview_parts.append(
                        "The design emphasizes improved documentation standards."
                    )

        return " ".join(overview_parts)

    def _create_architecture_description(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> ArchitectureDescription:
        """Create architecture description from analysis."""
        # Generate architecture overview
        if analysis.architecture_overview:
            overview = analysis.architecture_overview
        else:
            overview = "The system follows a modular architecture with clear separation of concerns."

        # Extract patterns from analysis
        patterns = analysis.design_patterns.copy() if analysis.design_patterns else []

        # Add patterns inferred from components
        if analysis.components:
            component_names = [comp.name.lower() for comp in analysis.components]
            if any("service" in name for name in component_names):
                patterns.append("Service Layer Pattern")
            if any("repository" in name or "dao" in name for name in component_names):
                patterns.append("Repository Pattern")
            if any("controller" in name for name in component_names):
                patterns.append("MVC Pattern")

        # Generate component list
        components = []
        if analysis.components:
            components = [comp.name for comp in analysis.components]
        else:
            # Infer components from specification requirements
            for req in spec.functional_requirements:
                if "data" in req.user_story.lower():
                    components.append("Data Management Component")
                if "user" in req.user_story.lower():
                    components.append("User Interface Component")
                if "api" in req.user_story.lower():
                    components.append("API Component")

        # Remove duplicates and limit
        components = list(dict.fromkeys(components))[:8]

        return ArchitectureDescription(
            overview=overview, patterns=patterns, components=components
        )

    def _generate_components(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> list[ComponentSpec]:
        """Generate component specifications."""
        components = []

        # Use existing components from analysis if available
        if analysis.components:
            for comp_analysis in analysis.components:
                component = ComponentSpec(
                    name=comp_analysis.name,
                    description=comp_analysis.purpose,
                    interfaces=comp_analysis.interfaces,
                    dependencies=comp_analysis.dependencies,
                )
                components.append(component)
        else:
            # Generate components based on specification requirements
            component_map = {}

            for req in spec.functional_requirements:
                req_text = req.user_story.lower()

                # Identify component types from requirements
                if any(
                    keyword in req_text
                    for keyword in ["data", "store", "save", "retrieve"]
                ):
                    if "Data Management" not in component_map:
                        component_map["Data Management"] = {
                            "description": "Handles data storage, retrieval, and management operations",
                            "interfaces": ["IDataRepository", "IDataValidator"],
                            "dependencies": ["Database", "Validation Framework"],
                        }

                if any(
                    keyword in req_text
                    for keyword in ["user", "interface", "display", "view"]
                ):
                    if "User Interface" not in component_map:
                        component_map["User Interface"] = {
                            "description": "Provides user interaction and presentation layer",
                            "interfaces": ["IUserInterface", "IViewController"],
                            "dependencies": ["UI Framework", "Event System"],
                        }

                if any(
                    keyword in req_text
                    for keyword in ["api", "service", "endpoint", "request"]
                ):
                    if "API Service" not in component_map:
                        component_map["API Service"] = {
                            "description": "Handles external API requests and responses",
                            "interfaces": ["IAPIHandler", "IRequestProcessor"],
                            "dependencies": [
                                "HTTP Framework",
                                "Authentication Service",
                            ],
                        }

                if any(
                    keyword in req_text
                    for keyword in ["auth", "login", "security", "permission"]
                ):
                    if "Authentication" not in component_map:
                        component_map["Authentication"] = {
                            "description": "Manages user authentication and authorization",
                            "interfaces": ["IAuthenticator", "IAuthorizer"],
                            "dependencies": ["Security Framework", "User Management"],
                        }

            # Convert to ComponentSpec objects
            for name, details in component_map.items():
                component = ComponentSpec(
                    name=name,
                    description=details["description"],
                    interfaces=details["interfaces"],
                    dependencies=details["dependencies"],
                )
                components.append(component)

        return components

    def _generate_data_models(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> list[DataModel]:
        """Generate data models from analysis."""
        models = []

        # Use existing data models from analysis if available
        if analysis.data_models:
            for model_data in analysis.data_models:
                model = DataModel(
                    name=model_data.get("name", "UnknownModel"),
                    fields=self._convert_attributes_to_fields(
                        model_data.get("attributes", [])
                    ),
                    relationships=model_data.get("relationships", []),
                )
                models.append(model)
        else:
            # Generate models based on specification requirements
            model_candidates = set()

            for req in spec.functional_requirements:
                req_text = req.user_story.lower()

                # Extract potential model names from requirements
                if "user" in req_text:
                    model_candidates.add("User")
                if any(
                    keyword in req_text
                    for keyword in ["data", "record", "item", "entity"]
                ):
                    model_candidates.add("DataRecord")
                if "session" in req_text:
                    model_candidates.add("Session")
                if "config" in req_text:
                    model_candidates.add("Configuration")

            # Create basic models
            for model_name in list(model_candidates)[:5]:
                fields = self._generate_basic_fields_for_model(model_name)
                relationships = self._generate_basic_relationships_for_model(
                    model_name, model_candidates
                )

                model = DataModel(
                    name=model_name, fields=fields, relationships=relationships
                )
                models.append(model)

        return models

    def _generate_interfaces(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> list[InterfaceSpec]:
        """Generate interface specifications."""
        interfaces = []

        # Use existing interfaces from analysis if available
        if analysis.api_interfaces:
            for api_data in analysis.api_interfaces:
                interface = InterfaceSpec(
                    name=api_data.get("name", "UnknownInterface"),
                    methods=self._extract_methods_from_api_data(api_data),
                    description=api_data.get("docstring", "API interface"),
                )
                interfaces.append(interface)
        else:
            # Generate interfaces based on specification requirements
            interface_map = {}

            for req in spec.functional_requirements:
                req_text = req.user_story.lower()

                if any(
                    keyword in req_text for keyword in ["data", "store", "retrieve"]
                ):
                    if "IDataService" not in interface_map:
                        interface_map["IDataService"] = {
                            "description": "Interface for data management operations",
                            "methods": [
                                "create(data)",
                                "read(id)",
                                "update(id, data)",
                                "delete(id)",
                                "list()",
                            ],
                        }

                if any(keyword in req_text for keyword in ["user", "auth", "login"]):
                    if "IUserService" not in interface_map:
                        interface_map["IUserService"] = {
                            "description": "Interface for user management operations",
                            "methods": [
                                "authenticate(credentials)",
                                "authorize(user, action)",
                                "get_user(id)",
                                "update_user(id, data)",
                            ],
                        }

                if any(
                    keyword in req_text for keyword in ["api", "service", "request"]
                ):
                    if "IAPIHandler" not in interface_map:
                        interface_map["IAPIHandler"] = {
                            "description": "Interface for API request handling",
                            "methods": [
                                "handle_request(request)",
                                "validate_input(data)",
                                "format_response(data)",
                            ],
                        }

            # Convert to InterfaceSpec objects
            for name, details in interface_map.items():
                interface = InterfaceSpec(
                    name=name,
                    methods=details["methods"],
                    description=details["description"],
                )
                interfaces.append(interface)

        return interfaces

    def _create_error_handling_strategy(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> ErrorHandlingStrategy:
        """Create error handling strategy."""
        # Determine error categories based on requirements
        error_categories = []

        for req in spec.functional_requirements:
            req_text = req.user_story.lower()

            if any(keyword in req_text for keyword in ["data", "store", "save"]):
                error_categories.append("Data Validation Errors")
                error_categories.append("Storage Errors")

            if any(keyword in req_text for keyword in ["user", "auth", "login"]):
                error_categories.append("Authentication Errors")
                error_categories.append("Authorization Errors")

            if any(keyword in req_text for keyword in ["api", "request", "service"]):
                error_categories.append("Network Errors")
                error_categories.append("API Errors")

        # Remove duplicates
        error_categories = list(dict.fromkeys(error_categories))

        # Add common error categories
        if not error_categories:
            error_categories = [
                "Input Validation Errors",
                "System Errors",
                "Business Logic Errors",
            ]

        # Define recovery mechanisms
        recovery_mechanisms = [
            "Graceful degradation for non-critical failures",
            "Retry mechanisms for transient errors",
            "User-friendly error messages",
            "Logging and monitoring for debugging",
        ]

        # Determine logging strategy
        if analysis.technical_debt and any(
            "log" in debt.lower() for debt in analysis.technical_debt
        ):
            logging_strategy = (
                "Structured logging with appropriate levels (DEBUG, INFO, WARN, ERROR)"
            )
        else:
            logging_strategy = (
                "Comprehensive logging with structured format and appropriate levels"
            )

        return ErrorHandlingStrategy(
            error_categories=error_categories,
            recovery_mechanisms=recovery_mechanisms,
            logging_strategy=logging_strategy,
        )

    def _create_testing_strategy(
        self, spec: SpecificationDocument, analysis: DesignAnalysis
    ) -> TestingStrategy:
        """Create testing strategy."""
        # Determine testing approach based on analysis
        if (
            analysis.quality_metrics
            and "documentation_coverage" in analysis.quality_metrics
        ):
            coverage = analysis.quality_metrics["documentation_coverage"]
            if coverage > 0.7:
                unit_testing = "Comprehensive unit testing with high coverage (>90%)"
                target_coverage = 0.9
            elif coverage > 0.4:
                unit_testing = "Good unit testing coverage with focus on critical paths"
                target_coverage = 0.8
            else:
                unit_testing = "Basic unit testing with emphasis on core functionality"
                target_coverage = 0.7
        else:
            unit_testing = "Comprehensive unit testing using pytest framework"
            target_coverage = 0.85

        # Integration testing strategy
        integration_testing = (
            "Integration tests for component interactions and external dependencies"
        )

        # Performance testing strategy
        performance_testing = (
            "Performance testing for critical paths and scalability requirements"
        )

        return TestingStrategy(
            unit_testing=unit_testing,
            integration_testing=integration_testing,
            performance_testing=performance_testing,
            test_coverage_target=target_coverage,
        )

    def _convert_attributes_to_fields(self, attributes: list[str]) -> dict[str, str]:
        """Convert attribute list to field dictionary."""
        fields = {}

        for attr in attributes:
            # Simple type inference based on attribute name
            attr_lower = attr.lower()
            if any(keyword in attr_lower for keyword in ["id", "key"]):
                fields[attr] = "int"
            elif any(
                keyword in attr_lower for keyword in ["name", "title", "description"]
            ):
                fields[attr] = "str"
            elif any(
                keyword in attr_lower
                for keyword in ["date", "time", "created", "updated"]
            ):
                fields[attr] = "datetime"
            elif any(keyword in attr_lower for keyword in ["count", "number", "size"]):
                fields[attr] = "int"
            elif any(
                keyword in attr_lower for keyword in ["active", "enabled", "valid"]
            ):
                fields[attr] = "bool"
            else:
                fields[attr] = "str"

        return fields

    def _generate_basic_fields_for_model(self, model_name: str) -> dict[str, str]:
        """Generate basic fields for a model based on its name."""
        fields = {"id": "int"}

        model_lower = model_name.lower()

        if model_lower == "user":
            fields.update(
                {
                    "username": "str",
                    "email": "str",
                    "created_at": "datetime",
                    "is_active": "bool",
                }
            )
        elif model_lower == "datarecord":
            fields.update(
                {
                    "name": "str",
                    "data": "dict",
                    "created_at": "datetime",
                    "updated_at": "datetime",
                }
            )
        elif model_lower == "session":
            fields.update(
                {
                    "user_id": "int",
                    "token": "str",
                    "expires_at": "datetime",
                    "is_active": "bool",
                }
            )
        elif model_lower == "configuration":
            fields.update(
                {
                    "key": "str",
                    "value": "str",
                    "description": "str",
                    "updated_at": "datetime",
                }
            )
        else:
            fields.update(
                {"name": "str", "description": "str", "created_at": "datetime"}
            )

        return fields

    def _generate_basic_relationships_for_model(
        self, model_name: str, all_models: set
    ) -> list[str]:
        """Generate basic relationships for a model."""
        relationships = []

        model_lower = model_name.lower()

        if model_lower == "user" and "Session" in all_models:
            relationships.append("One-to-many relationship with Session")

        if model_lower == "session" and "User" in all_models:
            relationships.append("Many-to-one relationship with User")

        if model_lower == "datarecord" and "User" in all_models:
            relationships.append("Many-to-one relationship with User (owner)")

        return relationships

    def _extract_methods_from_api_data(self, api_data: dict[str, Any]) -> list[str]:
        """Extract methods from API data."""
        methods = []

        if "parameters" in api_data:
            params = ", ".join(api_data["parameters"])
            method_name = api_data.get("name", "unknown_method")
            return_type = api_data.get("return_type", "Any")
            methods.append(f"{method_name}({params}) -> {return_type}")
        else:
            methods.append(f"{api_data.get('name', 'unknown_method')}()")

        return methods

    def _parse_feedback(self, feedback: str) -> dict[str, Any]:
        """Parse user feedback to understand requested changes."""
        feedback_lower = feedback.lower()
        refinements = {
            "modify_overview": None,
            "add_components": [],
            "modify_components": [],
            "add_interfaces": [],
            "modify_error_handling": None,
            "modify_testing": None,
        }

        # Simple keyword-based parsing
        if "overview" in feedback_lower:
            refinements["modify_overview"] = feedback

        if "component" in feedback_lower:
            if "add" in feedback_lower or "more" in feedback_lower:
                refinements["add_components"] = [
                    "Additional component based on feedback"
                ]
            else:
                refinements["modify_components"] = [feedback]

        if "interface" in feedback_lower and "add" in feedback_lower:
            refinements["add_interfaces"] = ["Additional interface based on feedback"]

        if "error" in feedback_lower or "exception" in feedback_lower:
            refinements["modify_error_handling"] = feedback

        if "test" in feedback_lower:
            refinements["modify_testing"] = feedback

        # If no specific category matched, treat as general overview feedback
        if not any(refinements.values()):
            refinements["modify_overview"] = feedback

        return refinements

    def _apply_refinements(
        self, design: DesignDocument, refinements: dict[str, Any]
    ) -> DesignDocument:
        """Apply refinements to design document."""
        # Create a copy of the design
        refined_design = DesignDocument(
            overview=design.overview,
            architecture=design.architecture,
            components=design.components.copy(),
            data_models=design.data_models.copy(),
            interfaces=design.interfaces.copy(),
            error_handling=design.error_handling,
            testing_strategy=design.testing_strategy,
            version=design.version,
            approved=False,
        )

        # Apply overview changes
        if refinements["modify_overview"]:
            refined_design.overview = (
                f"{design.overview} {refinements['modify_overview']}"
            )

        # Add new components
        for new_comp_text in refinements["add_components"]:
            new_component = ComponentSpec(
                name="Additional Component",
                description=new_comp_text,
                interfaces=[],
                dependencies=[],
            )
            refined_design.components.append(new_component)

        # Add new interfaces
        for new_interface_text in refinements["add_interfaces"]:
            new_interface = InterfaceSpec(
                name="IAdditionalInterface",
                methods=["additional_method()"],
                description=new_interface_text,
            )
            refined_design.interfaces.append(new_interface)

        # Modify error handling
        if refinements["modify_error_handling"]:
            refined_design.error_handling.logging_strategy = f"{design.error_handling.logging_strategy} {refinements['modify_error_handling']}"

        # Modify testing strategy
        if refinements["modify_testing"]:
            refined_design.testing_strategy.unit_testing = f"{design.testing_strategy.unit_testing} {refinements['modify_testing']}"

        return refined_design

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

    async def _retrieve_architecture_patterns(
        self,
        spec: SpecificationDocument,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant architecture patterns via vector search.
        
        Args:
            spec: Specification document to search for patterns
            
        Returns:
            List of relevant code chunks with architecture patterns
        """
        if not self.vector_db:
            logger.warning("Vector database not available, skipping pattern retrieval")
            return []

        try:
            # Build search query from specification
            query_parts = [spec.introduction]
            query_parts.extend(spec.key_features[:3])  # Top 3 features
            query = " ".join(query_parts)

            # Search for relevant architecture patterns
            results = await self.vector_db.search(
                query=query,
                top_k=5,
                filter_metadata={"type": "architecture"},  # Prefer architecture-related code
            )

            logger.info(f"Retrieved {len(results)} relevant architecture patterns")
            return results

        except Exception as e:
            logger.warning(f"Failed to retrieve architecture patterns: {e}")
            return []

    def _build_design_context(
        self,
        spec: SpecificationDocument,
        analysis: DesignAnalysis,
        relevant_patterns: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build context dictionary for design prompt template.
        
        Args:
            spec: Specification document
            analysis: Design analysis from codebase
            relevant_patterns: Relevant code patterns from vector search
            
        Returns:
            Context dictionary for prompt template
        """
        # Format specification
        spec_text = self._format_specification_for_context(spec)

        # Format existing architecture
        architecture_text = self._format_architecture_for_context(analysis)

        # Format code patterns
        patterns_text = self._format_patterns_for_context(analysis, relevant_patterns)

        # Format similar implementations
        similar_impl_text = self._format_similar_implementations(relevant_patterns)

        context = {
            "specification": spec_text,
            "existing_architecture": architecture_text,
            "code_patterns": patterns_text,
            "similar_implementations": similar_impl_text,
        }

        return context

    def _format_specification_for_context(self, spec: SpecificationDocument) -> str:
        """Format specification for prompt context.
        
        Args:
            spec: Specification document
            
        Returns:
            Formatted specification text
        """
        lines = []

        lines.append(f"**Introduction:** {spec.introduction}")
        lines.append("")

        if spec.key_features:
            lines.append("**Key Features:**")
            for feature in spec.key_features[:5]:  # Top 5 features
                lines.append(f"- {feature}")
            lines.append("")

        if spec.functional_requirements:
            lines.append("**Functional Requirements:**")
            for req in spec.functional_requirements[:10]:  # Top 10 requirements
                lines.append(f"- {req.id}: {req.user_story}")
            lines.append("")

        return "\n".join(lines)

    def _format_architecture_for_context(self, analysis: DesignAnalysis) -> str:
        """Format existing architecture for prompt context.
        
        Args:
            analysis: Design analysis from codebase
            
        Returns:
            Formatted architecture text
        """
        lines = []

        if analysis.architecture_overview:
            lines.append(f"**Overview:** {analysis.architecture_overview}")
            lines.append("")

        if analysis.design_patterns:
            lines.append("**Design Patterns:**")
            for pattern in analysis.design_patterns:
                lines.append(f"- {pattern}")
            lines.append("")

        if analysis.components:
            lines.append("**Existing Components:**")
            for comp in analysis.components[:5]:  # Top 5 components
                lines.append(f"- {comp.name}: {comp.purpose}")
            lines.append("")

        if analysis.quality_metrics:
            lines.append("**Quality Metrics:**")
            for metric, value in list(analysis.quality_metrics.items())[:3]:
                lines.append(f"- {metric}: {value}")
            lines.append("")

        return "\n".join(lines) if lines else "No existing architecture information available."

    def _format_patterns_for_context(
        self,
        analysis: DesignAnalysis,
        relevant_patterns: list[dict[str, Any]],
    ) -> str:
        """Format code patterns for prompt context.
        
        Args:
            analysis: Design analysis from codebase
            relevant_patterns: Relevant patterns from vector search
            
        Returns:
            Formatted patterns text
        """
        lines = []

        # Add patterns from analysis
        if analysis.design_patterns:
            lines.append("**Detected Patterns:**")
            for pattern in analysis.design_patterns:
                lines.append(f"- {pattern}")
            lines.append("")

        # Add patterns from vector search
        if relevant_patterns:
            lines.append("**Code Examples:**")
            for i, pattern in enumerate(relevant_patterns[:3], 1):
                content = pattern.get("content", "")
                file_path = pattern.get("metadata", {}).get("file_path", "unknown")
                lines.append(f"\n**Example {i}** (from {file_path}):")
                lines.append(f"```python\n{content[:500]}...\n```")  # Truncate long examples
            lines.append("")

        return "\n".join(lines) if lines else "No specific patterns detected."

    def _format_similar_implementations(
        self,
        relevant_patterns: list[dict[str, Any]],
    ) -> str:
        """Format similar implementations for prompt context.
        
        Args:
            relevant_patterns: Relevant patterns from vector search
            
        Returns:
            Formatted similar implementations text
        """
        if not relevant_patterns:
            return "No similar implementations found in codebase."

        lines = []
        lines.append("**Similar Implementations in Codebase:**")

        for i, pattern in enumerate(relevant_patterns[:3], 1):
            content = pattern.get("content", "")
            metadata = pattern.get("metadata", {})
            file_path = metadata.get("file_path", "unknown")

            lines.append(f"\n**Implementation {i}** (from {file_path}):")
            lines.append(f"```python\n{content[:400]}...\n```")  # Truncate for context

        return "\n".join(lines)

    def _parse_ai_design(
        self,
        design_content: str,
        spec: SpecificationDocument,
        analysis: DesignAnalysis,
    ) -> DesignDocument:
        """Parse AI-generated design content into structured document.
        
        Args:
            design_content: Raw design content from AI
            spec: Original specification document
            analysis: Design analysis from codebase
            
        Returns:
            Structured design document
        """
        # For now, use the rule-based generation as fallback
        # In a production system, you would parse the AI-generated markdown
        # into structured components
        logger.info("Parsing AI-generated design content")

        # Use rule-based generation to create structure
        # The AI content would be used to enhance the descriptions
        design = self.generate_from_specification(spec, analysis)

        # Enhance with AI-generated content
        # In a full implementation, you would parse sections from design_content
        # and update the structured document accordingly

        # For now, prepend AI overview to the generated overview
        if "## Overview" in design_content or "# Overview" in design_content:
            # Extract overview section (simplified parsing)
            overview_start = design_content.find("Overview")
            if overview_start != -1:
                overview_end = design_content.find("##", overview_start + 10)
                if overview_end == -1:
                    overview_end = len(design_content)
                ai_overview = design_content[overview_start:overview_end].strip()
                # Clean up markdown headers
                ai_overview = ai_overview.replace("## Overview", "").replace("# Overview", "").strip()
                if ai_overview:
                    design.overview = ai_overview[:1000]  # Use AI overview

        return design
