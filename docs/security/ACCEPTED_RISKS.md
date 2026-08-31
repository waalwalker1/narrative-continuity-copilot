# Accepted Security Risks & Compensating Controls

This ledger documents evaluated upstream dependency security advisories that cannot currently be remediated by direct package upgrades without introducing breaking changes or incompatible architectural rewrites.

---

## 1. Advisory: GHSA-v3m3-f69x-jf25 (Quill Rich-Text Editor)

| Field | Description / Value |
|---|---|
| **Advisory ID** | `GHSA-v3m3-f69x-jf25` / `CVE-2024-5174` |
| **Package & Installed Version** | `quill@2.0.2` (and `quill@2.0.3`) |
| **Dependency Path** | `package.json` -> `node_modules/quill` |
| **Severity** | High (CVSS 7.5) |
| **Status** | `KNOWN_ACCEPTED_RISK` |
| **Vulnerable Feature** | Cross-site Scripting (XSS) vulnerability during HTML export/clipboard HTML serialization when parsing untrusted SVG or MathML elements. |
| **Exploitability Assessment** | 1. **Zero HTML Serialization / Export Usage**: Narrative Continuity Copilot does not invoke Quill's HTML export feature. Manuscript content is parsed and saved as plain text and structural units via API endpoints (`/api/v1/projects/{id}/revisions`).<br>2. **Plain-Text Content Loading**: The web frontend (`apps/web/src/components/QuillEditor.vue`) loads chapter content using `quill.setText(store.editorContent)` rather than raw HTML sinks (`innerHTML`), ensuring any embedded `<svg>`, `<math>`, or `<script>` tags in creative prose are treated strictly as inert text.<br>3. **Zero Untrusted HTML DOM Sinks**: The Vue frontend contains no `v-html` bindings or `dangerouslySetInnerHTML` assignments on manuscript content. |
| **Compensating Controls** | 1. Plain text loading and extraction via `quill.setText` and `quill.getText` in `apps/web/src/components/QuillEditor.vue`.<br>2. Strict manuscript AST sanitization and typing on ingestion in `src/narrative_copilot/ingestion/importer.py`.<br>3. State management in `apps/web/src/stores/manuscript.ts` maintains plain text chapter block content.<br>4. Automated XSS regression tests in Vitest unit suite (`apps/web/tests/unit/components.spec.ts`) and Playwright E2E suite (`apps/web/tests/e2e/workflow_flows.spec.ts`) verifying that `<script>`, `<svg onload>`, `<math>`, and `<img>` tags in manuscript prose do not execute. |
| **Review Date** | 2026-08-31 |
| **Expiry / Re-review Date** | 2027-02-28 (or upon availability of Quill 2.1.0+ non-breaking release) |

---

## 2. Advisory: GHSA-fx2h-pf6j-xcff (Vite Dev Server Windows Path Denial Bypass)

| Field | Description / Value |
|---|---|
| **Advisory ID** | `GHSA-fx2h-pf6j-xcff` |
| **Package & Installed Version** | `vite@5.4.21` (devDependency) |
| **Dependency Path** | `package.json` -> `devDependencies.vite` |
| **Severity** | High (CVSS 7.5) |
| **Status** | `KNOWN_ACCEPTED_RISK` |
| **Vulnerable Feature** | `server.fs.deny` bypass on Windows filesystems using 8.3 short names or alternate data streams in Vite development server. |
| **Exploitability Assessment** | 1. **Dev-Only Tooling**: Vite is strictly a development and build-time bundler; it is never run as an Internet-facing production server.<br>2. **Non-Windows Production Deployments**: Production runs Docker Linux containers with static build outputs (`dist/`) served via static file servers.<br>3. **No Sensitive Local Files**: The Vite root is scoped strictly to `apps/web/` without access to host system credentials. |
| **Compensating Controls** | 1. Multi-stage container build generates static assets via `vite build` without running the dev server.<br>2. Development and CI environments execute in controlled, single-tenant sandboxes. |
| **Review Date** | 2026-08-31 |
| **Expiry / Re-review Date** | 2027-02-28 (or next major Vite 6 bundler upgrade) |

---

## 3. Security Gate Policy

The automated CI security audit script (`scripts/npm_audit_gate.py`) permits only the explicitly reviewed advisory IDs above. If any new high, critical, or unreviewed vulnerability is detected, the security gate fails closed immediately.
