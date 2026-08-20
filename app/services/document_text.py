from io import BytesIO


class DocumentTextService:
    """Extract text from supported document formats."""

    def extract_text(
        self,
        *,
        content: bytes,
        content_type: str | None = None,
        filename: str | None = None,
    ) -> str:
        if not content:
            raise ValueError(
                "Document content cannot be empty."
            )

        is_pdf = content_type == "application/pdf" or (
            filename is not None
            and filename.lower().endswith(".pdf")
        )

        if not is_pdf:
            raise ValueError(
                "Only PDF documents are supported."
            )

        return self._extract_pdf_text(content)

    @staticmethod
    def _extract_pdf_text(
        content: bytes,
    ) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "PDF processing dependency is not installed."
            ) from exc

        try:
            reader = PdfReader(
                BytesIO(content)
            )
        except Exception as exc:
            raise ValueError(
                "Invalid PDF document."
            ) from exc

        pages: list[str] = []

        for page in reader.pages:
            text = page.extract_text() or ""
            normalized = " ".join(text.split())

            if normalized:
                pages.append(normalized)

        extracted_text = "\n\n".join(pages).strip()

        if not extracted_text:
            raise ValueError(
                "PDF does not contain extractable text."
            )

        return extracted_text