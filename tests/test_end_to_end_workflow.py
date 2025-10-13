"""End-to-end workflow tests with real Python projects."""

import os
import time
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

from dev_agent.workflow.workflow_manager import WorkflowManager
from dev_agent.workflow.phase_manager import PhaseManager
from dev_agent.models.enums import PhaseType, PhaseStatus
from dev_agent.state.state_manager import StateManager


class TestEndToEndWorkflow:
    """End-to-end workflow tests with realistic Python projects."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        self.project_path.mkdir(parents=True)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_realistic_python_project(self, project_type: str = "web_api") -> dict:
        """Create a realistic Python project for testing.

        Args:
            project_type: Type of project to create ('web_api', 'data_processing', 'cli_tool')

        Returns:
            Dictionary with project statistics
        """
        if project_type == "web_api":
            return self._create_web_api_project()
        elif project_type == "data_processing":
            return self._create_data_processing_project()
        elif project_type == "cli_tool":
            return self._create_cli_tool_project()
        else:
            raise ValueError(f"Unknown project type: {project_type}")

    def _create_web_api_project(self) -> dict:
        """Create a realistic web API project."""
        # Create directory structure
        directories = [
            "src/api/routes",
            "src/models",
            "src/services",
            "src/database",
            "src/auth",
            "tests/unit",
            "tests/integration",
            "migrations",
            "config",
        ]

        for dir_path in directories:
            (self.project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Main application file
        (
            self.project_path / "src" / "main.py"
        ).write_text('''"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from .database.connection import get_db
from .models.user import User
from .models.product import Product
from .services.user_service import UserService
from .services.product_service import ProductService
from .auth.jwt_handler import JWTBearer
from .api.routes import users, products, auth

app = FastAPI(
    title="E-commerce API",
    description="A comprehensive e-commerce API built with FastAPI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(products.router, prefix="/products", tags=["products"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to E-commerce API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
''')

        # User model
        (
            self.project_path / "src" / "models" / "user.py"
        ).write_text('''"""User model definition."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.base import Base


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create user from dictionary."""
        return cls(
            username=data.get("username"),
            email=data.get("email"),
            hashed_password=data.get("hashed_password"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            is_active=data.get("is_active", True),
            is_admin=data.get("is_admin", False)
        )
''')

        # Product model
        (
            self.project_path / "src" / "models" / "product.py"
        ).write_text('''"""Product model definition."""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.base import Base


class Product(Base):
    """Product model for e-commerce catalog."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    stock_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"
    
    def to_dict(self):
        """Convert product to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "sku": self.sku,
            "category": self.category,
            "stock_quantity": self.stock_quantity,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.stock_quantity > 0
    
    def update_stock(self, quantity_change: int) -> bool:
        """Update stock quantity."""
        new_quantity = self.stock_quantity + quantity_change
        if new_quantity < 0:
            return False
        self.stock_quantity = new_quantity
        return True
''')

        # User service
        (
            self.project_path / "src" / "services" / "user_service.py"
        ).write_text('''"""User service for business logic."""

from typing import List, Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..models.user import User
from ..database.connection import get_db


class UserService:
    """Service class for user-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_user(self, user_data: dict) -> User:
        """Create a new user."""
        # Hash the password
        hashed_password = self.pwd_context.hash(user_data["password"])
        user_data["hashed_password"] = hashed_password
        del user_data["password"]
        
        user = User.from_dict(user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update_user(self, user_id: int, user_data: dict) -> Optional[User]:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in user_data.items():
            if hasattr(user, key) and key != "id":
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user
''')

        # API routes
        (
            self.project_path / "src" / "api" / "routes" / "users.py"
        ).write_text('''"""User API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...services.user_service import UserService
from ...auth.jwt_handler import JWTBearer
from ...models.user import User

router = APIRouter()
jwt_bearer = JWTBearer()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    """Create a new user."""
    user_service = UserService(db)
    
    # Check if user already exists
    if user_service.get_user_by_username(user_data.get("username")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if user_service.get_user_by_email(user_data.get("email")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = user_service.create_user(user_data)
    return {"message": "User created successfully", "user_id": user.id}


@router.get("/", response_model=List[dict])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(jwt_bearer)
):
    """Get list of users."""
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit)
    return [user.to_dict() for user in users]


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(jwt_bearer)
):
    """Get user by ID."""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user.to_dict()


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    token: str = Depends(jwt_bearer)
):
    """Update user information."""
    user_service = UserService(db)
    user = user_service.update_user(user_id, user_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User updated successfully", "user": user.to_dict()}


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(jwt_bearer)
):
    """Delete user by ID."""
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}
''')

        # Test files
        (
            self.project_path / "tests" / "unit" / "test_user_service.py"
        ).write_text('''"""Unit tests for UserService."""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from src.services.user_service import UserService
from src.models.user import User


class TestUserService:
    """Test cases for UserService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def user_service(self, mock_db):
        """Create a UserService instance with mock database."""
        return UserService(mock_db)
    
    def test_create_user(self, user_service, mock_db):
        """Test user creation."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Mock the database operations
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with pytest.mock.patch.object(User, 'from_dict', return_value=mock_user):
            result = user_service.create_user(user_data)
        
        # Assertions
        assert result == mock_user
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
    
    def test_get_user_by_id(self, user_service, mock_db):
        """Test getting user by ID."""
        user_id = 1
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        result = user_service.get_user_by_id(user_id)
        
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)
    
    def test_authenticate_user_success(self, user_service, mock_db):
        """Test successful user authentication."""
        username = "testuser"
        password = "testpassword"
        
        mock_user = Mock(spec=User)
        mock_user.hashed_password = "hashed_password"
        
        # Mock the database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Mock password verification
        user_service.pwd_context.verify = Mock(return_value=True)
        
        result = user_service.authenticate_user(username, password)
        
        assert result == mock_user
        user_service.pwd_context.verify.assert_called_once_with(password, "hashed_password")
    
    def test_authenticate_user_invalid_password(self, user_service, mock_db):
        """Test authentication with invalid password."""
        username = "testuser"
        password = "wrongpassword"
        
        mock_user = Mock(spec=User)
        mock_user.hashed_password = "hashed_password"
        
        # Mock the database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Mock password verification to fail
        user_service.pwd_context.verify = Mock(return_value=False)
        
        result = user_service.authenticate_user(username, password)
        
        assert result is None
''')

        # Configuration files
        (self.project_path / "requirements.txt").write_text("""fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
""")

        (self.project_path / "pyproject.toml").write_text("""[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ecommerce-api"
version = "1.0.0"
description = "E-commerce API built with FastAPI"
authors = [{name = "Test Author", email = "test@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "alembic>=1.12.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
]
""")

        return {
            "project_type": "web_api",
            "files_created": len(list(self.project_path.rglob("*.py")))
            + 2,  # +2 for config files
            "total_lines": sum(
                len(f.read_text().split("\n")) for f in self.project_path.rglob("*.py")
            ),
            "directories": len([d for d in self.project_path.rglob("*") if d.is_dir()]),
            "features": [
                "FastAPI",
                "SQLAlchemy",
                "Authentication",
                "CRUD operations",
                "Testing",
            ],
        }

    def _create_data_processing_project(self) -> dict:
        """Create a realistic data processing project."""
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
            "scripts",
        ]

        for dir_path in directories:
            (self.project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Main processing pipeline
        (
            self.project_path / "src" / "pipeline.py"
        ).write_text('''"""Main data processing pipeline."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .processors.data_cleaner import DataCleaner
from .processors.feature_extractor import FeatureExtractor
from .analyzers.statistical_analyzer import StatisticalAnalyzer
from .exporters.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class DataProcessingPipeline:
    """Main pipeline for data processing and analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the pipeline with configuration."""
        self.config = config
        self.data_cleaner = DataCleaner(config.get("cleaning", {}))
        self.feature_extractor = FeatureExtractor(config.get("features", {}))
        self.analyzer = StatisticalAnalyzer(config.get("analysis", {}))
        self.report_generator = ReportGenerator(config.get("reporting", {}))
        
        self.raw_data: Optional[pd.DataFrame] = None
        self.cleaned_data: Optional[pd.DataFrame] = None
        self.features: Optional[pd.DataFrame] = None
        self.analysis_results: Optional[Dict[str, Any]] = None
    
    def load_data(self, file_path: Path) -> pd.DataFrame:
        """Load data from file."""
        logger.info(f"Loading data from {file_path}")
        
        if file_path.suffix == '.csv':
            data = pd.read_csv(file_path)
        elif file_path.suffix == '.json':
            data = pd.read_json(file_path)
        elif file_path.suffix in ['.xlsx', '.xls']:
            data = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        self.raw_data = data
        logger.info(f"Loaded {len(data)} rows and {len(data.columns)} columns")
        return data
    
    def clean_data(self) -> pd.DataFrame:
        """Clean the loaded data."""
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        logger.info("Starting data cleaning process")
        self.cleaned_data = self.data_cleaner.clean(self.raw_data)
        
        logger.info(f"Data cleaning complete. {len(self.cleaned_data)} rows remaining")
        return self.cleaned_data
    
    def extract_features(self) -> pd.DataFrame:
        """Extract features from cleaned data."""
        if self.cleaned_data is None:
            raise ValueError("No cleaned data available. Call clean_data() first.")
        
        logger.info("Starting feature extraction")
        self.features = self.feature_extractor.extract(self.cleaned_data)
        
        logger.info(f"Feature extraction complete. {len(self.features.columns)} features extracted")
        return self.features
    
    def analyze_data(self) -> Dict[str, Any]:
        """Perform statistical analysis on features."""
        if self.features is None:
            raise ValueError("No features available. Call extract_features() first.")
        
        logger.info("Starting statistical analysis")
        self.analysis_results = self.analyzer.analyze(self.features)
        
        logger.info("Statistical analysis complete")
        return self.analysis_results
    
    def generate_report(self, output_path: Path) -> Path:
        """Generate analysis report."""
        if self.analysis_results is None:
            raise ValueError("No analysis results available. Call analyze_data() first.")
        
        logger.info(f"Generating report at {output_path}")
        report_path = self.report_generator.generate(
            self.analysis_results,
            output_path,
            include_data=self.features
        )
        
        logger.info(f"Report generated successfully at {report_path}")
        return report_path
    
    def run_full_pipeline(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Run the complete data processing pipeline."""
        logger.info("Starting full data processing pipeline")
        
        try:
            # Load and process data
            self.load_data(input_path)
            self.clean_data()
            self.extract_features()
            self.analyze_data()
            
            # Generate report
            report_path = self.generate_report(output_path)
            
            # Return summary
            summary = {
                "status": "success",
                "input_file": str(input_path),
                "output_file": str(report_path),
                "rows_processed": len(self.cleaned_data),
                "features_extracted": len(self.features.columns),
                "analysis_metrics": list(self.analysis_results.keys())
            }
            
            logger.info("Pipeline completed successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "input_file": str(input_path)
            }
''')

        # Data cleaner
        (
            self.project_path / "src" / "processors" / "data_cleaner.py"
        ).write_text('''"""Data cleaning utilities."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Data cleaning and preprocessing utilities."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize data cleaner with configuration."""
        self.config = config
        self.remove_duplicates = config.get("remove_duplicates", True)
        self.handle_missing = config.get("handle_missing", "drop")
        self.outlier_method = config.get("outlier_method", "iqr")
        self.outlier_threshold = config.get("outlier_threshold", 1.5)
    
    def clean(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean the input data."""
        logger.info("Starting data cleaning process")
        
        cleaned_data = data.copy()
        
        # Remove duplicates
        if self.remove_duplicates:
            initial_rows = len(cleaned_data)
            cleaned_data = cleaned_data.drop_duplicates()
            removed_duplicates = initial_rows - len(cleaned_data)
            logger.info(f"Removed {removed_duplicates} duplicate rows")
        
        # Handle missing values
        cleaned_data = self._handle_missing_values(cleaned_data)
        
        # Handle outliers
        cleaned_data = self._handle_outliers(cleaned_data)
        
        # Data type optimization
        cleaned_data = self._optimize_dtypes(cleaned_data)
        
        logger.info(f"Data cleaning complete. Final shape: {cleaned_data.shape}")
        return cleaned_data
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset."""
        logger.info("Handling missing values")
        
        if self.handle_missing == "drop":
            # Drop rows with any missing values
            initial_rows = len(data)
            data = data.dropna()
            removed_rows = initial_rows - len(data)
            logger.info(f"Dropped {removed_rows} rows with missing values")
            
        elif self.handle_missing == "fill":
            # Fill missing values with appropriate defaults
            for column in data.columns:
                if data[column].dtype in ['int64', 'float64']:
                    # Fill numeric columns with median
                    data[column] = data[column].fillna(data[column].median())
                else:
                    # Fill categorical columns with mode
                    mode_value = data[column].mode()
                    if len(mode_value) > 0:
                        data[column] = data[column].fillna(mode_value[0])
                    else:
                        data[column] = data[column].fillna("Unknown")
            
            logger.info("Filled missing values with appropriate defaults")
        
        return data
    
    def _handle_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle outliers in numeric columns."""
        logger.info("Handling outliers")
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if self.outlier_method == "iqr":
                Q1 = data[column].quantile(0.25)
                Q3 = data[column].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - self.outlier_threshold * IQR
                upper_bound = Q3 + self.outlier_threshold * IQR
                
                # Cap outliers instead of removing them
                data[column] = data[column].clip(lower=lower_bound, upper=upper_bound)
                
            elif self.outlier_method == "zscore":
                z_scores = np.abs((data[column] - data[column].mean()) / data[column].std())
                data = data[z_scores < self.outlier_threshold]
        
        logger.info("Outlier handling complete")
        return data
    
    def _optimize_dtypes(self, data: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types for memory efficiency."""
        logger.info("Optimizing data types")
        
        for column in data.columns:
            col_type = data[column].dtype
            
            if col_type == 'int64':
                # Try to downcast integers
                if data[column].min() >= 0:
                    if data[column].max() < 255:
                        data[column] = data[column].astype('uint8')
                    elif data[column].max() < 65535:
                        data[column] = data[column].astype('uint16')
                    elif data[column].max() < 4294967295:
                        data[column] = data[column].astype('uint32')
                else:
                    if data[column].min() > -128 and data[column].max() < 127:
                        data[column] = data[column].astype('int8')
                    elif data[column].min() > -32768 and data[column].max() < 32767:
                        data[column] = data[column].astype('int16')
                    elif data[column].min() > -2147483648 and data[column].max() < 2147483647:
                        data[column] = data[column].astype('int32')
            
            elif col_type == 'float64':
                # Try to downcast floats
                data[column] = pd.to_numeric(data[column], downcast='float')
            
            elif col_type == 'object':
                # Convert strings to categories if beneficial
                if data[column].nunique() / len(data) < 0.5:
                    data[column] = data[column].astype('category')
        
        logger.info("Data type optimization complete")
        return data
''')

        return {
            "project_type": "data_processing",
            "files_created": len(list(self.project_path.rglob("*.py"))),
            "total_lines": sum(
                len(f.read_text().split("\n")) for f in self.project_path.rglob("*.py")
            ),
            "directories": len([d for d in self.project_path.rglob("*") if d.is_dir()]),
            "features": [
                "Pandas",
                "NumPy",
                "Data cleaning",
                "Feature extraction",
                "Statistical analysis",
            ],
        }

    def _create_cli_tool_project(self) -> dict:
        """Create a realistic CLI tool project."""
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
            (self.project_path / dir_path).mkdir(parents=True, exist_ok=True)

        # Main CLI application
        (self.project_path / "src" / "cli.py").write_text('''"""Main CLI application."""

import click
import sys
from pathlib import Path
from typing import Optional

from .commands.file_operations import file_group
from .commands.data_operations import data_group
from .utils.config_manager import ConfigManager
from .utils.logger import setup_logging


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool, quiet: bool):
    """A powerful CLI tool for file and data operations."""
    
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Setup logging
    log_level = 'DEBUG' if verbose else 'WARNING' if quiet else 'INFO'
    setup_logging(log_level)
    
    # Load configuration
    config_manager = ConfigManager(config)
    ctx.obj['config'] = config_manager
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    click.echo("CLI Tool v1.0.0")
    if ctx.obj.get('verbose'):
        click.echo(f"Python: {sys.version}")
        click.echo(f"Platform: {sys.platform}")


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    config_manager = ctx.obj['config']
    config_data = config_manager.get_all()
    
    click.echo("Current Configuration:")
    for key, value in config_data.items():
        click.echo(f"  {key}: {value}")


# Add command groups
cli.add_command(file_group)
cli.add_command(data_group)


if __name__ == '__main__':
    cli()
''')

        # File operations commands
        (
            self.project_path / "src" / "commands" / "file_operations.py"
        ).write_text('''"""File operation commands."""

import click
import shutil
from pathlib import Path
from typing import List, Optional
import hashlib
import json

from ..utils.file_utils import FileUtils
from ..utils.progress_bar import ProgressBar


@click.group(name='file')
def file_group():
    """File operation commands."""
    pass


@file_group.command()
@click.argument('source', type=click.Path(exists=True))
@click.argument('destination', type=click.Path())
@click.option('--recursive', '-r', is_flag=True, help='Copy directories recursively')
@click.option('--preserve-metadata', '-p', is_flag=True, help='Preserve file metadata')
@click.pass_context
def copy(ctx, source: str, destination: str, recursive: bool, preserve_metadata: bool):
    """Copy files or directories."""
    source_path = Path(source)
    dest_path = Path(destination)
    
    try:
        if source_path.is_file():
            # Copy single file
            if preserve_metadata:
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copy(source_path, dest_path)
            
            if not ctx.obj.get('quiet'):
                click.echo(f"Copied {source} to {destination}")
        
        elif source_path.is_dir() and recursive:
            # Copy directory
            if preserve_metadata:
                shutil.copytree(source_path, dest_path, copy_function=shutil.copy2)
            else:
                shutil.copytree(source_path, dest_path)
            
            if not ctx.obj.get('quiet'):
                click.echo(f"Copied directory {source} to {destination}")
        
        else:
            raise click.ClickException("Source is a directory but --recursive not specified")
    
    except Exception as e:
        raise click.ClickException(f"Copy failed: {e}")


@file_group.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--algorithm', '-a', default='sha256', 
              type=click.Choice(['md5', 'sha1', 'sha256', 'sha512']),
              help='Hash algorithm to use')
@click.option('--output', '-o', type=click.Path(), help='Output file for hashes')
def hash(path: str, algorithm: str, output: Optional[str]):
    """Calculate file hashes."""
    path_obj = Path(path)
    file_utils = FileUtils()
    
    if path_obj.is_file():
        # Hash single file
        file_hash = file_utils.calculate_hash(path_obj, algorithm)
        result = f"{file_hash}  {path}"
        
        if output:
            with open(output, 'w') as f:
                f.write(result + '\\n')
        else:
            click.echo(result)
    
    elif path_obj.is_dir():
        # Hash all files in directory
        files = list(path_obj.rglob('*'))
        files = [f for f in files if f.is_file()]
        
        results = []
        with ProgressBar(len(files), "Hashing files") as progress:
            for file_path in files:
                try:
                    file_hash = file_utils.calculate_hash(file_path, algorithm)
                    relative_path = file_path.relative_to(path_obj)
                    results.append(f"{file_hash}  {relative_path}")
                    progress.update(1)
                except Exception as e:
                    click.echo(f"Error hashing {file_path}: {e}", err=True)
        
        if output:
            with open(output, 'w') as f:
                f.write('\\n'.join(results) + '\\n')
        else:
            for result in results:
                click.echo(result)


@file_group.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--pattern', '-p', help='File pattern to match')
@click.option('--size-min', type=int, help='Minimum file size in bytes')
@click.option('--size-max', type=int, help='Maximum file size in bytes')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), 
              default='table', help='Output format')
def analyze(directory: str, pattern: Optional[str], size_min: Optional[int], 
           size_max: Optional[int], format: str):
    """Analyze directory contents."""
    dir_path = Path(directory)
    file_utils = FileUtils()
    
    # Get file information
    files_info = file_utils.analyze_directory(
        dir_path, 
        pattern=pattern,
        size_min=size_min,
        size_max=size_max
    )
    
    if format == 'json':
        click.echo(json.dumps(files_info, indent=2, default=str))
    elif format == 'csv':
        # Simple CSV output
        click.echo("path,size,modified,type")
        for info in files_info:
            click.echo(f"{info['path']},{info['size']},{info['modified']},{info['type']}")
    else:
        # Table format
        click.echo(f"{'Path':<50} {'Size':<10} {'Modified':<20} {'Type':<10}")
        click.echo("-" * 90)
        for info in files_info:
            size_str = file_utils.format_size(info['size'])
            modified_str = info['modified'].strftime('%Y-%m-%d %H:%M')
            click.echo(f"{str(info['path']):<50} {size_str:<10} {modified_str:<20} {info['type']:<10}")
''')

        return {
            "project_type": "cli_tool",
            "files_created": len(list(self.project_path.rglob("*.py"))),
            "total_lines": sum(
                len(f.read_text().split("\n")) for f in self.project_path.rglob("*.py")
            ),
            "directories": len([d for d in self.project_path.rglob("*") if d.is_dir()]),
            "features": [
                "Click CLI",
                "File operations",
                "Data processing",
                "Configuration management",
            ],
        }

    @pytest.mark.asyncio
    async def test_web_api_project_workflow(self):
        """Test complete workflow with a web API project."""
        print("\n=== Testing Web API Project Workflow ===")

        # Create realistic web API project
        project_stats = self.create_realistic_python_project("web_api")
        print(f"Created web API project: {project_stats}")

        # Create mock CLI interface that approves everything
        mock_cli = Mock()
        mock_cli.display_message = Mock()
        mock_cli.display_progress = Mock()
        mock_cli.request_approval = Mock(return_value=True)
        mock_cli.get_user_input = Mock(return_value="Approved")

        # Initialize workflow manager
        workflow_manager = WorkflowManager(mock_cli)

        # Start project
        project_state = await workflow_manager.start_new_project(str(self.project_path))
        assert project_state is not None
        assert project_state.current_phase == PhaseType.INDEXING

        # Test indexing phase
        print("Testing indexing phase...")
        success = await workflow_manager.transition_to_phase(PhaseType.INDEXING)
        assert success, "Indexing phase should succeed"

        # Verify indexing results
        state_manager = StateManager(str(self.project_path))
        current_state = state_manager.load_project_state()
        assert current_state.indexing_complete
        assert current_state.index_metadata is not None

        print(
            f"Indexing complete: {current_state.index_metadata.total_files} files indexed"
        )

        # Test specification phase
        print("Testing specification phase...")
        success = await workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
        assert success, "Specification phase should succeed"

        # Verify specification was generated
        current_state = state_manager.load_project_state()
        assert current_state.specification is not None
        assert current_state.specification.approved

        print(
            f"Specification generated with {len(current_state.specification.functional_requirements)} requirements"
        )

        # Test design phase
        print("Testing design phase...")
        success = await workflow_manager.transition_to_phase(PhaseType.DESIGN)
        assert success, "Design phase should succeed"

        # Verify design was generated
        current_state = state_manager.load_project_state()
        assert current_state.design is not None
        assert current_state.design.approved

        print(
            f"Design generated with {len(current_state.design.components)} components"
        )

        # Test implementation phase
        print("Testing implementation phase...")
        success = await workflow_manager.transition_to_phase(PhaseType.IMPLEMENTATION)
        assert success, "Implementation phase should succeed"

        # Verify tasks were generated
        current_state = state_manager.load_project_state()
        assert current_state.tasks is not None
        assert current_state.tasks.approved

        print(f"Implementation tasks generated: {len(current_state.tasks.tasks)} tasks")

        # Verify CLI interactions
        assert mock_cli.display_message.call_count > 10, (
            "Should have many status messages"
        )
        assert mock_cli.request_approval.call_count >= 3, (
            "Should request approval for each phase"
        )

        print("✓ Web API project workflow test passed!")

    @pytest.mark.asyncio
    async def test_data_processing_project_workflow(self):
        """Test complete workflow with a data processing project."""
        print("\n=== Testing Data Processing Project Workflow ===")

        # Create realistic data processing project
        project_stats = self.create_realistic_python_project("data_processing")
        print(f"Created data processing project: {project_stats}")

        # Create mock CLI interface
        mock_cli = Mock()
        mock_cli.display_message = Mock()
        mock_cli.display_progress = Mock()
        mock_cli.request_approval = Mock(return_value=True)
        mock_cli.get_user_input = Mock(return_value="Looks good!")

        # Initialize workflow manager
        workflow_manager = WorkflowManager(mock_cli)

        # Run complete workflow
        project_state = await workflow_manager.start_new_project(str(self.project_path))
        success = await workflow_manager.execute_complete_workflow()

        assert success, "Complete workflow should succeed"

        # Verify final state
        state_manager = StateManager(str(self.project_path))
        final_state = state_manager.load_project_state()

        assert final_state.current_phase == PhaseType.IMPLEMENTATION
        assert final_state.indexing_complete
        assert final_state.specification is not None
        assert final_state.design is not None
        assert final_state.tasks is not None

        # Verify project-specific characteristics were captured
        spec_text = final_state.specification.introduction.lower()
        assert any(
            keyword in spec_text
            for keyword in ["data", "processing", "analysis", "pipeline"]
        )

        print("✓ Data processing project workflow test passed!")

    @pytest.mark.asyncio
    async def test_cli_tool_project_workflow(self):
        """Test complete workflow with a CLI tool project."""
        print("\n=== Testing CLI Tool Project Workflow ===")

        # Create realistic CLI tool project
        project_stats = self.create_realistic_python_project("cli_tool")
        print(f"Created CLI tool project: {project_stats}")

        # Create mock CLI interface
        mock_cli = Mock()
        mock_cli.display_message = Mock()
        mock_cli.display_progress = Mock()
        mock_cli.request_approval = Mock(return_value=True)
        mock_cli.get_user_input = Mock(return_value="Approved")

        # Initialize workflow manager
        workflow_manager = WorkflowManager(mock_cli)

        # Test workflow with timing
        start_time = time.time()

        project_state = await workflow_manager.start_new_project(str(self.project_path))
        success = await workflow_manager.execute_complete_workflow()

        end_time = time.time()
        workflow_time = end_time - start_time

        assert success, "Complete workflow should succeed"

        # Verify timing is reasonable
        assert workflow_time < 300, f"Workflow took too long: {workflow_time:.2f}s"

        # Verify final state
        state_manager = StateManager(str(self.project_path))
        final_state = state_manager.load_project_state()

        assert final_state.current_phase == PhaseType.IMPLEMENTATION

        # Verify CLI-specific characteristics were captured
        spec_text = final_state.specification.introduction.lower()
        assert any(
            keyword in spec_text for keyword in ["cli", "command", "tool", "interface"]
        )

        print(f"✓ CLI tool project workflow test passed in {workflow_time:.2f}s!")

    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self):
        """Test workflow error handling and recovery."""
        print("\n=== Testing Workflow Error Recovery ===")

        # Create project
        project_stats = self.create_realistic_python_project("web_api")

        # Create mock CLI interface that sometimes fails
        mock_cli = Mock()
        mock_cli.display_message = Mock()
        mock_cli.display_progress = Mock()

        # First approval fails, second succeeds
        mock_cli.request_approval = Mock(side_effect=[False, True, True, True])
        mock_cli.get_user_input = Mock(return_value="Retry approved")

        # Initialize workflow manager
        workflow_manager = WorkflowManager(mock_cli)

        # Start project
        project_state = await workflow_manager.start_new_project(str(self.project_path))

        # Test that failed approval is handled gracefully
        success = await workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
        assert not success, "First transition should fail due to approval denial"

        # Verify state didn't change
        state_manager = StateManager(str(self.project_path))
        current_state = state_manager.load_project_state()
        assert current_state.current_phase == PhaseType.INDEXING

        # Retry should succeed
        success = await workflow_manager.transition_to_phase(PhaseType.SPECIFICATION)
        assert success, "Retry should succeed"

        # Verify error messages were displayed
        assert mock_cli.display_message.call_count > 5

        print("✓ Workflow error recovery test passed!")

    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self):
        """Test workflow state persistence across sessions."""
        print("\n=== Testing Workflow State Persistence ===")

        # Create project
        project_stats = self.create_realistic_python_project("web_api")

        # Create mock CLI interface
        mock_cli = Mock()
        mock_cli.display_message = Mock()
        mock_cli.display_progress = Mock()
        mock_cli.request_approval = Mock(return_value=True)
        mock_cli.get_user_input = Mock(return_value="Approved")

        # Session 1: Start project and complete indexing
        workflow_manager1 = WorkflowManager(mock_cli)
        project_state1 = await workflow_manager1.start_new_project(str(self.project_path))

        success = await workflow_manager1.transition_to_phase(PhaseType.SPECIFICATION)
        assert success

        # Get session ID for verification
        session_id = project_state1.session_data.session_id

        # Session 2: Resume project
        workflow_manager2 = WorkflowManager(mock_cli)
        project_state2 = await workflow_manager2.resume_project(str(self.project_path))

        # Verify state was restored
        assert project_state2.session_data.session_id == session_id
        assert project_state2.current_phase == PhaseType.SPECIFICATION
        assert project_state2.indexing_complete
        assert project_state2.specification is not None

        # Continue workflow in second session
        success = await workflow_manager2.transition_to_phase(PhaseType.DESIGN)
        assert success

        # Session 3: Resume again
        workflow_manager3 = WorkflowManager(mock_cli)
        project_state3 = await workflow_manager3.resume_project(str(self.project_path))

        # Verify all progress was maintained
        assert project_state3.current_phase == PhaseType.DESIGN
        assert project_state3.specification is not None
        assert project_state3.design is not None

        print("✓ Workflow state persistence test passed!")

    @pytest.mark.asyncio
    async def test_workflow_performance_benchmarks(self):
        """Test workflow performance with different project sizes."""
        print("\n=== Testing Workflow Performance Benchmarks ===")

        project_types = ["web_api", "data_processing", "cli_tool"]
        performance_results = {}

        for project_type in project_types:
            print(f"\nBenchmarking {project_type} project...")

            # Create project
            project_stats = self.create_realistic_python_project(project_type)

            # Create mock CLI interface
            mock_cli = Mock()
            mock_cli.display_message = Mock()
            mock_cli.display_progress = Mock()
            mock_cli.request_approval = Mock(return_value=True)
            mock_cli.get_user_input = Mock(return_value="Approved")

            # Measure workflow performance
            workflow_manager = WorkflowManager(mock_cli)

            start_time = time.time()
            project_state = await workflow_manager.start_new_project(str(self.project_path))
            success = await workflow_manager.execute_complete_workflow()
            end_time = time.time()

            workflow_time = end_time - start_time

            assert success, f"Workflow should succeed for {project_type}"

            # Calculate performance metrics
            lines_per_second = project_stats["total_lines"] / workflow_time
            files_per_second = project_stats["files_created"] / workflow_time

            performance_results[project_type] = {
                "total_time": workflow_time,
                "lines_processed": project_stats["total_lines"],
                "files_processed": project_stats["files_created"],
                "lines_per_second": lines_per_second,
                "files_per_second": files_per_second,
            }

            print(
                f"{project_type}: {workflow_time:.2f}s, {lines_per_second:.0f} lines/s"
            )

            # Performance assertions
            assert workflow_time < 180, (
                f"Workflow too slow for {project_type}: {workflow_time:.2f}s"
            )
            assert lines_per_second > 100, (
                f"Processing too slow for {project_type}: {lines_per_second:.0f} lines/s"
            )

            # Clean up for next iteration
            self.teardown_method()
            self.setup_method()

        # Print summary
        print(f"\n=== Performance Summary ===")
        for project_type, results in performance_results.items():
            print(f"{project_type}:")
            print(f"  Total time: {results['total_time']:.2f}s")
            print(f"  Lines processed: {results['lines_processed']:,}")
            print(f"  Processing speed: {results['lines_per_second']:.0f} lines/s")

        print("✓ Workflow performance benchmarks test passed!")

    @pytest.mark.asyncio
    async def test_workflow_with_real_project_patterns(self):
        """Test workflow with realistic project patterns and structures."""
        print("\n=== Testing Workflow with Real Project Patterns ===")

        # Create a more complex project with realistic patterns
        project_stats = self.create_realistic_python_project("web_api")

        # Add some additional realistic files
        additional_files = [
            (
                "docker-compose.yml",
                "version: '3.8'\nservices:\n  api:\n    build: .\n    ports:\n      - '8000:8000'",
            ),
            (
                ".env.example",
                "DATABASE_URL=postgresql://user:pass@localhost/db\nSECRET_KEY=your-secret-key",
            ),
            (
                "Dockerfile",
                "FROM python:3.11\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt",
            ),
            (
                ".github/workflows/ci.yml",
                "name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest",
            ),
        ]

        for filename, content in additional_files:
            file_path = self.project_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Create mock CLI interface
        mock_cli = Mock()
        mock_cli.display_message = Mock()
        mock_cli.display_progress = Mock()
        mock_cli.request_approval = Mock(return_value=True)
        mock_cli.get_user_input = Mock(return_value="Approved")

        # Initialize workflow manager
        workflow_manager = WorkflowManager(mock_cli)

        # Run workflow
        project_state = await workflow_manager.start_new_project(str(self.project_path))
        success = await workflow_manager.execute_complete_workflow()

        assert success, "Workflow should handle realistic project patterns"

        # Verify the workflow captured project characteristics
        state_manager = StateManager(str(self.project_path))
        final_state = state_manager.load_project_state()

        # Check that the specification includes relevant details
        spec_intro = final_state.specification.introduction.lower()
        assert any(
            keyword in spec_intro for keyword in ["api", "web", "service", "endpoint"]
        )

        # Check that design includes architectural components
        design_overview = final_state.design.overview.lower()
        assert any(
            keyword in design_overview
            for keyword in ["architecture", "component", "service", "model"]
        )

        # Check that tasks are comprehensive
        assert len(final_state.tasks.tasks) > 5, (
            "Should generate multiple implementation tasks"
        )

        # Verify indexing captured the project structure
        assert final_state.index_metadata.total_files >= project_stats["files_created"]
        assert "python" in final_state.index_metadata.languages_detected

        print("✓ Workflow with real project patterns test passed!")


if __name__ == "__main__":
    # Run the tests manually for debugging
    test_instance = TestEndToEndWorkflow()

    print("Running end-to-end workflow tests...")

    test_instance.setup_method()
    try:
        # Run individual tests
        test_instance.test_web_api_project_workflow()
        test_instance.test_data_processing_project_workflow()
        test_instance.test_cli_tool_project_workflow()
        test_instance.test_workflow_error_recovery()
        test_instance.test_workflow_state_persistence()
        test_instance.test_workflow_performance_benchmarks()
        test_instance.test_workflow_with_real_project_patterns()

        print("\n✅ All end-to-end workflow tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        test_instance.teardown_method()
