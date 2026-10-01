"""Double-dummy reference evidence for BridgeLab.

Double-dummy results are objective optimal-play reference measurements.
They are not bidding recommendations, natural/adjusted Playing Tricks,
or authority over system, convention, treatment, or partnership policy.
"""
from __future__ import annotations

from dataclasses import dataclass

from .capability_providers import ProviderDescriptor, Capability
from .trick_solver import TrickSolverResult, TrickSolverStatus


@dataclass(frozen=True, slots=True)
class DoubleDummyEvidence:
    """One immutable double-dummy reference observation."""

    provider: ProviderDescriptor
    result: TrickSolverResult
    source_ids: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.provider, ProviderDescriptor):
            raise TypeError("provider must be ProviderDescriptor")
        if self.provider.capability is not Capability.DOUBLE_DUMMY:
            raise ValueError(
                "double-dummy evidence requires a DOUBLE_DUMMY provider"
            )
        if not isinstance(self.result, TrickSolverResult):
            raise TypeError("result must be TrickSolverResult")

        for name in ("source_ids", "notes"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple")
            for value in values:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"{name} entries must be non-blank strings"
                    )

    @property
    def status(self) -> TrickSolverStatus:
        return self.result.status

    @property
    def maximum_declarer_tricks(self) -> int | None:
        return self.result.maximum_declarer_tricks
