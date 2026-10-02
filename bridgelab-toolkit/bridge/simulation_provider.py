"""Raw-sample simulation provider boundary for BridgeLab.

A6.12 — Simulation Provider Boundary.

A simulation provider produces individual declarer-trick samples for one
contract context. Raw samples remain available for downstream per-sample
duplicate scoring; the provider boundary does not score averages, compare
alternatives, rank outcomes, or modify bidding policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from typing import Callable, Iterable

from .auction import Contract
from .deals import Deal


class SimulationSampleStatus(str, Enum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SimulationSampleRequest:
    deal: Deal
    contract: Contract
    sample_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.deal, Deal):
            raise TypeError("deal must be Deal")
        if not isinstance(self.contract, Contract):
            raise TypeError("contract must be Contract")
        if (
            not isinstance(self.sample_count, int)
            or isinstance(self.sample_count, bool)
            or self.sample_count < 1
        ):
            raise ValueError("sample_count must be a positive integer")


@dataclass(frozen=True, slots=True)
class SimulationSampleResult:
    provider_id: str
    implementation: str
    version: str | None
    status: SimulationSampleStatus
    contract: Contract
    requested_sample_count: int
    declarer_tricks: tuple[int, ...]
    elapsed_seconds: float
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        object.__setattr__(self, "provider_id", self.provider_id.strip())

        if not isinstance(self.implementation, str) or not self.implementation.strip():
            raise ValueError("implementation must be a non-blank string")
        object.__setattr__(self, "implementation", self.implementation.strip())

        if self.version is not None:
            if not isinstance(self.version, str) or not self.version.strip():
                raise ValueError("version must be None or a non-blank string")
            object.__setattr__(self, "version", self.version.strip())

        if not isinstance(self.status, SimulationSampleStatus):
            raise TypeError("status must be SimulationSampleStatus")
        if not isinstance(self.contract, Contract):
            raise TypeError("contract must be Contract")
        if (
            not isinstance(self.requested_sample_count, int)
            or isinstance(self.requested_sample_count, bool)
            or self.requested_sample_count < 1
        ):
            raise ValueError("requested_sample_count must be a positive integer")
        if not isinstance(self.declarer_tricks, tuple):
            raise TypeError("declarer_tricks must be a tuple")
        if not isinstance(self.elapsed_seconds, (int, float)) or isinstance(
            self.elapsed_seconds, bool
        ) or self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be non-negative")

        if self.status is SimulationSampleStatus.SUCCESS:
            if len(self.declarer_tricks) != self.requested_sample_count:
                raise ValueError(
                    "successful simulation must return exactly requested_sample_count samples"
                )
            if any(
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 13
                for value in self.declarer_tricks
            ):
                raise ValueError(
                    "successful simulation samples must be integer tricks from 0 to 13"
                )
        elif self.declarer_tricks:
            raise ValueError(
                "failed/unavailable simulation result must not contain samples"
            )


SimulationSampleCallable = Callable[
    [Deal, Contract, int],
    Iterable[int],
]


@dataclass(frozen=True, slots=True)
class LiveSimulationProvider:
    """Expose an injected sample-producing simulator through a stable boundary."""

    sample_callable: SimulationSampleCallable | None
    provider_id: str = "simulation"
    implementation: str = "live-simulation"
    version: str | None = None

    def __post_init__(self) -> None:
        if self.sample_callable is not None and not callable(self.sample_callable):
            raise TypeError("sample_callable must be callable or None")
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        object.__setattr__(self, "provider_id", self.provider_id.strip())
        if not isinstance(self.implementation, str) or not self.implementation.strip():
            raise ValueError("implementation must be a non-blank string")
        object.__setattr__(self, "implementation", self.implementation.strip())
        if self.version is not None:
            if not isinstance(self.version, str) or not self.version.strip():
                raise ValueError("version must be None or a non-blank string")
            object.__setattr__(self, "version", self.version.strip())

    def sample(self, request: SimulationSampleRequest) -> SimulationSampleResult:
        if not isinstance(request, SimulationSampleRequest):
            raise TypeError("request must be SimulationSampleRequest")

        if self.sample_callable is None:
            return SimulationSampleResult(
                provider_id=self.provider_id,
                implementation=self.implementation,
                version=self.version,
                status=SimulationSampleStatus.UNAVAILABLE,
                contract=request.contract,
                requested_sample_count=request.sample_count,
                declarer_tricks=(),
                elapsed_seconds=0.0,
                error="simulation implementation is unavailable",
            )

        started = perf_counter()
        try:
            produced = self.sample_callable(
                request.deal,
                request.contract,
                request.sample_count,
            )
            samples = tuple(produced)
        except Exception as exc:
            return SimulationSampleResult(
                provider_id=self.provider_id,
                implementation=self.implementation,
                version=self.version,
                status=SimulationSampleStatus.FAILED,
                contract=request.contract,
                requested_sample_count=request.sample_count,
                declarer_tricks=(),
                elapsed_seconds=perf_counter() - started,
                error=f"{type(exc).__name__}: {exc}",
            )

        elapsed = perf_counter() - started
        if len(samples) != request.sample_count or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 13
            for value in samples
        ):
            return SimulationSampleResult(
                provider_id=self.provider_id,
                implementation=self.implementation,
                version=self.version,
                status=SimulationSampleStatus.FAILED,
                contract=request.contract,
                requested_sample_count=request.sample_count,
                declarer_tricks=(),
                elapsed_seconds=elapsed,
                error="simulation implementation returned invalid samples",
            )

        return SimulationSampleResult(
            provider_id=self.provider_id,
            implementation=self.implementation,
            version=self.version,
            status=SimulationSampleStatus.SUCCESS,
            contract=request.contract,
            requested_sample_count=request.sample_count,
            declarer_tricks=samples,
            elapsed_seconds=elapsed,
            error=None,
        )
