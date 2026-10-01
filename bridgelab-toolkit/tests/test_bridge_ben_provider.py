"""A3.3 composition and registration of the BEN bidding adviser."""

import pytest

from bridge.ben_bidding_transport import (
    BenBiddingTransport,
    BenTransportConfig,
)
from bridge.ben_provider import (
    BEN_IMPLEMENTATION,
    BEN_PROVIDER_ID,
    create_ben_bidding_adviser,
    register_ben_bidding_adviser,
)
from bridge.capability_providers import (
    BiddingAdviser,
    Capability,
)
from bridge.capability_registry import CapabilityProviderRegistry
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
)


def test_create_ben_adviser_uses_bidding_descriptor():
    adviser = create_ben_bidding_adviser(version="test-version")

    assert isinstance(adviser, ExternalBiddingAdviserAdapter)
    assert isinstance(adviser, BiddingAdviser)

    assert adviser.descriptor.provider_id == BEN_PROVIDER_ID
    assert adviser.descriptor.capability is Capability.BIDDING
    assert adviser.descriptor.implementation == BEN_IMPLEMENTATION
    assert adviser.descriptor.version == "test-version"


def test_create_ben_adviser_uses_ben_transport():
    adviser = create_ben_bidding_adviser()

    assert isinstance(adviser._transport, BenBiddingTransport)


def test_custom_config_is_preserved_by_transport():
    config = BenTransportConfig(
        base_url="http://ben.example:9999/",
        timeout_seconds=3.5,
        details=False,
        tournament="imps",
    )

    adviser = create_ben_bidding_adviser(config=config)

    assert adviser._transport.config is config
    assert adviser._transport.config.base_url == "http://ben.example:9999"
    assert adviser._transport.config.timeout_seconds == 3.5
    assert adviser._transport.config.details is False
    assert adviser._transport.config.tournament == "imps"


def test_invalid_config_is_rejected():
    with pytest.raises(TypeError, match="BenTransportConfig"):
        create_ben_bidding_adviser(config="not-config")


def test_registration_is_explicit():
    registry = CapabilityProviderRegistry()

    adviser = create_ben_bidding_adviser()

    assert registry.registrations == ()
    assert registry.get(Capability.BIDDING, BEN_PROVIDER_ID) is None
    assert isinstance(adviser, BiddingAdviser)


def test_register_ben_adds_one_bidding_provider():
    registry = CapabilityProviderRegistry()

    item = register_ben_bidding_adviser(
        registry,
        version="test-version",
    )

    assert len(registry.registrations) == 1
    assert item.registration_order == 0
    assert item.descriptor.provider_id == BEN_PROVIDER_ID
    assert item.descriptor.capability is Capability.BIDDING
    assert item.descriptor.version == "test-version"

    assert registry.require(
        Capability.BIDDING,
        BEN_PROVIDER_ID,
    ) is item.provider


def test_registered_ben_is_visible_only_as_bidding_capability():
    registry = CapabilityProviderRegistry()

    register_ben_bidding_adviser(registry)

    assert len(registry.providers_for(Capability.BIDDING)) == 1
    assert registry.providers_for(Capability.OPENING_LEAD) == ()
    assert registry.providers_for(Capability.PLAY) == ()
    assert registry.providers_for(Capability.DOUBLE_DUMMY) == ()
    assert registry.providers_for(Capability.DEAL_EVALUATION) == ()


def test_duplicate_ben_registration_is_rejected_by_registry():
    registry = CapabilityProviderRegistry()

    register_ben_bidding_adviser(registry)

    with pytest.raises(ValueError, match="duplicate provider_id"):
        register_ben_bidding_adviser(registry)


def test_registration_does_not_invoke_ben():
    registry = CapabilityProviderRegistry()

    item = register_ben_bidding_adviser(registry)

    assert item.provider is registry.require(
        Capability.BIDDING,
        BEN_PROVIDER_ID,
    )


def test_invalid_registry_is_rejected():
    with pytest.raises(
        TypeError,
        match="CapabilityProviderRegistry",
    ):
        register_ben_bidding_adviser(object())
