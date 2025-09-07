"""Tests for task generator."""

from unittest.mock import Mock

import pytest

from dev_agent.generation.task_generator import TaskGenerator
from dev_agent.interfaces.cli_interface import ICLIInterface
from dev_agent.models.documents import (
    ArchitectureDescription,
    ComponentSpec,
    DataModel,
    DesignDocument,
    ErrorHandlingStrategy,
    InterfaceSpec,
    Task,
    TaskList,
    TestingStrategy,
)
from dev_agent.models.enums import TaskStatus


class TestTaskGenerator:
    """Test cases for TaskGenerator."""

    @pytest.fixture
    def mock_cli(self):
        """Create a mock CLI interface."""
        cli = Mock(spec=ICLIInterface)
        cli.display_message = Mock()
        cli.get_user_input = Mock()
        cli.request_approval = Mock(return_value=True)
        return cli

    @pytest.fixture
    def generator(self, mock_cli):
        """Create a task generator with mock CLI."""
        return TaskGenerator(cli_interface=mock_cli)

    @pytest.fixture
    def generator_no_cli(self):
        """Create a task generator without CLI."""
        return TaskGenerator()

    @pytest.fixture
    def sample_design(self):
        """Create sample design document."""
        components = [
            ComponentSpec(
                name="UserService",
                description="Handles user management operations",
                interfaces=["IUserService"],
                dependencies=["UserRepository", "AuthService"]
            ),
            ComponentSpec(
                name="DataRepository",
                description="Manages data persistence operations",
                interfaces=["IDataRepository"],
                dependencies=["Database"]
            )
        ]

        data_models = [
            DataModel(
                name="User",
                fields={"id": "int", "username": "str", "email": "str", "created_at": "datetime"},
                relationships=["One-to-many with Session"]
            ),
            DataModel(
                name="Session",
                fields={"id": "int", "user_id": "int", "token": "str", "expires_at": "datetime"},
                relationships=["Many-to-one with User"]
            )
        ]

        interfaces = [
            InterfaceSpec(
                name="IUserService",
                methods=["create_user(data)", "authenticate(credentials)", "get_user(id)"],
                description="Interface for user management operations"
            ),
            InterfaceSpec(
                name="IDataRepository",
                methods=["save(entity)", "find(id)", "delete(id)", "list()"],
                description="Interface for data persistence operations"
            )
        ]

        error_handling = ErrorHandlingStrategy(
            error_categories=["Validation Errors", "Authentication Errors", "Database Errors"],
            recovery_mechanisms=["Graceful degradation", "Retry mechanisms", "User notifications"],
            logging_strategy="Structured logging with appropriate levels"
        )

        testing_strategy = TestingStrategy(
            unit_testing="Comprehensive unit testing with pytest",
            integration_testing="Integration tests for component interactions",
            performance_testing="Performance testing for critical paths",
            test_coverage_target=0.85
        )

        architecture = ArchitectureDescription(
            overview="Service-oriented architecture with clear separation",
            patterns=["Repository Pattern", "Service Layer"],
            components=["UserService", "DataRepository"]
        )

        return DesignDocument(
            overview="Test application design",
            architecture=architecture,
            components=components,
            data_models=data_models,
            interfaces=interfaces,
            error_handling=error_handling,
            testing_strategy=testing_strategy,
            version="1.0",
            approved=True
        )

    def test_generate_from_design(self, generator, sample_design):
        """Test generating task list from design document."""
        task_list = generator.generate_from_design(sample_design)

        assert isinstance(task_list, TaskList)
        assert task_list.version == "1.0"
        assert not task_list.approved
        assert len(task_list.tasks) > 0
        assert len(task_list.dependencies) >= 0
        assert len(task_list.estimated_effort) == len(task_list.tasks)

        # Check that all tasks have proper structure
        for task in task_list.tasks:
            assert task.id is not None
            assert task.title is not None
            assert task.status == TaskStatus.NOT_STARTED
            assert isinstance(task.requirements_refs, list)

    def test_component_task_generation(self, generator, sample_design):
        """Test generation of component-related tasks."""
        task_list = generator.generate_from_design(sample_design)

        # Should have tasks for each component
        component_tasks = [t for t in task_list.tasks if "component" in t.title.lower()]
        assert len(component_tasks) >= 2  # UserService and DataRepository

        # Check UserService task
        user_service_task = next((t for t in component_tasks if "UserService" in t.title), None)
        assert user_service_task is not None
        assert "UserService" in user_service_task.title
        assert "user management operations" in user_service_task.description.lower()
        assert len(user_service_task.requirements_refs) > 0

    def test_data_model_task_generation(self, generator, sample_design):
        """Test generation of data model tasks."""
        task_list = generator.generate_from_design(sample_design)

        # Should have tasks for each data model
        model_tasks = [t for t in task_list.tasks if "data model" in t.title.lower()]
        assert len(model_tasks) >= 2  # User and Session models

        # Check User model task
        user_model_task = next((t for t in model_tasks if "User" in t.title), None)
        assert user_model_task is not None
        assert "User" in user_model_task.title
        assert "fields and validation" in user_model_task.description.lower()

        # Should also have validation tasks
        validation_tasks = [t for t in task_list.tasks if "validation" in t.title.lower()]
        assert len(validation_tasks) >= 2  # One for each model

    def test_interface_task_generation(self, generator, sample_design):
        """Test generation of interface tasks."""
        task_list = generator.generate_from_design(sample_design)

        # Should have tasks for each interface
        interface_tasks = [t for t in task_list.tasks if "interface" in t.title.lower()]
        assert len(interface_tasks) >= 2  # IUserService and IDataRepository

        # Check IUserService task
        user_interface_task = next((t for t in interface_tasks if "IUserService" in t.title), None)
        assert user_interface_task is not None
        assert "IUserService" in user_interface_task.title
        assert "user management operations" in user_interface_task.description.lower()

    def test_testing_task_generation(self, generator, sample_design):
        """Test generation of testing tasks."""
        task_list = generator.generate_from_design(sample_design)

        # Should have unit and integration testing tasks
        testing_tasks = [t for t in task_list.tasks if "test" in t.title.lower()]
        assert len(testing_tasks) >= 2  # Unit and integration tests

        # Check unit testing task
        unit_test_task = next((t for t in testing_tasks if "unit" in t.title.lower()), None)
        assert unit_test_task is not None
        assert "unit test" in unit_test_task.title.lower()
        assert "85%" in unit_test_task.implementation_notes or "0.85" in str(unit_test_task.implementation_notes)

        # Check integration testing task
        integration_test_task = next((t for t in testing_tasks if "integration" in t.title.lower()), None)
        assert integration_test_task is not None
        assert "integration test" in integration_test_task.title.lower()

    def test_error_handling_task_generation(self, generator, sample_design):
        """Test generation of error handling tasks."""
        task_list = generator.generate_from_design(sample_design)

        # Should have error handling task
        error_tasks = [t for t in task_list.tasks if "error" in t.title.lower()]
        assert len(error_tasks) >= 1

        error_task = error_tasks[0]
        assert "error handling" in error_task.title.lower()
        assert "logging" in error_task.description.lower()
        assert len(error_task.context_requirements) > 0

    def test_integration_task_generation(self, generator, sample_design):
        """Test generation of integration tasks."""
        task_list = generator.generate_from_design(sample_design)

        # Should have integration task
        integration_tasks = [t for t in task_list.tasks if "integrate" in t.title.lower()]
        assert len(integration_tasks) >= 1

        integration_task = integration_tasks[0]
        assert "integrate" in integration_task.title.lower()
        assert "wire together" in integration_task.description.lower()
        assert "All functional requirements" in integration_task.requirements_refs

    def test_task_dependencies(self, generator, sample_design):
        """Test task dependency generation."""
        task_list = generator.generate_from_design(sample_design)

        # Should have some dependencies
        assert len(task_list.dependencies) > 0

        # Integration tasks should depend on other tasks
        integration_tasks = [t for t in task_list.tasks if "integrate" in t.title.lower()]
        if integration_tasks:
            integration_task_id = integration_tasks[0].id
            if integration_task_id in task_list.dependencies:
                deps = task_list.dependencies[integration_task_id]
                assert len(deps) > 0  # Should depend on other tasks

    def test_effort_estimation(self, generator, sample_design):
        """Test effort estimation for tasks."""
        task_list = generator.generate_from_design(sample_design)

        # All tasks should have effort estimates
        assert len(task_list.estimated_effort) == len(task_list.tasks)

        # All estimates should be positive integers
        for task_id, effort in task_list.estimated_effort.items():
            assert isinstance(effort, int)
            assert effort > 0
            assert effort <= 20  # Reasonable upper bound

        # Different task types should have different effort estimates
        efforts = list(task_list.estimated_effort.values())
        assert len(set(efforts)) > 1  # Should have variety in estimates

    def test_format_task_list(self, generator, sample_design):
        """Test formatting task list as markdown."""
        task_list = generator.generate_from_design(sample_design)
        formatted = generator.format_task_list(task_list)

        assert isinstance(formatted, str)
        assert "# Implementation Plan" in formatted
        assert "## Task Metadata" in formatted
        assert f"**Total Tasks:** {len(task_list.tasks)}" in formatted
        assert "**Version:** 1.0" in formatted
        assert "**Status:** Draft" in formatted

        # Should have task checkboxes
        assert "- [ ]" in formatted  # Unchecked tasks
        assert "_Requirements:" in formatted  # Requirement references

    def test_format_task_list_with_grouping(self, generator, sample_design):
        """Test formatting task list with proper grouping."""
        task_list = generator.generate_from_design(sample_design)
        formatted = generator.format_task_list(task_list)

        # Should group related tasks
        lines = formatted.split("\n")
        task_lines = [line for line in lines if line.startswith("- [")]

        # Should have multiple task entries
        assert len(task_lines) > 0

        # Should have requirement references
        req_lines = [line for line in lines if "_Requirements:" in line]
        assert len(req_lines) > 0

    def test_refine_tasks(self, generator, sample_design):
        """Test refining task list based on feedback."""
        original_tasks = generator.generate_from_design(sample_design)
        feedback = "Add more testing tasks and adjust effort estimates"

        refined_tasks = generator.refine_tasks(original_tasks, feedback)

        assert refined_tasks.version != original_tasks.version
        assert not refined_tasks.approved
        # Should have added tasks based on feedback
        assert len(refined_tasks.tasks) >= len(original_tasks.tasks)

    def test_request_user_approval_with_cli(self, generator, mock_cli, sample_design):
        """Test requesting user approval with CLI interface."""
        task_list = generator.generate_from_design(sample_design)
        mock_cli.request_approval.return_value = True

        approved = generator.request_user_approval(task_list)

        assert approved is True
        assert task_list.approved is True
        mock_cli.request_approval.assert_called_once()

    def test_request_user_approval_without_cli(self, generator_no_cli, sample_design):
        """Test requesting user approval without CLI interface."""
        task_list = generator_no_cli.generate_from_design(sample_design)

        approved = generator_no_cli.request_user_approval(task_list)

        assert approved is True  # Auto-approve when no CLI
        assert task_list.approved is True

    def test_request_user_approval_rejected(self, generator, mock_cli, sample_design):
        """Test user rejecting approval."""
        task_list = generator.generate_from_design(sample_design)
        mock_cli.request_approval.return_value = False

        approved = generator.request_user_approval(task_list)

        assert approved is False
        assert task_list.approved is False

    def test_task_categorization(self, generator):
        """Test task categorization logic."""
        # Test different task types
        data_task = Task(id="1", title="Implement User data model", description="", requirements_refs=[], subtasks=[], status=TaskStatus.NOT_STARTED)
        component_task = Task(id="2", title="Implement UserService component", description="", requirements_refs=[], subtasks=[], status=TaskStatus.NOT_STARTED)
        test_task = Task(id="3", title="Implement unit tests", description="", requirements_refs=[], subtasks=[], status=TaskStatus.NOT_STARTED)
        interface_task = Task(id="4", title="Define IUserService interface", description="", requirements_refs=[], subtasks=[], status=TaskStatus.NOT_STARTED)

        assert generator._determine_task_category(data_task) == "Data Models"
        assert generator._determine_task_category(component_task) == "Components"
        assert generator._determine_task_category(test_task) == "Testing"
        assert generator._determine_task_category(interface_task) == "Interfaces"

    def test_status_markers(self, generator):
        """Test status marker generation."""
        assert generator._get_status_marker(TaskStatus.NOT_STARTED) == " "
        assert generator._get_status_marker(TaskStatus.IN_PROGRESS) == "-"
        assert generator._get_status_marker(TaskStatus.COMPLETED) == "x"

    def test_requirement_extraction_from_component(self, generator, sample_design):
        """Test extracting requirements from component descriptions."""
        user_component = sample_design.components[0]  # UserService
        req_refs = generator._extract_requirements_from_component(user_component, sample_design)

        assert len(req_refs) > 0
        assert any("user" in ref.lower() or "auth" in ref.lower() for ref in req_refs)

    def test_requirement_extraction_from_model(self, generator, sample_design):
        """Test extracting requirements from data models."""
        user_model = sample_design.data_models[0]  # User
        req_refs = generator._extract_requirements_from_model(user_model, sample_design)

        assert len(req_refs) > 0
        assert any("user" in ref.lower() for ref in req_refs)

    def test_version_increment(self, generator):
        """Test version increment functionality."""
        assert generator._increment_version("1.0") == "1.1"
        assert generator._increment_version("2.5") == "2.6"
        assert generator._increment_version("invalid") == "1.1"
        assert generator._increment_version("1") == "1.1"

    def test_parse_feedback(self, generator):
        """Test parsing user feedback."""
        feedback = "Add more tasks for security and remove unnecessary ones"
        refinements = generator._parse_feedback(feedback)

        assert "add_tasks" in refinements
        assert "remove_tasks" in refinements
        assert len(refinements["add_tasks"]) > 0 or len(refinements["remove_tasks"]) > 0

    def test_apply_refinements(self, generator, sample_design):
        """Test applying refinements to task list."""
        task_list = generator.generate_from_design(sample_design)
        original_task_count = len(task_list.tasks)

        refinements = {
            "add_tasks": ["New security task"],
            "modify_tasks": [],
            "remove_tasks": ["Remove something"],
            "change_order": False,
            "adjust_effort": {"general": "increase effort"},
            "add_dependencies": {}
        }

        refined_task_list = generator._apply_refinements(task_list, refinements)

        # Should have modified the task list
        assert refined_task_list != task_list
        assert not refined_task_list.approved

        # Should have added and removed tasks (net effect depends on implementation)
        # At minimum, should be different from original
        assert len(refined_task_list.tasks) != original_task_count or \
               refined_task_list.estimated_effort != task_list.estimated_effort


class TestTaskGeneratorIntegration:
    """Integration tests for task generator."""

    @pytest.fixture
    def generator(self):
        """Create generator for integration tests."""
        return TaskGenerator()

    @pytest.fixture
    def comprehensive_design(self):
        """Create comprehensive design document for integration testing."""
        components = [
            ComponentSpec(
                name="AuthenticationService",
                description="Handles user authentication and authorization",
                interfaces=["IAuthService", "ITokenManager"],
                dependencies=["UserRepository", "TokenStorage", "PasswordHasher"]
            ),
            ComponentSpec(
                name="UserRepository",
                description="Manages user data persistence and retrieval",
                interfaces=["IUserRepository"],
                dependencies=["Database", "UserValidator"]
            ),
            ComponentSpec(
                name="APIController",
                description="Handles HTTP API requests and responses",
                interfaces=["IAPIController"],
                dependencies=["AuthenticationService", "UserRepository", "ResponseFormatter"]
            )
        ]

        data_models = [
            DataModel(
                name="User",
                fields={
                    "id": "int", "username": "str", "email": "str",
                    "password_hash": "str", "created_at": "datetime",
                    "updated_at": "datetime", "is_active": "bool"
                },
                relationships=["One-to-many with Session", "One-to-many with ApiKey"]
            ),
            DataModel(
                name="Session",
                fields={
                    "id": "int", "user_id": "int", "token": "str",
                    "expires_at": "datetime", "created_at": "datetime"
                },
                relationships=["Many-to-one with User"]
            ),
            DataModel(
                name="ApiKey",
                fields={
                    "id": "int", "user_id": "int", "key": "str",
                    "name": "str", "created_at": "datetime", "is_active": "bool"
                },
                relationships=["Many-to-one with User"]
            )
        ]

        interfaces = [
            InterfaceSpec(
                name="IAuthService",
                methods=[
                    "authenticate(username, password) -> AuthResult",
                    "authorize(user, resource) -> bool",
                    "create_session(user) -> Session",
                    "validate_session(token) -> User"
                ],
                description="Interface for authentication and authorization operations"
            ),
            InterfaceSpec(
                name="IUserRepository",
                methods=[
                    "create_user(user_data) -> User",
                    "find_user_by_id(id) -> User",
                    "find_user_by_username(username) -> User",
                    "update_user(id, data) -> User",
                    "delete_user(id) -> bool"
                ],
                description="Interface for user data persistence operations"
            ),
            InterfaceSpec(
                name="IAPIController",
                methods=[
                    "handle_login(request) -> Response",
                    "handle_logout(request) -> Response",
                    "handle_user_creation(request) -> Response",
                    "handle_user_update(request) -> Response"
                ],
                description="Interface for HTTP API request handling"
            )
        ]

        error_handling = ErrorHandlingStrategy(
            error_categories=[
                "Authentication Errors", "Authorization Errors", "Validation Errors",
                "Database Errors", "Network Errors", "Business Logic Errors"
            ],
            recovery_mechanisms=[
                "Graceful degradation for non-critical failures",
                "Retry mechanisms with exponential backoff",
                "Circuit breaker pattern for external dependencies",
                "User-friendly error messages with actionable guidance",
                "Comprehensive logging and monitoring"
            ],
            logging_strategy="Structured logging with correlation IDs, appropriate levels (DEBUG, INFO, WARN, ERROR), and centralized log aggregation"
        )

        testing_strategy = TestingStrategy(
            unit_testing="Comprehensive unit testing with pytest, mocking external dependencies, and focus on edge cases",
            integration_testing="Integration tests for database operations, API endpoints, and service interactions",
            performance_testing="Load testing for authentication endpoints, database query optimization, and response time monitoring",
            test_coverage_target=0.90
        )

        architecture = ArchitectureDescription(
            overview="Layered architecture with clear separation between API, service, and data layers",
            patterns=["Repository Pattern", "Service Layer Pattern", "Dependency Injection", "MVC Pattern"],
            components=["APIController", "AuthenticationService", "UserRepository"]
        )

        return DesignDocument(
            overview="Comprehensive user authentication and management system with RESTful API",
            architecture=architecture,
            components=components,
            data_models=data_models,
            interfaces=interfaces,
            error_handling=error_handling,
            testing_strategy=testing_strategy,
            version="1.0",
            approved=True
        )

    def test_comprehensive_task_generation(self, generator, comprehensive_design):
        """Test comprehensive task generation from complex design."""
        task_list = generator.generate_from_design(comprehensive_design)

        # Should generate comprehensive task list
        assert len(task_list.tasks) >= 15  # Should have many tasks for complex design
        assert len(task_list.dependencies) > 0
        assert len(task_list.estimated_effort) == len(task_list.tasks)

        # Should cover all major areas
        task_titles = [task.title.lower() for task in task_list.tasks]

        # Should have component tasks
        assert any("authenticationservice" in title for title in task_titles)
        assert any("userrepository" in title for title in task_titles)
        assert any("apicontroller" in title for title in task_titles)

        # Should have data model tasks
        assert any("user" in title and "data model" in title for title in task_titles)
        assert any("session" in title and "data model" in title for title in task_titles)
        assert any("apikey" in title and "data model" in title for title in task_titles)

        # Should have interface tasks
        assert any("iauthservice" in title for title in task_titles)
        assert any("iuserrepository" in title for title in task_titles)
        assert any("iapicontroller" in title for title in task_titles)

        # Should have testing tasks
        assert any("unit test" in title for title in task_titles)
        assert any("integration test" in title for title in task_titles)
        assert any("performance test" in title for title in task_titles)

        # Should have error handling and integration tasks
        assert any("error handling" in title for title in task_titles)
        assert any("integrate" in title for title in task_titles)

    def test_task_requirement_coverage(self, generator, comprehensive_design):
        """Test that tasks properly reference requirements."""
        task_list = generator.generate_from_design(comprehensive_design)

        # All tasks should have requirement references
        for task in task_list.tasks:
            assert len(task.requirements_refs) > 0
            assert all(isinstance(ref, str) for ref in task.requirements_refs)

        # Should have variety in requirement references
        all_req_refs = set()
        for task in task_list.tasks:
            all_req_refs.update(task.requirements_refs)

        assert len(all_req_refs) > 3  # Should reference multiple requirement areas

    def test_task_dependency_logic(self, generator, comprehensive_design):
        """Test logical task dependencies."""
        task_list = generator.generate_from_design(comprehensive_design)

        # Find specific task types
        data_model_tasks = [t for t in task_list.tasks if "data model" in t.title.lower()]
        component_tasks = [t for t in task_list.tasks if "component" in t.title.lower()]
        test_tasks = [t for t in task_list.tasks if "test" in t.title.lower()]
        integration_tasks = [t for t in task_list.tasks if "integrate" in t.title.lower()]

        # Component tasks should depend on data model tasks
        for component_task in component_tasks:
            if component_task.id in task_list.dependencies:
                deps = task_list.dependencies[component_task.id]
                # Should have some dependencies on data models
                data_model_ids = [t.id for t in data_model_tasks]
                assert any(dep in data_model_ids for dep in deps)

        # Integration tasks should depend on most other tasks
        for integration_task in integration_tasks:
            if integration_task.id in task_list.dependencies:
                deps = task_list.dependencies[integration_task.id]
                assert len(deps) > 3  # Should depend on many tasks

    def test_effort_estimation_logic(self, generator, comprehensive_design):
        """Test effort estimation logic."""
        task_list = generator.generate_from_design(comprehensive_design)

        # Different task types should have different effort estimates
        data_model_efforts = []
        component_efforts = []
        test_efforts = []

        for task in task_list.tasks:
            effort = task_list.estimated_effort[task.id]
            if "data model" in task.title.lower():
                data_model_efforts.append(effort)
            elif "component" in task.title.lower():
                component_efforts.append(effort)
            elif "test" in task.title.lower():
                test_efforts.append(effort)

        # Components should generally take more effort than data models
        if data_model_efforts and component_efforts:
            avg_data_effort = sum(data_model_efforts) / len(data_model_efforts)
            avg_component_effort = sum(component_efforts) / len(component_efforts)
            assert avg_component_effort >= avg_data_effort

        # All efforts should be reasonable
        all_efforts = list(task_list.estimated_effort.values())
        assert min(all_efforts) >= 1  # At least 1 hour
        assert max(all_efforts) <= 20  # At most 20 hours per task

    def test_formatted_output_quality(self, generator, comprehensive_design):
        """Test quality of formatted task list output."""
        task_list = generator.generate_from_design(comprehensive_design)
        formatted = generator.format_task_list(task_list)

        # Should be well-structured markdown
        lines = formatted.split("\n")

        # Should have proper header
        assert lines[0] == "# Implementation Plan"

        # Should have task entries with checkboxes
        task_lines = [line for line in lines if line.startswith("- [")]
        assert len(task_lines) > 10  # Should have many tasks

        # Should have requirement references
        req_lines = [line for line in lines if "_Requirements:" in line]
        assert len(req_lines) > 5  # Should have many requirement references

        # Should have metadata section
        assert "## Task Metadata" in formatted
        assert f"**Total Tasks:** {len(task_list.tasks)}" in formatted
        assert "**Estimated Total Effort:**" in formatted

        # Should be properly formatted (no empty task lines)
        for line in task_lines:
            assert len(line.strip()) > 10  # Should have substantial content
            assert ". " in line  # Should have task ID and title

    def test_full_workflow_with_refinement(self, generator, comprehensive_design):
        """Test full workflow including refinement."""
        # Generate initial task list
        initial_tasks = generator.generate_from_design(comprehensive_design)

        # Verify initial generation
        assert len(initial_tasks.tasks) > 10
        assert initial_tasks.version == "1.0"
        assert not initial_tasks.approved

        # Format and verify
        formatted = generator.format_task_list(initial_tasks)
        assert len(formatted) > 2000  # Should be comprehensive

        # Refine with feedback
        feedback = "Add more security-focused tasks and increase testing coverage"
        refined_tasks = generator.refine_tasks(initial_tasks, feedback)

        # Verify refinement
        assert refined_tasks.version == "1.1"
        assert not refined_tasks.approved
        assert len(refined_tasks.tasks) >= len(initial_tasks.tasks)

        # Format refined version
        refined_formatted = generator.format_task_list(refined_tasks)
        assert len(refined_formatted) >= len(formatted)

        # Approve final version
        approved = generator.request_user_approval(refined_tasks)
        assert approved is True
        assert refined_tasks.approved is True

    def test_edge_cases_and_robustness(self, generator):
        """Test edge cases and robustness."""
        # Test with minimal design
        minimal_design = DesignDocument(
            overview="Minimal design",
            architecture=ArchitectureDescription(overview="Simple", patterns=[], components=[]),
            components=[],
            data_models=[],
            interfaces=[],
            error_handling=ErrorHandlingStrategy(
                error_categories=["Basic Errors"],
                recovery_mechanisms=["Basic Recovery"],
                logging_strategy="Basic Logging"
            ),
            testing_strategy=TestingStrategy(
                unit_testing="Basic unit testing",
                integration_testing="Basic integration testing",
                performance_testing="Basic performance testing",
                test_coverage_target=0.7
            ),
            version="1.0",
            approved=True
        )

        task_list = generator.generate_from_design(minimal_design)

        # Should still generate some tasks
        assert len(task_list.tasks) > 0
        assert len(task_list.estimated_effort) == len(task_list.tasks)

        # Should be able to format even minimal task list
        formatted = generator.format_task_list(task_list)
        assert "# Implementation Plan" in formatted
        assert "## Task Metadata" in formatted

        # Should handle refinement
        refined = generator.refine_tasks(task_list, "Add more tasks")
        assert refined.version != task_list.version
