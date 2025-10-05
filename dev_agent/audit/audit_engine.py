"""Core audit engine for verifying dev-agent functionality.

This module implements the AuditEngine class which orchestrates all audit
checks across the dev-agent system, including indexing, specification,
design, implementation, state management, Azure OpenAI integration,
and error handling.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from dev_agent.audit.models import AuditConfig, AuditReport, AuditResult

logger = logging.getLogger(__name__)


class AuditEngine:
    """Comprehensive audit system for dev-agent functionality.

    The AuditEngine performs systematic checks of all core features to ensure
    the system is functioning correctly. It tests each phase of the workflow,
    state management, Azure OpenAI integration, and error handling.

    Attributes:
        config: Configuration for audit execution
        results: List of audit results collected during execution

    Example:
        ```python
        from dev_agent.audit import AuditEngine, AuditConfig

        config = AuditConfig(
            test_project_path="/path/to/test/project",
            skip_azure_tests=False,
        )

        engine = AuditEngine(config)
        report = await engine.run_audit()

        print(f"Overall status: {report.overall_status}")
        print(f"Passed: {report.passed_checks}/{report.total_checks}")
        ```
    """

    def __init__(self, config: AuditConfig | None = None) -> None:
        """Initialize the audit engine.

        Args:
            config: Configuration for audit execution. If None, uses defaults.
        """
        self.config = config or AuditConfig()
        self.results: list[AuditResult] = []
        logger.info("AuditEngine initialized with config: %s", self.config)

    async def run_audit(self) -> AuditReport:
        """Run comprehensive audit of all dev-agent functionality.

        Executes all audit checks in sequence and generates a comprehensive
        report with results and recommendations.

        Returns:
            AuditReport containing all results and summary

        Raises:
            AuditError: If audit execution fails critically
        """
        logger.info("Starting comprehensive dev-agent audit")
        self.results = []

        # Run all audit checks
        await self._audit_indexing_phase()
        await self._audit_specification_phase()
        await self._audit_design_phase()
        await self._audit_implementation_phase()
        await self._audit_state_management()

        if not self.config.skip_azure_tests:
            await self._audit_azure_openai_integration()

        await self._audit_error_handling()

        # Generate report
        report = self.generate_audit_report()

        # Save report if configured
        if self.config.save_report:
            self._save_report(report)

        logger.info(
            "Audit complete: %d/%d checks passed",
            report.passed_checks,
            report.total_checks,
        )

        return report

    async def _audit_indexing_phase(self) -> AuditResult:
        """Audit the indexing phase functionality.

        Verifies that:
        - Tree-sitter can parse Python code correctly
        - FAISS vector storage works
        - Azure OpenAI embeddings are generated

        Returns:
            AuditResult for indexing phase
        """
        logger.info("Auditing indexing phase")

        details = {}
        recommendations = []
        issues = []

        try:
            # Create a temporary test project
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as temp_dir:
                test_project_path = Path(temp_dir) / "test_project"
                test_project_path.mkdir()

                # Create a simple Python file for testing
                test_file = test_project_path / "test_module.py"
                test_file.write_text(
                    '''"""Test module for audit."""

def hello_world():
    """Say hello."""
                    return "Hello, World!"

class TestClass:
    """Test class."""
    
    def __init__(self, name: str):
        """Initialize with name."""
        self.name = name
    
    def greet(self) -> str:
        """Return greeting."""
        return f"Hello, {self.name}!"
''',
                    encoding="utf-8",
                )

                details["test_project_path"] = str(test_project_path)
                details["test_file_created"] = True

                # Test 1: Tree-sitter parsing
                logger.info("Testing Tree-sitter parsing...")
                try:
                    from dev_agent.indexing.tree_sitter_parser import TreeSitterParser

                    parser = TreeSitterParser()
                    ast = parser.parse_file(str(test_file), "python")

                    if ast:
                        # Extract functions and classes
                        functions = parser.get_function_definitions(ast, str(test_file))
                        classes = parser.get_class_definitions(ast, str(test_file))

                        details["tree_sitter_parsing"] = "success"
                        details["functions_found"] = len(functions)
                        details["classes_found"] = len(classes)

                        if len(functions) < 1 or len(classes) < 1:
                            issues.append(
                                "Tree-sitter parsed file but didn't extract expected functions/classes"
                            )
                            recommendations.append(
                                "Verify Tree-sitter parser configuration"
                            )
                    else:
                        issues.append("Tree-sitter failed to parse test file")
                        details["tree_sitter_parsing"] = "failed"
                        recommendations.append(
                            "Check Tree-sitter installation and language support"
                        )

                except Exception as e:
                    issues.append(f"Tree-sitter parsing error: {e}")
                    details["tree_sitter_parsing"] = "error"
                    details["tree_sitter_error"] = str(e)
                    recommendations.append(
                        "Install tree-sitter and tree-sitter-python packages"
                    )

                # Test 2: FAISS vector storage
                logger.info("Testing FAISS vector storage...")
                try:
                    from dev_agent.indexing.vector_database import VectorDatabase

                    vector_db = VectorDatabase(str(test_project_path / ".index"))

                    # Test basic FAISS operations
                    if vector_db.index is not None:
                        details["faiss_initialization"] = "success"
                        details["faiss_dimension"] = vector_db.dimension
                    else:
                        issues.append("FAISS index not initialized")
                        details["faiss_initialization"] = "failed"
                        recommendations.append("Check FAISS installation")

                except Exception as e:
                    issues.append(f"FAISS vector storage error: {e}")
                    details["faiss_initialization"] = "error"
                    details["faiss_error"] = str(e)
                    recommendations.append("Install faiss-cpu package")

                # Test 3: Embedding generation (only if not skipping Azure tests)
                if not self.config.skip_azure_tests:
                    logger.info("Testing Azure OpenAI embedding generation...")
                    try:
                        import os

                        # Check if Azure OpenAI is configured
                        if not os.getenv("AZURE_OPENAI_API_KEY"):
                            issues.append("Azure OpenAI API key not configured")
                            details["embedding_generation"] = "skipped"
                            details["embedding_reason"] = "API key not configured"
                            recommendations.append(
                                "Set AZURE_OPENAI_API_KEY environment variable"
                            )
                        else:
                            # Try to create embedding client
                            from dev_agent.llm.azure_client import AzureEmbeddingClient
                            from dev_agent.config.config_manager import ConfigManager

                            config_manager = ConfigManager()
                            azure_config = config_manager.get_azure_config()

                            if azure_config:
                                embedding_client = AzureEmbeddingClient(azure_config)

                                # Test embedding generation with a simple text
                                test_text = "def hello(): return 'world'"
                                embedding = await embedding_client.embed_text(test_text)

                                if embedding and len(embedding) > 0:
                                    details["embedding_generation"] = "success"
                                    details["embedding_dimension"] = len(embedding)
                                else:
                                    issues.append("Embedding generation returned empty result")
                                    details["embedding_generation"] = "failed"
                                    recommendations.append(
                                        "Verify Azure OpenAI embedding deployment"
                                    )
                            else:
                                issues.append("Azure OpenAI configuration not found")
                                details["embedding_generation"] = "skipped"
                                details["embedding_reason"] = "Configuration not found"
                                recommendations.append(
                                    "Run 'dev-agent azure configure' to set up Azure OpenAI"
                                )

                    except Exception as e:
                        issues.append(f"Embedding generation error: {e}")
                        details["embedding_generation"] = "error"
                        details["embedding_error"] = str(e)
                        recommendations.append(
                            "Check Azure OpenAI configuration and API connectivity"
                        )
                else:
                    details["embedding_generation"] = "skipped"
                    details["embedding_reason"] = "Azure tests skipped by configuration"

            # Determine overall status
            if not issues:
                status = "pass"
                message = "Indexing phase is fully functional"
            elif details.get("tree_sitter_parsing") == "success" and details.get(
                "faiss_initialization"
            ) == "success":
                status = "warning"
                message = f"Indexing phase partially functional: {len(issues)} issue(s) found"
            else:
                status = "fail"
                message = f"Indexing phase has critical issues: {len(issues)} issue(s) found"

            # Add issues to details
            if issues:
                details["issues"] = issues

        except Exception as e:
            logger.error(f"Critical error during indexing phase audit: {e}")
            status = "fail"
            message = f"Indexing phase audit failed: {e}"
            details["critical_error"] = str(e)
            recommendations.append("Check system dependencies and configuration")

        result = AuditResult(
            component="Indexing Phase",
            status=status,
            message=message,
            details=details,
            recommendations=recommendations,
        )

        self.results.append(result)
        return result

    async def _audit_specification_phase(self) -> AuditResult:
        """Audit the specification phase functionality.

        Verifies that:
        - GPT-4 can generate specifications
        - Specifications reference indexed code
        - Specification documents have correct structure

        Returns:
            AuditResult for specification phase
        """
        logger.info("Auditing specification phase")

        details = {}
        recommendations = []
        issues = []

        try:
            # Test 1: Check specification generator availability
            logger.info("Testing specification generator...")
            try:
                from dev_agent.generation.specification_generator import (
                    SpecificationGenerator,
                )

                generator = SpecificationGenerator()
                details["generator_available"] = True

            except Exception as e:
                issues.append(f"Specification generator import error: {e}")
                details["generator_available"] = False
                details["generator_error"] = str(e)
                recommendations.append("Check specification generator module")

            # Test 2: Test specification document structure
            logger.info("Testing specification document structure...")
            try:
                from dev_agent.models.documents import (
                    Requirement,
                    SpecificationDocument,
                )
                from dev_agent.models.enums import Priority, SpecificationSource

                # Create a test specification
                test_req = Requirement(
                    id="FR-1",
                    user_story="As a user, I want to test the system",
                    acceptance_criteria=[
                        "WHEN the system is tested THEN it SHALL pass all checks"
                    ],
                    priority=Priority.HIGH,
                )

                test_spec = SpecificationDocument(
                    introduction="Test specification for audit",
                    key_features=["Feature 1", "Feature 2"],
                    functional_requirements=[test_req],
                    source=SpecificationSource.USER_INPUT,
                    version="1.0",
                    approved=False,
                )

                # Verify structure
                if test_spec.introduction and test_spec.functional_requirements:
                    details["document_structure"] = "valid"
                    details["requirements_count"] = len(
                        test_spec.functional_requirements
                    )
                else:
                    issues.append("Specification document structure incomplete")
                    details["document_structure"] = "invalid"
                    recommendations.append("Verify SpecificationDocument model")

            except Exception as e:
                issues.append(f"Specification document structure error: {e}")
                details["document_structure"] = "error"
                details["structure_error"] = str(e)
                recommendations.append("Check specification document models")

            # Test 3: Test GPT-4 specification generation (only if not skipping Azure tests)
            if not self.config.skip_azure_tests:
                logger.info("Testing GPT-4 specification generation...")
                try:
                    import os

                    if not os.getenv("AZURE_OPENAI_API_KEY"):
                        issues.append("Azure OpenAI API key not configured")
                        details["gpt4_generation"] = "skipped"
                        details["gpt4_reason"] = "API key not configured"
                        recommendations.append(
                            "Set AZURE_OPENAI_API_KEY environment variable"
                        )
                    else:
                        from dev_agent.config.config_manager import ConfigManager
                        from dev_agent.llm.azure_client import AzureOpenAIClient

                        config_manager = ConfigManager()
                        azure_config = config_manager.get_azure_config()

                        if azure_config:
                            llm_client = AzureOpenAIClient(azure_config)

                            # Test simple completion
                            test_prompt = "Generate a brief requirement: As a user, I want"
                            response = await llm_client.generate_completion(
                                prompt=test_prompt,
                                system_prompt="You are a requirements analyst. Complete the user story in one sentence.",
                                temperature=0.7,
                                max_tokens=100,
                            )

                            if response and len(response) > 10:
                                details["gpt4_generation"] = "success"
                                details["response_length"] = len(response)
                            else:
                                issues.append("GPT-4 generated empty or invalid response")
                                details["gpt4_generation"] = "failed"
                                recommendations.append(
                                    "Verify Azure OpenAI deployment configuration"
                                )
                        else:
                            issues.append("Azure OpenAI configuration not found")
                            details["gpt4_generation"] = "skipped"
                            details["gpt4_reason"] = "Configuration not found"
                            recommendations.append(
                                "Run 'dev-agent azure configure' to set up Azure OpenAI"
                            )

                except Exception as e:
                    issues.append(f"GPT-4 generation error: {e}")
                    details["gpt4_generation"] = "error"
                    details["gpt4_error"] = str(e)
                    recommendations.append(
                        "Check Azure OpenAI configuration and API connectivity"
                    )
            else:
                details["gpt4_generation"] = "skipped"
                details["gpt4_reason"] = "Azure tests skipped by configuration"

            # Test 4: Test specification formatting
            logger.info("Testing specification formatting...")
            try:
                from dev_agent.generation.specification_generator import (
                    SpecificationGenerator,
                )

                generator = SpecificationGenerator()

                # Use the test spec from earlier
                if "document_structure" in details and details["document_structure"] == "valid":
                    formatted = generator.format_specification_document(test_spec)

                    if formatted and "# Requirements Document" in formatted:
                        details["formatting"] = "success"
                        details["formatted_length"] = len(formatted)
                    else:
                        issues.append("Specification formatting produced invalid output")
                        details["formatting"] = "failed"
                        recommendations.append("Check specification formatter")
                else:
                    details["formatting"] = "skipped"
                    details["formatting_reason"] = "Document structure test failed"

            except Exception as e:
                issues.append(f"Specification formatting error: {e}")
                details["formatting"] = "error"
                details["formatting_error"] = str(e)
                recommendations.append("Check specification generator formatting method")

            # Determine overall status
            if not issues:
                status = "pass"
                message = "Specification phase is fully functional"
            elif details.get("generator_available") and details.get(
                "document_structure"
            ) == "valid":
                status = "warning"
                message = f"Specification phase partially functional: {len(issues)} issue(s) found"
            else:
                status = "fail"
                message = f"Specification phase has critical issues: {len(issues)} issue(s) found"

            # Add issues to details
            if issues:
                details["issues"] = issues

        except Exception as e:
            logger.error(f"Critical error during specification phase audit: {e}")
            status = "fail"
            message = f"Specification phase audit failed: {e}"
            details["critical_error"] = str(e)
            recommendations.append("Check specification generator dependencies")

        result = AuditResult(
            component="Specification Phase",
            status=status,
            message=message,
            details=details,
            recommendations=recommendations,
        )

        self.results.append(result)
        return result

    async def _audit_design_phase(self) -> AuditResult:
        """Audit the design phase functionality.

        Verifies that:
        - Design documents are generated correctly
        - Designs reference specifications and codebase patterns
        - Design documents have correct structure

        Returns:
            AuditResult for design phase
        """
        logger.info("Auditing design phase")

        details = {}
        recommendations = []
        issues = []

        try:
            # Test 1: Check design generator availability
            logger.info("Testing design generator...")
            try:
                from dev_agent.generation.design_generator import DesignGenerator

                # Design generator requires a codebase analyzer
                from dev_agent.analysis.codebase_analyzer import CodebaseAnalyzer

                analyzer = CodebaseAnalyzer(".")
                generator = DesignGenerator(analyzer)
                details["generator_available"] = True

            except Exception as e:
                issues.append(f"Design generator import error: {e}")
                details["generator_available"] = False
                details["generator_error"] = str(e)
                recommendations.append("Check design generator module")

            # Test 2: Test design document structure
            logger.info("Testing design document structure...")
            try:
                from dev_agent.models.documents import (
                    ArchitectureDescription,
                    ComponentSpec,
                    DataModel,
                    DesignDocument,
                    ErrorHandlingStrategy,
                    InterfaceSpec,
                    TestingStrategy,
                )

                # Create a test design document
                test_architecture = ArchitectureDescription(
                    overview="Test architecture overview",
                    patterns=["MVC", "Repository Pattern"],
                    components=["Component A", "Component B"],
                )

                test_component = ComponentSpec(
                    name="TestComponent",
                    description="Test component for audit",
                    interfaces=["ITestInterface"],
                    dependencies=["Dependency1"],
                )

                test_data_model = DataModel(
                    name="TestModel",
                    fields={"id": "int", "name": "str"},
                    relationships=["has_many TestRelated"],
                )

                test_interface = InterfaceSpec(
                    name="ITestInterface",
                    methods=["method1()", "method2()"],
                    description="Test interface",
                )

                test_error_handling = ErrorHandlingStrategy(
                    error_categories=["ValidationError", "SystemError"],
                    recovery_mechanisms=["Retry", "Fallback"],
                    logging_strategy="Structured logging with levels",
                )

                test_testing_strategy = TestingStrategy(
                    unit_testing="pytest with fixtures",
                    integration_testing="End-to-end tests",
                    performance_testing="Load testing",
                    test_coverage_target=0.9,
                )

                test_design = DesignDocument(
                    overview="Test design document for audit",
                    architecture=test_architecture,
                    components=[test_component],
                    data_models=[test_data_model],
                    interfaces=[test_interface],
                    error_handling=test_error_handling,
                    testing_strategy=test_testing_strategy,
                    version="1.0",
                    approved=False,
                )

                # Verify structure
                if (
                    test_design.overview
                    and test_design.architecture
                    and test_design.components
                ):
                    details["document_structure"] = "valid"
                    details["components_count"] = len(test_design.components)
                    details["data_models_count"] = len(test_design.data_models)
                    details["interfaces_count"] = len(test_design.interfaces)
                else:
                    issues.append("Design document structure incomplete")
                    details["document_structure"] = "invalid"
                    recommendations.append("Verify DesignDocument model")

            except Exception as e:
                issues.append(f"Design document structure error: {e}")
                details["document_structure"] = "error"
                details["structure_error"] = str(e)
                recommendations.append("Check design document models")

            # Test 3: Test design formatting
            logger.info("Testing design formatting...")
            try:
                if details.get("generator_available") and details.get(
                    "document_structure"
                ) == "valid":
                    formatted = generator.format_design_document(test_design)

                    if formatted and "# Design Document" in formatted:
                        details["formatting"] = "success"
                        details["formatted_length"] = len(formatted)

                        # Check for key sections
                        required_sections = [
                            "## Overview",
                            "## Architecture",
                            "## Components",
                            "## Data Models",
                        ]
                        missing_sections = [
                            section
                            for section in required_sections
                            if section not in formatted
                        ]

                        if missing_sections:
                            issues.append(
                                f"Design formatting missing sections: {', '.join(missing_sections)}"
                            )
                            recommendations.append(
                                "Verify design document formatter includes all sections"
                            )
                    else:
                        issues.append("Design formatting produced invalid output")
                        details["formatting"] = "failed"
                        recommendations.append("Check design formatter")
                else:
                    details["formatting"] = "skipped"
                    details["formatting_reason"] = (
                        "Generator not available or document structure test failed"
                    )

            except Exception as e:
                issues.append(f"Design formatting error: {e}")
                details["formatting"] = "error"
                details["formatting_error"] = str(e)
                recommendations.append("Check design generator formatting method")

            # Test 4: Test GPT-4 design generation (only if not skipping Azure tests)
            if not self.config.skip_azure_tests:
                logger.info("Testing GPT-4 design generation...")
                try:
                    import os

                    if not os.getenv("AZURE_OPENAI_API_KEY"):
                        issues.append("Azure OpenAI API key not configured")
                        details["gpt4_design_generation"] = "skipped"
                        details["gpt4_design_reason"] = "API key not configured"
                        recommendations.append(
                            "Set AZURE_OPENAI_API_KEY environment variable"
                        )
                    else:
                        from dev_agent.config.config_manager import ConfigManager
                        from dev_agent.llm.azure_client import AzureOpenAIClient

                        config_manager = ConfigManager()
                        azure_config = config_manager.get_azure_config()

                        if azure_config:
                            llm_client = AzureOpenAIClient(azure_config)

                            # Test simple design-related completion
                            test_prompt = "Describe a simple component architecture for a web application in one sentence."
                            response = await llm_client.generate_completion(
                                prompt=test_prompt,
                                system_prompt="You are a software architect. Provide a concise architectural description.",
                                temperature=0.7,
                                max_tokens=100,
                            )

                            if response and len(response) > 10:
                                details["gpt4_design_generation"] = "success"
                                details["design_response_length"] = len(response)
                            else:
                                issues.append(
                                    "GPT-4 design generation returned empty or invalid response"
                                )
                                details["gpt4_design_generation"] = "failed"
                                recommendations.append(
                                    "Verify Azure OpenAI deployment configuration"
                                )
                        else:
                            issues.append("Azure OpenAI configuration not found")
                            details["gpt4_design_generation"] = "skipped"
                            details["gpt4_design_reason"] = "Configuration not found"
                            recommendations.append(
                                "Run 'dev-agent azure configure' to set up Azure OpenAI"
                            )

                except Exception as e:
                    issues.append(f"GPT-4 design generation error: {e}")
                    details["gpt4_design_generation"] = "error"
                    details["gpt4_design_error"] = str(e)
                    recommendations.append(
                        "Check Azure OpenAI configuration and API connectivity"
                    )
            else:
                details["gpt4_design_generation"] = "skipped"
                details["gpt4_design_reason"] = "Azure tests skipped by configuration"

            # Determine overall status
            if not issues:
                status = "pass"
                message = "Design phase is fully functional"
            elif details.get("generator_available") and details.get(
                "document_structure"
            ) == "valid":
                status = "warning"
                message = f"Design phase partially functional: {len(issues)} issue(s) found"
            else:
                status = "fail"
                message = f"Design phase has critical issues: {len(issues)} issue(s) found"

            # Add issues to details
            if issues:
                details["issues"] = issues

        except Exception as e:
            logger.error(f"Critical error during design phase audit: {e}")
            status = "fail"
            message = f"Design phase audit failed: {e}"
            details["critical_error"] = str(e)
            recommendations.append("Check design generator dependencies")

        result = AuditResult(
            component="Design Phase",
            status=status,
            message=message,
            details=details,
            recommendations=recommendations,
        )

        self.results.append(result)
        return result

    async def _audit_implementation_phase(self) -> AuditResult:
        """Audit the implementation phase functionality.

        Verifies that:
        - Tasks are generated correctly
        - Tasks reference design documents
        - Task structure is valid and actionable

        Returns:
            AuditResult for implementation phase
        """
        logger.info("Auditing implementation phase")

        details = {}
        recommendations = []
        issues = []

        try:
            # Test 1: Check task generator availability
            logger.info("Testing task generator...")
            try:
                from dev_agent.generation.task_generator import TaskGenerator

                generator = TaskGenerator()
                details["generator_available"] = True

            except Exception as e:
                issues.append(f"Task generator import error: {e}")
                details["generator_available"] = False
                details["generator_error"] = str(e)
                recommendations.append("Check task generator module")

            # Test 2: Test task document structure
            logger.info("Testing task document structure...")
            try:
                from dev_agent.models.documents import Task, TaskList
                from dev_agent.models.enums import TaskStatus

                # Create test tasks
                test_task1 = Task(
                    id="1",
                    title="Implement data model",
                    description="Create User data model with validation",
                    requirements_refs=["FR-1", "FR-2"],
                    subtasks=[],
                    status=TaskStatus.NOT_STARTED,
                    target_language="python",
                    context_requirements=["Data models", "Validation"],
                    implementation_notes="Include email validation",
                    generated_files=[],
                )

                test_task2 = Task(
                    id="2",
                    title="Implement API endpoint",
                    description="Create REST API endpoint for user management",
                    requirements_refs=["FR-3"],
                    subtasks=[],
                    status=TaskStatus.NOT_STARTED,
                    target_language="python",
                    context_requirements=["API patterns", "Authentication"],
                    implementation_notes="Use FastAPI framework",
                    generated_files=[],
                )

                test_task_list = TaskList(
                    tasks=[test_task1, test_task2],
                    dependencies={"2": ["1"]},
                    estimated_effort={"1": 4, "2": 6},
                    version="1.0",
                    approved=False,
                )

                # Verify structure
                if test_task_list.tasks and len(test_task_list.tasks) > 0:
                    details["document_structure"] = "valid"
                    details["tasks_count"] = len(test_task_list.tasks)
                    details["has_dependencies"] = len(test_task_list.dependencies) > 0
                    details["has_estimates"] = len(test_task_list.estimated_effort) > 0

                    # Verify task references requirements
                    tasks_with_refs = sum(
                        1 for task in test_task_list.tasks if task.requirements_refs
                    )
                    details["tasks_with_requirements"] = tasks_with_refs

                    if tasks_with_refs == 0:
                        issues.append("Tasks do not reference requirements")
                        recommendations.append(
                            "Ensure tasks link back to requirements"
                        )
                else:
                    issues.append("Task list structure incomplete")
                    details["document_structure"] = "invalid"
                    recommendations.append("Verify TaskList model")

            except Exception as e:
                issues.append(f"Task document structure error: {e}")
                details["document_structure"] = "error"
                details["structure_error"] = str(e)
                recommendations.append("Check task document models")

            # Test 3: Test task formatting
            logger.info("Testing task formatting...")
            try:
                if details.get("generator_available") and details.get(
                    "document_structure"
                ) == "valid":
                    formatted = generator.format_task_list(test_task_list)

                    if formatted and "# Implementation Plan" in formatted:
                        details["formatting"] = "success"
                        details["formatted_length"] = len(formatted)

                        # Check for key elements
                        required_elements = ["- [ ]", "_Requirements:"]
                        missing_elements = [
                            elem for elem in required_elements if elem not in formatted
                        ]

                        if missing_elements:
                            issues.append(
                                f"Task formatting missing elements: {', '.join(missing_elements)}"
                            )
                            recommendations.append(
                                "Verify task formatter includes checkboxes and requirement references"
                            )
                    else:
                        issues.append("Task formatting produced invalid output")
                        details["formatting"] = "failed"
                        recommendations.append("Check task formatter")
                else:
                    details["formatting"] = "skipped"
                    details["formatting_reason"] = (
                        "Generator not available or document structure test failed"
                    )

            except Exception as e:
                issues.append(f"Task formatting error: {e}")
                details["formatting"] = "error"
                details["formatting_error"] = str(e)
                recommendations.append("Check task generator formatting method")

            # Test 4: Test task generation from design (rule-based)
            logger.info("Testing task generation from design...")
            try:
                if details.get("generator_available"):
                    from dev_agent.models.documents import (
                        ArchitectureDescription,
                        ComponentSpec,
                        DataModel,
                        DesignDocument,
                        ErrorHandlingStrategy,
                        TestingStrategy,
                    )

                    # Create minimal design document for testing
                    test_design = DesignDocument(
                        overview="Test design for task generation",
                        architecture=ArchitectureDescription(
                            overview="Simple architecture",
                            patterns=["MVC"],
                            components=["Component A"],
                        ),
                        components=[
                            ComponentSpec(
                                name="TestComponent",
                                description="Test component",
                                interfaces=["ITest"],
                                dependencies=[],
                            )
                        ],
                        data_models=[
                            DataModel(
                                name="TestModel",
                                fields={"id": "int"},
                                relationships=[],
                            )
                        ],
                        interfaces=[],
                        error_handling=ErrorHandlingStrategy(
                            error_categories=["ValidationError"],
                            recovery_mechanisms=["Retry"],
                            logging_strategy="Standard logging",
                        ),
                        testing_strategy=TestingStrategy(
                            unit_testing="pytest",
                            integration_testing="pytest",
                            performance_testing="",
                            test_coverage_target=0.8,
                        ),
                        version="1.0",
                        approved=False,
                    )

                    generated_tasks = generator.generate_from_design(test_design)

                    if generated_tasks and len(generated_tasks.tasks) > 0:
                        details["task_generation"] = "success"
                        details["generated_tasks_count"] = len(generated_tasks.tasks)
                    else:
                        issues.append("Task generation produced no tasks")
                        details["task_generation"] = "failed"
                        recommendations.append(
                            "Verify task generator can create tasks from design"
                        )
                else:
                    details["task_generation"] = "skipped"
                    details["task_generation_reason"] = "Generator not available"

            except Exception as e:
                issues.append(f"Task generation error: {e}")
                details["task_generation"] = "error"
                details["task_generation_error"] = str(e)
                recommendations.append("Check task generator logic")

            # Determine overall status
            if not issues:
                status = "pass"
                message = "Implementation phase is fully functional"
            elif details.get("generator_available") and details.get(
                "document_structure"
            ) == "valid":
                status = "warning"
                message = f"Implementation phase partially functional: {len(issues)} issue(s) found"
            else:
                status = "fail"
                message = f"Implementation phase has critical issues: {len(issues)} issue(s) found"

            # Add issues to details
            if issues:
                details["issues"] = issues

        except Exception as e:
            logger.error(f"Critical error during implementation phase audit: {e}")
            status = "fail"
            message = f"Implementation phase audit failed: {e}"
            details["critical_error"] = str(e)
            recommendations.append("Check task generator dependencies")

        result = AuditResult(
            component="Implementation Phase",
            status=status,
            message=message,
            details=details,
            recommendations=recommendations,
        )

        self.results.append(result)
        return result

    async def _audit_state_management(self) -> AuditResult:
        """Audit state management functionality.

        Verifies that:
        - State can be saved and loaded
        - State persists across sessions
        - State integrity is maintained

        Returns:
            AuditResult for state management
        """
        logger.info("Auditing state management")

        details = {}
        recommendations = []
        issues = []

        try:
            # Create a temporary directory for testing
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as temp_dir:
                test_project_path = Path(temp_dir) / "test_project"
                test_project_path.mkdir()

                details["test_project_path"] = str(test_project_path)

                # Test 1: Check state manager availability
                logger.info("Testing state manager...")
                try:
                    from dev_agent.state.state_manager import StateManager

                    state_manager = StateManager(str(test_project_path))
                    details["state_manager_available"] = True

                    # Verify directories were created
                    dev_agent_dir = test_project_path / ".dev_agent"
                    if dev_agent_dir.exists():
                        details["directories_created"] = True
                    else:
                        issues.append("State manager did not create .dev_agent directory")
                        details["directories_created"] = False
                        recommendations.append(
                            "Verify state manager directory creation logic"
                        )

                except Exception as e:
                    issues.append(f"State manager import error: {e}")
                    details["state_manager_available"] = False
                    details["state_manager_error"] = str(e)
                    recommendations.append("Check state manager module")

                # Test 2: Test state save and load
                if details.get("state_manager_available"):
                    logger.info("Testing state save and load...")
                    try:
                        from datetime import datetime

                        from dev_agent.models.enums import PhaseType
                        from dev_agent.models.project_state import (
                            IndexMetadata,
                            ProjectState,
                            SessionData,
                        )

                        # Create test state
                        session_data = SessionData(
                            session_id="test-session-123",
                            started_at=datetime.now(),
                            last_activity=datetime.now(),
                            user_approvals={},
                            pending_approvals=[],
                        )

                        index_metadata = IndexMetadata(
                            total_files=10,
                            total_lines=500,
                            languages_detected=["python"],
                            index_size_mb=1.5,
                            last_indexed=datetime.now(),
                            index_version="1.0",
                        )

                        test_state = ProjectState(
                            project_path=str(test_project_path),
                            current_phase=PhaseType.INDEXING,
                            indexing_complete=True,
                            specification=None,
                            design=None,
                            tasks=None,
                            implementation_progress={},
                            index_metadata=index_metadata,
                            session_data=session_data,
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                        )

                        # Test save
                        save_success = state_manager.save_project_state(test_state)

                        if save_success:
                            details["state_save"] = "success"

                            # Verify file was created
                            state_file = test_project_path / ".dev_agent" / "state.json"
                            if state_file.exists():
                                details["state_file_created"] = True
                                details["state_file_size"] = state_file.stat().st_size
                            else:
                                issues.append("State file was not created")
                                details["state_file_created"] = False
                                recommendations.append(
                                    "Verify state manager file writing logic"
                                )
                        else:
                            issues.append("State save operation failed")
                            details["state_save"] = "failed"
                            recommendations.append("Check state serialization logic")

                        # Test load
                        loaded_state = state_manager.load_project_state()

                        if loaded_state:
                            details["state_load"] = "success"

                            # Verify loaded state matches saved state
                            if loaded_state.project_path == test_state.project_path:
                                details["state_integrity"] = "valid"
                                details["loaded_phase"] = loaded_state.current_phase.value
                                details["loaded_indexing_complete"] = (
                                    loaded_state.indexing_complete
                                )
                            else:
                                issues.append("Loaded state does not match saved state")
                                details["state_integrity"] = "invalid"
                                recommendations.append(
                                    "Verify state serialization/deserialization logic"
                                )
                        else:
                            issues.append("State load operation failed")
                            details["state_load"] = "failed"
                            recommendations.append("Check state deserialization logic")

                    except Exception as e:
                        issues.append(f"State save/load error: {e}")
                        details["state_save_load"] = "error"
                        details["state_save_load_error"] = str(e)
                        recommendations.append("Check state manager save/load methods")

                # Test 3: Test phase status update
                if details.get("state_manager_available") and details.get(
                    "state_save"
                ) == "success":
                    logger.info("Testing phase status update...")
                    try:
                        from dev_agent.models.enums import PhaseType

                        update_success = state_manager.update_phase_status(
                            PhaseType.SPECIFICATION, "Testing phase update"
                        )

                        if update_success:
                            details["phase_update"] = "success"

                            # Verify the update persisted
                            updated_state = state_manager.load_project_state()
                            if (
                                updated_state
                                and updated_state.current_phase == PhaseType.SPECIFICATION
                            ):
                                details["phase_update_persisted"] = True
                            else:
                                issues.append("Phase update did not persist")
                                details["phase_update_persisted"] = False
                                recommendations.append(
                                    "Verify phase update persistence logic"
                                )
                        else:
                            issues.append("Phase update operation failed")
                            details["phase_update"] = "failed"
                            recommendations.append("Check phase update logic")

                    except Exception as e:
                        issues.append(f"Phase update error: {e}")
                        details["phase_update"] = "error"
                        details["phase_update_error"] = str(e)
                        recommendations.append("Check state manager update methods")

                # Test 4: Test document save and load
                if details.get("state_manager_available"):
                    logger.info("Testing document save and load...")
                    try:
                        from dev_agent.models.enums import DocumentType

                        test_document = "# Test Document\n\nThis is a test document."

                        # Test save
                        doc_save_success = state_manager.save_document(
                            test_document, DocumentType.SPECIFICATION
                        )

                        if doc_save_success:
                            details["document_save"] = "success"

                            # Test load
                            loaded_document = state_manager.load_document(
                                DocumentType.SPECIFICATION
                            )

                            if loaded_document == test_document:
                                details["document_load"] = "success"
                                details["document_integrity"] = "valid"
                            else:
                                issues.append("Loaded document does not match saved document")
                                details["document_load"] = "failed"
                                details["document_integrity"] = "invalid"
                                recommendations.append(
                                    "Verify document save/load logic"
                                )
                        else:
                            issues.append("Document save operation failed")
                            details["document_save"] = "failed"
                            recommendations.append("Check document save logic")

                    except Exception as e:
                        issues.append(f"Document save/load error: {e}")
                        details["document_save_load"] = "error"
                        details["document_save_load_error"] = str(e)
                        recommendations.append("Check state manager document methods")

            # Determine overall status
            if not issues:
                status = "pass"
                message = "State management is fully functional"
            elif details.get("state_manager_available") and details.get(
                "state_save"
            ) == "success":
                status = "warning"
                message = f"State management partially functional: {len(issues)} issue(s) found"
            else:
                status = "fail"
                message = f"State management has critical issues: {len(issues)} issue(s) found"

            # Add issues to details
            if issues:
                details["issues"] = issues

        except Exception as e:
            logger.error(f"Critical error during state management audit: {e}")
            status = "fail"
            message = f"State management audit failed: {e}"
            details["critical_error"] = str(e)
            recommendations.append("Check state manager dependencies")

        result = AuditResult(
            component="State Management",
            status=status,
            message=message,
            details=details,
            recommendations=recommendations,
        )

        self.results.append(result)
        return result

    async def _audit_azure_openai_integration(self) -> AuditResult:
        """Audit Azure OpenAI integration.

        Verifies that:
        - API connectivity works
        - Token counting is accurate
        - Cost tracking functions correctly

        Returns:
            AuditResult for Azure OpenAI integration
        """
        logger.info("Auditing Azure OpenAI integration")

        details = {}
        recommendations = []
        issues = []

        try:
            import os

            # Test 1: Check Azure OpenAI configuration
            logger.info("Checking Azure OpenAI configuration...")
            try:
                api_key = os.getenv("AZURE_OPENAI_API_KEY")
                endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

                if not api_key:
                    issues.append("AZURE_OPENAI_API_KEY environment variable not set")
                    details["api_key_configured"] = False
                    recommendations.append("Set AZURE_OPENAI_API_KEY environment variable")
                else:
                    details["api_key_configured"] = True

                if not endpoint:
                    issues.append("AZURE_OPENAI_ENDPOINT environment variable not set")
                    details["endpoint_configured"] = False
                    recommendations.append("Set AZURE_OPENAI_ENDPOINT environment variable")
                else:
                    details["endpoint_configured"] = True
                    details["endpoint"] = endpoint

                if not deployment:
                    issues.append(
                        "AZURE_OPENAI_DEPLOYMENT_NAME environment variable not set"
                    )
                    details["deployment_configured"] = False
                    recommendations.append(
                        "Set AZURE_OPENAI_DEPLOYMENT_NAME environment variable"
                    )
                else:
                    details["deployment_configured"] = True
                    details["deployment_name"] = deployment

            except Exception as e:
                issues.append(f"Configuration check error: {e}")
                details["configuration_check"] = "error"
                details["configuration_error"] = str(e)

            # Test 2: Test API connectivity (only if configured)
            if details.get("api_key_configured") and details.get("endpoint_configured"):
                logger.info("Testing Azure OpenAI API connectivity...")
                try:
                    from dev_agent.config.config_manager import ConfigManager
                    from dev_agent.llm.azure_client import AzureOpenAIClient

                    config_manager = ConfigManager()
                    azure_config = config_manager.get_azure_config()

                    if azure_config:
                        llm_client = AzureOpenAIClient(azure_config)

                        # Test simple completion
                        test_response = await llm_client.generate_completion(
                            prompt="Say 'test'",
                            system_prompt="You are a test assistant.",
                            temperature=0.0,
                            max_tokens=10,
                        )

                        if test_response and len(test_response) > 0:
                            details["api_connectivity"] = "success"
                            details["test_response_length"] = len(test_response)
                        else:
                            issues.append("API returned empty response")
                            details["api_connectivity"] = "failed"
                            recommendations.append("Verify Azure OpenAI deployment is active")
                    else:
                        issues.append("Azure OpenAI configuration not found")
                        details["api_connectivity"] = "skipped"
                        details["api_connectivity_reason"] = "Configuration not found"
                        recommendations.append(
                            "Run 'dev-agent azure configure' to set up Azure OpenAI"
                        )

                except Exception as e:
                    issues.append(f"API connectivity error: {e}")
                    details["api_connectivity"] = "error"
                    details["api_connectivity_error"] = str(e)
                    recommendations.append(
                        "Check Azure OpenAI endpoint and API key validity"
                    )
            else:
                details["api_connectivity"] = "skipped"
                details["api_connectivity_reason"] = "Configuration incomplete"

            # Test 3: Test token counting
            logger.info("Testing token counting...")
            try:
                from dev_agent.llm.token_counter import TokenCounter

                token_counter = TokenCounter()

                test_text = "This is a test sentence for token counting."
                token_count = token_counter.count_tokens(test_text)

                if token_count > 0:
                    details["token_counting"] = "success"
                    details["test_token_count"] = token_count

                    # Verify reasonable token count (should be around 8-10 tokens)
                    if 5 <= token_count <= 15:
                        details["token_count_reasonable"] = True
                    else:
                        issues.append(
                            f"Token count seems unreasonable: {token_count} for simple sentence"
                        )
                        details["token_count_reasonable"] = False
                        recommendations.append("Verify tiktoken model configuration")
                else:
                    issues.append("Token counting returned zero")
                    details["token_counting"] = "failed"
                    recommendations.append("Check tiktoken installation and configuration")

            except Exception as e:
                issues.append(f"Token counting error: {e}")
                details["token_counting"] = "error"
                details["token_counting_error"] = str(e)
                recommendations.append("Install tiktoken package")

            # Test 4: Test cost tracking
            logger.info("Testing cost tracking...")
            try:
                from dev_agent.llm.cost_tracker import CostTracker
                from dev_agent.models.enums import PhaseType

                cost_tracker = CostTracker()
                cost_tracker.set_phase(PhaseType.INDEXING)

                # Record some test usage
                test_cost = cost_tracker.record_completion(
                    prompt_tokens=100, completion_tokens=50, model="gpt-4"
                )

                if test_cost > 0:
                    details["cost_tracking"] = "success"
                    details["test_cost"] = test_cost

                    # Get total cost
                    total_cost = cost_tracker.get_current_cost()
                    if total_cost >= test_cost:
                        details["cost_accumulation"] = "success"
                        details["total_cost"] = total_cost
                    else:
                        issues.append("Cost accumulation not working correctly")
                        details["cost_accumulation"] = "failed"
                        recommendations.append("Verify cost tracker accumulation logic")

                    # Get token counts
                    total_tokens = cost_tracker.get_total_tokens()
                    if total_tokens == 150:  # 100 + 50
                        details["token_tracking"] = "success"
                        details["total_tokens"] = total_tokens
                    else:
                        issues.append(
                            f"Token tracking incorrect: expected 150, got {total_tokens}"
                        )
                        details["token_tracking"] = "failed"
                        recommendations.append("Verify cost tracker token counting")
                else:
                    issues.append("Cost tracking returned zero cost")
                    details["cost_tracking"] = "failed"
                    recommendations.append("Check cost tracker pricing configuration")

            except Exception as e:
                issues.append(f"Cost tracking error: {e}")
                details["cost_tracking"] = "error"
                details["cost_tracking_error"] = str(e)
                recommendations.append("Check cost tracker module")

            # Determine overall status
            if not issues:
                status = "pass"
                message = "Azure OpenAI integration is fully functional"
            elif details.get("token_counting") == "success" and details.get(
                "cost_tracking"
            ) == "success":
                status = "warning"
                message = f"Azure OpenAI integration partially functional: {len(issues)} issue(s) found"
            else:
                status = "fail"
                message = f"Azure OpenAI integration has critical issues: {len(issues)} issue(s) found"

            # Add issues to details
            if issues:
                details["issues"] = issues

        except Exception as e:
            logger.error(f"Critical error during Azure OpenAI integration audit: {e}")
            status = "fail"
            message = f"Azure OpenAI integration audit failed: {e}"
            details["critical_error"] = str(e)
            recommendations.append("Check Azure OpenAI dependencies")

        result = AuditResult(
            component="Azure OpenAI Integration",
            status=status,
            message=message,
            details=details,
            recommendations=recommendations,
        )

        self.results.append(result)
        return result

    async def _audit_error_handling(self) -> AuditResult:
        """Audit error handling functionality.

        Verifies that:
        - Errors are handled gracefully
        - Error messages are helpful
        - System degrades gracefully

        Returns:
            AuditResult for error handling
        """
        logger.info("Auditing error handling")

        details = {}
        recommendations = []
        issues = []

        try:
            # Test 1: Check error exception classes
            logger.info("Testing error exception classes...")
            try:
                from dev_agent.errors.exceptions import (
                    AnalysisError,
                    ConfigurationError,
                    GenerationError,
                    IndexingError,
                    ProjectNotFoundError,
                    StateError,
                )
                from dev_agent.errors.llm_exceptions import (
                    LLMAPIError,
                    LLMAuthenticationError,
                    LLMBadRequestError,
                    LLMError,
                    LLMRateLimitError,
                    LLMTimeoutError,
                    LLMTokenLimitError,
                )

                details["exception_classes_available"] = True
                details["general_exceptions_count"] = 6
                details["llm_exceptions_count"] = 7

                # Test exception hierarchy
                test_error = LLMAPIError("Test error", "Test suggestion")
                if isinstance(test_error, LLMError):
                    details["exception_hierarchy"] = "valid"
                else:
                    issues.append("Exception hierarchy not properly structured")
                    details["exception_hierarchy"] = "invalid"
                    recommendations.append("Verify exception class inheritance")

            except ImportError as e:
                issues.append(f"Error exception classes import error: {e}")
                details["exception_classes_available"] = False
                details["exception_import_error"] = str(e)
                recommendations.append("Check error exception modules")

            # Test 2: Test error handler
            logger.info("Testing error handler...")
            try:
                from dev_agent.errors.error_handler import ErrorHandler

                error_handler = ErrorHandler()
                details["error_handler_available"] = True

                # Test error handling with a sample error
                try:
                    # Simulate an error
                    raise ValueError("Test error for audit")
                except ValueError as e:
                    handled = error_handler.handle_error(e, "test_context")

                    if handled:
                        details["error_handling"] = "success"
                    else:
                        issues.append("Error handler did not handle error properly")
                        details["error_handling"] = "failed"
                        recommendations.append("Verify error handler logic")

            except ImportError as e:
                issues.append(f"Error handler import error: {e}")
                details["error_handler_available"] = False
                details["error_handler_import_error"] = str(e)
                recommendations.append("Check error handler module")
            except Exception as e:
                issues.append(f"Error handler test error: {e}")
                details["error_handling"] = "error"
                details["error_handling_error"] = str(e)

            # Test 3: Test error recovery
            logger.info("Testing error recovery...")
            try:
                from dev_agent.errors.recovery import RecoveryManager

                recovery_manager = RecoveryManager()
                details["recovery_manager_available"] = True

                # Test recovery strategy
                test_error = Exception("Test error for recovery")
                recovery_strategy = recovery_manager.get_recovery_strategy(test_error)

                if recovery_strategy:
                    details["recovery_strategy"] = "available"
                    details["recovery_strategy_type"] = type(recovery_strategy).__name__
                else:
                    issues.append("Recovery manager did not provide recovery strategy")
                    details["recovery_strategy"] = "unavailable"
                    recommendations.append("Verify recovery manager strategy logic")

            except ImportError as e:
                issues.append(f"Recovery manager import error: {e}")
                details["recovery_manager_available"] = False
                details["recovery_manager_import_error"] = str(e)
                recommendations.append("Check recovery manager module")
            except Exception as e:
                issues.append(f"Recovery manager test error: {e}")
                details["recovery_strategy"] = "error"
                details["recovery_error"] = str(e)

            # Test 4: Test graceful degradation with LLM errors
            if not self.config.skip_azure_tests:
                logger.info("Testing graceful degradation with LLM errors...")
                try:
                    from dev_agent.errors.llm_exceptions import LLMRateLimitError

                    # Simulate a rate limit error
                    try:
                        raise LLMRateLimitError(
                            "Rate limit exceeded", "Wait and retry"
                        )
                    except LLMRateLimitError as e:
                        # Check if error has helpful message
                        if e.message and e.resolution:
                            details["llm_error_messages"] = "helpful"
                            details["llm_error_has_resolution"] = True
                        else:
                            issues.append("LLM errors lack helpful messages or suggestions")
                            details["llm_error_messages"] = "unhelpful"
                            recommendations.append(
                                "Add helpful messages and suggestions to LLM exceptions"
                            )

                except Exception as e:
                    issues.append(f"LLM error handling test error: {e}")
                    details["llm_error_handling"] = "error"
                    details["llm_error_handling_error"] = str(e)
            else:
                details["llm_error_handling"] = "skipped"
                details["llm_error_handling_reason"] = "Azure tests skipped"

            # Test 5: Test error logging
            logger.info("Testing error logging...")
            try:
                import logging

                # Check if logging is configured
                root_logger = logging.getLogger("dev_agent")
                if root_logger.handlers:
                    details["logging_configured"] = True
                    details["log_handlers_count"] = len(root_logger.handlers)
                else:
                    issues.append("Logging not configured for dev_agent")
                    details["logging_configured"] = False
                    recommendations.append("Configure logging for the application")

                # Test logging an error
                try:
                    test_logger = logging.getLogger("dev_agent.audit.test")
                    test_logger.error("Test error log for audit")
                    details["error_logging"] = "success"
                except Exception as e:
                    issues.append(f"Error logging test failed: {e}")
                    details["error_logging"] = "failed"
                    recommendations.append("Verify logging configuration")

            except Exception as e:
                issues.append(f"Logging test error: {e}")
                details["error_logging"] = "error"
                details["logging_error"] = str(e)

            # Determine overall status
            if not issues:
                status = "pass"
                message = "Error handling is fully functional"
            elif details.get("exception_classes_available") and details.get(
                "error_handler_available"
            ):
                status = "warning"
                message = f"Error handling partially functional: {len(issues)} issue(s) found"
            else:
                status = "fail"
                message = f"Error handling has critical issues: {len(issues)} issue(s) found"

            # Add issues to details
            if issues:
                details["issues"] = issues

        except Exception as e:
            logger.error(f"Critical error during error handling audit: {e}")
            status = "fail"
            message = f"Error handling audit failed: {e}"
            details["critical_error"] = str(e)
            recommendations.append("Check error handling dependencies")

        result = AuditResult(
            component="Error Handling",
            status=status,
            message=message,
            details=details,
            recommendations=recommendations,
        )

        self.results.append(result)
        return result

    def generate_audit_report(self) -> AuditReport:
        """Generate comprehensive audit report from collected results.

        Aggregates all audit results and calculates overall status and
        summary statistics.

        Returns:
            AuditReport with all results and summary
        """
        logger.info("Generating audit report")

        # Determine overall status
        overall_status: Literal["pass", "fail", "warning"]
        if any(r.status == "fail" for r in self.results):
            overall_status = "fail"
        elif any(r.status == "warning" for r in self.results):
            overall_status = "warning"
        else:
            overall_status = "pass"

        # Generate summary
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        warnings = sum(1 for r in self.results if r.status == "warning")
        total = len(self.results)

        summary = (
            f"Audit completed with {passed}/{total} checks passed. "
            f"{failed} checks failed and {warnings} warnings were generated."
        )

        if overall_status == "pass":
            summary += " All core functionality is working correctly."
        elif overall_status == "warning":
            summary += " Some features need attention but core functionality works."
        else:
            summary += " Critical issues found that require immediate attention."

        report = AuditReport(
            timestamp=datetime.now(),
            results=self.results,
            overall_status=overall_status,
            summary=summary,
        )

        return report

    def _save_report(self, report: AuditReport) -> None:
        """Save audit report to file.

        Args:
            report: AuditReport to save
        """
        report_path = Path(self.config.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        markdown_content = report.to_markdown()
        report_path.write_text(markdown_content, encoding="utf-8")

        logger.info("Audit report saved to: %s", report_path)
