# Cost Management Guide

This guide helps you understand, track, and optimize Azure OpenAI costs when using dev-agent.

## Understanding Azure OpenAI Pricing

Azure OpenAI charges based on token usage. Tokens are pieces of text that the model processes - roughly 4 characters or 0.75 words per token.

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

| Phase | Operation | Typical Tokens | Estimated Cost |
|-------|-----------|----------------|----------------|
| **Indexing** | Embed 1,000 code chunks | ~500,000 | $0.05 |
| **Specification** | Generate spec with context | ~3,000 prompt + 2,000 completion | $0.21 |
| **Design** | Generate design with context | ~4,000 prompt + 3,000 completion | $0.30 |
| **Implementation** | Generate code with context | ~2,000 prompt + 1,500 completion | $0.15 |

**Total for typical feature**: ~$0.70 - $1.50

**Note**: Costs vary significantly based on:
- Codebase size
- Feature complexity
- Amount of context included
- Model used (GPT-4 vs GPT-4 Turbo)

## Tracking Costs in dev-agent

### Automatic Cost Tracking

dev-agent automatically tracks token usage and costs for all operations:

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
# By Operation Type:
#   Embeddings:    487,234 tokens  ($0.05)
#   Completions:   12,450 tokens   ($0.62)
#   Total:         499,684 tokens  ($0.67)
# 
# By Phase:
#   Indexing:      487,234 tokens  ($0.05)
#   Specification: 5,230 tokens    ($0.21)
#   Design:        7,220 tokens    ($0.30)
#   
# Total Estimated Cost: $0.67
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

### 3. Use Appropriate Models

Choose the right model for each task:

| Task | Recommended Model | Cost Savings |
|------|-------------------|--------------|
| Simple code generation | GPT-4 Turbo | 67% vs GPT-4 |
| Complex architecture | GPT-4 | Best quality |
| Code embeddings | text-embedding-ada-002 | Only option |

**Configuration**:
```bash
# Use GPT-4 Turbo for cost savings
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4-turbo"

# Or configure per-operation
# (future enhancement)
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

Configure budget warnings to avoid surprises:

```bash
# Set budget warning threshold
export AZURE_OPENAI_BUDGET_WARNING="10.00"  # Warn at $10

# Set hard budget limit
export AZURE_OPENAI_BUDGET_LIMIT="50.00"  # Stop at $50
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

```
Indexing:        $0.02
Specification:   $0.15
Design:          $0.20
Implementation:  $0.30
--------------------------
Total:           $0.67
```

### Medium Project (10,000 LOC)

```
Indexing:        $0.15
Specification:   $0.25
Design:          $0.35
Implementation:  $0.50
--------------------------
Total:           $1.25
```

### Large Project (100,000 LOC)

```
Indexing:        $1.50
Specification:   $0.40
Design:          $0.60
Implementation:  $0.80
--------------------------
Total:           $3.30
```

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

## Azure Cost Management Integration

### View Costs in Azure Portal

1. Navigate to your Azure OpenAI resource
2. Click "Cost Management" in the left menu
3. View detailed billing information
4. Set up budget alerts in Azure

### Export Cost Data

```bash
# Export Azure cost data
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --query "[?contains(instanceName, 'openai')]" \
  --output table
```

### Set Up Azure Budget Alerts

1. Go to "Cost Management + Billing" in Azure Portal
2. Click "Budgets"
3. Create a new budget for your OpenAI resource
4. Set alert thresholds (e.g., 50%, 75%, 90%)
5. Configure email notifications

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

- [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)
- [Azure Cost Management](https://learn.microsoft.com/en-us/azure/cost-management-billing/)
- [Token Counting Guide](https://platform.openai.com/tokenizer)
- [Azure OpenAI Best Practices](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/best-practices)

## Next Steps

- [Azure OpenAI Setup](../configuration/azure-openai.md) - Configure Azure OpenAI
- [Usage Examples](../examples/azure-setup.md) - See practical examples
- [Troubleshooting Guide](../configuration/troubleshooting.md) - Solve common issues
- [API Documentation](../api/llm.md) - Explore the LLM integration API
