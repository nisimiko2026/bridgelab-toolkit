"""Bidding-adviser registry view for BridgeLab.

A7.2 — Adviser Registry.

This is a capability-specific view over CapabilityProviderRegistry. It keeps
bidding adviser discovery explicit and deterministic without introducing
ranking, voting, fallback, or provider-specific hard-coding.
"""
from __future__ import annotations

from dataclasses import dataclass

from .capability_providers import BiddingAdviser, Capability, ProviderDescriptor
from .capability_registry import CapabilityProviderRegistry, RegisteredProvider


@dataclass(frozen=True, slots=True)
class RegisteredBiddingAdviser:
    descriptor: ProviderDescriptor
    registration_order: int
    adviser: BiddingAdviser

    def __post_init__(self) -> None:
        if not isinstance(self.descriptor, ProviderDescriptor):
            raise TypeError("descriptor must be ProviderDescriptor")
        if self.descriptor.capability is not Capability.BIDDING:
            raise ValueError("registered bidding adviser requires BIDDING capability")
        if not isinstance(self.registration_order, int) or isinstance(
            self.registration_order, bool
        ):
            raise TypeError("registration_order must be an integer")
        if self.registration_order < 0:
            raise ValueError("registration_order cannot be negative")
        if not isinstance(self.adviser, BiddingAdviser):
            raise TypeError("adviser must satisfy BiddingAdviser")


class BiddingAdviserRegistry:
    """Passive bidding-only view over the shared capability registry."""

    def __init__(self, registry: CapabilityProviderRegistry | None = None) -> None:
        if registry is None:
            registry = CapabilityProviderRegistry()
        if not isinstance(registry, CapabilityProviderRegistry):
            raise TypeError("registry must be CapabilityProviderRegistry")
        self._registry = registry

    @property
    def capability_registry(self) -> CapabilityProviderRegistry:
        return self._registry

    def register(self, adviser: BiddingAdviser) -> RegisteredBiddingAdviser:
        item = self._registry.register(adviser)
        return _as_bidding_registration(item)

    @property
    def registrations(self) -> tuple[RegisteredBiddingAdviser, ...]:
        return tuple(
            _as_bidding_registration(item)
            for item in self._registry.registrations
            if item.descriptor.capability is Capability.BIDDING
        )

    @property
    def advisers(self) -> tuple[BiddingAdviser, ...]:
        return tuple(item.adviser for item in self.registrations)

    @property
    def descriptors(self) -> tuple[ProviderDescriptor, ...]:
        return tuple(item.descriptor for item in self.registrations)

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(item.descriptor.provider_id for item in self.registrations)

    def get(self, provider_id: str) -> BiddingAdviser | None:
        provider = self._registry.get(Capability.BIDDING, provider_id)
        if provider is None:
            return None
        if not isinstance(provider, BiddingAdviser):
            raise TypeError(
                f"registered bidding provider {provider_id!r} does not satisfy "
                "BiddingAdviser"
            )
        return provider

    def require(self, provider_id: str) -> BiddingAdviser:
        adviser = self.get(provider_id)
        if adviser is None:
            if not isinstance(provider_id, str) or not provider_id.strip():
                # Preserve the shared registry's validation semantics.
                self._registry.require(Capability.BIDDING, provider_id)
            raise KeyError((Capability.BIDDING.value, provider_id.strip()))
        return adviser

    def descriptor(self, provider_id: str) -> ProviderDescriptor | None:
        adviser = self.get(provider_id)
        return None if adviser is None else adviser.descriptor

    def contains(self, provider_id: str) -> bool:
        return self.get(provider_id) is not None


def _as_bidding_registration(item: RegisteredProvider) -> RegisteredBiddingAdviser:
    if not isinstance(item, RegisteredProvider):
        raise TypeError("item must be RegisteredProvider")
    if item.descriptor.capability is not Capability.BIDDING:
        raise ValueError("registration is not a bidding adviser")
    if not isinstance(item.provider, BiddingAdviser):
        raise TypeError("registered provider does not satisfy BiddingAdviser")
    return RegisteredBiddingAdviser(
        descriptor=item.descriptor,
        registration_order=item.registration_order,
        adviser=item.provider,
    )
