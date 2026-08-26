# ADR-006: Deterministic Validation Surrounding LLM Invocations

## Status
Accepted

## Context
LLMs are prone to hallucinating citations, inventing new facts, and flattening literary ambiguity into false contradictions.

## Decision
Enclose all LLM inferences within deterministic boundaries:
1. **Preconditions**: Filter candidate fact pairs deterministically before calling LLM adjudicators.
2. **Strict Schema**: Providers must return structured JSON conforming to Pydantic models.
3. **Evidence Critic**: Deterministically rejects any cited anchor ID not present in the input payload.
4. **Final Validator**: Deterministically validates that output alerts cite real, existing anchors before displaying them to the author.

## Consequences
- Guaranteed 0% hallucinated evidence anchor rate.
- Complete auditability and reproducibility.
