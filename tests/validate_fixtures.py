#!/usr/bin/env python3
"""Validate that conftest.py fixtures are properly defined.

This script checks that all fixtures in conftest.py are syntactically correct
and can be imported without errors.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_imports():
    """Validate that conftest fixtures can be imported."""
    print("Validating conftest.py imports...")
    
    try:
        # Import conftest module
        import tests.conftest as conftest
        print("✅ conftest.py imported successfully")
        
        # Check for key fixtures
        fixtures = [
            'azure_config',
            'temp_cache_dir',
            'mock_azure_openai_client',
            'mock_streaming_response',
            'mock_llm_client',
            'mock_embedding_client',
            'mock_cost_tracker',
            'cost_tracker_no_budget',
            'mock_token_counter',
            'token_counter_gpt4_turbo',
            'token_counter_gpt35',
            'sample_code_text',
            'sample_code_chunks',
            'sample_embeddings',
        ]
        
        missing_fixtures = []
        for fixture_name in fixtures:
            if not hasattr(conftest, fixture_name):
                missing_fixtures.append(fixture_name)
        
        if missing_fixtures:
            print(f"❌ Missing fixtures: {', '.join(missing_fixtures)}")
            return False
        
        print(f"✅ All {len(fixtures)} key fixtures are defined")
        
        # Check for helper functions
        helpers = [
            'create_mock_completion_response',
            'create_mock_embedding_response',
            'create_mock_streaming_chunks',
        ]
        
        missing_helpers = []
        for helper_name in helpers:
            if not hasattr(conftest, helper_name):
                missing_helpers.append(helper_name)
        
        if missing_helpers:
            print(f"❌ Missing helper functions: {', '.join(missing_helpers)}")
            return False
        
        print(f"✅ All {len(helpers)} helper functions are defined")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import conftest.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def validate_fixture_types():
    """Validate that fixtures return expected types."""
    print("\nValidating fixture types...")
    
    try:
        from tests.conftest import (
            create_mock_completion_response,
            create_mock_embedding_response,
            create_mock_streaming_chunks,
        )
        
        # Test completion response builder
        completion_response = create_mock_completion_response()
        assert hasattr(completion_response, 'choices')
        assert hasattr(completion_response, 'usage')
        print("✅ create_mock_completion_response works correctly")
        
        # Test embedding response builder
        embedding_response = create_mock_embedding_response(count=3)
        assert hasattr(embedding_response, 'data')
        assert len(embedding_response.data) == 3
        print("✅ create_mock_embedding_response works correctly")
        
        # Test streaming chunks builder
        chunks = create_mock_streaming_chunks(["Hello", "World"])
        assert len(chunks) == 2
        print("✅ create_mock_streaming_chunks works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Fixture type validation failed: {e}")
        return False


def main():
    """Run all validations."""
    print("=" * 60)
    print("Validating conftest.py fixtures")
    print("=" * 60)
    
    results = []
    
    # Run validations
    results.append(("Import validation", validate_imports()))
    results.append(("Type validation", validate_fixture_types()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All validations passed!")
        return 0
    else:
        print("\n❌ Some validations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
