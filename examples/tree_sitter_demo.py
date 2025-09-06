#!/usr/bin/env python3
"""Demonstration of TreeSitterParser capabilities."""

import os
import sys
from pathlib import Path

# Add the project root to the path so we can import dev_agent
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dev_agent.indexing.tree_sitter_parser import TreeSitterParser


def demo_basic_parsing():
    """Demonstrate basic parsing capabilities."""
    print("=== TreeSitterParser Basic Parsing Demo ===\n")
    
    parser = TreeSitterParser()
    
    # Create a sample Python file
    sample_code = '''
"""Sample module for demonstration."""

import os
from typing import List, Optional

class DataProcessor:
    """A sample data processor class."""
    
    def __init__(self, name: str):
        self.name = name
        self.processed_items = []
    
    def process_item(self, item: str) -> bool:
        """Process a single item."""
        if not item:
            return False
        
        processed = item.upper().strip()
        self.processed_items.append(processed)
        return True
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {
            'name': self.name,
            'total_processed': len(self.processed_items),
            'items': self.processed_items
        }

def create_processor(name: str) -> DataProcessor:
    """Factory function for creating processors."""
    return DataProcessor(name)

def main():
    """Main demonstration function."""
    processor = create_processor("demo")
    processor.process_item("  hello world  ")
    processor.process_item("python rocks")
    
    stats = processor.get_stats()
    print(f"Processed {stats['total_processed']} items")

if __name__ == "__main__":
    main()
'''
    
    # Write sample code to a temporary file
    temp_file = "temp_demo.py"
    with open(temp_file, 'w') as f:
        f.write(sample_code)
    
    try:
        # Parse the file
        print(f"Parsing file: {temp_file}")
        ast = parser.parse_file(temp_file, 'python')
        
        if ast:
            print("✓ File parsed successfully\n")
            
            # Extract functions
            print("--- Functions Found ---")
            functions = parser.get_function_definitions(ast, temp_file)
            for func in functions:
                params = ', '.join(func.parameters) if func.parameters else 'no parameters'
                print(f"  • {func.name}({params}) at line {func.start_line}")
                if func.docstring:
                    print(f"    Docstring: {func.docstring[:50]}...")
            
            print()
            
            # Extract classes
            print("--- Classes Found ---")
            classes = parser.get_class_definitions(ast, temp_file)
            for cls in classes:
                bases = ', '.join(cls.base_classes) if cls.base_classes else 'no inheritance'
                print(f"  • {cls.name}({bases}) at line {cls.start_line}")
                if cls.docstring:
                    print(f"    Docstring: {cls.docstring[:50]}...")
                if cls.methods:
                    print(f"    Methods: {', '.join(m.name for m in cls.methods)}")
            
            print()
            
            # Extract imports
            print("--- Imports Found ---")
            imports = parser.extract_imports(ast, temp_file)
            for imp in imports:
                if imp.names:
                    print(f"  • from {imp.module} import {', '.join(imp.names)}")
                else:
                    alias_str = f" as {imp.alias}" if imp.alias else ""
                    print(f"  • import {imp.module}{alias_str}")
            
            print()
            
            # Extract all symbols
            print("--- All Symbols ---")
            symbols = parser.extract_symbols(ast, temp_file)
            symbol_counts = {}
            for symbol in symbols:
                symbol_counts[symbol.symbol_type] = symbol_counts.get(symbol.symbol_type, 0) + 1
            
            for symbol_type, count in symbol_counts.items():
                print(f"  • {symbol_type}: {count}")
        
        else:
            print("✗ Failed to parse file")
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)


def demo_multiple_files():
    """Demonstrate analyzing multiple files."""
    print("\n=== Multiple Files Analysis Demo ===\n")
    
    parser = TreeSitterParser()
    
    # Find sample files
    sample_files_dir = project_root / "tests" / "sample_files"
    sample_files = []
    
    if sample_files_dir.exists():
        for file_path in sample_files_dir.glob("*.py"):
            sample_files.append(str(file_path))
    
    if not sample_files:
        print("No sample files found, creating temporary files...")
        
        # Create temporary files for demo
        file1_content = '''
def helper_function():
    return "helper"

class HelperClass:
    def method1(self):
        pass
'''
        
        file2_content = '''
import json
from datetime import datetime

class JsonProcessor:
    def process(self, data):
        return json.loads(data)
'''
        
        sample_files = ["temp_file1.py", "temp_file2.py"]
        with open(sample_files[0], 'w') as f:
            f.write(file1_content)
        with open(sample_files[1], 'w') as f:
            f.write(file2_content)
    
    try:
        print(f"Analyzing {len(sample_files)} files:")
        for file_path in sample_files:
            print(f"  • {file_path}")
        
        print()
        
        # Create comprehensive analysis
        ast_index = parser.analyze_code_structure(sample_files)
        
        print("--- Analysis Results ---")
        print(f"Total functions found: {len(ast_index.functions)}")
        print(f"Total classes found: {len(ast_index.classes)}")
        print(f"Total imports found: {len(ast_index.imports)}")
        print(f"Total symbols found: {len(ast_index.symbols)}")
        
        print("\n--- File Metadata ---")
        for file_path, metadata in ast_index.file_metadata.items():
            filename = os.path.basename(file_path)
            print(f"  {filename}:")
            print(f"    Language: {metadata.get('language', 'unknown')}")
            print(f"    Lines: {metadata.get('line_count', 0)}")
            print(f"    Functions: {metadata.get('function_count', 0)}")
            print(f"    Classes: {metadata.get('class_count', 0)}")
            print(f"    Imports: {metadata.get('import_count', 0)}")
        
        # Create symbol map
        print("\n--- Symbol Map Demo ---")
        symbol_map = parser.create_symbol_map(sample_files)
        print(f"Total symbols in map: {len(symbol_map)}")
        
        # Show a few example symbols
        print("Sample symbols:")
        for i, (key, symbol) in enumerate(symbol_map.items()):
            if i >= 5:  # Show only first 5
                break
            filename = os.path.basename(symbol.file_path)
            print(f"  • {symbol.name} ({symbol.symbol_type}) in {filename}:{symbol.line_number}")
    
    finally:
        # Clean up temporary files
        for file_path in sample_files:
            if file_path.startswith("temp_") and os.path.exists(file_path):
                os.remove(file_path)


def demo_performance():
    """Demonstrate performance characteristics."""
    print("\n=== Performance Demo ===\n")
    
    import time
    
    parser = TreeSitterParser()
    
    # Create a larger file for performance testing
    large_code = '''
"""Large module for performance testing."""

import os
import sys
from typing import List, Dict, Optional
'''
    
    # Add many classes and functions
    for i in range(50):
        large_code += f'''

class TestClass{i}:
    """Test class {i}."""
    
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self, param: int) -> int:
        """Method {i}."""
        return param + {i}
    
    def another_method_{i}(self):
        return self.value * 2

def test_function_{i}(x: int, y: str = "default") -> str:
    """Test function {i}."""
    return f"{{x}}: {{y}} - {i}"
'''
    
    temp_file = "large_temp_demo.py"
    with open(temp_file, 'w') as f:
        f.write(large_code)
    
    try:
        print(f"Performance test with file containing ~{len(large_code.split())} words")
        
        # Time the parsing
        start_time = time.time()
        ast = parser.parse_file(temp_file, 'python')
        parse_time = time.time() - start_time
        
        print(f"Parse time: {parse_time:.4f} seconds")
        
        # Time the analysis
        start_time = time.time()
        ast_index = parser.analyze_code_structure([temp_file])
        analysis_time = time.time() - start_time
        
        print(f"Analysis time: {analysis_time:.4f} seconds")
        print(f"Total time: {parse_time + analysis_time:.4f} seconds")
        
        # Show results
        print(f"\nResults:")
        print(f"  Functions extracted: {len(ast_index.functions)}")
        print(f"  Classes extracted: {len(ast_index.classes)}")
        print(f"  Symbols extracted: {len(ast_index.symbols)}")
        
        # Calculate throughput
        metadata = ast_index.file_metadata[temp_file]
        lines_per_second = metadata['line_count'] / (parse_time + analysis_time)
        print(f"  Throughput: {lines_per_second:.0f} lines/second")
    
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def main():
    """Run all demonstrations."""
    print("TreeSitterParser Demonstration")
    print("=" * 50)
    
    try:
        demo_basic_parsing()
        demo_multiple_files()
        demo_performance()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nThe TreeSitterParser provides:")
        print("  ✓ Fast Python code parsing")
        print("  ✓ Function and class extraction")
        print("  ✓ Import statement analysis")
        print("  ✓ Symbol mapping and indexing")
        print("  ✓ Multi-file analysis")
        print("  ✓ Graceful error handling")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()