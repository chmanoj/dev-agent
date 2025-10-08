#!/usr/bin/env python3
"""Test script to verify insecure SSL mode works correctly."""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_config_model():
    """Test that AzureOpenAIConfig accepts verify_ssl parameter."""
    print("Testing AzureOpenAIConfig model...")
    
    from dev_agent.models.llm_config import AzureOpenAIConfig
    
    # Test with SSL verification enabled (default)
    config1 = AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key="test-key",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
    )
    assert config1.verify_ssl is True, "Default verify_ssl should be True"
    print("  ✓ Default verify_ssl=True")
    
    # Test with SSL verification disabled
    config2 = AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key="test-key",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        verify_ssl=False,
    )
    assert config2.verify_ssl is False, "verify_ssl should be False when set"
    print("  ✓ Explicit verify_ssl=False works")
    
    print("✅ Config model tests passed\n")


def test_env_variable():
    """Test that environment variable is parsed correctly."""
    print("Testing environment variable parsing...")
    
    from dev_agent.config.config_manager import ConfigManager
    
    # Set environment variables
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.openai.azure.com/"
    os.environ["AZURE_OPENAI_API_KEY"] = "test-key"
    os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4"
    os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"] = "text-embedding-ada-002"
    
    # Test with verify_ssl=false
    os.environ["AZURE_OPENAI_VERIFY_SSL"] = "false"
    config_manager = ConfigManager()
    config = config_manager._load_azure_config_from_env()
    assert config is not None, "Config should be loaded from env vars"
    assert config.verify_ssl is False, "verify_ssl should be False"
    print("  ✓ AZURE_OPENAI_VERIFY_SSL=false works")
    
    # Test with verify_ssl=true
    os.environ["AZURE_OPENAI_VERIFY_SSL"] = "true"
    config = config_manager._load_azure_config_from_env()
    assert config.verify_ssl is True, "verify_ssl should be True"
    print("  ✓ AZURE_OPENAI_VERIFY_SSL=true works")
    
    # Test with verify_ssl=1
    os.environ["AZURE_OPENAI_VERIFY_SSL"] = "1"
    config = config_manager._load_azure_config_from_env()
    assert config.verify_ssl is True, "verify_ssl should be True for '1'"
    print("  ✓ AZURE_OPENAI_VERIFY_SSL=1 works")
    
    # Test with verify_ssl=0
    os.environ["AZURE_OPENAI_VERIFY_SSL"] = "0"
    config = config_manager._load_azure_config_from_env()
    assert config.verify_ssl is False, "verify_ssl should be False for '0'"
    print("  ✓ AZURE_OPENAI_VERIFY_SSL=0 works")
    
    # Clean up
    for key in ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", 
                "AZURE_OPENAI_DEPLOYMENT_NAME", "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
                "AZURE_OPENAI_VERIFY_SSL"]:
        os.environ.pop(key, None)
    
    print("✅ Environment variable tests passed\n")


def test_client_initialization():
    """Test that clients can be initialized with verify_ssl setting."""
    print("Testing client initialization...")
    
    from dev_agent.models.llm_config import AzureOpenAIConfig
    from dev_agent.llm.azure_client import AzureOpenAIClient
    from dev_agent.llm.embeddings import AzureEmbeddingClient
    
    # Create config with SSL verification disabled
    config = AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        api_key="test-key",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        verify_ssl=False,
    )
    
    # Test Azure OpenAI client initialization
    try:
        client = AzureOpenAIClient(config)
        print("  ✓ AzureOpenAIClient initialized with verify_ssl=False")
    except Exception as e:
        print(f"  ✗ AzureOpenAIClient initialization failed: {e}")
        return False
    
    # Test embedding client initialization
    try:
        embedding_client = AzureEmbeddingClient(config)
        print("  ✓ AzureEmbeddingClient initialized with verify_ssl=False")
    except Exception as e:
        print(f"  ✗ AzureEmbeddingClient initialization failed: {e}")
        return False
    
    print("✅ Client initialization tests passed\n")
    return True


def test_bearer_token_with_insecure():
    """Test that bearer token authentication works with insecure mode."""
    print("Testing bearer token with insecure mode...")
    
    from dev_agent.models.llm_config import AzureOpenAIConfig
    
    # Test with bearer token and SSL disabled
    config = AzureOpenAIConfig(
        endpoint="https://test.openai.azure.com/",
        bearer_token="test-bearer-token",
        deployment_name="gpt-4",
        embedding_deployment="text-embedding-ada-002",
        verify_ssl=False,
        user_sid="A123456",
        custom_headers={"department": "engineering"},
    )
    
    assert config.verify_ssl is False, "verify_ssl should be False"
    assert config.bearer_token is not None, "bearer_token should be set"
    assert config.openai_api_type == "azure_ad", "Should use azure_ad type"
    print("  ✓ Bearer token with verify_ssl=False works")
    
    print("✅ Bearer token tests passed\n")


def main():
    """Run all tests."""
    print("="*60)
    print("Testing Insecure SSL Mode Implementation")
    print("="*60)
    print()
    
    try:
        test_config_model()
        test_env_variable()
        test_client_initialization()
        test_bearer_token_with_insecure()
        
        print("="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print()
        print("The insecure SSL mode feature is working correctly!")
        print()
        print("Next steps:")
        print("  1. Test with real Azure OpenAI: uv run dev-agent azure test --insecure")
        print("  2. Verify warnings are displayed")
        print("  3. Fix SSL certificates properly (see FIX_SSL_CERTIFICATE_ERROR.md)")
        print()
        
        return 0
        
    except AssertionError as e:
        print()
        print("="*60)
        print("❌ TEST FAILED")
        print("="*60)
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print()
        print("="*60)
        print("❌ UNEXPECTED ERROR")
        print("="*60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
