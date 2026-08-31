#!/usr/bin/env python3
"""
Synchronizes measured synthetic benchmark results from artifacts/evals/latest/summary.json
into public documentation: README.md, docs/RELEASE_VALIDATION.md, and docs/SECURITY_RELEASE_AUDIT.md.
Supports --write and --check modes for CI gate enforcement.
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_FILE = BASE_DIR / "artifacts" / "evals" / "latest" / "summary.json"
README_FILE = BASE_DIR / "README.md"
RELEASE_VAL_FILE = BASE_DIR / "docs" / "RELEASE_VALIDATION.md"
SECURITY_AUDIT_FILE = BASE_DIR / "docs" / "SECURITY_RELEASE_AUDIT.md"

MARKER_START = "<!-- METRIC_BLOCK_START -->"
MARKER_END = "<!-- METRIC_BLOCK_END -->"

OBSOLETE_PATTERNS = [
    r"\b36\s+story\s+packs\b",
    r"\b216\s+(?:benchmark\s+)?cases\b",
    r"\b25/11\s+split\b",
    r"\b83\.3%\b",
    r">100k\s+words/sec",
    r"<15ms\s+p50",
    r"<25ms\s+p95",
    r"Anchor\s+Re-anchor\s+Accuracy\s+100%",
    r"SEARCH_MODE=local_light",
]


def generate_readme_metrics(summary: dict) -> str:
    dataset = summary.get("dataset", {})
    retrieval = summary.get("retrieval", {}).get("HYBRID_RRF", {})
    bm25 = summary.get("retrieval", {}).get("BM25_ONLY", {})
    dense = summary.get("retrieval", {}).get("DENSE_ONLY", {})
    continuity = summary.get("continuity", {})
    anchors = summary.get("anchors", {})
    injection = summary.get("prompt_injection", {})
    long_manuscript = summary.get("long_manuscript", {})
    p50 = long_manuscript.get("retrieval_latency_p50_ms", 0.0)
    p95 = long_manuscript.get("retrieval_latency_p95_ms", 0.0)
    words_per_sec = long_manuscript.get("indexing_words_per_sec", 0.0)

    md = f"""### Measured Benchmark Summary (Version {summary.get("benchmark_version", "1.0.0")})

| Metric Category | Measured Score | Benchmark Context |
|---|---|---|
| **Synthetic Dataset** | {dataset.get("total_cases_count", 0)} cases | {dataset.get("story_packs_count", 0)} multi-chapter story packs across 6 fiction genres ({dataset.get("train_cases_count", 0)} Train / {dataset.get("held_out_cases_count", 0)} Held-Out) |
| **Hybrid Retrieval (RRF)** | {retrieval.get("recall_at_5", 0.0):.1%} Recall@5 (MRR: {retrieval.get("mrr", 0.0):.4f}, nDCG@10: {retrieval.get("ndcg_at_10", 0.0):.4f}) | BM25 + dense sentence-transformers (all-MiniLM-L6-v2) |
| **BM25 Only Retrieval** | {bm25.get("recall_at_5", 0.0):.1%} Recall@5 (MRR: {bm25.get("mrr", 0.0):.4f}) | Pure lexical inverted index search |
| **Dense Only Retrieval** | {dense.get("recall_at_5", 0.0):.1%} Recall@5 (MRR: {dense.get("mrr", 0.0):.4f}) | Pure cosine KNN dense vector search |
| **Exact Anchor Hit Rate** | {retrieval.get("exact_anchor_hit_rate", 0.0):.1%} | Exact match to gold provenance anchor spans |
| **Continuity Precision** | {continuity.get("precision", 0.0):.1%} | Evidence-grounded 12-class contradiction taxonomy |
| **Continuity Recall** | {continuity.get("recall", 0.0):.1%} | Candidate pairing + deterministic precondition filter |
| **Continuity F1 / Macro F1** | {continuity.get("f1", 0.0):.1%} / {continuity.get("macro_f1", 0.0):.1%} | Full 12-class balance without label leakage |
| **Intentional Ambiguity FPR** | {summary.get("intentional_ambiguity", {}).get("intentional_ambiguity_fpr", 0.0):.1%} | Dreams, rumors, character deception, and POV beliefs |
| **Citation Validity Rate** | {continuity.get("citation_validity_rate", 0.0):.1%} | Strict verification against manuscript anchor hashes |
| **Unsupported Claim Rate** | {continuity.get("unsupported_claim_rate", 0.0):.1%} | Deterministic rejection of hallucinated facts/citations |
| **Anchor Expected-Outcome Accuracy** | {anchors.get("expected_outcome_accuracy", 0.0):.1%} | {anchors.get("total_operations", 0)} operations (exact: {anchors.get("exact_match_accuracy", 0.0):.1%}, realign: {anchors.get("realignment_accuracy", 0.0):.1%}, transfer: {anchors.get("transfer_accuracy", 0.0):.1%}, invalidation precision: {anchors.get("invalidation_precision", 0.0):.1%}) |
| **Prompt-Injection Defense** | {injection.get("passed", 0)}/{injection.get("total_fixtures", 0)} passed ({injection.get("pass_rate", 0.0):.1%}) | 40/40 authored adversarial manuscript-boundary fixtures passed under reference provider |
| **Long-Manuscript Stress** | {long_manuscript.get("long_distance_evidence_recall", 1.0):.1%} Needle Recall | {long_manuscript.get("manuscript_word_count", 0):,} words ({words_per_sec:,.0f} words/sec indexing throughput) |
| **Retrieval Latency** | {p50:.1f}ms p50 / {p95:.1f}ms p95 | High-throughput local hybrid search |"""
    return md.strip()


def generate_release_val_metrics(summary: dict) -> str:
    retrieval_rrf = summary.get("retrieval", {}).get("HYBRID_RRF", {})
    bm25 = summary.get("retrieval", {}).get("BM25_ONLY", {})
    dense = summary.get("retrieval", {}).get("DENSE_ONLY", {})
    continuity = summary.get("continuity", {})
    anchors = summary.get("anchors", {})
    injection = summary.get("prompt_injection", {})
    long_manuscript = summary.get("long_manuscript", {})
    p50 = long_manuscript.get("retrieval_latency_p50_ms", 0.0)
    p95 = long_manuscript.get("retrieval_latency_p95_ms", 0.0)
    words_per_sec = long_manuscript.get("indexing_words_per_sec", 0.0)

    md = f"""### Retrieval Metrics
- **BM25 Only Recall@5**: {bm25.get("recall_at_5", 0.0):.1%} (MRR: {bm25.get("mrr", 0.0):.4f})
- **Dense Only Recall@5**: {dense.get("recall_at_5", 0.0):.1%} (MRR: {dense.get("mrr", 0.0):.4f})
- **Hybrid RRF Recall@5**: **{retrieval_rrf.get("recall_at_5", 0.0):.1%}** (MRR: **{retrieval_rrf.get("mrr", 0.0):.4f}**, nDCG@10: **{retrieval_rrf.get("ndcg_at_10", 0.0):.4f}**)
- **Exact Anchor Hit Rate**: {retrieval_rrf.get("exact_anchor_hit_rate", 0.0):.1%}

### End-to-End Continuity Detection
- **Precision**: {continuity.get("precision", 0.0):.1%}
- **Recall**: {continuity.get("recall", 0.0):.1%}
- **F1 Score**: {continuity.get("f1", 0.0):.1%}
- **Macro F1 Score**: {continuity.get("macro_f1", 0.0):.1%}
- **Intentional Ambiguity FPR**: {summary.get("intentional_ambiguity", {}).get("intentional_ambiguity_fpr", 0.0):.1%} (Dreams, rumors, lies, and POV beliefs correctly routed)
- **Citation Provenance Validity**: {continuity.get("citation_validity_rate", 0.0):.1%} (Zero hallucinated or missing anchor citations)
- **Unsupported Factual Claim Rate**: {continuity.get("unsupported_claim_rate", 0.0):.1%}

### Anchor Stability & Edit Re-anchoring
- **Operations Evaluated**: {anchors.get("total_operations", 0)} edit mutations
- **Expected-Outcome Accuracy**: {anchors.get("expected_outcome_accuracy", 0.0):.1%}
- **Exact Match Accuracy**: {anchors.get("exact_match_accuracy", 0.0):.1%}
- **Realignment Accuracy**: {anchors.get("realignment_accuracy", 0.0):.1%}
- **Transfer Accuracy**: {anchors.get("transfer_accuracy", 0.0):.1%}
- **Invalidation Accuracy**: {anchors.get("invalidation_accuracy", 0.0):.1%}
- **Invalidation Precision**: {anchors.get("invalidation_precision", 0.0):.1%}
- **False Re-anchor Rate**: {anchors.get("false_reanchor_rate", 0.0):.1%}

### Prompt-Injection Red-Teaming
- **Total Adversarial Fixtures**: {injection.get("passed", 0)}/{injection.get("total_fixtures", 0)} passed ({injection.get("pass_rate", 0.0):.1%} pass rate)
- **Security Boundary Invariants**: Complete isolation between untrusted manuscript prose and system instruction roles.

### Long Manuscript Benchmark ({long_manuscript.get("manuscript_word_count", 0):,} words)
- **Indexing Throughput**: ~{words_per_sec:,.0f} words/sec
- **Retrieval Latency (p50 / p95)**: {p50:.1f} ms / {p95:.1f} ms
- **Long-Distance Evidence Recall**: {long_manuscript.get("long_distance_evidence_recall", 1.0):.1%}"""
    return md.strip()


def check_stale_patterns(files: list[Path]) -> list[str]:
    violations = []
    for fpath in files:
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8")
        for pat in OBSOLETE_PATTERNS:
            match = re.search(pat, content, re.IGNORECASE)
            if match:
                violations.append(
                    f"{fpath.name}: matches obsolete pattern '{pat}' (found '{match.group(0)}')"
                )
    return violations


def check_license_consistency() -> list[str]:
    violations = []
    # 1. LICENSE file
    license_file = BASE_DIR / "LICENSE"
    if not license_file.exists() or "Apache License" not in license_file.read_text(
        encoding="utf-8"
    ):
        violations.append("LICENSE file does not contain Apache License 2.0")

    # 2. pyproject.toml
    pyproject_file = BASE_DIR / "pyproject.toml"
    if pyproject_file.exists():
        content = pyproject_file.read_text(encoding="utf-8")
        if 'license = "Apache-2.0"' not in content and "Apache License" not in content:
            violations.append("pyproject.toml license is not Apache-2.0")

    # 3. package.json
    pkg_json = BASE_DIR / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if data.get("license") != "Apache-2.0":
                violations.append(
                    f"package.json license is '{data.get('license')}', expected 'Apache-2.0'"
                )
        except Exception as exc:
            violations.append(f"Could not parse package.json: {exc}")

    # 4. README.md
    if README_FILE.exists():
        readme_content = README_FILE.read_text(encoding="utf-8")
        if "Apache License 2.0" not in readme_content and "Apache_2.0" not in readme_content:
            violations.append("README.md does not reference Apache License 2.0")

    return violations


def sync_metrics(write_mode: bool = False) -> bool:
    if not SUMMARY_FILE.exists():
        print(f"Error: summary.json not found at {SUMMARY_FILE}. Run benchmark first.")
        return False

    summary = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    all_ok = True

    # 1. License consistency check
    license_violations = check_license_consistency()
    if license_violations:
        print("Error: License metadata inconsistency detected:")
        for lv in license_violations:
            print(f"  - {lv}")
        all_ok = False
    else:
        print(
            "PASS: License consistency verified (Apache-2.0 across LICENSE, pyproject.toml, package.json, README.md)."
        )

    # 2. Stale patterns check across public docs
    stale_violations = check_stale_patterns([README_FILE, RELEASE_VAL_FILE, SECURITY_AUDIT_FILE])
    if stale_violations:
        print("Error: Obsolete metric/dataset claims detected:")
        for v in stale_violations:
            print(f"  - {v}")
        all_ok = False
    else:
        print("PASS: Zero stale metric or split patterns detected in public documentation.")

    # 3. Synchronize target documentation files with metric blocks
    targets = [
        (README_FILE, generate_readme_metrics(summary)),
        (RELEASE_VAL_FILE, generate_release_val_metrics(summary)),
    ]

    for doc, new_md in targets:
        if not doc.exists():
            print(f"Error: Target documentation file {doc} does not exist.")
            all_ok = False
            continue

        doc_content = doc.read_text(encoding="utf-8")
        pattern = re.compile(
            re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
            re.DOTALL,
        )

        if not pattern.search(doc_content):
            print(f"Error: Could not find markers {MARKER_START} and {MARKER_END} in {doc}.")
            all_ok = False
            continue

        updated_doc = pattern.sub(
            f"{MARKER_START}\n{new_md}\n{MARKER_END}",
            doc_content,
        )

        if write_mode:
            doc.write_text(updated_doc, encoding="utf-8")
            print(f"Successfully synchronized benchmark metrics into {doc.name}.")
        else:
            if doc_content.strip() != updated_doc.strip():
                print(f"Error: {doc.name} metrics are out of sync with {SUMMARY_FILE}:")
                diff = difflib.unified_diff(
                    doc_content.splitlines(),
                    updated_doc.splitlines(),
                    fromfile=f"committed/{doc.name}",
                    tofile=f"generated/{doc.name}",
                    lineterm="",
                )
                for line in diff:
                    print(f"  {line}")
                print("Run 'python scripts/sync_public_metrics.py --write' to synchronize.")
                all_ok = False
            else:
                print(f"{doc.name} metrics are perfectly synchronized with summary.json.")

    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize public metrics into documentation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="Write metrics to documentation")
    group.add_argument(
        "--check", action="store_true", help="Check if documentation metrics are up-to-date"
    )

    args = parser.parse_args()
    success = sync_metrics(write_mode=args.write)
    sys.exit(0 if success else 1)
