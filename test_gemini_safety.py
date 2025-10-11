#!/usr/bin/env python3
"""Test Gemini client with safety settings."""

import asyncio
import os
import sys
from pathlib import Path

# Add the dev_agent package to the path
sys.path.insert(0, str(Path(__file__).parent))

from dev_agent.llm import create_llm_client
from dev_agent.models.llm_config import GeminiConfig

async def test_gemini_safety():
    """Test Gemini client with safety settings."""
    
    # Load API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return False
    
    # Create Gemini config with permissive safety settings
    config = GeminiConfig(
        api_key=api_key,
        model_name="gemini-2.5-flash",
        temperature=0.7,
        max_output_tokens=1000,
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE", 
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )
    
    print(f"Testing Gemini with safety settings: {config.safety_settings}")
    
    try:
        client = create_llm_client("gemini", config)
        
        # Test with the most basic prompt
        prompt = "Hello, how are you?"
        
        print(f"Testing prompt: {prompt}")
        
        result = await client.generate_completion(prompt)
        
        print(f"Success! Generated {len(result)} characters")
        print(f"First 200 chars: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gemini_safety())
    sys.exit(0 if success else 1)