"""Unit tests for document chunking, processor registry, and folder tree."""

import pytest

from app.documents.chunking import TextSplitterService
from app.documents.models import DocumentIndexMode
from app.documents.processors.registry import DocumentProcessorRegistry, index_mode_for_mimetype
from app.documents.routes import _build_folder_tree

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


async def test_chunking_empty():
    assert await TextSplitterService().split_text("") == []


async def test_chunking_single_chunk():
    chunks = await TextSplitterService().split_text("one short paragraph")
    assert chunks == ["one short paragraph"]


async def test_chunking_splits_long_text():
    text = "\n\n".join(f"Paragraph {i} " + ("x " * 100) for i in range(10))
    chunks = await TextSplitterService(chunk_size=200, chunk_overlap=50).split_text(text)
    assert len(chunks) > 1


def test_registry_resolves_by_extension():
    assert DocumentProcessorRegistry.resolve_mimetype("report.pdf", None) == "application/pdf"
    assert DocumentProcessorRegistry.resolve_mimetype("notes.md", None) == "text/markdown"


def test_registry_resolves_by_content_type():
    assert DocumentProcessorRegistry.resolve_mimetype("weird", "text/csv") == "text/csv"


def test_registry_unknown_is_none():
    assert DocumentProcessorRegistry.resolve_mimetype("x.zip", "application/zip") is None


def test_registry_get_processor_unknown_raises():
    with pytest.raises(ValueError):
        DocumentProcessorRegistry().get_processor("application/zip")


def test_supported_types_count():
    assert len(DocumentProcessorRegistry.get_allowed_mimetypes()) == 7


def test_index_mode_routing():
    assert index_mode_for_mimetype(XLSX) == DocumentIndexMode.stub
    assert index_mode_for_mimetype("text/plain") == DocumentIndexMode.full


def test_folder_tree_nested():
    tree = _build_folder_tree([("reports/q3", 2), ("reports/q4", 1)])
    assert len(tree) == 1
    reports = tree[0]
    assert reports.name == "reports"
    assert {c.name for c in reports.children} == {"q3", "q4"}
    counts = {c.name: c.document_count for c in reports.children}
    assert counts == {"q3": 2, "q4": 1}
