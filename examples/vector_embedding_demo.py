#!/usr/bin/env python3
"""
Demo script showing the vector embedding system in action.

This script demonstrates:
1. Creating a VectorDatabase instance
2. Chunking code using CodeChunker
3. Storing embeddings for code chunks
4. Performing similarity searches
5. Retrieving similar code based on queries
"""

import os
import tempfile
import shutil
from pathlib import Path

from dev_agent.indexing.vector_database import VectorDatabase
from dev_agent.indexing.code_chunker import CodeChunker
from dev_agent.models.indexing import CodeChunk


def create_sample_code_files(temp_dir: str) -> list[str]:
    """Create sample Python files for demonstration."""
    files = []
    
    # File 1: Math utilities
    math_utils = '''"""Math utility functions."""

def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

def multiply_values(x, y):
    """Multiply two values."""
    return x * y

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
'''
    
    math_file = os.path.join(temp_dir, 'math_utils.py')
    with open(math_file, 'w') as f:
        f.write(math_utils)
    files.append(math_file)
    
    # File 2: String utilities
    string_utils = '''"""String utility functions."""

def reverse_string(text):
    """Reverse a string."""
    return text[::-1]

def count_words(text):
    """Count words in a text."""
    return len(text.split())

def capitalize_words(text):
    """Capitalize each word in a text."""
    return ' '.join(word.capitalize() for word in text.split())

class TextProcessor:
    """A text processing class."""
    
    def __init__(self):
        self.processed_count = 0
    
    def clean_text(self, text):
        """Clean and normalize text."""
        self.processed_count += 1
        return text.strip().lower()
    
    def extract_keywords(self, text, min_length=3):
        """Extract keywords from text."""
        words = text.split()
        return [word for word in words if len(word) >= min_length]
'''
    
    string_file = os.path.join(temp_dir, 'string_utils.py')
    with open(string_file, 'w') as f:
        f.write(string_utils)
    files.append(string_file)
    
    # File 3: File utilities
    file_utils = '''"""File utility functions."""

import os
import json

def read_text_file(filepath):
    """Read content from a text file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def write_json_data(data, filepath):
    """Write data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_file_size(filepath):
    """Get the size of a file in bytes."""
    return os.path.getsize(filepath)

class FileManager:
    """A file management class."""
    
    def __init__(self, base_path):
        self.base_path = base_path
        self.operations_log = []
    
    def create_directory(self, dirname):
        """Create a directory."""
        full_path = os.path.join(self.base_path, dirname)
        os.makedirs(full_path, exist_ok=True)
        self.operations_log.append(f"Created directory: {dirname}")
        return full_path
    
    def list_files(self, pattern="*"):
        """List files matching a pattern."""
        from glob import glob
        search_path = os.path.join(self.base_path, pattern)
        return glob(search_path)
'''
    
    file_file = os.path.join(temp_dir, 'file_utils.py')
    with open(file_file, 'w') as f:
        f.write(file_utils)
    files.append(file_file)
    
    return files


def demonstrate_vector_embedding_system():
    """Demonstrate the complete vector embedding system."""
    print("🚀 Vector Embedding System Demo")
    print("=" * 50)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    index_path = os.path.join(temp_dir, 'vector_index')
    
    try:
        # Step 1: Initialize components
        print("\n1️⃣ Initializing Vector Database and Code Chunker...")
        vector_db = VectorDatabase(index_path)
        chunker = CodeChunker(max_chunk_size=512, overlap_size=50)
        
        print(f"   ✅ Vector database initialized with {vector_db.embedding_dimension}D embeddings")
        print(f"   ✅ Code chunker configured (max_size={chunker.max_chunk_size}, overlap={chunker.overlap_size})")
        
        # Step 2: Create sample code files
        print("\n2️⃣ Creating sample code files...")
        sample_files = create_sample_code_files(temp_dir)
        print(f"   ✅ Created {len(sample_files)} sample Python files")
        
        # Step 3: Chunk the code files
        print("\n3️⃣ Chunking code files...")
        all_chunks = []
        for file_path in sample_files:
            chunks = chunker.chunk_file(file_path, 'python')
            all_chunks.extend(chunks)
            print(f"   📄 {Path(file_path).name}: {len(chunks)} chunks")
        
        print(f"   ✅ Total chunks created: {len(all_chunks)}")
        
        # Step 4: Store embeddings
        print("\n4️⃣ Storing embeddings in vector database...")
        chunk_ids = vector_db.store_embeddings(all_chunks)
        print(f"   ✅ Stored {len(chunk_ids)} embeddings")
        
        # Step 5: Display database statistics
        print("\n5️⃣ Database Statistics:")
        stats = vector_db.get_stats()
        for key, value in stats.items():
            print(f"   📊 {key}: {value}")
        
        # Step 6: Demonstrate similarity search
        print("\n6️⃣ Similarity Search Demonstrations:")
        
        # Search 1: Mathematical operations
        print("\n   🔍 Search: 'addition function'")
        results = vector_db.query_similar("addition function", k=3)
        for i, match in enumerate(results, 1):
            print(f"      {i}. Score: {match.similarity_score:.3f} | {match.chunk.file_path}:{match.chunk.start_line}-{match.chunk.end_line}")
            print(f"         Type: {match.chunk.chunk_type} | Language: {match.chunk.language}")
        
        # Search 2: Text processing
        print("\n   🔍 Search: 'text processing'")
        results = vector_db.query_similar("text processing", k=3)
        for i, match in enumerate(results, 1):
            print(f"      {i}. Score: {match.similarity_score:.3f} | {match.chunk.file_path}:{match.chunk.start_line}-{match.chunk.end_line}")
            print(f"         Type: {match.chunk.chunk_type} | Language: {match.chunk.language}")
        
        # Search 3: File operations
        print("\n   🔍 Search: 'file reading'")
        results = vector_db.query_similar("file reading", k=3)
        for i, match in enumerate(results, 1):
            print(f"      {i}. Score: {match.similarity_score:.3f} | {match.chunk.file_path}:{match.chunk.start_line}-{match.chunk.end_line}")
            print(f"         Type: {match.chunk.chunk_type} | Language: {match.chunk.language}")
        
        # Search 4: Class definitions
        print("\n   🔍 Search: 'class with methods'")
        results = vector_db.query_similar("class with methods", k=3)
        for i, match in enumerate(results, 1):
            print(f"      {i}. Score: {match.similarity_score:.3f} | {match.chunk.file_path}:{match.chunk.start_line}-{match.chunk.end_line}")
            print(f"         Type: {match.chunk.chunk_type} | Language: {match.chunk.language}")
        
        # Step 7: Demonstrate chunk-based similarity search
        print("\n7️⃣ Chunk-based Similarity Search:")
        
        # Create a query chunk
        query_chunk = CodeChunk(
            content="def sum_numbers(nums): return sum(nums)",
            file_path="query.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function"
        )
        
        print(f"   🔍 Query chunk: {query_chunk.content}")
        results = vector_db.query_similar_by_chunk(query_chunk, k=3)
        for i, match in enumerate(results, 1):
            print(f"      {i}. Score: {match.similarity_score:.3f} | {match.chunk.file_path}:{match.chunk.start_line}-{match.chunk.end_line}")
            print(f"         Type: {match.chunk.chunk_type}")
        
        # Step 8: Save and demonstrate persistence
        print("\n8️⃣ Testing Persistence...")
        vector_db.save_index()
        print("   ✅ Index saved to disk")
        
        # Create new database instance to test loading
        new_db = VectorDatabase(index_path)
        new_stats = new_db.get_stats()
        print(f"   ✅ Loaded index with {new_stats['total_embeddings']} embeddings")
        
        # Test search with loaded database
        loaded_results = new_db.query_similar("calculator", k=2)
        print(f"   🔍 Search with loaded DB found {len(loaded_results)} results")
        
        print("\n🎉 Demo completed successfully!")
        print("\n📋 Summary:")
        print(f"   • Processed {len(sample_files)} Python files")
        print(f"   • Created {len(all_chunks)} code chunks")
        print(f"   • Stored {len(chunk_ids)} vector embeddings")
        print(f"   • Demonstrated similarity search capabilities")
        print(f"   • Verified persistence and loading")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary files")


if __name__ == "__main__":
    demonstrate_vector_embedding_system()