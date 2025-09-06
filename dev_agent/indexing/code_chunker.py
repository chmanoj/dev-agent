"""Code chunking strategies for embedding generation."""

import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from ..models.indexing import CodeChunk, FunctionDef, ClassDef, ASTIndex


class CodeChunker:
    """Intelligent code chunking for embedding generation."""
    
    def __init__(self, max_chunk_size: int = 512, overlap_size: int = 50):
        """Initialize the code chunker.
        
        Args:
            max_chunk_size: Maximum number of characters per chunk
            overlap_size: Number of characters to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
    
    def chunk_file(self, file_path: str, language: str = 'python') -> List[CodeChunk]:
        """Chunk a single file into embeddings-ready pieces.
        
        Args:
            file_path: Path to the file to chunk
            language: Programming language of the file
            
        Returns:
            List of CodeChunk objects
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
        
        return self.chunk_content(content, file_path, language)
    
    def chunk_content(self, content: str, file_path: str, language: str = 'python') -> List[CodeChunk]:
        """Chunk file content using multiple strategies.
        
        Args:
            content: File content to chunk
            file_path: Path to the source file
            language: Programming language
            
        Returns:
            List of CodeChunk objects
        """
        chunks = []
        
        # Strategy 1: Function-level chunking
        function_chunks = self._chunk_by_functions(content, file_path, language)
        chunks.extend(function_chunks)
        
        # Strategy 2: Class-level chunking
        class_chunks = self._chunk_by_classes(content, file_path, language)
        chunks.extend(class_chunks)
        
        # Strategy 3: Module-level chunking for remaining content
        module_chunks = self._chunk_by_sliding_window(content, file_path, language)
        chunks.extend(module_chunks)
        
        # Strategy 4: Import and docstring chunks
        special_chunks = self._chunk_special_sections(content, file_path, language)
        chunks.extend(special_chunks)
        
        return chunks
    
    def chunk_from_ast(self, ast_index: ASTIndex, file_path: str) -> List[CodeChunk]:
        """Create chunks from AST analysis results.
        
        Args:
            ast_index: AST index containing parsed information
            file_path: Path to the source file
            
        Returns:
            List of CodeChunk objects
        """
        chunks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
        
        # Create chunks from functions
        for func_key, func_def in ast_index.functions.items():
            # Match by filename only, not full path
            if Path(func_def.file_path).name != Path(file_path).name:
                continue
            
            chunk_content = self._extract_lines(lines, func_def.start_line, func_def.end_line)
            if chunk_content.strip():
                chunk = CodeChunk(
                    content=chunk_content,
                    file_path=file_path,
                    start_line=func_def.start_line,
                    end_line=func_def.end_line,
                    language=self._detect_language(file_path),
                    chunk_type='function'
                )
                chunks.append(chunk)
        
        # Create chunks from classes
        for class_key, class_def in ast_index.classes.items():
            # Match by filename only, not full path
            if Path(class_def.file_path).name != Path(file_path).name:
                continue
            
            chunk_content = self._extract_lines(lines, class_def.start_line, class_def.end_line)
            if chunk_content.strip():
                chunk = CodeChunk(
                    content=chunk_content,
                    file_path=file_path,
                    start_line=class_def.start_line,
                    end_line=class_def.end_line,
                    language=self._detect_language(file_path),
                    chunk_type='class'
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_functions(self, content: str, file_path: str, language: str) -> List[CodeChunk]:
        """Extract function-level chunks using regex patterns.
        
        Args:
            content: File content
            file_path: Source file path
            language: Programming language
            
        Returns:
            List of function chunks
        """
        chunks = []
        lines = content.split('\n')
        
        if language == 'python':
            # Python function pattern
            func_pattern = r'^(\s*)def\s+(\w+)\s*\('
            
            i = 0
            while i < len(lines):
                line = lines[i]
                match = re.match(func_pattern, line)
                
                if match:
                    indent_level = len(match.group(1))
                    func_name = match.group(2)
                    start_line = i + 1
                    
                    # Find end of function by tracking indentation
                    j = i + 1
                    while j < len(lines):
                        if lines[j].strip() == '':
                            j += 1
                            continue
                        
                        current_indent = len(lines[j]) - len(lines[j].lstrip())
                        if current_indent <= indent_level and lines[j].strip():
                            break
                        j += 1
                    
                    end_line = j
                    func_content = '\n'.join(lines[i:j])
                    
                    if len(func_content) <= self.max_chunk_size:
                        chunk = CodeChunk(
                            content=func_content,
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            language=language,
                            chunk_type='function'
                        )
                        chunks.append(chunk)
                    else:
                        # Function too large, split it
                        sub_chunks = self._split_large_function(func_content, file_path, start_line, language)
                        chunks.extend(sub_chunks)
                    
                    i = j
                else:
                    i += 1
        
        return chunks
    
    def _chunk_by_classes(self, content: str, file_path: str, language: str) -> List[CodeChunk]:
        """Extract class-level chunks using regex patterns.
        
        Args:
            content: File content
            file_path: Source file path
            language: Programming language
            
        Returns:
            List of class chunks
        """
        chunks = []
        lines = content.split('\n')
        
        if language == 'python':
            # Python class pattern
            class_pattern = r'^(\s*)class\s+(\w+)\s*[\(:]'
            
            i = 0
            while i < len(lines):
                line = lines[i]
                match = re.match(class_pattern, line)
                
                if match:
                    indent_level = len(match.group(1))
                    class_name = match.group(2)
                    start_line = i + 1
                    
                    # Find end of class by tracking indentation
                    j = i + 1
                    while j < len(lines):
                        if lines[j].strip() == '':
                            j += 1
                            continue
                        
                        current_indent = len(lines[j]) - len(lines[j].lstrip())
                        if current_indent <= indent_level and lines[j].strip():
                            break
                        j += 1
                    
                    end_line = j
                    class_content = '\n'.join(lines[i:j])
                    
                    if len(class_content) <= self.max_chunk_size:
                        chunk = CodeChunk(
                            content=class_content,
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            language=language,
                            chunk_type='class'
                        )
                        chunks.append(chunk)
                    else:
                        # Class too large, split it
                        sub_chunks = self._split_large_class(class_content, file_path, start_line, language)
                        chunks.extend(sub_chunks)
                    
                    i = j
                else:
                    i += 1
        
        return chunks
    
    def _chunk_by_sliding_window(self, content: str, file_path: str, language: str) -> List[CodeChunk]:
        """Create overlapping chunks using sliding window approach.
        
        Args:
            content: File content
            file_path: Source file path
            language: Programming language
            
        Returns:
            List of sliding window chunks
        """
        chunks = []
        
        if len(content) <= self.max_chunk_size:
            # File is small enough to be a single chunk
            chunk = CodeChunk(
                content=content,
                file_path=file_path,
                start_line=1,
                end_line=len(content.split('\n')),
                language=language,
                chunk_type='module'
            )
            chunks.append(chunk)
            return chunks
        
        # Split into overlapping chunks
        start = 0
        chunk_num = 0
        
        while start < len(content):
            end = min(start + self.max_chunk_size, len(content))
            chunk_content = content[start:end]
            
            # Calculate line numbers
            lines_before = content[:start].count('\n')
            lines_in_chunk = chunk_content.count('\n') + 1
            start_line = lines_before + 1
            end_line = start_line + lines_in_chunk - 1
            
            chunk = CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language=language,
                chunk_type='module_fragment'
            )
            chunks.append(chunk)
            
            # Move start position with overlap
            if end >= len(content):
                break
            
            start = end - self.overlap_size
            chunk_num += 1
        
        return chunks
    
    def _chunk_special_sections(self, content: str, file_path: str, language: str) -> List[CodeChunk]:
        """Extract special sections like imports, docstrings, and comments.
        
        Args:
            content: File content
            file_path: Source file path
            language: Programming language
            
        Returns:
            List of special section chunks
        """
        chunks = []
        lines = content.split('\n')
        
        if language == 'python':
            # Extract module-level docstring
            docstring_chunk = self._extract_module_docstring(lines, file_path, language)
            if docstring_chunk:
                chunks.append(docstring_chunk)
            
            # Extract import block
            import_chunk = self._extract_import_block(lines, file_path, language)
            if import_chunk:
                chunks.append(import_chunk)
        
        return chunks
    
    def _extract_module_docstring(self, lines: List[str], file_path: str, language: str) -> Optional[CodeChunk]:
        """Extract module-level docstring."""
        # Look for docstring at the beginning of the file (after imports/comments)
        start_line = None
        end_line = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            if stripped.startswith('"""') or stripped.startswith("'''"):
                quote_type = '"""' if stripped.startswith('"""') else "'''"
                start_line = i + 1
                
                # Find end of docstring
                if stripped.count(quote_type) >= 2:
                    # Single line docstring
                    end_line = i + 1
                else:
                    # Multi-line docstring
                    for j in range(i + 1, len(lines)):
                        if quote_type in lines[j]:
                            end_line = j + 1
                            break
                
                if end_line:
                    docstring_content = '\n'.join(lines[i:end_line])
                    return CodeChunk(
                        content=docstring_content,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        language=language,
                        chunk_type='docstring'
                    )
                break
            
            # If we hit non-comment, non-docstring code, stop looking
            if not stripped.startswith('import') and not stripped.startswith('from'):
                break
        
        return None
    
    def _extract_import_block(self, lines: List[str], file_path: str, language: str) -> Optional[CodeChunk]:
        """Extract the import block from the beginning of the file."""
        import_lines = []
        start_line = None
        end_line = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip comments and empty lines at the beginning
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check if this is an import line
            if stripped.startswith('import ') or stripped.startswith('from '):
                if start_line is None:
                    start_line = i + 1
                import_lines.append(line)
                end_line = i + 1
            elif start_line is not None:
                # We've hit non-import code after imports, stop
                break
        
        if import_lines and start_line and end_line:
            import_content = '\n'.join(import_lines)
            return CodeChunk(
                content=import_content,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language=language,
                chunk_type='imports'
            )
        
        return None
    
    def _split_large_function(self, func_content: str, file_path: str, start_line: int, language: str) -> List[CodeChunk]:
        """Split a large function into smaller chunks."""
        chunks = []
        lines = func_content.split('\n')
        
        # Try to split at logical boundaries (empty lines, comments)
        current_chunk = []
        current_size = 0
        chunk_start_line = start_line
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            current_size += len(line) + 1  # +1 for newline
            
            # Check if we should split here
            should_split = (
                current_size >= self.max_chunk_size and
                (line.strip() == '' or line.strip().startswith('#'))
            ) or i == len(lines) - 1
            
            if should_split or i == len(lines) - 1:
                if current_chunk:
                    chunk_content = '\n'.join(current_chunk)
                    chunk = CodeChunk(
                        content=chunk_content,
                        file_path=file_path,
                        start_line=chunk_start_line,
                        end_line=chunk_start_line + len(current_chunk) - 1,
                        language=language,
                        chunk_type='function_fragment'
                    )
                    chunks.append(chunk)
                
                # Start new chunk with overlap
                if i < len(lines) - 1:
                    overlap_lines = min(self.overlap_size // 20, len(current_chunk))  # Rough estimate
                    current_chunk = current_chunk[-overlap_lines:] if overlap_lines > 0 else []
                    current_size = sum(len(line) + 1 for line in current_chunk)
                    chunk_start_line = chunk_start_line + len(current_chunk) - overlap_lines
                else:
                    current_chunk = []
                    current_size = 0
        
        return chunks
    
    def _split_large_class(self, class_content: str, file_path: str, start_line: int, language: str) -> List[CodeChunk]:
        """Split a large class into smaller chunks."""
        # Similar to function splitting but preserve class structure
        return self._split_large_function(class_content, file_path, start_line, language)
    
    def _extract_lines(self, lines: List[str], start_line: int, end_line: int) -> str:
        """Extract lines from a list, handling 1-based indexing."""
        # Convert to 0-based indexing
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        return '\n'.join(lines[start_idx:end_idx])
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        return language_map.get(ext, 'unknown')
    
    def optimize_chunks(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Optimize chunks by removing duplicates and merging small adjacent chunks.
        
        Args:
            chunks: List of chunks to optimize
            
        Returns:
            Optimized list of chunks
        """
        if not chunks:
            return chunks
        
        # Sort chunks by file path and line number
        sorted_chunks = sorted(chunks, key=lambda c: (c.file_path, c.start_line))
        
        # Remove duplicates based on content hash
        seen_hashes = set()
        unique_chunks = []
        
        for chunk in sorted_chunks:
            content_hash = hash(chunk.content)
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_chunks.append(chunk)
        
        # Merge small adjacent chunks of the same type
        merged_chunks = []
        current_chunk = None
        
        for chunk in unique_chunks:
            if current_chunk is None:
                current_chunk = chunk
                continue
            
            # Check if chunks can be merged
            can_merge = (
                current_chunk.file_path == chunk.file_path and
                current_chunk.language == chunk.language and
                current_chunk.chunk_type == chunk.chunk_type and
                current_chunk.end_line + 1 >= chunk.start_line and
                len(current_chunk.content) + len(chunk.content) <= self.max_chunk_size
            )
            
            if can_merge:
                # Merge chunks
                merged_content = current_chunk.content + '\n' + chunk.content
                current_chunk = CodeChunk(
                    content=merged_content,
                    file_path=current_chunk.file_path,
                    start_line=current_chunk.start_line,
                    end_line=chunk.end_line,
                    language=current_chunk.language,
                    chunk_type=current_chunk.chunk_type
                )
            else:
                # Can't merge, add current chunk and start new one
                merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        # Add the last chunk
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        return merged_chunks