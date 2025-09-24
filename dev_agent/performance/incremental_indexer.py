"""Incremental indexing system for large codebases with change detection."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..interfaces.indexing_interface import IIndexingEngine
from ..models.indexing import ASTIndex, CodeChunk, SymbolInfo
from ..models.project_state import IndexMetadata
from ..models.results import IndexResult
from .performance_optimizer import PerformanceOptimizer

logger = logging.getLogger(__name__)


@dataclass
class FileChangeInfo:
    """Information about file changes."""
    
    path: str
    change_type: str  # 'added', 'modified', 'deleted'
    old_hash: Optional[str]
    new_hash: Optional[str]
    timestamp: float


@dataclass
class IncrementalIndexConfig:
    """Configuration for incremental indexing."""
    
    enable_change_detection: bool = True
    hash_algorithm: str = "md5"
    batch_size: int = 50
    max_workers: int = 4
    enable_dependency_tracking: bool = True
    enable_smart_invalidation: bool = True
    checkpoint_interval: int = 100  # Files processed between checkpoints


class IncrementalIndexer:
    """Incremental indexing system with intelligent change detection."""

    def __init__(
        self,
        base_indexer: IIndexingEngine,
        project_path: str,
        config: Optional[IncrementalIndexConfig] = None,
        performance_optimizer: Optional[PerformanceOptimizer] = None,
    ):
        """Initialize the incremental indexer.
        
        Args:
            base_indexer: Base indexing engine to wrap
            project_path: Path to the project root
            config: Incremental indexing configuration
            performance_optimizer: Performance optimizer instance
        """
        self.base_indexer = base_indexer
        self.project_path = Path(project_path)
        self.config = config or IncrementalIndexConfig()
        self.performance_optimizer = performance_optimizer
        
        # Index state tracking
        self.index_dir = self.project_path / ".dev_agent" / "incremental_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # File tracking
        self.file_hashes: Dict[str, str] = {}
        self.file_timestamps: Dict[str, float] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}
        
        # Change tracking
        self.pending_changes: List[FileChangeInfo] = []
        self.processed_files: Set[str] = set()
        
        # Load existing state
        self._load_incremental_state()
        
        logger.info("IncrementalIndexer initialized")

    def build_incremental_index(
        self,
        force_full_rebuild: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> IndexResult:
        """Build incremental index with change detection.
        
        Args:
            force_full_rebuild: Force complete rebuild instead of incremental
            progress_callback: Progress callback function
            
        Returns:
            Index result with incremental statistics
        """
        start_time = time.time()
        
        if force_full_rebuild:
            logger.info("Performing full index rebuild")
            return self._build_full_index(progress_callback)
        
        logger.info("Starting incremental index build")
        
        # Detect changes
        changes = self._detect_file_changes()
        
        if not changes:
            logger.info("No changes detected, index is up to date")
            return IndexResult(
                success=True,
                message="Index is up to date",
                files_processed=0,
                symbols_found=len(self.base_indexer.ast_index.symbols) if self.base_indexer.ast_index else 0,
                processing_time=time.time() - start_time,
                metadata=self._get_current_metadata(),
            )
        
        logger.info(f"Detected {len(changes)} file changes")
        
        # Process changes incrementally
        result = self._process_incremental_changes(changes, progress_callback)
        
        # Save updated state
        self._save_incremental_state()
        
        return result

    def invalidate_file(self, file_path: str) -> None:
        """Invalidate a specific file and its dependents.
        
        Args:
            file_path: Path to the file to invalidate
        """
        abs_path = str(Path(file_path).resolve())
        
        # Remove from processed files
        self.processed_files.discard(abs_path)
        
        # Invalidate dependents if smart invalidation is enabled
        if self.config.enable_smart_invalidation:
            dependents = self._get_all_dependents(abs_path)
            for dependent in dependents:
                self.processed_files.discard(dependent)
            
            logger.info(f"Invalidated {abs_path} and {len(dependents)} dependents")
        else:
            logger.info(f"Invalidated {abs_path}")

    def get_change_summary(self) -> Dict[str, Any]:
        """Get summary of recent changes.
        
        Returns:
            Dictionary with change statistics
        """
        if not self.pending_changes:
            return {"total_changes": 0}
        
        change_types = {}
        for change in self.pending_changes:
            change_types[change.change_type] = change_types.get(change.change_type, 0) + 1
        
        return {
            "total_changes": len(self.pending_changes),
            "change_types": change_types,
            "oldest_change": min(change.timestamp for change in self.pending_changes),
            "newest_change": max(change.timestamp for change in self.pending_changes),
        }

    def optimize_index_structure(self) -> None:
        """Optimize index structure for better performance."""
        logger.info("Optimizing incremental index structure")
        
        # Clean up orphaned entries
        self._cleanup_orphaned_entries()
        
        # Optimize dependency graph
        self._optimize_dependency_graph()
        
        # Compact file tracking data
        self._compact_file_tracking()
        
        logger.info("Index structure optimization completed")

    def _detect_file_changes(self) -> List[FileChangeInfo]:
        """Detect changes in the codebase since last index."""
        changes = []
        current_files = set()
        
        # Scan current files
        for file_path in self._discover_source_files():
            current_files.add(str(file_path))
            
            # Calculate current hash
            current_hash = self._calculate_file_hash(file_path)
            old_hash = self.file_hashes.get(str(file_path))
            
            if old_hash is None:
                # New file
                changes.append(FileChangeInfo(
                    path=str(file_path),
                    change_type="added",
                    old_hash=None,
                    new_hash=current_hash,
                    timestamp=time.time(),
                ))
            elif old_hash != current_hash:
                # Modified file
                changes.append(FileChangeInfo(
                    path=str(file_path),
                    change_type="modified",
                    old_hash=old_hash,
                    new_hash=current_hash,
                    timestamp=time.time(),
                ))
        
        # Check for deleted files
        for tracked_file in set(self.file_hashes.keys()):
            if tracked_file not in current_files:
                changes.append(FileChangeInfo(
                    path=tracked_file,
                    change_type="deleted",
                    old_hash=self.file_hashes[tracked_file],
                    new_hash=None,
                    timestamp=time.time(),
                ))
        
        self.pending_changes = changes
        return changes

    def _process_incremental_changes(
        self,
        changes: List[FileChangeInfo],
        progress_callback: Optional[callable] = None,
    ) -> IndexResult:
        """Process incremental changes to update the index."""
        start_time = time.time()
        total_changes = len(changes)
        processed_count = 0
        errors = []
        
        # Group changes by type for efficient processing
        added_files = [c for c in changes if c.change_type == "added"]
        modified_files = [c for c in changes if c.change_type == "modified"]
        deleted_files = [c for c in changes if c.change_type == "deleted"]
        
        # Process deletions first
        for change in deleted_files:
            try:
                self._process_file_deletion(change)
                processed_count += 1
                
                if progress_callback:
                    progress_callback(processed_count, total_changes, f"Deleted {change.path}")
                    
            except Exception as e:
                error_msg = f"Error processing deletion {change.path}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Process additions and modifications in batches
        files_to_process = added_files + modified_files
        
        if files_to_process:
            batch_results = self._process_file_batches(
                files_to_process,
                progress_callback,
                processed_count,
                total_changes,
            )
            processed_count += len(batch_results)
            errors.extend(batch_results.get('errors', []))
        
        # Update tracking data
        for change in changes:
            if change.change_type == "deleted":
                self.file_hashes.pop(change.path, None)
                self.file_timestamps.pop(change.path, None)
            else:
                self.file_hashes[change.path] = change.new_hash
                self.file_timestamps[change.path] = change.timestamp
        
        # Calculate final statistics
        symbols_count = len(self.base_indexer.ast_index.symbols) if self.base_indexer.ast_index else 0
        
        return IndexResult(
            success=len(errors) == 0,
            message=f"Processed {processed_count} changes" + (f" with {len(errors)} errors" if errors else ""),
            files_processed=processed_count,
            symbols_found=symbols_count,
            processing_time=time.time() - start_time,
            metadata=self._get_current_metadata(),
            errors=errors,
        )

    def _process_file_deletion(self, change: FileChangeInfo) -> None:
        """Process deletion of a file."""
        file_path = change.path
        
        # Remove from AST index if it exists
        if self.base_indexer.ast_index:
            # Remove symbols from this file
            symbols_to_remove = [
                symbol_id for symbol_id, symbol in self.base_indexer.ast_index.symbols.items()
                if symbol.file_path == file_path
            ]
            
            for symbol_id in symbols_to_remove:
                self.base_indexer.ast_index.symbols.pop(symbol_id, None)
            
            # Remove functions from this file
            functions_to_remove = [
                func_id for func_id, func in self.base_indexer.ast_index.functions.items()
                if func.file_path == file_path
            ]
            
            for func_id in functions_to_remove:
                self.base_indexer.ast_index.functions.pop(func_id, None)
            
            # Remove classes from this file
            classes_to_remove = [
                class_id for class_id, cls in self.base_indexer.ast_index.classes.items()
                if cls.file_path == file_path
            ]
            
            for class_id in classes_to_remove:
                self.base_indexer.ast_index.classes.pop(class_id, None)
        
        # Remove from dependency tracking
        self.dependency_graph.pop(file_path, None)
        self.reverse_dependencies.pop(file_path, None)
        
        # Remove from reverse dependencies of other files
        for deps in self.reverse_dependencies.values():
            deps.discard(file_path)
        
        logger.debug(f"Processed deletion of {file_path}")

    def _process_file_batches(
        self,
        changes: List[FileChangeInfo],
        progress_callback: Optional[callable],
        initial_count: int,
        total_changes: int,
    ) -> Dict[str, Any]:
        """Process file changes in optimized batches."""
        batch_size = self.config.batch_size
        max_workers = self.config.max_workers
        errors = []
        processed_files = []
        
        # Process in batches
        for i in range(0, len(changes), batch_size):
            batch = changes[i:i + batch_size]
            
            if self.performance_optimizer:
                # Use performance optimizer for batch processing
                operations = [
                    (self._process_single_file_change, (change,), {})
                    for change in batch
                ]
                
                batch_results = self.performance_optimizer.optimize_batch_operations(
                    operations,
                    use_processes=False,  # Use threads for I/O bound operations
                )
                
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        errors.append(f"Error processing {batch[j].path}: {result}")
                    else:
                        processed_files.append(batch[j].path)
            else:
                # Fallback to thread pool
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_change = {
                        executor.submit(self._process_single_file_change, change): change
                        for change in batch
                    }
                    
                    for future in as_completed(future_to_change):
                        change = future_to_change[future]
                        try:
                            future.result()
                            processed_files.append(change.path)
                        except Exception as e:
                            errors.append(f"Error processing {change.path}: {e}")
            
            # Update progress
            current_count = initial_count + len(processed_files)
            if progress_callback:
                progress_callback(
                    current_count,
                    total_changes,
                    f"Processed batch {i // batch_size + 1}"
                )
            
            # Checkpoint periodically
            if len(processed_files) % self.config.checkpoint_interval == 0:
                self._save_incremental_state()
        
        return {
            'processed_files': processed_files,
            'errors': errors,
        }

    def _process_single_file_change(self, change: FileChangeInfo) -> None:
        """Process a single file change."""
        file_path = Path(change.path)
        
        if not file_path.exists():
            logger.warning(f"File {file_path} no longer exists, skipping")
            return
        
        # Use base indexer to process the file
        # This is a simplified approach - in practice, you'd want to
        # integrate more deeply with the base indexer's internals
        
        try:
            # Read and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update dependency tracking if enabled
            if self.config.enable_dependency_tracking:
                self._update_file_dependencies(str(file_path), content)
            
            # Mark as processed
            self.processed_files.add(str(file_path))
            
            logger.debug(f"Processed {change.change_type} for {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            raise

    def _update_file_dependencies(self, file_path: str, content: str) -> None:
        """Update dependency tracking for a file."""
        # Extract imports and dependencies from content
        dependencies = self._extract_dependencies(content)
        
        # Update dependency graph
        old_deps = self.dependency_graph.get(file_path, set())
        new_deps = set(dependencies)
        
        self.dependency_graph[file_path] = new_deps
        
        # Update reverse dependencies
        # Remove old reverse dependencies
        for old_dep in old_deps:
            if old_dep in self.reverse_dependencies:
                self.reverse_dependencies[old_dep].discard(file_path)
        
        # Add new reverse dependencies
        for new_dep in new_deps:
            if new_dep not in self.reverse_dependencies:
                self.reverse_dependencies[new_dep] = set()
            self.reverse_dependencies[new_dep].add(file_path)

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract file dependencies from content."""
        dependencies = []
        
        # Simple regex-based extraction for Python imports
        import re
        
        # Match import statements
        import_patterns = [
            r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
            r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend(matches)
        
        # Convert module names to potential file paths
        file_dependencies = []
        for dep in dependencies:
            # Convert module.submodule to module/submodule.py
            potential_path = dep.replace('.', '/') + '.py'
            file_dependencies.append(potential_path)
        
        return file_dependencies

    def _get_all_dependents(self, file_path: str) -> Set[str]:
        """Get all files that depend on the given file."""
        dependents = set()
        to_check = {file_path}
        checked = set()
        
        while to_check:
            current = to_check.pop()
            if current in checked:
                continue
            
            checked.add(current)
            
            # Get direct dependents
            direct_dependents = self.reverse_dependencies.get(current, set())
            dependents.update(direct_dependents)
            
            # Add to check queue for transitive dependencies
            to_check.update(direct_dependents - checked)
        
        return dependents

    def _build_full_index(self, progress_callback: Optional[callable] = None) -> IndexResult:
        """Build a complete index from scratch."""
        # Clear existing state
        self.file_hashes.clear()
        self.file_timestamps.clear()
        self.dependency_graph.clear()
        self.reverse_dependencies.clear()
        self.processed_files.clear()
        
        # Use base indexer to build full index
        result = self.base_indexer.build_index()
        
        if result.success:
            # Update tracking data for all files
            for file_path in self._discover_source_files():
                file_hash = self._calculate_file_hash(file_path)
                self.file_hashes[str(file_path)] = file_hash
                self.file_timestamps[str(file_path)] = time.time()
                self.processed_files.add(str(file_path))
        
        return result

    def _discover_source_files(self) -> List[Path]:
        """Discover all source files in the project."""
        source_files = []
        supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp'}
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip hidden directories and common build/cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'build', 'dist', 'target'
            }]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in supported_extensions:
                    source_files.append(file_path)
        
        return source_files

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file."""
        hash_func = hashlib.new(self.config.hash_algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash {file_path}: {e}")
            return ""

    def _get_current_metadata(self) -> IndexMetadata:
        """Get current index metadata."""
        return IndexMetadata(
            total_files=len(self.file_hashes),
            indexed_files=len(self.processed_files),
            last_updated=time.time(),
            index_version="incremental_v1",
        )

    def _load_incremental_state(self) -> None:
        """Load incremental indexing state from disk."""
        state_file = self.index_dir / "incremental_state.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.file_hashes = state.get('file_hashes', {})
                self.file_timestamps = state.get('file_timestamps', {})
                self.dependency_graph = {
                    k: set(v) for k, v in state.get('dependency_graph', {}).items()
                }
                self.reverse_dependencies = {
                    k: set(v) for k, v in state.get('reverse_dependencies', {}).items()
                }
                self.processed_files = set(state.get('processed_files', []))
                
                logger.info(f"Loaded incremental state for {len(self.file_hashes)} files")
                
            except Exception as e:
                logger.warning(f"Failed to load incremental state: {e}")

    def _save_incremental_state(self) -> None:
        """Save incremental indexing state to disk."""
        state_file = self.index_dir / "incremental_state.json"
        
        try:
            state = {
                'file_hashes': self.file_hashes,
                'file_timestamps': self.file_timestamps,
                'dependency_graph': {
                    k: list(v) for k, v in self.dependency_graph.items()
                },
                'reverse_dependencies': {
                    k: list(v) for k, v in self.reverse_dependencies.items()
                },
                'processed_files': list(self.processed_files),
                'last_saved': time.time(),
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.debug("Saved incremental indexing state")
            
        except Exception as e:
            logger.error(f"Failed to save incremental state: {e}")

    def _cleanup_orphaned_entries(self) -> None:
        """Clean up orphaned entries in tracking data."""
        # Remove entries for files that no longer exist
        existing_files = {str(f) for f in self._discover_source_files()}
        
        orphaned_files = set(self.file_hashes.keys()) - existing_files
        
        for orphaned in orphaned_files:
            self.file_hashes.pop(orphaned, None)
            self.file_timestamps.pop(orphaned, None)
            self.dependency_graph.pop(orphaned, None)
            self.reverse_dependencies.pop(orphaned, None)
            self.processed_files.discard(orphaned)
        
        if orphaned_files:
            logger.info(f"Cleaned up {len(orphaned_files)} orphaned entries")

    def _optimize_dependency_graph(self) -> None:
        """Optimize dependency graph structure."""
        # Remove empty dependency sets
        empty_keys = [k for k, v in self.dependency_graph.items() if not v]
        for key in empty_keys:
            self.dependency_graph.pop(key, None)
        
        empty_reverse_keys = [k for k, v in self.reverse_dependencies.items() if not v]
        for key in empty_reverse_keys:
            self.reverse_dependencies.pop(key, None)

    def _compact_file_tracking(self) -> None:
        """Compact file tracking data structures."""
        # Remove very old timestamp entries (older than 30 days)
        cutoff_time = time.time() - (30 * 24 * 3600)
        
        old_entries = [
            path for path, timestamp in self.file_timestamps.items()
            if timestamp < cutoff_time and path not in self.processed_files
        ]
        
        for path in old_entries:
            self.file_timestamps.pop(path, None)
        
        if old_entries:
            logger.info(f"Compacted {len(old_entries)} old timestamp entries")