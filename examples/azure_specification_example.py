"""Example: Azure OpenAI Specification Generation

This example demonstrates how to use Azure OpenAI to generate technical
specifications from user requirements and codebase analysis.

Requirements:
- Azure OpenAI endpoint and API key configured
- Environment variables set (see below)
- dev-agent installed with Azure OpenAI dependencies
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.token_counter import TokenCounter
from dev_agent.llm.cost_tracker import CostTracker
from dev_agent.llm.prompt_templates import PromptTemplate
from dev_agent.models.llm_config import AzureOpenAIConfig
from pydantic import SecretStr


def setup_azure_config() -> AzureOpenAIConfig:
    """Set up Azure OpenAI configuration from environment variables.
    
    Required environment variables:
    - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint URL
    - AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
    - AZURE_OPENAI_DEPLOYMENT_NAME: Your GPT-4 deployment name
    
    Returns:
        AzureOpenAIConfig: Validated configuration object
    """
    # Get configuration from environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key-here")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    # Create configuration with validation
    config = AzureOpenAIConfig(
        endpoint=endpoint,
        api_key=SecretStr(api_key),
        api_version="2024-02-15-preview",
        deployment_name=deployment_name,
        embedding_deployment="text-embedding-ada-002",
        max_tokens=4000,
        temperature=0.7,
        max_retries=3,
        timeout=60,
    )
    
    return config


def create_specification_prompt() -> PromptTemplate:
    """Create a prompt template for specification generation.
    
    Returns:
        PromptTemplate: Structured prompt for spec generation
    """
    system_prompt = """You are a technical specification writer with expertise in software architecture.
Your task is to create detailed, actionable specifications based on user requirements and codebase context.

Guidelines:
1. Write clear, unambiguous requirements
2. Include acceptance criteria for each feature
3. Consider edge cases and error handling
4. Maintain consistency with existing architecture
5. Use industry-standard terminology
"""

    user_prompt_template = """## User Requirements
{user_requirements}

## Codebase Context
{codebase_context}

## Existing Patterns
{existing_patterns}

## Task
Generate a comprehensive technical specification that includes:
1. Overview and objectives
2. Functional requirements with acceptance criteria
3. Technical requirements and constraints
4. Data models and interfaces
5. Error handling strategy
6. Testing requirements

Format the specification in markdown with clear sections and bullet points.
"""

    return PromptTemplate(
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        required_context=["user_requirements", "codebase_context", "existing_patterns"],
        max_context_tokens=6000,
        temperature=0.7,
        max_tokens=4000,
    )


async def generate_specification_example():
    """Example: Generate a specification using Azure OpenAI.
    
    This example shows:
    1. Setting up Azure OpenAI client
    2. Creating a structured prompt
    3. Counting tokens before API call
    4. Generating specification with GPT-4
    5. Tracking costs
    """
    print("=" * 70)
    print("Azure OpenAI Specification Generation Example")
    print("=" * 70)
    
    # Step 1: Set up configuration
    print("\n[1/6] Setting up Azure OpenAI configuration...")
    try:
        config = setup_azure_config()
        print(f"✅ Configuration loaded")
        print(f"   Endpoint: {config.endpoint}")
        print(f"   Deployment: {config.deployment_name}")
        print(f"   Max tokens: {config.max_tokens}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease set the following environment variables:")
        print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("  export AZURE_OPENAI_API_KEY='your-api-key-here'")
        print("  export AZURE_OPENAI_DEPLOYMENT_NAME='gpt-4'")
        return
    
    # Step 2: Initialize clients
    print("\n[2/6] Initializing Azure OpenAI client...")
    llm_client = AzureOpenAIClient(config)
    token_counter = TokenCounter()
    cost_tracker = CostTracker()
    print("✅ Clients initialized")
    
    # Step 3: Prepare context
    print("\n[3/6] Preparing specification context...")
    
    # Example user requirements
    user_requirements = """
    - Create a user authentication system
    - Support email/password and OAuth2 authentication
    - Implement JWT token-based sessions
    - Include password reset functionality
    - Add rate limiting for login attempts
    - Support multi-factor authentication (MFA)
    """
    
    # Example codebase context (would come from vector search in real usage)
    codebase_context = """
    Existing authentication patterns:
    - Uses FastAPI for REST API endpoints
    - Pydantic models for data validation
    - SQLAlchemy for database operations
    - Redis for session storage
    - Follows repository pattern for data access
    """
    
    # Example existing patterns
    existing_patterns = """
    - All API endpoints use async/await
    - Error handling with custom exception classes
    - Logging with structured JSON format
    - Type hints on all functions
    - Comprehensive docstrings in Google style
    """
    
    print("✅ Context prepared")
    print(f"   User requirements: {len(user_requirements)} characters")
    print(f"   Codebase context: {len(codebase_context)} characters")
    
    # Step 4: Build prompt and count tokens
    print("\n[4/6] Building prompt and counting tokens...")
    
    template = create_specification_prompt()
    prompt = template.user_prompt_template.format(
        user_requirements=user_requirements,
        codebase_context=codebase_context,
        existing_patterns=existing_patterns,
    )
    
    # Count tokens before API call
    prompt_tokens = token_counter.count_tokens(prompt, model="gpt-4")
    system_tokens = token_counter.count_tokens(template.system_prompt, model="gpt-4")
    total_input_tokens = prompt_tokens + system_tokens
    
    print(f"✅ Prompt built")
    print(f"   System prompt tokens: {system_tokens}")
    print(f"   User prompt tokens: {prompt_tokens}")
    print(f"   Total input tokens: {total_input_tokens}")
    
    # Estimate cost before calling API
    estimated_cost = token_counter.estimate_cost(
        prompt_tokens=total_input_tokens,
        completion_tokens=template.max_tokens,
        model="gpt-4",
    )
    print(f"   Estimated cost: ${estimated_cost:.4f}")
    
    # Step 5: Generate specification
    print("\n[5/6] Generating specification with Azure OpenAI...")
    print("   (This may take 10-30 seconds...)")
    
    try:
        # Call Azure OpenAI to generate specification
        specification = await llm_client.generate_completion(
            prompt=prompt,
            system_prompt=template.system_prompt,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
        )
        
        print("✅ Specification generated successfully!")
        print(f"   Response length: {len(specification)} characters")
        
        # Count actual completion tokens
        completion_tokens = token_counter.count_tokens(specification, model="gpt-4")
        print(f"   Completion tokens: {completion_tokens}")
        
        # Step 6: Track costs
        print("\n[6/6] Tracking costs...")
        cost_tracker.record_completion(
            prompt_tokens=total_input_tokens,
            completion_tokens=completion_tokens,
            model="gpt-4",
        )
        
        report = cost_tracker.get_report()
        print(f"✅ Cost tracking updated")
        print(f"   Total tokens: {report['total_tokens']}")
        print(f"   Actual cost: ${report['total_cost']:.4f}")
        
        # Display generated specification (first 500 characters)
        print("\n" + "=" * 70)
        print("Generated Specification (preview):")
        print("=" * 70)
        print(specification[:500] + "..." if len(specification) > 500 else specification)
        print("=" * 70)
        
        # Save to file
        output_file = Path("specification_example_output.md")
        output_file.write_text(specification)
        print(f"\n💾 Full specification saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error generating specification: {e}")
        print(f"   Error type: {type(e).__name__}")
        return
    
    print("\n✅ Example completed successfully!")
    print("\nKey takeaways:")
    print("  1. Always count tokens before API calls to estimate costs")
    print("  2. Use structured prompts with clear instructions")
    print("  3. Include relevant codebase context for better results")
    print("  4. Track costs for all operations")
    print("  5. Handle errors gracefully with try/except blocks")


async def generate_specification_with_streaming():
    """Example: Generate specification with streaming for real-time feedback.
    
    This shows how to use streaming to display tokens as they're generated,
    providing better user experience for long-running operations.
    """
    print("\n" + "=" * 70)
    print("Streaming Specification Generation Example")
    print("=" * 70)
    
    print("\n[1/3] Setting up configuration...")
    try:
        config = setup_azure_config()
        llm_client = AzureOpenAIClient(config)
        print("✅ Configuration ready")
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return
    
    print("\n[2/3] Preparing prompt...")
    template = create_specification_prompt()
    prompt = template.user_prompt_template.format(
        user_requirements="Create a simple REST API for task management",
        codebase_context="FastAPI application with SQLAlchemy",
        existing_patterns="Async endpoints, Pydantic models, type hints",
    )
    
    print("\n[3/3] Generating specification with streaming...")
    print("-" * 70)
    
    try:
        # Stream tokens as they're generated
        full_response = ""
        async for token in llm_client.generate_streaming(
            prompt=prompt,
            system_prompt=template.system_prompt,
        ):
            print(token, end="", flush=True)
            full_response += token
        
        print("\n" + "-" * 70)
        print(f"\n✅ Streaming completed! Generated {len(full_response)} characters")
        
    except Exception as e:
        print(f"\n❌ Streaming error: {e}")


def main():
    """Run specification generation examples."""
    print("\n🚀 Azure OpenAI Specification Generation Examples\n")
    
    # Check if Azure OpenAI is configured
    if not os.getenv("AZURE_OPENAI_API_KEY") or not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("⚠️  Azure OpenAI not configured!")
        print("\nTo run this example, set the following environment variables:")
        print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("  export AZURE_OPENAI_API_KEY='your-api-key-here'")
        print("  export AZURE_OPENAI_DEPLOYMENT_NAME='gpt-4'")
        print("\nNever commit API keys to version control!")
        return
    
    # Run examples
    asyncio.run(generate_specification_example())
    
    # Optional: Run streaming example
    print("\n" + "=" * 70)
    response = input("\nRun streaming example? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(generate_specification_with_streaming())
    
    print("\n🎉 All examples completed!")


if __name__ == "__main__":
    main()
