#!/usr/bin/env python3
"""Test script to verify task 5 implementation."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_workflow_manager_initialization():
    """Test that WorkflowManager initializes LLM components correctly."""
    from dev_agent.cli.interactive_cli import InteractiveCLI
    from dev_agent.workflow.workflow_manager import WorkflowManager
    
    print("✓ Imports successful")
    
    # Create a CLI interface
    cli = InteractiveCLI()
    
    # Create WorkflowManager (should initialize LLM components)
    workflow_manager = WorkflowManager(
        cli_interface=cli,
        embedding_client=None,  # No embedding client for this test
    )
    
    print("✓ WorkflowManager created successfully")
    
    # Check that LLM component attributes exist
    assert hasattr(workflow_manager, 'llm_client'), "Missing llm_client attribute"
    assert hasattr(workflow_manager, 'token_counter'), "Missing token_counter attribute"
    assert hasattr(workflow_manager, 'vector_db'), "Missing vector_db attribute"
    
    print("✓ LLM component attributes exist")
    
    # Check that _initialize_llm_components method exists
    assert hasattr(workflow_manager, '_initialize_llm_components'), "Missing _initialize_llm_components method"
    
    # Check that _initialize_vector_database method exists
    assert hasattr(workflow_manager, '_initialize_vector_database'), "Missing _initialize_vector_database method"
    
    print("✓ Initialization methods exist")
    
    # If Azure OpenAI is not configured, components should be None
    # If it is configured, they should be initialized
    if workflow_manager.llm_client is None:
        print("ℹ Azure OpenAI not configured - LLM components are None (expected)")
    else:
        print("✓ Azure OpenAI configured - LLM components initialized")
        assert workflow_manager.token_counter is not None, "token_counter should be initialized"
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_workflow_manager_initialization()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
