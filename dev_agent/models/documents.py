"""Document data models for specifications, designs, and tasks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .enums import Priority, SpecificationSource, TaskStatus

if TYPE_CHECKING:
    from .language_patterns import FrameworkPatterns, LanguagePatterns


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
    """Implementation task specification with language and framework awareness."""

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
    
    # New fields for language and framework patterns
    language: str | None = None  # Language type (e.g., "python", "typescript")
    framework: str | None = None  # Framework type (e.g., "fastapi", "react")
    naming_pattern: str | None = None  # Applied naming pattern (e.g., "snake_case", "PascalCase")
    file_patterns: list[str] = None  # Expected file patterns for this task
    validation_rules: list[str] = None  # Pattern validation rules to apply

    def __post_init__(self):
        if self.context_requirements is None:
            self.context_requirements = []
        if self.generated_files is None:
            self.generated_files = []
        if self.file_patterns is None:
            self.file_patterns = []
        if self.validation_rules is None:
            self.validation_rules = []
    
    def validate_naming_conventions(self, patterns: 'LanguagePatterns') -> list[str]:
        """Validate task naming against language patterns.
        
        Args:
            patterns: Language patterns to validate against
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        # Validate class names in title/description
        import re
        class_names = re.findall(r'\b[A-Z][a-zA-Z]*\b', self.title + " " + self.description)
        for class_name in class_names:
            if not patterns.validate_class_name(class_name):
                errors.append(f"Class name '{class_name}' doesn't follow {patterns.class_naming} convention")
        
        # Validate method names if mentioned
        method_names = re.findall(r'\b[a-z][a-zA-Z_]*\(\)', self.description)
        for method_name in method_names:
            method_name = method_name.replace('()', '')
            if not patterns.validate_method_name(method_name):
                errors.append(f"Method name '{method_name}' doesn't follow {patterns.method_naming} convention")
        
        return errors
    
    def apply_naming_patterns(self, patterns: 'LanguagePatterns') -> 'Task':
        """Apply language patterns to transform task naming.
        
        Args:
            patterns: Language patterns to apply
            
        Returns:
            New Task instance with transformed naming
        """
        # Transform class names in title and description
        import re
        
        def transform_class_names(text: str) -> str:
            class_names = re.findall(r'\b[A-Z][a-zA-Z]*\b', text)
            for class_name in class_names:
                transformed = patterns.transform_to_class_name(class_name)
                text = text.replace(class_name, transformed)
            return text
        
        def transform_method_names(text: str) -> str:
            method_matches = re.findall(r'\b[a-z][a-zA-Z_]*\(\)', text)
            for match in method_matches:
                method_name = match.replace('()', '')
                transformed = patterns.transform_to_method_name(method_name)
                text = text.replace(match, f"{transformed}()")
            return text
        
        # Create new task with transformed naming
        new_task = Task(
            id=self.id,
            title=transform_method_names(transform_class_names(self.title)),
            description=transform_method_names(transform_class_names(self.description)),
            requirements_refs=self.requirements_refs.copy(),
            subtasks=self.subtasks.copy(),
            status=self.status,
            target_language=self.target_language,
            context_requirements=self.context_requirements.copy() if self.context_requirements else [],
            implementation_notes=self.implementation_notes,
            generated_files=self.generated_files.copy() if self.generated_files else [],
            language=self.language,
            framework=self.framework,
            naming_pattern=f"{patterns.class_naming}/{patterns.method_naming}",
            file_patterns=self.file_patterns.copy() if self.file_patterns else [],
            validation_rules=self.validation_rules.copy() if self.validation_rules else []
        )
        
        return new_task
    
    def add_framework_context(self, framework_patterns: 'FrameworkPatterns') -> 'Task':
        """Add framework-specific context to the task.
        
        Args:
            framework_patterns: Framework patterns to apply
            
        Returns:
            New Task instance with framework context added
        """
        # Add framework-specific dependencies to context
        framework_context = []
        if framework_patterns.common_dependencies:
            framework_context.append(f"Framework dependencies: {', '.join(framework_patterns.common_dependencies[:3])}")
        
        if framework_patterns.component_suffix:
            framework_context.append(f"Component naming: use '{framework_patterns.component_suffix}' suffix")
        
        # Add framework-specific file patterns
        new_file_patterns = self.file_patterns.copy() if self.file_patterns else []
        new_file_patterns.extend(framework_patterns.test_file_patterns)
        
        # Create new task with framework context
        new_task = Task(
            id=self.id,
            title=self.title,
            description=self.description,
            requirements_refs=self.requirements_refs.copy(),
            subtasks=self.subtasks.copy(),
            status=self.status,
            target_language=self.target_language,
            context_requirements=(self.context_requirements or []) + framework_context,
            implementation_notes=self.implementation_notes,
            generated_files=self.generated_files.copy() if self.generated_files else [],
            language=self.language,
            framework=framework_patterns.framework.value,
            naming_pattern=self.naming_pattern,
            file_patterns=new_file_patterns,
            validation_rules=self.validation_rules.copy() if self.validation_rules else []
        )
        
        return new_task


@dataclass
class TaskList:
    """Complete task list document."""

    tasks: list[Task]
    dependencies: dict[str, list[str]]
    estimated_effort: dict[str, int]
    version: str
    approved: bool
