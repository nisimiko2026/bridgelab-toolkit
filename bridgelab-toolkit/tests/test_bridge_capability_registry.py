import unittest

from bridge.auction import Call
from bridge.capability_providers import Capability, CapabilityResult, ProviderDescriptor, ProviderStatus
from bridge.capability_registry import CapabilityProviderRegistry


class _BidProvider:
    def __init__(self, provider_id):
        self.descriptor = ProviderDescriptor(provider_id, Capability.BIDDING, "fixture")

    def advise(self, context):
        return CapabilityResult(self.descriptor, ProviderStatus.SUCCESS, Call.parse("P"))


class _LeadProvider:
    descriptor = ProviderDescriptor("fixture.lead", Capability.OPENING_LEAD, "fixture")

    def advise(self, state):
        raise AssertionError("registry must not invoke providers")


class _WrongShape:
    descriptor = ProviderDescriptor("wrong", Capability.BIDDING, "fixture")


class CapabilityProviderRegistryTests(unittest.TestCase):
    def test_multiple_providers_for_same_capability_preserve_registration_order(self):
        first, second = _BidProvider("ben.bid"), _BidProvider("brl.bid")
        registry = CapabilityProviderRegistry((first, second))
        self.assertEqual(registry.providers_for(Capability.BIDDING), (first, second))

    def test_capabilities_remain_separate(self):
        bid, lead = _BidProvider("ben.bid"), _LeadProvider()
        registry = CapabilityProviderRegistry((bid, lead))
        self.assertEqual(registry.providers_for(Capability.BIDDING), (bid,))
        self.assertEqual(registry.providers_for(Capability.OPENING_LEAD), (lead,))

    def test_lookup_is_explicit_and_case_insensitive(self):
        bid = _BidProvider("BEN.Bid")
        registry = CapabilityProviderRegistry((bid,))
        self.assertIs(registry.get(Capability.BIDDING, "ben.bid"), bid)
        self.assertIsNone(registry.get(Capability.PLAY, "ben.bid"))

    def test_duplicate_id_within_capability_is_rejected(self):
        with self.assertRaises(ValueError):
            CapabilityProviderRegistry((_BidProvider("ben.bid"), _BidProvider("BEN.BID")))

    def test_wrong_protocol_is_rejected(self):
        with self.assertRaises(TypeError):
            CapabilityProviderRegistry((_WrongShape(),))

    def test_registry_never_calls_provider_during_registration_or_query(self):
        lead = _LeadProvider()
        registry = CapabilityProviderRegistry((lead,))
        self.assertIs(registry.require(Capability.OPENING_LEAD, "fixture.lead"), lead)


if __name__ == "__main__":
    unittest.main()
