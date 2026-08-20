from unittest.mock import MagicMock

import pytest
from pypdf import PdfReader

from app.services.document_text import (
    DocumentTextService,
)


def test_rejects_empty_content():
    service = DocumentTextService()

    with pytest.raises(
        ValueError,
        match="Document content cannot be empty.",
    ):
        service.extract_text(
            content=b"",
            filename="document.pdf",
        )


def test_rejects_non_pdf():
    service = DocumentTextService()

    with pytest.raises(
        ValueError,
        match="Only PDF documents are supported.",
    ):
        service.extract_text(
            content=b"hello",
            filename="document.txt",
        )


def test_rejects_invalid_pdf():
    service = DocumentTextService()

    with pytest.raises(
        ValueError,
        match="Invalid PDF document.",
    ):
        service.extract_text(
            content=b"not a pdf",
            filename="document.pdf",
        )


def test_extracts_pdf_text(monkeypatch):
    service = DocumentTextService()

    page_one = MagicMock()
    page_one.extract_text.return_value = (
        "KnowledgeHub document"
    )

    page_two = MagicMock()
    page_two.extract_text.return_value = (
        "processing pipeline"
    )

    class FakeReader:
        def __init__(self, _stream):
            self.pages = [
                page_one,
                page_two,
            ]

    monkeypatch.setattr(
        "pypdf.PdfReader",
        FakeReader,
    )

    result = service.extract_text(
        content=b"fake pdf content",
        filename="document.pdf",
    )

    assert result == (
        "KnowledgeHub document\n\n"
        "processing pipeline"
    )


def test_extracts_text_when_content_type_is_pdf(
    monkeypatch,
):
    service = DocumentTextService()

    page = MagicMock()
    page.extract_text.return_value = (
        "KnowledgeHub"
    )

    class FakeReader:
        def __init__(self, _stream):
            self.pages = [page]

    monkeypatch.setattr(
        "pypdf.PdfReader",
        FakeReader,
    )

    result = service.extract_text(
        content=b"fake pdf content",
        content_type="application/pdf",
        filename="document.bin",
    )

    assert result == "KnowledgeHub"