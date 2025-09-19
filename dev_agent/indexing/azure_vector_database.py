"""Enhanced vector database with Azure OpenAI embeddings support."""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np

from dev_agent.config.config_manager import DevAgentConfig
from dev_agent.models.indexing import CodeChunk
from dev_agent.models.results import CodeMatch
from dev_agent.services.azure_openai_service import AzureOpenAIService
from dev_agent.errors.exceptions import IndexingError

logger = logging.getLogger(__name__)


class AzureVectorDatabase:
    """Vector database with Azure OpenAI embeddings support."""
    
    def __init__(self, index_path: str, config: DevAgentConfig):
        """Initialize Azure vector database.
        
        Args:
            index_path: Path to store index files
            config: Dev agent configuration
        """
        self.index_path = Path(index_path)
        self.config = config
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Azure OpenAI service if configured
        self.use_azure_embeddings = config.indexing.use_azure_embeddings
        self.azure_service: Optional[AzureOpenAIService] = None
        
        if self.use_azure_embeddings:
            try:
                self.azure_service = AzureOpenAIService(config.azure_openai)
                logger.info("Azure OpenAI embeddings enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure OpenAI service: {e}")
                logger.info("Falling back to local embeddings")
                self.use_azure_embeddings = False
        
        # Fallback to local embeddings
        if not self.use_azure_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.local_model = SentenceTransformer(config.indexing.embedding_model)
                logger.info(f"Using local embeddings model: {config.indexing.embedding_model}")
            except ImportError:
                raise IndexingError(
                    "sentence-transformers not available and Azure OpenAI not configured. "
                    "Please install sentence-transformers or configure Azure OpenAI."
                )
        
        # FAISS index
        self.faiss_index: Optional[faiss.Index] = None
        self.chunk_metadata: List[Dict[str, Any]] = []
        self.embedding_dimension: Optional[int] = None
        
        # Load existing index if available
        self._load_existing_index()
    
    def _get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if self.embedding_dimension is not None:
            return self.embedding_dimension
        
        # Test with a small text to get dimension
        test_embeddings = self._generate_embeddings_batch(["test"])
        if test_embeddings and test_embeddings[0] is not None:
            self.embedding_dimension = len(test_embeddings[0])
        else:
            # Default dimensions for common models
            if self.use_azure_embeddings:
                self.embedding_dimension = 1536  # text-embedding-ada-002 dimension
            else:
                self.embedding_dimension = 384   # all-MiniLM-L6-v2 dimension
        
        return self.embedding_dimension
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (None for failed embeddings)
        """
        if not texts:
            return []
        
        try:
            if self.use_azure_embeddings and self.azure_service:
                # Use Azure OpenAI embeddings
                response = self.azure_service.generate_embeddings(texts)
                return response.embeddings
            else:
                # Use local embeddings
                embeddings = self.local_model.encode(texts, convert_to_numpy=True)
                return [embedding.tolist() for embedding in embeddings]
                
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            # Return None for all texts to indicate failure
            return [None] * len(texts)
    
    def store_embeddings(self, code_chunks: List[CodeChunk]) -> List[str]:
        """Store embeddings for code chunks.
        
        Args:
            code_chunks: List of code chunks to embed and store
            
        Returns:
            List of chunk IDs that were successfully stored
        """
        if not code_chunks:
            return []
        
        logger.info(f"Generating embeddings for {len(code_chunks)} code chunks")
        
        # Extract texts for embedding
        texts = [chunk.content for chunk in code_chunks]
        
        # Generate embeddings in batches
        batch_size = 20 if self.use_azure_embeddings else 50
        all_embeddings = []
        successful_chunks = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_chunks = code_chunks[i:i + batch_size]
            
            try:
                batch_embeddings = self._generate_embeddings_batch(batch_texts)
                
                # Filter out failed embeddings
                for j, embedding in enumerate(batch_embeddings):
                    if embedding is not None:
                        all_embeddings.append(embedding)
                        successful_chunks.append(batch_chunks[j])
                
                if i % (batch_size * 5) == 0:  # Progress update
                    logger.info(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} chunks")
                    
            except Exception as e:
                logger.error(f"Failed to process batch {i//batch_size}: {e}")
                continue
        
        if not all_embeddings:
            logger.error("No embeddings were generated successfully")
            return []
        
        logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
        
        # Convert to numpy array
        embeddings_array = np.array(all_embeddings, dtype=np.float32)
        
        # Initialize or update FAISS index
        dimension = self._get_embedding_dimension()
        
        if self.faiss_index is None:
            # Create new index
            self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            logger.info(f"Created new FAISS index with dimension {dimension}")
        
        # Add embeddings to index
        start_id = len(self.chunk_metadata)
        self.faiss_index.add(embeddings_array)
        
        # Store metadata
        chunk_ids = []
        for i, chunk in enumerate(successful_chunks):
            chunk_id = f"chunk_{start_id + i}"
            chunk_ids.append(chunk_id)
            
            metadata = {
                'id': chunk_id,
                'file_path': chunk.file_path,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line,
                'content': chunk.content,
                'chunk_type': chunk.chunk_type,
                'language': chunk.language,
                'function_name': getattr(chunk, 'function_name', None),
                'class_name': getattr(chunk, 'class_name', None),
            }
            self.chunk_metadata.append(metadata)
        
        logger.info(f"Stored {len(chunk_ids)} embeddings in FAISS index")
        return chunk_ids
    
    def query_similar(self, query: str, k: int = 10, threshold: float = 0.7) -> List[CodeMatch]:
        """Query for similar code chunks.
        
        Args:
            query: Text query to search for
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of CodeMatch objects
        """
        if self.faiss_index is None or not self.chunk_metadata:
            logger.warning("No embeddings available for querying")
            return []
        
        try:
            # Generate embedding for query
            query_embeddings = self._generate_embeddings_batch([query])
            if not query_embeddings or query_embeddings[0] is None:
                logger.error("Failed to generate embedding for query")
                return []
            
            query_vector = np.array([query_embeddings[0]], dtype=np.float32)
            
            # Search in FAISS index
            scores, indices = self.faiss_index.search(query_vector, min(k, len(self.chunk_metadata)))
            
            # Convert results to CodeMatch objects
            matches = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for invalid indices
                    continue
                
                # Convert inner product score to similarity (0-1 range)
                similarity = float(score)
                
                if similarity < threshold:
                    continue
                
                metadata = self.chunk_metadata[idx]
                
                match = CodeMatch(
                    file_path=metadata['file_path'],
                    start_line=metadata['start_line'],
                    end_line=metadata['end_line'],
                    content=metadata['content'],
                    similarity_score=similarity,
                    chunk_type=metadata['chunk_type'],
                    language=metadata['language'],
                    function_name=metadata.get('function_name'),
                    class_name=metadata.get('class_name'),
                )
                matches.append(match)
            
            logger.info(f"Found {len(matches)} similar code chunks for query")
            return matches
            
        except Exception as e:
            logger.error(f"Error querying similar code: {e}")
            return []
    
    def save_index(self) -> bool:
        """Save the FAISS index and metadata to disk.
        
        Returns:
            True if save was successful
        """
        try:
            if self.faiss_index is not None:
                # Save FAISS index
                faiss_path = self.index_path / "faiss_index.bin"
                faiss.write_index(self.faiss_index, str(faiss_path))
                logger.info(f"Saved FAISS index to {faiss_path}")
            
            # Save metadata
            metadata_path = self.index_path / "chunk_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_metadata, f, indent=2, ensure_ascii=False)
            
            # Save configuration
            config_path = self.index_path / "vector_config.json"
            config_data = {
                'use_azure_embeddings': self.use_azure_embeddings,
                'embedding_dimension': self.embedding_dimension,
                'total_chunks': len(self.chunk_metadata),
                'embedding_model': (
                    self.config.azure_openai.embedding_model if self.use_azure_embeddings
                    else self.config.indexing.embedding_model
                ),
            }
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved vector database with {len(self.chunk_metadata)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save vector database: {e}")
            return False
    
    def _load_existing_index(self) -> bool:
        """Load existing FAISS index and metadata from disk.
        
        Returns:
            True if load was successful
        """
        faiss_path = self.index_path / "faiss_index.bin"
        metadata_path = self.index_path / "chunk_metadata.json"
        config_path = self.index_path / "vector_config.json"
        
        if not all(p.exists() for p in [faiss_path, metadata_path, config_path]):
            logger.info("No existing vector database found")
            return False
        
        try:
            # Load FAISS index
            self.faiss_index = faiss.read_index(str(faiss_path))
            
            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.chunk_metadata = json.load(f)
            
            # Load configuration
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                self.embedding_dimension = config_data.get('embedding_dimension')
            
            logger.info(f"Loaded existing vector database with {len(self.chunk_metadata)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load existing vector database: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database.
        
        Returns:
            Dictionary with database statistics
        """
        stats = {
            'total_chunks': len(self.chunk_metadata),
            'embedding_dimension': self.embedding_dimension,
            'use_azure_embeddings': self.use_azure_embeddings,
            'index_exists': self.faiss_index is not None,
        }
        
        if self.faiss_index is not None:
            stats['faiss_index_size'] = self.faiss_index.ntotal
        
        # Language distribution
        languages = {}
        for metadata in self.chunk_metadata:
            lang = metadata.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1
        stats['language_distribution'] = languages
        
        # Chunk type distribution
        chunk_types = {}
        for metadata in self.chunk_metadata:
            chunk_type = metadata.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        stats['chunk_type_distribution'] = chunk_types
        
        return stats
    
    def clear_index(self) -> bool:
        """Clear the vector database.
        
        Returns:
            True if clear was successful
        """
        try:
            self.faiss_index = None
            self.chunk_metadata = []
            self.embedding_dimension = None
            
            # Remove files
            for file_path in [
                self.index_path / "faiss_index.bin",
                self.index_path / "chunk_metadata.json",
                self.index_path / "vector_config.json",
            ]:
                if file_path.exists():
                    file_path.unlink()
            
            logger.info("Cleared vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear vector database: {e}")
            return False
    
    def test_azure_connection(self) -> bool:
        """Test Azure OpenAI connection for embeddings.
        
        Returns:
            True if connection is successful
        """
        if not self.use_azure_embeddings or not self.azure_service:
            return False
        
        try:
            # Test with a simple embedding
            embeddings = self._generate_embeddings_batch(["test connection"])
            return embeddings and embeddings[0] is not None
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {e}")
            return False