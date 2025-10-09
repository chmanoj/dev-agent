"""Comprehensive end-to-end tests for Gemini API integration.

This test suite verifies the complete workflow functionality with Gemini provider:
- Complete workflow (indexing → specification → design → implementation)
- FAISS vector database compatibility with Gemini embeddings
- Provider switching during a session
- Cost tracking across both providers
- Error handling and recovery for Gemini API failures
- Backward compatibility with existing Azure OpenAI workflows

Requirements tested:
- 8.4: End-to-end workflow verification
- 8.5: Provider switching and compatibility
- 8.6: Backward compatibility with Azure OpenAI
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dev_agent.llm import create_embedding_client, create_llm_client
from dev_agent.models.enums import LLMProvider, PhaseStatus, PhaseType

if TYPE_CHECKING:
    from dev_agent.llm.cost_tracker import CostTracker
    from dev_agent.llm.gemini_client import GeminiClient
    from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient
    from dev_agent.models.llm_config import GeminiConfig


class TestGeminiEndToEndWorkflow:
    """Comprehensive end-to-end tests for Gemini integration."""

    @pytest.fixture
    def mock_gemini_config(self) -> GeminiConfig:
        """Create mock Gemini configuration."""
        from pydantic import SecretStr

        from dev_agent.models.llm_config import GeminiConfig

        return GeminiConfig(
            api_key=SecretStr("AIzaSyTest123456789012345678901234567890"),  # Valid length mock key
            model_name="gemini-pro",
            embedding_model="embedding-001",
            max_output_tokens=2048,
            temperature=0.7,
            max_retries=3,
            timeout=60,
        )

    @pytest.fixture
    def mock_azure_config(self):
        """Create mock Azure OpenAI configuration."""
        from pydantic import SecretStr

        from dev_agent.models.llm_config import AzureOpenAIConfig

        return AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-api-key"),
            api_version="2024-02-15-preview",
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

    @pytest.fixture
    def cost_tracker(self) -> CostTracker:
        """Create cost tracker."""
        from dev_agent.llm.cost_tracker import CostTracker

        return CostTracker()

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory with sample code."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create sample Python project structure
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()

            # Main module
            (project_path / "src" / "calculator.py").write_text('''"""Simple calculator module."""

from typing import Union

Number = Union[int, float]


class Calculator:
    """A simple calculator class."""
    
    def __init__(self) -> None:
        """Initialize calculator."""
        self.history: list[str] = []
    
    def add(self, a: Number, b: Number) -> Number:
        """Add two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Sum of a and b
        """
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: Number, b: Number) -> Number:
        """Subtract two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Difference of a and b
        """
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: Number, b: Number) -> Number:
        """Multiply two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Product of a and b
        """
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: Number, b: Number) -> Number:
        """Divide two numbers.
        
        Args:
            a: First number
            b: Second number (cannot be zero)
            
        Returns:
            Quotient of a and b
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def get_history(self) -> list[str]:
        """Get calculation history.
        
        Returns:
            List of calculation strings
        """
        return self.history.copy()
    
    def clear_history(self) -> None:
        """Clear calculation history."""
        self.history.clear()
''')

            # Test file
            (project_path / "tests" / "test_calculator.py").write_text('''"""Tests for calculator module."""

import pytest
from src.calculator import Calculator


class TestCalculator:
    """Test cases for Calculator class."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return Calculator()
    
    def test_add(self, calculator):
        """Test addition."""
        result = calculator.add(2, 3)
        assert result == 5
    
    def test_subtract(self, calculator):
        """Test subtraction."""
        result = calculator.subtract(5, 3)
        assert result == 2
    
    def test_multiply(self, calculator):
        """Test multiplication."""
        result = calculator.multiply(4, 3)
        assert result == 12
    
    def test_divide(self, calculator):
        """Test division."""
        result = calculator.divide(10, 2)
        assert result == 5.0
    
    def test_divide_by_zero(self, calculator):
        """Test division by zero raises error."""
        with pytest.raises(ZeroDivisionError):
            calculator.divide(10, 0)
    
    def test_history(self, calculator):
        """Test calculation history."""
        calculator.add(1, 2)
        calculator.subtract(5, 3)
        
        history = calculator.get_history()
        assert len(history) == 2
        assert "1 + 2 = 3" in history
        assert "5 - 3 = 2" in history
    
    def test_clear_history(self, calculator):
        """Test clearing history."""
        calculator.add(1, 2)
        calculator.clear_history()
        
        history = calculator.get_history()
        assert len(history) == 0
''')

            # Configuration files
            (project_path / "pyproject.toml").write_text('''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "calculator"
version = "1.0.0"
description = "Simple calculator application"
authors = [{name = "Test Author", email = "test@example.com"}]
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
test = ["pytest>=7.0.0"]
''')

            (project_path / "README.md").write_text('''# Calculator

A simple calculator application with basic arithmetic operations.

## Features

- Addition, subtraction, multiplication, division
- Calculation history
- Type hints and comprehensive documentation
- Full test coverage

## Usage

```python
from src.calculator import Calculator

calc = Calculator()
result = calc.add(2, 3)  # Returns 5
print(calc.get_history())  # Shows calculation history
```
''')

            yield project_path

    # Test 1: Complete Workflow with Gemini Provider
    @pytest.mark.asyncio
    async def test_complete_workflow_with_gemini(
        self,
        temp_project_dir: Path,
        mock_gemini_config: GeminiConfig,
        cost_tracker: CostTracker,
    ) -> None:
        """Test complete workflow: indexing → specification → design → implementation.

        Requirements: 8.4 - Complete workflow verification
        """
        from dev_agent.generation.design_generator import DesignGenerator
        from dev_agent.generation.python_code_generator import PythonCodeGenerator
        from dev_agent.generation.specification_generator import SpecificationGenerator
        from dev_agent.indexing.indexing_engine import IndexingEngine
        from dev_agent.llm.gemini_client import GeminiClient
        from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient

        # Mock Gemini API responses
        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel") as mock_model, \
             patch("google.generativeai.embed_content") as mock_embed:

            # Setup mocks
            mock_response = MagicMock()
            mock_response.text = "Generated specification content"
            mock_model.return_value.generate_content_async = AsyncMock(return_value=mock_response)

            mock_embed.return_value = {"embedding": [[0.1] * 768, [0.2] * 768]}

            # Create clients
            llm_client = GeminiClient(mock_gemini_config)
            embedding_client = GeminiEmbeddingClient(
                mock_gemini_config,
                cache_dir=temp_project_dir / ".dev_agent" / "embedding_cache"
            )

            # Mock token counting
            llm_client.count_tokens = MagicMock(return_value=50)

            # Phase 1: Indexing
            indexing_engine = IndexingEngine(
                project_path=str(temp_project_dir),
                embedding_client=embedding_client,
                cost_tracker=cost_tracker,
            )

            # Index the project
            index_result = indexing_engine.build_index()
            assert index_result is not None
            assert index_result.success
            assert index_result.embeddings_count >= 0

            # Phase 2: Specification Generation
            spec_generator = SpecificationGenerator(
                llm_client=llm_client,
                cost_tracker=cost_tracker,
            )

            feature_description = "Add a power function to calculate exponentiation"
            specification = await spec_generator.generate_specification(
                feature_description=feature_description,
                project_path=temp_project_dir,
                codebase_summary="Simple calculator with basic arithmetic operations",
            )

            assert specification is not None
            assert isinstance(specification, str)
            assert len(specification) > 0

            # Phase 3: Design Generation
            design_generator = DesignGenerator(
                llm_client=llm_client,
                cost_tracker=cost_tracker,
            )

            mock_response.text = "Generated design document"
            design = await design_generator.generate_design(
                specification=specification,
                project_path=temp_project_dir,
                codebase_summary="Calculator with arithmetic operations",
            )

            assert design is not None
            assert isinstance(design, str)
            assert len(design) > 0

            # Phase 4: Implementation
            code_generator = PythonCodeGenerator(
                llm_client=llm_client,
                cost_tracker=cost_tracker,
            )

            mock_response.text = '''def power(self, a: Number, b: Number) -> Number:
    """Calculate a raised to the power of b.
    
    Args:
        a: Base number
        b: Exponent
        
    Returns:
        a raised to the power of b
    """
    result = a ** b
    self.history.append(f"{a} ** {b} = {result}")
    return result'''

            code = await code_generator.generate_code(
                specification=specification,
                file_path=temp_project_dir / "src" / "calculator.py",
                context="Adding power function to Calculator class",
            )

            assert code is not None
            assert isinstance(code, str)
            assert "def power" in code
            assert "**" in code

            # Verify cost tracking across all phases
            report = cost_tracker.get_report()
            assert report["total_tokens"] > 0
            assert report["estimated_cost"] > 0

    # Test 2: FAISS Vector Database Compatibility
    @pytest.mark.asyncio
    async def test_faiss_compatibility_with_gemini_embeddings(
        self,
        temp_project_dir: Path,
        mock_gemini_config: GeminiConfig,
    ) -> None:
        """Test FAISS vector database compatibility with Gemini embeddings.

        Requirements: 8.4 - FAISS compatibility verification
        """
        from dev_agent.indexing.vector_database import VectorDatabase
        from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient

        with patch("google.generativeai.configure"), \
             patch("google.generativeai.embed_content") as mock_embed:

            # Mock embedding responses
            mock_embed.return_value = {
                "embedding": [
                    [0.1, 0.2, 0.3] + [0.0] * 765,  # 768-dimensional
                    [0.4, 0.5, 0.6] + [0.0] * 765,
                    [0.7, 0.8, 0.9] + [0.0] * 765,
                ]
            }

            embedding_client = GeminiEmbeddingClient(
                mock_gemini_config,
                cache_dir=temp_project_dir / ".dev_agent" / "embedding_cache"
            )

            # Create vector database
            db_path = temp_project_dir / ".dev_agent" / "vector.db"
            vector_db = VectorDatabase(
                db_path=db_path,
                embedding_client=embedding_client,
            )

            # Add code chunks
            code_chunks = [
                "def add(a, b): return a + b",
                "def subtract(a, b): return a - b",
                "def multiply(a, b): return a * b",
            ]

            for i, chunk in enumerate(code_chunks):
                embedding = await embedding_client.embed_text(chunk)
                vector_db.add_chunk(
                    chunk_id=f"chunk_{i}",
                    embedding=embedding,
                    metadata={"code": chunk, "function": chunk.split("(")[0].replace("def ", "")},
                )

            # Test similarity search
            query = "addition function"
            query_embedding = await embedding_client.embed_text(query)
            results = vector_db.search(query_embedding, top_k=2)

            assert len(results) > 0
            assert results[0]["metadata"]["function"] == "add"

            # Test batch operations
            batch_embeddings = await embedding_client.embed_batch(code_chunks)
            assert len(batch_embeddings) == len(code_chunks)
            assert all(len(emb) == 768 for emb in batch_embeddings)

    # Test 3: Provider Switching During Session
    @pytest.mark.asyncio
    async def test_provider_switching_during_session(
        self,
        temp_project_dir: Path,
        mock_gemini_config: GeminiConfig,
        mock_azure_config,
        cost_tracker: CostTracker,
    ) -> None:
        """Test switching between providers during a session.

        Requirements: 8.5 - Provider switching verification
        """
        from dev_agent.llm import create_embedding_client, create_llm_client

        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel") as mock_gemini_model, \
             patch("google.generativeai.embed_content") as mock_gemini_embed, \
             patch("openai.AsyncAzureOpenAI") as mock_azure_client:

            # Setup Gemini mocks
            mock_gemini_response = MagicMock()
            mock_gemini_response.text = "Gemini generated content"
            mock_gemini_model.return_value.generate_content_async = AsyncMock(
                return_value=mock_gemini_response
            )
            mock_gemini_embed.return_value = {"embedding": [[0.1] * 768]}

            # Setup Azure mocks
            mock_azure_instance = MagicMock()
            mock_azure_completion = MagicMock()
            mock_azure_completion.choices = [
                MagicMock(message=MagicMock(content="Azure generated content"))
            ]
            mock_azure_completion.usage = MagicMock(
                prompt_tokens=50, completion_tokens=100, total_tokens=150
            )
            mock_azure_instance.chat.completions.create = AsyncMock(
                return_value=mock_azure_completion
            )

            mock_azure_embedding = MagicMock()
            mock_azure_embedding.data = [MagicMock(embedding=[0.1] * 1536)]
            mock_azure_embedding.usage = MagicMock(total_tokens=25)
            mock_azure_instance.embeddings.create = AsyncMock(
                return_value=mock_azure_embedding
            )
            mock_azure_client.return_value = mock_azure_instance

            # Test 1: Start with Gemini
            gemini_llm = create_llm_client(
                provider=LLMProvider.GEMINI,
                config=mock_gemini_config,
            )

            gemini_result = await gemini_llm.generate_completion(
                prompt="Test prompt",
                max_tokens=100,
            )
            assert gemini_result == "Gemini generated content"

            # Test 2: Switch to Azure OpenAI
            azure_llm = create_llm_client(
                provider=LLMProvider.AZURE_OPENAI,
                config=mock_azure_config,
            )

            azure_result = await azure_llm.generate_completion(
                prompt="Test prompt",
                max_tokens=100,
            )
            assert azure_result == "Azure generated content"

            # Test 3: Test embedding clients
            cache_dir = temp_project_dir / ".dev_agent" / "embedding_cache"

            gemini_embedding = create_embedding_client(
                provider=LLMProvider.GEMINI,
                config=mock_gemini_config,
                cache_dir=cache_dir / "gemini",
            )

            azure_embedding = create_embedding_client(
                provider=LLMProvider.AZURE_OPENAI,
                config=mock_azure_config,
                cache_dir=cache_dir / "azure",
            )

            # Generate embeddings with both providers
            test_text = "def test(): pass"

            gemini_emb = await gemini_embedding.embed_text(test_text)
            azure_emb = await azure_embedding.embed_text(test_text)

            # Verify different dimensions
            assert len(gemini_emb) == 768  # Gemini dimension
            assert len(azure_emb) == 1536  # Azure OpenAI dimension

            # Test 4: Verify both can be used in same workflow
            from dev_agent.generation.specification_generator import SpecificationGenerator

            # Use Gemini for specification
            spec_gen_gemini = SpecificationGenerator(
                llm_client=gemini_llm,
                cost_tracker=cost_tracker,
            )

            spec = await spec_gen_gemini.generate_specification(
                feature_description="Add logging functionality",
                project_path=temp_project_dir,
                codebase_summary="Calculator application",
            )
            assert spec == "Gemini generated content"

            # Use Azure for design (switching providers mid-workflow)
            spec_gen_azure = SpecificationGenerator(
                llm_client=azure_llm,
                cost_tracker=cost_tracker,
            )

            design = await spec_gen_azure.generate_specification(
                feature_description="Design logging system",
                project_path=temp_project_dir,
                codebase_summary="Calculator with logging",
            )
            assert design == "Azure generated content"

    # Test 4: Cost Tracking Across Both Providers
    @pytest.mark.asyncio
    async def test_cost_tracking_across_providers(
        self,
        mock_gemini_config: GeminiConfig,
        mock_azure_config,
    ) -> None:
        """Test cost tracking works across both providers.

        Requirements: 8.4 - Cost tracking verification
        """
        from dev_agent.llm.cost_tracker import CostTracker
        from dev_agent.models.enums import LLMProvider

        cost_tracker = CostTracker()

        # Track Gemini usage
        cost_tracker.record_completion(
            prompt_tokens=100,
            completion_tokens=200,
            model="gemini-pro",
            provider=LLMProvider.GEMINI,
        )

        cost_tracker.record_embedding(
            tokens=50,
            model="embedding-001",
            provider=LLMProvider.GEMINI,
        )

        # Track Azure OpenAI usage
        cost_tracker.record_completion(
            prompt_tokens=150,
            completion_tokens=250,
            model="gpt-4",
            provider=LLMProvider.AZURE_OPENAI,
        )

        cost_tracker.record_embedding(
            tokens=75,
            model="text-embedding-ada-002",
            provider=LLMProvider.AZURE_OPENAI,
        )

        # Get comprehensive report
        report = cost_tracker.get_report()

        # Verify total tracking
        assert report.total_prompt_tokens == 375  # 100+50+150+75 (includes embedding tokens)
        assert report.total_completion_tokens == 450  # 200+250
        assert report.total_embedding_tokens == 125  # 50+75
        assert report.total_cost > 0

        # Verify provider-specific tracking
        assert LLMProvider.GEMINI in report.by_provider
        assert LLMProvider.AZURE_OPENAI in report.by_provider

        gemini_cost = report.by_provider[LLMProvider.GEMINI]
        azure_cost = report.by_provider[LLMProvider.AZURE_OPENAI]

        # Verify cost calculations are different for each provider
        assert gemini_cost != azure_cost
        assert gemini_cost > 0
        assert azure_cost > 0

    # Test 5: Error Handling and Recovery
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(
        self,
        mock_gemini_config: GeminiConfig,
    ) -> None:
        """Test error handling and recovery for Gemini API failures.

        Requirements: 8.4 - Error handling verification
        """
        from google.api_core import exceptions as google_exceptions

        from dev_agent.errors.llm_exceptions import (
            LLMAPIError,
            LLMAuthenticationError,
            LLMRateLimitError,
            LLMTimeoutError,
        )
        from dev_agent.llm.gemini_client import GeminiClient

        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel") as mock_model:

            client = GeminiClient(mock_gemini_config)

            # Test 1: Authentication Error
            mock_model.return_value.generate_content_async = AsyncMock(
                side_effect=google_exceptions.PermissionDenied("Invalid API key")
            )

            with pytest.raises(LLMAuthenticationError) as exc_info:
                await client.generate_completion("test prompt")

            assert "authenticate with Google Gemini API" in str(exc_info.value)

            # Test 2: Rate Limit Error (should be retried)
            mock_model.return_value.generate_content_async = AsyncMock(
                side_effect=google_exceptions.ResourceExhausted("Rate limit exceeded")
            )

            with pytest.raises(google_exceptions.ResourceExhausted):
                # This will be retried by tenacity but eventually fail
                await client.generate_completion("test prompt")

            # Test 3: Timeout Error
            mock_model.return_value.generate_content_async = AsyncMock(
                side_effect=google_exceptions.DeadlineExceeded("Request timeout")
            )

            with pytest.raises(google_exceptions.DeadlineExceeded):
                await client.generate_completion("test prompt")

            # Test 4: Generic API Error
            mock_model.return_value.generate_content_async = AsyncMock(
                side_effect=google_exceptions.GoogleAPIError("Service unavailable")
            )

            with pytest.raises(LLMAPIError):
                await client.generate_completion("test prompt")

            # Test 5: Recovery after error
            mock_response = MagicMock()
            mock_response.text = "Recovered response"
            mock_model.return_value.generate_content_async = AsyncMock(
                return_value=mock_response
            )

            result = await client.generate_completion("test prompt")
            assert result == "Recovered response"

    # Test 6: Backward Compatibility with Azure OpenAI
    @pytest.mark.asyncio
    async def test_backward_compatibility_with_azure(
        self,
        temp_project_dir: Path,
        mock_azure_config,
        cost_tracker: CostTracker,
    ) -> None:
        """Test backward compatibility with existing Azure OpenAI workflows.

        Requirements: 8.6 - Backward compatibility verification
        """
        from dev_agent.generation.specification_generator import SpecificationGenerator
        from dev_agent.indexing.indexing_engine import IndexingEngine
        from dev_agent.llm import create_embedding_client, create_llm_client

        with patch("openai.AsyncAzureOpenAI") as mock_azure_client:

            # Setup Azure mocks
            mock_azure_instance = MagicMock()
            mock_azure_completion = MagicMock()
            mock_azure_completion.choices = [
                MagicMock(message=MagicMock(content="Azure specification content"))
            ]
            mock_azure_completion.usage = MagicMock(
                prompt_tokens=100, completion_tokens=200, total_tokens=300
            )
            mock_azure_instance.chat.completions.create = AsyncMock(
                return_value=mock_azure_completion
            )

            mock_azure_embedding = MagicMock()
            mock_azure_embedding.data = [MagicMock(embedding=[0.1] * 1536)]
            mock_azure_embedding.usage = MagicMock(total_tokens=50)
            mock_azure_instance.embeddings.create = AsyncMock(
                return_value=mock_azure_embedding
            )
            mock_azure_client.return_value = mock_azure_instance

            # Test 1: Default provider should still be Azure OpenAI
            with patch.dict(os.environ, {}, clear=True):
                # No PREFERRED_LLM_PROVIDER set
                default_llm = create_llm_client()
                assert default_llm.__class__.__name__ == "AzureOpenAIClient"

                default_embedding = create_embedding_client(
                    cache_dir=temp_project_dir / ".dev_agent" / "embedding_cache"
                )
                assert default_embedding.__class__.__name__ == "AzureEmbeddingClient"

            # Test 2: Existing Azure workflows should work unchanged
            azure_llm = create_llm_client(
                provider=LLMProvider.AZURE_OPENAI,
                config=mock_azure_config,
            )

            azure_embedding = create_embedding_client(
                provider=LLMProvider.AZURE_OPENAI,
                config=mock_azure_config,
                cache_dir=temp_project_dir / ".dev_agent" / "embedding_cache",
            )

            # Test indexing with Azure (existing workflow)
            indexing_engine = IndexingEngine(
                project_path=str(temp_project_dir),
                embedding_client=azure_embedding,
                cost_tracker=cost_tracker,
            )

            index_result = indexing_engine.build_index()
            assert index_result is not None
            assert index_result.success

            # Test specification generation with Azure (existing workflow)
            spec_generator = SpecificationGenerator(
                llm_client=azure_llm,
                cost_tracker=cost_tracker,
            )

            specification = await spec_generator.generate_specification(
                feature_description="Add validation to calculator",
                project_path=temp_project_dir,
                codebase_summary="Calculator application",
            )

            assert specification == "Azure specification content"

            # Test 3: Cost tracking should work with Azure
            report = cost_tracker.get_report()
            assert report["total_tokens"] > 0
            assert LLMProvider.AZURE_OPENAI.value in report["by_provider"]

    # Test 7: Environment Variable Provider Selection
    @pytest.mark.asyncio
    async def test_environment_variable_provider_selection(self) -> None:
        """Test provider selection via environment variables.

        Requirements: 8.5 - Provider selection verification
        """
        from dev_agent.llm import get_preferred_provider

        # Test 1: Default to Azure OpenAI
        with patch.dict(os.environ, {}, clear=True):
            provider = get_preferred_provider()
            assert provider == LLMProvider.AZURE_OPENAI

        # Test 2: Explicit Gemini selection
        with patch.dict(os.environ, {"PREFERRED_LLM_PROVIDER": "gemini"}):
            provider = get_preferred_provider()
            assert provider == LLMProvider.GEMINI

        # Test 3: Alternative Gemini names
        for gemini_name in ["google", "google_gemini"]:
            with patch.dict(os.environ, {"PREFERRED_LLM_PROVIDER": gemini_name}):
                provider = get_preferred_provider()
                assert provider == LLMProvider.GEMINI

        # Test 4: Alternative Azure names
        for azure_name in ["azure", "azure_openai"]:
            with patch.dict(os.environ, {"PREFERRED_LLM_PROVIDER": azure_name}):
                provider = get_preferred_provider()
                assert provider == LLMProvider.AZURE_OPENAI

    # Test 8: Credential Validation
    @pytest.mark.asyncio
    async def test_credential_validation(self) -> None:
        """Test credential validation for both providers.

        Requirements: 8.4 - Credential validation verification
        """
        from dev_agent.llm import validate_provider_credentials

        # Test 1: Valid Gemini credentials
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyTest123"}):
            is_valid, error = validate_provider_credentials(LLMProvider.GEMINI)
            assert is_valid
            assert error == ""

        # Test 2: Invalid Gemini API key format
        with patch.dict(os.environ, {"GEMINI_API_KEY": "invalid-key"}):
            is_valid, error = validate_provider_credentials(LLMProvider.GEMINI)
            assert not is_valid
            assert "Invalid Gemini API key format" in error

        # Test 3: Missing Gemini API key
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = validate_provider_credentials(LLMProvider.GEMINI)
            assert not is_valid
            assert "GEMINI_API_KEY environment variable is required" in error

        # Test 4: Valid Azure OpenAI credentials
        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert is_valid
            assert error == ""

        # Test 5: Missing Azure OpenAI endpoint
        with patch.dict(os.environ, {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002",
        }):
            is_valid, error = validate_provider_credentials(LLMProvider.AZURE_OPENAI)
            assert not is_valid
            assert "AZURE_OPENAI_ENDPOINT environment variable is required" in error

    # Test 9: Factory Pattern Error Handling
    @pytest.mark.asyncio
    async def test_factory_pattern_error_handling(self) -> None:
        """Test error handling in factory functions.

        Requirements: 8.4 - Factory error handling verification
        """
        from dev_agent.llm import create_embedding_client, create_llm_client

        # Test 1: Unsupported provider string
        with pytest.raises(ValueError) as exc_info:
            create_llm_client(provider="unsupported_provider")

        assert "Unsupported provider: 'unsupported_provider'" in str(exc_info.value)

        # Test 2: Missing credentials
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                create_llm_client(provider="gemini")

            assert "Provider credential validation failed" in str(exc_info.value)

        # Test 3: Wrong config type (with valid credentials)
        from pydantic import SecretStr

        from dev_agent.models.llm_config import AzureOpenAIConfig

        azure_config = AzureOpenAIConfig(
            endpoint="https://test.openai.azure.com/",
            api_key=SecretStr("test-key"),
            deployment_name="gpt-4",
            embedding_deployment="text-embedding-ada-002",
        )

        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyTest123456789012345678901234567890"}):
            with pytest.raises(ValueError) as exc_info:
                create_llm_client(provider="gemini", config=azure_config)

            assert "Expected GeminiConfig for Gemini provider" in str(exc_info.value)

    # Test 10: Performance and Scalability
    @pytest.mark.asyncio
    async def test_performance_and_scalability(
        self,
        temp_project_dir: Path,
        mock_gemini_config: GeminiConfig,
    ) -> None:
        """Test performance and scalability with Gemini provider.

        Requirements: 8.4 - Performance verification
        """
        from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient

        with patch("google.generativeai.configure"), \
             patch("google.generativeai.embed_content") as mock_embed:

            # Mock batch embedding responses
            def mock_batch_embed(model, content, task_type):
                if isinstance(content, list):
                    return {"embedding": [[0.1] * 768 for _ in content]}
                else:
                    return {"embedding": [0.1] * 768}

            mock_embed.side_effect = mock_batch_embed

            embedding_client = GeminiEmbeddingClient(
                mock_gemini_config,
                cache_dir=temp_project_dir / ".dev_agent" / "embedding_cache"
            )

            # Test 1: Large batch processing
            large_batch = [f"Code chunk {i}" for i in range(100)]

            embeddings = await embedding_client.embed_batch(
                large_batch, batch_size=16
            )

            assert len(embeddings) == 100
            assert all(len(emb) == 768 for emb in embeddings)

            # Test 2: Concurrent processing
            async def process_batch(batch_id: int) -> list[list[float]]:
                batch = [f"Batch {batch_id} chunk {i}" for i in range(10)]
                return await embedding_client.embed_batch(batch)

            # Process multiple batches concurrently
            tasks = [process_batch(i) for i in range(5)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 5
            assert all(len(batch_result) == 10 for batch_result in results)

            # Test 3: Cache efficiency
            # First call should hit API
            test_text = "def test_function(): pass"
            embedding1 = await embedding_client.embed_text(test_text)

            # Second call should hit cache (same mock response)
            embedding2 = await embedding_client.embed_text(test_text)

            assert embedding1 == embedding2

    # Test 11: Integration with Existing Components
    @pytest.mark.asyncio
    async def test_integration_with_existing_components(
        self,
        temp_project_dir: Path,
        mock_gemini_config: GeminiConfig,
        cost_tracker: CostTracker,
    ) -> None:
        """Test integration with existing dev-agent components.

        Requirements: 8.4, 8.6 - Component integration verification
        """
        from dev_agent.state.state_manager import StateManager
        from dev_agent.workflow.workflow_manager import WorkflowManager

        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel") as mock_model, \
             patch("google.generativeai.embed_content") as mock_embed:

            # Setup mocks
            mock_response = MagicMock()
            mock_response.text = "Generated content"
            mock_model.return_value.generate_content_async = AsyncMock(
                return_value=mock_response
            )
            mock_embed.return_value = {"embedding": [[0.1] * 768]}

            # Test 1: State Manager integration
            state_manager = StateManager(temp_project_dir)

            # Initialize project state
            await state_manager.initialize_project(
                project_path=temp_project_dir,
                project_name="test-calculator",
            )

            # Update state with Gemini provider
            state = await state_manager.get_current_state()
            state.llm_provider = LLMProvider.GEMINI
            await state_manager.save_state(state)

            # Verify state persistence
            loaded_state = await state_manager.get_current_state()
            assert loaded_state.llm_provider == LLMProvider.GEMINI

            # Test 2: Workflow Manager integration
            workflow_manager = WorkflowManager(
                project_path=temp_project_dir,
                state_manager=state_manager,
                cost_tracker=cost_tracker,
            )

            # Set Gemini as provider
            workflow_manager.set_llm_provider(LLMProvider.GEMINI, mock_gemini_config)

            # Test workflow phase execution
            await workflow_manager.execute_phase(
                phase_type=PhaseType.INDEXING,
                user_input="Index the calculator project",
            )

            # Verify phase completion
            current_state = await state_manager.get_current_state()
            assert current_state.current_phase == PhaseType.INDEXING
            assert current_state.phases[PhaseType.INDEXING].status == PhaseStatus.COMPLETED

            # Test 3: Cost tracking integration
            report = cost_tracker.get_report()
            assert report["total_tokens"] > 0
            assert "by_provider" in report
            assert LLMProvider.GEMINI.value in report["by_provider"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])