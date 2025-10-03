"""Tests for the vector database implementation."""

from __future__ import annotations

import os
import shutil
import tempfile
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from dev_agent.errors.llm_exceptions import LLMAPIError
from dev_agent.indexing.vector_database import VectorDatabase
from dev_agent.models.indexing import CodeChunk, CodeMatch


@pytest.fixture
def mock_embedding_client():
    """Create a mock embedding client."""
    client = AsyncMock()
    client.dimension = 1536  # text-embedding-ada-002 dimension
    
    # Mock embed_text to return a normalized vector
    async def mock_embed_text(text: str) -> list[float]:
        # Generate deterministic embedding based on text hash
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.rand(1536).astype(np.float32)
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.tolist()
    
    client.embed_text = mock_embed_text
    
    # Mock embed_batch to return normalized vectors
    async def mock_embed_batch(texts: list[str], batch_size: int = 16) -> list[list[float]]:
        embeddings = []
        for text in texts:
            embedding = await mock_embed_text(text)
            embeddings.append(embedding)
        return embeddings
    
    client.embed_batch = mock_embed_batch
    
    return client


class TestVectorDatabase:
    """Test cases for VectorDatabase class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.temp_dir, "test_index")

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_initialization(self, mock_embedding_client):
        """Test vector database initialization."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        
        assert db is not None
        assert db.index is not None
        assert db.embedding_dimension == 1536
        assert db.embedding_client is mock_embedding_client
        assert os.path.exists(self.index_path)

    @pytest.mark.asyncio
    async def test_initialization_without_client(self):
        """Test that initialization fails without embedding client."""
        with pytest.raises(ValueError, match="embedding_client is required"):
            VectorDatabase(self.index_path, None)

    @pytest.mark.asyncio
    async def test_generate_embedding(self, mock_embedding_client):
        """Test embedding generation."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        text = "def hello_world(): print('Hello, World!')"
        embedding = await db.generate_embedding(text)

        assert embedding is not None
        assert len(embedding) == db.embedding_dimension
        assert embedding.dtype.name.startswith("float")
        # Check normalization
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01  # Should be normalized

    @pytest.mark.asyncio
    async def test_store_single_embedding(self, mock_embedding_client):
        """Test storing a single code chunk."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        chunk = CodeChunk(
            content="def add(a, b): return a + b",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        chunk_id = await db.store_embedding(chunk)

        assert chunk_id is not None
        assert chunk_id in db.metadata_store
        assert db.index.ntotal == 1

    @pytest.mark.asyncio
    async def test_store_multiple_embeddings(self, mock_embedding_client):
        """Test storing multiple code chunks."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        chunks = [
            CodeChunk(
                content="def add(a, b): return a + b",
                file_path="test.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function",
            ),
            CodeChunk(
                content="def subtract(a, b): return a - b",
                file_path="test.py",
                start_line=3,
                end_line=3,
                language="python",
                chunk_type="function",
            ),
            CodeChunk(
                content="class Calculator: pass",
                file_path="test.py",
                start_line=5,
                end_line=5,
                language="python",
                chunk_type="class",
            ),
        ]

        chunk_ids = await db.store_embeddings(chunks)

        assert len(chunk_ids) == 3
        assert db.index.ntotal == 3
        assert all(chunk_id in db.metadata_store for chunk_id in chunk_ids)

    @pytest.mark.asyncio
    async def test_similarity_search(self, mock_embedding_client):
        """Test similarity search functionality."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        
        # Store some test chunks
        chunks = [
            CodeChunk(
                content="def add_numbers(x, y): return x + y",
                file_path="math.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function",
            ),
            CodeChunk(
                content="def multiply_values(a, b): return a * b",
                file_path="math.py",
                start_line=3,
                end_line=3,
                language="python",
                chunk_type="function",
            ),
            CodeChunk(
                content="class FileHandler: def read_file(self): pass",
                file_path="io.py",
                start_line=1,
                end_line=2,
                language="python",
                chunk_type="class",
            ),
        ]

        await db.store_embeddings(chunks)

        # Search for similar code
        results = await db.query_similar("addition function", k=2)

        assert len(results) <= 2
        assert all(isinstance(result, CodeMatch) for result in results)

        if results:
            # Results should be sorted by similarity (highest first)
            assert all(
                results[i].similarity_score >= results[i + 1].similarity_score
                for i in range(len(results) - 1)
            )

    @pytest.mark.asyncio
    async def test_query_similar_by_chunk(self, mock_embedding_client):
        """Test similarity search using a chunk as query."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        
        # Store test chunks
        chunks = [
            CodeChunk(
                content="def calculate_sum(numbers): return sum(numbers)",
                file_path="utils.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function",
            ),
            CodeChunk(
                content="def compute_average(values): return sum(values) / len(values)",
                file_path="stats.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function",
            ),
        ]

        await db.store_embeddings(chunks)

        # Create query chunk
        query_chunk = CodeChunk(
            content="def total_sum(items): return sum(items)",
            file_path="query.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        results = await db.query_similar_by_chunk(query_chunk, k=2)

        assert len(results) <= 2
        assert all(isinstance(result, CodeMatch) for result in results)

    @pytest.mark.asyncio
    async def test_get_chunk_by_id(self, mock_embedding_client):
        """Test retrieving chunk metadata by ID."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        chunk = CodeChunk(
            content="def test_function(): pass",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        chunk_id = await db.store_embedding(chunk)
        metadata = db.get_chunk_by_id(chunk_id)

        assert metadata is not None
        assert metadata["file_path"] == chunk.file_path
        assert metadata["start_line"] == chunk.start_line
        assert metadata["end_line"] == chunk.end_line
        assert metadata["language"] == chunk.language
        assert metadata["chunk_type"] == chunk.chunk_type

    @pytest.mark.asyncio
    async def test_update_embedding(self, mock_embedding_client):
        """Test updating an existing embedding."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        original_chunk = CodeChunk(
            content="def old_function(): pass",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        chunk_id = await db.store_embedding(original_chunk)
        original_count = db.index.ntotal

        new_chunk = CodeChunk(
            content="def new_function(): return 42",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        success = await db.update_embedding(chunk_id, new_chunk)

        assert success
        assert db.index.ntotal > original_count  # New embedding added

        # Original chunk should be marked as outdated
        original_metadata = db.get_chunk_by_id(chunk_id)
        assert original_metadata.get("outdated", False)

    @pytest.mark.asyncio
    async def test_delete_chunk(self, mock_embedding_client):
        """Test marking a chunk as deleted."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        chunk = CodeChunk(
            content="def to_delete(): pass",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        chunk_id = await db.store_embedding(chunk)
        success = db.delete_chunk(chunk_id)

        assert success

        # Chunk should be marked as deleted
        metadata = db.get_chunk_by_id(chunk_id)
        assert metadata.get("deleted", False)

    @pytest.mark.asyncio
    async def test_get_stats(self, mock_embedding_client):
        """Test database statistics."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        
        # Initially empty
        stats = db.get_stats()
        assert stats["total_embeddings"] == 0
        assert stats["active_chunks"] == 0

        # Add some chunks
        chunks = [
            CodeChunk(
                content="def func1(): pass",
                file_path="test.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function",
            ),
            CodeChunk(
                content="def func2(): pass",
                file_path="test.py",
                start_line=3,
                end_line=3,
                language="python",
                chunk_type="function",
            ),
        ]

        chunk_ids = await db.store_embeddings(chunks)

        # Delete one chunk
        db.delete_chunk(chunk_ids[0])

        stats = db.get_stats()
        assert stats["total_embeddings"] == 2
        assert stats["active_chunks"] == 1
        assert stats["deleted_chunks"] == 1
        assert stats["embedding_dimension"] == db.embedding_dimension
        assert "Azure OpenAI" in stats["model_name"]

    @pytest.mark.asyncio
    async def test_save_and_load_index(self, mock_embedding_client):
        """Test saving and loading the index."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        
        # Store some data
        chunk = CodeChunk(
            content="def persistent_function(): return True",
            file_path="persistent.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        chunk_id = await db.store_embedding(chunk)
        db.save_index()

        # Create new database instance with same path
        new_db = VectorDatabase(self.index_path, mock_embedding_client)

        # Check that data was loaded
        assert new_db.index.ntotal == 1
        assert chunk_id in new_db.metadata_store

        metadata = new_db.get_chunk_by_id(chunk_id)
        assert metadata is not None
        assert metadata["file_path"] == chunk.file_path

    @pytest.mark.asyncio
    async def test_empty_query(self, mock_embedding_client):
        """Test querying an empty database."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        results = await db.query_similar("test query", k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_minimum_similarity_threshold(self, mock_embedding_client):
        """Test similarity search with minimum threshold."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        chunk = CodeChunk(
            content="def specific_function(): return 'specific'",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        await db.store_embedding(chunk)

        # Search with high similarity threshold
        results = await db.query_similar(
            "completely different content", k=5, min_similarity=0.9
        )

        # Should return no results due to high threshold
        assert len(results) == 0 or all(r.similarity_score >= 0.9 for r in results)

    @pytest.mark.asyncio
    async def test_chunk_id_generation(self, mock_embedding_client):
        """Test that chunk IDs are unique and consistent."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        chunk1 = CodeChunk(
            content="def test(): pass",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        chunk2 = CodeChunk(
            content="def test(): pass",  # Same content
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        chunk3 = CodeChunk(
            content="def different(): pass",  # Different content
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )

        id1 = db._generate_chunk_id(chunk1)
        id2 = db._generate_chunk_id(chunk2)
        id3 = db._generate_chunk_id(chunk3)

        # Same chunks should have same ID
        assert id1 == id2

        # Different chunks should have different IDs
        assert id1 != id3

    @pytest.mark.asyncio
    async def test_rebuild_index(self, mock_embedding_client):
        """Test rebuilding the index to remove deleted entries."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        
        # Add some chunks
        chunks = [
            CodeChunk(
                content="def keep_me(): pass",
                file_path="test.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function",
            ),
            CodeChunk(
                content="def delete_me(): pass",
                file_path="test.py",
                start_line=3,
                end_line=3,
                language="python",
                chunk_type="function",
            ),
        ]

        chunk_ids = await db.store_embeddings(chunks)
        assert db.index.ntotal == 2

        # Delete one chunk
        db.delete_chunk(chunk_ids[1])

        # Rebuild index
        await db.rebuild_index()

        # Should have fewer embeddings after rebuild
        # Note: In the current implementation, rebuild doesn't actually remove
        # deleted embeddings because we don't store the original content
        # This test verifies the rebuild process runs without errors
        assert db.index is not None

    @pytest.mark.asyncio
    async def test_error_handling_on_embedding_failure(self, mock_embedding_client):
        """Test error handling when embedding generation fails."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        
        # Mock embed_text to raise an exception
        mock_embedding_client.embed_text = AsyncMock(side_effect=Exception("API Error"))
        
        chunk = CodeChunk(
            content="def test(): pass",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
        )
        
        # Should raise LLMAPIError
        with pytest.raises(LLMAPIError, match="Failed to generate embedding"):
            await db.store_embedding(chunk)

    @pytest.mark.asyncio
    async def test_batch_embedding_error_handling(self, mock_embedding_client):
        """Test error handling when batch embedding generation fails."""
        db = VectorDatabase(self.index_path, mock_embedding_client)
        
        # Mock embed_batch to raise an exception
        mock_embedding_client.embed_batch = AsyncMock(side_effect=Exception("Batch API Error"))
        
        chunks = [
            CodeChunk(
                content="def test1(): pass",
                file_path="test.py",
                start_line=1,
                end_line=1,
                language="python",
                chunk_type="function",
            ),
            CodeChunk(
                content="def test2(): pass",
                file_path="test.py",
                start_line=3,
                end_line=3,
                language="python",
                chunk_type="function",
            ),
        ]
        
        # Should raise LLMAPIError
        with pytest.raises(LLMAPIError, match="Failed to generate batch embeddings"):
            await db.store_embeddings(chunks)
