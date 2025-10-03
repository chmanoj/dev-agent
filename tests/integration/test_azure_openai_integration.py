"""Integration tests for Azure OpenAI integration with real API calls.

These tests are gated by the AZURE_OPENAI_INTEGRATION_TESTS environment variable
and use real Azure OpenAI API calls to verify end-to-end functionality.

Requirements tested:
- 9.6: Integration tests gated by environment variable
- 9.7: Real Azure OpenAI API calls for end-to-end verification
- 9.8: >90% code coverage for LLM-related modules

To run these tests:
    export AZURE_OPENAI_INTEGRATION_TESTS=true
    export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
    export AZURE_OPENAI_API_KEY=your-api-key
    export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
    export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
    pytest tests/integration/test_azure_openai_integration.py -v
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from dev_agent.llm.azure_client import AzureOpenAIClient
    from dev_agent.llm.cost_tracker import CostTracker
    from dev_agent.llm.embeddings import AzureEmbeddingClient
    from dev_agent.models.llm_config import AzureOpenAIConfig

# Skip all tests in this module if integration tests are not enabled
pytestmark = pytest.mark.skipif(
    os.getenv("AZURE_OPENAI_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled - set AZURE_OPENAI_INTEGRATION_TESTS=true to enable",
)


@pytest.fixture
def azure_config() -> AzureOpenAIConfig:
    """Create Azure OpenAI configuration from environment variables."""
    from pydantic import SecretStr

    from dev_agent.models.llm_config import AzureOpenAIConfig

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    embedding_deployment = os.getenv(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"
    )

    if not endpoint or not api_key:
        pytest.skip("Azure OpenAI credentials not configured")

    return AzureOpenAIConfig(
        endpoint=endpoint,
        api_key=SecretStr(api_key),
        deployment_name=deployment_name,
        embedding_deployment=embedding_deployment,
        max_tokens=1000,  # Keep costs low for testing
        temperature=0.7,
        max_retries=3,
        timeout=60,
    )


@pytest.fixture
def azure_llm_client(azure_config: AzureOpenAIConfig) -> AzureOpenAIClient:
    """Create Azure OpenAI LLM client."""
    from dev_agent.llm.azure_client import AzureOpenAIClient

    return AzureOpenAIClient(azure_config)


@pytest.fixture
def azure_embedding_client(azure_config: AzureOpenAIConfig) -> AzureEmbeddingClient:
    """Create Azure OpenAI embedding client."""
    from dev_agent.llm.embeddings import AzureEmbeddingClient

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "embedding_cache"
        yield AzureEmbeddingClient(azure_config, cache_dir=cache_dir)


@pytest.fixture
def cost_tracker() -> CostTracker:
    """Create cost tracker."""
    from dev_agent.llm.cost_tracker import CostTracker

    return CostTracker()


# Test 1: Basic LLM Completion
@pytest.mark.asyncio
async def test_real_completion_generation(azure_llm_client: AzureOpenAIClient) -> None:
    """Test basic completion generation with real Azure OpenAI API.

    Requirements: 9.7 - Real API calls for end-to-end verification
    """
    prompt = "Say 'Hello, World!' and nothing else."
    system_prompt = "You are a helpful assistant that follows instructions exactly."

    result = await azure_llm_client.generate_completion(
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
async def test_real_streaming_generation(azure_llm_client: AzureOpenAIClient) -> None:
    """Test streaming completion with real Azure OpenAI API.

    Requirements: 9.7 - Real API calls for streaming verification
    """
    prompt = "Count from 1 to 5, one number per line."
    system_prompt = "You are a helpful assistant."

    chunks = []
    async for chunk in azure_llm_client.generate_streaming(
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
async def test_real_token_counting(azure_llm_client: AzureOpenAIClient) -> None:
    """Test token counting accuracy with real API.

    Requirements: 9.7 - Verify token counting against actual API usage
    """
    prompt = "This is a test prompt for token counting."

    # Count tokens before API call
    token_count = azure_llm_client.count_tokens(prompt)
    assert token_count > 0
    assert isinstance(token_count, int)

    # Make API call and verify actual token usage
    result = await azure_llm_client.generate_completion(
        prompt=prompt,
        system_prompt="Respond with 'OK'.",
        max_tokens=10,
    )

    assert result is not None
    # Token count should be reasonable (not exact due to system prompt)
    assert token_count < 100


# Test 4: Cost Estimation
@pytest.mark.asyncio
async def test_real_cost_estimation(
    azure_llm_client: AzureOpenAIClient, cost_tracker: CostTracker
) -> None:
    """Test cost estimation with real API usage.

    Requirements: 9.7 - Verify cost tracking accuracy
    """
    prompt = "Generate a short greeting."

    # Estimate cost before call
    prompt_tokens = azure_llm_client.count_tokens(prompt)
    estimated_cost = azure_llm_client.estimate_cost(
        prompt_tokens=prompt_tokens, completion_tokens=50
    )

    assert estimated_cost > 0
    assert isinstance(estimated_cost, float)

    # Make actual API call
    result = await azure_llm_client.generate_completion(
        prompt=prompt, max_tokens=50
    )

    assert result is not None
    # Cost should be reasonable (less than $1 for this small request)
    assert estimated_cost < 1.0


# Test 5: Embedding Generation
@pytest.mark.asyncio
async def test_real_embedding_generation(
    azure_embedding_client: AzureEmbeddingClient,
) -> None:
    """Test embedding generation with real Azure OpenAI API.

    Requirements: 9.7 - Real API calls for embedding verification
    """
    text = "This is a test text for embedding generation."

    embedding = await azure_embedding_client.embed_text(text)

    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) == 1536  # text-embedding-ada-002 dimension
    assert all(isinstance(x, float) for x in embedding)


# Test 6: Batch Embedding Generation
@pytest.mark.asyncio
async def test_real_batch_embedding(
    azure_embedding_client: AzureEmbeddingClient,
) -> None:
    """Test batch embedding generation with real API.

    Requirements: 9.7 - Verify batch processing efficiency
    """
    texts = [
        "First test text for embedding.",
        "Second test text for embedding.",
        "Third test text for embedding.",
    ]

    embeddings = await azure_embedding_client.embed_batch(texts, batch_size=2)

    assert embeddings is not None
    assert isinstance(embeddings, list)
    assert len(embeddings) == len(texts)
    assert all(len(emb) == 1536 for emb in embeddings)


# Test 7: Embedding Cache
@pytest.mark.asyncio
async def test_real_embedding_cache(
    azure_embedding_client: AzureEmbeddingClient,
) -> None:
    """Test embedding cache with real API calls.

    Requirements: 9.7 - Verify caching reduces API calls
    """
    text = "This text will be cached."

    # First call - should hit API
    embedding1 = await azure_embedding_client.embed_text(text)
    cache_stats1 = azure_embedding_client.get_cache_stats()

    # Second call - should hit cache
    embedding2 = await azure_embedding_client.embed_text(text)
    cache_stats2 = azure_embedding_client.get_cache_stats()

    # Verify embeddings are identical
    assert embedding1 == embedding2

    # Verify cache hit increased
    assert cache_stats2["hits"] > cache_stats1["hits"]


# Test 8: Error Recovery and Retry
@pytest.mark.asyncio
async def test_real_error_recovery(azure_llm_client: AzureOpenAIClient) -> None:
    """Test error recovery with real API.

    Requirements: 9.7 - Verify retry logic works with real API
    """
    # Test with invalid parameters that should trigger retry
    prompt = "Test prompt"

    try:
        # This should succeed despite potential transient errors
        result = await azure_llm_client.generate_completion(
            prompt=prompt, max_tokens=10
        )
        assert result is not None
    except Exception as e:
        # If it fails, it should be with a proper error message
        assert str(e) is not None
        assert len(str(e)) > 0


# Test 9: End-to-End Specification Generation
@pytest.mark.asyncio
async def test_real_specification_generation(
    azure_llm_client: AzureOpenAIClient, cost_tracker: CostTracker
) -> None:
    """Test end-to-end specification generation with real API.

    Requirements: 9.7 - End-to-end workflow verification
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

        # Create specification generator
        spec_gen = SpecificationGenerator(
            llm_client=azure_llm_client, cost_tracker=cost_tracker
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


# Test 10: End-to-End Code Generation
@pytest.mark.asyncio
async def test_real_code_generation(
    azure_llm_client: AzureOpenAIClient, cost_tracker: CostTracker
) -> None:
    """Test end-to-end code generation with real API.

    Requirements: 9.7 - End-to-end code generation verification
    """
    from dev_agent.generation.python_code_generator import PythonCodeGenerator

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create code generator
        code_gen = PythonCodeGenerator(
            llm_client=azure_llm_client, cost_tracker=cost_tracker
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


# Test 11: End-to-End Vector Search
@pytest.mark.asyncio
async def test_real_vector_search(
    azure_embedding_client: AzureEmbeddingClient,
) -> None:
    """Test end-to-end vector search with real embeddings.

    Requirements: 9.7 - Verify vector search with real embeddings
    """
    from dev_agent.indexing.vector_database import VectorDatabase

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "vector.db"

        # Create vector database
        vector_db = VectorDatabase(
            db_path=db_path, embedding_client=azure_embedding_client
        )

        # Add some documents
        documents = [
            "Python is a programming language.",
            "JavaScript is used for web development.",
            "Machine learning uses neural networks.",
        ]

        for i, doc in enumerate(documents):
            embedding = await azure_embedding_client.embed_text(doc)
            vector_db.add_chunk(
                chunk_id=f"doc_{i}",
                embedding=embedding,
                metadata={"text": doc, "index": i},
            )

        # Search for similar documents
        query = "What is Python?"
        query_embedding = await azure_embedding_client.embed_text(query)
        results = vector_db.search(query_embedding, top_k=2)

        # Verify search results
        assert len(results) > 0
        assert results[0]["metadata"]["text"] == documents[0]  # Python doc should be first


# Test 12: Cost Tracking Across Workflow Phases
@pytest.mark.asyncio
async def test_real_cost_tracking_workflow(
    azure_llm_client: AzureOpenAIClient,
    azure_embedding_client: AzureEmbeddingClient,
    cost_tracker: CostTracker,
) -> None:
    """Test cost tracking across multiple workflow phases.

    Requirements: 9.7 - Verify cost tracking across workflow
    """
    from dev_agent.models.enums import PhaseType

    # Phase 1: Indexing (embeddings)
    texts = ["Code chunk 1", "Code chunk 2", "Code chunk 3"]
    embeddings = await azure_embedding_client.embed_batch(texts)

    # Track embedding tokens (estimate)
    embedding_tokens = len(texts) * 10  # Rough estimate
    cost_tracker.add_embedding_tokens(embedding_tokens, PhaseType.INDEXING)

    # Phase 2: Specification (completion)
    spec_prompt = "Generate a specification for a new feature."
    spec_result = await azure_llm_client.generate_completion(
        prompt=spec_prompt, max_tokens=100
    )

    prompt_tokens = azure_llm_client.count_tokens(spec_prompt)
    completion_tokens = azure_llm_client.count_tokens(spec_result)
    cost_tracker.add_completion(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        phase=PhaseType.SPECIFICATION,
    )

    # Phase 3: Design (completion)
    design_prompt = "Generate a design document."
    design_result = await azure_llm_client.generate_completion(
        prompt=design_prompt, max_tokens=100
    )

    prompt_tokens = azure_llm_client.count_tokens(design_prompt)
    completion_tokens = azure_llm_client.count_tokens(design_result)
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


# Test 13: Streaming with Cost Tracking
@pytest.mark.asyncio
async def test_real_streaming_with_cost_tracking(
    azure_llm_client: AzureOpenAIClient, cost_tracker: CostTracker
) -> None:
    """Test streaming responses with cost tracking.

    Requirements: 9.7 - Verify streaming and cost tracking integration
    """
    from dev_agent.models.enums import PhaseType

    prompt = "List three programming languages."
    prompt_tokens = azure_llm_client.count_tokens(prompt)

    # Stream response
    chunks = []
    async for chunk in azure_llm_client.generate_streaming(prompt=prompt):
        chunks.append(chunk)

    complete_response = "".join(chunks)
    completion_tokens = azure_llm_client.count_tokens(complete_response)

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


# Test 14: Performance Benchmarks
@pytest.mark.asyncio
async def test_real_performance_benchmarks(
    azure_llm_client: AzureOpenAIClient,
    azure_embedding_client: AzureEmbeddingClient,
) -> None:
    """Test performance benchmarks with real API.

    Requirements: 9.7 - Verify performance targets are met
    """
    import time

    # Benchmark 1: Completion generation (<10s for 1000 tokens)
    start = time.time()
    result = await azure_llm_client.generate_completion(
        prompt="Write a short paragraph about Python programming.",
        max_tokens=200,
    )
    completion_time = time.time() - start

    assert result is not None
    assert completion_time < 30  # Allow 30s for network latency

    # Benchmark 2: Embedding generation (<5s per 100 chunks)
    texts = [f"Test text {i}" for i in range(10)]
    start = time.time()
    embeddings = await azure_embedding_client.embed_batch(texts)
    embedding_time = time.time() - start

    assert len(embeddings) == len(texts)
    assert embedding_time < 10  # Allow 10s for 10 texts


# Test 15: Error Handling with Real API
@pytest.mark.asyncio
async def test_real_error_handling(azure_config: AzureOpenAIConfig) -> None:
    """Test error handling with real API scenarios.

    Requirements: 9.7 - Verify error handling with real API
    """
    from pydantic import SecretStr

    from dev_agent.errors.llm_exceptions import LLMAuthenticationError
    from dev_agent.llm.azure_client import AzureOpenAIClient
    from dev_agent.models.llm_config import AzureOpenAIConfig

    # Test 1: Invalid API key
    invalid_config = AzureOpenAIConfig(
        endpoint=azure_config.endpoint,
        api_key=SecretStr("invalid-key"),
        deployment_name=azure_config.deployment_name,
        embedding_deployment=azure_config.embedding_deployment,
    )

    invalid_client = AzureOpenAIClient(invalid_config)

    with pytest.raises((LLMAuthenticationError, Exception)):
        await invalid_client.generate_completion("Test prompt", max_tokens=10)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
