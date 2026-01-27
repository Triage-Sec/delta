"""Suffix-array-based discovery for repeated substrings."""

from __future__ import annotations

from collections import defaultdict

from .config import CompressionConfig
from .suffix_array import build_suffix_array, lcp_intervals
from .types import Candidate, TokenSeq
from .utils import is_compressible


def discover_candidates_sa(tokens: TokenSeq, config: CompressionConfig) -> list[Candidate]:
    min_len = config.min_subsequence_length
    max_len = config.max_subsequence_length
    if max_len < min_len:
        return []
    sa = build_suffix_array(tokens)
    extra_cost = 1 if config.dict_length_enabled else 0

    positions_by_subseq: dict[tuple, list[int]] = defaultdict(list)
    intervals = lcp_intervals(sa, min_len)
    for start, end, lcp_len in intervals:
        length_limit = min(lcp_len, max_len)
        for length in range(min_len, length_limit + 1):
            positions = [sa.suffix_array[idx] for idx in range(start, end + 1)]
            positions.sort()
            subseq = tuple(tokens[positions[0] : positions[0] + length])
            positions_by_subseq[subseq].extend(positions)

    candidates: list[Candidate] = []
    for subseq, positions in positions_by_subseq.items():
        positions = sorted(set(positions))
        non_overlapping: list[int] = []
        next_free = -1
        for pos in positions:
            if pos >= next_free:
                non_overlapping.append(pos)
                next_free = pos + len(subseq)
        count = len(non_overlapping)
        if is_compressible(len(subseq), count, extra_cost=extra_cost):
            candidates.append(
                Candidate(
                    subsequence=subseq,
                    length=len(subseq),
                    positions=tuple(non_overlapping),
                    priority=0,
                )
            )

    candidates.sort(key=lambda cand: cand.length, reverse=True)
    return candidates
