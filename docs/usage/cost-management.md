# Cost Management Guide

This guide helps you understand, track, and optimize AI provider costs when using dev-agent. dev-agent supports both Azure OpenAI and Google Gemini, each with different pricing models.

## Provider Pricing Comparison

Both providers charge based on token usage. Tokens are pieces of text that the model processes - roughly 4 characters or 0.75 words per token.

### Cost Comparison Overview

| Provider | Input (1K tokens) | Output (1K tokens) | Embeddings (1K tokens) | Savings vs Azure |
|----------|-------------------|-------------------|------------------------|------------------|
| **Azure OpenAI** | $0.01-$0.03 | $0.03-$0.06 | $0.0001 | Baseline |
| **Google Gemini** | $0.00025 | $0.0005 | $0.0001 | 95-98% |

**Key Takeaway**: Gemini offers significant cost savings (95-98%) for most operations.

## Understanding Azure OpenAI Pricing

Azure OpenAI charges based on token usage with higher rates but enterprise features.

### Current Pricing (as of 2024)

**GPT-4 Models**:
- **Prompt tokens**: $0.03 per 1,000 tokens
- **Completion tokens**: $0.06 per 1,000 tokens

**GPT-4 Turbo Models**:
- **Prompt tokens**: $0.01 per 1,000 tokens
- **Completion tokens**: $0.03 per 1,000 tokens

**GPT-4o Models** (when available):
- **Prompt tokens**: $0.005 per 1,000 tokens
- **Completion tokens**: $0.015 per 1,000 tokens

**Embeddings (text-embedding-ada-002)**:
- **All tokens**: $0.0001 per 1,000 tokens

**Note**: Prices vary by region and may change. Check [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/) for current rates.

## Understanding Google Gemini Pricing

Google Gemini offers significantly lower costs with competitive performance.

### Current Pricing (as of 2024)

**Gemini Pro Models**:
- **Input tokens**: $0.00025 per 1,000 tokens (97.5% cheaper than Azure GPT-4)
- **Output tokens**: $0.0005 per 1,000 tokens (99.2% cheaper than Azure GPT-4)

**Gemini Ultra Models**:
- **Input tokens**: $0.00125 per 1,000 tokens
- **Output tokens**: $0.0025 per 1,000 tokens

**Embeddings (embedding-001, text-embedding-004)**:
- **All tokens**: $0.0001 per 1,000 tokens (same as Azure)

**Rate Limits**:
- **Free tier**: 60 requests/minute, 32K tokens/minute
- **Paid tier**: 1000+ requests/minute, 128K+ tokens/minute

**Note**: Check [Gemini Pricing](https://ai.google.dev/pricing) for current rates and quotas.

## Token Usage in dev-agent

### What Counts as Tokens?

1. **Prompt Tokens**: Everything sent to the model
   - Your instructions and questions
   - Code context from your codebase
   - System prompts
   - Few-shot examples

2. **Completion Tokens**: Everything the model generates
   - Generated specifications
   - Generated designs
   - Generated code
   - Generated task lists

3. **Embedding Tokens**: Text converted to embeddings
   - Code chunks during indexing
   - Query text during vector search

### Typical Token Usage by Phase

| Phase | Operation | Typical Tokens | Azure OpenAI Cost | Gemini Cost | Savings |
|-------|-----------|----------------|-------------------|-------------|---------|
| **Indexing** | Embed 1,000 code chunks | ~500,000 | $0.05 | $0.05 | 0% |
| **Specification** | Generate spec with context | ~3,000 prompt + 2,000 completion | $0.21 | $0.0018 | 99.1% |
| **Design** | Generate design with context | ~4,000 prompt + 3,000 completion | $0.30 | $0.0025 | 99.2% |
| **Implementation** | Generate code with context | ~2,000 prompt + 1,500 completion | $0.15 | $0.0013 | 99.1% |

**Total for typical feature**:
- **Azure OpenAI**: ~$0.70 - $1.50
- **Gemini**: ~$0.06 - $0.10
- **Savings**: ~90-95% total cost reduction

**Note**: Costs vary significantly based on:
- Codebase size
- Feature complexity
- Amount of context included
- Model used (GPT-4 vs GPT-4 Turbo)

## Tracking Costs in dev-agent

### Automatic Cost Tracking

dev-agent automatically tracks token usage and costs for all providers:

```bash
# Run any workflow phase
uv run dev-agent init /path/to/project

# After each phase, you'll see:
# ✓ Indexing complete
# 
# Token Usage:
#   Embedding tokens: 487,234
#   Estimated cost: $0.05
```

### View Cost Report

Get a detailed cost report for your session:

```bash
# View cost report
uv run dev-agent cost-report

# Output:
# Cost Report - Session 2024-01-15
# ================================
# 
# Provider: Google Gemini (gemini-pro)
# 
# By Operation Type:
#   Embeddings:    487,234 tokens  ($0.05)
#   Completions:   12,450 tokens   ($0.01)
#   Total:         499,684 tokens  ($0.06)
# 
# By Phase:
#   Indexing:      487,234 tokens  ($0.05)
#   Specification: 5,230 tokens    ($0.004)
#   Design:        7,220 tokens    ($0.006)
#   
# Total Estimated Cost: $0.06
# 
# Savings vs Azure OpenAI: $0.61 (91% reduction)
```

### Programmatic Cost Tracking

Access cost data programmatically:

```python
from dev_agent.llm.cost_tracker import CostTracker

# Create cost tracker
tracker = CostTracker()

# Track completion usage
tracker.add_completion(
    prompt_tokens=1000,
    completion_tokens=500,
)

# Track embedding usage
tracker.add_embedding_tokens(50000)

# Get cost report
report = tracker.get_report()
print(f"Total cost: ${report['estimated_cost']:.2f}")
print(f"Total tokens: {report['total_tokens']:,}")
```

## Cost Optimization Strategies

### 1. Use Embedding Cache

dev-agent automatically caches embeddings to avoid re-computing them:

```bash
# First run: Generates embeddings
uv run dev-agent init /path/to/project
# Cost: $0.05 for 500K tokens

# Second run: Uses cached embeddings
uv run dev-agent resume /path/to/project
# Cost: $0.00 for embeddings (cache hit)
```

**Cache Benefits**:
- 100% cost savings on repeated embeddings
- Faster indexing (no API calls)
- Automatic cache invalidation on code changes

**Cache Location**: `.dev_agent/embedding_cache/`

### 2. Optimize Context Size

Reduce the amount of context sent to the model:

```python
# Configure context limits
config = {
    "max_context_chunks": 5,  # Default: 10
    "max_context_tokens": 2000,  # Default: 4000
}

# This reduces prompt tokens by ~50%
# Savings: ~$0.015 per completion
```

**Trade-offs**:
- Less context = lower cost
- Less context = potentially less accurate results
- Find the right balance for your use case

### 3. Choose the Right Provider and Model

Select the optimal provider and model for each task:

| Task | Azure OpenAI | Gemini | Best Choice | Cost Savings |
|------|--------------|--------|-------------|--------------|
| **Simple code generation** | GPT-4 Turbo | Gemini Pro | Gemini Pro | 95-98% |
| **Complex architecture** | GPT-4 | Gemini Ultra | Depends on needs | 90-95% |
| **Code embeddings** | text-embedding-ada-002 | embedding-001 | Either | Same cost |
| **Multimodal tasks** | GPT-4 Vision | Gemini Pro Vision | Gemini Pro Vision | 95-98% |

**Configuration**:
```bash
# Use Gemini for maximum cost savings
export PREFERRED_LLM_PROVIDER=gemini
export GEMINI_MODEL_NAME=gemini-pro

# Use Azure OpenAI for enterprise requirements
export PREFERRED_LLM_PROVIDER=azure
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo

# Switch providers per command
dev-agent generate --provider gemini --prompt "Simple function"
dev-agent generate --provider azure --prompt "Complex architecture"
```

### 4. Batch Operations

Process multiple items together to reduce overhead:

```python
# Batch embeddings (automatic in dev-agent)
embeddings = await embedding_client.embed_batch(
    texts=code_chunks,
    batch_size=16,  # Optimal batch size
)

# This reduces API calls by 16x
# Savings: Faster processing, same cost
```

### 5. Set Budget Limits

Configure budget warnings for both providers:

```bash
# Azure OpenAI budget limits
export AZURE_OPENAI_BUDGET_WARNING="10.00"  # Warn at $10
export AZURE_OPENAI_BUDGET_LIMIT="50.00"    # Stop at $50

# Gemini budget limits (much lower due to cost savings)
export GEMINI_BUDGET_WARNING="1.00"         # Warn at $1
export GEMINI_BUDGET_LIMIT="5.00"           # Stop at $5

# Combined budget across providers
export DEV_AGENT_TOTAL_BUDGET="20.00"       # Total monthly budget
```

When approaching limits:
```
⚠ Warning: Approaching budget limit
  Current usage: $9.50 / $10.00 (95%)
  Continue? [y/N]
```

### 6. Monitor and Analyze Usage

Review usage patterns to identify optimization opportunities:

```bash
# View detailed usage breakdown
uv run dev-agent cost-report --detailed

# Export usage data
uv run dev-agent cost-report --export usage.json

# Analyze in spreadsheet or BI tool
```

**Look for**:
- High-cost operations that could be optimized
- Repeated operations that could be cached
- Unnecessary context being included
- Opportunities to use cheaper models

## Budget Management

### Setting Up Budget Tracking

1. **Define your budget**:
   ```bash
   # Monthly budget example
   export AZURE_OPENAI_MONTHLY_BUDGET="100.00"
   ```

2. **Track spending**:
   ```python
   from dev_agent.llm.cost_tracker import CostTracker
   
   tracker = CostTracker()
   tracker.set_budget(monthly_limit=100.00)
   
   # Check budget status
   status = tracker.get_budget_status()
   print(f"Used: ${status['used']:.2f} / ${status['limit']:.2f}")
   print(f"Remaining: ${status['remaining']:.2f}")
   ```

3. **Set up alerts**:
   ```python
   # Configure budget alerts
   tracker.set_alert_thresholds([
       (50, "50% budget used"),
       (75, "75% budget used"),
       (90, "90% budget used - approaching limit"),
   ])
   ```

### Cost Allocation

Track costs by project or feature:

```python
# Tag operations with project/feature
tracker.add_completion(
    prompt_tokens=1000,
    completion_tokens=500,
    tags={"project": "user-auth", "phase": "implementation"},
)

# Get costs by tag
costs_by_project = tracker.get_costs_by_tag("project")
print(f"user-auth: ${costs_by_project['user-auth']:.2f}")
```

## Cost Estimation

### Estimate Before Running

Estimate costs before starting a workflow:

```bash
# Estimate indexing cost
uv run dev-agent estimate-cost /path/to/project

# Output:
# Cost Estimation for /path/to/project
# =====================================
# 
# Codebase Analysis:
#   Files: 1,234
#   Lines of code: 45,678
#   Estimated chunks: 2,500
# 
# Estimated Costs:
#   Indexing (embeddings): $0.12
#   Specification: $0.20
#   Design: $0.30
#   Implementation: $0.40
#   
# Total Estimated: $1.02
```

### Programmatic Estimation

```python
from dev_agent.llm.token_counter import TokenCounter

counter = TokenCounter()

# Estimate completion cost
prompt = "Generate a user authentication module"
context = load_relevant_code()

prompt_tokens = counter.count_tokens(prompt + context)
estimated_completion_tokens = 2000  # Estimate based on task

cost = counter.estimate_cost(
    prompt_tokens=prompt_tokens,
    completion_tokens=estimated_completion_tokens,
)

print(f"Estimated cost: ${cost:.2f}")
```

## Cost Optimization Checklist

Use this checklist to optimize costs:

- [ ] **Enable embedding cache** (automatic in dev-agent)
- [ ] **Review context size** - reduce if possible
- [ ] **Use GPT-4 Turbo** for non-critical tasks
- [ ] **Set budget limits** to avoid surprises
- [ ] **Monitor usage patterns** regularly
- [ ] **Batch operations** when possible
- [ ] **Remove unnecessary context** from prompts
- [ ] **Cache frequently used completions** (future enhancement)
- [ ] **Use streaming** to stop early if needed
- [ ] **Review and optimize prompts** regularly

## Real-World Cost Examples

### Small Project (1,000 LOC)

| Phase | Azure OpenAI | Gemini | Savings |
|-------|--------------|--------|---------|
| Indexing | $0.02 | $0.02 | 0% |
| Specification | $0.15 | $0.001 | 99.3% |
| Design | $0.20 | $0.002 | 99.0% |
| Implementation | $0.30 | $0.003 | 99.0% |
| **Total** | **$0.67** | **$0.026** | **96.1%** |

### Medium Project (10,000 LOC)

| Phase | Azure OpenAI | Gemini | Savings |
|-------|--------------|--------|---------|
| Indexing | $0.15 | $0.15 | 0% |
| Specification | $0.25 | $0.002 | 99.2% |
| Design | $0.35 | $0.003 | 99.1% |
| Implementation | $0.50 | $0.005 | 99.0% |
| **Total** | **$1.25** | **$0.16** | **87.2%** |

### Large Project (100,000 LOC)

| Phase | Azure OpenAI | Gemini | Savings |
|-------|--------------|--------|---------|
| Indexing | $1.50 | $1.50 | 0% |
| Specification | $0.40 | $0.004 | 99.0% |
| Design | $0.60 | $0.006 | 99.0% |
| Implementation | $0.80 | $0.008 | 99.0% |
| **Total** | **$3.30** | **$1.52** | **53.9%** |

**Note**: Implementation costs scale with number of features, not just codebase size.

## Troubleshooting Cost Issues

### Unexpectedly High Costs

**Problem**: Costs are higher than expected

**Diagnosis**:
1. Check cost report for breakdown
2. Look for repeated operations
3. Review context size in prompts
4. Check for cache misses

**Solutions**:
- Enable embedding cache
- Reduce context size
- Use GPT-4 Turbo
- Optimize prompts

### Budget Exceeded

**Problem**: Hit budget limit unexpectedly

**Solutions**:
1. Review usage patterns
2. Identify high-cost operations
3. Implement cost optimizations
4. Increase budget if justified
5. Use cheaper models for non-critical tasks

### Cache Not Working

**Problem**: Embeddings regenerated every time

**Diagnosis**:
```bash
# Check cache directory
ls -la .dev_agent/embedding_cache/

# Check cache stats
uv run dev-agent cache-stats
```

**Solutions**:
- Ensure cache directory exists and is writable
- Check for code changes (invalidates cache)
- Verify model name hasn't changed
- Clear and rebuild cache if corrupted

## Provider Cost Management Integration

### Azure Cost Management

#### View Costs in Azure Portal

1. Navigate to your Azure OpenAI resource
2. Click "Cost Management" in the left menu
3. View detailed billing information
4. Set up budget alerts in Azure

#### Export Azure Cost Data

```bash
# Export Azure cost data
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --query "[?contains(instanceName, 'openai')]" \
  --output table
```

#### Set Up Azure Budget Alerts

1. Go to "Cost Management + Billing" in Azure Portal
2. Click "Budgets"
3. Create a new budget for your OpenAI resource
4. Set alert thresholds (e.g., 50%, 75%, 90%)
5. Configure email notifications

### Google Cloud Cost Management

#### View Gemini Costs in Google Cloud Console

1. Navigate to [Google Cloud Console](https://console.cloud.google.com/)
2. Go to "Billing" → "Cost breakdown"
3. Filter by "Generative AI" service
4. View detailed usage and costs

#### Set Up Google Cloud Budget Alerts

1. Go to "Billing" → "Budgets & alerts"
2. Create a new budget
3. Set scope to "Generative AI" services
4. Configure alert thresholds
5. Set up email notifications

#### Export Gemini Cost Data

```bash
# Export Google Cloud billing data
gcloud billing accounts list
gcloud billing projects describe PROJECT_ID
```

### Multi-Provider Cost Tracking

Track costs across both providers in dev-agent:

```python
from dev_agent.llm.cost_tracker import MultiProviderCostTracker

# Track costs across providers
tracker = MultiProviderCostTracker()

# Get combined report
report = tracker.get_combined_report()
print(f"Azure OpenAI: ${report['azure']:.2f}")
print(f"Gemini: ${report['gemini']:.2f}")
print(f"Total: ${report['total']:.2f}")
print(f"Savings vs Azure-only: ${report['savings']:.2f}")
```

## Best Practices

1. **Monitor regularly**: Check costs weekly
2. **Set budgets**: Define limits before starting
3. **Use cache**: Enable for all projects
4. **Optimize prompts**: Remove unnecessary context
5. **Choose right model**: Balance cost and quality
6. **Track by project**: Allocate costs appropriately
7. **Review patterns**: Identify optimization opportunities
8. **Test estimates**: Validate before large operations
9. **Document costs**: Track for future planning
10. **Stay updated**: Monitor Azure pricing changes

## Additional Resources

### Azure OpenAI Resources
- [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)
- [Azure Cost Management](https://learn.microsoft.com/en-us/azure/cost-management-billing/)
- [Azure OpenAI Best Practices](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/best-practices)

### Google Gemini Resources
- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Google Cloud Billing](https://cloud.google.com/billing/docs)
- [Gemini API Best Practices](https://ai.google.dev/docs/best_practices)

### General Resources
- [Token Counting Guide](https://platform.openai.com/tokenizer)
- [Provider Selection Guide](provider-selection.md)
- [Gemini Setup Guide](../configuration/gemini-setup.md)

## Next Steps

- [Provider Selection Guide](provider-selection.md) - Choose the right provider for your needs
- [Gemini Setup Guide](../configuration/gemini-setup.md) - Configure Gemini for cost savings
- [Azure OpenAI Setup](../configuration/azure-openai.md) - Configure Azure OpenAI
- [Gemini Usage Examples](../examples/gemini-usage.md) - See practical Gemini examples
- [API Documentation](../api/llm.md) - Explore the LLM integration API
