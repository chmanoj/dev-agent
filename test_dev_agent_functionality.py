#!/usr/bin/env python3
"""Test script to demonstrate dev-agent functionality."""

import sys
import os
sys.path.insert(0, '.')

from dev_agent.indexing.indexing_engine import IndexingEngine
from dev_agent.analysis.codebase_analyzer import CodebaseAnalyzer
from dev_agent.generation.specification_generator import SpecificationGenerator

def test_indexing():
    """Test the indexing functionality."""
    print("🔍 Testing Indexing Engine...")
    
    engine = IndexingEngine('test-project')
    result = engine.build_index()
    
    print(f"  ✅ Indexing Success: {result.success}")
    print(f"  📁 Files Indexed: {result.metadata.get('total_files', 0)}")
    print(f"  🔧 Functions Found: {result.metadata.get('functions_count', 0)}")
    print(f"  🏗️  Classes Found: {result.metadata.get('classes_count', 0)}")
    
    if result.ast_index:
        print(f"  📊 AST Index: {len(result.ast_index.functions)} functions, {len(result.ast_index.classes)} classes")
        
        # Show some examples
        for func_key, func in list(result.ast_index.functions.items())[:2]:
            print(f"    - Function: {func.name}({', '.join(func.parameters)})")
        
        for cls_key, cls in list(result.ast_index.classes.items())[:1]:
            print(f"    - Class: {cls.name} with {len(cls.methods)} methods")
    
    return result.success

def test_analysis():
    """Test the codebase analysis functionality."""
    print("\n🔬 Testing Codebase Analysis...")
    
    engine = IndexingEngine('test-project')
    analyzer = CodebaseAnalyzer(engine)
    
    # Test specification analysis
    spec_analysis = analyzer.analyze_for_specification()
    
    print(f"  ✅ Analysis Success: {spec_analysis is not None}")
    print(f"  🎯 Project Purpose: {spec_analysis.project_purpose}")
    print(f"  🚀 Main Features: {len(spec_analysis.main_features)} features")
    print(f"  👥 User Roles: {spec_analysis.user_roles}")
    print(f"  📈 Confidence: {spec_analysis.confidence_score:.0%}")
    
    if spec_analysis.main_features:
        for feature in spec_analysis.main_features[:3]:
            print(f"    - {feature}")
    
    return spec_analysis is not None

def test_specification_generation():
    """Test specification generation."""
    print("\n📋 Testing Specification Generation...")
    
    engine = IndexingEngine('test-project')
    analyzer = CodebaseAnalyzer(engine)
    generator = SpecificationGenerator()
    
    # Get analysis
    analysis = analyzer.analyze_for_specification()
    
    # Generate specification
    spec = generator.generate_from_existing_code(analysis)
    
    print(f"  ✅ Generation Success: {spec is not None}")
    print(f"  📄 Introduction Length: {len(spec.introduction)} chars")
    print(f"  🎯 Key Features: {len(spec.key_features)} features")
    print(f"  📋 Requirements: {len(spec.functional_requirements)} requirements")
    print(f"  📊 Source: {spec.source.value}")
    
    if spec.functional_requirements:
        req = spec.functional_requirements[0]
        print(f"    - Example Requirement: {req.user_story[:60]}...")
    
    return spec is not None

def test_vector_search():
    """Test vector similarity search."""
    print("\n🔍 Testing Vector Search...")
    
    engine = IndexingEngine('test-project')
    
    # Test similarity search
    matches = engine.query_similar_code("user management", limit=3)
    
    print(f"  ✅ Search Success: {len(matches)} matches found")
    
    for i, match in enumerate(matches[:2]):
        print(f"    - Match {i+1} type: {type(match)}")
        if hasattr(match, 'chunk'):
            print(f"      File: {match.chunk.file_path} (similarity: {match.similarity_score:.2f})")
            print(f"      Content: {match.chunk.content[:50] if match.chunk.content else 'No content'}...")
        elif hasattr(match, 'file_path'):
            print(f"      File: {match.file_path} (similarity: {match.similarity_score:.2f})")
            print(f"      Content: {match.content[:50] if hasattr(match, 'content') else 'No content'}...")
        else:
            print(f"      Unknown match structure: {match}")
    
    return len(matches) > 0

def main():
    """Run all functionality tests."""
    print("🚀 Testing dev-agent Functionality")
    print("=" * 50)
    
    results = []
    
    # Test each component
    results.append(test_indexing())
    results.append(test_analysis())
    results.append(test_specification_generation())
    results.append(test_vector_search())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    test_names = ["Indexing", "Analysis", "Specification Generation", "Vector Search"]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {i+1}. {name}: {status}")
    
    total_passed = sum(results)
    print(f"\n🎯 Overall: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("🎉 All functionality is working correctly!")
        print("\n💡 The dev-agent library is fully functional and ready to use!")
        print("   You can now run 'uv run dev-agent init <project>' to start using it.")
    else:
        print("⚠️  Some functionality needs attention.")
    
    return total_passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)