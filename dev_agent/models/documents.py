"""Document data models for specifications, designs, and tasks."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .enums import Priority, SpecificationSource, TaskStatus


@dataclass
class CodeAnalysisRef:
    """Reference to code analysis that informed a requirement."""

    file_paths: list[str]
    functions: list[str]
    confidence_score: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_paths": self.file_paths,
            "functions": self.functions,
            "confidence_score": self.confidence_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeAnalysisRef":
        """Create from dictionary."""
        return cls(
            file_paths=data["file_paths"],
            functions=data["functions"],
            confidence_score=data["confidence_score"],
        )


@dataclass
class Requirement:
    """A functional requirement with acceptance criteria."""

    id: str
    user_story: str
    acceptance_criteria: list[str]
    priority: Priority
    source_analysis: CodeAnalysisRef | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "user_story": self.user_story,
            "acceptance_criteria": self.acceptance_criteria,
            "priority": self.priority.value,
            "source_analysis": self.source_analysis.to_dict() if self.source_analysis else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Requirement":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            user_story=data["user_story"],
            acceptance_criteria=data["acceptance_criteria"],
            priority=Priority(data["priority"]),
            source_analysis=CodeAnalysisRef.from_dict(data["source_analysis"]) if data.get("source_analysis") else None,
        )


@dataclass
class SpecificationDocument:
    """Complete specification document."""

    introduction: str
    key_features: list[str]
    functional_requirements: list[Requirement]
    source: SpecificationSource
    version: str
    approved: bool
    approval_timestamp: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "introduction": self.introduction,
            "key_features": self.key_features,
            "functional_requirements": [req.to_dict() for req in self.functional_requirements],
            "source": self.source.value,
            "version": self.version,
            "approved": self.approved,
            "approval_timestamp": self.approval_timestamp.isoformat() if self.approval_timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpecificationDocument":
        """Create from dictionary."""
        return cls(
            introduction=data["introduction"],
            key_features=data["key_features"],
            functional_requirements=[Requirement.from_dict(req) for req in data["functional_requirements"]],
            source=SpecificationSource(data["source"]),
            version=data["version"],
            approved=data["approved"],
            approval_timestamp=datetime.fromisoformat(data["approval_timestamp"]) if data.get("approval_timestamp") else None,
        )


@dataclass
class ComponentSpec:
    """Specification for a system component."""

    name: str
    description: str
    interfaces: list[str]
    dependencies: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "interfaces": self.interfaces,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentSpec":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            interfaces=data["interfaces"],
            dependencies=data["dependencies"],
        )


@dataclass
class DataModel:
    """Data model specification."""

    name: str
    fields: dict[str, str]
    relationships: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "fields": self.fields,
            "relationships": self.relationships,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataModel":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            fields=data["fields"],
            relationships=data["relationships"],
        )


@dataclass
class InterfaceSpec:
    """Interface specification."""

    name: str
    methods: list[str]
    description: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "methods": self.methods,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InterfaceSpec":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            methods=data["methods"],
            description=data["description"],
        )


@dataclass
class ErrorHandlingStrategy:
    """Error handling strategy specification."""

    error_categories: list[str]
    recovery_mechanisms: list[str]
    logging_strategy: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_categories": self.error_categories,
            "recovery_mechanisms": self.recovery_mechanisms,
            "logging_strategy": self.logging_strategy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ErrorHandlingStrategy":
        """Create from dictionary."""
        return cls(
            error_categories=data["error_categories"],
            recovery_mechanisms=data["recovery_mechanisms"],
            logging_strategy=data["logging_strategy"],
        )


@dataclass
class TestingStrategy:
    """Testing strategy specification."""

    unit_testing: str
    integration_testing: str
    performance_testing: str
    test_coverage_target: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "unit_testing": self.unit_testing,
            "integration_testing": self.integration_testing,
            "performance_testing": self.performance_testing,
            "test_coverage_target": self.test_coverage_target,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestingStrategy":
        """Create from dictionary."""
        return cls(
            unit_testing=data["unit_testing"],
            integration_testing=data["integration_testing"],
            performance_testing=data["performance_testing"],
            test_coverage_target=data["test_coverage_target"],
        )


@dataclass
class ArchitectureDescription:
    """Architecture description."""

    overview: str
    patterns: list[str]
    components: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overview": self.overview,
            "patterns": self.patterns,
            "components": self.components,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArchitectureDescription":
        """Create from dictionary."""
        return cls(
            overview=data["overview"],
            patterns=data["patterns"],
            components=data["components"],
        )


@dataclass
class DesignDocument:
    """Complete design document."""

    overview: str
    architecture: ArchitectureDescription
    components: list[ComponentSpec]
    data_models: list[DataModel]
    interfaces: list[InterfaceSpec]
    error_handling: ErrorHandlingStrategy
    testing_strategy: TestingStrategy
    version: str
    approved: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overview": self.overview,
            "architecture": self.architecture.to_dict(),
            "components": [c.to_dict() for c in self.components],
            "data_models": [d.to_dict() for d in self.data_models],
            "interfaces": [i.to_dict() for i in self.interfaces],
            "error_handling": self.error_handling.to_dict(),
            "testing_strategy": self.testing_strategy.to_dict(),
            "version": self.version,
            "approved": self.approved,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DesignDocument":
        """Create from dictionary."""
        return cls(
            overview=data["overview"],
            architecture=ArchitectureDescription.from_dict(data["architecture"]),
            components=[ComponentSpec.from_dict(c) for c in data["components"]],
            data_models=[DataModel.from_dict(d) for d in data["data_models"]],
            interfaces=[InterfaceSpec.from_dict(i) for i in data["interfaces"]],
            error_handling=ErrorHandlingStrategy.from_dict(data["error_handling"]),
            testing_strategy=TestingStrategy.from_dict(data["testing_strategy"]),
            version=data["version"],
            approved=data["approved"],
        )


@dataclass
class Task:
    """Implementation task specification."""

    id: str
    title: str
    description: str
    requirements_refs: list[str]
    subtasks: list[str]
    status: TaskStatus
    target_language: str = "python"
    context_requirements: list[str] = None
    implementation_notes: str | None = None
    generated_files: list[str] = None

    def __post_init__(self):
        if self.context_requirements is None:
            self.context_requirements = []
        if self.generated_files is None:
            self.generated_files = []


@dataclass
class TaskList:
    """Complete task list document."""

    tasks: list[Task]
    dependencies: dict[str, list[str]]
    estimated_effort: dict[str, int]
    version: str
    approved: bool
