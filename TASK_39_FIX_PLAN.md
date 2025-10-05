# Task 39: Detailed Fix Plan

## Phase 1: Critical Fixes

### Fix 1: embedding_client Parameter (15 tests)

**Problem:** Tests creating `IndexingEngine` without `embedding_client` parameter

**Solution:** Create a mock embedding client fixture and update all tests

**Files to modify:**
1. `tests/conftest.py` - Add mock embedding client fixture
2. `tests/test_functionality_integration.py` - Use fixture
3. `tests/test_indexing_engine_performance.py` - Use fixture
4. `tests/test_large_codebase_integration.py` - Use fixture

**Implementation:**
```python
# In conftest.py
@pytest.fixture
def mock_embedding_client():
    """Create a mock embedding client for testing."""
    client = AsyncMock(spec=IEmbeddingClient)
    client.embed_text = AsyncMock(return_value=[0.1] * 1536)
    client.embed_batch = AsyncMock(return_value=[[0.1] * 1536])
    client.dimension = 1536
    return client
```

---

### Fix 2: Model Initialization (30 tests)

**Problem:** `CodeContext` and `RequirementEvidence` model signatures changed

**Current Errors:**
- `TypeError: CodeContext.__init__() got an unexpected keyword argument 'task_id'`
- `TypeError: RequirementEvidence.__init__() got an unexpected keyword argument 'code_examples'`

**Solution:** Check model definitions and update test fixtures

**Files to check:**
1. `dev_agent/models/analysis.py` - Check CodeContext
2. `dev_agent/models/specification.py` - Check RequirementEvidence

**Files to modify:**
1. `tests/test_codebase_analyzer.py`
2. `tests/test_specification_workflow.py`

---

### Fix 3: Framework Detectors (9 tests)

**Problem:** JSON parsing using `eval()` instead of `json.loads()`

**Error:** `NameError: name 'true' is not defined`

**Solution:** Replace `eval()` with `json.loads()` in React detector

**Files to modify:**
1. `dev_agent/analysis/framework_detectors.py`

**Implementation:**
```python
# Replace:
config = eval(content)  # ❌ WRONG

# With:
config = json.loads(content)  # ✅ CORRECT
```

---

### Fix 4: Interactive CLI (7 tests)

**Problem:** Console/print mocking issues

**Solution:** Update mocking strategy for Rich console

**Files to modify:**
1. `tests/test_interactive_cli.py`

---

## Phase 2: Integration Fixes

### Fix 5: End-to-End Workflows (7 tests)

**Problem:** `FileNotFoundError: .../src/api/routes/users.py`

**Solution:** Fix file generation paths or update test expectations

**Files to modify:**
1. `tests/test_end_to_end_workflow.py`

---

### Fix 6: CLI Integration (7 tests)

**Problem:** Azure status and cost report commands failing

**Files to modify:**
1. `tests/test_cli_integration.py`
2. `tests/test_cli_main.py`
3. `tests/test_validate_command.py`

---

## Phase 3: Performance & Coverage

### Fix 7: Performance Tests (22 tests)

**Problem:** Performance targets too aggressive

**Solution:** Adjust targets or optimize code

**Files to modify:**
1. `tests/test_performance.py`
2. `tests/test_indexing_engine_performance.py`
3. `tests/test_performance_benchmarks.py`

---

## Execution Order

1. ✅ Language parsers (DONE)
2. ⏭️ embedding_client fixture
3. ⏭️ Model initialization
4. ⏭️ Framework detectors
5. ⏭️ Interactive CLI
6. ⏭️ End-to-end workflows
7. ⏭️ CLI integration
8. ⏭️ Performance tests
9. ⏭️ Coverage improvements
