"""Tests for pattern subsumption analysis."""

import pytest
from small.subsumption import (
    build_subsumption_graph,
    find_maximal_patterns,
    prune_subsumed_candidates,
    rank_by_independent_value,
    deduplicate_candidates,
)
from small.types import Candidate
from small.config import CompressionConfig


def _make_candidate(subseq: tuple, positions: tuple[int, ...]) -> Candidate:
    return Candidate(
        subsequence=subseq,
        length=len(subseq),
        positions=positions,
        priority=0,
    )


def test_build_subsumption_graph_basic():
    candidates = [
        _make_candidate(("a", "b", "c", "d"), (0, 10)),
        _make_candidate(("a", "b"), (0, 5, 10)),
        _make_candidate(("c", "d"), (2, 12)),
        _make_candidate(("b", "c"), (1, 11)),
    ]
    
    graph = build_subsumption_graph(candidates)
    
    # "abcd" subsumes "ab", "cd", "bc"
    assert 1 in graph.subsumes[0]  # ab
    assert 2 in graph.subsumes[0]  # cd
    assert 3 in graph.subsumes[0]  # bc
    
    # "ab" is subsumed by "abcd"
    assert 0 in graph.subsumed_by[1]


def test_build_subsumption_graph_no_subsumption():
    candidates = [
        _make_candidate(("a", "b"), (0, 5)),
        _make_candidate(("c", "d"), (2, 7)),
    ]
    
    graph = build_subsumption_graph(candidates)
    
    # No subsumption relationships
    assert len(graph.subsumes[0]) == 0
    assert len(graph.subsumes[1]) == 0


def test_find_maximal_patterns():
    candidates = [
        _make_candidate(("a", "b", "c"), (0, 10)),
        _make_candidate(("a", "b"), (0, 5, 10)),
        _make_candidate(("x", "y"), (20, 30)),
    ]
    
    maximal = find_maximal_patterns(candidates)
    
    # "abc" and "xy" are maximal
    assert len(maximal) == 2
    subseqs = {c.subsequence for c in maximal}
    assert ("a", "b", "c") in subseqs
    assert ("x", "y") in subseqs


def test_prune_subsumed_candidates_removes_fully_subsumed():
    # "abc" at positions 0, 10
    # "ab" at positions 0, 10 (fully covered by abc)
    candidates = [
        _make_candidate(("a", "b", "c"), (0, 10)),
        _make_candidate(("a", "b"), (0, 10)),
    ]
    
    config = CompressionConfig(dict_length_enabled=False, static_dictionary_auto=False)
    pruned = prune_subsumed_candidates(candidates, config)
    
    # Only "abc" should remain
    assert len(pruned) == 1
    assert pruned[0].subsequence == ("a", "b", "c")


def test_prune_subsumed_candidates_keeps_independent():
    # "abc" at positions 0, 10
    # "ab" at positions 0, 10, 20, 30, 40 (has independent occurrences at 20, 30, 40)
    # Need at least 4 independent positions for length-2 pattern to be compressible
    candidates = [
        _make_candidate(("a", "b", "c"), (0, 10)),
        _make_candidate(("a", "b"), (0, 10, 20, 30, 40, 50)),  # 4 independent positions
    ]
    
    config = CompressionConfig(dict_length_enabled=False, static_dictionary_auto=False)
    pruned = prune_subsumed_candidates(candidates, config)
    
    # Both should remain, "ab" should have only independent positions
    assert len(pruned) == 2
    
    ab_cand = next(c for c in pruned if c.subsequence == ("a", "b"))
    # 20, 30, 40, 50 are independent (0 and 10 covered by "abc")
    assert 20 in ab_cand.positions
    assert 30 in ab_cand.positions
    assert 40 in ab_cand.positions


def test_rank_by_independent_value():
    candidates = [
        _make_candidate(("a", "b", "c"), (0, 10, 20)),  # Maximal, high value
        _make_candidate(("a", "b"), (0, 10)),  # Subsumed, lower value
    ]
    
    config = CompressionConfig(dict_length_enabled=False, static_dictionary_auto=False)
    ranked = rank_by_independent_value(candidates, config)
    
    # Should return tuples sorted by score
    assert len(ranked) == 2
    # First should be the maximal pattern
    assert ranked[0][0].subsequence == ("a", "b", "c")
    assert ranked[0][1] > ranked[1][1]


def test_deduplicate_candidates_merges_positions():
    candidates = [
        _make_candidate(("a", "b"), (0, 5)),
        _make_candidate(("a", "b"), (10, 15)),
    ]
    
    deduped = deduplicate_candidates(candidates)
    
    # Should merge into one candidate
    assert len(deduped) == 1
    assert set(deduped[0].positions) == {0, 5, 10, 15}


def test_deduplicate_candidates_takes_max_priority():
    candidates = [
        Candidate(subsequence=("a", "b"), length=2, positions=(0,), priority=1),
        Candidate(subsequence=("a", "b"), length=2, positions=(5,), priority=5),
    ]
    
    deduped = deduplicate_candidates(candidates)
    
    assert len(deduped) == 1
    assert deduped[0].priority == 5


def test_deduplicate_candidates_empty():
    assert deduplicate_candidates([]) == []


def test_subsumption_with_overlapping_patterns():
    # Patterns that overlap in different ways
    candidates = [
        _make_candidate(("a", "b", "c", "d", "e"), (0, 20)),
        _make_candidate(("a", "b", "c"), (0, 10, 20)),
        _make_candidate(("c", "d", "e"), (2, 22)),
        _make_candidate(("b", "c", "d"), (1, 21)),
    ]
    
    graph = build_subsumption_graph(candidates)
    
    # The long pattern should subsume all shorter ones
    assert len(graph.subsumes[0]) == 3
