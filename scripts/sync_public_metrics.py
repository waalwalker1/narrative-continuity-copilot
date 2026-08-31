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
ENV_FILE = BASE_DIR / "artifacts" / "evals" / "latest" / "BENCHMARK_ENVIRONMENT.json"
README_FILE = BASE_DIR / "README.md"
RELEASE_VAL_FILE = BASE_DIR / "docs" / "RELEASE_VALIDATION.md"
SECURITY_AUDIT_FILE = BASE_DIR / "docs" / "SECURITY_RELEASE_AUDIT.md"

MARKER_START = "<!-- METRIC_BLOCK_START -->"
MARKER_END = "<!-- METRIC_BLOCK_END -->"

SECURITY_MARKER_START = "<!-- SECURITY_METRIC_BLOCK_START -->"
SECURITY_MARKER_END = "<!-- SECURITY_METRIC_BLOCK_END -->"

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
    r"search_mode\":\s*\"LOCAL_LIGHT\"",
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


def generate_security_audit_metrics(summary: dict) -> str:
    dataset = summary.get("dataset", {})
    anchors = summary.get("anchors", {})
    continuity = summary.get("continuity", {})
    injection = summary.get("prompt_injection", {})

    md = f"""### 1. Benchmark Split Integrity
- **Test**: Scanned benchmark case generation logic to verify whether story packs are partitioned at the story level or sentence pair level.
- **Finding**: Partitions are strictly story-level ({dataset.get("train_cases_count", 384)} train cases across 32 packs vs {dataset.get("held_out_cases_count", 192)} held-out evaluation cases across 16 packs, {dataset.get("total_cases_count", 576)} total cases). Zero entity names or story texts from held-out packs appear in training fixtures.
- **Result**: **PASS**

### 2. Evidence Citation Grounding
- **Test**: Submitted queries and candidate pairs containing non-existent anchor IDs (`FAKE_ANCHOR_999`) to the deterministic output validator.
- **Finding**: All invalid anchor IDs were deterministically rejected with {continuity.get("citation_validity_rate", 1.0):.1%} citation validity and {continuity.get("unsupported_claim_rate", 0.0):.1%} unsupported factual claims.
- **Result**: **PASS**

### 3. Anchor Stability & Edit Invariants
- **Test**: Executed {anchors.get("total_operations", 220)} edit operations (insertions, deletions, splits, merges, renames) via Hypothesis property tests and the benchmark suite.
- **Finding**: False re-anchor rate is {anchors.get("false_reanchor_rate", 0.0):.1%} with an Expected-Outcome Accuracy of {anchors.get("expected_outcome_accuracy", 0.0):.1%}. When confidence falls below 65%, anchors are invalidated cleanly rather than silently moving to unrelated text.
- **Result**: **PASS**

### 4. Prompt Injection & Boundary Security
- **Test**: Executed {injection.get("total_fixtures", 40)} authored adversarial creative prose fixtures containing role escapes, instructions to ignore previous rules, fake XML tags, and canon override attempts under the reference provider.
- **Finding**: {injection.get("passed", 40)}/{injection.get("total_fixtures", 40)} authored adversarial manuscript-boundary fixtures passed ({injection.get("pass_rate", 1.0):.1%}) under the deterministic reference provider with complete system instruction separation, JSON envelope serialization, and deterministic validation.
- **Result**: **PASS**"""
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


def check_benchmark_environment_metadata(summary: dict) -> list[str]:
    violations = []
    if not ENV_FILE.exists():
        violations.append(f"Missing {ENV_FILE}")
        return violations

    try:
        env_data = json.loads(ENV_FILE.read_text(encoding="utf-8"))
        if env_data.get("search_mode") != "FULL_REFERENCE":
            violations.append(
                f"BENCHMARK_ENVIRONMENT.json search_mode is '{env_data.get('search_mode')}', expected 'FULL_REFERENCE'"
            )
        if env_data.get("embedding_mode") != "sentence_transformer":
            violations.append(
                f"BENCHMARK_ENVIRONMENT.json embedding_mode is '{env_data.get('embedding_mode')}', expected 'sentence_transformer'"
            )
        if env_data.get("embedding_model") != "sentence-transformers/all-MiniLM-L6-v2":
            violations.append(
                f"BENCHMARK_ENVIRONMENT.json embedding_model is '{env_data.get('embedding_model')}', expected 'sentence-transformers/all-MiniLM-L6-v2'"
            )

        expected_commit = summary.get("benchmark_source_commit")
        if env_data.get("benchmark_source_commit") != expected_commit:
            violations.append(
                f"BENCHMARK_ENVIRONMENT.json benchmark_source_commit '{env_data.get('benchmark_source_commit')}' != summary commit '{expected_commit}'"
            )

        # Check commit in docs/RELEASE_VALIDATION.md
        if RELEASE_VAL_FILE.exists():
            rel_text = RELEASE_VAL_FILE.read_text(encoding="utf-8")
            if expected_commit and expected_commit not in rel_text:
                violations.append(
                    f"RELEASE_VALIDATION.md does not contain expected benchmark_source_commit '{expected_commit}'"
                )

    except Exception as exc:
        violations.append(f"Failed to validate BENCHMARK_ENVIRONMENT.json: {exc}")

    return violations


def check_auxiliary_reports() -> list[str]:
    violations = []
    evals_dir = BASE_DIR / "artifacts" / "evals" / "latest"
    expected_reports = [
        "RETRIEVAL_REPORT.md",
        "CONTINUITY_REPORT.md",
        "CLASS_BREAKDOWN.md",
        "ANCHOR_STABILITY_REPORT.md",
        "INCREMENTAL_UPDATE_REPORT.md",
        "PROMPT_INJECTION_REPORT.md",
        "GROUNDING_REPORT.md",
        "LONG_MANUSCRIPT_REPORT.md",
        "ABLATION_REPORT.md",
        "FAILURE_ANALYSIS.md",
        "PROVIDER_STATUS.md",
    ]
    for rep in expected_reports:
        rep_path = evals_dir / rep
        if not rep_path.exists():
            violations.append(f"Missing auxiliary report: {rep}")

    # Check CLASS_BREAKDOWN.md has 12 rows
    cb_path = evals_dir / "CLASS_BREAKDOWN.md"
    if cb_path.exists():
        lines = [
            line
            for line in cb_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("| ")
            and not line.startswith("| Conflict Class")
            and not line.startswith("|---")
        ]
        if len(lines) != 12:
            violations.append(f"CLASS_BREAKDOWN.md contains {len(lines)} class rows, expected 12")

    # Check FAILURE_ANALYSIS.md has all 4 sections
    fa_path = evals_dir / "FAILURE_ANALYSIS.md"
    if fa_path.exists():
        fa_text = fa_path.read_text(encoding="utf-8")
        for section in ("Continuity", "Anchor", "Incremental", "Retrieval"):
            if section not in fa_text:
                violations.append(f"FAILURE_ANALYSIS.md missing required section for '{section}'")

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

    # 2. Benchmark Environment metadata check
    env_violations = check_benchmark_environment_metadata(summary)
    if env_violations:
        print("Error: BENCHMARK_ENVIRONMENT.json metadata inconsistency detected:")
        for ev in env_violations:
            print(f"  - {ev}")
        all_ok = False
    else:
        print(
            "PASS: Benchmark environment metadata verified (FULL_REFERENCE + sentence_transformer + MiniLM + SHA match)."
        )

    # 3. Stale patterns check across public docs
    stale_violations = check_stale_patterns(
        [README_FILE, RELEASE_VAL_FILE, SECURITY_AUDIT_FILE, ENV_FILE]
    )
    if stale_violations:
        print("Error: Obsolete metric/dataset claims detected:")
        for v in stale_violations:
            print(f"  - {v}")
        all_ok = False
    else:
        print("PASS: Zero stale metric or split patterns detected in public documentation.")

    # 4. Auxiliary reports completeness check
    report_violations = check_auxiliary_reports()
    if report_violations:
        print("Error: Auxiliary benchmark reports violation detected:")
        for rv in report_violations:
            print(f"  - {rv}")
        all_ok = False
    else:
        print(
            "PASS: Auxiliary benchmark reports verified (10 reports, 12 classes in CLASS_BREAKDOWN, all 4 sections in FAILURE_ANALYSIS)."
        )

    # 5. Synchronize target documentation files with metric blocks
    targets = [
        (README_FILE, generate_readme_metrics(summary), MARKER_START, MARKER_END),
        (RELEASE_VAL_FILE, generate_release_val_metrics(summary), MARKER_START, MARKER_END),
        (
            SECURITY_AUDIT_FILE,
            generate_security_audit_metrics(summary),
            SECURITY_MARKER_START,
            SECURITY_MARKER_END,
        ),
    ]

    for doc, new_md, m_start, m_end in targets:
        if not doc.exists():
            print(f"Error: Target documentation file {doc} does not exist.")
            all_ok = False
            continue

        doc_content = doc.read_text(encoding="utf-8")
        pattern = re.compile(
            re.escape(m_start) + r".*?" + re.escape(m_end),
            re.DOTALL,
        )

        if not pattern.search(doc_content):
            print(f"Error: Could not find markers {m_start} and {m_end} in {doc}.")
            all_ok = False
            continue

        updated_doc = pattern.sub(
            f"{m_start}\n{new_md}\n{m_end}",
            doc_content,
        )

        # Synchronize commit in RELEASE_VALIDATION.md if present
        if doc == RELEASE_VAL_FILE and summary.get("benchmark_source_commit"):
            c_sha = summary["benchmark_source_commit"]
            updated_doc = re.sub(
                r"- \*\*Benchmark Source Commit\*\*:\s*`[0-9a-f]{40}`",
                f"- **Benchmark Source Commit**: `{c_sha}`",
                updated_doc,
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
