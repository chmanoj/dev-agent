"""Test data management for consistent testing."""

import shutil
import tempfile
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ProjectSize(Enum):
    """Enumeration for project sizes."""

    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"


class ProjectType(Enum):
    """Enumeration for project types."""

    WEB_API = "web_api"
    DATA_PROCESSING = "data_processing"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    MICROSERVICE = "microservice"


@dataclass
class TestProjectSpec:
    """Specification for a test project."""

    name: str
    project_type: ProjectType
    size: ProjectSize
    num_files: int
    lines_per_file: int
    features: list[str]
    dependencies: list[str]
    complexity_level: int  # 1-5 scale


class TestDataManager:
    """Manager for creating and managing test data consistently."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize test data manager.

        Args:
            base_dir: Base directory for test data (uses temp if None)
        """
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.mkdtemp())
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Project specifications
        self.project_specs = self._define_project_specs()

        # Template cache
        self._template_cache = {}

    def _define_project_specs(self) -> dict[str, TestProjectSpec]:
        """Define standard project specifications."""
        return {
            "tiny_web_api": TestProjectSpec(
                name="tiny_web_api",
                project_type=ProjectType.WEB_API,
                size=ProjectSize.TINY,
                num_files=5,
                lines_per_file=100,
                features=["FastAPI", "Basic CRUD"],
                dependencies=["fastapi", "uvicorn"],
                complexity_level=1,
            ),
            "small_web_api": TestProjectSpec(
                name="small_web_api",
                project_type=ProjectType.WEB_API,
                size=ProjectSize.SMALL,
                num_files=15,
                lines_per_file=200,
                features=["FastAPI", "SQLAlchemy", "Authentication"],
                dependencies=["fastapi", "sqlalchemy", "python-jose"],
                complexity_level=2,
            ),
            "medium_web_api": TestProjectSpec(
                name="medium_web_api",
                project_type=ProjectType.WEB_API,
                size=ProjectSize.MEDIUM,
                num_files=35,
                lines_per_file=400,
                features=[
                    "FastAPI",
                    "SQLAlchemy",
                    "Authentication",
                    "Testing",
                    "Docker",
                ],
                dependencies=["fastapi", "sqlalchemy", "pytest", "docker"],
                complexity_level=3,
            ),
            "large_web_api": TestProjectSpec(
                name="large_web_api",
                project_type=ProjectType.WEB_API,
                size=ProjectSize.LARGE,
                num_files=75,
                lines_per_file=600,
                features=[
                    "FastAPI",
                    "SQLAlchemy",
                    "Authentication",
                    "Testing",
                    "Docker",
                    "Monitoring",
                ],
                dependencies=["fastapi", "sqlalchemy", "pytest", "prometheus-client"],
                complexity_level=4,
            ),
            "small_data_processing": TestProjectSpec(
                name="small_data_processing",
                project_type=ProjectType.DATA_PROCESSING,
                size=ProjectSize.SMALL,
                num_files=12,
                lines_per_file=300,
                features=["Pandas", "NumPy", "Data cleaning"],
                dependencies=["pandas", "numpy", "scikit-learn"],
                complexity_level=2,
            ),
            "medium_data_processing": TestProjectSpec(
                name="medium_data_processing",
                project_type=ProjectType.DATA_PROCESSING,
                size=ProjectSize.MEDIUM,
                num_files=30,
                lines_per_file=500,
                features=["Pandas", "NumPy", "Machine Learning", "Visualization"],
                dependencies=["pandas", "numpy", "scikit-learn", "matplotlib"],
                complexity_level=3,
            ),
            "small_cli_tool": TestProjectSpec(
                name="small_cli_tool",
                project_type=ProjectType.CLI_TOOL,
                size=ProjectSize.SMALL,
                num_files=10,
                lines_per_file=250,
                features=["Click", "File operations", "Configuration"],
                dependencies=["click", "pyyaml"],
                complexity_level=2,
            ),
            "medium_library": TestProjectSpec(
                name="medium_library",
                project_type=ProjectType.LIBRARY,
                size=ProjectSize.MEDIUM,
                num_files=25,
                lines_per_file=350,
                features=["Public API", "Documentation", "Testing"],
                dependencies=["pytest", "sphinx"],
                complexity_level=3,
            ),
            "huge_project": TestProjectSpec(
                name="huge_project",
                project_type=ProjectType.WEB_API,
                size=ProjectSize.HUGE,
                num_files=150,
                lines_per_file=800,
                features=[
                    "Microservices",
                    "Database",
                    "Caching",
                    "Monitoring",
                    "Testing",
                ],
                dependencies=["fastapi", "sqlalchemy", "redis", "pytest"],
                complexity_level=5,
            ),
        }

    def create_sample_python_project(self, spec_name: str) -> Path:
        """Create a sample Python project based on specification.

        Args:
            spec_name: Name of the project specification

        Returns:
            Path to the created project
        """
        if spec_name not in self.project_specs:
            raise ValueError(f"Unknown project spec: {spec_name}")

        spec = self.project_specs[spec_name]
        project_path = self.base_dir / spec.name

        # Remove existing project if it exists
        if project_path.exists():
            shutil.rmtree(project_path)

        project_path.mkdir(parents=True)

        # Create project based on type
        if spec.project_type == ProjectType.WEB_API:
            return self._create_web_api_project(project_path, spec)
        elif spec.project_type == ProjectType.DATA_PROCESSING:
            return self._create_data_processing_project(project_path, spec)
        elif spec.project_type == ProjectType.CLI_TOOL:
            return self._create_cli_tool_project(project_path, spec)
        elif spec.project_type == ProjectType.LIBRARY:
            return self._create_library_project(project_path, spec)
        elif spec.project_type == ProjectType.MICROSERVICE:
            return self._create_microservice_project(project_path, spec)
        else:
            raise ValueError(f"Unsupported project type: {spec.project_type}")

    def _create_web_api_project(
        self, project_path: Path, spec: TestProjectSpec
    ) -> Path:
        """Create a web API project."""
        # Create directory structure
        directories = [
            "src/api/routes",
            "src/models",
            "src/services",
            "src/database",
            "src/auth",
            "tests/unit",
            "tests/integration",
            "config",
            "migrations",
        ]

        for dir_path in directories:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Create main application file
        main_content = self._get_web_api_main_template(spec)
        (project_path / "src" / "main.py").write_text(main_content)

        # Create model files
        for i in range(min(5, spec.num_files // 3)):
            model_content = self._get_model_template(f"Model{i:02d}", spec)
            (project_path / "src" / "models" / f"model_{i:02d}.py").write_text(
                model_content
            )

        # Create service files
        for i in range(min(5, spec.num_files // 3)):
            service_content = self._get_service_template(f"Service{i:02d}", spec)
            (project_path / "src" / "services" / f"service_{i:02d}.py").write_text(
                service_content
            )

        # Create API route files
        for i in range(min(5, spec.num_files // 3)):
            route_content = self._get_route_template(f"Route{i:02d}", spec)
            (project_path / "src" / "api" / "routes" / f"routes_{i:02d}.py").write_text(
                route_content
            )

        # Create test files
        for i in range(min(10, spec.num_files - 15)):
            test_content = self._get_test_template(f"Test{i:02d}", spec)
            test_dir = "unit" if i % 2 == 0 else "integration"
            (project_path / "tests" / test_dir / f"test_{i:02d}.py").write_text(
                test_content
            )

        # Create configuration files
        self._create_config_files(project_path, spec)

        return project_path

    def _create_data_processing_project(
        self, project_path: Path, spec: TestProjectSpec
    ) -> Path:
        """Create a data processing project."""
        # Create directory structure
        directories = [
            "src/processors",
            "src/analyzers",
            "src/exporters",
            "src/utils",
            "tests/unit",
            "tests/integration",
            "data/raw",
            "data/processed",
            "config",
            "notebooks",
        ]

        for dir_path in directories:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Create main pipeline
        pipeline_content = self._get_data_pipeline_template(spec)
        (project_path / "src" / "pipeline.py").write_text(pipeline_content)

        # Create processor files
        for i in range(min(8, spec.num_files // 2)):
            processor_content = self._get_data_processor_template(
                f"Processor{i:02d}", spec
            )
            (project_path / "src" / "processors" / f"processor_{i:02d}.py").write_text(
                processor_content
            )

        # Create analyzer files
        for i in range(min(5, spec.num_files // 3)):
            analyzer_content = self._get_data_analyzer_template(
                f"Analyzer{i:02d}", spec
            )
            (project_path / "src" / "analyzers" / f"analyzer_{i:02d}.py").write_text(
                analyzer_content
            )

        # Create utility files
        for i in range(min(5, spec.num_files // 4)):
            util_content = self._get_utility_template(f"Util{i:02d}", spec)
            (project_path / "src" / "utils" / f"util_{i:02d}.py").write_text(
                util_content
            )

        # Create test files
        remaining_files = spec.num_files - 18  # Subtract already created files
        for i in range(max(0, remaining_files)):
            test_content = self._get_test_template(f"DataTest{i:02d}", spec)
            test_dir = "unit" if i % 2 == 0 else "integration"
            (project_path / "tests" / test_dir / f"test_data_{i:02d}.py").write_text(
                test_content
            )

        # Create configuration files
        self._create_config_files(project_path, spec)

        return project_path

    def _create_cli_tool_project(
        self, project_path: Path, spec: TestProjectSpec
    ) -> Path:
        """Create a CLI tool project."""
        # Create directory structure
        directories = [
            "src/commands",
            "src/utils",
            "src/config",
            "tests/unit",
            "tests/integration",
            "docs",
        ]

        for dir_path in directories:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Create main CLI file
        cli_content = self._get_cli_main_template(spec)
        (project_path / "src" / "cli.py").write_text(cli_content)

        # Create command files
        for i in range(min(6, spec.num_files // 2)):
            command_content = self._get_cli_command_template(f"Command{i:02d}", spec)
            (project_path / "src" / "commands" / f"command_{i:02d}.py").write_text(
                command_content
            )

        # Create utility files
        for i in range(min(4, spec.num_files // 3)):
            util_content = self._get_utility_template(f"CliUtil{i:02d}", spec)
            (project_path / "src" / "utils" / f"util_{i:02d}.py").write_text(
                util_content
            )

        # Create test files
        remaining_files = spec.num_files - 10
        for i in range(max(0, remaining_files)):
            test_content = self._get_test_template(f"CliTest{i:02d}", spec)
            test_dir = "unit" if i % 2 == 0 else "integration"
            (project_path / "tests" / test_dir / f"test_cli_{i:02d}.py").write_text(
                test_content
            )

        # Create configuration files
        self._create_config_files(project_path, spec)

        return project_path

    def _create_library_project(
        self, project_path: Path, spec: TestProjectSpec
    ) -> Path:
        """Create a library project."""
        # Create directory structure
        directories = [
            "src/core",
            "src/utils",
            "src/exceptions",
            "tests/unit",
            "tests/integration",
            "docs",
            "examples",
        ]

        for dir_path in directories:
            (project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Create main library files
        for i in range(min(10, spec.num_files // 2)):
            core_content = self._get_library_core_template(f"Core{i:02d}", spec)
            (project_path / "src" / "core" / f"core_{i:02d}.py").write_text(
                core_content
            )

        # Create utility files
        for i in range(min(5, spec.num_files // 4)):
            util_content = self._get_utility_template(f"LibUtil{i:02d}", spec)
            (project_path / "src" / "utils" / f"util_{i:02d}.py").write_text(
                util_content
            )

        # Create test files
        remaining_files = spec.num_files - 15
        for i in range(max(0, remaining_files)):
            test_content = self._get_test_template(f"LibTest{i:02d}", spec)
            test_dir = "unit" if i % 2 == 0 else "integration"
            (project_path / "tests" / test_dir / f"test_lib_{i:02d}.py").write_text(
                test_content
            )

        # Create configuration files
        self._create_config_files(project_path, spec)

        return project_path

    def _create_microservice_project(
        self, project_path: Path, spec: TestProjectSpec
    ) -> Path:
        """Create a microservice project."""
        # Similar to web API but with additional microservice patterns
        return self._create_web_api_project(project_path, spec)

    def _get_web_api_main_template(self, spec: TestProjectSpec) -> str:
        """Get template for web API main file."""
        complexity_imports = ""
        complexity_middleware = ""

        if spec.complexity_level >= 2:
            complexity_imports += "from fastapi.middleware.cors import CORSMiddleware\n"
            complexity_middleware += """
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""

        if spec.complexity_level >= 3:
            complexity_imports += (
                "from prometheus_fastapi_instrumentator import Instrumentator\n"
            )
            complexity_middleware += "Instrumentator().instrument(app).expose(app)\n"

        return f'''"""Main FastAPI application for {spec.name}."""

from fastapi import FastAPI, HTTPException
import uvicorn
{complexity_imports}

app = FastAPI(
    title="{spec.name.replace("_", " ").title()}",
    description="Generated test API",
    version="1.0.0"
)

{complexity_middleware}

@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to {spec.name}"}}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

    def _get_model_template(self, class_name: str, spec: TestProjectSpec) -> str:
        """Get template for model files."""
        return f'''"""Model {class_name} for {spec.name}."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from typing import Dict, Any


class {class_name}:
    """Model class {class_name}."""
    
    def __init__(self, name: str, value: int = 0):
        self.name = name
        self.value = value
        self.created_at = datetime.now()
        self.active = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {{
            "name": self.name,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "active": self.active
        }}
    
    def update(self, **kwargs) -> None:
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def validate(self) -> bool:
        """Validate model data."""
        return bool(self.name and isinstance(self.value, int))
'''

    def _get_service_template(self, class_name: str, spec: TestProjectSpec) -> str:
        """Get template for service files."""
        return f'''"""Service {class_name} for {spec.name}."""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class {class_name}:
    """Service class {class_name}."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {{}}
        self.data_store = {{}}
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the service."""
        try:
            self._initialized = True
            logger.info(f"{class_name} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {class_name}: {{e}}")
            return False
    
    def create(self, data: Dict[str, Any]) -> str:
        """Create new item."""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        
        item_id = f"item_{{len(self.data_store)}}"
        self.data_store[item_id] = data
        return item_id
    
    def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item by ID."""
        return self.data_store.get(item_id)
    
    def update(self, item_id: str, data: Dict[str, Any]) -> bool:
        """Update item."""
        if item_id in self.data_store:
            self.data_store[item_id].update(data)
            return True
        return False
    
    def delete(self, item_id: str) -> bool:
        """Delete item."""
        if item_id in self.data_store:
            del self.data_store[item_id]
            return True
        return False
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all items."""
        return list(self.data_store.values())
'''

    def _get_route_template(self, class_name: str, spec: TestProjectSpec) -> str:
        """Get template for route files."""
        return f'''"""Routes {class_name} for {spec.name}."""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

router = APIRouter()


@router.get("/items", response_model=List[Dict[str, Any]])
async def get_items():
    """Get all items."""
    return [{{"id": 1, "name": "test_item"}}]


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(item: Dict[str, Any]):
    """Create new item."""
    return {{"message": "Item created", "id": 1}}


@router.get("/items/{{item_id}}")
async def get_item(item_id: int):
    """Get item by ID."""
    if item_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return {{"id": item_id, "name": f"item_{{item_id}}"}}


@router.put("/items/{{item_id}}")
async def update_item(item_id: int, item: Dict[str, Any]):
    """Update item."""
    return {{"message": "Item updated", "id": item_id}}


@router.delete("/items/{{item_id}}")
async def delete_item(item_id: int):
    """Delete item."""
    return {{"message": "Item deleted"}}
'''

    def _get_test_template(self, class_name: str, spec: TestProjectSpec) -> str:
        """Get template for test files."""
        return f'''"""Test {class_name} for {spec.name}."""

import pytest
from unittest.mock import Mock, patch


class Test{class_name}:
    """Test cases for {class_name}."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_data = {{"name": "test", "value": 42}}
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        assert True
    
    def test_with_mock(self):
        """Test with mocking."""
        mock_obj = Mock()
        mock_obj.method.return_value = "mocked"
        
        result = mock_obj.method()
        assert result == "mocked"
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            raise ValueError("Test error")
    
    @pytest.mark.parametrize("input_val,expected", [
        (1, 2),
        (2, 4),
        (3, 6)
    ])
    def test_parametrized(self, input_val, expected):
        """Test with parameters."""
        assert input_val * 2 == expected
'''

    def _get_data_pipeline_template(self, spec: TestProjectSpec) -> str:
        """Get template for data processing pipeline."""
        return f'''"""Data processing pipeline for {spec.name}."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DataPipeline:
    """Main data processing pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data = None
        self.processed_data = None
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from file."""
        logger.info(f"Loading data from {{file_path}}")
        
        if file_path.endswith('.csv'):
            self.data = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            self.data = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format")
        
        return self.data
    
    def clean_data(self) -> pd.DataFrame:
        """Clean the loaded data."""
        if self.data is None:
            raise ValueError("No data loaded")
        
        # Remove duplicates
        cleaned = self.data.drop_duplicates()
        
        # Handle missing values
        cleaned = cleaned.fillna(cleaned.mean(numeric_only=True))
        
        self.processed_data = cleaned
        return cleaned
    
    def analyze_data(self) -> Dict[str, Any]:
        """Analyze the processed data."""
        if self.processed_data is None:
            raise ValueError("No processed data available")
        
        analysis = {{
            "shape": self.processed_data.shape,
            "columns": list(self.processed_data.columns),
            "dtypes": self.processed_data.dtypes.to_dict(),
            "missing_values": self.processed_data.isnull().sum().to_dict(),
            "summary_stats": self.processed_data.describe().to_dict()
        }}
        
        return analysis
    
    def export_results(self, output_path: str) -> None:
        """Export processed data."""
        if self.processed_data is None:
            raise ValueError("No processed data to export")
        
        self.processed_data.to_csv(output_path, index=False)
        logger.info(f"Results exported to {{output_path}}")
'''

    def _get_data_processor_template(
        self, class_name: str, spec: TestProjectSpec
    ) -> str:
        """Get template for data processor files."""
        return f'''"""Data processor {class_name} for {spec.name}."""

import pandas as pd
import numpy as np
from typing import Any, Dict, List


class {class_name}:
    """Data processor {class_name}."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {{}}
        self.processed_count = 0
    
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process the input data."""
        if data.empty:
            return data
        
        # Apply transformations
        processed = data.copy()
        
        # Normalize numeric columns
        numeric_cols = processed.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            processed[col] = (processed[col] - processed[col].mean()) / processed[col].std()
        
        # Process categorical columns
        categorical_cols = processed.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            processed[col] = processed[col].str.lower().str.strip()
        
        self.processed_count += len(processed)
        return processed
    
    def validate(self, data: pd.DataFrame) -> bool:
        """Validate processed data."""
        if data.empty:
            return False
        
        # Check for infinite values
        if np.isinf(data.select_dtypes(include=[np.number])).any().any():
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {{
            "processed_count": self.processed_count,
            "config": self.config
        }}
'''

    def _get_data_analyzer_template(
        self, class_name: str, spec: TestProjectSpec
    ) -> str:
        """Get template for data analyzer files."""
        return f'''"""Data analyzer {class_name} for {spec.name}."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from scipy import stats


class {class_name}:
    """Data analyzer {class_name}."""
    
    def __init__(self):
        self.analysis_results = {{}}
    
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive data analysis."""
        results = {{}}
        
        # Basic statistics
        results['basic_stats'] = self._basic_statistics(data)
        
        # Correlation analysis
        results['correlations'] = self._correlation_analysis(data)
        
        # Distribution analysis
        results['distributions'] = self._distribution_analysis(data)
        
        self.analysis_results = results
        return results
    
    def _basic_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics."""
        numeric_data = data.select_dtypes(include=[np.number])
        
        return {{
            'mean': numeric_data.mean().to_dict(),
            'median': numeric_data.median().to_dict(),
            'std': numeric_data.std().to_dict(),
            'min': numeric_data.min().to_dict(),
            'max': numeric_data.max().to_dict()
        }}
    
    def _correlation_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between variables."""
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.shape[1] < 2:
            return {{'message': 'Not enough numeric columns for correlation'}}
        
        correlation_matrix = numeric_data.corr()
        
        return {{
            'correlation_matrix': correlation_matrix.to_dict(),
            'strong_correlations': self._find_strong_correlations(correlation_matrix)
        }}
    
    def _distribution_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data distributions."""
        numeric_data = data.select_dtypes(include=[np.number])
        results = {{}}
        
        for column in numeric_data.columns:
            col_data = numeric_data[column].dropna()
            
            # Normality test
            _, p_value = stats.normaltest(col_data)
            
            results[column] = {{
                'skewness': stats.skew(col_data),
                'kurtosis': stats.kurtosis(col_data),
                'is_normal': p_value > 0.05,
                'p_value': p_value
            }}
        
        return results
    
    def _find_strong_correlations(self, corr_matrix: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find strong correlations (>0.7 or <-0.7)."""
        strong_corrs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    strong_corrs.append({{
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': corr_value
                    }})
        
        return strong_corrs
'''

    def _get_cli_main_template(self, spec: TestProjectSpec) -> str:
        """Get template for CLI main file."""
        return f'''"""Main CLI application for {spec.name}."""

import click
from typing import Optional


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', type=click.Path(exists=True), help='Config file path')
@click.pass_context
def cli(ctx, verbose: bool, config: Optional[str]):
    """CLI tool for {spec.name.replace("_", " ")}."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def process(ctx, input_file: str, output: Optional[str]):
    """Process input file."""
    verbose = ctx.obj.get('verbose', False)
    
    if verbose:
        click.echo(f"Processing {{input_file}}")
    
    # Simulate processing
    result = f"Processed {{input_file}}"
    
    if output:
        with open(output, 'w') as f:
            f.write(result)
        click.echo(f"Output written to {{output}}")
    else:
        click.echo(result)


@cli.command()
def version():
    """Show version information."""
    click.echo("{spec.name} v1.0.0")


if __name__ == '__main__':
    cli()
'''

    def _get_cli_command_template(self, class_name: str, spec: TestProjectSpec) -> str:
        """Get template for CLI command files."""
        return f'''"""CLI command {class_name} for {spec.name}."""

import click
from typing import List, Optional


@click.group(name='{class_name.lower()}')
def {class_name.lower()}_group():
    """{class_name} commands."""
    pass


@{class_name.lower()}_group.command()
@click.argument('items', nargs=-1)
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'table']), default='table')
def list_items(items: List[str], format: str):
    """List items with specified format."""
    if not items:
        items = ['item1', 'item2', 'item3']
    
    if format == 'json':
        import json
        click.echo(json.dumps(list(items)))
    elif format == 'csv':
        click.echo(','.join(items))
    else:
        for item in items:
            click.echo(f"- {{item}}")


@{class_name.lower()}_group.command()
@click.argument('name')
@click.option('--description', '-d', help='Item description')
def create(name: str, description: Optional[str]):
    """Create new item."""
    click.echo(f"Created item: {{name}}")
    if description:
        click.echo(f"Description: {{description}}")


@{class_name.lower()}_group.command()
@click.argument('name')
@click.confirmation_option(prompt='Are you sure you want to delete this item?')
def delete(name: str):
    """Delete item."""
    click.echo(f"Deleted item: {{name}}")
'''

    def _get_utility_template(self, class_name: str, spec: TestProjectSpec) -> str:
        """Get template for utility files."""
        return f'''"""Utility {class_name} for {spec.name}."""

import os
import json
import hashlib
from typing import Any, Dict, List, Optional
from pathlib import Path


class {class_name}:
    """Utility class {class_name}."""
    
    @staticmethod
    def read_json_file(file_path: str) -> Dict[str, Any]:
        """Read JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def write_json_file(file_path: str, data: Dict[str, Any]) -> None:
        """Write JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate file hash."""
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def ensure_directory(dir_path: str) -> None:
        """Ensure directory exists."""
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[str]:
        """List files matching pattern."""
        path = Path(directory)
        return [str(f) for f in path.glob(pattern) if f.is_file()]
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{{size_bytes:.1f}} {{unit}}"
            size_bytes /= 1024
        return f"{{size_bytes:.1f}} TB"
'''

    def _get_library_core_template(self, class_name: str, spec: TestProjectSpec) -> str:
        """Get template for library core files."""
        return f'''"""Core library component {class_name} for {spec.name}."""

from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod


class {class_name}Interface(ABC):
    """Interface for {class_name}."""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data."""
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate data."""
        pass


class {class_name}({class_name}Interface):
    """Core library component {class_name}."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {{}}
        self._cache = {{}}
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the component."""
        try:
            self._initialized = True
            return True
        except Exception:
            return False
    
    def process(self, data: Any) -> Any:
        """Process input data."""
        if not self._initialized:
            raise RuntimeError("Component not initialized")
        
        if not self.validate(data):
            raise ValueError("Invalid input data")
        
        # Check cache
        cache_key = self._get_cache_key(data)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Process data
        result = self._process_internal(data)
        
        # Cache result
        self._cache[cache_key] = result
        
        return result
    
    def validate(self, data: Any) -> bool:
        """Validate input data."""
        return data is not None
    
    def _process_internal(self, data: Any) -> Any:
        """Internal processing logic."""
        if isinstance(data, (list, tuple)):
            return [self._transform_item(item) for item in data]
        else:
            return self._transform_item(data)
    
    def _transform_item(self, item: Any) -> Any:
        """Transform individual item."""
        return str(item).upper()
    
    def _get_cache_key(self, data: Any) -> str:
        """Generate cache key for data."""
        return str(hash(str(data)))
    
    def clear_cache(self) -> None:
        """Clear internal cache."""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get component statistics."""
        return {{
            "initialized": self._initialized,
            "cache_size": len(self._cache),
            "config": self.config
        }}
'''

    def _create_config_files(self, project_path: Path, spec: TestProjectSpec) -> None:
        """Create configuration files for the project."""
        # requirements.txt
        requirements = "\\n".join(spec.dependencies + ["pytest>=7.0.0"])
        (project_path / "requirements.txt").write_text(requirements)

        # pyproject.toml
        pyproject_content = f"""[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{spec.name.replace("_", "-")}"
version = "1.0.0"
description = "Generated test project"
authors = [{{name = "Test Author", email = "test@example.com"}}]
license = {{text = "MIT"}}
readme = "README.md"
requires-python = ">=3.8"
dependencies = {spec.dependencies}

[project.optional-dependencies]
test = ["pytest>=7.0.0", "pytest-cov>=3.0.0"]
"""
        (project_path / "pyproject.toml").write_text(pyproject_content)

        # README.md
        readme_content = f"""# {spec.name.replace("_", " ").title()}

Generated test project for {spec.project_type.value}.

## Features

{chr(10).join(f"- {feature}" for feature in spec.features)}

## Installation

```bash
pip install -e .
```

## Usage

See examples in the `examples/` directory.

## Testing

```bash
pytest
```
"""
        (project_path / "README.md").write_text(readme_content)

    def get_project_stats(self, project_path: Path) -> dict[str, Any]:
        """Get statistics for a created project.

        Args:
            project_path: Path to the project

        Returns:
            Dictionary with project statistics
        """
        if not project_path.exists():
            return {"error": "Project path does not exist"}

        python_files = list(project_path.rglob("*.py"))
        total_lines = 0

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    total_lines += len(f.readlines())
            except Exception:
                continue

        directories = [d for d in project_path.rglob("*") if d.is_dir()]

        return {
            "project_path": str(project_path),
            "python_files": len(python_files),
            "total_lines": total_lines,
            "directories": len(directories),
            "avg_lines_per_file": total_lines / len(python_files)
            if python_files
            else 0,
            "file_list": [str(f.relative_to(project_path)) for f in python_files],
        }

    def cleanup(self) -> None:
        """Clean up all created test data."""
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)

    def list_available_specs(self) -> list[str]:
        """List all available project specifications."""
        return list(self.project_specs.keys())

    def get_spec_info(self, spec_name: str) -> dict[str, Any] | None:
        """Get information about a project specification."""
        if spec_name not in self.project_specs:
            return None

        spec = self.project_specs[spec_name]
        return asdict(spec)


class TestDataManagerTests:
    """Tests for TestDataManager."""

    def test_create_small_web_api(self):
        """Test creating a small web API project."""
        manager = TestDataManager()

        try:
            project_path = manager.create_sample_python_project("small_web_api")
            assert project_path.exists()

            stats = manager.get_project_stats(project_path)
            assert stats["python_files"] > 10
            assert stats["total_lines"] > 1000

            print(f"Created small web API: {stats}")

        finally:
            manager.cleanup()

    def test_create_medium_data_processing(self):
        """Test creating a medium data processing project."""
        manager = TestDataManager()

        try:
            project_path = manager.create_sample_python_project(
                "medium_data_processing"
            )
            assert project_path.exists()

            stats = manager.get_project_stats(project_path)
            assert stats["python_files"] > 20
            assert stats["total_lines"] > 5000

            print(f"Created medium data processing: {stats}")

        finally:
            manager.cleanup()

    def test_list_specs(self):
        """Test listing available specifications."""
        manager = TestDataManager()

        specs = manager.list_available_specs()
        assert len(specs) > 5
        assert "small_web_api" in specs
        assert "medium_data_processing" in specs

        print(f"Available specs: {specs}")


if __name__ == "__main__":
    # Run tests
    tests = TestDataManagerTests()
    tests.test_create_small_web_api()
    tests.test_create_medium_data_processing()
    tests.test_list_specs()

    print("✅ All test data management tests passed!")
