import random

from small import CompressionConfig, compress, decompress
from small.discovery import discover_candidates
from small.selection import select_occurrences


def test_round_trip_random_strings():
    rng = random.Random(7)
    cfg = CompressionConfig(
        verify=False,
        static_dictionary_auto=False,
        fuzzy_enabled=False,
    )
    vocab = ["a", "b", "c", "d", "e"]
    for _ in range(50):
        length = rng.randint(0, 60)
        tokens = [rng.choice(vocab) for _ in range(length)]
        result = compress(tokens, cfg)
        restored = decompress(result.serialized_tokens, cfg)
        assert restored == tokens
        assert result.compressed_length <= result.original_length


def test_round_trip_random_ints():
    rng = random.Random(11)
    cfg = CompressionConfig(
        verify=False,
        static_dictionary_auto=False,
        fuzzy_enabled=False,
    )
    vocab = list(range(8))
    for _ in range(40):
        length = rng.randint(0, 50)
        tokens = [rng.choice(vocab) for _ in range(length)]
        result = compress(tokens, cfg)
        restored = decompress(result.serialized_tokens, cfg)
        assert restored == tokens
        assert result.compressed_length <= result.original_length


def test_dictionary_consistency():
    tokens = ["a", "b", "a", "b", "a", "b", "a", "b"]
    cfg = CompressionConfig(static_dictionary_auto=False)
    result = compress(tokens, cfg)
    if result.dictionary_map:
        for token in result.body_tokens:
            if isinstance(token, str) and token.startswith(cfg.meta_token_prefix):
                assert token in result.dictionary_map
        for meta in result.dictionary_map:
            assert result.body_tokens.count(meta) > 0


def test_occurrence_validity():
    rng = random.Random(23)
    cfg = CompressionConfig(static_dictionary_auto=False)
    vocab = ["x", "y", "z", "w"]
    for _ in range(20):
        length = rng.randint(5, 40)
        tokens = [rng.choice(vocab) for _ in range(length)]
        candidates = discover_candidates(tokens, cfg.max_subsequence_length, cfg)
        selection = select_occurrences(candidates, cfg)
        occupied = [False] * len(tokens)
        for occ in selection.selected:
            assert 0 <= occ.start < len(tokens)
            assert occ.start + occ.length <= len(tokens)
            assert not any(occupied[occ.start : occ.start + occ.length])
            for i in range(occ.start, occ.start + occ.length):
                occupied[i] = True


def test_edge_sequences():
    cfg = CompressionConfig(static_dictionary_auto=False)
    cases = [
        [],
        ["a"],
        ["a", "b"],
        ["a"] * 20,
        ["a", "b", "c", "d", "e"] * 5,
    ]
    for tokens in cases:
        result = compress(tokens, cfg)
        restored = decompress(result.serialized_tokens, cfg)
        assert restored == tokens
        assert result.compressed_length <= result.original_length
