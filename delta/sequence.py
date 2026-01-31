"""Immutable token sequence utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from .types import Token


@dataclass(frozen=True)
class TokenSequence(Sequence[Token]):
    _tokens: tuple[Token, ...]

    @classmethod
    def from_iterable(cls, items: Iterable[Token]) -> "TokenSequence":
        return cls(tuple(items))

    def __len__(self) -> int:
        return len(self._tokens)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return TokenSequence(self._tokens[item])
        return self._tokens[item]

    def __iter__(self) -> Iterator[Token]:
        return iter(self._tokens)

    def to_tuple(self) -> tuple[Token, ...]:
        return self._tokens
