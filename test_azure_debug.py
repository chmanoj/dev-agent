#!/usr/bin/env python3
"""Debug script for Azure OpenAI connection testing with full error details."""

import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dev_agent.config.config_manager import ConfigManager
from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient


async def test_completion(config):
    """Test chat completion with detailed error reporting."""
    print("\n" + "="*60)
    print("Testing Chat Completion")
    print("="*60)
    
    try:
        print(f"Endpoint: {config.endpoint}")
        print(f"Deployment: {config.deployment_name}")
        print(f"API Version: {config.api_version}")
        print(f"Timeout: {config.timeout}s")
        print()
        
        client = AzureOpenAIClient(config)
        print("✓ Client initialized successfully")
        
        print("Sending test request...")
        response = await client.generate_completion(
            prompt="Say 'test successful' if you can read this.",
            system_prompt="You are a helpful assistant.",
            max_tokens=10,
        )
        
        print(f"✅ SUCCESS: {response}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")
        print("\n" + "-"*60)
        print("FULL STACK TRACE:")
        print("-"*60)
        traceback.print_exc()
        print("-"*60)
        
        # Additional debugging info
        print("\nDEBUGGING INFORMATION:")
        print("-"*60)
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"Caused by: {type(e.__cause__).__name__}: {e.__cause__}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response}")
        if hasattr(e, 'status_code'):
            print(f"Status Code: {e.status_code}")
        print("-"*60)
        
        return False


async def test_embeddings(config):
    """Test embeddings with detailed error reporting."""
    print("\n" + "="*60)
    print("Testing Embeddings")
    print("="*60)
    
    try:
        print(f"Endpoint: {config.endpoint}")
        print(f"Embedding Deployment: {config.embedding_deployment}")
        print(f"API Version: {config.api_version}")
        print()
        
        client = AzureEmbeddingClient(config)
        print("✓ Client initialized successfully")
        
        print("Sending test embedding request...")
        embeddings = await client.embed_batch(texts=["test embedding"])
        
        if embeddings and len(embeddings) > 0:
            dimension = len(embeddings[0])
            print(f"✅ SUCCESS: Generated embedding with dimension {dimension}")
            return True
        else:
            print("❌ FAILED: No embeddings returned")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")
        print("\n" + "-"*60)
        print("FULL STACK TRACE:")
        print("-"*60)
        traceback.print_exc()
        print("-"*60)
        
        # Additional debugging info
        print("\nDEBUGGING INFORMATION:")
        print("-"*60)
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"Caused by: {type(e.__cause__).__name__}: {e.__cause__}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response}")
        if hasattr(e, 'status_code'):
            print(f"Status Code: {e.status_code}")
        print("-"*60)
        
        return False


async def main():
    """Main test function."""
    print("="*60)
    print("Azure OpenAI Connection Debug Test")
    print("="*60)
    
    # Load configuration
    print("\nLoading configuration...")
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        if not config.azure_openai:
            print("❌ ERROR: Azure OpenAI is not configured")
            print("\nSet these environment variables:")
            print("  AZURE_OPENAI_ENDPOINT")
            print("  AZURE_OPENAI_API_KEY or AZURE_OPENAI_TOKEN")
            print("  AZURE_OPENAI_DEPLOYMENT_NAME")
            print("  AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            return
        
        azure_config = config.azure_openai
        azure_config.verify_ssl = False
        print("✓ Configuration loaded successfully")
        
        # Display configuration (without secrets)
        print("\nConfiguration Details:")
        print("-"*60)
        print(f"Endpoint: {azure_config.endpoint}")
        print(f"API Version: {azure_config.api_version}")
        print(f"Deployment: {azure_config.deployment_name}")
        print(f"Embedding Deployment: {azure_config.embedding_deployment}")
        print(f"Timeout: {azure_config.timeout}s")
        print(f"Max Retries: {azure_config.max_retries}")
        
        # Check authentication method
        if azure_config.bearer_token:
            print("Authentication: Azure AD (Bearer Token)")
            if azure_config.user_sid:
                print(f"User SID: {azure_config.user_sid}")
            if azure_config.custom_headers:
                print(f"Custom Headers: {list(azure_config.custom_headers.keys())}")
        else:
            print("Authentication: API Key")
            if azure_config.api_key:
                key_preview = azure_config.api_key.get_secret_value()[:10]
                print(f"API Key: {key_preview}... (truncated)")
        print("-"*60)
        
    except Exception as e:
        print(f"❌ ERROR loading configuration: {e}")
        print("\n" + "-"*60)
        print("FULL STACK TRACE:")
        print("-"*60)
        traceback.print_exc()
        print("-"*60)
        return
    
    # Test completion
    completion_success = await test_completion(azure_config)
    
    # Test embeddings
    embedding_success = await test_embeddings(azure_config)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Chat Completion: {'✅ PASSED' if completion_success else '❌ FAILED'}")
    print(f"Embeddings:      {'✅ PASSED' if embedding_success else '❌ FAILED'}")
    print("="*60)
    
    if completion_success and embedding_success:
        print("\n🎉 All tests passed! Your Azure OpenAI configuration is working.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Review the error details above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
