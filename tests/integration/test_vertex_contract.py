"""
Contract tests for Google Vertex AI / Gemini adapter.
Verifies system instruction separation, structured JSON response validation, and error mapping.
"""

from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from narrative_copilot.llm.vertex_provider import VertexAIProvider, VertexAIProviderError


class SampleResponseModel(BaseModel):
    summary: str
    confidence: float


@pytest.mark.asyncio
async def test_vertex_ai_provider_structured_generation() -> None:
    provider = VertexAIProvider(project_id="test-gcp-project", location="us-central1")

    # Mock client and generate_content response
    mock_response = MagicMock()
    mock_response.text = '{"summary": "Evidence verified.", "confidence": 0.98}'

    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response

    mock_client = MagicMock()
    mock_client.models = mock_models
    provider._client = mock_client

    result = await provider.generate_structured(
        system_instruction="You are a continuity reviewer.",
        evidence_payload={"claim": "blue eyes"},
        response_model=SampleResponseModel,
    )

    assert result.summary == "Evidence verified."
    assert result.confidence == 0.98

    # Verify generate_content called with structured schema config
    mock_models.generate_content.assert_called_once()
    call_kwargs = mock_models.generate_content.call_args.kwargs
    assert call_kwargs["config"]["response_mime_type"] == "application/json"
    assert call_kwargs["config"]["response_schema"] is SampleResponseModel


@pytest.mark.asyncio
async def test_vertex_ai_provider_malformed_json_error() -> None:
    provider = VertexAIProvider(project_id="test-gcp-project")

    mock_response = MagicMock()
    mock_response.text = "NOT_JSON"

    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response

    mock_client = MagicMock()
    mock_client.models = mock_models
    provider._client = mock_client

    with pytest.raises(VertexAIProviderError) as exc_info:
        await provider.generate_structured(
            system_instruction="sys",
            evidence_payload={},
            response_model=SampleResponseModel,
        )
    assert exc_info.value.code is not None
