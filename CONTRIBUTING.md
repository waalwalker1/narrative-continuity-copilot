# Contributing to Narrative Continuity Copilot

Thank you for your interest in contributing to Narrative Continuity Copilot! We welcome contributions to our evidence-grounded story memory and narrative continuity analysis framework.

## Code of Conduct
We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone.

## Development Workflow

### Prerequisites
- Python 3.12+ with [`uv`](https://github.com/astral-sh/uv)
- Node.js 20+ with `npm`
- Docker & Docker Compose (for Elasticsearch)

### Setup
```bash
# Clone the repository
git clone https://github.com/example/narrative-continuity-copilot.git
cd narrative-continuity-copilot

# Install Python and Node dependencies
make setup

# Start Elasticsearch
docker compose up -d elasticsearch

# Run validation suite
make verify-local
```

### Quality Standards
Before opening a pull request, ensure all gates pass:
- `make lint` (Ruff, ESLint)
- `make typecheck` (mypy, vue-tsc)
- `make test` (unit and integration tests)
- `make eval` (retrieval and continuity benchmark)
- `make security` (bandit, pip-audit, prompt injection suite)
- `make release-check` (full clean validation)

## Principles
1. **Author Agency First**: AI is a reviewer and memory aid, not an autonomous ghostwriter.
2. **Provenance Grounding**: All continuity flags must cite valid manuscript anchors.
3. **Privacy**: Never log raw manuscript text in telemetry.
