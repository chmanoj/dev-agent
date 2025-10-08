# Fixes for Three Critical Issues

## Issue #1: Token Limit Exceeded During Embedding Generation
**Error**: `Error code 400. message= this models maximum context length is 8192 tokens, however you requested 8241 tokens`

### Root Cause
Code chunks were not being validated against the Azure OpenAI embedding API token limit (8192 tokens for text-embedding-ada-002).

### Fix Applied
1. **Updated `CodeChunker.__init__`** to accept `max_tokens` parameter (default 8000 to stay under 8192 limit)
2. **Added `_validate_token_limits()` method** to check all chunks before embedding generation
3. **Added `_split_oversized_chunk()` method** to split chunks that exceed token limits
4. **Integrated tiktoken** for accurate token counting (falls back to character-based estimation if unavailable)

**Files Modified**:
- `dev_agent/indexing/code_chunker.py`

### How It Works
- After optimizing chunks, the chunker now validates each chunk's token count
- If a chunk exceeds 8000 tokens, it's split into smaller chunks line-by-line
- Each split chunk is validated to ensure it stays under the limit
- Warnings are logged when chunks need to be split

---

## Issue #2: Embedding Client Not Available in Specification Phase
**Error**: `specification phase failed: embedding_client is required`

### Root Cause
The `IndexingEngine` was being re-initialized in the specification phase without the `embedding_client` parameter, causing the `VectorDatabase` to fail initialization.

### Fix Applied
1. **Updated `PhaseManager.__init__`** to accept `embedding_client` and `cost_tracker` parameters
2. **Updated `WorkflowManager.__init__`** to accept and store `embedding_client`
3. **Modified all `IndexingEngine` initializations** in `PhaseManager` to pass `embedding_client` and `cost_tracker`
4. **Updated `PhaseManager` instantiations** in `WorkflowManager` to pass these parameters

**Files Modified**:
- `dev_agent/workflow/phase_manager.py`
- `dev_agent/workflow/workflow_manager.py`

### How It Works
- The embedding client is now passed through the entire workflow chain:
  - CLI → WorkflowManager → PhaseManager → IndexingEngine → VectorDatabase
- This ensures vector search capabilities are available in all phases
- The same embedding client instance is reused across phases for consistency

---

## Issue #3: Cost Tracking Shows $0.00 After Indexing
**Error**: Cost displayed as $0.00 despite generating many embeddings

### Root Cause
The `AzureEmbeddingClient` was not recording token usage with the `CostTracker` when generating embeddings.

### Fix Applied
1. **Updated `AzureEmbeddingClient.__init__`** to accept `cost_tracker` parameter
2. **Modified `_process_single_batch()` method** to record embedding costs after each batch
3. **Added cost tracking integration** that calls `cost_tracker.record_embedding()` with token usage

**Files Modified**:
- `dev_agent/llm/embeddings.py`

### How It Works
- After each batch of embeddings is generated, the client checks if a cost tracker is available
- If present, it records the token usage via `cost_tracker.record_embedding()`
- The cost tracker calculates costs based on Azure OpenAI pricing ($0.0001 per 1K tokens)
- Total cost is accumulated and displayed at the end of indexing

---

## Remaining Work

### CLI Integration
The CLI needs to be updated to pass `embedding_client` when creating `WorkflowManager`:

**Files to Update**:
- `dev_agent/cli/main.py` (4 locations)
- `dev_agent/cli/interactive_cli.py` (1 location)
- `dev_agent/cli/enhanced_cli.py` (1 location)

**Pattern to Apply**:
```python
# Before
workflow_manager = WorkflowManager(cli)

# After
from dev_agent.llm.embeddings import AzureEmbeddingClient

config = config_manager.get_config()
embedding_client = AzureEmbeddingClient(
    config.azure_openai,
    cost_tracker=cost_tracker  # if available
)

workflow_manager = WorkflowManager(
    cli,
    embedding_client=embedding_client,
    cost_tracker=cost_tracker  # if available
)
```

---

## Testing Recommendations

1. **Test Token Limit Handling**:
   - Index a codebase with very large files (>8000 tokens)
   - Verify chunks are split automatically
   - Check that no 400 errors occur during embedding generation

2. **Test Specification Phase**:
   - Complete indexing phase
   - Transition to specification phase
   - Verify no "embedding_client is required" error
   - Confirm vector search works for finding similar code

3. **Test Cost Tracking**:
   - Index a codebase with multiple files
   - Check that cost is displayed at end of indexing
   - Verify cost is non-zero and reasonable
   - Check cost report shows embedding token usage

---

## Benefits

1. **Robustness**: System now handles large code files gracefully
2. **Consistency**: Embedding client is available throughout all workflow phases
3. **Transparency**: Users can see actual API costs for embeddings
4. **Debugging**: Better error messages and logging for troubleshooting
