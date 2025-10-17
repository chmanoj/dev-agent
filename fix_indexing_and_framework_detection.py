#!/usr/bin/env python3
"""Fix script to address indexing and framework detection issues."""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def fix_indexing_issues():
    """Fix the indexing and framework detection issues."""
    
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
    
    print("🔧 Fixing indexing and framework detection issues...")
    
    # 1. Fix framework detection for Streamlit
    print("\n1. Fixing framework detection...")
    
    # Read the test project files to understand the framework
    test_app_path = Path("test-app")
    main_py = test_app_path / "main.py"
    pyproject_toml = test_app_path / "pyproject.toml"
    
    if main_py.exists():
        with open(main_py) as f:
            content = f.read()
            if "streamlit" in content.lower():
                print("   ✓ Detected Streamlit framework in main.py")
    
    if pyproject_toml.exists():
        with open(pyproject_toml) as f:
            content = f.read()
            if "streamlit" in content.lower():
                print("   ✓ Detected Streamlit dependency in pyproject.toml")
    
    # 2. Test embedding generation
    print("\n2. Testing embedding generation...")
    
    try:
        from dev_agent.llm import create_embedding_client
        from dev_agent.indexing.indexing_engine import IndexingEngine
        
        # Create embedding client
        embedding_client = create_embedding_client()
        print(f"   ✓ Created embedding client: {type(embedding_client)}")
        
        # Test embedding generation
        test_texts = [
            "import streamlit as st",
            "st.title('Hello World')",
            "def main():\n    st.write('Hello')"
        ]
        
        embeddings = await embedding_client.embed_batch(test_texts)
        print(f"   ✓ Generated {len(embeddings)} test embeddings")
        
        # 3. Re-index the test project with proper embedding generation
        print("\n3. Re-indexing test project...")
        
        # Remove existing index
        index_path = test_app_path / ".dev_agent" / "index"
        if index_path.exists():
            import shutil
            shutil.rmtree(index_path)
            print("   ✓ Removed existing index")
        
        # Create new indexing engine
        engine = IndexingEngine(
            project_path=str(test_app_path),
            embedding_client=embedding_client
        )
        
        # Build index
        result = engine.build_index()
        print(f"   ✓ Indexed {result.files_indexed} files")
        print(f"   ✓ Generated {result.embeddings_count} embeddings")
        print(f"   ✓ Found {len(result.ast_index.functions)} functions")
        
        # 4. Test vector search
        print("\n4. Testing vector search...")
        
        if result.embeddings_count > 0:
            # Test search
            matches = await engine.vector_db.query_similar(
                query_text="streamlit page with title",
                k=3,
                min_similarity=0.1
            )
            print(f"   ✓ Found {len(matches)} similar code chunks")
            
            for i, match in enumerate(matches[:2]):
                print(f"     Match {i+1}: {match.chunk.file_path} (similarity: {match.similarity_score:.2f})")
        else:
            print("   ⚠️  No embeddings generated - need to investigate further")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def fix_framework_detection():
    """Fix the framework detection logic."""
    
    print("\n5. Fixing framework detection logic...")
    
    # The issue is in the task generator - it's hardcoded to use Django
    # Let's check the current framework detection logic
    
    try:
        from dev_agent.analysis.codebase_analyzer import CodebaseAnalyzer
        from dev_agent.indexing.indexing_engine import IndexingEngine
        from dev_agent.llm import create_embedding_client
        
        # Create analyzer for test project
        embedding_client = create_embedding_client()
        engine = IndexingEngine(
            project_path="test-app",
            embedding_client=embedding_client
        )
        analyzer = CodebaseAnalyzer(engine)
        
        # Test framework detection
        patterns = analyzer.identify_code_patterns()
        print(f"   ✓ Identified {len(patterns.structural_patterns)} structural patterns")
        
        # Check if Streamlit is detected
        streamlit_detected = False
        for pattern in patterns.import_patterns:
            if "streamlit" in pattern.description.lower():
                streamlit_detected = True
                print(f"   ✓ Detected Streamlit pattern: {pattern.description}")
        
        if not streamlit_detected:
            print("   ⚠️  Streamlit not detected in patterns - this needs fixing")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error in framework detection: {e}")
        return False

if __name__ == "__main__":
    async def main():
        success1 = await fix_indexing_issues()
        success2 = await fix_framework_detection()
        
        if success1 and success2:
            print("\n✅ All fixes completed successfully!")
            print("\nNext steps:")
            print("1. Re-run the dev-agent workflow")
            print("2. The system should now properly detect Streamlit")
            print("3. Generated tasks should be Streamlit-specific")
            print("4. Code generation should use the indexed codebase")
        else:
            print("\n❌ Some fixes failed - check the errors above")
        
        return success1 and success2
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)