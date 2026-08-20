from pathlib import Path

import pytest

from app.services.storage import StorageService


def test_save_file_creates_tenant_scoped_file(
    tmp_path: Path,
):
    service = StorageService(tmp_path)

    storage_path = service.save(
        tenant_id="tenant-1",
        filename="knowledge.pdf",
        content=b"hello world",
    )

    assert storage_path == (
        "tenant-1/knowledge.pdf"
    )

    stored_file = (
        tmp_path
        / "tenant-1"
        / "knowledge.pdf"
    )

    assert stored_file.exists()
    assert stored_file.read_bytes() == b"hello world"


def test_open_existing_file(
    tmp_path: Path,
):
    service = StorageService(tmp_path)

    storage_path = service.save(
        tenant_id="tenant-1",
        filename="knowledge.pdf",
        content=b"hello",
    )

    result = service.open(storage_path)

    assert result is not None
    assert result.read_bytes() == b"hello"


def test_open_missing_file_returns_none(
    tmp_path: Path,
):
    service = StorageService(tmp_path)

    result = service.open(
        "tenant-1/missing.pdf",
    )

    assert result is None


def test_save_rejects_path_traversal_filename(
    tmp_path: Path,
):
    service = StorageService(tmp_path)

    with pytest.raises(
        ValueError,
        match="Invalid filename.",
    ):
        service.save(
            tenant_id="tenant-1",
            filename="../secret.pdf",
            content=b"secret",
        )


def test_save_rejects_nested_filename(
    tmp_path: Path,
):
    service = StorageService(tmp_path)

    with pytest.raises(
        ValueError,
        match="Invalid filename.",
    ):
        service.save(
            tenant_id="tenant-1",
            filename="nested/secret.pdf",
            content=b"secret",
        )


def test_open_rejects_absolute_path(
    tmp_path: Path,
):
    service = StorageService(tmp_path)

    with pytest.raises(
        ValueError,
        match="Invalid storage path.",
    ):
        service.open(
            str(tmp_path / "secret.pdf"),
        )


def test_open_rejects_parent_directory_traversal(
    tmp_path: Path,
):
    service = StorageService(tmp_path)

    with pytest.raises(
        ValueError,
        match="Invalid storage path.",
    ):
        service.open(
            "../secret.pdf",
        )


def test_delete_removes_existing_file(
    tmp_path: Path,
):
    service = StorageService(tmp_path)

    storage_path = service.save(
        tenant_id="tenant-1",
        filename="knowledge.pdf",
        content=b"hello",
    )

    service.delete(storage_path)

    assert not (
        tmp_path
        / "tenant-1"
        / "knowledge.pdf"
    ).exists()