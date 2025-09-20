"""Core enums for the dev-agent system."""

from enum import Enum


class PhaseType(Enum):
    """Represents the four phases of the development workflow."""

    INDEXING = "indexing"
    SPECIFICATION = "specification"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"


class PhaseStatus(Enum):
    """Status of a workflow phase."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"


class TaskStatus(Enum):
    """Status of an implementation task."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Priority(Enum):
    """Priority level for requirements and tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentType(Enum):
    """Types of documents managed by the system."""

    SPECIFICATION = "specification"
    DESIGN = "design"
    TASKS = "tasks"


class SpecificationSource(Enum):
    """Source of specification generation."""

    EXISTING_CODE = "existing_code"
    USER_INPUT = "user_input"

class LanguageType(Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    SQL = "sql"
    DOCKERFILE = "dockerfile"
    SHELL = "shell"
    MAKEFILE = "makefile"


class FrameworkType(Enum):
    """Supported frameworks and libraries."""

    # Python frameworks
    DJANGO = "django"
    FLASK = "flask"
    FASTAPI = "fastapi"
    PYTEST = "pytest"
    SQLALCHEMY = "sqlalchemy"
    CELERY = "celery"
    PANDAS = "pandas"
    NUMPY = "numpy"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"

    # JavaScript/TypeScript frameworks
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    EXPRESS = "express"
    NODEJS = "nodejs"
    WEBPACK = "webpack"
    BABEL = "babel"
    JEST = "jest"
    ESLINT = "eslint"
    NESTJS = "nestjs"

    # Java frameworks
    SPRING_BOOT = "spring_boot"
    SPRING = "spring"
    HIBERNATE = "hibernate"
    JUNIT = "junit"
    MAVEN = "maven"
    GRADLE = "gradle"

    # Web frameworks
    BOOTSTRAP = "bootstrap"
    TAILWIND = "tailwind"
    JQUERY = "jquery"
    SASS = "sass"


class PatternType(Enum):
    """Types of code patterns that can be analyzed."""

    NAMING_CONVENTION = "naming_convention"
    ARCHITECTURAL = "architectural"
    DESIGN_PATTERN = "design_pattern"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    IMPORT_STYLE = "import_style"
    FORMATTING = "formatting"