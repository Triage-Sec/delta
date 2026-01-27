# Final Notes and Guidance

## Preserve Correctness

- Favor correctness over compression gains.
- Fail loudly on invalid inputs or inconsistent dictionaries.
- Avoid silent data corruption at all costs.

## Measure Everything

- Metrics are mandatory during development and tuning.
- Compare compression quality across domains rather than relying on intuition.

## Document Assumptions

Current assumptions:

- Token sequences are moderate in length (<= 100K typical).
- Vocabulary size is bounded (<= 200K typical).
- Exact matches dominate over near-duplicate matches in most corpora.

Revisit these if workloads change.

## Prioritize Testability

- Keep functions pure where possible.
- Avoid hidden global state.
- Accept external dependencies (tokenizers, corpora) via explicit adapters.

## Build for Extension

- Pattern discovery and selection are modular stages.
- New discovery modes and dictionary formats should plug in with minimal refactoring.
- Configuration validation should be updated with new features.
