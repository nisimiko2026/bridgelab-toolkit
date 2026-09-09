"""Exact, formula-neutral probability values."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import total_ordering
from math import gcd


@total_ordering
@dataclass(frozen=True, slots=True)
class ProbabilityValue:
    """A canonical exact probability in the closed interval [0, 1]."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.numerator, int)
            or isinstance(self.numerator, bool)
            or not isinstance(self.denominator, int)
            or isinstance(self.denominator, bool)
        ):
            raise TypeError("probability numerator and denominator must be integers")
        if self.denominator <= 0:
            raise ValueError("probability denominator must be positive")
        if self.numerator < 0 or self.numerator > self.denominator:
            raise ValueError("probability must be in the closed interval [0, 1]")
        divisor = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // divisor)
        object.__setattr__(self, "denominator", self.denominator // divisor)

    @classmethod
    def from_fraction(cls, numerator: int, denominator: int) -> ProbabilityValue:
        """Construct from exact integer fraction components."""

        return cls(numerator, denominator)

    @classmethod
    def from_canonical_dict(cls, payload: dict[str, int]) -> ProbabilityValue:
        """Reconstruct from the exact two-integer serialization contract."""

        if not isinstance(payload, dict) or set(payload) != {"numerator", "denominator"}:
            raise ValueError("probability payload requires numerator and denominator only")
        return cls(payload["numerator"], payload["denominator"])

    def as_fraction(self) -> Fraction:
        """Return the exact standard-library rational representation."""

        return Fraction(self.numerator, self.denominator)

    def complement(self) -> ProbabilityValue:
        """Return the exact complementary probability."""

        return ProbabilityValue(self.denominator - self.numerator, self.denominator)

    @property
    def is_zero(self) -> bool:
        return self.numerator == 0

    @property
    def is_one(self) -> bool:
        return self.numerator == self.denominator

    def to_canonical_dict(self) -> dict[str, int]:
        """Serialize without floating-point or display-policy conversion."""

        return {"numerator": self.numerator, "denominator": self.denominator}

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ProbabilityValue):
            return NotImplemented
        return self.numerator * other.denominator < other.numerator * self.denominator
