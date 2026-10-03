"""A7.2 bidding-adviser registry tests."""

import pytest

from bridge.bidding_adviser_registry import (
    BiddingAdviserRegistry,
    RegisteredBiddingAdviser,
)
from bridge.capability_providers import (
    Capability,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.capability_registry import CapabilityProviderRegistry
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)


class StubTransport:
    def __init__(self, recommendation="1S"):
        self.recommendation = recommendation

    def observe(self, context):
        return ExternalBiddingObservation(
            status=ProviderStatus.SUCCESS,
            recommendation=self.recommendation,
        )


def _adviser(provider_id, recommendation="1S"):
    return ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.BIDDING,
            implementation=f"{provider_id}-test",
            version="test",
        ),
        transport=StubTransport(recommendation),
    )


def test_empty_registry_has_no_advisers():
    registry = BiddingAdviserRegistry()

    assert registry.registrations == ()
    assert registry.advisers == ()
    assert registry.descriptors == ()
    assert registry.provider_ids == ()


def test_register_returns_bidding_specific_registration():
    registry = BiddingAdviserRegistry()
    ben = _adviser("ben")

    item = registry.register(ben)

    assert isinstance(item, RegisteredBiddingAdviser)
    assert item.descriptor is ben.descriptor
    assert item.adviser is ben
    assert item.registration_order == 0


def test_multiple_advisers_preserve_registration_order():
    registry = BiddingAdviserRegistry()
    ben = _adviser("ben")
    brl = _adviser("brl")

    registry.register(ben)
    registry.register(brl)

    assert registry.provider_ids == ("ben", "brl")
    assert registry.advisers == (ben, brl)
    assert tuple(x.registration_order for x in registry.registrations) == (0, 1)


def test_get_and_require_are_case_insensitive():
    registry = BiddingAdviserRegistry()
    ben = _adviser("ben")
    registry.register(ben)

    assert registry.get("BEN") is ben
    assert registry.require("BeN") is ben


def test_contains_is_case_insensitive():
    registry = BiddingAdviserRegistry()
    registry.register(_adviser("ben"))

    assert registry.contains("BEN")
    assert not registry.contains("missing")


def test_descriptor_lookup_returns_registered_descriptor():
    registry = BiddingAdviserRegistry()
    ben = _adviser("ben")
    registry.register(ben)

    assert registry.descriptor("BEN") is ben.descriptor
    assert registry.descriptor("missing") is None


def test_missing_get_returns_none():
    registry = BiddingAdviserRegistry()

    assert registry.get("missing") is None


def test_missing_require_raises_key_error():
    registry = BiddingAdviserRegistry()

    with pytest.raises(KeyError):
        registry.require("missing")


@pytest.mark.parametrize("provider_id", ("", " "))
def test_blank_provider_id_preserves_shared_registry_validation(provider_id):
    registry = BiddingAdviserRegistry()

    with pytest.raises(ValueError):
        registry.get(provider_id)
    with pytest.raises(ValueError):
        registry.require(provider_id)
    with pytest.raises(ValueError):
        registry.contains(provider_id)
    with pytest.raises(ValueError):
        registry.descriptor(provider_id)


def test_wraps_existing_capability_registry_without_copying():
    shared = CapabilityProviderRegistry()
    ben = _adviser("ben")
    shared.register(ben)

    registry = BiddingAdviserRegistry(shared)

    assert registry.capability_registry is shared
    assert registry.require("ben") is ben


def test_registration_through_view_updates_shared_registry():
    shared = CapabilityProviderRegistry()
    registry = BiddingAdviserRegistry(shared)
    ben = _adviser("ben")

    registry.register(ben)

    assert shared.require(Capability.BIDDING, "ben") is ben


def test_later_shared_registration_is_visible_through_view():
    shared = CapabilityProviderRegistry()
    registry = BiddingAdviserRegistry(shared)
    brl = _adviser("brl")

    shared.register(brl)

    assert registry.require("brl") is brl
    assert registry.provider_ids == ("brl",)


def test_duplicate_provider_id_rejected_by_shared_registry():
    registry = BiddingAdviserRegistry()
    registry.register(_adviser("ben"))

    with pytest.raises(ValueError, match="duplicate provider_id"):
        registry.register(_adviser("BEN"))


def test_registry_is_not_hard_coded_to_ben():
    registry = BiddingAdviserRegistry()
    names = ("ben", "brl", "future-ai")

    for name in names:
        registry.register(_adviser(name))

    assert registry.provider_ids == names


def test_non_bidding_provider_registration_is_rejected_by_shared_contract():
    class FakeNonBiddingProvider:
        descriptor = ProviderDescriptor(
            provider_id="dds",
            capability=Capability.DOUBLE_DUMMY,
            implementation="fake-dds",
        )

    registry = BiddingAdviserRegistry()

    with pytest.raises(TypeError):
        registry.register(FakeNonBiddingProvider())


def test_surface_has_no_ranking_voting_or_fallback_semantics():
    registry = BiddingAdviserRegistry()

    for name in (
        "winner",
        "best",
        "rank",
        "ranking",
        "vote",
        "votes",
        "selected",
        "preferred",
        "fallback",
        "default",
    ):
        assert not hasattr(registry, name)
