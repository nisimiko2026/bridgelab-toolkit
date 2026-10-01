import unittest

from bridge.auction import Call
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_evidence import (
    DecisionEvidence,
    DisagreementContext,
    DisagreementKind,
    EvidenceScope,
    classify_disagreement,
)


class DecisionEvidenceTests(unittest.TestCase):

    def provider(self, provider_id: str) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.BIDDING,
            implementation="test",
            version="1",
        )

    def evidence(
        self,
        recommendation: str | None,
        *,
        provider_id: str = "test.provider",
        status: ProviderStatus = ProviderStatus.SUCCESS,
        scope: EvidenceScope = EvidenceScope.PROVIDER,
        confidence: float | None = None,
        system_id: str | None = None,
        convention_id: str | None = None,
        treatment_id: str | None = None,
        partnership_id: str | None = None,
    ) -> DecisionEvidence[Call]:
        result = CapabilityResult(
            provider=self.provider(provider_id),
            status=status,
            recommendation=(
                Call.parse(recommendation)
                if recommendation is not None
                else None
            ),
        )

        return DecisionEvidence(
            result=result,
            scope=scope,
            system_id=system_id,
            convention_id=convention_id,
            treatment_id=treatment_id,
            partnership_id=partnership_id,
            confidence=confidence,
        )

    def test_same_recommendation_is_agreement(self) -> None:
        left = self.evidence(
            "3C",
            provider_id="bridgelab.rules",
            scope=EvidenceScope.PARTNERSHIP,
        )
        right = self.evidence(
            "3C",
            provider_id="ben.bid",
        )

        disagreement = classify_disagreement(left, right)

        self.assertEqual(
            disagreement.kind,
            DisagreementKind.AGREEMENT,
        )
        self.assertEqual(
            disagreement.left_provider_id,
            "bridgelab.rules",
        )
        self.assertEqual(
            disagreement.right_provider_id,
            "ben.bid",
        )

    def test_unknown_external_system_is_not_policy_defect(self) -> None:
        left = self.evidence(
            "3C",
            provider_id="bridgelab.rules",
            scope=EvidenceScope.PARTNERSHIP,
            system_id="2over1",
        )
        right = self.evidence(
            "4H",
            provider_id="expert.corpus",
            scope=EvidenceScope.EXPERT_CORPUS,
        )

        disagreement = classify_disagreement(
            left,
            right,
            context=DisagreementContext(
                external_system_known=False,
            ),
        )

        self.assertEqual(
            disagreement.kind,
            DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
        )

    def test_explicit_treatment_difference_is_preserved(self) -> None:
        left = self.evidence(
            "3C",
            provider_id="bridgelab.rules",
            scope=EvidenceScope.TREATMENT,
            treatment_id="treatment.a",
        )
        right = self.evidence(
            "3D",
            provider_id="ben.bid",
            scope=EvidenceScope.TREATMENT,
            treatment_id="treatment.b",
        )

        disagreement = classify_disagreement(
            left,
            right,
            context=DisagreementContext(
                external_system_known=True,
                same_system=True,
                same_convention=True,
                same_treatment=False,
            ),
        )

        self.assertEqual(
            disagreement.kind,
            DisagreementKind.TREATMENT_DIFFERENCE,
        )

    def test_policy_gap_requires_explicit_context(self) -> None:
        left = self.evidence(
            "3C",
            provider_id="bridgelab.rules",
            scope=EvidenceScope.PARTNERSHIP,
        )
        right = self.evidence(
            "4H",
            provider_id="brl.bid",
        )

        ordinary = classify_disagreement(
            left,
            right,
            context=DisagreementContext(
                external_system_known=True,
                same_system=True,
                same_convention=True,
                same_treatment=True,
                same_partnership_agreement=True,
            ),
        )

        explicit_gap = classify_disagreement(
            left,
            right,
            context=DisagreementContext(
                external_system_known=True,
                same_system=True,
                same_convention=True,
                same_treatment=True,
                same_partnership_agreement=True,
                bridgelab_policy_expected=True,
            ),
        )

        self.assertEqual(
            ordinary.kind,
            DisagreementKind.JUDGMENT_DIFFERENCE,
        )
        self.assertEqual(
            explicit_gap.kind,
            DisagreementKind.POSSIBLE_POLICY_GAP,
        )

    def test_abstention_remains_evidence_not_a_fabricated_bid(self) -> None:
        left = self.evidence(
            "3C",
            provider_id="bridgelab.rules",
            scope=EvidenceScope.PARTNERSHIP,
        )
        right = self.evidence(
            None,
            provider_id="brl.bid",
            status=ProviderStatus.ABSTAIN,
        )

        disagreement = classify_disagreement(left, right)

        self.assertIsNone(right.recommendation)
        self.assertEqual(
            right.result.status,
            ProviderStatus.ABSTAIN,
        )
        self.assertEqual(
            disagreement.kind,
            DisagreementKind.EXTERNAL_MODEL_ABSTAIN,
        )

    def test_confidence_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            self.evidence(
                "3H",
                confidence=1.01,
            )

        with self.assertRaises(ValueError):
            self.evidence(
                "3H",
                confidence=-0.01,
            )

        valid = self.evidence(
            "3H",
            confidence=0.75,
        )

        self.assertEqual(valid.confidence, 0.75)


if __name__ == "__main__":
    unittest.main()
