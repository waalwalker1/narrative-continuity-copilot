"""
Unit tests for benchmark environment metadata generation and invariants.
"""

import json
from pathlib import Path


def test_benchmark_environment_schema() -> None:
    env_file = (
        Path(__file__).resolve().parent.parent.parent
        / "artifacts"
        / "evals"
        / "latest"
        / "BENCHMARK_ENVIRONMENT.json"
    )
    if not env_file.exists():
        return

    data = json.loads(env_file.read_text(encoding="utf-8"))

    # Invariants for canonical full reference release
    assert data["embedding_mode"] == "sentence_transformer"
    assert data["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert data["embedding_dimension"] == 384
    assert data["search_mode"] in ("FULL_REFERENCE", "LOCAL_LIGHT")
    assert "benchmark_source_commit" in data
    assert len(data["benchmark_source_commit"]) >= 7
