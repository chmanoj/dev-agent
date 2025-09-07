#!/usr/bin/env python3
"""
Demo script showing TaskGenerator functionality.

This script demonstrates how to use the TaskGenerator to convert
a design document into an actionable task list.
"""

from dev_agent.generation.task_generator import TaskGenerator
from dev_agent.models.documents import (
    DesignDocument, ComponentSpec, DataModel, InterfaceSpec,
    ErrorHandlingStrategy, TestingStrategy, ArchitectureDescription
)


def create_sample_design():
    """Create a sample design document for demonstration."""
    
    # Define components
    components = [
        ComponentSpec(
            name="UserService",
            description="Handles user management operations including registration, authentication, and profile management",
            interfaces=["IUserService", "IAuthenticationService"],
            dependencies=["UserRepository", "PasswordHasher", "TokenManager"]
        ),
        ComponentSpec(
            name="UserRepository",
            description="Manages user data persistence and retrieval operations",
            interfaces=["IUserRepository"],
            dependencies=["Database", "UserValidator"]
        ),
        ComponentSpec(
            name="APIController",
            description="Handles HTTP API requests and responses for user operations",
            interfaces=["IAPIController"],
            dependencies=["UserService", "RequestValidator", "ResponseFormatter"]
        )
    ]
    
    # Define data models
    data_models = [
        DataModel(
            name="User",
            fields={
                "id": "int",
                "username": "str", 
                "email": "str",
                "password_hash": "str",
                "created_at": "datetime",
                "updated_at": "datetime",
                "is_active": "bool"
            },
            relationships=["One-to-many with Session", "One-to-many with ApiKey"]
        ),
        DataModel(
            name="Session",
            fields={
                "id": "int",
                "user_id": "int",
                "token": "str",
                "expires_at": "datetime",
                "created_at": "datetime"
            },
            relationships=["Many-to-one with User"]
        )
    ]
    
    # Define interfaces
    interfaces = [
        InterfaceSpec(
            name="IUserService",
            methods=[
                "create_user(user_data) -> User",
                "authenticate_user(username, password) -> AuthResult",
                "get_user_by_id(user_id) -> User",
                "update_user(user_id, data) -> User",
                "deactivate_user(user_id) -> bool"
            ],
            description="Interface for user management operations"
        ),
        InterfaceSpec(
            name="IUserRepository",
            methods=[
                "save_user(user) -> User",
                "find_user_by_id(user_id) -> User",
                "find_user_by_username(username) -> User",
                "update_user(user_id, data) -> User",
                "delete_user(user_id) -> bool"
            ],
            description="Interface for user data persistence operations"
        )
    ]
    
    # Define error handling strategy
    error_handling = ErrorHandlingStrategy(
        error_categories=[
            "Authentication Errors",
            "Validation Errors", 
            "Database Errors",
            "Network Errors",
            "Business Logic Errors"
        ],
        recovery_mechanisms=[
            "Graceful degradation for non-critical failures",
            "Retry mechanisms with exponential backoff",
            "User-friendly error messages with actionable guidance",
            "Comprehensive logging and monitoring",
            "Circuit breaker pattern for external dependencies"
        ],
        logging_strategy="Structured logging with correlation IDs and appropriate levels (DEBUG, INFO, WARN, ERROR)"
    )
    
    # Define testing strategy
    testing_strategy = TestingStrategy(
        unit_testing="Comprehensive unit testing with pytest, mocking external dependencies, and focus on edge cases",
        integration_testing="Integration tests for database operations, API endpoints, and service interactions",
        performance_testing="Load testing for authentication endpoints and database query optimization",
        test_coverage_target=0.90
    )
    
    # Define architecture
    architecture = ArchitectureDescription(
        overview="Layered architecture with clear separation between API, service, and data layers",
        patterns=["Repository Pattern", "Service Layer Pattern", "Dependency Injection"],
        components=["APIController", "UserService", "UserRepository"]
    )
    
    return DesignDocument(
        overview="User management system with authentication, registration, and profile management capabilities",
        architecture=architecture,
        components=components,
        data_models=data_models,
        interfaces=interfaces,
        error_handling=error_handling,
        testing_strategy=testing_strategy,
        version="1.0",
        approved=True
    )


def main():
    """Main demo function."""
    print("=== TaskGenerator Demo ===\n")
    
    # Create sample design
    print("1. Creating sample design document...")
    design = create_sample_design()
    print(f"   - Created design with {len(design.components)} components")
    print(f"   - {len(design.data_models)} data models")
    print(f"   - {len(design.interfaces)} interfaces")
    print()
    
    # Initialize TaskGenerator
    print("2. Initializing TaskGenerator...")
    generator = TaskGenerator()
    print("   - TaskGenerator initialized successfully")
    print()
    
    # Generate task list
    print("3. Generating task list from design...")
    task_list = generator.generate_from_design(design)
    print(f"   - Generated {len(task_list.tasks)} tasks")
    print(f"   - {len(task_list.dependencies)} dependency relationships")
    print(f"   - Total estimated effort: {sum(task_list.estimated_effort.values())} hours")
    print()
    
    # Display task categories
    print("4. Task breakdown by category:")
    categories = {}
    for task in task_list.tasks:
        category = generator._determine_task_category(task)
        if category not in categories:
            categories[category] = []
        categories[category].append(task)
    
    for category, tasks in categories.items():
        print(f"   - {category}: {len(tasks)} tasks")
    print()
    
    # Format and display task list
    print("5. Formatted task list (first 1000 characters):")
    formatted = generator.format_task_list(task_list)
    print("-" * 60)
    print(formatted[:1000])
    if len(formatted) > 1000:
        print(f"\n... (truncated, full length: {len(formatted)} characters)")
    print("-" * 60)
    print()
    
    # Demonstrate refinement
    print("6. Demonstrating task refinement...")
    feedback = "Add more security-focused tasks and increase testing coverage"
    refined_task_list = generator.refine_tasks(task_list, feedback)
    print(f"   - Original tasks: {len(task_list.tasks)}")
    print(f"   - Refined tasks: {len(refined_task_list.tasks)}")
    print(f"   - Version updated: {task_list.version} -> {refined_task_list.version}")
    print()
    
    # Show some example tasks
    print("7. Example tasks:")
    for i, task in enumerate(task_list.tasks[:3]):
        print(f"   Task {task.id}: {task.title}")
        print(f"   Description: {task.description}")
        print(f"   Requirements: {', '.join(task.requirements_refs)}")
        print(f"   Estimated effort: {task_list.estimated_effort[task.id]} hours")
        if i < 2:
            print()
    
    print("\n=== Demo completed successfully! ===")


if __name__ == "__main__":
    main()