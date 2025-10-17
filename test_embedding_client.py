#!/usr/bin/env python3
"""Test script to verify embedding client functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_embedding_client():
    """Test the embedding client with current configuration."""
    try:
        # Import the factory function
        from dev_agent.llm import create_embedding_client, get_preferred_provider
        
        print("Testing embedding client...")
        
        # Get preferred provider
        provider = get_preferred_provider()
        print(f"Preferred provider: {provider}")
        
        # Create embedding client
        embedding_client = create_embedding_client(provider=provider)
        print(f"Created embedding client: {type(embedding_client)}")
        print(f"Embedding dimension: {embedding_client.dimension}")
        
        # Test embedding generation
        test_texts = [
            "def hello_world():\n    return 'Hello, World!'",
            "import streamlit as st\nst.title('Test App')",
            "class TestClass:\n    def __init__(self):\n        pass"
        ]
        
        print(f"Testing embedding generation with {len(test_texts)} texts...")
        embeddings = await embedding_client.embed_batch(test_texts)
        
        print(f"Successfully generated {len(embeddings)} embeddings")
        print(f"First embedding shape: {len(embeddings[0]) if embeddings else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"Error testing embedding client: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load environment variables from gemini.export.txt
    env_file = Path("gemini.export.txt")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    key_value = line[7:]  # Remove "export "
                    if "=" in key_value:
                        key, value = key_value.split("=", 1)
                        os.environ[key] = value
                        print(f"Set {key}={value}")
    
    # Run the test
    success = asyncio.run(test_embedding_client())
    sys.exit(0 if success else 1)