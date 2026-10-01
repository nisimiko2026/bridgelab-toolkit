"""Registry and explicit lookup for BridgeLab capability providers.

The registry is deliberately passive: it records providers and exposes them by
capability or explicit provider id.  It does not rank, vote, call, or silently
fall back between providers.  Selection policy belongs to a caller that has
explicitly chosen how evidence should be gathered for a task.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capability_providers import (
    BiddingAdviser,
    Capability,
    DealEvaluator,
    DoubleDummyProvider,
    OpeningLeadAdviser,
    PlayAdviser,
    ProviderDescriptor,
)


_PROTOCOLS = {
    Capability.BIDDING: BiddingAdviser,
    Capability.OPENING_LEAD: OpeningLeadAdviser,
    Capability.PLAY: PlayAdviser,
    Capability.DOUBLE_DUMMY: DoubleDummyProvider,
    Capability.DEAL_EVALUATION: DealEvaluator,
}


@dataclass(frozen=True, slots=True)
class RegisteredProvider:
    descriptor: ProviderDescriptor
    registration_order: int
    provider: object


class CapabilityProviderRegistry:
    """Deterministic catalogue of providers, without preference semantics."""

    def __init__(self, providers=()) -> None:
        self._items: list[RegisteredProvider] = []
        self._by_key: dict[tuple[Capability, str], RegisteredProvider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: object) -> RegisteredProvider:
        descriptor = getattr(provider, "descriptor", None)
        if not isinstance(descriptor, ProviderDescriptor):
            raise TypeError("provider must expose a ProviderDescriptor as descriptor")

        protocol = _PROTOCOLS[descriptor.capability]
        if not isinstance(provider, protocol):
            raise TypeError(
                f"provider {descriptor.provider_id!r} does not satisfy "
                f"{descriptor.capability.value} capability contract"
            )

        key = (descriptor.capability, descriptor.provider_id.casefold())
        if key in self._by_key:
            raise ValueError(
                f"duplicate provider_id for {descriptor.capability.value}: "
                f"{descriptor.provider_id}"
            )

        item = RegisteredProvider(descriptor, len(self._items), provider)
        self._items.append(item)
        self._by_key[key] = item
        return item

    @property
    def registrations(self) -> tuple[RegisteredProvider, ...]:
        return tuple(self._items)

    def providers_for(self, capability: Capability) -> tuple[object, ...]:
        if not isinstance(capability, Capability):
            raise TypeError("capability must be Capability")
        return tuple(
            item.provider for item in self._items
            if item.descriptor.capability is capability
        )

    def descriptors_for(self, capability: Capability) -> tuple[ProviderDescriptor, ...]:
        if not isinstance(capability, Capability):
            raise TypeError("capability must be Capability")
        return tuple(
            item.descriptor for item in self._items
            if item.descriptor.capability is capability
        )

    def get(self, capability: Capability, provider_id: str) -> object | None:
        if not isinstance(capability, Capability):
            raise TypeError("capability must be Capability")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id must be a non-blank string")
        item = self._by_key.get((capability, provider_id.strip().casefold()))
        return None if item is None else item.provider

    def require(self, capability: Capability, provider_id: str) -> object:
        provider = self.get(capability, provider_id)
        if provider is None:
            raise KeyError((capability.value, provider_id.strip()))
        return provider
