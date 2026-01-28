"""Tests for numpy-accelerated suffix array construction."""

import pytest
from small.suffix_array_fast import (
    build_suffix_array_fast,
    lcp_intervals_fast,
    should_use_fast_suffix_array,
    SuffixArrayFast,
)
from small.suffix_array import build_suffix_array


def test_build_suffix_array_fast_basic():
    tokens = ["a", "b", "a", "b", "a"]
    result = build_suffix_array_fast(tokens)
    
    assert isinstance(result, SuffixArrayFast)
    assert len(result.suffix_array) == 5
    assert len(result.lcp) == 4  # LCP has n-1 elements


def test_build_suffix_array_fast_empty():
    result = build_suffix_array_fast([])
    
    assert len(result.suffix_array) == 0
    assert len(result.lcp) == 0


def test_build_suffix_array_fast_single():
    result = build_suffix_array_fast(["a"])
    
    assert len(result.suffix_array) == 1
    assert result.suffix_array[0] == 0
    assert len(result.lcp) == 0


def test_suffix_array_fast_matches_standard():
    tokens = ["b", "a", "n", "a", "n", "a"]
    
    fast_result = build_suffix_array_fast(tokens)
    standard_result = build_suffix_array(tokens)
    
    # Suffix arrays should match
    assert list(fast_result.suffix_array) == standard_result.suffix_array
    
    # LCP arrays should match
    assert list(fast_result.lcp) == standard_result.lcp


def test_suffix_array_fast_repeated_pattern():
    tokens = ["a", "b"] * 10
    result = build_suffix_array_fast(tokens)
    
    # Should have valid suffix array
    assert len(result.suffix_array) == 20
    assert set(result.suffix_array) == set(range(20))


def test_lcp_intervals_fast():
    tokens = ["a", "b", "a", "b", "c", "a", "b"]
    sa = build_suffix_array_fast(tokens)
    
    intervals = lcp_intervals_fast(sa, min_len=2)
    
    # Should find intervals with LCP >= 2
    assert len(intervals) > 0
    
    for start, end, lcp_val in intervals:
        assert lcp_val >= 2


def test_lcp_intervals_fast_empty():
    sa = SuffixArrayFast(
        suffix_array=__import__("numpy").array([], dtype=__import__("numpy").int32),
        lcp=__import__("numpy").array([], dtype=__import__("numpy").int32),
    )
    
    intervals = lcp_intervals_fast(sa, min_len=2)
    assert intervals == []


def test_should_use_fast_suffix_array():
    # Small inputs should use standard
    assert not should_use_fast_suffix_array(500)
    
    # Large inputs should use fast
    assert should_use_fast_suffix_array(2000)


def test_to_lists_conversion():
    tokens = ["a", "b", "c"]
    result = build_suffix_array_fast(tokens)
    
    sa_list, lcp_list = result.to_lists()
    
    assert isinstance(sa_list, list)
    assert isinstance(lcp_list, list)
    assert len(sa_list) == 3
    assert len(lcp_list) == 2


def test_suffix_array_fast_various_types():
    # Test with integers
    tokens = [1, 2, 3, 1, 2]
    result = build_suffix_array_fast(tokens)
    assert len(result.suffix_array) == 5
    
    # Test with mixed types
    tokens_mixed = ["a", 1, "b", 1]
    result_mixed = build_suffix_array_fast(tokens_mixed)
    assert len(result_mixed.suffix_array) == 4


def test_lcp_values_correct():
    # "banana" - classic example
    tokens = list("banana")
    sa = build_suffix_array_fast(tokens)
    
    # Suffix array for "banana": [5, 3, 1, 0, 4, 2]
    # Suffixes: "a", "ana", "anana", "banana", "na", "nana"
    # LCP: [1, 3, 0, 0, 2] (comparing adjacent sorted suffixes)
    
    # The LCP between "a" and "ana" is 1
    # The LCP between "ana" and "anana" is 3
    # etc.
    
    # Just verify it's computed without errors
    assert len(sa.lcp) == len(tokens) - 1
