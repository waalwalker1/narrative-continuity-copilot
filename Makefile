.PHONY: setup data index dev api web lint typecheck test test-integration test-e2e eval red-team demo security build docker-smoke verify-local release-check clean

PYTHON ?= .venv/bin/python
UVICORN ?= .venv/bin/uvicorn
PYTEST ?= .venv/bin/pytest
RUFF ?= .venv/bin/ruff
MYPY ?= .venv/bin/mypy
BANDIT ?= .venv/bin/bandit
PIP_AUDIT ?= .venv/bin/pip-audit

setup:
	uv sync --extra dev --extra cloud
	npm install

data:
	PYTHONPATH=. $(PYTHON) tools/synthetic_stories/generator.py

index:
	PYTHONPATH=. $(PYTHON) -c "import asyncio; from apps.api.main import es_engine; asyncio.run(es_engine.ensure_indices())"

dev:
	make -j2 api web

api:
	PYTHONPATH=. $(UVICORN) apps.api.main:app --reload --port 8000

web:
	npm run dev

lint:
	$(RUFF) check .
	$(RUFF) format --check .
	npm run lint

typecheck:
	$(MYPY) src apps/api tests
	npm run typecheck

test:
	PYTHONPATH=. $(PYTEST) tests/unit tests/property

test-integration:
	PYTHONPATH=. $(PYTEST) tests/integration

test-e2e:
	npx playwright test --config apps/web/playwright.config.ts

eval:
	PYTHONPATH=. $(PYTHON) evals/runners/run_all.py
	PYTHONPATH=. $(PYTHON) scripts/sync_public_metrics.py --write

red-team:
	PYTHONPATH=. $(PYTHON) -c "import asyncio; from evals.runners.injection_runner import InjectionBenchmarkRunner; r = InjectionBenchmarkRunner(); res = asyncio.run(r.run_benchmark()); print(res)"

demo:
	PYTHONPATH=. $(PYTHON) -c "print('Offline demo ready. Run make dev and navigate to http://localhost:3000')"

security:
	$(BANDIT) -r src apps/api -ll
	$(PIP_AUDIT)
	python3 scripts/npm_audit_gate.py
	.venv/bin/detect-secrets scan src apps tests docs scripts README.md --baseline .secrets.baseline
	make red-team

build:
	npm run build
	$(PYTHON) -m build

docker-smoke:
	python3 scripts/docker_smoke.py

verify-local: lint typecheck test test-integration eval security

release-check: verify-local
	PYTHONPATH=. $(PYTHON) scripts/sync_public_metrics.py --check
	npm run build
	@echo "Local release validation gates verified successfully."

clean:
	rm -rf .pytest_cache .coverage htmlcov coverage.xml .mypy_cache .ruff_cache apps/web/dist node_modules/.vite *.db
