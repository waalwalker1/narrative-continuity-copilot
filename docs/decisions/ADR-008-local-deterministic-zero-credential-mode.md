# ADR-008: Local Deterministic Zero-Credential Execution Mode

## Status
Accepted

## Context
Developers, CI pipelines, and security audits need to run unit, integration, and evaluation suites reliably without requiring external cloud accounts or paid API keys.

## Decision
Provide a canonical `LOCAL_ONLY` execution path featuring:
- Local SentenceTransformers CPU embeddings (`all-MiniLM-L6-v2`).
- `DeterministicFixtureLLMProvider` for 100% reproducible offline test and evaluation runs.
- In-memory mock fallback for Elasticsearch.

## Consequences
- Clean checkout verification passes out-of-the-box in zero-network environments.
- Cloud providers (Vertex AI) remain optional adapters with separate contract tests.
