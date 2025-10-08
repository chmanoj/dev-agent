# Testing Guide for Three Critical Fixes

## Quick Test Commands

### Test 1: Token Limit Handling
```bash
# Index a large codebase
uv run dev-agent init /path/to/large/codebase

# What to look for:
# ✅ No "Error code 400" messages
# ✅ Warnings about splitting oversized chunks (if any large files)
# ✅ Successful completion of indexing
# ✅ Non-zero cost displayed at end
```

### Test 2: Specification Phase Transition
```bash
# Resume project and move to specification
uv run dev-agent resume /path/to/project

# What to look for:
# ✅ No "embedding_client is required" error
# ✅ Can successfully transition to specification phase
# ✅ Vector search works (finds similar code)
# ✅ Specification generation completes
```

### Test 3: Cost Tracking
```bash
# Check cost report
uv run dev-agent cost /path/to/project

# What to look for:
# ✅ Non-zero embedding costs displayed
# ✅ Token usage statistics shown
# ✅ Breakdown by phase (if multiple phases completed)
# ✅ Reasonable cost values (not $0.00)
```

## Expected Behavior

### Before Fixes
❌ Error: "this models maximum context length is 8192 tokens, however you requested 8241 tokens"
❌ Error: "specification phase failed: embedding_client is required"
❌ Cost: $0.00 (incorrect)

### After Fixes
✅ Large chunks automatically split
✅ All phases work without errors
✅ Cost: $X.XX (accurate, non-zero)

## Detailed Test Scenarios

### Scenario 1: Large File Handling
```bash
# Create a test file with >8000 tokens
cat > test_large.py << 'EOF'
# [Insert a very large Python file here]
EOF

# Index it
uv run dev-agent init .

# Expected output:
# "Chunk from test_large.py:1-500 exceeds token limit (8241 > 8000). Splitting..."
# "Split oversized chunk into 2 smaller chunks"
# "✅ Indexing Complete!"
```

### Scenario 2: Full Workflow
```bash
# 1. Initialize project
uv run dev-agent init /path/to/project

# Expected: Successful indexing with cost displayed

# 2. Resume and check status
uv run dev-agent resume /path/to/project

# Expected: Shows current phase, no errors

# 3. Move to specification phase
# (Follow prompts in interactive mode)

# Expected: Specification generation works, uses vector search

# 4. Check costs
uv run dev-agent cost /path/to/project

# Expected: Shows embedding costs from indexing
```

### Scenario 3: Error Recovery
```bash
# Test without Azure OpenAI configured
unset AZURE_OPENAI_API_KEY
uv run dev-agent init .

# Expected:
# "Warning: Could not initialize embedding client"
# "Some features may be limited"
# System continues with limited functionality
```

## Verification Checklist

- [ ] No 400 errors during indexing
- [ ] Large files (>8000 tokens) are handled
- [ ] Specification phase works after indexing
- [ ] Cost tracking shows non-zero values
- [ ] Vector search works in all phases
- [ ] Error messages are helpful
- [ ] System degrades gracefully without Azure OpenAI

## Performance Expectations

### Indexing Performance
- **Small project** (<100 files): 10-30 seconds
- **Medium project** (100-1000 files): 1-5 minutes
- **Large project** (1000+ files): 5-20 minutes

### Cost Expectations
- **Embeddings**: ~$0.0001 per 1K tokens
- **Typical file**: ~500-2000 tokens
- **100 files**: ~$0.01-0.05
- **1000 files**: ~$0.10-0.50

## Troubleshooting

### Issue: Still seeing token limit errors
**Solution**: Check that code_chunker.py changes were applied correctly

### Issue: Embedding client not found
**Solution**: Verify Azure OpenAI configuration:
```bash
uv run dev-agent azure status
```

### Issue: Cost still shows $0.00
**Solution**: Check that embedding client has cost_tracker:
```bash
# In Python console:
from dev_agent.config import ConfigManager
from dev_agent.llm.embeddings import AzureEmbeddingClient
from dev_agent.llm.cost_tracker import CostTracker

config = ConfigManager().get_config()
tracker = CostTracker()
client = AzureEmbeddingClient(config.azure_openai, cost_tracker=tracker)
# Should work without errors
```

## Success Criteria

All three issues are fixed when:
1. ✅ Can index large codebases without 400 errors
2. ✅ Can transition to specification phase without errors
3. ✅ Cost tracking shows accurate non-zero values

## Reporting Issues

If you encounter problems:
1. Check the logs in `.dev_agent/logs/`
2. Run with `--verbose` flag for detailed output
3. Verify Azure OpenAI configuration
4. Check that all files were updated correctly

## Additional Resources

- `QUICK_FIX_SUMMARY.md` - Overview of all fixes
- `FIXES_FOR_THREE_ISSUES.md` - Detailed technical explanation
- `CLI_INTEGRATION_COMPLETE.md` - CLI changes documentation
