"""Tests for chunking functionality."""

import tempfile
import time

from src.RTFD.chunking import ChunkingManager, get_chunk_size


class TestChunkingManager:
    """Tests for ChunkingManager class."""

    def test_init_with_default_path(self):
        """Test initialization with default database path."""
        manager = ChunkingManager()
        assert manager.db_path is not None
        assert manager.ttl == 600

    def test_init_with_custom_path(self):
        """Test initialization with custom database path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_chunking.db"
            manager = ChunkingManager(db_path=db_path, ttl=300)
            assert manager.db_path == db_path
            assert manager.ttl == 300

    def test_store_and_retrieve_continuation(self):
        """Test storing and retrieving a continuation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChunkingManager(db_path=f"{tmpdir}/test.db")

            # Create test content
            content = "This is some remaining content that should be chunked."
            metadata = {"chunk_number": 1, "total_tokens": 1000}

            # Store continuation
            token = manager.store_continuation(content, metadata)
            assert token is not None
            assert len(token) > 0

            # Retrieve continuation with chunk size
            result = manager.get_next_chunk(token, chunk_size=10)
            assert result is not None
            assert "content" in result
            assert "chunk_number" in result
            assert result["chunk_number"] == 2  # Incremented from metadata

    def test_continuation_with_small_chunk_size(self):
        """Test chunking with small chunk size that requires multiple chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChunkingManager(db_path=f"{tmpdir}/test.db")

            # Create longer content that will need multiple chunks
            content = " ".join([f"word{i}" for i in range(100)])
            metadata = {"chunk_number": 1}

            # Store continuation
            token = manager.store_continuation(content, metadata)

            # Get first chunk
            result1 = manager.get_next_chunk(token, chunk_size=20)
            assert result1 is not None
            assert result1["has_more"] is True
            assert result1["continuation_token"] is not None

            # Get second chunk
            token2 = result1["continuation_token"]
            result2 = manager.get_next_chunk(token2, chunk_size=20)
            assert result2 is not None

            # Content should be different
            assert result1["content"] != result2["content"]

    def test_last_chunk(self):
        """Test that the last chunk is handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChunkingManager(db_path=f"{tmpdir}/test.db")

            # Small content that fits in one chunk
            content = "Small content"
            metadata = {"chunk_number": 1}

            token = manager.store_continuation(content, metadata)
            result = manager.get_next_chunk(token, chunk_size=1000)

            assert result is not None
            assert result["has_more"] is False
            assert result["continuation_token"] is None
            assert result["content"] == content

    def test_expired_continuation(self):
        """Test that expired continuations return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChunkingManager(db_path=f"{tmpdir}/test.db", ttl=1)

            content = "Test content"
            metadata = {"chunk_number": 1}

            token = manager.store_continuation(content, metadata)

            # Wait for expiration
            time.sleep(2)

            # Should return None for expired token
            result = manager.get_next_chunk(token, chunk_size=100)
            assert result is None

    def test_invalid_token(self):
        """Test that invalid tokens return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChunkingManager(db_path=f"{tmpdir}/test.db")

            result = manager.get_next_chunk("invalid-token-12345", chunk_size=100)
            assert result is None

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ChunkingManager(db_path=f"{tmpdir}/test.db", ttl=1)

            # Store some continuations
            token1 = manager.store_continuation("content1", {"chunk_number": 1})
            token2 = manager.store_continuation("content2", {"chunk_number": 1})

            # Wait for expiration
            time.sleep(2)

            # Cleanup should remove both
            removed_count = manager.cleanup_expired()
            assert removed_count == 2

            # Both should now be invalid
            assert manager.get_next_chunk(token1, chunk_size=100) is None
            assert manager.get_next_chunk(token2, chunk_size=100) is None


class TestGetChunkSize:
    """Tests for get_chunk_size function."""

    def test_default_chunk_size(self, monkeypatch):
        """Test default chunk size when env var not set."""
        monkeypatch.delenv("RTFD_CHUNK_TOKENS", raising=False)
        assert get_chunk_size() == 2000

    def test_custom_chunk_size(self, monkeypatch):
        """Test custom chunk size from environment variable."""
        monkeypatch.setenv("RTFD_CHUNK_TOKENS", "8000")
        assert get_chunk_size() == 8000

    def test_disabled_chunking(self, monkeypatch):
        """Test chunking disabled with 0."""
        monkeypatch.setenv("RTFD_CHUNK_TOKENS", "0")
        assert get_chunk_size() == 0

    def test_invalid_chunk_size(self, monkeypatch):
        """Test invalid chunk size falls back to default."""
        monkeypatch.setenv("RTFD_CHUNK_TOKENS", "invalid")
        assert get_chunk_size() == 2000
