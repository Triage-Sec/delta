"""Tests for adaptive region-aware compression."""

import pytest
from small.adaptive import (
    RegionType,
    Region,
    detect_regions,
    detect_regions_heuristic,
    filter_candidates_by_region,
    get_region_stats,
    DEFAULT_MARKERS,
)
from small.types import Candidate


def _make_candidate(subseq: tuple, positions: tuple[int, ...], priority: int = 0) -> Candidate:
    return Candidate(
        subsequence=subseq,
        length=len(subseq),
        positions=positions,
        priority=priority,
    )


def test_detect_regions_system_marker():
    tokens = ["[SYSTEM]", "You", "are", "helpful", "[USER]", "Hello"]
    regions = detect_regions(tokens)
    
    assert len(regions) >= 2
    
    # Find system region
    system_regions = [r for r in regions if r.region_type == RegionType.SYSTEM]
    assert len(system_regions) >= 1
    
    # Find user region
    user_regions = [r for r in regions if r.region_type == RegionType.USER]
    assert len(user_regions) >= 1


def test_detect_regions_code_fence():
    tokens = ["text", "before", "```", "code", "here", "```", "text", "after"]
    regions = detect_regions(tokens)
    
    code_regions = [r for r in regions if r.region_type == RegionType.CODE]
    assert len(code_regions) >= 1


def test_detect_regions_empty():
    regions = detect_regions([])
    assert regions == []


def test_detect_regions_no_markers():
    tokens = ["hello", "world", "test"]
    regions = detect_regions(tokens)
    
    # Should have at least one region (unknown type)
    assert len(regions) >= 1


def test_detect_regions_custom_markers():
    tokens = ["<<START>>", "content", "<<END>>"]
    custom_markers = {"<<START>>": RegionType.SYSTEM, "<<END>>": RegionType.USER}
    
    regions = detect_regions(tokens, custom_markers)
    
    # Should detect custom markers
    assert len(regions) >= 1


def test_detect_regions_heuristic():
    tokens = list(range(100))
    regions = detect_regions_heuristic(tokens, system_fraction=0.2)
    
    # Should have system and user regions
    assert len(regions) == 2
    
    system_region = regions[0]
    assert system_region.region_type == RegionType.SYSTEM
    assert system_region.end == 20  # 20% of 100


def test_filter_candidates_by_region_system():
    tokens = ["[SYSTEM]", "important", "stuff", "[USER]", "hello", "world", "test"]
    regions = detect_regions(tokens)
    
    candidates = [
        _make_candidate(("hello", "world"), (4, 5)),  # In user region
        _make_candidate(("important", "stuff"), (1, 2)),  # In system region
    ]
    
    filtered = filter_candidates_by_region(candidates, regions, tokens)
    
    # Candidates in system region should have lower priority (negative boost)
    system_cand = next(c for c in filtered if c.subsequence == ("important", "stuff"))
    user_cand = next(c for c in filtered if c.subsequence == ("hello", "world"))
    
    # System region has priority_boost of -2, user has 0
    assert system_cand.priority < user_cand.priority


def test_filter_candidates_by_region_empty():
    assert filter_candidates_by_region([], [], []) == []


def test_region_max_compression_ratio():
    # System regions should have high max_compression_ratio (minimal compression)
    system_region = Region(
        start=0,
        end=10,
        region_type=RegionType.SYSTEM,
        max_compression_ratio=0.95,
        priority_boost=-2,
    )
    assert system_region.max_compression_ratio > 0.9
    
    # Context regions should allow more compression
    context_region = Region(
        start=10,
        end=20,
        region_type=RegionType.CONTEXT,
        max_compression_ratio=0.5,
        priority_boost=3,
    )
    assert context_region.max_compression_ratio < 0.6


def test_get_region_stats():
    tokens = ["a"] * 100
    regions = [
        Region(0, 30, RegionType.SYSTEM, 0.95, -2),
        Region(30, 100, RegionType.USER, 0.85, 0),
    ]
    
    stats = get_region_stats(regions, tokens)
    
    assert stats["system"] == 30
    assert stats["user"] == 70


def test_region_type_enum():
    assert RegionType.SYSTEM.value == "system"
    assert RegionType.USER.value == "user"
    assert RegionType.CONTEXT.value == "context"
    assert RegionType.CODE.value == "code"
    assert RegionType.DATA.value == "data"


def test_default_markers_present():
    assert "[SYSTEM]" in DEFAULT_MARKERS
    assert "[USER]" in DEFAULT_MARKERS
    assert "```" in DEFAULT_MARKERS
