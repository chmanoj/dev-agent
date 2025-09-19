"""Document data models for specifications, designs, and tasks."""

from dataclasses import dataclass
from datetime import datetime

from .enums import Priority, SpecificationSource, TaskStatus


@dataclass
class CodeAnalysisRef:
    """Reference to code analysis that informed a requirement."""

    file_paths: list[str]
    functions: list[str]
    confidence_score: float


@dataclass
class Requirement:
    """A functional requirement with acceptance criteria."""

    id: str
    user_story: str
    acceptance_criteria: list[str]
    priority: Priority
    source_analysis: CodeAnalysisRef | None = None


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
