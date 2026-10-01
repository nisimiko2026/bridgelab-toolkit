"""Explicit composition helpers for BridgeLab capability providers.

Composition wires concrete implementations into the passive provider registry.
It does not select a preferred provider, rank providers, vote, invoke them, or
silently fall back between implementations.
"""
from __future__ import annotations

from .capability_providers import (
    Capability,
    ProviderDescriptor,
)
from .capability_registry import CapabilityProviderRegistry
from .double_dummy_provider import TrickSolverDoubleDummyProvider
from .trick_solver import TrickSolver


def register_trick_solver_provider(
    registry: CapabilityProviderRegistry,
    solver: TrickSolver,
    *,
    provider_id: str,
    implementation: str,
    version: str | None = None,
) -> TrickSolverDoubleDummyProvider:
    """Register one explicitly identified TrickSolver as a DD provider."""

    if not isinstance(registry, CapabilityProviderRegistry):
        raise TypeError("registry must be CapabilityProviderRegistry")

    provider = TrickSolverDoubleDummyProvider(
        solver=solver,
        descriptor=ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.DOUBLE_DUMMY,
            implementation=implementation,
            version=version,
        ),
    )

    registry.register(provider)
    return provider
