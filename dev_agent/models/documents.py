"""Document data models for specifications, designs, and tasks."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
from .enums import Priority, SpecificationSource, TaskStatus


@dataclass
class CodeAnalysisRef:
    """Reference to code analysis that informed a requirement."""
    file_paths: List[str]
    functions: List[str]
    confidence_score: float


@dataclass
class Requirement:
    """A functional requirement with acceptance criteria."""
    id: str
    user_story: str
    acceptance_criteria: List[str]
    priority: Priority
    source_analysis: Optional[CodeAnalysisRef] = None


@dataclass
class SpecificationDocument:
    """Complete specification document."""
    introduction: str
    key_features: List[str]
    functional_requirements: List[Requirement]
    source: SpecificationSource
    version: str
    approved: bool
    approval_timestamp: Optional[datetime] = None


@dataclass
class ComponentSpec:
    """Specification for a system component."""
    name: str
    description: str
    interfaces: List[str]
    dependencies: List[str]


@dataclass
class DataModel:
    """Data model specification."""
    name: str
    fields: Dict[str, str]
    relationships: List[str]


@dataclass
class InterfaceSpec:
    """Interface specification."""
    name: str
    methods: List[str]
    description: str


@dataclass
class ErrorHandlingStrategy:
    """Error handling strategy specification."""
    error_categories: List[str]
    recovery_mechanisms: List[str]
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
    patterns: List[str]
    components: List[str]


@dataclass
class DesignDocument:
    """Complete design document."""
    overview: str
    architecture: ArchitectureDescription
    components: List[ComponentSpec]
    data_models: List[DataModel]
    interfaces: List[InterfaceSpec]
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
    requirements_refs: List[str]
    subtasks: List[str]
    status: TaskStatus
    target_language: str = "python"
    context_requirements: List[str] = None
    implementation_notes: Optional[str] = None
    generated_files: List[str] = None
    
    def __post_init__(self):
        if self.context_requirements is None:
            self.context_requirements = []
        if self.generated_files is None:
            self.generated_files = []


@dataclass
class TaskList:
    """Complete task list document."""
    tasks: List[Task]
    dependencies: Dict[str, List[str]]
    estimated_effort: Dict[str, int]
    version: str
    approved: bool