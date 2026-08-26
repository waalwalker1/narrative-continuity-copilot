"""
LLM and Embedding provider protocols and interfaces.
"""

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredLLMProvider(Protocol):
    """
    Protocol for LLM providers that return strictly typed Pydantic models from evidence.
    """

    async def generate_structured(
        self,
        system_instruction: str,
        evidence_payload: dict[str, Any],
        response_model: type[T],
    ) -> T:
        """
        Generate structured output conforming to response_model.
        """
        ...


class EmbeddingProvider(Protocol):
    """
    Protocol for dense text embedding providers.
    """

    @property
    def dimension(self) -> int: ...

    @property
    def model_name(self) -> str: ...

    def encode(self, texts: list[str]) -> list[list[float]]: ...

    async def aencode(self, texts: list[str]) -> list[list[float]]: ...
