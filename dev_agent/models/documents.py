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


@dataclass
class DataModel:
    """Data model specification."""

    name: str
    fields: dict[str, str]
    relationships: list[str]


@dataclass
class InterfaceSpec:
    """Interface specification."""

    name: str
    methods: list[str]
    description: str


@dataclass
class ErrorHandlingStrategy:
    """Error handling strategy specification."""

    error_categories: list[str]
    recovery_mechanisms: list[str]
    logging_strategy: str


@dataclass
class TestingStrategy:
    """Testing strategy specification."""

    unit_testing: str
    integration_testing: str
    performance_testing: str
    test_coverage_target: float


@dataclass
class ArchitectureDescription:
    """Architecture description."""

    overview: str
    patterns: list[str]
    components: list[str]


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
