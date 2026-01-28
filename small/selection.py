"""Pattern selection strategies."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .config import CompressionConfig
from .types import Candidate, Occurrence
from .utils import is_compressible


@dataclass(frozen=True)
class SelectionResult:
    selected: list[Occurrence]


def _min_count_for_compressibility(length: int, extra_cost: int) -> int:
    """Compute minimum occurrence count required for a pattern to be compressible.
    
    Compressibility condition: length * count > 1 + length + count + extra_cost
    Solving for count: count > (1 + length + extra_cost) / (length - 1)
    """
    if length <= 1:
        return 1_000_000_000  # Effectively infinite
    return math.ceil((2 + length + extra_cost) / (length - 1))


def _compute_savings(length: int, count: int, extra_cost: int) -> int:
    """Compute net token savings for a pattern with given length and occurrence count."""
    if count == 0:
        return 0
    # Original tokens: length * count
    # Compressed: 1 (meta-token entry) + length (definition) + count (references) + extra_cost
    original = length * count
    compressed = 1 + length + count + extra_cost
    return max(0, original - compressed)


def _compute_marginal_savings(length: int, current_count: int, extra_cost: int) -> float:
    """Compute marginal savings from adding one more occurrence of a pattern."""
    current_savings = _compute_savings(length, current_count, extra_cost)
    new_savings = _compute_savings(length, current_count + 1, extra_cost)
    return new_savings - current_savings


def _savings_density(occ: Occurrence) -> float:
    """Compute savings-density score for an occurrence.
    
    Higher values indicate better compression value per position consumed.
    """
    if occ.length <= 1:
        return 0.0
    # Savings per token if this occurrence is part of a compressed pattern
    pattern_savings = occ.length - 1  # Replace N tokens with 1 reference
    density = pattern_savings / occ.length
    return density + occ.priority * 0.1


def _build_occurrences(candidates: Iterable[Candidate]) -> list[Occurrence]:
    occurrences: list[Occurrence] = []
    for candidate in candidates:
        for pos in candidate.positions:
            occurrences.append(
                Occurrence(
                    start=pos,
                    length=candidate.length,
                    subsequence=candidate.subsequence,
                    priority=candidate.priority,
                    patches=candidate.patches.get(pos, ()),
                )
            )
    occurrences.sort(key=lambda occ: (occ.start + occ.length, occ.start))
    return occurrences


def _group_by_subsequence(occurrences: list[Occurrence]) -> dict[tuple, list[Occurrence]]:
    grouped: dict[tuple, list[Occurrence]] = {}
    for occ in occurrences:
        grouped.setdefault(occ.subsequence, []).append(occ)
    return grouped


def _non_overlapping_with_compressibility(
    occurrences: list[Occurrence], 
    config: CompressionConfig,
) -> list[Occurrence]:
    """Greedy selection using savings-density, enforcing compressibility during selection."""
    if not occurrences:
        return []
    
    extra_cost = 1 if config.dict_length_enabled else 0
    
    # First pass: group by subsequence to know total available counts
    subseq_available: dict[tuple, int] = {}
    for occ in occurrences:
        subseq_available[occ.subsequence] = subseq_available.get(occ.subsequence, 0) + 1
    
    # Sort by savings-density (highest first), then by start position for stability
    sorted_occs = sorted(
        occurrences, 
        key=lambda o: (-_savings_density(o), o.start, o.length)
    )
    
    selected: list[Occurrence] = []
    occupied: set[int] = set()
    subseq_counts: dict[tuple, int] = {}
    
    for occ in sorted_occs:
        positions = set(range(occ.start, occ.start + occ.length))
        if positions & occupied:
            continue
        
        current_count = subseq_counts.get(occ.subsequence, 0)
        total_available = subseq_available.get(occ.subsequence, 0)
        min_count = _min_count_for_compressibility(occ.length, extra_cost)
        
        # Accept if pattern could potentially become compressible
        # (i.e., there are enough occurrences in total)
        if total_available >= min_count:
            selected.append(occ)
            occupied |= positions
            subseq_counts[occ.subsequence] = current_count + 1
    
    # Post-filter: only keep patterns that achieved compressibility
    final_selected: list[Occurrence] = []
    for occ in selected:
        count = subseq_counts.get(occ.subsequence, 0)
        if is_compressible(occ.length, count, extra_cost=extra_cost):
            final_selected.append(occ)
    
    final_selected.sort(key=lambda occ: occ.start)
    return final_selected


def _weighted_interval_scheduling_with_savings(
    occurrences: list[Occurrence],
    config: CompressionConfig,
) -> list[Occurrence]:
    """Weighted interval scheduling with proper savings calculation accounting for dictionary overhead."""
    if not occurrences:
        return []
    
    extra_cost = 1 if config.dict_length_enabled else 0
    
    # Sort by end position
    occs = sorted(occurrences, key=lambda occ: (occ.start + occ.length, occ.start))
    ends = [occ.start + occ.length for occ in occs]

    # p[i]: last index < i that doesn't overlap
    p: list[int] = []
    for i, occ in enumerate(occs):
        lo = 0
        hi = i - 1
        idx = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if ends[mid] <= occ.start:
                idx = mid
                lo = mid + 1
            else:
                hi = mid - 1
        p.append(idx)

    # First pass: compute weights using raw savings (amortized dictionary cost)
    # We estimate based on expected occurrence count from candidates
    subseq_total_counts: dict[tuple, int] = {}
    for occ in occs:
        subseq_total_counts[occ.subsequence] = subseq_total_counts.get(occ.subsequence, 0) + 1
    
    weights: list[float] = []
    for occ in occs:
        total_count = subseq_total_counts[occ.subsequence]
        length = occ.length
        
        # Amortized dictionary cost per occurrence
        dict_cost_per_occ = (1 + length + extra_cost) / total_count if total_count > 0 else length
        
        # Savings: original tokens - (1 reference + amortized dict cost)
        savings = length - 1 - dict_cost_per_occ
        weight = max(0, savings) + occ.priority * 0.5
        weights.append(weight)
    
    # DP over occurrences
    dp = [0.0] * len(occs)
    choose = [False] * len(occs)
    for i in range(len(occs)):
        take = weights[i] + (dp[p[i]] if p[i] >= 0 else 0)
        skip = dp[i - 1] if i > 0 else 0
        if take > skip:
            dp[i] = take
            choose[i] = True
        else:
            dp[i] = skip
            choose[i] = False

    # Reconstruct
    selected: list[Occurrence] = []
    i = len(occs) - 1
    while i >= 0:
        if choose[i]:
            selected.append(occs[i])
            i = p[i]
        else:
            i -= 1
    selected.reverse()
    
    # Post-filter for compressibility
    grouped = _group_by_subsequence(selected)
    final_selected: list[Occurrence] = []
    for subseq, group_occs in grouped.items():
        if is_compressible(len(subseq), len(group_occs), extra_cost=extra_cost):
            final_selected.extend(group_occs)
    
    final_selected.sort(key=lambda occ: occ.start)
    return final_selected


def _beam_search_with_savings(
    occurrences: list[Occurrence], 
    width: int,
    config: CompressionConfig,
) -> list[Occurrence]:
    """Beam search with proper savings calculation."""
    if not occurrences:
        return []
    
    extra_cost = 1 if config.dict_length_enabled else 0
    occs = sorted(occurrences, key=lambda occ: (occ.start, occ.length))
    
    # State: (score, last_end, selected, subseq_counts)
    initial_counts: dict[tuple, int] = {}
    states: list[tuple[float, int, list[Occurrence], dict[tuple, int]]] = [
        (0.0, -1, [], initial_counts.copy())
    ]
    
    for occ in occs:
        new_states: list[tuple[float, int, list[Occurrence], dict[tuple, int]]] = []
        for score, last_end, selected, subseq_counts in states:
            # Option 1: skip
            new_states.append((score, last_end, selected, subseq_counts))
            
            # Option 2: take (if non-overlapping)
            if occ.start >= last_end:
                current_count = subseq_counts.get(occ.subsequence, 0)
                marginal = _compute_marginal_savings(occ.length, current_count, extra_cost)
                
                new_score = score + marginal + occ.priority * 0.5
                new_selected = selected + [occ]
                new_counts = subseq_counts.copy()
                new_counts[occ.subsequence] = current_count + 1
                
                new_states.append((
                    new_score, 
                    occ.start + occ.length, 
                    new_selected, 
                    new_counts
                ))
        
        # Keep top-k by score
        new_states.sort(key=lambda s: (s[0], -s[1]), reverse=True)
        states = new_states[:max(1, width)]
    
    # Select best state
    states.sort(key=lambda s: s[0], reverse=True)
    best_selected = states[0][2]
    best_counts = states[0][3]
    
    # Filter for compressibility
    final_selected: list[Occurrence] = []
    for occ in best_selected:
        count = best_counts.get(occ.subsequence, 0)
        if is_compressible(occ.length, count, extra_cost=extra_cost):
            final_selected.append(occ)
    
    final_selected.sort(key=lambda occ: occ.start)
    return final_selected


def select_occurrences(candidates: Iterable[Candidate], config: CompressionConfig) -> SelectionResult:
    """Select non-overlapping occurrences for compression.
    
    Selection modes:
    - greedy: Fast selection using savings-density heuristic
    - optimal: Weighted interval scheduling with proper savings
    - beam: Beam search balancing exploration and exploitation
    - ilp: Integer linear programming (requires scipy, see selection_ilp module)
    """
    occurrences = _build_occurrences(candidates)
    
    if config.selection_mode == "greedy":
        selected = _non_overlapping_with_compressibility(occurrences, config)
    elif config.selection_mode == "optimal":
        selected = _weighted_interval_scheduling_with_savings(occurrences, config)
    elif config.selection_mode == "beam":
        selected = _beam_search_with_savings(occurrences, config.beam_width, config)
    elif config.selection_mode == "ilp":
        # Lazy import to avoid scipy dependency for basic usage
        try:
            from .selection_ilp import select_occurrences_ilp
            selected = select_occurrences_ilp(candidates, config)
        except ImportError:
            # Fall back to optimal if scipy not available
            selected = _weighted_interval_scheduling_with_savings(occurrences, config)
    else:
        raise ValueError(f"Unsupported selection mode: {config.selection_mode}")

    return SelectionResult(selected=selected)
