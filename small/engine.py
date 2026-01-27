"""Compression engine pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import warnings

from .config import CompressionConfig
from .dictionary import build_body_tokens
from .discovery import discover_candidates
from .discovery_sa import discover_candidates_sa
from .fuzzy import discover_fuzzy_candidates
from .swap import perform_swaps
from .types import Candidate, Token, TokenSeq
from .validation import validate_config


@dataclass(frozen=True)
class DiscoveryStage:
    name: str

    def discover(self, tokens: TokenSeq, config: CompressionConfig) -> list[Candidate]:
        raise NotImplementedError


@dataclass(frozen=True)
class ExactDiscoveryStage(DiscoveryStage):
    use_suffix_array: bool = True

    def discover(self, tokens: TokenSeq, config: CompressionConfig) -> list[Candidate]:
        if self.use_suffix_array:
            return discover_candidates_sa(tokens, config)
        return discover_candidates(tokens, config.max_subsequence_length, config)


@dataclass(frozen=True)
class FuzzyDiscoveryStage(DiscoveryStage):
    def discover(self, tokens: TokenSeq, config: CompressionConfig) -> list[Candidate]:
        return discover_fuzzy_candidates(tokens, config)


@dataclass(frozen=True)
class CompressionEngine:
    discovery_stages: tuple[DiscoveryStage, ...]

    def compress_tokens(self, tokens: TokenSeq, config: CompressionConfig) -> tuple[list[Token], dict[Token, tuple[Token, ...]]]:
        for warning in validate_config(config):
            warnings.warn(warning.message, RuntimeWarning)
        working_tokens = list(tokens)
        dictionary_map: dict[Token, tuple[Token, ...]] = {}
        depth_limit = config.hierarchical_max_depth if config.hierarchical_enabled else 1

        for _ in range(depth_limit):
            candidates: list[Candidate] = []
            for stage in self.discovery_stages:
                candidates.extend(stage.discover(working_tokens, config))
            if not candidates:
                break
            swap_result = perform_swaps(working_tokens, candidates, config)
            if not swap_result.dictionary_map:
                break
            dictionary_map.update(swap_result.dictionary_map)
            working_tokens = build_body_tokens(working_tokens, swap_result.replacements, config)
            if not config.hierarchical_enabled:
                break

        return working_tokens, dictionary_map


def default_engine(config: CompressionConfig) -> CompressionEngine:
    stages: list[DiscoveryStage] = [ExactDiscoveryStage(name="exact-sa", use_suffix_array=True)]
    if config.fuzzy_enabled:
        stages.insert(0, FuzzyDiscoveryStage(name="fuzzy"))
    return CompressionEngine(tuple(stages))
