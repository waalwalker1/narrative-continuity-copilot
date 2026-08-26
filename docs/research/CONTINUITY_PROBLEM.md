# Narrative Continuity and Story Memory in Long-Form Fiction

## The Engineering Problem
Writing a novel (60,000 to 120,000 words) presents fundamental cognitive challenges for authors. Human working memory cannot simultaneously retain thousands of micro-assertions introduced across hundreds of scenes written over months or years.

Common continuity failures in fiction include:
1. **Attribute Drift**: Eye color, age, handedness, or scars shifting between early and late chapters.
2. **Timeline Inversion**: Events referenced before they occur or travel times that violate spatial constraints.
3. **Object State Incoherence**: Destroyed or lost heirlooms reappearing without explanation.
4. **Epistemic Leaks**: Characters acting on secret information they have not yet learned.
5. **World-Rule Contradictions**: Breaking established magic systems or speculative technology rules.

## Why Naive RAG Fails
Standard Retrieval-Augmented Generation (RAG) treats long documents as generic text chunks. In creative fiction:
- Thematic similarity leads to false retrievals (e.g. retrieving every sword fight when looking for a specific wound).
- Aliases, honorifics, and nicknames (e.g. "Elizabeth", "Lizzy", "Miss Bennet", "Mrs. Darcy") scatter entity assertions.
- Point-of-view (POV) beliefs, rumors, lies, and dream visions appear as factual statements in the text but do not constitute physical canon.

## The Hybrid Memory + Evidence Solution
Narrative Continuity Copilot addresses these challenges by:
1. **Structured Story Memory**: Versioned entities, typed predicates, narrative scopes, and epistemic statuses.
2. **Stable Block Provenance**: Binding assertions to immutable block hashes rather than brittle character offsets.
3. **Elasticsearch Hybrid RRF**: Fusing BM25 lexical precision with dense semantic embeddings.
4. **Author Canon Authority**: Ensuring the AI remains an evidence-backed reviewer rather than an autonomous decision-maker.
