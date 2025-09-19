"""Enhanced indexing engine with Azure OpenAI embeddings support."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dev_agent.config.config_manager import DevAgentConfig
from dev_agent.indexing.indexing_engine import IndexingEngine
from dev_agent.indexing.azure_vector_database import AzureVectorDatabase
from dev_agent.models.indexing import CodeChunk
from dev_agent.models.results import CodeMatch, IndexResult

logger = logging.getLogger(__name__)


class EnhancedIndexingEngine(IndexingEngine):
    """Enhanced indexing engine with Azure OpenAI embeddings support."""
    
    def __init__(self, project_path: str, config: DevAgentConfig, index_path: Optional[str] = None):
        """Initialize the enhanced indexing engine.
        
        Args:
            project_path: Path to the project root
            config: Dev agent configuration
            index_path: Custom path for index storage (optional)
        """
        # Initialize base indexing engine
        super().__init__(project_path, index_path)
        
        self.config = config
        
        # Replace vector database with Azure-enabled version
        self.vector_db = AzureVectorDatabase(str(self.index_path), config)
        
        logger.info(f"Enhanced indexing engine initialized with Azure support: {config.indexing.use_azure_embeddings}")
    
    def build_index(self) -> IndexResult:
        """Build a complete index with enhanced Azure OpenAI support.
        
        Returns:
            IndexResult with success status and metadata
        """
        start_time = time.time()
        errors = []
        
        try:
            logger.info("Starting enhanced codebase indexing with Azure OpenAI support")
            
            # Test Azure connection if enabled
            if self.config.indexing.use_azure_embeddings:
                if not self.vector_db.test_azure_connection():
                    logger.warning("Azure OpenAI connection test failed, falling back to local embeddings")
                    self.config.indexing.use_azure_embeddings = False
                    # Reinitialize vector database with updated config
                    self.vector_db = AzureVectorDatabase(str(self.index_path), self.config)
            
            # Step 1: Discover files
            logger.info("Discovering source files...")
            source_files = self._discover_source_files()
            self.total_files = len(source_files)
            
            if not source_files:
                return IndexResult(
                    success=False,
                    ast_index=None,
                    embeddings_count=0,
                    errors=["No source files found in project"],
                    metadata={}
                )
            
            logger.info(f"Found {len(source_files)} source files")
            self._update_progress(0, len(source_files), "Starting AST parsing...")
            
            # Step 2: Parse AST for all files
            logger.info("Parsing AST for all files...")
            ast_index = self.parse_codebase_ast()
            
            if not ast_index:
                return IndexResult(
                    success=False,
                    ast_index=None,
                    embeddings_count=0,
                    errors=["Failed to parse codebase AST"],
                    metadata={}
                )
            
            # Step 3: Generate enhanced code chunks
            logger.info("Generating enhanced code chunks...")
            self._update_progress(len(source_files) // 2, len(source_files), "Generating code chunks...")
            
            all_chunks = self._generate_enhanced_chunks(source_files, ast_index)
            
            if not all_chunks:
                logger.warning("No code chunks generated")
                all_chunks = []
            
            logger.info(f"Generated {len(all_chunks)} enhanced code chunks")
            
            # Step 4: Generate and store embeddings with Azure OpenAI
            logger.info("Generating embeddings with Azure OpenAI support...")
            self._update_progress(3 * len(source_files) // 4, len(source_files), "Generating embeddings...")
            
            embeddings_count = 0
            if all_chunks:
                chunk_ids = self.vector_db.store_embeddings(all_chunks)
                embeddings_count = len(chunk_ids)
                logger.info(f"Generated {embeddings_count} embeddings")
            
            # Step 5: Save enhanced index to disk
            logger.info("Saving enhanced index to disk...")
            self._save_index_metadata(ast_index, source_files, embeddings_count)
            self.vector_db.save_index()
            
            # Update progress to complete
            self._update_progress(len(source_files), len(source_files), "Enhanced indexing complete!")
            
            # Create enhanced metadata
            end_time = time.time()
            total_lines = sum(
                metadata.get('line_count', 0) 
                for metadata in ast_index.file_metadata.values()
            )
            
            languages_detected = list(set(
                metadata.get('language', 'unknown')
                for metadata in ast_index.file_metadata.values()
            ))
            
            # Get vector database stats
            vector_stats = self.vector_db.get_stats()
            
            metadata = {
                'indexing_time_seconds': end_time - start_time,
                'total_files': len(source_files),
                'total_lines': total_lines,
                'total_chunks': len(all_chunks),
                'embeddings_count': embeddings_count,
                'languages_detected': languages_detected,
                'functions_count': len(ast_index.functions),
                'classes_count': len(ast_index.classes),
                'imports_count': len(ast_index.imports),
                'symbols_count': len(ast_index.symbols),
                'use_azure_embeddings': self.config.indexing.use_azure_embeddings,
                'embedding_model': (
                    self.config.azure_openai.embedding_model if self.config.indexing.use_azure_embeddings
                    else self.config.indexing.embedding_model
                ),
                'vector_stats': vector_stats,
            }
            
            logger.info(f"Enhanced indexing completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Indexed {len(source_files)} files, {total_lines} lines of code")
            logger.info(f"Generated {embeddings_count} embeddings from {len(all_chunks)} chunks")
            logger.info(f"Using Azure embeddings: {self.config.indexing.use_azure_embeddings}")
            
            return IndexResult(
                success=True,
                ast_index=ast_index,
                embeddings_count=embeddings_count,
                errors=errors,
                metadata=metadata
            )
            
        except Exception as e:
            error_msg = f"Critical error during enhanced indexing: {e}"
            errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
            
            return IndexResult(
                success=False,
                ast_index=None,
                embeddings_count=0,
                errors=errors,
                metadata={}
            )
    
    def _generate_enhanced_chunks(self, source_files: List[Path], ast_index) -> List[CodeChunk]:
        """Generate enhanced code chunks with better context.
        
        Args:
            source_files: List of source files
            ast_index: AST index with parsed information
            
        Returns:
            List of enhanced code chunks
        """
        all_chunks = []
        
        for i, file_path in enumerate(source_files):
            try:
                # Use AST-based chunking when possible for better context
                chunks = self.code_chunker.chunk_from_ast(ast_index, str(file_path))
                
                if not chunks:
                    # Fallback to content-based chunking
                    chunks = self.code_chunker.chunk_file(str(file_path))
                
                # Enhance chunks with additional context
                enhanced_chunks = self._enhance_chunks_with_context(chunks, ast_index, file_path)
                all_chunks.extend(enhanced_chunks)
                
                if i % 10 == 0:  # Update progress every 10 files
                    self._update_progress(
                        len(source_files) // 2 + i // 2, 
                        len(source_files), 
                        f"Enhanced chunking file {i+1}/{len(source_files)}"
                    )
                    
            except Exception as e:
                error_msg = f"Error enhancing chunks for file {file_path}: {e}"
                logger.warning(error_msg)
                continue
        
        # Optimize chunks with enhanced logic
        logger.info(f"Optimizing {len(all_chunks)} enhanced chunks...")
        all_chunks = self.code_chunker.optimize_chunks(all_chunks)
        logger.info(f"Optimized to {len(all_chunks)} enhanced chunks")
        
        return all_chunks
    
    def _enhance_chunks_with_context(
        self, chunks: List[CodeChunk], ast_index, file_path: Path
    ) -> List[CodeChunk]:
        """Enhance code chunks with additional context information.
        
        Args:
            chunks: Original code chunks
            ast_index: AST index with parsed information
            file_path: Path to the source file
            
        Returns:
            List of enhanced code chunks
        """
        enhanced_chunks = []
        file_str = str(file_path)
        
        for chunk in chunks:
            # Add function and class context
            function_name = None
            class_name = None
            
            # Find containing function
            for func_key, func_def in ast_index.functions.items():
                if (func_def.file_path == file_str and 
                    func_def.start_line <= chunk.start_line <= func_def.end_line):
                    function_name = func_def.name
                    break
            
            # Find containing class
            for class_key, class_def in ast_index.classes.items():
                if (class_def.file_path == file_str and 
                    class_def.start_line <= chunk.start_line <= class_def.end_line):
                    class_name = class_def.name
                    break
            
            # Create enhanced chunk with additional attributes
            enhanced_chunk = CodeChunk(
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
                chunk_type=chunk.chunk_type,
                language=chunk.language,
            )
            
            # Add context as attributes (if the CodeChunk model supports it)
            if hasattr(enhanced_chunk, 'function_name'):
                enhanced_chunk.function_name = function_name
            if hasattr(enhanced_chunk, 'class_name'):
                enhanced_chunk.class_name = class_name
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def query_similar_code(self, query: str, limit: int = 10, threshold: float = 0.7) -> List[CodeMatch]:
        """Query for similar code using enhanced vector similarity.
        
        Args:
            query: Text query to search for
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of CodeMatch objects with enhanced context
        """
        try:
            matches = self.vector_db.query_similar(query, k=limit, threshold=threshold)
            
            logger.info(f"Found {len(matches)} similar code matches for query: '{query[:50]}...'")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error querying similar code: {e}")
            return []
    
    def get_vector_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database.
        
        Returns:
            Dictionary with vector database statistics
        """
        return self.vector_db.get_stats()
    
    def test_azure_connection(self) -> bool:
        """Test Azure OpenAI connection.
        
        Returns:
            True if connection is successful
        """
        if not self.config.indexing.use_azure_embeddings:
            return False
        
        return self.vector_db.test_azure_connection()


def create_indexing_engine(
    project_path: str, config: DevAgentConfig, index_path: Optional[str] = None
) -> EnhancedIndexingEngine:
    """Create an enhanced indexing engine with Azure OpenAI support.
    
    Args:
        project_path: Path to the project root
        config: Dev agent configuration
        index_path: Custom path for index storage (optional)
        
    Returns:
        Enhanced indexing engine instance
    """
    return EnhancedIndexingEngine(project_path, config, index_path)