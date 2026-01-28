"""Tests for pattern importance scoring."""

import pytest
from small.pattern_importance import (
    PositionalImportanceScorer,
    FrequencyImportanceScorer,
    LengthImportanceScorer,
    CompositeImportanceScorer,
    create_default_scorer,
    adjust_candidate_priorities,
    filter_high_importance_candidates,
)
from small.types import Candidate


def _make_candidate(subseq: tuple, positions: tuple[int, ...], priority: int = 0) -> Candidate:
    return Candidate(
        subsequence=subseq,
        length=len(subseq),
        positions=positions,
        priority=priority,
    )


def test_positional_importance_scorer():
    tokens = list(range(100))
    candidates = [
        _make_candidate(("a", "b"), (5, 10)),    # Early positions
        _make_candidate(("c", "d"), (90, 95)),   # Late positions
    ]
    
    scorer = PositionalImportanceScorer(decay_rate=2.0)
    scores = scorer.score_patterns(tokens, candidates)
    
    # Earlier positions should have higher importance
    assert len(scores) == 2
    assert scores[0] > scores[1]


def test_frequency_importance_scorer():
    tokens = list(range(100))
    candidates = [
        _make_candidate(("a", "b"), (0, 10, 20, 30, 40)),  # High frequency
        _make_candidate(("c", "d"), (50,)),                 # Low frequency
    ]
    
    scorer = FrequencyImportanceScorer()
    scores = scorer.score_patterns(tokens, candidates)
    
    # Rare patterns should have higher importance
    assert len(scores) == 2
    assert scores[1] > scores[0]  # Low frequency = high importance


def test_length_importance_scorer():
    tokens = list(range(100))
    candidates = [
        _make_candidate(("a",) * 8, (0, 20)),  # Long pattern
        _make_candidate(("b", "c"), (10, 30)),  # Short pattern
    ]
    
    scorer = LengthImportanceScorer()
    scores = scorer.score_patterns(tokens, candidates)
    
    # Longer patterns should have higher importance
    assert len(scores) == 2
    assert scores[0] > scores[1]


def test_composite_importance_scorer():
    tokens = list(range(100))
    candidates = [
        _make_candidate(("a", "b", "c"), (5, 15)),
        _make_candidate(("x", "y"), (80, 90)),
    ]
    
    scorer = CompositeImportanceScorer(
        scorers=[
            (PositionalImportanceScorer(), 0.5),
            (LengthImportanceScorer(), 0.5),
        ]
    )
    scores = scorer.score_patterns(tokens, candidates)
    
    assert len(scores) == 2
    # First candidate: early + longer -> higher score
    assert scores[0] > scores[1]


def test_create_default_scorer():
    scorer = create_default_scorer()
    
    tokens = list(range(50))
    candidates = [
        _make_candidate(("a", "b"), (5, 10)),
        _make_candidate(("c", "d"), (40, 45)),
    ]
    
    scores = scorer.score_patterns(tokens, candidates)
    assert len(scores) == 2
    assert all(0 <= s <= 1 for s in scores)


def test_adjust_candidate_priorities():
    candidates = [
        _make_candidate(("a", "b"), (0, 10), priority=0),
        _make_candidate(("c", "d"), (20, 30), priority=0),
    ]
    
    # First candidate high importance (should not boost priority much)
    # Second candidate low importance (should boost priority)
    importance_scores = [0.9, 0.1]
    
    adjusted = adjust_candidate_priorities(candidates, importance_scores, importance_weight=1.0)
    
    assert len(adjusted) == 2
    # Low importance -> higher priority boost
    assert adjusted[1].priority > adjusted[0].priority


def test_adjust_candidate_priorities_weight():
    candidates = [
        _make_candidate(("a", "b"), (0, 10), priority=0),
    ]
    importance_scores = [0.0]  # Low importance
    
    # With weight=1.0, should get full priority adjustment
    adjusted_full = adjust_candidate_priorities(candidates, importance_scores, importance_weight=1.0)
    
    # With weight=0.0, should get no adjustment
    adjusted_none = adjust_candidate_priorities(candidates, importance_scores, importance_weight=0.0)
    
    assert adjusted_full[0].priority > adjusted_none[0].priority


def test_filter_high_importance_candidates():
    candidates = [
        _make_candidate(("a", "b"), (0, 10)),  # High importance - filtered
        _make_candidate(("c", "d"), (20, 30)), # Low importance - kept
    ]
    importance_scores = [0.9, 0.3]
    
    filtered = filter_high_importance_candidates(candidates, importance_scores, threshold=0.8)
    
    assert len(filtered) == 1
    assert filtered[0].subsequence == ("c", "d")


def test_scorer_empty_candidates():
    scorer = PositionalImportanceScorer()
    scores = scorer.score_patterns([], [])
    assert scores == []


def test_scorer_single_occurrence():
    tokens = list(range(100))
    candidates = [
        _make_candidate(("a", "b"), (50,)),  # Single occurrence
    ]
    
    scorer = PositionalImportanceScorer()
    scores = scorer.score_patterns(tokens, candidates)
    
    assert len(scores) == 1
    assert 0 <= scores[0] <= 1
