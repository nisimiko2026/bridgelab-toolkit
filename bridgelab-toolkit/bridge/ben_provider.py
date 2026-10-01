"""Composition helpers for the BEN external bidding adviser.

This module wires the BEN-specific transport into BridgeLab's provider-neutral
external adviser and capability registry contracts.

Registration is explicit.  Nothing here selects BEN automatically, ranks it
against another adviser, or promotes BEN output to BridgeLab policy.
"""

from __future__ import annotations

from .ben_bidding_transport import BenBiddingTransport, BenTransportConfig
from .capability_providers import Capability, ProviderDescriptor
from .capability_registry import CapabilityProviderRegistry, RegisteredProvider
from .external_bidding_adviser import ExternalBiddingAdviserAdapter


BEN_PROVIDER_ID = "ben"
BEN_IMPLEMENTATION = "ben-rest"


def create_ben_bidding_adviser(
    *,
    config: BenTransportConfig | None = None,
    version: str | None = None,
) -> ExternalBiddingAdviserAdapter:
    """Create an unregistered BEN bidding adviser."""

    if config is None:
        config = BenTransportConfig()
    elif not isinstance(config, BenTransportConfig):
        raise TypeError("config must be BenTransportConfig or None")

    descriptor = ProviderDescriptor(
        provider_id=BEN_PROVIDER_ID,
        capability=Capability.BIDDING,
        implementation=BEN_IMPLEMENTATION,
        version=version,
    )

    return ExternalBiddingAdviserAdapter(
        descriptor=descriptor,
        transport=BenBiddingTransport(config),
    )


def register_ben_bidding_adviser(
    registry: CapabilityProviderRegistry,
    *,
    config: BenTransportConfig | None = None,
    version: str | None = None,
) -> RegisteredProvider:
    """Create and explicitly register BEN as a bidding provider."""

    if not isinstance(registry, CapabilityProviderRegistry):
        raise TypeError(
            "registry must be CapabilityProviderRegistry"
        )

    adviser = create_ben_bidding_adviser(
        config=config,
        version=version,
    )

    return registry.register(adviser)
