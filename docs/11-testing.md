# Testing Strategy

## Unit Tests

- Suffix array correctness against naive implementation
- Discovery on known patterns
- Compressibility conditions
- Selection strategies (greedy vs optimal)
- Dictionary serialization round-trip

## Integration Tests

- Code-like and policy-like samples
- Round-trip correctness and compression ratio checks

## Regression Tests

- Fixture-driven corpus with minimum expected ratios
- Failures indicate quality regressions or correctness issues

## Performance Tests

- Latency scaling benchmark across token counts
- Track O(n log n) scaling and enforce 8K < 100ms target where possible
