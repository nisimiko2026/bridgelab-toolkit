"""A7.6 multi-adviser disagreement analysis tests."""

import pytest

from bridge.auction import Auction, Call
from bridge.bidding_rules import BiddingContext, SystemContext
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.capability_registry import CapabilityProviderRegistry
from bridge.decision_evidence import (
    DecisionEvidence,
    DisagreementKind,
    EvidenceScope,
)
from bridge.external_bidding_adviser import (
    ExternalBiddingAdviserAdapter,
    ExternalBiddingObservation,
)
from bridge.models import Hand, Seat, Vulnerability
from bridge.multi_adviser_disagreement import (
    AdviserSemanticContext,
    analyze_multi_adviser_disagreement,
)
from bridge.multi_bidding_adviser import BiddingAdviserRequest


def _context():
    return BiddingContext.create(
        hand=Hand.parse("AKQJ5.K82.976.A7"),
        auction=Auction(Seat.NORTH, ("1C", "P")),
        vulnerability=Vulnerability.NONE,
        system=SystemContext("TWO_OVER_ONE_GF"),
    )


def _bridge(call="3NT", system_id="TWO_OVER_ONE_GF"):
    descriptor = ProviderDescriptor(
        provider_id="bridgelab",
        capability=Capability.BIDDING,
        implementation="bridgelab-policy",
        version="test",
    )
    return DecisionEvidence(
        result=CapabilityResult(
            provider=descriptor,
            status=ProviderStatus.SUCCESS,
            recommendation=Call.parse(call),
        ),
        scope=EvidenceScope.PARTNERSHIP,
        system_id=system_id,
    )


class StubTransport:
    def __init__(self, observation):
        self.observation = observation
        self.calls = 0

    def observe(self, context):
        self.calls += 1
        return self.observation


def _provider(provider_id, call=None, *, status=ProviderStatus.SUCCESS):
    transport = StubTransport(
        ExternalBiddingObservation(
            status=status,
            recommendation=call if status is ProviderStatus.SUCCESS else None,
            source_ids=(f"{provider_id}:source",),
            model_id=f"{provider_id}-model",
        )
    )
    adviser = ExternalBiddingAdviserAdapter(
        descriptor=ProviderDescriptor(
            provider_id=provider_id,
            capability=Capability.BIDDING,
            implementation=f"{provider_id}-test",
            version="test",
        ),
        transport=transport,
    )
    return adviser, transport


class RaisingAdviser:
    descriptor = ProviderDescriptor(
        provider_id="broken",
        capability=Capability.BIDDING,
        implementation="raising-test",
        version="test",
    )

    def __init__(self):
        self.calls = 0

    def advise(self, context):
        raise AssertionError("advise should not be called")

    def evidence(self, context, **kwargs):
        self.calls += 1
        raise RuntimeError("boom")


def test_each_adviser_is_classified_independently_against_bridgelab():
    same, _ = _provider("same", "3NT")
    sayc, _ = _provider("sayc", "4S")
    unknown, _ = _provider("unknown", "4H")
    registry = CapabilityProviderRegistry((same, sayc, unknown))

    result = analyze_multi_adviser_disagreement(
        case_id="case-1",
        bridgelab=_bridge(),
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("same", system_id="TWO_OVER_ONE_GF"),
            BiddingAdviserRequest("sayc", system_id="SAYC"),
            BiddingAdviserRequest("unknown"),
        ),
    )

    assert tuple(x.kind for x in result.classified) == (
        DisagreementKind.AGREEMENT,
        DisagreementKind.SYSTEM_DIFFERENCE,
        DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM,
    )


def test_two_external_advisers_agreeing_does_not_create_majority_semantics():
    a, _ = _provider("a", "4S")
    b, _ = _provider("b", "4S")
    registry = CapabilityProviderRegistry((a, b))

    result = analyze_multi_adviser_disagreement(
        case_id="case-2",
        bridgelab=_bridge("3NT"),
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("a", system_id="TWO_OVER_ONE_GF"),
            BiddingAdviserRequest("b", system_id="TWO_OVER_ONE_GF"),
        ),
    )

    assert tuple(x.kind for x in result.classified) == (
        DisagreementKind.JUDGMENT_DIFFERENCE,
        DisagreementKind.JUDGMENT_DIFFERENCE,
    )
    for name in ("winner", "vote", "votes", "majority", "selected", "preferred"):
        assert not hasattr(result, name)


def test_abstain_is_classified_but_not_fabricated_as_recommendation():
    abstain, _ = _provider("abstain", status=ProviderStatus.ABSTAIN)

    result = analyze_multi_adviser_disagreement(
        case_id="case-3",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry((abstain,)),
        context=_context(),
        requests=(BiddingAdviserRequest("abstain"),),
    )

    assert result.gathered.evidence[0].recommendation is None
    assert result.disagreements[0].kind is DisagreementKind.EXTERNAL_MODEL_ABSTAIN


@pytest.mark.parametrize("status", (ProviderStatus.UNAVAILABLE, ProviderStatus.FAILED))
def test_operational_non_success_is_not_classified_as_bidding_disagreement(status):
    provider, _ = _provider("offline", status=status)

    result = analyze_multi_adviser_disagreement(
        case_id="case-4",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry((provider,)),
        context=_context(),
        requests=(BiddingAdviserRequest("offline"),),
    )

    assert result.disagreements == (None,)
    assert result.classified == ()
    assert result.decision_case.disagreements == ()


def test_runtime_exception_is_isolated_and_not_classified_as_vote():
    broken = RaisingAdviser()
    good, good_transport = _provider("good", "3NT")
    registry = CapabilityProviderRegistry((broken, good))

    result = analyze_multi_adviser_disagreement(
        case_id="case-5",
        bridgelab=_bridge(),
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("broken"),
            BiddingAdviserRequest("good", system_id="TWO_OVER_ONE_GF"),
        ),
    )

    assert broken.calls == 1
    assert good_transport.calls == 1
    assert result.gathered.evidence[0].result.status is ProviderStatus.FAILED
    assert result.disagreements[0] is None
    assert result.disagreements[1].kind is DisagreementKind.AGREEMENT
    assert len(result.gathered.failures) == 1


def test_semantic_context_can_classify_convention_difference():
    external, _ = _provider("ai", "4S")

    result = analyze_multi_adviser_disagreement(
        case_id="case-6",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry((external,)),
        context=_context(),
        requests=(
            BiddingAdviserRequest("ai", system_id="TWO_OVER_ONE_GF"),
        ),
        semantic_contexts=(
            AdviserSemanticContext(same_convention=False),
        ),
    )

    assert result.classified[0].kind is DisagreementKind.CONVENTION_DIFFERENCE


def test_semantic_context_can_classify_treatment_difference():
    external, _ = _provider("ai", "4S")

    result = analyze_multi_adviser_disagreement(
        case_id="case-7",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry((external,)),
        context=_context(),
        requests=(
            BiddingAdviserRequest("ai", system_id="TWO_OVER_ONE_GF"),
        ),
        semantic_contexts=(
            AdviserSemanticContext(
                same_convention=True,
                same_treatment=False,
            ),
        ),
    )

    assert result.classified[0].kind is DisagreementKind.TREATMENT_DIFFERENCE


def test_semantic_context_can_classify_partnership_difference():
    external, _ = _provider("ai", "4S")

    result = analyze_multi_adviser_disagreement(
        case_id="case-8",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry((external,)),
        context=_context(),
        requests=(
            BiddingAdviserRequest("ai", system_id="TWO_OVER_ONE_GF"),
        ),
        semantic_contexts=(
            AdviserSemanticContext(
                same_convention=True,
                same_treatment=True,
                same_partnership_agreement=False,
            ),
        ),
    )

    assert result.classified[0].kind is DisagreementKind.PARTNERSHIP_AGREEMENT


def test_semantic_context_can_classify_policy_gap():
    external, _ = _provider("ai", "4S")

    result = analyze_multi_adviser_disagreement(
        case_id="case-9",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry((external,)),
        context=_context(),
        requests=(
            BiddingAdviserRequest("ai", system_id="TWO_OVER_ONE_GF"),
        ),
        semantic_contexts=(
            AdviserSemanticContext(
                same_convention=True,
                same_treatment=True,
                same_partnership_agreement=True,
                bridgelab_policy_expected=True,
            ),
        ),
    )

    assert result.classified[0].kind is DisagreementKind.POSSIBLE_POLICY_GAP


def test_unknown_system_takes_precedence_over_unproven_semantic_claims():
    external, _ = _provider("ai", "4S")

    result = analyze_multi_adviser_disagreement(
        case_id="case-10",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry((external,)),
        context=_context(),
        requests=(BiddingAdviserRequest("ai"),),
        semantic_contexts=(
            AdviserSemanticContext(
                same_convention=False,
                bridgelab_policy_expected=True,
            ),
        ),
    )

    assert result.classified[0].kind is DisagreementKind.UNKNOWN_EXTERNAL_SYSTEM


def test_decision_case_preserves_all_external_evidence_but_only_real_disagreements():
    good, _ = _provider("good", "3NT")
    offline, _ = _provider("offline", status=ProviderStatus.UNAVAILABLE)
    registry = CapabilityProviderRegistry((good, offline))

    result = analyze_multi_adviser_disagreement(
        case_id="case-11",
        bridgelab=_bridge(),
        registry=registry,
        context=_context(),
        requests=(
            BiddingAdviserRequest("good", system_id="TWO_OVER_ONE_GF"),
            BiddingAdviserRequest("offline"),
        ),
        notes=("multi-ai audit",),
    )

    assert len(result.decision_case.external) == 2
    assert len(result.decision_case.disagreements) == 1
    assert result.decision_case.disagreements[0].kind is DisagreementKind.AGREEMENT
    assert result.decision_case.notes == ("multi-ai audit",)


def test_default_semantic_contexts_are_one_per_request():
    a, _ = _provider("a", "4S")
    b, _ = _provider("b", "4H")

    result = analyze_multi_adviser_disagreement(
        case_id="case-12",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry((a, b)),
        context=_context(),
        requests=(
            BiddingAdviserRequest("a"),
            BiddingAdviserRequest("b", system_id="SAYC"),
        ),
    )

    assert len(result.contexts) == 2
    assert result.contexts[0].external_system_known is False
    assert result.contexts[1].same_system is False


def test_semantic_context_count_must_match_requests():
    with pytest.raises(ValueError, match="equal length"):
        analyze_multi_adviser_disagreement(
            case_id="case-13",
            bridgelab=_bridge(),
            registry=CapabilityProviderRegistry(),
            context=_context(),
            requests=(BiddingAdviserRequest("x"),),
            semantic_contexts=(),
        )


def test_semantic_contexts_must_be_tuple():
    with pytest.raises(TypeError, match="semantic_contexts must be a tuple"):
        analyze_multi_adviser_disagreement(
            case_id="case-14",
            bridgelab=_bridge(),
            registry=CapabilityProviderRegistry(),
            context=_context(),
            requests=(),
            semantic_contexts=[],
        )


def test_empty_adviser_set_is_valid():
    result = analyze_multi_adviser_disagreement(
        case_id="case-15",
        bridgelab=_bridge(),
        registry=CapabilityProviderRegistry(),
        context=_context(),
        requests=(),
    )

    assert result.gathered.evidence == ()
    assert result.contexts == ()
    assert result.disagreements == ()
    assert result.decision_case.external == ()
    assert result.decision_case.disagreements == ()


def test_bridgelab_evidence_is_required():
    with pytest.raises(TypeError, match="bridgelab must be DecisionEvidence"):
        analyze_multi_adviser_disagreement(
            case_id="case-16",
            bridgelab=object(),
            registry=CapabilityProviderRegistry(),
            context=_context(),
            requests=(),
        )
