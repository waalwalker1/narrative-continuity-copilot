# Accepted Security Risks & Compensating Controls

This ledger documents evaluated upstream dependency security advisories that cannot currently be remediated by direct package upgrades without introducing breaking changes or incompatible architectural rewrites.

---

## 1. Advisory: GHSA-v3m3-f69x-jf25 (Quill Rich-Text Editor)

| Field | Description / Value |
|---|---|
| **Advisory ID** | `GHSA-v3m3-f69x-jf25` / `CVE-2024-5174` |
| **Package & Installed Version** | `quill@2.0.2` (and `quill@2.0.3`) |
| **Dependency Path** | `package.json` -> `apps/web/package.json` -> `node_modules/quill` |
| **Severity** | High (CVSS 7.5) |
| **Vulnerable Feature** | Cross-site Scripting (XSS) vulnerability during HTML export/clipboard HTML serialization when parsing untrusted SVG or MathML elements. |
| **Proof of Non-Exploitability** | 1. **No HTML Rendering or Export**: Narrative Continuity Copilot uses Quill purely in headless/structured Delta mode. Manuscript data is imported, parsed, and exported via typed AST markdown (`Unit`, `Block`, `Span`) and Quill Delta operations.<br>2. **No Arbitrary HTML Insertion**: User prose is strictly plain text with delta formatting attributes; raw HTML tags (`<svg>`, `<script>`, `<math>`) are not evaluated as live DOM elements.<br>3. **Zero Browser-side InnerHTML**: The web client never calls `dangerouslySetInnerHTML` or `element.innerHTML` on manuscript content. |
| **Compensating Controls** | 1. Strict manuscript AST sanitization and typing on ingestion in `src/narrative_copilot/ingestion/importer.py`.<br>2. Quill delta integrity verification on every save/load cycle in `apps/web/src/stores/editor.ts`.<br>3. Strict Content Security Policy (CSP) headers prohibiting inline scripts and unsafe eval.<br>4. Automated red-team prompt injection and XSS fuzzing in CI security job. |
| **Review Date** | 2026-08-30 |
| **Expiry / Re-review Date** | 2027-02-28 (or upon availability of Quill 2.1.0+ non-breaking release) |

---

## 2. Advisory: GHSA-fx2h-pf6j-xcff (Vite Dev Server Windows Path Denial Bypass)

| Field | Description / Value |
|---|---|
| **Advisory ID** | `GHSA-fx2h-pf6j-xcff` |
| **Package & Installed Version** | `vite@5.4.21` (devDependency) |
| **Dependency Path** | `package.json` -> `devDependencies.vite` |
| **Severity** | High (CVSS 7.5) |
| **Vulnerable Feature** | `server.fs.deny` bypass on Windows filesystems using 8.3 short names or alternate data streams in Vite development server. |
| **Proof of Non-Exploitability** | 1. **Dev-Only Tooling**: Vite is strictly a development and build-time bundler; it is never run as an Internet-facing production server.<br>2. **Non-Windows Production Deployments**: Production runs Docker Linux containers with static build outputs served via Nginx or FastAPI static files.<br>3. **No Sensitive Local Files**: The Vite root is scoped strictly to `apps/web/` without access to host system credentials. |
| **Compensating Controls** | 1. Docker multi-stage build produces static assets (`dist/`) without running Vite dev server in production.<br>2. CI and developer environments execute in controlled, single-tenant sandboxes. |
| **Review Date** | 2026-08-30 |
| **Expiry / Re-review Date** | 2027-02-28 (or next major Vite 6 bundler upgrade) |

---

## 3. Security Gate Policy

The automated CI security audit script (`scripts/npm_audit_gate.py`) permits only the explicitly reviewed advisories above. If any new high, critical, or unreviewed moderate advisory is detected, the security gate fails closed immediately.
