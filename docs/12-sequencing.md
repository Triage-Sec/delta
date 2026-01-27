# Implementation Sequencing

## Phase One: Core Baseline

Implemented:

- Immutable token sequences
- Suffix array + LCP (doubling algorithm)
- Exact discovery and greedy selection
- Token replacement + dictionary construction
- Decompression + verification

Relevant modules:

- `small/sequence.py`
- `small/suffix_array.py`
- `small/discovery_sa.py`
- `small/selection.py`
- `small/compressor.py`

## Phase Two: Selection Optimization

Implemented:

- Weighted interval scheduling (optimal)
- Beam search

Relevant modules:

- `small/selection.py`
- `small/config.py`

## Phase Three: Hierarchical Compression

Implemented:

- Multi-pass compression
- Length tokens for hierarchical parsing
- Topological dictionary ordering
- Recursive expansion

Relevant modules:

- `small/compressor.py`
- `small/dictionary.py`
- `small/config.py`

## Phase Four: Grammar-Aware Compression

Implemented (Python):

- AST parsing and subtree hashing
- AST-derived candidate discovery
- Priority integration into selection

Relevant modules:

- `small/ast_python.py`
- `small/compressor.py`

## Phase Five: Domain Dictionaries

Implemented:

- Static dictionary registry and auto-detection
- Static marker format
- Apply static dictionary before dynamic compression
- Training utilities support

Relevant modules:

- `small/static_dicts.py`
- `small/domain.py`
- `small/compressor.py`
- `small/training.py`

## Phase Six: Fuzzy Matching

Implemented (minimal):

- Near-duplicate grouping with signatures + Hamming distance
- Canonical selection + patch encoding
- Lossless reconstruction

Relevant modules:

- `small/fuzzy.py`
- `small/dictionary.py`
- `small/compressor.py`
