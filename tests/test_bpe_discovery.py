"""Tests for BPE-style pattern discovery."""

import pytest
from small.bpe_discovery import (
    _count_adjacent_pairs,
    _find_pair_positions,
    _compute_merge_savings,
    discover_bpe_candidates,
    discover_extended_bpe_candidates,
)
from small.config import CompressionConfig


def test_count_adjacent_pairs():
    tokens = ["a", "b", "a", "b", "c", "a", "b"]
    counts = _count_adjacent_pairs(tokens)
    assert counts[("a", "b")] == 3
    assert counts[("b", "a")] == 1
    assert counts[("b", "c")] == 1
    assert counts[("c", "a")] == 1


def test_count_adjacent_pairs_empty():
    counts = _count_adjacent_pairs([])
    assert len(counts) == 0


def test_count_adjacent_pairs_single():
    counts = _count_adjacent_pairs(["a"])
    assert len(counts) == 0


def test_find_pair_positions():
    tokens = ["a", "b", "a", "b", "c", "a", "b"]
    positions = _find_pair_positions(tokens, ("a", "b"))
    # Non-overlapping: positions 0, 2, 5
    assert positions == [0, 2, 5]


def test_find_pair_positions_overlapping():
    tokens = ["a", "a", "a", "a"]
    positions = _find_pair_positions(tokens, ("a", "a"))
    # Non-overlapping: positions 0, 2
    assert positions == [0, 2]


def test_compute_merge_savings():
    # Pattern of length 2, appearing 5 times
    # Original: 2 * 5 = 10 tokens
    # Compressed: 1 + 2 + 5 + 0 = 8 tokens (no extra_cost)
    # Savings: 10 - 8 = 2
    assert _compute_merge_savings(2, 5, 0) == 2
    
    # With extra_cost = 1
    # Compressed: 1 + 2 + 5 + 1 = 9 tokens
    # Savings: 10 - 9 = 1
    assert _compute_merge_savings(2, 5, 1) == 1


def test_discover_bpe_candidates_basic():
    tokens = ["a", "b"] * 10 + ["c", "d"] * 5
    config = CompressionConfig(
        dict_length_enabled=False,
        static_dictionary_auto=False,
    )
    candidates = discover_bpe_candidates(tokens, config)
    
    # Should find ("a", "b") as a compressible pattern
    assert len(candidates) > 0
    ab_cands = [c for c in candidates if c.subsequence == ("a", "b")]
    assert len(ab_cands) > 0


def test_discover_bpe_candidates_empty():
    config = CompressionConfig(static_dictionary_auto=False)
    candidates = discover_bpe_candidates([], config)
    assert candidates == []


def test_discover_bpe_candidates_no_repeats():
    tokens = ["a", "b", "c", "d", "e"]
    config = CompressionConfig(static_dictionary_auto=False)
    candidates = discover_bpe_candidates(tokens, config)
    # No pair appears enough times to be compressible
    assert candidates == []


def test_discover_extended_bpe_candidates():
    tokens = ["a", "b", "c"] * 10
    config = CompressionConfig(
        dict_length_enabled=False,
        static_dictionary_auto=False,
        max_subsequence_length=8,
    )
    candidates = discover_extended_bpe_candidates(tokens, config)
    
    # Should find patterns, potentially extended beyond pairs
    assert len(candidates) > 0


def test_bpe_candidates_have_priority_bonus():
    tokens = ["a", "b"] * 10
    config = CompressionConfig(
        dict_length_enabled=False,
        static_dictionary_auto=False,
    )
    candidates = discover_bpe_candidates(tokens, config)
    
    # BPE candidates should have priority = 1
    for cand in candidates:
        assert cand.priority >= 1
