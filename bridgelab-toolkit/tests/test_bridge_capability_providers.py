import unittest

from bridge.auction import Call
from bridge.capability_providers import (
    BiddingAdviser, Capability, CapabilityResult, ProviderDescriptor,
    ProviderEvidence, ProviderStatus,
)


class _BidProvider:
    descriptor = ProviderDescriptor("test.bid", Capability.BIDDING, "fixture", "1")

    def advise(self, context):
        return CapabilityResult(
            self.descriptor, ProviderStatus.SUCCESS, Call.parse("P"),
            evidence=ProviderEvidence(("fixture:1",), model_id="test-model"),
        )


class CapabilityProviderContractTests(unittest.TestCase):
    def test_descriptor_is_capability_specific_and_normalized(self):
        item = ProviderDescriptor("  ben.bid  ", Capability.BIDDING, " BEN ", " 1.0 ")
        self.assertEqual(item.provider_id, "ben.bid")
        self.assertEqual(item.implementation, "BEN")
        self.assertEqual(item.version, "1.0")

    def test_success_requires_recommendation(self):
        descriptor = ProviderDescriptor("x", Capability.BIDDING, "fixture")
        with self.assertRaises(ValueError):
            CapabilityResult(descriptor, ProviderStatus.SUCCESS)

    def test_abstention_cannot_hide_a_recommendation(self):
        descriptor = ProviderDescriptor("x", Capability.BIDDING, "fixture")
        with self.assertRaises(ValueError):
            CapabilityResult(descriptor, ProviderStatus.ABSTAIN, Call.parse("P"))

    def test_provider_evidence_preserves_provenance_without_policy_claims(self):
        evidence = ProviderEvidence((" source:a ", "source:b"), " model-7 ", (" observed ",))
        self.assertEqual(evidence.source_ids, ("source:a", "source:b"))
        self.assertEqual(evidence.model_id, "model-7")
        self.assertEqual(evidence.notes, ("observed",))

    def test_runtime_protocol_accepts_capability_provider(self):
        self.assertIsInstance(_BidProvider(), BiddingAdviser)


if __name__ == "__main__":
    unittest.main()
