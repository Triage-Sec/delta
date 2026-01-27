# Performance Optimization

## Complexity Targets

- Discovery (suffix array): O(n log n) build + O(n) enumeration
- Selection: greedy O(p log p), optimal O(n log n)
- Replacement: O(n)

Overall target: O(n log n) per compression pass.

## Memory Considerations

- Suffix array and LCP are O(n)
- Chunked discovery can reduce peak memory for large sequences
- Token sequences are stored immutably to avoid extra copies

## Parallelization

- Window-based discovery supports parallel execution across lengths
- Enabled via `parallel_discovery` for large sequences
- Hierarchical passes remain sequential
