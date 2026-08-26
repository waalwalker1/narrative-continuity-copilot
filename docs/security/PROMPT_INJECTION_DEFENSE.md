# Manuscript Prompt-Injection Defense Architecture

## Untrusted Data Invariant
In creative writing systems, manuscript prose is inherently untrusted. A manuscript might contain:
- Characters saying `"Ignore previous instructions"`.
- Dialogue discussing system prompts, AI commands, or markdown injection.
- Deliberate XML or JSON syntax inside fiction manuscripts.

## Defense Boundaries
1. **Typed Envelope Serialization**: Manuscript passages are transmitted strictly inside typed JSON payloads, never interpolated directly into system instructions.
2. **System Prompt Role Isolation**: System instructions and task constraints are passed strictly through provider system roles.
3. **Deterministic Output Validation**: Post-inference validators reject any alert containing unknown anchor IDs, unsupported claims, or unapproved canon mutations.
4. **Zero-Trust Author Action Gate**: Creative prose cannot trigger state changes or apply author decisions. All decisions require explicit user interaction with the application API.
