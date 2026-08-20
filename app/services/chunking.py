class TextChunkingService:
    """Split extracted document text into deterministic chunks."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(
        self,
        text: str,
    ) -> list[str]:
        normalized_text = " ".join(
            text.split()
        ).strip()

        if not normalized_text:
            return []

        chunks: list[str] = []
        start = 0
        text_length = len(normalized_text)

        while start < text_length:
            end = min(
                start + self.chunk_size,
                text_length,
            )

            if end < text_length:
                boundary = normalized_text.rfind(
                    " ",
                    start,
                    end,
                )

                if boundary > start:
                    end = boundary

            chunk = normalized_text[
                start:end
            ].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            next_start = end - self.chunk_overlap

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks