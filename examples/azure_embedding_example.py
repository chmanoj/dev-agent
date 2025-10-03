"""Example: Azure OpenAI Embeddings and Vector Search

This example demonstrates how to use Azure OpenAI embeddings for semantic
code search and similarity matching.

Requirements:
- Azure OpenAI endpoint and API key configured
- Environment variables set (see below)
- dev-agent installed with Azure OpenAI dependencies
"""

import asyncio
import os
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.llm.embedding_cache import EmbeddingCache
from dev_agent.llm.cost_tracker import CostTracker
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr


def setup_azure_config() -> AzureOpenAIConfig:
    """Set up Azure OpenAI configuration from environment variables.
    
    Returns:
        AzureOpenAIConfig: Validated configuration object
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key-here")
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
    
    return AzureOpenAIConfig(
        endpoint=endpoint,
        api_key=SecretStr(api_key),
        api_version="2024-02-15-preview",
        deployment_name="gpt-4",  # Not used for embeddings
        embedding_deployment=embedding_deployment,
        batch_size=16,  # Batch size for embedding generation
        max_retries=3,
        timeout=60,
    )


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        float: Cosine similarity score (0-1)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    return float(dot_product / (norm1 * norm2))


async def basic_embedding_example():
    """Example: Generate embeddings for text using Azure OpenAI.
    
    This example shows:
    1. Setting up Azure embedding client
    2. Generating embeddings for single text
    3. Understanding embedding dimensions
    4. Tracking costs
    """
    print("=" * 70)
    print("Basic Embedding Generation Example")
    print("=" * 70)
    
    # Step 1: Set up configuration
    print("\n[1/4] Setting up Azure OpenAI configuration...")
    try:
        config = setup_azure_config()
        print(f"✅ Configuration loaded")
        print(f"   Endpoint: {config.endpoint}")
        print(f"   Embedding deployment: {config.embedding_deployment}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Step 2: Initialize embedding client
    print("\n[2/4] Initializing embedding client...")
    cache_dir = Path(".dev_agent/embedding_cache")
    embedding_cache = EmbeddingCache(cache_dir)
    cost_tracker = CostTracker()
    
    embedding_client = AzureEmbeddingClient(
        config=config,
        cache=embedding_cache,
        cost_tracker=cost_tracker,
    )
    
    print(f"✅ Embedding client initialized")
    print(f"   Cache directory: {cache_dir}")
    print(f"   Embedding dimension: {embedding_client.dimension}")
    
    # Step 3: Generate embedding for single text
    print("\n[3/4] Generating embedding for code snippet...")
    
    code_snippet = """
    def calculate_fibonacci(n: int) -> int:
        \"\"\"Calculate the nth Fibonacci number.\"\"\"
        if n <= 1:
            return n
        return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)
    """
    
    print(f"   Code snippet: {len(code_snippet)} characters")
    
    try:
        # Generate embedding
        embedding = await embedding_client.embed_text(code_snippet)
        
        print(f"✅ Embedding generated!")
        print(f"   Dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        print(f"   Vector norm: {np.linalg.norm(embedding):.4f}")
        
        # Check if it was cached
        cache_stats = embedding_cache.get_stats()
        print(f"\n   Cache stats:")
        print(f"   - Hits: {cache_stats.get('hits', 0)}")
        print(f"   - Misses: {cache_stats.get('misses', 0)}")
        
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return
    
    # Step 4: Display cost information
    print("\n[4/4] Cost tracking...")
    report = cost_tracker.get_report()
    print(f"✅ Cost report:")
    print(f"   Embedding tokens: {report.get('embedding_tokens', 0)}")
    print(f"   Total cost: ${report.get('total_cost', 0):.6f}")
    
    print("\n✅ Example completed successfully!")


async def batch_embedding_example():
    """Example: Generate embeddings in batches for efficiency.
    
    This shows how to process multiple texts efficiently using batching.
    """
    print("\n" + "=" * 70)
    print("Batch Embedding Generation Example")
    print("=" * 70)
    
    # Step 1: Setup
    print("\n[1/3] Setting up...")
    try:
        config = setup_azure_config()
        cache_dir = Path(".dev_agent/embedding_cache")
        embedding_cache = EmbeddingCache(cache_dir)
        cost_tracker = CostTracker()
        
        embedding_client = AzureEmbeddingClient(
            config=config,
            cache=embedding_cache,
            cost_tracker=cost_tracker,
        )
        print("✅ Setup complete")
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return
    
    # Step 2: Prepare code chunks
    print("\n[2/3] Preparing code chunks...")
    
    code_chunks = [
        "def add(a: int, b: int) -> int: return a + b",
        "def subtract(a: int, b: int) -> int: return a - b",
        "def multiply(a: int, b: int) -> int: return a * b",
        "def divide(a: int, b: int) -> float: return a / b",
        "class Calculator: pass",
        "import math",
        "from typing import List, Dict",
        "async def fetch_data(): pass",
        "def process_list(items: list[str]) -> list[str]: return items",
        "logger.info('Processing started')",
    ]
    
    print(f"✅ Prepared {len(code_chunks)} code chunks")
    
    # Step 3: Generate embeddings in batch
    print("\n[3/3] Generating embeddings in batch...")
    print(f"   Batch size: {config.batch_size}")
    
    try:
        # Generate embeddings for all chunks
        embeddings = await embedding_client.embed_batch(
            texts=code_chunks,
            batch_size=config.batch_size,
        )
        
        print(f"✅ Generated {len(embeddings)} embeddings!")
        print(f"   Dimension: {len(embeddings[0])}")
        
        # Show cache performance
        cache_stats = embedding_cache.get_stats()
        total_requests = cache_stats.get('hits', 0) + cache_stats.get('misses', 0)
        hit_rate = (cache_stats.get('hits', 0) / total_requests * 100) if total_requests > 0 else 0
        
        print(f"\n   Cache performance:")
        print(f"   - Total requests: {total_requests}")
        print(f"   - Cache hits: {cache_stats.get('hits', 0)}")
        print(f"   - Cache misses: {cache_stats.get('misses', 0)}")
        print(f"   - Hit rate: {hit_rate:.1f}%")
        
        # Cost report
        report = cost_tracker.get_report()
        print(f"\n   Cost report:")
        print(f"   - Embedding tokens: {report.get('embedding_tokens', 0)}")
        print(f"   - Total cost: ${report.get('total_cost', 0):