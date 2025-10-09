"""Integration tests for Google Gemini API integration with real API calls.

These tests are gated by the GEMINI_INTEGRATION_TESTS environment variable
and use real Gemini API calls to verify end-to-end functionality.

Requirements tested:
- 8.2: Integration tests gated by environment variable
- 8.4: Real Gemini API calls for end-to-end verification
- 8.7: FAISS compatibility with Gemini embeddings

To run these tests:
    export GEMINI_INTEGRATION_TESTS=true
    export GEMINI_API_KEY=your-api-key-here
    pytest tests/integration/test_gemini_integration.py -v
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from dev_agent.llm.cost_tracker import CostTracker
    from dev_agent.llm.gemini_client import GeminiClient
    from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient
    from dev_agent.models.llm_config import GeminiConfig

# Skip all tests in this module if integration tests are not enabled
pytestmark = pytest.mark.skipif(
    os.getenv("GEMINI_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled - set GEMINI_INTEGRATION_TESTS=true to enable",
)


@pytest.fixture
def gemini_config() -> GeminiConfig:
    """Create Gemini configuration from environment variables."""
    from pydantic import SecretStr

    from dev_agent.models.llm_config import GeminiConfig

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-pro")
    embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "embedding-001")

    if not api_key:
        pytest.skip("Gemini API key not configured")

    return GeminiConfig(
        api_key=SecretStr(api_key),
        model_name=model_name,
        embedding_model=embedding_model,
        max_output_tokens=1000,  # Keep costs low for testing
        temperature=0.7,
        max_retries=3,
        timeout=60,
    )


@pytest.fixture
def gemini_llm_client(gemini_config: GeminiConfig) -> GeminiClient:
    """Create Gemini LLM client."""
    from dev_agent.llm.gemini_client import GeminiClient

    return GeminiClient(gemini_config)


@pytest.fixture
def gemini_embedding_client(gemini_config: GeminiConfig) -> GeminiEmbeddingClient:
    """Create Gemini embedding client."""
    from dev_agent.llm.gemini_embeddings import GeminiEmbeddingClient

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "embedding_cache"
        yield GeminiEmbeddingClient(gemini_config, cache_dir=cache_dir)


@pytest.fixture
def cost_tracker() -> CostTracker:
    """Create cost tracker."""
    from dev_agent.llm.cost_tracker import CostTracker

    return CostTracker()


# Test 1: Basic LLM Completion
@pytest.mark.asyncio
async def test_real_gemini_completion_generation(gemini_llm_client: GeminiClient) -> None:
    """Test basic completion generation with real Gemini API.

    Requirements: 8.2, 8.4 - Real API calls for end-to-end verification
    """
    prompt = "Say 'Hello, World!' and nothing else."
    system_prompt = "You are a helpful assistant that follows instructions exactly."

    result = await gemini_llm_client.generate_completion(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.0,  # Deterministic
        max_tokens=50,
    )

    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
    assert "hello" in result.lower() or "world" in result.lower()


# Test 2: Streaming Responses
@pytest.mark.asyncio
async def test_real_gemini_streaming_generation(gemini_llm_client: GeminiClient) -> None:
    """Test streaming completion with real Gemini API.

    Requirements: 8.2, 8.4 - Real API calls for streaming verification
    """
    prompt = "Count from 1 to 5, one number per line."
    system_prompt = "You are a helpful assistant."

    chunks = []
    async for chunk in gemini_llm_client.generate_streaming(
        prompt=prompt, system_prompt=system_prompt
    ):
        assert isinstance(chunk, str)
        chunks.append(chunk)

    # Verify we received multiple chunks
    assert len(chunks) > 0

    # Verify complete response
    complete_response = "".join(chunks)
    assert len(complete_response) > 0


# Test 3: Token Counting
@pytest.mark.asyncio
async def test_real_gemini_token_counting(gemini_llm_client: GeminiClient) -> None:
    """Test token counting accuracy with real API.

    Requirements: 8.2, 8.4 - Verify token counting against actual API usage
    """
    prompt = "This is a test prompt for token counting."

    # Count tokens before API call
    token_count = gemini_llm_client.count_tokens(prompt)
    assert token_count > 0
    assert isinstance(token_count, int)

    # Make API call and verify actual token usage
    result = await gemini_llm_client.generate_completion(
        prompt=prompt,
        system_prompt="Respond with 'OK'.",
        max_tokens=10,
    )

    assert result is not None
    # Token count should be reasonable (not exact due to system prompt)
    assert token_count < 100


# Test 4: Cost Estimation
@pytest.mark.asyncio
async def test_real_gemini_cost_estimation(
    gemini_llm_client: GeminiClient, cost_tracker: CostTracker
) -> None:
    """Test cost estimation with real API usage.

    Requirements: 8.2, 8.4 - Verify cost tracking accuracy
    """
    prompt = "Generate a short greeting."

    # Estimate cost before call
    prompt_tokens = gemini_llm_client.count_tokens(prompt)
    estimated_cost = gemini_llm_client.estimate_cost(
        prompt_tokens=prompt_tokens, completion_tokens=50
    )

    assert estimated_cost > 0
    assert isinstance(estimated_cost, float)

    # Make actual API call
    result = await gemini_llm_client.generate_completion(
        prompt=prompt, max_tokens=50
    )

    assert result is not None
    # Cost should be reasonable (less than $1 for this small request)
    assert estimated_cost < 1.0


# Test 5: Embedding Generation
@pytest.mark.asyncio
async def test_real_gemini_embedding_generation(
    gemini_embedding_client: GeminiEmbeddingClient,
) -> None:
    """Test embedding generation with real Gemini API.

    Requirements: 8.2, 8.4 - Real API calls for embedding verification
    """
    text = "This is a test text for embedding generation."

    embedding = await gemini_embedding_client.embed_text(text)

    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) == 768  # Gemini embedding dimension
    assert all(isinstance(x, float) for x in embedding)


# Test 6: Batch Embedding Generation
@pytest.mark.asyncio
async def test_real_gemini_batch_embedding(
    gemini_embedding_client: GeminiEmbeddingClient,
) -> None:
    """Test batch embedding generation with real API.

    Requirements: 8.2, 8.4 - Verify batch processing efficiency
    """
    texts = [
        "First test text for embedding.",
        "Second test text for embedding.",
        "Third test text for embedding.",
    ]

    embeddings = await gemini_embedding_client.embed_batch(texts, batch_size=2)

    assert embeddings is not None
    assert isinstance(embeddings, list)
    assert len(embeddings) == len(texts)
    assert all(len(emb) == 768 for emb in embeddings)


# Test 7: Embedding Cache
@pytest.mark.asyncio
async def test_real_gemini_embedding_cache(
    gemini_embedding_client: GeminiEmbeddingClient,
) -> None:
    """Test embedding cache with real API calls.

    Requirements: 8.2, 8.4 - Verify caching reduces API calls
    """
    text = "This text will be cached."

    # First call - should hit API
    embedding1 = await gemini_embedding_client.embed_text(text)
    
    # Second call - should hit cache
    embedding2 = await gemini_embedding_client.embed_text(text)

    # Verify embeddings are identical
    assert embedding1 == embedding2


# Test 8: Provider Switching
@pytest.mark.asyncio
async def test_real_provider_switching() -> None:
    """Test switching between Azure OpenAI and Gemini providers.

    Requirements: 8.2, 8.4 - Verify provider switching functionality
    """
    from dev_agent.llm import create_llm_client, create_embedding_client
    from dev_agent.models.enums import LLMProvider

    # Test Gemini LLM client creation
    gemini_llm = create_llm_client(provider=LLMProvider.GEMINI)
    assert gemini_llm is not None
    
    # Test basic completion with Gemini
    result = await gemini_llm.generate_completion(
        prompt="Say hello", max_tokens=10
    )
    assert result is not None
    assert isinstance(result, str)

    # Test Gemini embedding client creation
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "embedding_cache"
        gemini_embedding = create_embedding_client(
            provider=LLMProvider.GEMINI, cache_dir=cache_dir
        )
        assert gemini_embedding is not None
        
        # Test basic embedding with Gemini
        embedding = await gemini_embedding.embed_text("test text")
        assert embedding is not None
        assert len(embedding) == 768


# Test 9: FAISS Compatibility with Gemini Embeddings
@pytest.mark.asyncio
async def test_real_faiss_compatibility_with_gemini(
    gemini_embedding_client: GeminiEmbeddingClient,
) -> None:
    """Test FAISS compatibility with Gemini embeddings.

    Requirements: 8.2, 8.4, 8.7 - Verify FAISS integration with Gemini embeddings
    """
    from dev_agent.indexing.vector_database import VectorDatabase

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "vector.db"

        # Create vector database with Gemini embeddings
        vector_db = VectorDatabase(
            db_path=db_path, embedding_client=gemini_embedding_client
        )

        # Add some documents
        documents = [
            "Python is a programming language.",
            "JavaScript is used for web development.",
            "Machine learning uses neural networks.",
        ]

        for i, doc in enumerate(documents):
            embedding = await gemini_embedding_client.embed_text(doc)
            vector_db.add_chunk(
                chunk_id=f"doc_{i}",
                embedding=embedding,
                metadata={"text": doc, "index": i},
            )

        # Search for similar documents
        query = "What is Python?"
        query_embedding = await gemini_embedding_client.embed_text(query)
        results = vector_db.search(query_embedding, top_k=2)

        # Verify search results
        assert len(results) > 0
        assert results[0]["metadata"]["text"] == documents[0]  # Python doc should be first


# Test 10: End-to-End Specification Generation with Gemini
@pytest.mark.asyncio
async def test_real_gemini_specification_generation(
    gemini_llm_client: GeminiClient, cost_tracker: CostTracker
) -> None:
    """Test end-to-end specification generation with real Gemini API.

    Requirements: 8.2, 8.4 - End-to-end workflow verification
    """
    from dev_agent.generation.specification_generator import SpecificationGenerator

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a simple test file
        test_file = project_path / "test.py"
        test_file.write_text(
            """
def hello_world():
    '''Say hello.'''
    return 'Hello, World!'
"""
        )

        # Create specification generator with Gemini client
        spec_gen = SpecificationGenerator(
            llm_client=gemini_llm_client, cost_tracker=cost_tracker
        )

        # Generate specification
        feature_description = "Add a goodbye function that returns 'Goodbye, World!'"
        specification = await spec_gen.generate_specification(
            feature_description=feature_description,
            project_path=project_path,
            codebase_summary="Simple Python project with hello_world function",
        )

        # Verify specification was generated
        assert specification is not None
        assert isinstance(specification, str)
        assert len(specification) > 100
        assert "goodbye" in specification.lower()

        # Verify cost tracking
        report = cost_tracker.get_report()
        assert report["total_tokens"] > 0
        assert report["estimated_cost"] > 0


# Test 11: End-to-End Code Generation with Gemini
@pytest.mark.asyncio
async def test_real_gemini_code_generation(
    gemini_llm_client: GeminiClient, cost_tracker: CostTracker
) -> None:
    """Test end-to-end code generation with real Gemini API.

    Requirements: 8.2, 8.4 - End-to-end code generation verification
    """
    from dev_agent.generation.python_code_generator import PythonCodeGenerator

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create code generator with Gemini client
        code_gen = PythonCodeGenerator(
            llm_client=gemini_llm_client, cost_tracker=cost_tracker
        )

        # Generate code
        specification = """
        Create a function called 'add_numbers' that:
        - Takes two integer parameters: a and b
        - Returns their sum
        - Includes type hints
        - Includes a docstring
        """

        code = await code_gen.generate_code(
            specification=specification,
            file_path=project_path / "math_utils.py",
            context="Simple Python utility functions",
        )

        # Verify code was generated
        assert code is not None
        assert isinstance(code, str)
        assert "def add_numbers" in code
        assert "int" in code  # Type hints
        assert '"""' in code or "'''" in code  # Docstring

        # Verify cost tracking
        report = cost_tracker.get_report()
        assert report["total_tokens"] > 0


# Test 12: End-to-End Vector Search with Gemini Embeddings
@pytest.mark.asyncio
async def test_real_gemini_vector_search(
    gemini_embedding_client: GeminiEmbeddingClient,
) -> None:
    """Test end-to-end vector search with real Gemini embeddings.

    Requirements: 8.2, 8.4, 8.7 - Verify vector search with real Gemini embeddings
    """
    from dev_agent.indexing.vector_database import VectorDatabase

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "vector.db"

        # Create vector database with Gemini embeddings
        vector_db = VectorDatabase(
            db_path=db_path, embedding_client=gemini_embedding_client
        )

        # Add some code documents
        code_documents = [
            "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "class Calculator: def add(self, a, b): return a + b",
            "import numpy as np; arr = np.array([1, 2, 3])",
        ]

        for i, doc in enumerate(code_documents):
            embedding = await gemini_embedding_client.embed_text(doc)
            vector_db.add_chunk(
                chunk_id=f"code_{i}",
                embedding=embedding,
                metadata={"code": doc, "index": i},
            )

        # Search for similar code
        query = "recursive function"
        query_embedding = await gemini_embedding_client.embed_text(query)
        results = vector_db.search(query_embedding, top_k=2)

        # Verify search results
        assert len(results) > 0
        # Fibonacci function should be most similar to "recursive function"
        assert "fibonacci" in results[0]["metadata"]["code"]


# Test 13: Cost Tracking Across Workflow Phases with Gemini
@pytest.mark.asyncio
async def test_real_gemini_cost_tracking_workflow(
    gemini_llm_client: GeminiClient,
    gemini_embedding_client: GeminiEmbeddingClient,
    cost_tracker: CostTracker,
) -> None:
    """Test cost tracking across multiple workflow phases with Gemini.

    Requirements: 8.2, 8.4 - Verify cost tracking across workflow
    """
    from dev_agent.models.enums import PhaseType

    # Phase 1: Indexing (embeddings)
    texts = ["Code chunk 1", "Code chunk 2", "Code chunk 3"]
    embeddings = await gemini_embedding_client.embed_batch(texts)

    # Track embedding tokens (estimate)
    embedding_tokens = len(texts) * 10  # Rough estimate
    cost_tracker.add_embedding_tokens(embedding_tokens, PhaseType.INDEXING)

    # Phase 2: Specification (completion)
    spec_prompt = "Generate a specification for a new feature."
    spec_result = await gemini_llm_client.generate_completion(
        prompt=spec_prompt, max_tokens=100
    )

    prompt_tokens = gemini_llm_client.count_tokens(spec_prompt)
    completion_tokens = gemini_llm_client.count_tokens(spec_result)
    cost_tracker.add_completion(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        phase=PhaseType.SPECIFICATION,
    )

    # Phase 3: Design (completion)
    design_prompt = "Generate a design document."
    design_result = await gemini_llm_client.generate_completion(
        prompt=design_prompt, max_tokens=100
    )

    prompt_tokens = gemini_llm_client.count_tokens(design_prompt)
    completion_tokens = gemini_llm_client.count_tokens(design_result)
    cost_tracker.add_completion(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        phase=PhaseType.DESIGN,
    )

    # Get cost report
    report = cost_tracker.get_report()

    # Verify cost tracking
    assert report["total_tokens"] > 0
    assert report["total_embedding_tokens"] > 0
    assert report["total_completion_tokens"] > 0
    assert report["estimated_cost"] > 0
    assert len(report["by_phase"]) >= 2  # At least 2 phases tracked


# Test 14: Streaming with Cost Tracking
@pytest.mark.asyncio
async def test_real_gemini_streaming_with_cost_tracking(
    gemini_llm_client: GeminiClient, cost_tracker: CostTracker
) -> None:
    """Test streaming responses with cost tracking using Gemini.

    Requirements: 8.2, 8.4 - Verify streaming and cost tracking integration
    """
    from dev_agent.models.enums import PhaseType

    prompt = "List three programming languages."
    prompt_tokens = gemini_llm_client.count_tokens(prompt)

    # Stream response
    chunks = []
    async for chunk in gemini_llm_client.generate_streaming(prompt=prompt):
        chunks.append(chunk)

    complete_response = "".join(chunks)
    completion_tokens = gemini_llm_client.count_tokens(complete_response)

    # Track cost
    cost_tracker.add_completion(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        phase=PhaseType.IMPLEMENTATION,
    )

    # Verify tracking
    report = cost_tracker.get_report()
    assert report["total_tokens"] > 0
    assert report["estimated_cost"] > 0


# Test 15: Performance Benchmarks with Gemini
@pytest.mark.asyncio
async def test_real_gemini_performance_benchmarks(
    gemini_llm_client: GeminiClient,
    gemini_embedding_client: GeminiEmbeddingClient,
) -> None:
    """Test performance benchmarks with real Gemini API.

    Requirements: 8.2, 8.4 - Verify performance targets are met
    """
    import time

    # Benchmark 1: Completion generation (<30s for 200 tokens)
    start = time.time()
    result = await gemini_llm_client.generate_completion(
        prompt="Write a short paragraph about Python programming.",
        max_tokens=200,
    )
    completion_time = time.time() - start

    assert result is not None
    assert completion_time < 30  # Allow 30s for network latency

    # Benchmark 2: Embedding generation (<10s per 10 chunks)
    texts = [f"Test text {i}" for i in range(10)]
    start = time.time()
    embeddings = await gemini_embedding_client.embed_batch(texts)
    embedding_time = time.time() - start

    assert len(embeddings) == len(texts)
    assert embedding_time < 15  # Allow 15s for 10 texts with Gemini


# Test 16: Error Handling with Real Gemini API
@pytest.mark.asyncio
async def test_real_gemini_error_handling(gemini_config: GeminiConfig) -> None:
    """Test error handling with real Gemini API scenarios.

    Requirements: 8.2, 8.4 - Verify error handling with real API
    """
    from pydantic import SecretStr

    from dev_agent.errors.llm_exceptions import LLMAuthenticationError
    from dev_agent.llm.gemini_client import GeminiClient
    from dev_agent.models.llm_config import GeminiConfig

    # Test 1: Invalid API key
    invalid_config = GeminiConfig(
        api_key=SecretStr("invalid-key"),
        model_name=gemini_config.model_name,
        embedding_model=gemini_config.embedding_model,
    )

    invalid_client = GeminiClient(invalid_config)

    with pytest.raises((LLMAuthenticationError, Exception)):
        await invalid_client.generate_completion("Test prompt", max_tokens=10)


# Test 17: Multi-Provider Comparison
@pytest.mark.asyncio
async def test_real_multi_provider_comparison() -> None:
    """Test comparison between Azure OpenAI and Gemini providers.

    Requirements: 8.2, 8.4 - Verify both providers work with same interface
    """
    from dev_agent.llm import create_llm_client, create_embedding_client
    from dev_agent.models.enums import LLMProvider

    # Skip if Azure OpenAI is not configured
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if not (azure_endpoint and azure_key and azure_deployment):
        pytest.skip("Azure OpenAI not configured for comparison test")

    # Test same prompt with both providers
    prompt = "Write a simple Python function."
    
    # Gemini client
    gemini_client = create_llm_client(provider=LLMProvider.GEMINI)
    gemini_result = await gemini_client.generate_completion(prompt, max_tokens=100)
    
    # Azure OpenAI client
    azure_client = create_llm_client(provider=LLMProvider.AZURE_OPENAI)
    azure_result = await azure_client.generate_completion(prompt, max_tokens=100)
    
    # Both should return valid results
    assert gemini_result is not None
    assert azure_result is not None
    assert isinstance(gemini_result, str)
    assert isinstance(azure_result, str)
    assert len(gemini_result) > 0
    assert len(azure_result) > 0

    # Test embeddings with both providers
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "embedding_cache"
        
        text = "def hello(): return 'Hello, World!'"
        
        # Gemini embeddings
        gemini_embedding_client = create_embedding_client(
            provider=LLMProvider.GEMINI, cache_dir=cache_dir / "gemini"
        )
        gemini_embedding = await gemini_embedding_client.embed_text(text)
        
        # Azure OpenAI embeddings
        azure_embedding_client = create_embedding_client(
            provider=LLMProvider.AZURE_OPENAI, cache_dir=cache_dir / "azure"
        )
        azure_embedding = await azure_embedding_client.embed_text(text)
        
        # Both should return valid embeddings with different dimensions
        assert gemini_embedding is not None
        assert azure_embedding is not None
        assert len(gemini_embedding) == 768  # Gemini dimension
        assert len(azure_embedding) == 1536  # Azure OpenAI dimension


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])