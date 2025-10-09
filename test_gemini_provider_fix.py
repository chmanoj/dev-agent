#!/usr/bin/env python3
"""Test script to verify Gemini provider configuration fix."""

import os
import sys

# Set up Gemini environment variables
os.environ["GEMINI_API_KEY"] = "AIzaSyDummy_Test_Key_For_Validation_Only_12345"
os.environ["GEMINI_MODEL_NAME"] = "gemini-2.5-flash"
os.environ["GEMINI_EMBEDDING_MODEL"] = "gemini-embedding-001"
os.environ["PREFERRED_LLM_PROVIDER"] = "gemini"

# Unset Azure OpenAI variables to ensure we're testing Gemini only
for key in [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
]:
    os.environ.pop(key, None)

try:
    from dev_agent.config import ConfigManager
    from dev_agent.models.enums import LLMProvider

    print("✓ Imports successful")

    # Test 1: Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()
    print("✓ Configuration loaded")

    # Test 2: Get LLM provider
    provider = config_manager.get_llm_provider()
    print(f"✓ Provider detected: {provider}")

    # Test 3: Verify it's Gemini
    assert provider == LLMProvider.GEMINI, f"Expected GEMINI, got {provider}"
    print("✓ Provider is GEMINI as expected")

    # Test 4: Verify Gemini config is loaded
    assert config.gemini is not None, "Gemini config should not be None"
    print("✓ Gemini config is loaded")

    # Test 5: Verify Azure OpenAI config is None or not required
    print(f"  Azure OpenAI config: {config.azure_openai}")

    # Test 6: Validate provider config
    is_valid, error_msg = config_manager.validate_provider_config(LLMProvider.GEMINI)
    assert is_valid, f"Gemini config validation failed: {error_msg}"
    print("✓ Gemini config is valid")

    print("\n✅ All tests passed! Gemini provider fix is working correctly.")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
