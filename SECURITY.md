# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security and privacy of authors' creative work very seriously.

If you discover a security vulnerability (such as prompt injection vectors, unauthorized data exfiltration, or citation tampering), please report it responsibly:

1. **Do not** open a public GitHub issue.
2. Email security findings to `security@example.org` (or use GitHub Private Vulnerability Reporting).
3. Include detailed steps to reproduce the issue, sample manuscript text, and observed behavior.

## Core Security Invariants
- **Manuscript Text is Untrusted**: Creative prose can contain adversarial prompt injection sequences (e.g. `Ignore previous instructions`). The system treats all manuscript text as data, isolating it within strict JSON envelopes and enforcing deterministic output validation.
- **Privacy Minimization**: Raw manuscript prose is never stored in telemetry spans, logs, or unencrypted external caches.
- **Provenance Integrity**: Cross-project and cross-revision citation spoofing is strictly prevented by the deterministic validator.
