"""Tests for selection algorithm improvements."""

import pytest
from small.selection import (
    _min_count_for_compressibility,
    _compute_savings,
    _compute_marginal_savings,
    _savings_density,
    _non_overlapping_with_compressibility,
    _weighted_interval_scheduling_with_savings,
    _beam_search_with_savings,
    select_occurrences,
)
from small.types import Candidate, Occurrence
from small.config import CompressionConfig


def test_min_count_for_compressibility():
    # For length=2, extra_cost=0:
    # Compressibility: length * count > 1 + length + count + extra_cost
    # 2 * count > 1 + 2 + count + 0
    # count > 3
    # So min_count = 4
    assert _min_count_for_compressibility(2, 0) == 4
    
    # For length=3, extra_cost=0:
    # 3 * count > 1 + 3 + count + 0
    # 2 * count > 4
    # count > 2
    # So min_count = 3
    assert _min_count_for_compressibility(3, 0) == 3
    
    # Length=1 should return huge number (not compressible)
    assert _min_count_for_compressibility(1, 0) >= 1_000_000


def test_compute_savings():
    # length=3, count=5, extra_cost=0
    # Original: 3 * 5 = 15
    # Compressed: 1 + 3 + 5 + 0 = 9
    # Savings: 15 - 9 = 6
    assert _compute_savings(3, 5, 0) == 6
    
    # count=0 should return 0
    assert _compute_savings(3, 0, 0) == 0


def test_compute_marginal_savings():
    # Going from count=2 to count=3 for length=3, extra_cost=0
    # Current: 3*2 - (1+3+2+0) = 6 - 6 = 0
    # New: 3*3 - (1+3+3+0) = 9 - 7 = 2
    # Marginal: 2 - 0 = 2
    assert _compute_marginal_savings(3, 2, 0) == 2


def test_savings_density():
    occ = Occurrence(
        start=0,
        length=4,
        subsequence=("a", "b", "c", "d"),
        priority=0,
    )
    
    # density = (4-1)/4 = 0.75
    density = _savings_density(occ)
    assert 0.7 < density < 0.8
    
    # With priority bonus
    occ_with_priority = Occurrence(
        start=0,
        length=4,
        subsequence=("a", "b", "c", "d"),
        priority=5,
    )
    density_with_priority = _savings_density(occ_with_priority)
    assert density_with_priority > density


def test_non_overlapping_with_compressibility():
    # Create occurrences that need to meet compressibility
    occurrences = [
        Occurrence(start=0, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=5, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=10, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=15, length=3, subsequence=("a", "b", "c"), priority=0),
    ]
    
    config = CompressionConfig(dict_length_enabled=False, static_dictionary_auto=False)
    selected = _non_overlapping_with_compressibility(occurrences, config)
    
    # All should be selected as they're compressible together
    assert len(selected) >= 3  # Minimum for compressibility


def test_selection_rejects_uncompressible_patterns():
    # Pattern that appears only twice (not compressible for length=3)
    occurrences = [
        Occurrence(start=0, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=5, length=3, subsequence=("a", "b", "c"), priority=0),
    ]
    
    config = CompressionConfig(dict_length_enabled=True, static_dictionary_auto=False)
    selected = _non_overlapping_with_compressibility(occurrences, config)
    
    # Should be empty - pattern doesn't meet compressibility
    assert len(selected) == 0


def test_weighted_interval_scheduling_with_savings():
    occurrences = [
        Occurrence(start=0, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=5, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=10, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=2, length=2, subsequence=("x", "y"), priority=0),  # Overlaps with first
    ]
    
    config = CompressionConfig(dict_length_enabled=False, static_dictionary_auto=False)
    selected = _weighted_interval_scheduling_with_savings(occurrences, config)
    
    # Should select non-overlapping set
    for i, occ1 in enumerate(selected):
        for occ2 in selected[i+1:]:
            # Check no overlap
            assert occ1.start + occ1.length <= occ2.start or occ2.start + occ2.length <= occ1.start


def test_beam_search_with_savings():
    occurrences = [
        Occurrence(start=0, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=3, length=3, subsequence=("a", "b", "c"), priority=0),
        Occurrence(start=6, length=3, subsequence=("a", "b", "c"), priority=0),
    ]
    
    config = CompressionConfig(dict_length_enabled=False, static_dictionary_auto=False)
    selected = _beam_search_with_savings(occurrences, 8, config)
    
    # All should be selected (non-overlapping)
    assert len(selected) == 3


def test_select_occurrences_greedy():
    candidates = [
        Candidate(
            subsequence=("a", "b"),
            length=2,
            positions=(0, 5, 10, 15, 20),
            priority=0,
        )
    ]
    
    config = CompressionConfig(
        selection_mode="greedy",
        dict_length_enabled=False,
        static_dictionary_auto=False,
    )
    result = select_occurrences(candidates, config)
    
    # Should select all positions (pattern is compressible)
    assert len(result.selected) == 5


def test_select_occurrences_optimal():
    candidates = [
        Candidate(
            subsequence=("a", "b", "c"),
            length=3,
            positions=(0, 5, 10),
            priority=0,
        )
    ]
    
    config = CompressionConfig(
        selection_mode="optimal",
        dict_length_enabled=False,
        static_dictionary_auto=False,
    )
    result = select_occurrences(candidates, config)
    
    # Should select all positions
    assert len(result.selected) == 3


def test_select_occurrences_beam():
    candidates = [
        Candidate(
            subsequence=("a", "b", "c"),
            length=3,
            positions=(0, 5, 10),
            priority=0,
        )
    ]
    
    config = CompressionConfig(
        selection_mode="beam",
        beam_width=8,
        dict_length_enabled=False,
        static_dictionary_auto=False,
    )
    result = select_occurrences(candidates, config)
    
    assert len(result.selected) == 3


def test_select_occurrences_prefers_longer_patterns():
    # Overlapping candidates: length-4 vs length-2
    candidates = [
        Candidate(
            subsequence=("a", "b", "c", "d"),
            length=4,
            positions=(0, 10, 20),
            priority=0,
        ),
        Candidate(
            subsequence=("a", "b"),
            length=2,
            positions=(0, 5, 10, 15, 20),
            priority=0,
        ),
    ]
    
    config = CompressionConfig(
        selection_mode="greedy",
        dict_length_enabled=False,
        static_dictionary_auto=False,
    )
    result = select_occurrences(candidates, config)
    
    # Should prefer longer pattern due to savings density
    selected_subseqs = {occ.subsequence for occ in result.selected}
    assert ("a", "b", "c", "d") in selected_subseqs


def test_selection_invalid_mode():
    candidates = []
    config = CompressionConfig(selection_mode="invalid_mode", static_dictionary_auto=False)
    
    with pytest.raises(ValueError):
        select_occurrences(candidates, config)
