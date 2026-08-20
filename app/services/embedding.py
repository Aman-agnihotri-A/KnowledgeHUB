from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    """Interface for generating vector embeddings."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> list[float]:
        raise NotImplementedError

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [
            self.embed(text)
            for text in texts
        ]


class DeterministicEmbeddingService(
    EmbeddingService,
):
    """
    Deterministic local embedding provider.

    This provider is intentionally used for local
    development and tests. A production provider can
    implement EmbeddingService without changing the
    document-processing pipeline.
    """

    def __init__(
        self,
        dimensions: int = 8,
    ) -> None:
        if dimensions <= 0:
            raise ValueError(
                "dimensions must be greater than zero."
            )

        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return "deterministic-local-v1"

    def embed(
        self,
        text: str,
    ) -> list[float]:
        normalized = text.strip()

        if not normalized:
            raise ValueError(
                "Cannot generate an embedding for empty text."
            )

        values = [
            0.0
            for _ in range(self._dimensions)
        ]

        encoded = normalized.encode(
            "utf-8"
        )

        for index, character in enumerate(
            encoded
        ):
            bucket = (
                index % self._dimensions
            )

            values[bucket] += (
                character / 255.0
            )

        magnitude = sum(
            value * value
            for value in values
        ) ** 0.5

        if magnitude == 0:
            return values

        return [
            value / magnitude
            for value in values
        ]