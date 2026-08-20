from pathlib import Path


class StorageService:
    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _tenant_root(
        self,
        tenant_id: str,
    ) -> Path:
        tenant_root = (
            self.base_path / str(tenant_id)
        ).resolve()

        if self.base_path not in tenant_root.parents:
            raise ValueError(
                "Invalid tenant storage path."
            )

        tenant_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        return tenant_root

    def save(
        self,
        *,
        tenant_id: str,
        filename: str,
        content: bytes,
    ) -> str:
        if not filename:
            raise ValueError(
                "Filename cannot be empty."
            )

        original_name = Path(filename).name

        if original_name != filename:
            raise ValueError(
                "Invalid filename."
            )

        tenant_root = self._tenant_root(
            tenant_id,
        )

        destination = (
            tenant_root / original_name
        ).resolve()

        if self.base_path not in destination.parents:
            raise ValueError(
                "Invalid storage path."
            )

        destination.write_bytes(content)

        return destination.relative_to(
            self.base_path
        ).as_posix()

    def open(
        self,
        storage_path: str,
    ) -> Path | None:
        relative_path = Path(storage_path)

        if relative_path.is_absolute():
            raise ValueError(
                "Invalid storage path."
            )

        if ".." in relative_path.parts:
            raise ValueError(
                "Invalid storage path."
            )

        destination = (
            self.base_path / relative_path
        ).resolve()

        if self.base_path not in destination.parents:
            raise ValueError(
                "Invalid storage path."
            )

        if not destination.is_file():
            return None

        return destination

    def delete(
        self,
        storage_path: str,
    ) -> None:
        destination = self.open(
            storage_path,
        )

        if destination is not None:
            destination.unlink()