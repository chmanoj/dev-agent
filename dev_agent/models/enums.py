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
    STREAMLIT = "streamlit"
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


class ProjectType(Enum):
    """Types of projects that can be scaffolded."""

    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    MICROSERVICE = "microservice"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    DESKTOP_APPLICATION = "desktop_application"
    MOBILE_BACKEND = "mobile_backend"
    BATCH_PROCESSING = "batch_processing"


class TemplateType(Enum):
    """Types of templates available for scaffolding."""

    PROJECT_STRUCTURE = "project_structure"
    BUILD_CONFIGURATION = "build_configuration"
    CI_CD_PIPELINE = "ci_cd_pipeline"
    DOCUMENTATION = "documentation"
    TESTING_FRAMEWORK = "testing_framework"
    LINTING_CONFIGURATION = "linting_configuration"
    CONTAINERIZATION = "containerization"
    DEPLOYMENT = "deployment"


class TeamSize(Enum):
    """Team size categories for template customization."""

    SOLO = "solo"
    SMALL = "small"  # 2-5 developers
    MEDIUM = "medium"  # 6-15 developers
    LARGE = "large"  # 16+ developers


class CICDPlatform(Enum):
    """Supported CI/CD platforms."""

    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure_devops"
    CIRCLECI = "circleci"
    TRAVIS_CI = "travis_ci"


class LLMProvider(Enum):
    """Supported LLM providers.

    This enum defines the AI providers that can be used for code generation,
    specification creation, and embedding generation.
    """

    AZURE_OPENAI = "azure_openai"
    GEMINI = "gemini"
    # Future providers can be added here:
    # AWS_BEDROCK = "aws_bedrock"
    # OPENAI = "openai"


class LLMOperationType(Enum):
    """Types of LLM operations.

    This enum categorizes different types of operations performed with LLM
    providers, which is useful for tracking usage, costs, and performance.
    """

    COMPLETION = "completion"
    STREAMING = "streaming"
    EMBEDDING = "embedding"
    TOKEN_COUNT = "token_count"
