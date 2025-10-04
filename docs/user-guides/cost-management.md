# Cost Management Guide

## Overview

dev-agent uses Azure OpenAI APIs, which charge based on token usage. This guide helps you understand, track, and optimize your API costs while using dev-agent effectively.

## Understanding Azure OpenAI Pricing

### Token-Based Pricing

Azure OpenAI charges per 1,000 tokens. A token is roughly 4 characters or 0.75 words in English.

### Current Pricing (as of 2024)

**GPT-4 Models**:
- Input tokens: $0.03 per 1K tokens
- Output tokens: $0.06 per 1K tokens

**GPT-4 Turbo**:
- Input tokens: $0.01 per 1K tokens
- Output tokens: $0.03 per 1K tokens

**Embeddings (text-embedding-ada-002)**:
- All tokens: $0.0001 per 1K tokens

> **Note**: Prices may vary by region and Azure subscription. Check your Azure portal for exact pricing.

### What Counts as Tokens?

**Input Tokens** (Prompt):
- Your feature description
- Retrieved code context
- System prompts
- Previous conversation history

**Output Tokens** (Completion):
- Generated specifications
- Design documents
- Implementation tasks
- Code generation

**Embedding Tokens**:
- Code chunks during indexing
- Query text during search

## Cost Breakdown by Phase

### Typical Costs

Here's what you can expect for a medium-sized project (10K lines of code):

| Phase | Operation | Tokens | Cost |
|-------|-----------|--------|------|
| **Indexing** | Parse & embed code | 50,000 | $0.05 |
| **Specification** | Generate spec | 5,000 input<br>3,000 output | $0.33 |
| **Design** | Generate design | 6,000 input<br>4,000 output | $0.42 |
| **Implementation** | Generate tasks | 4,000 input<br>2,000 output | $0.24 |
| **Code Generation** | Generate code (per task) | 2,000 input<br>1,000 output | $0.12 |

**Total for one feature**: ~$1.16 (excluding code generation)

### Cost Factors

**Codebase Size**:
- Small (< 5K lines): $0.02 - $0.10 for indexing
- Medium (5K - 50K lines): $0.10 - $0.50 for indexing
- Large (> 50K lines): $0.50 - $2.00 for indexing

**Feature Complexity**:
- Simple feature: $0.30 - $0.60
- Medium feature: $0.60 - $1.20
- Complex feature: $1.20 - $3.00

**Iterations**:
- Each rejection and regeneration adds 50-100% of phase cost
- Approval on first try minimizes costs

## Tracking Costs

### Real-Time Cost Display

dev-agent shows costs during operations:

```bash
dev-agent phase specification

# Output includes:
💰 Cost Summary:
   Prompt tokens: 3,456
   Completion tokens: 2,134
   Total tokens: 5,590
   Estimated cost: $0.18
```

### Cost Report Command

View detailed cost breakdown:

```bash
# Overall cost report
dev-agent cost

# Output:
╭─────────────────────────────────────────────────────────────╮
│                     Cost Report                              │
├─────────────────────────────────────────────────────────────┤
│ Phase            │ Tokens      │ Cost      │ Percentage     │
├─────────────────────────────────────────────────────────────┤
│ Indexing         │ 50,234      │ $0.05     │ 4.3%          │
│ Specification    │ 5,590       │ $0.18     │ 15.5%         │
│ Design           │ 10,123      │ $0.42     │ 36.2%         │
│ Implementation   │ 6,045       │ $0.24     │ 20.7%         │
│ Code Generation  │ 8,234       │ $0.27     │ 23.3%         │
├─────────────────────────────────────────────────────────────┤
│ Total            │ 80,226      │ $1.16     │ 100%          │
╰─────────────────────────────────────────────────────────────╯

Total API Calls: 47
Average Cost per Call: $0.025
```

### Phase-Specific Costs

```bash
# Cost for specific phase
dev-agent cost --phase specification

# Export cost data
dev-agent cost --export cost-report.json
```

### Cost History

```bash
# View cost trends over time
dev-agent cost --history

# Output:
Cost History (Last 30 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2024-01-15: $2.34 (3 features)
2024-01-14: $1.87 (2 features)
2024-01-13: $0.45 (1 feature)
...

Total (30 days): $45.67
Average per day: $1.52
```

## Cost Optimization Strategies

### 1. Use Embedding Cache

**Problem**: Re-indexing unchanged code wastes tokens

**Solution**: Enable embedding cache

```bash
# Enable cache (default)
dev-agent config set embedding_cache true

# Cache location
~/.dev_agent/cache/embeddings/
```

**Savings**: 90-100% on repeated indexing

### 2. Exclude Unnecessary Files

**Problem**: Indexing generated files, dependencies, or documentation

**Solution**: Configure exclusion patterns

```json
// .dev_agent/config.json
{
  "exclude_patterns": [
    "node_modules/",
    "venv/",
    ".venv/",
    "dist/",
    "build/",
    "*.min.js",
    "*.min.css",
    "docs/site/",
    "coverage/",
    "__pycache__/"
  ]
}
```

**Savings**: 30-70% on indexing costs

### 3. Approve on First Try

**Problem**: Each rejection and regeneration doubles phase cost

**Solution**: Provide detailed, clear requirements upfront

**Example**:
```bash
# ❌ Vague (likely needs iteration)
"Add authentication"

# ✅ Specific (likely approved first try)
"Add JWT-based authentication with:
- Email/password login
- Token refresh mechanism
- Role-based access control (admin, user, guest)
- Password reset via email
- Following existing auth patterns in auth/session_manager.py"
```

**Savings**: 50% per phase

### 4. Batch Related Features

**Problem**: Indexing cost paid for each feature

**Solution**: Work on related features in one session

```bash
# Instead of:
dev-agent init project  # Index
# Work on feature 1
dev-agent init project  # Re-index
# Work on feature 2

# Do this:
dev-agent init project  # Index once
# Work on feature 1
# Work on feature 2 (uses same index)
```

**Savings**: Eliminates redundant indexing

### 5. Use Incremental Indexing

**Problem**: Full re-index after small changes

**Solution**: Use incremental indexing

```bash
# Only index changed files
dev-agent index --incremental

# Or configure automatic incremental indexing
dev-agent config set incremental_indexing true
```

**Savings**: 80-95% on re-indexing

### 6. Optimize Context Window

**Problem**: Including too much context in prompts

**Solution**: Configure context limits

```json
// .dev_agent/config.json
{
  "max_context_chunks": 5,  // Default: 10
  "max_chunk_size": 500      // Default: 1000
}
```

**Savings**: 20-40% on generation phases

### 7. Use Smaller Models for Simple Tasks

**Problem**: Using GPT-4 for everything

**Solution**: Configure model selection

```bash
# Use GPT-3.5 Turbo for simple tasks
dev-agent config set simple_task_model gpt-35-turbo

# Use GPT-4 only for complex tasks
dev-agent config set complex_task_model gpt-4
```

**Savings**: 60-70% on simple tasks

### 8. Set Budget Limits

**Problem**: Unexpected high costs

**Solution**: Configure budget warnings

```bash
# Set daily budget limit
dev-agent config set daily_budget 10.00

# Set per-feature budget
dev-agent config set feature_budget 2.00

# Enable warnings
dev-agent config set budget_warnings true
```

**Result**: Prevents cost overruns

## Budget Management

### Setting Budgets

```bash
# Configure budget limits
dev-agent config set daily_budget 10.00
dev-agent config set weekly_budget 50.00
dev-agent config set monthly_budget 200.00

# Set per-operation limits
dev-agent config set max_cost_per_phase 1.00
```

### Budget Warnings

When approaching limits:

```
⚠️  Budget Warning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Daily budget: $8.45 / $10.00 (84.5%)
This operation will cost approximately $0.42

Continue? [y/N]
```

### Budget Exceeded

When limits are reached:

```
🛑 Budget Exceeded
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Daily budget exceeded: $10.23 / $10.00

Operation blocked. Options:
1. Increase budget: dev-agent config set daily_budget 15.00
2. Wait until tomorrow (budget resets at midnight UTC)
3. Review costs: dev-agent cost --detailed
```

## Cost Analysis

### Detailed Cost Breakdown

```bash
# Detailed analysis
dev-agent cost --detailed

# Output:
╭─────────────────────────────────────────────────────────────────────────────╮
│                          Detailed Cost Analysis                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Operation                    │ Calls │ Tokens    │ Cost    │ Avg/Call      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Embedding Generation         │ 15    │ 50,234    │ $0.05   │ $0.003        │
│ Specification Generation     │ 2     │ 11,180    │ $0.36   │ $0.180        │
│ Design Generation            │ 2     │ 20,246    │ $0.84   │ $0.420        │
│ Implementation Generation    │ 1     │ 6,045     │ $0.24   │ $0.240        │
│ Code Generation              │ 8     │ 24,702    │ $0.81   │ $0.101        │
│ Context Retrieval            │ 19    │ 3,456     │ $0.00   │ $0.000        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Total                        │ 47    │ 115,863   │ $2.30   │ $0.049        │
╰─────────────────────────────────────────────────────────────────────────────╯

Most Expensive Operations:
1. Design Generation (2 calls): $0.84 (36.5%)
2. Code Generation (8 calls): $0.81 (35.2%)
3. Specification Generation (2 calls): $0.36 (15.7%)

Optimization Opportunities:
• Specification regenerated once (cost: $0.18) - improve initial requirements
• Design regenerated once (cost: $0.42) - review before approval
• 8 code generation calls - consider batching related tasks
```

### Cost Trends

```bash
# Analyze cost trends
dev-agent cost --trends

# Output:
Cost Trends
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Average cost per feature: $1.45
Trend: ↓ 12% (improving)

Cost by feature complexity:
• Simple features: $0.45 avg (15 features)
• Medium features: $1.23 avg (8 features)
• Complex features: $2.87 avg (3 features)

Most efficient phase: Indexing (95% cache hit rate)
Least efficient phase: Specification (40% regeneration rate)

Recommendations:
1. Improve specification requirements to reduce regenerations
2. Continue using embedding cache (saving $0.15 per feature)
3. Consider batching simple features (potential 20% savings)
```

## Cost Comparison

### vs. Manual Development

| Task | Manual Time | Manual Cost* | dev-agent Cost | Savings |
|------|-------------|--------------|----------------|---------|
| Write specification | 2 hours | $100 | $0.30 | 99.7% |
| Create design doc | 3 hours | $150 | $0.40 | 99.7% |
| Plan implementation | 1 hour | $50 | $0.20 | 99.6% |
| Generate boilerplate | 2 hours | $100 | $0.15 | 99.9% |
| **Total** | **8 hours** | **$400** | **$1.05** | **99.7%** |

*Assuming $50/hour developer rate

### vs. Other AI Tools

| Tool | Cost Model | Typical Feature Cost | Notes |
|------|------------|---------------------|-------|
| **dev-agent** | Pay-per-use | $1.00 - $2.00 | Azure OpenAI pricing |
| GitHub Copilot | $10/month | $0.33/feature* | Subscription model |
| ChatGPT Plus | $20/month | $0.67/feature* | Subscription model |
| Claude Pro | $20/month | $0.67/feature* | Subscription model |

*Assuming 30 features per month

**dev-agent advantages**:
- Pay only for what you use
- No monthly subscription
- Enterprise-grade security (Azure)
- Codebase-specific context
- Structured workflow

## Best Practices

### Before Starting

1. **Review Configuration**
   ```bash
   dev-agent config show
   ```

2. **Set Budget Limits**
   ```bash
   dev-agent config set daily_budget 10.00
   ```

3. **Enable Caching**
   ```bash
   dev-agent config set embedding_cache true
   ```

4. **Configure Exclusions**
   ```bash
   # Edit .dev_agent/config.json
   ```

### During Development

1. **Monitor Costs**
   ```bash
   dev-agent status  # Shows current session cost
   ```

2. **Approve Carefully**
   - Review specifications thoroughly
   - Provide detailed feedback if rejecting
   - Avoid multiple regenerations

3. **Batch Operations**
   - Work on related features together
   - Reuse indexing across features

### After Completion

1. **Review Cost Report**
   ```bash
   dev-agent cost --detailed
   ```

2. **Identify Optimization Opportunities**
   - High regeneration rates
   - Expensive operations
   - Cache misses

3. **Update Configuration**
   - Adjust exclusion patterns
   - Optimize context limits
   - Update budget limits

## Troubleshooting

### High Indexing Costs

**Symptom**: Indexing costs > $1.00

**Diagnosis**:
```bash
dev-agent cost --phase indexing --detailed
```

**Solutions**:
1. Add exclusion patterns for generated files
2. Remove documentation sites from indexing
3. Exclude test fixtures and mock data
4. Enable incremental indexing

### Frequent Regenerations

**Symptom**: Multiple regenerations per phase

**Diagnosis**:
```bash
dev-agent cost --trends
# Look for high regeneration rates
```

**Solutions**:
1. Provide more detailed initial requirements
2. Reference specific code examples
3. Review generated content before rejecting
4. Use interactive mode for clarification

### Budget Overruns

**Symptom**: Exceeding budget limits

**Diagnosis**:
```bash
dev-agent cost --history
# Identify cost spikes
```

**Solutions**:
1. Review and adjust budget limits
2. Optimize configuration settings
3. Batch related features
4. Use cost estimation before operations

## Cost Estimation

### Estimate Before Running

```bash
# Estimate indexing cost
dev-agent estimate index /path/to/project

# Output:
Indexing Cost Estimate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files to index: 156
Estimated tokens: 45,000 - 55,000
Estimated cost: $0.05 - $0.06

Proceed? [y/N]
```

```bash
# Estimate feature cost
dev-agent estimate feature "Add user authentication"

# Output:
Feature Cost Estimate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Complexity: Medium
Estimated phases:
• Specification: $0.20 - $0.35
• Design: $0.30 - $0.50
• Implementation: $0.15 - $0.25

Total estimate: $0.65 - $1.10

Proceed? [y/N]
```

## Advanced Cost Management

### Custom Cost Tracking

```python
# Track costs in your own system
import json

# Export cost data
cost_data = json.load(open('.dev_agent/cost_report.json'))

# Integrate with your billing system
for operation in cost_data['operations']:
    your_billing_system.record_cost(
        service='dev-agent',
        operation=operation['type'],
        cost=operation['cost'],
        timestamp=operation['timestamp']
    )
```

### Cost Allocation

```bash
# Tag operations for cost allocation
dev-agent config set cost_tag "project:auth-feature"

# View costs by tag
dev-agent cost --by-tag

# Output:
Cost by Tag
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

project:auth-feature: $2.34
project:api-refactor: $1.87
project:ui-updates: $0.95
```

## Next Steps

- Learn about [Best Practices](best-practices.md)
- Explore [Advanced Usage](advanced-usage.md)
- Review [Four-Phase Workflow](four-phase-workflow.md)
- Check [CLI Reference](../cli-reference/commands.md)
