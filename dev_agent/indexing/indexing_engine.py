"""High-performance indexing engine for codebase analysis."""

import json
import mmap
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..interfaces.indexing_interface import IIndexingEngine
from ..models.indexing import ASTIndex, CodeChunk, SymbolInfo
from ..models.project_state import IndexMetadata
from ..models.results import IndexResult
from .code_chunker import CodeChunker
from .tree_sitter_parser import TreeSitterParser
from .vector_database import VectorDatabase


class IndexingEngine(IIndexingEngine):
    """High-performance indexing engine that orchestrates AST parsing and embeddings."""

    def __init__(self, project_path: str, index_path: str | None = None):
        """Initialize the indexing engine.

        Args:
            project_path: Path to the project root
            index_path: Custom path for index storage (optional)
        """
        self.project_path = Path(project_path)
        self.index_path = (
            Path(index_path)
            if index_path
            else self.project_path / ".dev_agent" / "index"
        )

        # Create index directory
        self.index_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.tree_sitter_parser = TreeSitterParser()
        self.vector_db = VectorDatabase(str(self.index_path))
        self.code_chunker = CodeChunker(max_chunk_size=512, overlap_size=50)

        # Index state
        self.ast_index: ASTIndex | None = None
        self.index_metadata: IndexMetadata | None = None
        self.supported_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
        }

        # Performance settings
        self.max_workers = min(4, os.cpu_count() or 1)  # Limit concurrent processing
        self.memory_map_threshold = 1024 * 1024  # 1MB threshold for memory mapping

        # Progress tracking
        self.progress_callback = None
        self.current_progress = 0.0
        self.total_files = 0

        # Load existing index if available
        self._load_existing_index()

    def set_progress_callback(self, callback) -> None:
        """Set callback function for progress updates.

        Args:
            callback: Function that takes (current, total, message) parameters
        """
        self.progress_callback = callback

    def _update_progress(self, current: int, total: int, message: str = "") -> None:
        """Update progress and call callback if set."""
        self.current_progress = current / total if total > 0 else 0.0
        if self.progress_callback:
            self.progress_callback(current, total, message)

    def build_index(self) -> IndexResult:
        """Build a complete index of the codebase.

        Returns:
            IndexResult with success status and metadata
        """
        start_time = time.time()
        errors = []

        try:
            print("Starting codebase indexing...")

            # Step 1: Discover files
            print("Discovering source files...")
            source_files = self._discover_source_files()
            self.total_files = len(source_files)

            if not source_files:
                return IndexResult(
                    success=False,
                    ast_index=None,
                    embeddings_count=0,
                    errors=["No source files found in project"],
                    metadata={},
                )

            print(f"Found {len(source_files)} source files")
            self._update_progress(0, len(source_files), "Starting AST parsing...")

            # Step 2: Parse AST for all files
            print("Parsing AST for all files...")
            ast_index = self.parse_codebase_ast()

            if not ast_index:
                return IndexResult(
                    success=False,
                    ast_index=None,
                    embeddings_count=0,
                    errors=["Failed to parse codebase AST"],
                    metadata={},
                )

            # Step 3: Generate code chunks
            print("Generating code chunks...")
            self._update_progress(
                len(source_files) // 2, len(source_files), "Generating code chunks..."
            )

            all_chunks = []
            for i, file_path in enumerate(source_files):
                try:
                    # Use AST-based chunking when possible
                    chunks = self.code_chunker.chunk_from_ast(ast_index, str(file_path))
                    if not chunks:
                        # Fallback to content-based chunking
                        chunks = self.code_chunker.chunk_file(str(file_path))

                    all_chunks.extend(chunks)

                    if i % 10 == 0:  # Update progress every 10 files
                        self._update_progress(
                            len(source_files) // 2 + i // 2,
                            len(source_files),
                            f"Chunking file {i + 1}/{len(source_files)}",
                        )

                except Exception as e:
                    error_msg = f"Error chunking file {file_path}: {e}"
                    errors.append(error_msg)
                    print(f"Warning: {error_msg}")

            # Optimize chunks
            print(f"Optimizing {len(all_chunks)} chunks...")
            all_chunks = self.code_chunker.optimize_chunks(all_chunks)
            print(f"Optimized to {len(all_chunks)} chunks")

            # Step 4: Generate and store embeddings
            print("Generating embeddings...")
            self._update_progress(
                3 * len(source_files) // 4,
                len(source_files),
                "Generating embeddings...",
            )

            embeddings_count = 0
            if all_chunks:
                chunk_ids = self.vector_db.store_embeddings(all_chunks)
                embeddings_count = len(chunk_ids)
                print(f"Generated {embeddings_count} embeddings")

            # Step 5: Save index to disk
            print("Saving index to disk...")
            self._save_index_metadata(ast_index, source_files, embeddings_count)
            self.vector_db.save_index()

            # Update progress to complete
            self._update_progress(
                len(source_files), len(source_files), "Indexing complete!"
            )

            # Create metadata
            end_time = time.time()
            total_lines = sum(
                metadata.get("line_count", 0)
                for metadata in ast_index.file_metadata.values()
            )

            languages_detected = list(
                set(
                    metadata.get("language", "unknown")
                    for metadata in ast_index.file_metadata.values()
                )
            )

            metadata = {
                "indexing_time_seconds": end_time - start_time,
                "total_files": len(source_files),
                "total_lines": total_lines,
                "total_chunks": len(all_chunks),
                "embeddings_count": embeddings_count,
                "languages_detected": languages_detected,
                "functions_count": len(ast_index.functions),
                "classes_count": len(ast_index.classes),
                "imports_count": len(ast_index.imports),
                "symbols_count": len(ast_index.symbols),
            }

            print(f"Indexing completed in {end_time - start_time:.2f} seconds")
            print(f"Indexed {len(source_files)} files, {total_lines} lines of code")
            print(
                f"Generated {embeddings_count} embeddings from {len(all_chunks)} chunks"
            )

            return IndexResult(
                success=True,
                ast_index=ast_index,
                embeddings_count=embeddings_count,
                errors=errors,
                metadata=metadata,
            )

        except Exception as e:
            error_msg = f"Critical error during indexing: {e}"
            errors.append(error_msg)
            print(f"Error: {error_msg}")

            return IndexResult(
                success=False,
                ast_index=None,
                embeddings_count=0,
                errors=errors,
                metadata={},
            )

    def parse_codebase_ast(self) -> ASTIndex | None:
        """Parse the entire codebase into an AST index.

        Returns:
            ASTIndex containing all parsed information
        """
        source_files = self._discover_source_files()
        if not source_files:
            return None

        print(f"Parsing AST for {len(source_files)} files...")

        # Use parallel processing for large codebases
        if len(source_files) > 10:
            return self._parse_ast_parallel(source_files)
        else:
            return self._parse_ast_sequential(source_files)

    def _parse_ast_sequential(self, source_files: list[Path]) -> ASTIndex:
        """Parse AST sequentially for smaller codebases."""
        ast_index = ASTIndex(
            functions={}, classes={}, imports=[], symbols={}, file_metadata={}
        )

        for i, file_path in enumerate(source_files):
            try:
                self._update_progress(i, len(source_files), f"Parsing {file_path.name}")
                self._parse_single_file(file_path, ast_index)
            except Exception as e:
                print(f"Warning: Error parsing {file_path}: {e}")

        return ast_index

    def _parse_ast_parallel(self, source_files: list[Path]) -> ASTIndex:
        """Parse AST in parallel for larger codebases."""
        ast_index = ASTIndex(
            functions={}, classes={}, imports=[], symbols={}, file_metadata={}
        )

        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all parsing tasks
            future_to_file = {
                executor.submit(self._parse_file_safe, file_path): file_path
                for file_path in source_files
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                completed += 1

                try:
                    file_ast_data = future.result()
                    if file_ast_data:
                        self._merge_ast_data(ast_index, file_ast_data)

                    self._update_progress(
                        completed,
                        len(source_files),
                        f"Parsed {file_path.name} ({completed}/{len(source_files)})",
                    )

                except Exception as e:
                    print(f"Warning: Error parsing {file_path}: {e}")

        return ast_index

    def _parse_file_safe(self, file_path: Path) -> dict[str, Any] | None:
        """Safely parse a single file and return AST data."""
        try:
            # Create a temporary AST index for this file
            temp_ast = ASTIndex(
                functions={}, classes={}, imports=[], symbols={}, file_metadata={}
            )

            self._parse_single_file(file_path, temp_ast)

            # Return the data in a serializable format
            return {
                "functions": temp_ast.functions,
                "classes": temp_ast.classes,
                "imports": temp_ast.imports,
                "symbols": temp_ast.symbols,
                "file_metadata": temp_ast.file_metadata,
            }

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None

    def _merge_ast_data(
        self, main_ast: ASTIndex, file_ast_data: dict[str, Any]
    ) -> None:
        """Merge AST data from a single file into the main index."""
        # Merge functions
        main_ast.functions.update(file_ast_data["functions"])

        # Merge classes
        main_ast.classes.update(file_ast_data["classes"])

        # Merge imports
        main_ast.imports.extend(file_ast_data["imports"])

        # Merge symbols
        main_ast.symbols.update(file_ast_data["symbols"])

        # Merge file metadata
        main_ast.file_metadata.update(file_ast_data["file_metadata"])

    def _parse_single_file(self, file_path: Path, ast_index: ASTIndex) -> None:
        """Parse a single file and add results to AST index."""
        language = self._detect_language(file_path)
        if language not in self.tree_sitter_parser.supported_languages:
            return

        # Use memory mapping for large files
        if file_path.stat().st_size > self.memory_map_threshold:
            ast = self._parse_file_with_mmap(file_path, language)
        else:
            ast = self.tree_sitter_parser.parse_file(str(file_path), language)

        if not ast:
            return

        # Extract all information from AST
        functions = self.tree_sitter_parser.get_function_definitions(
            ast, str(file_path)
        )
        classes = self.tree_sitter_parser.get_class_definitions(ast, str(file_path))
        imports = self.tree_sitter_parser.extract_imports(ast, str(file_path))
        symbols = self.tree_sitter_parser.extract_symbols(ast, str(file_path))

        # Add to index with unique keys
        for func in functions:
            key = f"{file_path}:{func.name}:{func.start_line}"
            ast_index.functions[key] = func

        for cls in classes:
            key = f"{file_path}:{cls.name}:{cls.start_line}"
            ast_index.classes[key] = cls

        ast_index.imports.extend(imports)

        for symbol in symbols:
            key = f"{file_path}:{symbol.name}:{symbol.line_number}"
            ast_index.symbols[key] = symbol

        # Add file metadata
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            ast_index.file_metadata[str(file_path)] = {
                "language": language,
                "line_count": len(content.split("\n")),
                "char_count": len(content),
                "function_count": len(functions),
                "class_count": len(classes),
                "import_count": len(imports),
                "symbol_count": len(symbols),
                "file_size_bytes": file_path.stat().st_size,
            }
        except Exception as e:
            ast_index.file_metadata[str(file_path)] = {
                "language": language,
                "error": str(e),
            }

    def _parse_file_with_mmap(self, file_path: Path, language: str) -> Any:
        """Parse a large file using memory mapping for efficiency."""
        try:
            with open(file_path, encoding="utf-8") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    # Read content from memory-mapped file
                    content = mmapped_file.read().decode("utf-8")

                    # Create a temporary file-like object for tree-sitter
                    # Note: This is a simplified approach; in production you might
                    # want to use tree-sitter's streaming capabilities
                    return self.tree_sitter_parser.parse_file(str(file_path), language)
        except Exception as e:
            print(f"Error memory-mapping file {file_path}: {e}")
            # Fallback to regular parsing
            return self.tree_sitter_parser.parse_file(str(file_path), language)

    def generate_embeddings(self, code_chunks: list[CodeChunk]) -> list[Any]:
        """Generate vector embeddings for code chunks.

        Args:
            code_chunks: List of code chunks to embed

        Returns:
            List of embeddings (implementation depends on vector DB)
        """
        if not code_chunks:
            return []

        print(f"Generating embeddings for {len(code_chunks)} chunks...")

        # Use batch processing for efficiency
        batch_size = 50
        all_embeddings = []

        for i in range(0, len(code_chunks), batch_size):
            batch = code_chunks[i : i + batch_size]

            try:
                # Generate embeddings through vector database
                batch_embeddings = self.vector_db._generate_embeddings_batch(
                    [chunk.content for chunk in batch]
                )
                all_embeddings.extend(batch_embeddings)

                if i % (batch_size * 5) == 0:  # Progress update every 5 batches
                    print(
                        f"Generated embeddings for {min(i + batch_size, len(code_chunks))}/{len(code_chunks)} chunks"
                    )

            except Exception as e:
                print(
                    f"Warning: Error generating embeddings for batch {i // batch_size}: {e}"
                )
                # Add empty embeddings for failed batch
                all_embeddings.extend([None] * len(batch))

        return all_embeddings

    def store_embeddings(self, embeddings: list[Any]) -> bool:
        """Store embeddings in the vector database.

        Args:
            embeddings: List of embeddings to store

        Returns:
            True if storage successful
        """
        try:
            # This is handled by the vector database's store_embeddings method
            # which is called during build_index
            return True
        except Exception as e:
            print(f"Error storing embeddings: {e}")
            return False

    def query_similar_code(self, query: str, limit: int = 10) -> list[Any]:
        """Query for similar code using vector similarity.

        Args:
            query: Text query to search for
            limit: Maximum number of results

        Returns:
            List of CodeMatch objects
        """
        try:
            return self.vector_db.query_similar(query, k=limit)
        except Exception as e:
            print(f"Error querying similar code: {e}")
            return []

    def get_symbol_map(self) -> dict[str, SymbolInfo]:
        """Get a map of all symbols in the codebase.

        Returns:
            Dictionary mapping symbol keys to SymbolInfo objects
        """
        if not self.ast_index:
            # Try to load existing index
            self._load_existing_index()

        if self.ast_index:
            return self.ast_index.symbols
        else:
            return {}

    def get_index_metadata(self) -> IndexMetadata | None:
        """Get metadata about the current index.

        Returns:
            IndexMetadata object or None if no index exists
        """
        return self.index_metadata

    def _discover_source_files(self) -> list[Path]:
        """Discover all source files in the project.

        Returns:
            List of source file paths
        """
        source_files = []

        # Directories to skip
        skip_dirs = {
            ".git",
            ".svn",
            ".hg",  # Version control
            "__pycache__",
            ".pytest_cache",  # Python cache
            "node_modules",
            ".npm",  # Node.js
            ".venv",
            "venv",
            "env",  # Virtual environments
            "build",
            "dist",
            "target",  # Build outputs
            ".idea",
            ".vscode",  # IDEs
            ".dev_agent",  # Our own directory
        }

        def should_skip_dir(dir_path: Path) -> bool:
            """Check if directory should be skipped."""
            return dir_path.name in skip_dirs or (
                dir_path.name.startswith(".")
                and dir_path.name not in {".github", ".gitlab"}
            )

        # Walk through project directory
        for root, dirs, files in os.walk(self.project_path):
            root_path = Path(root)

            # Filter out directories to skip
            dirs[:] = [d for d in dirs if not should_skip_dir(root_path / d)]

            # Add source files
            for file in files:
                file_path = root_path / file
                if file_path.suffix in self.supported_extensions:
                    # Additional checks
                    if (
                        not file.startswith(".")
                        and file_path.stat().st_size > 0
                        and file_path.stat().st_size
                        < 10 * 1024 * 1024  # Skip files > 10MB
                    ):
                        source_files.append(file_path)

        return sorted(source_files)

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()

        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
        }

        return language_map.get(ext, "unknown")

    def _save_index_metadata(
        self, ast_index: ASTIndex, source_files: list[Path], embeddings_count: int
    ) -> None:
        """Save index metadata to disk."""
        total_lines = sum(
            metadata.get("line_count", 0)
            for metadata in ast_index.file_metadata.values()
        )

        languages_detected = list(
            set(
                metadata.get("language", "unknown")
                for metadata in ast_index.file_metadata.values()
            )
        )

        # Create IndexMetadata
        self.index_metadata = IndexMetadata(
            total_files=len(source_files),
            total_lines=total_lines,
            languages_detected=languages_detected,
            index_size_mb=self._calculate_index_size(),
            last_indexed=time.time(),
            index_version="1.0",
        )

        # Save to disk
        metadata_file = self.index_path / "index_metadata.json"
        try:
            with open(metadata_file, "w") as f:
                json.dump(asdict(self.index_metadata), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save index metadata: {e}")

        # Save AST index
        ast_file = self.index_path / "ast_index.json"
        try:
            # Convert AST index to serializable format
            ast_data = {
                "functions": {k: asdict(v) for k, v in ast_index.functions.items()},
                "classes": {k: asdict(v) for k, v in ast_index.classes.items()},
                "imports": [asdict(imp) for imp in ast_index.imports],
                "symbols": {k: asdict(v) for k, v in ast_index.symbols.items()},
                "file_metadata": ast_index.file_metadata,
            }

            with open(ast_file, "w") as f:
                json.dump(ast_data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save AST index: {e}")

        # Store in memory
        self.ast_index = ast_index

    def _load_existing_index(self) -> bool:
        """Load existing index from disk if available.

        Returns:
            True if index was loaded successfully
        """
        metadata_file = self.index_path / "index_metadata.json"
        ast_file = self.index_path / "ast_index.json"

        if not (metadata_file.exists() and ast_file.exists()):
            return False

        try:
            # Load metadata
            with open(metadata_file) as f:
                metadata_dict = json.load(f)
                self.index_metadata = IndexMetadata(**metadata_dict)

            # Load AST index
            with open(ast_file) as f:
                ast_data = json.load(f)

            # Reconstruct AST index from serialized data
            from ..models.indexing import ClassDef, FunctionDef, Import, SymbolInfo

            functions = {}
            for k, v in ast_data["functions"].items():
                functions[k] = FunctionDef(**v)

            classes = {}
            for k, v in ast_data["classes"].items():
                classes[k] = ClassDef(**v)

            imports = [Import(**imp_data) for imp_data in ast_data["imports"]]

            symbols = {}
            for k, v in ast_data["symbols"].items():
                symbols[k] = SymbolInfo(**v)

            self.ast_index = ASTIndex(
                functions=functions,
                classes=classes,
                imports=imports,
                symbols=symbols,
                file_metadata=ast_data["file_metadata"],
            )

            print(
                f"Loaded existing index with {len(functions)} functions, {len(classes)} classes"
            )
            return True

        except Exception as e:
            print(f"Warning: Could not load existing index: {e}")
            return False

    def _calculate_index_size(self) -> float:
        """Calculate the total size of index files in MB."""
        total_size = 0

        for file_path in self.index_path.glob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size / (1024 * 1024)  # Convert to MB

    def is_index_stale(self, max_age_hours: int = 24) -> bool:
        """Check if the index is stale and needs rebuilding.

        Args:
            max_age_hours: Maximum age in hours before index is considered stale

        Returns:
            True if index should be rebuilt
        """
        if not self.index_metadata:
            return True

        # Check age
        age_hours = (time.time() - self.index_metadata.last_indexed) / 3600
        if age_hours > max_age_hours:
            return True

        # Check if source files have been modified
        source_files = self._discover_source_files()
        if len(source_files) != self.index_metadata.total_files:
            return True

        # Check modification times (simplified check)
        index_time = self.index_metadata.last_indexed
        for file_path in source_files[:10]:  # Check first 10 files for performance
            if file_path.stat().st_mtime > index_time:
                return True

        return False

    def rebuild_index_if_stale(self, max_age_hours: int = 24) -> bool:
        """Rebuild index if it's stale.

        Args:
            max_age_hours: Maximum age in hours before rebuilding

        Returns:
            True if index was rebuilt
        """
        if self.is_index_stale(max_age_hours):
            print("Index is stale, rebuilding...")
            result = self.build_index()
            return result.success
        else:
            print("Index is up to date")
            return False
