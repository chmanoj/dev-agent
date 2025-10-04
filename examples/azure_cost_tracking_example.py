"""Example: Azure OpenAI Cost Tracking and Management

This example demonstrates how to track token usage and costs for Azure OpenAI
operations, set budget limits, and generate cost reports.

Requirements:
- Azure OpenAI endpoint and API key configured
- Environment variables set (see below)
- dev-agent installed with Azure OpenAI dependencies
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_agent.llm.azure_client import AzureOpenAIClient
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.llm.token_counter import TokenCounter
from dev_agent.llm.cost_tracker import CostTracker
from dev_agent.llm.embedding_cache import EmbeddingCache
from dev_agent.models.llm_config import AzureOpenAIConfig
from dev_agent.models.enums import PhaseType
from pydantic import SecretStr


def setup_azure_config() -> AzureOpenAIConfig:
    """Set up Azure OpenAI configuration from environment variables.
    
    Returns:
        AzureOpenAIConfig: Validated configuration object
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key-here")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
    
    return AzureOpenAIConfig(
        endpoint=endpoint,
        api_key=SecretStr(api_key),
        api_version="2024-02-15-preview",
        deployment_name=deployment_name,
        embedding_deployment=embedding_deployment,
        max_tokens=2000,
        temperature=0.7,
        max_retries=3,
        timeout=60,
        batch_size=16,
    )


async def basic_cost_tracking_example():
    """Example: Track costs for basic Azure OpenAI operations.
    
    This example shows:
    1. Setting up cost tracking
    2. Tracking completion costs
    3. Tracking embedding costs
    4. Generating cost reports
    """
    print("=" * 70)
    print("Basic Cost Tracking Example")
    print("=" * 70)
    
    # Step 1: Setup
    print("\n[1/5] Setting up cost tracking...")
    try:
        config = setup_azure_config()
        cost_tracker = CostTracker()
        token_counter = TokenCounter()
        
        llm_client = AzureOpenAIClient(config)
        
        print("✅ Cost tracking initialized")
        print(f"   Tracking session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return
    
    # Step 2: Track completion costs
    print("\n[2/5] Generating completion and tracking costs...")
    
    prompt = "Explain what a Python decorator is in 2 sentences."
    
    # Count tokens before API call
    prompt_tokens = token_counter.count_tokens(prompt, model="gpt-4")
    print(f"   Prompt tokens: {prompt_tokens}")
    
    # Estimate cost before calling
    estimated_cost = token_counter.estimate_cost(
        prompt_tokens=prompt_tokens,
        completion_tokens=100,  # Estimated
        model="gpt-4",
    )
    print(f"   Estimated cost: ${estimated_cost:.4f}")
    
    try:
        # Generate completion
        response = await llm_client.generate_completion(
            prompt=prompt,
            max_tokens=100,
        )
        
        # Count actual completion tokens
        completion_tokens = token_counter.count_tokens(response, model="gpt-4")
        
        # Record in cost tracker
        cost_tracker.record_completion(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model="gpt-4",
        )
        
        print(f"✅ Completion generated")
        print(f"   Actual completion tokens: {completion_tokens}")
        print(f"   Total tokens: {prompt_tokens + completion_tokens}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 3: Track embedding costs
    print("\n[3/5] Generating embeddings and tracking costs...")
    
    cache_dir = Path(".dev_agent/embedding_cache")
    embedding_cache = EmbeddingCache(cache_dir)
    
    embedding_client = AzureEmbeddingClient(
        config=config,
        cache=embedding_cache,
        cost_tracker=cost_tracker,
    )
    
    texts = [
        "def hello(): print('Hello')",
        "class MyClass: pass",
        "import numpy as np",
    ]
    
    try:
        embeddings = await embedding_client.embed_batch(texts)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 4: Generate cost report
    print("\n[4/5] Generating cost report...")
    
    report = cost_tracker.get_report()
    
    print("✅ Cost Report:")
    print(f"   Prompt tokens: {report.get('prompt_tokens', 0):,}")
    print(f"   Completion tokens: {report.get('completion_tokens', 0):,}")
    print(f"   Embedding tokens: {report.get('embedding_tokens', 0):,}")
    print(f"   Total tokens: {report.get('total_tokens', 0):,}")
    print(f"   Total cost: ${report.get('total_cost', 0):.6f}")
    
    # Step 5: Break down costs by operation type
    print("\n[5/5] Cost breakdown by operation type...")
    
    operations = cost_tracker.get_operations_summary()
    
    print("✅ Operations Summary:")
    for op_type, stats in operations.items():
        print(f"   {op_type}:")
        print(f"     - Count: {stats['count']}")
        print(f"     - Tokens: {stats['tokens']:,}")
        print(f"     - Cost: ${stats['cost']:.6f}")
    
    print("\n✅ Example completed successfully!")


async def phase_based_cost_tracking_example():
    """Example: Track costs per workflow phase.
    
    This shows how to track costs separately for different phases
    of the development workflow.
    """
    print("\n" + "=" * 70)
    print("Phase-Based Cost Tracking Example")
    print("=" * 70)
    
    # Setup
    print("\n[1/4] Setting up...")
    try:
        config = setup_azure_config()
        cost_tracker = CostTracker()
        llm_client = AzureOpenAIClient(config)
        print("✅ Setup complete")
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return
    
    # Simulate different workflow phases
    phases = [
        (PhaseType.INDEXING, "Analyzing codebase structure"),
        (PhaseType.SPECIFICATION, "Generating technical specification"),
        (PhaseType.DESIGN, "Creating design document"),
        (PhaseType.IMPLEMENTATION, "Generating implementation code"),
    ]
    
    for phase, description in phases:
        print(f"\n[Phase: {phase.value}] {description}...")
        
        try:
            # Simulate phase operation
            prompt = f"Generate a brief {phase.value} document for a user authentication system."
            
            response = await llm_client.generate_completion(
                prompt=prompt,
                max_tokens=200,
            )
            
            # Record with phase information
            token_counter = TokenCounter()
            prompt_tokens = token_counter.count_tokens(prompt, model="gpt-4")
            completion_tokens = token_counter.count_tokens(response, model="gpt-4")
            
            cost_tracker.record_completion(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model="gpt-4",
                phase=phase,
            )
            
            print(f"   ✅ Completed - Tokens: {prompt_tokens + completion_tokens}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    # Generate phase-based report
    print("\n💰 Cost Report by Phase:")
    print("=" * 70)
    
    phase_costs = cost_tracker.get_costs_by_phase()
    
    for phase, cost_data in phase_costs.items():
        print(f"\n{phase.value.upper()}:")
        print(f"   Tokens: {cost_data['tokens']:,}")
        print(f"   Cost: ${cost_data['cost']:.6f}")
        print(f"   Operations: {cost_data['operations']}")
    
    # Total summary
    total_report = cost_tracker.get_report()
    print(f"\nTOTAL:")
    print(f"   Tokens: {total_report['total_tokens']:,}")
    print(f"   Cost: ${total_report['total_cost']:.6f}")


async def budget_management_example():
    """Example: Manage budgets and set cost limits.
    
    This shows how to set budget thresholds and receive warnings
    when approaching limits.
    """
    print("\n" + "=" * 70)
    print("Budget Management Example")
    print("=" * 70)
    
    # Setup with budget limits
    print("\n[1/4] Setting up with budget limits...")
    try:
        config = setup_azure_config()
        cost_tracker = CostTracker()
        llm_client = AzureOpenAIClient(config)
        
        # Set budget thresholds
        budget_limit = 1.00  # $1.00 limit
        warning_threshold = 0.80  # Warn at 80%
        
        print("✅ Setup complete")
        print(f"   Budget limit: ${budget_limit:.2f}")
        print(f"   Warning threshold: {warning_threshold * 100:.0f}%")
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return
    
    # Simulate operations
    print("\n[2/4] Running operations with budget monitoring...")
    
    operations = [
        "Generate a function to validate email addresses",
        "Create a class for user authentication",
        "Write a REST API endpoint for user registration",
        "Generate unit tests for the authentication system",
        "Create documentation for the API",
    ]
    
    for i, operation in enumerate(operations, 1):
        print(f"\n   Operation {i}/{len(operations)}: {operation[:50]}...")
        
        try:
            # Generate completion
            response = await llm_client.generate_completion(
                prompt=operation,
                max_tokens=150,
            )
            
            # Track cost
            token_counter = TokenCounter()
            prompt_tokens = token_counter.count_tokens(operation, model="gpt-4")
            completion_tokens = token_counter.count_tokens(response, model="gpt-4")
            
            cost_tracker.record_completion(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model="gpt-4",
            )
            
            # Check budget
            current_cost = cost_tracker.get_report()['total_cost']
            percentage_used = (current_cost / budget_limit) * 100
            
            print(f"   ✅ Completed - Cost: ${current_cost:.4f} ({percentage_used:.1f}% of budget)")
            
            # Budget warnings
            if current_cost >= budget_limit:
                print(f"   🚨 BUDGET LIMIT EXCEEDED! Stop operations.")
                break
            elif current_cost >= (budget_limit * warning_threshold):
                print(f"   ⚠️  WARNING: Approaching budget limit!")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    # Final budget report
    print("\n[3/4] Final budget report...")
    
    final_report = cost_tracker.get_report()
    final_cost = final_report['total_cost']
    
    print("💰 Budget Summary:")
    print(f"   Budget limit: ${budget_limit:.2f}")
    print(f"   Total spent: ${final_cost:.4f}")
    print(f"   Remaining: ${budget_limit - final_cost:.4f}")
    print(f"   Percentage used: {(final_cost / budget_limit) * 100:.1f}%")
    
    if final_cost < budget_limit:
        print("   ✅ Within budget")
    else:
        print("   🚨 Over budget")
    
    # Recommendations
    print("\n[4/4] Cost optimization recommendations...")
    
    print("💡 Recommendations:")
    print("   1. Use caching to avoid redundant API calls")
    print("   2. Reduce max_tokens for shorter responses")
    print("   3. Use lower temperature for more focused outputs")
    print("   4. Batch operations when possible")
    print("   5. Monitor token usage per operation")


async def cost_optimization_example():
    """Example: Demonstrate cost optimization techniques.
    
    This shows various strategies to reduce Azure OpenAI costs.
    """
    print("\n" + "=" * 70)
    print("Cost Optimization Example")
    print("=" * 70)
    
    # Setup
    print("\n[1/5] Setting up...")
    try:
        config = setup_azure_config()
        print("✅ Setup complete")
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return
    
    # Technique 1: Use caching for embeddings
    print("\n[2/5] Technique 1: Embedding caching...")
    
    cache_dir = Path(".dev_agent/embedding_cache")
    embedding_cache = EmbeddingCache(cache_dir)
    cost_tracker_1 = CostTracker()
    
    embedding_client = AzureEmbeddingClient(
        config=config,
        cache=embedding_cache,
        cost_tracker=cost_tracker_1,
    )
    
    texts = ["def hello(): pass"] * 5  # Same text 5 times
    
    try:
        # First call - no cache
        await embedding_client.embed_batch(texts)
        cost_without_cache = cost_tracker_1.get_report()['total_cost']
        
        # Second call - with cache
        cost_tracker_2 = CostTracker()
        embedding_client_2 = AzureEmbeddingClient(
            config=config,
            cache=embedding_cache,
            cost_tracker=cost_tracker_2,
        )
        await embedding_client_2.embed_batch(texts)
        cost_with_cache = cost_tracker_2.get_report()['total_cost']
        
        print(f"   Without cache: ${cost_without_cache:.6f}")
        print(f"   With cache: ${cost_with_cache:.6f}")
        print(f"   Savings: ${cost_without_cache - cost_with_cache:.6f} ({(1 - cost_with_cache/cost_without_cache)*100:.1f}%)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Technique 2: Reduce max_tokens
    print("\n[3/5] Technique 2: Optimize max_tokens...")
    
    llm_client = AzureOpenAIClient(config)
    token_counter = TokenCounter()
    
    prompt = "Explain Python decorators"
    
    try:
        # High max_tokens
        cost_tracker_high = CostTracker()
        response_high = await llm_client.generate_completion(prompt, max_tokens=1000)
        tokens_high = token_counter.count_tokens(response_high, model="gpt-4")
        cost_tracker_high.record_completion(
            prompt_tokens=token_counter.count_tokens(prompt, model="gpt-4"),
            completion_tokens=tokens_high,
            model="gpt-4",
        )
        
        # Low max_tokens
        cost_tracker_low = CostTracker()
        response_low = await llm_client.generate_completion(prompt, max_tokens=100)
        tokens_low = token_counter.count_tokens(response_low, model="gpt-4")
        cost_tracker_low.record_completion(
            prompt_tokens=token_counter.count_tokens(prompt, model="gpt-4"),
            completion_tokens=tokens_low,
            model="gpt-4",
        )
        
        print(f"   High max_tokens (1000): {tokens_high} tokens, ${cost_tracker_high.get_report()['total_cost']:.6f}")
        print(f"   Low max_tokens (100): {tokens_low} tokens, ${cost_tracker_low.get_report()['total_cost']:.6f}")
        print(f"   Savings: ${cost_tracker_high.get_report()['total_cost'] - cost_tracker_low.get_report()['total_cost']:.6f}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Technique 3: Batch operations
    print("\n[4/5] Technique 3: Batch operations...")
    
    print("   Batching embeddings reduces API calls and improves efficiency")
    print("   Example: 16 texts in 1 batch vs 16 individual calls")
    print("   Savings: ~15-20% reduction in total time and overhead")
    
    # Technique 4: Token counting before API calls
    print("\n[5/5] Technique 4: Pre-flight token counting...")
    
    print("   Always count tokens before API calls to:")
    print("   1. Avoid exceeding context limits")
    print("   2. Estimate costs accurately")
    print("   3. Optimize prompt length")
    print("   4. Make informed decisions about API calls")
    
    print("\n✅ Cost optimization techniques demonstrated!")


def main():
    """Run cost tracking examples."""
    print("\n🚀 Azure OpenAI Cost Tracking Examples\n")
    
    # Check configuration
    if not os.getenv("AZURE_OPENAI_API_KEY") or not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("⚠️  Azure OpenAI not configured!")
        print("\nTo run this example, set the following environment variables:")
        print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("  export AZURE_OPENAI_API_KEY='your-api-key-here'")
        print("  export AZURE_OPENAI_DEPLOYMENT_NAME='gpt-4'")
        print("  export AZURE_OPENAI_EMBEDDING_DEPLOYMENT='text-embedding-ada-002'")
        print("\n⚠️  Never commit API keys to version control!")
        return
    
    # Run examples
    asyncio.run(basic_cost_tracking_example())
    
    # Optional examples
    print("\n" + "=" * 70)
    response = input("\nRun phase-based tracking example? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(phase_based_cost_tracking_example())
    
    print("\n" + "=" * 70)
    response = input("\nRun budget management example? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(budget_management_example())
    
    print("\n" + "=" * 70)
    response = input("\nRun cost optimization example? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(cost_optimization_example())
    
    print("\n🎉 All examples completed!")
    print("\nKey takeaways:")
    print("  1. Always track token usage and costs for all operations")
    print("  2. Set budget limits and monitor spending")
    print("  3. Use caching to reduce redundant API calls")
    print("  4. Optimize max_tokens based on actual needs")
    print("  5. Batch operations for better efficiency")
    print("  6. Count tokens before API calls to estimate costs")
    print("  7. Track costs per workflow phase for better insights")


if __name__ == "__main__":
    main()
