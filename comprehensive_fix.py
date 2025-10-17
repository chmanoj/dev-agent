#!/usr/bin/env python3
"""Comprehensive fix for indexing, framework detection, and code generation issues."""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    """Main fix function."""
    
    # Load environment variables
    env_file = Path("gemini.export.txt")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    key_value = line[7:]  # Remove "export "
                    if "=" in key_value:
                        key, value = key_value.split("=", 1)
                        os.environ[key] = value
    
    print("🔧 Comprehensive Fix for dev-agent Issues")
    print("=" * 50)
    
    # 1. Test framework detection
    print("\n1. Testing Framework Detection...")
    
    try:
        from dev_agent.analysis.framework_detector import FrameworkDetector
        from dev_agent.models.enums import LanguageType
        
        detector = FrameworkDetector()
        test_app_path = Path("test-app")
        
        # Detect frameworks
        frameworks = detector.detect_frameworks(test_app_path, LanguageType.PYTHON)
        print(f"   Detected frameworks: {[f.value for f in frameworks]}")
        
        # Check if Streamlit is detected
        from dev_agent.models.enums import FrameworkType
        if FrameworkType.STREAMLIT in frameworks:
            print("   ✅ Streamlit correctly detected!")
        else:
            print("   ❌ Streamlit not detected - checking dependencies...")
            
            # Check pyproject.toml
            pyproject_file = test_app_path / "pyproject.toml"
            if pyproject_file.exists():
                with open(pyproject_file) as f:
                    content = f.read()
                    if "streamlit" in content.lower():
                        print("   ⚠️  Streamlit found in pyproject.toml but not detected by framework detector")
                        
                        # Let's debug the dependency detection
                        dependencies = detector._detect_python_dependencies(test_app_path)
                        print(f"   Debug: Detected Python dependencies: {[d.value for d in dependencies]}")
        
    except Exception as e:
        print(f"   ❌ Error in framework detection: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Test indexing with embeddings
    print("\n2. Testing Indexing with Embeddings...")
    
    try:
        from dev_agent.llm import create_embedding_client
        from dev_agent.indexing.indexing_engine import IndexingEngine
        
        # Create embedding client
        embedding_client = create_embedding_client()
        print(f"   ✅ Created embedding client: {type(embedding_client).__name__}")
        
        # Test embedding generation
        test_texts = [
            "import streamlit as st\nst.title('Hello World')",
            "def create_joke_page():\n    st.write('Joke here')",
            "st.sidebar.success('Navigation')"
        ]
        
        embeddings = await embedding_client.embed_batch(test_texts)
        print(f"   ✅ Generated {len(embeddings)} test embeddings")
        
        # Re-index the test project
        print("   Re-indexing test project...")
        
        # Remove existing index
        index_path = test_app_path / ".dev_agent" / "index"
        if index_path.exists():
            import shutil
            shutil.rmtree(index_path)
            print("   ✅ Removed existing index")
        
        # Create new indexing engine
        engine = IndexingEngine(
            project_path=str(test_app_path),
            embedding_client=embedding_client
        )
        
        # Build index
        result = engine.build_index()
        print(f"   ✅ Indexing completed successfully")
        print(f"   ✅ Generated {result.embeddings_count} embeddings")
        print(f"   ✅ AST index has {len(result.ast_index.functions)} functions")
        
        # Test vector search
        if result.embeddings_count > 0:
            matches = await engine.vector_db.query_similar(
                query_text="streamlit page with title and content",
                k=3,
                min_similarity=0.1
            )
            print(f"   ✅ Vector search found {len(matches)} matches")
            
            for i, match in enumerate(matches[:2]):
                print(f"     Match {i+1}: {match.chunk.file_path} (similarity: {match.similarity_score:.2f})")
        
    except Exception as e:
        print(f"   ❌ Error in indexing: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Test project state and framework storage
    print("\n3. Testing Project State and Framework Storage...")
    
    try:
        from dev_agent.workflow.workflow_manager import WorkflowManager
        from dev_agent.cli.enhanced_cli import EnhancedCLI
        from dev_agent.state.state_manager import StateManager
        
        # Create CLI interface (mock)
        class MockCLI:
            def display_message(self, message):
                print(f"   CLI: {message}")
            def request_approval(self, message):
                return True
        
        cli = MockCLI()
        
        # Create workflow manager
        workflow_manager = WorkflowManager(cli_interface=cli)
        
        # Initialize for test project
        await workflow_manager.initialize_project("test-app")
        
        # Check if frameworks were detected and stored
        state_manager = StateManager()
        project_state = state_manager.load_project_state()
        
        if project_state and project_state.detected_frameworks:
            print(f"   ✅ Frameworks stored in project state: {[f.value for f in project_state.detected_frameworks]}")
            
            if any(f.value == "streamlit" for f in project_state.detected_frameworks):
                print("   ✅ Streamlit correctly stored in project state!")
            else:
                print("   ❌ Streamlit not found in project state")
        else:
            print("   ❌ No frameworks found in project state")
        
    except Exception as e:
        print(f"   ❌ Error in project state: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Test task generation with correct framework
    print("\n4. Testing Task Generation with Correct Framework...")
    
    try:
        # This would require a full workflow run, so let's just check the logic
        print("   ℹ️  Task generation test requires full workflow - check manually")
        print("   ℹ️  Expected: Tasks should be Streamlit-specific, not Django")
        
    except Exception as e:
        print(f"   ❌ Error in task generation test: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Summary and Next Steps:")
    print("1. Run: rm -rf test-app/.dev_agent")
    print("2. Run: uv run dev-agent init test-app")
    print("3. Check that indexing generates embeddings > 0")
    print("4. Check that framework detection shows 'streamlit'")
    print("5. Proceed through workflow and verify Streamlit-specific tasks")
    print("6. Test code generation with: generate --task-id task_1")
    print("7. Verify generated code is Streamlit-specific")

if __name__ == "__main__":
    asyncio.run(main())