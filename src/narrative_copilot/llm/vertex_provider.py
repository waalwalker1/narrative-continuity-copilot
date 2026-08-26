"""
Google Vertex AI / Gemini adapter for structured LLM inference.
"""

import json
import os
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from narrative_copilot.schemas.errors import ErrorCode

T = TypeVar("T", bound=BaseModel)


class VertexAIProviderError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class VertexAIProvider:
    """
    Adapter for Google Vertex AI / Gemini models using the official google-genai SDK.
    Enforces structured JSON outputs and schema validation.
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "")
        self.location = location or os.getenv("GCP_LOCATION", "us-central1")
        self.model_name = model_name or os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from google import genai

                self._client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location,
                )
            except Exception as e:
                raise VertexAIProviderError(
                    ErrorCode.LLM_PROVIDER_UNAVAILABLE,
                    f"Failed to initialize Vertex AI client: {e}",
                )
        return self._client

    async def generate_structured(
        self,
        system_instruction: str,
        evidence_payload: dict[str, Any],
        response_model: type[T],
    ) -> T:
        """
        Generate structured output adhering to response_model schema.
        """
        client = self._get_client()

        prompt_content = (
            f"EVIDENCE PAYLOAD (Strictly ground your reasoning in this data):\n"
            f"{json.dumps(evidence_payload, indent=2)}\n\n"
            f"Respond with a valid JSON object matching the required schema."
        )

        try:
            # Call generate_content with structured response schema
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt_content,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "response_schema": response_model,
                },
            )

            response_text = response.text
            if not response_text:
                raise VertexAIProviderError(
                    ErrorCode.SCHEMA_MISMATCH,
                    "Empty response returned from Vertex AI model.",
                )

            data = json.loads(response_text)
            return response_model.model_validate(data)

        except ValidationError as ve:
            raise VertexAIProviderError(
                ErrorCode.SCHEMA_MISMATCH,
                f"Model response did not adhere to schema {response_model.__name__}: {ve}",
            )
        except Exception as e:
            raise VertexAIProviderError(
                ErrorCode.LLM_PROVIDER_UNAVAILABLE,
                f"Vertex AI inference error: {e}",
            )
