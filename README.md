# Small

**Lossless Token Sequence Compression for Large Language Models**

Small is a research-grade lossless compression system that reduces the computational and economic cost of LLM inference by eliminating redundancy in input sequences before they reach the model. It replaces repeated multi-token patterns with compact meta-token references backed by a learnable dictionary format, achieving substantial compression on structured inputs while guaranteeing perfect reconstruction.

## Motivation

As context augmentation techniques become standard practice—retrieval-augmented generation, tool schemas, code repositories, policy documents, multi-turn conversations—input sequences increasingly contain repeated subsequences that consume context window budget and quadratic attention compute without contributing new information. Small addresses this by compressing these redundant patterns at the token level.

## Key Features

- **Lossless Compression**: Perfect round-trip reconstruction guaranteed
- **Model-Agnostic**: Operates on token sequences from any tokenizer
- **Learnable Format**: Dictionary format designed for transformer fine-tuning
- **Multiple Discovery Strategies**: Suffix array, BPE-style, AST-aware (Python)
- **Optimal Selection**: Greedy, weighted interval scheduling, beam search, or ILP
- **ML Integration**: Importance scoring, region-aware compression, quality prediction
- **Production Ready**: Comprehensive test suite, type hints, structured logging

## Installation

```bash
# Basic installation
pip install small

# From source
git clone https://github.com/triage-sec/small.git
cd small
pip install -e .

# With optional dependencies
pip install -e ".[analysis]"      # ML analysis tools
pip install -e ".[training]"      # Fine-tuning utilities
pip install -e ".[all]"           # Everything
```

## Quick Start

```python
from small import compress, decompress, CompressionConfig

# Compress a token sequence
tokens = ["the", "quick", "brown", "fox"] * 20
config = CompressionConfig(verify=True)
result = compress(tokens, config)

print(f"Original: {result.original_length} tokens")
print(f"Compressed: {result.compressed_length} tokens")
print(f"Ratio: {result.compressed_length / result.original_length:.1%}")

# Decompress (lossless)
restored = decompress(result.serialized_tokens, config)
assert restored == tokens
```

## How It Works

Small identifies repeated token subsequences and replaces them with meta-tokens, storing the mapping in a prefix dictionary:

```
Original:  [the, cat, sat, on, the, mat, the, cat, ran]
                ^^^^^^^^            ^^^^^^^^
Compressed: [<Dict>, <MT_0>, <Len:2>, the, cat, </Dict>, <MT_0>, sat, on, the, mat, <MT_0>, ran]
```

The compression format is designed to be learnable by transformer models with minimal fine-tuning.

### Compressibility Constraint

A pattern is only compressed if it provides net savings:

```
length × count > 1 + length + count + overhead
```

This ensures compression never increases sequence length.

## Configuration

```python
from small import CompressionConfig

config = CompressionConfig(
    # Pattern discovery
    min_subsequence_length=2,
    max_subsequence_length=8,
    discovery_mode="suffix-array",  # or "sliding-window", "bpe"
    
    # Selection algorithm
    selection_mode="greedy",        # or "optimal", "beam", "ilp"
    beam_width=8,
    
    # Hierarchical compression
    hierarchical_enabled=True,
    hierarchical_max_depth=3,
    
    # ML features (optional)
    use_importance_scoring=False,
    enable_adaptive_regions=False,
    enable_quality_prediction=False,
    
    # Verification
    verify=True,
)
```

## Selection Algorithms

| Mode | Complexity | Description |
|------|------------|-------------|
| `greedy` | O(n log n) | Fast, savings-density heuristic |
| `optimal` | O(n²) | Weighted interval scheduling |
| `beam` | O(n × width) | Beam search with marginal savings |
| `ilp` | Exponential | Globally optimal (requires scipy) |

## Advanced Features

### BPE-Style Discovery

```python
from small.bpe_discovery import discover_bpe_candidates

# Iterative pair merging for better compression
candidates = discover_bpe_candidates(tokens, config, max_iterations=100)
```

### Pattern Importance Scoring

```python
from small import create_default_scorer, adjust_candidate_priorities

scorer = create_default_scorer()
scores = scorer.score_patterns(tokens, candidates)
adjusted = adjust_candidate_priorities(candidates, scores)
```

### Region-Aware Compression

```python
from small import detect_regions, filter_candidates_by_region, RegionType

# Detect semantic regions
regions = detect_regions(tokens)  # SYSTEM, USER, CONTEXT, CODE, DATA

# Apply per-region compression limits
filtered = filter_candidates_by_region(candidates, regions, tokens)
```

### Quality Prediction

```python
from small import create_predictor

predictor = create_predictor(task_type="code")
prediction = predictor.predict(tokens, result)

if prediction.recommendation == "compress":
    # Safe to use compressed output
    pass
```

### Python AST-Aware Compression

```python
from small import compress_python_source

source = '''
def foo():
    return bar()

def baz():
    return bar()
'''

tokens, result = compress_python_source(source)
```

## Benchmarks

```bash
# Compression ratio benchmark
python benchmarks/ratio.py --tokens 8192 --runs 10

# Latency benchmark
python benchmarks/latency.py --tokens 8192 --runs 10

# Compare subsequence lengths
python benchmarks/length_compare.py --tokens 8192 --lengths 2,3,4,5,6
```

## Architecture

```
small/
├── compressor.py          # Core compress/decompress API
├── config.py              # Configuration dataclass
├── engine.py              # Compression pipeline orchestration
├── discovery.py           # Sliding window discovery
├── discovery_sa.py        # Suffix array discovery
├── bpe_discovery.py       # BPE-style iterative discovery
├── selection.py           # Pattern selection algorithms
├── selection_ilp.py       # ILP-based optimal selection
├── subsumption.py         # Cross-pattern analysis
├── pattern_importance.py  # ML importance scoring
├── adaptive.py            # Region-aware compression
├── quality_predictor.py   # Compression quality prediction
├── suffix_array.py        # Suffix array construction
├── suffix_array_fast.py   # NumPy-accelerated suffix array
└── ...
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=small --cov-report=html

# Run specific test modules
pytest tests/test_compress.py -v
```

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Design Intent](docs/00-intent.md) - Motivation and objectives
- [Compression Format](docs/02-format.md) - Dictionary and body format
- [Architecture](docs/06-architecture.md) - System design
- [Algorithm Details](docs/ALGORITHMS.md) - Discovery and selection algorithms
- [ML Integration](docs/ML_INTEGRATION.md) - Importance scoring and quality prediction
- [API Reference](docs/API.md) - Complete API documentation

## Citation

If you use Small in your research, please cite:

```bibtex
@software{small2024,
  title={Small: Lossless Token Sequence Compression for Large Language Models},
  author={Triage-Sec},
  year={2026},
  url={https://github.com/triage-sec/small}
}
```

This work builds on:

```bibtex
@article{harvill2024lossless,
  title={Lossless Token Sequence Compression via Meta-Tokens},
  author={Harvill, John and others},
  year={2024}
}
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome. Please ensure:

1. All tests pass (`pytest`)
2. Code is formatted (`ruff format`)
3. Type hints are complete (`mypy small/`)
4. New features include tests

## Acknowledgments

- The foundational LTSC algorithm from Harvill et al.
- The open-source community for feedback and contributions
