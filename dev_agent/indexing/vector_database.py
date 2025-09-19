"""Vector database implementation for code embeddings using FAISS."""

import hashlib
import json
from pathlib import Path
from typing import Any

from ..models.indexing import CodeChunk, CodeMatch

try:
    import faiss
    import numpy as np

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

    # Mock classes for testing without FAISS
    class faiss:
        @staticmethod
        def IndexFlatIP(dim):
            return MockIndex()

        @staticmethod
        def IndexFlatL2(dim):
            return MockIndex()

    import numpy as np

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

    # Mock for testing without sentence-transformers
    class SentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name

        def encode(self, texts, **kwargs):
            # Return mock embeddings
            return np.random.rand(len(texts), 384).astype(np.float32)


class MockIndex:
    """Mock FAISS index for testing without FAISS."""

    def __init__(self):
        self.vectors = []
        self.d = 384  # Default embedding dimension
        self.ntotal = 0

    def add(self, vectors):
        if len(vectors.shape) == 1:
            vectors = vectors.reshape(1, -1)
        self.vectors.extend(vectors)
        self.ntotal += len(vectors)

    def search(self, query_vectors, k):
        if len(self.vectors) == 0:
            return np.array([[0.0] * k]), np.array([[0] * k])

        # Simple mock similarity search
        distances = np.random.rand(len(query_vectors), min(k, len(self.vectors)))
        indices = np.random.randint(
            0, len(self.vectors), (len(query_vectors), min(k, len(self.vectors)))
        )
        return distances, indices

    def write_index(self, filename):
        # Mock write operation
        pass

    @staticmethod
    def read_index(filename):
        return MockIndex()


class VectorDatabase:
    """High-performance vector database for code embeddings using FAISS."""

    def __init__(
        self,
        index_path: str,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """Initialize the vector database.

        Args:
            index_path: Path to store the vector index
            embedding_model: Name of the sentence transformer model to use
        """
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)

        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.index = None
        self.metadata_store = {}
        self.chunk_id_to_index = {}
        self.index_to_chunk_id = {}
        self.embedding_dimension = 384  # Default for MiniLM

        # File paths
        self.index_file = self.index_path / "faiss_index.bin"
        self.metadata_file = self.index_path / "metadata.json"
        self.chunk_mapping_file = self.index_path / "chunk_mapping.json"

        self._initialize_model()
        self._load_or_create_index()

    def _initialize_model(self) -> None:
        """Initialize the sentence transformer model."""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                # Get actual embedding dimension from model
                test_embedding = self.embedding_model.encode(["test"])
                self.embedding_dimension = test_embedding.shape[1]
            except Exception as e:
                print(f"Warning: Could not load sentence transformer model: {e}")
                self.embedding_model = SentenceTransformer(
                    self.embedding_model_name
                )  # Use mock
        else:
            print("Warning: sentence-transformers not available, using mock embeddings")
            self.embedding_model = SentenceTransformer(
                self.embedding_model_name
            )  # Use mock

    def _load_or_create_index(self) -> None:
        """Load existing index or create a new one."""
        if self.index_file.exists() and FAISS_AVAILABLE:
            try:
                self.index = faiss.read_index(str(self.index_file))
                self._load_metadata()
                print(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"Warning: Could not load existing index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self) -> None:
        """Create a new FAISS index."""
        if FAISS_AVAILABLE:
            # Use cosine similarity (inner product with normalized vectors)
            self.index = faiss.IndexFlatIP(self.embedding_dimension)
        else:
            self.index = MockIndex()

        self.metadata_store = {}
        self.chunk_id_to_index = {}
        self.index_to_chunk_id = {}
        print(f"Created new FAISS index with dimension {self.embedding_dimension}")

    def _load_metadata(self) -> None:
        """Load metadata and chunk mappings from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file) as f:
                    self.metadata_store = json.load(f)

            if self.chunk_mapping_file.exists():
                with open(self.chunk_mapping_file) as f:
                    mapping_data = json.load(f)
                    self.chunk_id_to_index = {
                        k: int(v)
                        for k, v in mapping_data.get("chunk_to_index", {}).items()
                    }
                    self.index_to_chunk_id = {
                        int(k): v
                        for k, v in mapping_data.get("index_to_chunk", {}).items()
                    }
        except Exception as e:
            print(f"Warning: Could not load metadata: {e}")
            self.metadata_store = {}
            self.chunk_id_to_index = {}
            self.index_to_chunk_id = {}

    def _save_metadata(self) -> None:
        """Save metadata and chunk mappings to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata_store, f, indent=2)

            mapping_data = {
                "chunk_to_index": {
                    k: str(v) for k, v in self.chunk_id_to_index.items()
                },
                "index_to_chunk": {
                    str(k): v for k, v in self.index_to_chunk_id.items()
                },
            }
            with open(self.chunk_mapping_file, "w") as f:
                json.dump(mapping_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metadata: {e}")

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a text string.

        Args:
            text: Text to embed

        Returns:
            Normalized embedding vector
        """
        if not self.embedding_model:
            # Return random embedding for testing
            return np.random.rand(self.embedding_dimension).astype(np.float32)

        try:
            embedding = self.embedding_model.encode([text], convert_to_numpy=True)[0]
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding.astype(np.float32)
        except Exception as e:
            print(f"Warning: Could not generate embedding: {e}")
            return np.random.rand(self.embedding_dimension).astype(np.float32)

    def store_embedding(
        self, chunk: CodeChunk, embedding: np.ndarray | None = None
    ) -> str:
        """Store a code chunk and its embedding in the database.

        Args:
            chunk: Code chunk to store
            embedding: Pre-computed embedding (optional)

        Returns:
            Unique chunk ID
        """
        # Generate unique chunk ID
        chunk_id = self._generate_chunk_id(chunk)

        # Generate embedding if not provided
        if embedding is None:
            embedding = self.generate_embedding(chunk.content)

        # Add to FAISS index
        current_index = self.index.ntotal
        self.index.add(embedding.reshape(1, -1))

        # Update mappings
        self.chunk_id_to_index[chunk_id] = current_index
        self.index_to_chunk_id[current_index] = chunk_id

        # Store metadata
        self.metadata_store[chunk_id] = {
            "file_path": chunk.file_path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "language": chunk.language,
            "chunk_type": chunk.chunk_type,
            "content_hash": hashlib.md5(chunk.content.encode()).hexdigest(),
            "content_length": len(chunk.content),
        }

        return chunk_id

    def store_embeddings(self, chunks: list[CodeChunk]) -> list[str]:
        """Store multiple code chunks and their embeddings.

        Args:
            chunks: List of code chunks to store

        Returns:
            List of chunk IDs
        """
        chunk_ids = []

        # Generate embeddings in batch for efficiency
        texts = [chunk.content for chunk in chunks]
        embeddings = self._generate_embeddings_batch(texts)

        # Store each chunk with its embedding
        for chunk, embedding in zip(chunks, embeddings, strict=False):
            chunk_id = self.store_embedding(chunk, embedding)
            chunk_ids.append(chunk_id)

        return chunk_ids

    def _generate_embeddings_batch(self, texts: list[str]) -> list[np.ndarray]:
        """Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of normalized embedding vectors
        """
        if not self.embedding_model:
            # Return random embeddings for testing
            return [
                np.random.rand(self.embedding_dimension).astype(np.float32)
                for _ in texts
            ]

        try:
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            # Normalize for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            embeddings = embeddings / norms
            return [emb.astype(np.float32) for emb in embeddings]
        except Exception as e:
            print(f"Warning: Could not generate batch embeddings: {e}")
            return [
                np.random.rand(self.embedding_dimension).astype(np.float32)
                for _ in texts
            ]

    def query_similar(
        self, query_text: str, k: int = 10, min_similarity: float = 0.0
    ) -> list[CodeMatch]:
        """Find similar code chunks using vector similarity search.

        Args:
            query_text: Text to search for
            k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of CodeMatch objects sorted by similarity
        """
        if self.index.ntotal == 0:
            return []

        # Generate query embedding
        query_embedding = self.generate_embedding(query_text)

        # Search in FAISS index
        similarities, indices = self.index.search(
            query_embedding.reshape(1, -1), min(k, self.index.ntotal)
        )

        # Convert results to CodeMatch objects
        matches = []
        for similarity, idx in zip(similarities[0], indices[0], strict=False):
            if similarity < min_similarity:
                continue

            chunk_id = self.index_to_chunk_id.get(idx)
            if not chunk_id:
                continue

            metadata = self.metadata_store.get(chunk_id)
            if not metadata:
                continue

            # Reconstruct CodeChunk from metadata
            chunk = CodeChunk(
                content="",  # Content not stored in metadata for efficiency
                file_path=metadata["file_path"],
                start_line=metadata["start_line"],
                end_line=metadata["end_line"],
                language=metadata["language"],
                chunk_type=metadata["chunk_type"],
            )

            match = CodeMatch(
                chunk=chunk, similarity_score=float(similarity), embedding_id=chunk_id
            )
            matches.append(match)

        return matches

    def query_similar_by_chunk(
        self, chunk: CodeChunk, k: int = 10, min_similarity: float = 0.0
    ) -> list[CodeMatch]:
        """Find similar code chunks using an existing chunk as query.

        Args:
            chunk: Code chunk to use as query
            k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of CodeMatch objects sorted by similarity
        """
        return self.query_similar(chunk.content, k, min_similarity)

    def get_chunk_by_id(self, chunk_id: str) -> dict[str, Any] | None:
        """Get chunk metadata by ID.

        Args:
            chunk_id: Unique chunk identifier

        Returns:
            Chunk metadata or None if not found
        """
        return self.metadata_store.get(chunk_id)

    def update_embedding(self, chunk_id: str, new_chunk: CodeChunk) -> bool:
        """Update an existing embedding with new content.

        Args:
            chunk_id: ID of chunk to update
            new_chunk: New chunk content

        Returns:
            True if update successful, False otherwise
        """
        if chunk_id not in self.chunk_id_to_index:
            return False

        # For FAISS, we can't update in place, so we'd need to rebuild
        # For now, we'll just add the new chunk and mark the old one as outdated
        new_chunk_id = self.store_embedding(new_chunk)

        # Mark old chunk as outdated in metadata
        if chunk_id in self.metadata_store:
            self.metadata_store[chunk_id]["outdated"] = True
            self.metadata_store[chunk_id]["replaced_by"] = new_chunk_id

        return True

    def delete_chunk(self, chunk_id: str) -> bool:
        """Mark a chunk as deleted (FAISS doesn't support true deletion).

        Args:
            chunk_id: ID of chunk to delete

        Returns:
            True if deletion successful, False otherwise
        """
        if chunk_id not in self.metadata_store:
            return False

        # Mark as deleted in metadata
        self.metadata_store[chunk_id]["deleted"] = True
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        active_chunks = sum(
            1
            for meta in self.metadata_store.values()
            if not meta.get("deleted", False) and not meta.get("outdated", False)
        )

        return {
            "total_embeddings": self.index.ntotal,
            "active_chunks": active_chunks,
            "deleted_chunks": sum(
                1 for meta in self.metadata_store.values() if meta.get("deleted", False)
            ),
            "outdated_chunks": sum(
                1
                for meta in self.metadata_store.values()
                if meta.get("outdated", False)
            ),
            "embedding_dimension": self.embedding_dimension,
            "model_name": self.embedding_model_name,
            "index_size_mb": self._get_index_size_mb(),
        }

    def _get_index_size_mb(self) -> float:
        """Get the size of the index files in MB."""
        total_size = 0
        for file_path in [self.index_file, self.metadata_file, self.chunk_mapping_file]:
            if file_path.exists():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)

    def save_index(self) -> None:
        """Save the index and metadata to disk."""
        try:
            if FAISS_AVAILABLE:
                faiss.write_index(self.index, str(self.index_file))
            self._save_metadata()
            print(f"Saved vector database with {self.index.ntotal} embeddings")
        except Exception as e:
            print(f"Warning: Could not save index: {e}")

    def _generate_chunk_id(self, chunk: CodeChunk) -> str:
        """Generate a unique ID for a code chunk.

        Args:
            chunk: Code chunk

        Returns:
            Unique chunk ID
        """
        # Create ID based on file path, line numbers, and content hash
        content_hash = hashlib.md5(chunk.content.encode()).hexdigest()[:8]
        return f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}:{content_hash}"

    def rebuild_index(self) -> None:
        """Rebuild the index from scratch, removing deleted/outdated entries."""
        print("Rebuilding vector database index...")

        # Collect active chunks
        active_chunks = []
        active_embeddings = []

        for chunk_id, metadata in self.metadata_store.items():
            if metadata.get("deleted", False) or metadata.get("outdated", False):
                continue

            # Reconstruct chunk
            chunk = CodeChunk(
                content="",  # We don't store full content in metadata
                file_path=metadata["file_path"],
                start_line=metadata["start_line"],
                end_line=metadata["end_line"],
                language=metadata["language"],
                chunk_type=metadata["chunk_type"],
            )

            # Get embedding from current index
            old_index = self.chunk_id_to_index.get(chunk_id)
            if old_index is not None and old_index < self.index.ntotal:
                active_chunks.append((chunk_id, chunk))

        # Create new index
        self._create_new_index()

        # Re-add active chunks (this will regenerate embeddings)
        print(f"Rebuilding {len(active_chunks)} active chunks...")
        for chunk_id, chunk in active_chunks:
            # Note: This will regenerate embeddings since we don't store them
            # In a production system, you'd want to store embeddings separately
            self.store_embedding(chunk)

        print(f"Index rebuild complete. New size: {self.index.ntotal} embeddings")
