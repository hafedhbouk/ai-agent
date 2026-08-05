import pytest
from pathlib import Path
from app.rag.chunker import Chunker, ChunkingStrategy
from app.rag.schemas import DocumentMetadata, ChunkMetadata
from app.rag.ingestor import DocumentIngestor, DocumentIngestionError


def test_chunker_splits_text():
    chunker = Chunker(chunk_size=50, chunk_overlap=10)
    text = "Lorem ipsum dolor sit amet. " * 20
    metadata = {"source": "test.txt"}
    chunks = chunker.chunk_text(text, metadata)
    assert len(chunks) > 1
    assert all(isinstance(c, ChunkMetadata) for c in chunks)
    assert chunks[0].chunk_index == 0
    assert chunks[-1].chunk_index == len(chunks) - 1


def test_chunker_empty_text():
    chunker = Chunker()
    chunks = chunker.chunk_text("", {"source": "test.txt"})
    assert chunks == []


def test_chunker_single_chunk():
    chunker = Chunker(chunk_size=1000, chunk_overlap=200)
    text = "Short text."
    metadata = {"source": "test.txt"}
    chunks = chunker.chunk_text(text, metadata)
    assert len(chunks) == 1


def test_ingestor_unsupported_extension(tmp_path):
    ingestor = DocumentIngestor()
    file_path = tmp_path / "test.xyz"
    file_path.write_text("hello")
    with pytest.raises(DocumentIngestionError):
        import asyncio
        asyncio.run(ingestor.ingest_file(file_path, "test"))


def test_ingestor_text_file(tmp_path):
    ingestor = DocumentIngestor()
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello world\nThis is a test.", encoding="utf-8")
    import asyncio
    doc = asyncio.run(ingestor.ingest_file(file_path, "test"))
    assert doc.filename == "test.txt"
    assert "Hello world" in doc.content


def test_document_metadata_model():
    meta = DocumentMetadata(source="test.txt", content="Hello world", filename="test.txt", mime_type="text/plain")
    assert meta.source == "test.txt"
    assert meta.content == "Hello world"
    assert meta.metadata == {}
