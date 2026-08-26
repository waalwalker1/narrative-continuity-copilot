#!/usr/bin/env python3
"""
Bootstrap script for .agents/ and .build/ infrastructure.
Creates all required agent definitions, skills, and private build ledger files.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

AGENTS = {
    "build-orchestrator": {
        "title": "Build Orchestrator",
        "description": "Coordinates full-system implementation, task DAG execution, evidence verification, and release gates.",
        "owns": [
            "Requirement decomposition",
            "Task DAG sequencing",
            "Cross-subsystem integration",
            "Acceptance matrix verification",
            "Release gate decisions",
        ],
    },
    "product-domain-researcher": {
        "title": "Product & Domain Researcher",
        "description": "Owns long-form fiction writing workflow research, editorial continuity taxonomy, and author agency requirements.",
        "owns": [
            "Narrative continuity problem definition",
            "Editorial taxonomy of narrative contradictions",
            "Author workflow integration patterns",
            "Distinction between verified facts and research assumptions",
        ],
    },
    "manuscript-structure-engineer": {
        "title": "Manuscript Structure Engineer",
        "description": "Owns parsing, structural segmentation (book -> part -> chapter -> scene -> block), and multi-format ingestion.",
        "owns": [
            "DOCX, Markdown, and plain text parsers",
            "Hierarchical structural unit schema",
            "Deterministic scene and block boundary detection",
            "Format-specific normalization and sanitization",
        ],
    },
    "provenance-anchor-engineer": {
        "title": "Provenance & Anchor Engineer",
        "description": "Owns stable block IDs, span anchors, text hashes, re-anchoring algorithms, and source citation verification.",
        "owns": [
            "Stable block UUID generation and preservation",
            "Local character offset and hash-anchoring",
            "Fuzzy and context-aware re-anchoring on edits",
            "Anchor stability and invalidation metrics",
        ],
    },
    "story-memory-engineer": {
        "title": "Story Memory Engineer",
        "description": "Owns structured story memory schemas: entities, facts, relations, timeline events, world rules, and open threads.",
        "owns": [
            "Pydantic schemas for story memory models",
            "Narrative scope and epistemic status typing",
            "Author canon status transitions",
            "Provenance-backed memory assertions",
        ],
    },
    "entity-resolution-engineer": {
        "title": "Entity & Alias Resolution Engineer",
        "description": "Owns entity resolution, alias merging, nickname handling, candidate merge scoring, and author-directed split/merge.",
        "owns": [
            "Lexical, phonetic, and contextual alias matching",
            "False-merge prevention heuristics",
            "Author confirmation workflow for ambiguous entities",
            "Entity graph consistency",
        ],
    },
    "retrieval-search-engineer": {
        "title": "Retrieval & Search Engineer",
        "description": "Owns Elasticsearch index mappings, BM25 lexical search, dense vector search, hybrid RRF fusion, and metadata filtering.",
        "owns": [
            "Elasticsearch chunk and memory index mappings",
            "Embedding provider abstraction and vector indexing",
            "Reciprocal Rank Fusion (RRF) implementation",
            "Task-specific retrieval strategies and score decomposition",
        ],
    },
    "continuity-reasoning-engineer": {
        "title": "Continuity Reasoning Engineer",
        "description": "Owns continuity contradiction taxonomy, deterministic candidate preconditions, and evidence-pair adjudicator.",
        "owns": [
            "12-class continuity contradiction taxonomy",
            "Deterministic candidate pair pre-filtering",
            "Evidence-grounded conflict adjudication",
            "Intentional ambiguity, rumor, and POV routing",
        ],
    },
    "llm-grounding-security-engineer": {
        "title": "LLM Grounding & Security Engineer",
        "description": "Owns structured prompts, schema validation, evidence-only context boundaries, and prompt-injection defense.",
        "owns": [
            "Evidence-delimited prompt templates",
            "Deterministic citation and output validation",
            "Manuscript prompt-injection defense and red-teaming",
            "Hallucination mitigation and unsupported claim rejection",
        ],
    },
    "incremental-indexing-engineer": {
        "title": "Incremental Indexing Engineer",
        "description": "Owns revision diffing, affected-block detection, selective memory invalidation, and incremental re-indexing.",
        "owns": [
            "Revision diffing algorithm",
            "Impact neighborhood calculation",
            "Selective embedding and memory invalidation",
            "Idempotent indexing job execution",
        ],
    },
    "api-platform-engineer": {
        "title": "API & Platform Engineer",
        "description": "Owns FastAPI backend, SQLite persistence, lifecycle endpoints, error contracts, and readiness checks.",
        "owns": [
            "REST API endpoints and Pydantic v2 serialization",
            "SQLite metadata persistence layer",
            "Standardized error codes and error handler",
            "Health and readiness probes",
        ],
    },
    "author-ux-engineer": {
        "title": "Author UX Engineer",
        "description": "Owns Vue 3 + TypeScript application, Quill 2 editor integration, continuity review cards, and author controls.",
        "owns": [
            "Quill editor with stable custom block attributes",
            "Continuity review queue and evidence navigation",
            "Story memory explorer and timeline visualization",
            "Author resolution action flows and local state sync",
        ],
    },
    "evaluation-scientist": {
        "title": "Evaluation Scientist",
        "description": "Owns synthetic benchmark generation, retrieval metrics, end-to-end continuity evaluation, and ablation studies.",
        "owns": [
            "Deterministic synthetic story pack generator",
            "180+ continuity benchmark test suite",
            "Retrieval (Recall@k, MRR, nDCG) and continuity (P/R/F1) metrics",
            "Comprehensive ablation and failure analysis reports",
        ],
    },
    "cloud-observability-engineer": {
        "title": "Cloud & Observability Engineer",
        "description": "Owns Vertex AI provider adapter, GCP reference architecture, OpenTelemetry tracing, Prometheus metrics, and Docker.",
        "owns": [
            "Google Vertex AI / Gemini SDK adapter",
            "OpenTelemetry spans and Prometheus metric instrumentation",
            "Multi-service Docker Compose configuration",
            "GCP reference Terraform/architecture specification",
        ],
    },
    "independent-security-release-auditor": {
        "title": "Independent Security & Release Auditor",
        "description": "Owns independent verification, red-team auditing, invariant falsification, and final release gate audit.",
        "owns": [
            "Adversarial prompt injection verification",
            "Evidence citation integrity auditing",
            "Zero-data-leak privacy verification",
            "Independent release certification verdict",
        ],
    },
    "docs-release-agent": {
        "title": "Documentation & Release Agent",
        "description": "Owns public documentation, architecture ADRs, metric synchronization, and public repo normalization.",
        "owns": [
            "Neutral open-source README and documentation",
            "Architecture Decision Records (ADRs)",
            "Automated public metric synchronization",
            "Public repo terminology normalization",
        ],
    },
}

SKILLS = {
    "source-verification": "Rigorous verification of claims, external libraries, and data contracts against authoritative sources.",
    "context-efficiency": "Designing compact, high-signal prompts and payload structures that minimize token overhead.",
    "instruction-boundary": "Strict isolation between system instructions and untrusted manuscript text using typed schemas.",
    "evidence-ledger": "Maintaining immutable proof records for every test run, benchmark score, and release assertion.",
    "test-first-contract": "Defining schema and behavioral contracts before implementing subsystem logic.",
    "reproducible-evals": "Ensuring deterministic seeds, fixed story packs, and reproducible evaluation pipelines.",
    "public-repo-normalization": "Auditing and stripping internal hiring context, private notes, and non-neutral language.",
    "security-review": "Systematic red-teaming for prompt injection, path traversal, XXE, and data leakage.",
    "technical-writing": "Authoring precise, neutral architectural and developer documentation.",
    "github-release": "Structuring CI/CD workflows, release gates, and packaging artifacts.",
    "manuscript-segmentation": "Parsing long-form fiction into hierarchical parts, chapters, scenes, and blocks.",
    "quill-delta-integrity": "Managing Quill 2 editor deltas, custom blots, and persistent block attributes.",
    "provenance-anchoring": "Binding narrative facts to immutable block hashes and character offsets.",
    "revision-aware-indexing": "Tracking manuscript revisions and maintaining version-specific search indices.",
    "story-memory-modeling": "Structuring narrative entities, facts, relations, rules, and threads.",
    "narrative-epistemics": "Modeling point-of-view beliefs, rumors, deception, and unreliable narration.",
    "temporal-continuity": "Reasoning over story timelines, causal ordering, and relative chronology.",
    "alias-entity-resolution": "Resolving character nicknames, titles, and variant names without false merges.",
    "elasticsearch-hybrid-retrieval": "Implementing combined BM25 lexical and dense vector search via Reciprocal Rank Fusion.",
    "embedding-provider-contracts": "Abstracting dense embedding generation across SentenceTransformers and test stubs.",
    "retrieval-reranking": "Contextual reranking of candidate evidence chunks for maximum precision.",
    "continuity-verification": "Adjudicating candidate fact pairs against the 12-class continuity taxonomy.",
    "intentional-contradiction-handling": "Recognizing and preserving deliberate author choices, mysteries, and POV conflicts.",
    "evidence-grounded-llm": "Constraining LLM reasoning strictly to provided evidence spans with anchor validation.",
    "hallucination-detection": "Deterministic post-validation of LLM outputs to reject uncited facts or invalid anchors.",
    "manuscript-prompt-injection-defense": "Hardening against adversarial dialogue and prompt injections embedded in creative prose.",
    "author-agency-ux": "Designing editorial UI patterns that put the author in total control of story canon.",
    "privacy-minimization": "Ensuring zero raw manuscript leakage into telemetry, cloud logs, or public telemetry.",
    "vertex-ai-adapter": "Implementing standard-compliant Google GenAI SDK integrations with structured output.",
    "long-context-evaluation": "Benchmarking retrieval and memory performance over book-length (60k-100k word) manuscripts.",
    "observability": "Instrumenting systems with Prometheus metrics and OpenTelemetry trace spans.",
    "ai-assisted-development": "Developing automated testing, golden fixture generation, and evaluation harness tools.",
}


def bootstrap():
    # 1. Create .agents/agents
    agents_dir = BASE_DIR / ".agents" / "agents"
    for name, data in AGENTS.items():
        agent_dir = agents_dir / name
        agent_dir.mkdir(parents=True, exist_ok=True)
        md_file = agent_dir / "agent.md"
        owns_list = "\n".join(f"- {o}" for o in data["owns"])
        content = f"""# {data["title"]} (`{name}`)

## Description
{data["description"]}

## Ownership & Scope
{owns_list}

## Interaction Protocol
- Adhere strictly to the repository architecture and non-negotiable product principles.
- Maintain deterministic evidence-grounding across all deliverables.
- Log all decisions, milestones, and benchmark outputs to the private build ledger.
"""
        md_file.write_text(content.strip() + "\n")
        print(f"Created agent: {name}")

    # 2. Create .agents/skills
    skills_dir = BASE_DIR / ".agents" / "skills"
    for name, desc in SKILLS.items():
        skill_dir = skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        md_file = skill_dir / "SKILL.md"
        content = f"""---
name: {name}
description: {desc}
---

# Skill: {name.replace("-", " ").title()}

## Objective
{desc}

## Standard Operating Procedure
1. Verify input contracts and schema definitions prior to execution.
2. Execute procedural steps using evidence-backed, deterministic techniques.
3. Validate output against invariants and record artifacts in the evidence ledger.
"""
        md_file.write_text(content.strip() + "\n")
        print(f"Created skill: {name}")

    # 3. Create .build/ control plane
    build_dir = BASE_DIR / ".build"
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "handoffs").mkdir(parents=True, exist_ok=True)

    status_content = """# Build Status: Narrative Continuity Copilot

## Build Phase: Phase 1 — Research, Setup & Contracts
- **Status**: IN_PROGRESS
- **Orchestrator**: build-orchestrator
- **Timestamp**: 2026-08-26T18:25:00Z
- **Active Task**: Bootstrap infrastructure, define schemas, and setup repo skeleton.

## Subsystem Progress
- [x] Agent definitions & skills bootstrap (.agents/)
- [x] Private build control plane (.build/)
- [ ] Core schemas & ADRs (Phase 1)
- [ ] Manuscript structure & anchor engine (Phase 2)
- [ ] Elasticsearch & embedding pipeline (Phase 3)
- [ ] Structured story memory (Phase 4)
- [ ] Continuity reasoning & adjudication (Phase 5)
- [ ] Incremental reindexing (Phase 6)
- [ ] FastAPI backend service (Phase 7)
- [ ] Vue 3 + Quill frontend application (Phase 8)
- [ ] Synthetic evaluation benchmark (Phase 9)
- [ ] Observability, Docker, and CI (Phase 10)
- [ ] Normalization, security audit, and freeze (Phase 11)
"""
    (build_dir / "STATUS.md").write_text(status_content.strip() + "\n")

    task_dag_content = """# Task Dependency Graph (DAG)

```mermaid
graph TD
    T01[T01: Bootstrap Agents & Ledger] --> T02[T02: Project Skeleton & Dependencies]
    T02 --> T03[T03: Core Schemas & ADRs]
    T03 --> T04[T04: Manuscript Structure & Ingestion]
    T04 --> T05[T05: Stable Provenance Anchor Engine]
    T05 --> T06[T06: Embedding Providers & Elasticsearch]
    T06 --> T07[T07: Hybrid Retrieval & Scoring]
    T07 --> T08[T08: Story Memory Extraction & Entity Resolution]
    T08 --> T09[T09: Continuity Reasoning & Preconditions]
    T09 --> T10[T10: Evidence Critic & Deterministic Validator]
    T10 --> T11[T11: Incremental Indexing Engine]
    T11 --> T12[T12: FastAPI Platform & Persistence]
    T12 --> T13[T13: Vue 3 + Quill Frontend]
    T13 --> T14[T14: Synthetic Story & Benchmark Generator]
    T14 --> T15[T15: Full Evaluation & Ablation Suite]
    T15 --> T16[T16: Prompt Injection Red-Teaming Suite]
    T16 --> T17[T17: Observability, Metrics & Docker E2E]
    T17 --> T18[T18: Playwright Browser Tests]
    T18 --> T19[T19: Public Normalization & Docs Sync]
    T19 --> T20[T20: Independent Security Release Audit]
    T20 --> T21[T21: Release Gate & Freeze]
```

## Task Execution State
- [x] **T01**: Bootstrap Agents, Skills & Build Ledger
- [ ] **T02**: Python (`pyproject.toml`, `uv.lock`) & Node (`package.json`) workspace setup
- [ ] **T03**: Pydantic schemas, error codes, and ADRs
- [ ] **T04**: DOCX / Markdown / Plaintext manuscript structure parser
- [ ] **T05**: Stable block IDs, hash anchors, and edit re-anchoring benchmark
- [ ] **T06**: Embedding providers (`SentenceTransformer`, `DeterministicStub`) & Elasticsearch client
- [ ] **T07**: Hybrid RRF search, task queries, and score decomposition
- [ ] **T08**: Story memory extraction, canonicalization, and alias resolution
- [ ] **T09**: Continuity conflict taxonomy (12 classes) & candidate generator
- [ ] **T10**: Deterministic precondition filter, LLM adjudicator, and output validator
- [ ] **T11**: Incremental indexing, revision diffing, and selective re-checking
- [ ] **T12**: FastAPI endpoints, SQLite persistence, and health probes
- [ ] **T13**: Vue 3 + Quill editor, continuity cards, memory views, and author controls
- [ ] **T14**: Synthetic story generator (>=36 packs, >=180 cases)
- [ ] **T15**: Evaluation suite (retrieval, continuity, long-manuscript, ablations)
- [ ] **T16**: Prompt injection test suite (>=40 adversarial fixtures)
- [ ] **T17**: OpenTelemetry, Prometheus metrics, and Docker Compose setup
- [ ] **T18**: Playwright browser E2E test flows
- [ ] **T19**: Public documentation, metric synchronization script, and normalization
- [ ] **T20**: Independent release audit & evidence verification
- [ ] **T21**: Final release gate freeze
"""
    (build_dir / "TASK_DAG.md").write_text(task_dag_content.strip() + "\n")

    evidence_content = """# Evidence Ledger

| Timestamp | Task | Artifact / Test / Metric | Result | Signed-Off By |
|---|---|---|---|---|
| 2026-08-26T18:25:00Z | T01 | `.agents/` (16 agents, 32 skills) | CREATED | build-orchestrator |
| 2026-08-26T18:25:00Z | T01 | `.build/` private control plane | INITIALIZED | build-orchestrator |
"""
    (build_dir / "EVIDENCE_LEDGER.md").write_text(evidence_content.strip() + "\n")

    decisions_content = """# Private Build Decisions & Invariants

## D01: Reviewer, Not Ghostwriter
The system acts exclusively as an evidence-grounded continuity reviewer and story-memory assistant. It never rewrites prose, generates scenes, or alters canon without explicit author decision.

## D02: Strict Evidence Grounding
All continuity alerts and memory assertions must cite valid, existing source anchors. Invented or hallucinated citations are deterministically rejected.

## D03: Epistemic & Intentionality Scoping
Apparent contradictions arising from POV beliefs, character lies, rumors, dreams, or intentional ambiguity are classified properly and never flattened into raw plot errors.

## D04: Stable Provenance Over Offsets
Block UUIDs combined with content hashes and local character offsets ensure resilient re-anchoring across editing sessions.

## D05: Privacy by Default
No raw manuscript text in application telemetry, logs, or unrequested cloud calls. Local execution mode operates completely zero-credential.
"""
    (build_dir / "DECISIONS.md").write_text(decisions_content.strip() + "\n")

    snapshot_content = """# Source & Dependency Snapshot
- Target Stack: Python 3.12+ (uv), Vue 3 + TypeScript (Node 20+), Elasticsearch 8, SQLite, Quill 2
- Model Abstractions: SentenceTransformers (local pinned CPU model) / Vertex AI SDK / Deterministic Fixtures
- Testing Frameworks: Pytest, Hypothesis, Vitest, Vue Test Utils, Playwright
"""
    (build_dir / "SOURCE_SNAPSHOT.md").write_text(snapshot_content.strip() + "\n")

    risk_content = """# Risk Register & Mitigation

| Risk ID | Description | Impact | Mitigation Strategy |
|---|---|---|---|
| R-01 | Hallucinated evidence citations in LLM adjudicator | Critical | Deterministic validator rejects citations not in provided anchor payload |
| R-02 | False positives on deliberate author mysteries / POV | High | Narrative epistemic scope modeling and author suppression actions |
| R-03 | Stale citations after manuscript editing | High | Stable block UUIDs, context hashing, and re-anchor confidence scoring |
| R-04 | Performance degradation on 100k-word manuscripts | Medium | Hybrid Elasticsearch retrieval + selective incremental reindexing |
| R-05 | Manuscript prompt injection via creative dialogue | High | Structural JSON boundary separation and strict output schema validation |
"""
    (build_dir / "RISK_REGISTER.md").write_text(risk_content.strip() + "\n")

    print("Private build control plane initialized successfully.")


if __name__ == "__main__":
    bootstrap()
