"""A3.9 role-aware DecisionCase view tests."""

from bridge.auction import Call
from bridge.capability_providers import (
    Capability,
    CapabilityResult,
    ProviderDescriptor,
    ProviderStatus,
)
from bridge.decision_case import DecisionCase
from bridge.decision_case_roles import (
    build_decision_case_role_view,
)
from bridge.decision_evidence import (
    DecisionEvidence,
    EvidenceScope,
)
from bridge.evidence_roles import EvidenceRole


def bidding_evidence(
    provider_id: str,
    call: str,
    scope: EvidenceScope,
) -> DecisionEvidence:
    descriptor = ProviderDescriptor(
        provider_id=provider_id,
        capability=Capability.BIDDING,
        implementation=f"{provider_id}-test",
        version="test",
    )

    return DecisionEvidence(
        result=CapabilityResult(
            provider=descriptor,
            status=ProviderStatus.SUCCESS,
            recommendation=Call.parse(call),
        ),
        scope=scope,
    )


def bridgelab_evidence(call: str = "3C") -> DecisionEvidence:
    return bidding_evidence(
        "bridgelab",
        call,
        EvidenceScope.PARTNERSHIP,
    )


def external_evidence(
    provider_id: str,
    call: str,
) -> DecisionEvidence:
    return bidding_evidence(
        provider_id,
        call,
        EvidenceScope.PROVIDER,
    )


def test_empty_case_produces_empty_role_view():
    case = DecisionCase(case_id="a39-empty")

    view = build_decision_case_role_view(case)

    assert view.case_id == "a39-empty"
    assert view.evidence == ()


def test_bridgelab_is_policy_recommendation():
    bridge = bridgelab_evidence()

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a39-policy",
            bridgelab=bridge,
        )
    )

    assert len(view.evidence) == 1
    assert (
        view.evidence[0].role
        is EvidenceRole.POLICY_RECOMMENDATION
    )
    assert view.evidence[0].evidence is bridge


def test_external_evidence_is_external_recommendation():
    ben = external_evidence("ben", "4H")

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a39-external",
            external=(ben,),
        )
    )

    assert len(view.evidence) == 1
    assert (
        view.evidence[0].role
        is EvidenceRole.EXTERNAL_RECOMMENDATION
    )
    assert view.evidence[0].evidence is ben


def test_multiple_external_observations_preserve_order():
    ben = external_evidence("ben", "4H")
    brl = external_evidence("brl", "3H")

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a39-order",
            external=(ben, brl),
        )
    )

    external = view.for_role(
        EvidenceRole.EXTERNAL_RECOMMENDATION
    )

    assert tuple(
        item.evidence
        for item in external
    ) == (ben, brl)


def test_same_bid_keeps_policy_and_external_roles_separate():
    bridge = bridgelab_evidence("4H")
    ben = external_evidence("ben", "4H")

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a39-same-bid",
            bridgelab=bridge,
            external=(ben,),
        )
    )

    assert view.evidence[0].role is (
        EvidenceRole.POLICY_RECOMMENDATION
    )
    assert view.evidence[1].role is (
        EvidenceRole.EXTERNAL_RECOMMENDATION
    )

    assert (
        view.evidence[0].evidence.result.recommendation
        == view.evidence[1].evidence.result.recommendation
    )


def test_for_role_returns_only_requested_role():
    bridge = bridgelab_evidence("3C")
    ben = external_evidence("ben", "4H")
    brl = external_evidence("brl", "3H")

    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a39-filter",
            bridgelab=bridge,
            external=(ben, brl),
        )
    )

    policy = view.for_role(
        EvidenceRole.POLICY_RECOMMENDATION
    )
    external = view.for_role(
        EvidenceRole.EXTERNAL_RECOMMENDATION
    )

    assert len(policy) == 1
    assert policy[0].evidence is bridge

    assert len(external) == 2
    assert external[0].evidence is ben
    assert external[1].evidence is brl


def test_missing_role_returns_empty_tuple():
    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a39-missing",
            bridgelab=bridgelab_evidence(),
        )
    )

    assert view.for_role(
        EvidenceRole.OUTCOME_MEASUREMENT
    ) == ()


def test_building_view_does_not_modify_case():
    bridge = bridgelab_evidence("3C")
    ben = external_evidence("ben", "4H")

    case = DecisionCase(
        case_id="a39-immutable",
        bridgelab=bridge,
        external=(ben,),
        notes=("Original case.",),
    )

    original_external = case.external
    original_notes = case.notes

    view = build_decision_case_role_view(case)

    assert case.bridgelab is bridge
    assert case.external is original_external
    assert case.notes is original_notes

    assert len(view.evidence) == 2


def test_view_contains_no_disagreement_or_winner_field():
    view = build_decision_case_role_view(
        DecisionCase(
            case_id="a39-passive",
            bridgelab=bridgelab_evidence(),
            external=(external_evidence("ben", "4H"),),
        )
    )

    assert not hasattr(view, "winner")
    assert not hasattr(view, "preferred")
    assert not hasattr(view, "score")
    assert not hasattr(view, "disagreements")
