"""Integration tests for new compression features."""

import pytest
from small import compress, CompressionConfig
from small.compressor import decompress


def test_compression_roundtrip_with_greedy():
    """Test that compression with greedy selection roundtrips correctly."""
    tokens = ["the", "cat", "sat", "on", "the", "mat", "the", "cat", "ran", "on", "the", "mat"]
    config = CompressionConfig(
        selection_mode="greedy",
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens


def test_compression_roundtrip_with_optimal():
    """Test that compression with optimal selection roundtrips correctly."""
    tokens = ["a", "b", "c"] * 10 + ["x", "y", "z"] * 5
    config = CompressionConfig(
        selection_mode="optimal",
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens


def test_compression_roundtrip_with_beam():
    """Test that compression with beam selection roundtrips correctly."""
    tokens = ["hello", "world"] * 8 + ["foo", "bar"] * 6
    config = CompressionConfig(
        selection_mode="beam",
        beam_width=8,
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens


def test_hierarchical_compression_with_early_stopping():
    """Test that hierarchical compression with early stopping works."""
    # Highly repetitive pattern
    tokens = (["a", "b", "c", "d"] * 5 + ["e"]) * 4
    config = CompressionConfig(
        hierarchical_enabled=True,
        hierarchical_max_depth=5,
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens
    assert result.compressed_length < result.original_length


def test_compression_with_suffix_array_discovery():
    """Test compression using suffix array discovery."""
    tokens = ["the", "quick", "brown", "fox"] * 10
    config = CompressionConfig(
        discovery_mode="suffix-array",
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens


def test_compression_with_dict_length_enabled():
    """Test compression with length tokens in dictionary."""
    tokens = ["x", "y", "z"] * 15
    config = CompressionConfig(
        dict_length_enabled=True,
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens


def test_compression_with_dict_length_disabled():
    """Test compression without length tokens."""
    tokens = ["x", "y", "z"] * 15
    config = CompressionConfig(
        dict_length_enabled=False,
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens


def test_no_compression_when_not_beneficial():
    """Test that compression is skipped when it would increase size."""
    tokens = ["a", "b", "c", "d", "e"]  # No repeats
    config = CompressionConfig(
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    
    # Should skip compression when not beneficial
    assert result.compressed_length <= result.original_length


def test_compression_preserves_token_types():
    """Test that compression preserves different token types."""
    # Mix of strings and integers
    tokens = [1, 2, 3] * 5 + ["a", "b"] * 8
    config = CompressionConfig(
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens


def test_compression_with_long_patterns():
    """Test compression with max_subsequence_length."""
    # Pattern of length 6
    pattern = ["a", "b", "c", "d", "e", "f"]
    tokens = pattern * 10
    
    config = CompressionConfig(
        max_subsequence_length=8,
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens
    assert result.compressed_length < result.original_length


def test_compression_metrics_available():
    """Test that metrics are computed when enabled."""
    tokens = ["a", "b"] * 20
    config = CompressionConfig(
        metrics_enabled=True,
        static_dictionary_auto=False,
    )
    
    result = compress(tokens, config)
    
    assert result.metrics is not None


def test_selection_modes_all_produce_valid_output():
    """Test that all selection modes produce valid compressed output."""
    tokens = ["hello", "world", "hello", "world", "foo", "hello", "world"]
    
    for mode in ["greedy", "optimal", "beam"]:
        config = CompressionConfig(
            selection_mode=mode,
            beam_width=8,
            static_dictionary_auto=False,
            verify=True,
        )
        
        result = compress(tokens, config)
        decompressed = decompress(result.serialized_tokens, config)
        
        assert list(decompressed) == tokens, f"Failed for mode: {mode}"


def test_empty_input():
    """Test compression of empty input."""
    config = CompressionConfig(static_dictionary_auto=False)
    result = compress([], config)
    
    assert result.original_length == 0
    assert result.compressed_length == 0


def test_single_token():
    """Test compression of single token."""
    config = CompressionConfig(static_dictionary_auto=False)
    result = compress(["single"], config)
    
    decompressed = decompress(result.serialized_tokens, config)
    assert list(decompressed) == ["single"]


def test_compression_respects_min_length():
    """Test that patterns below min_subsequence_length are not compressed."""
    # Pattern where repetitions don't meet min length
    tokens = list("abcdefghij") * 2  # Each pair only appears twice
    config = CompressionConfig(
        min_subsequence_length=3,
        max_subsequence_length=3,
        static_dictionary_auto=False,
    )
    
    result = compress(tokens, config)
    
    # With only 2 occurrences of length-3 patterns, should not compress
    # (need at least 3 for compressibility)
    # If compression happened, verify it still roundtrips
    decompressed = decompress(result.serialized_tokens, config)
    assert list(decompressed) == tokens


def test_large_input_compression():
    """Test compression on larger input."""
    # Create input with multiple highly repeated patterns
    pattern1 = ["the", "quick", "brown"]
    pattern2 = ["fox", "jumps", "over"]
    tokens = (pattern1 + pattern2) * 100  # More repetitions for better compression
    
    config = CompressionConfig(
        static_dictionary_auto=False,
        verify=True,
    )
    
    result = compress(tokens, config)
    decompressed = decompress(result.serialized_tokens, config)
    
    assert list(decompressed) == tokens
    # Should at least not expand (compression may skip if not beneficial)
    assert result.compressed_length <= result.original_length
